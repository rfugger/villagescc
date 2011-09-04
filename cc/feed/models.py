"""
Models for storing feed items.  This is a denormalized merged list of all
feed items sorted by date.

Classes that are referenced by feed items must implement the following
interface:

Properties:
* id
* date
* location
* text
* feed_poster - Profile that created this feed item.
* FEED_TEMPLATE - template for rendering this item in a feed.

Methods:
* get_feed_users - All users who can have this feed item in their feed,
    including None if feed item is public.
* get_absolute_url

Class Methods:
* get_by_id - Model instance with given ID.

Exceptions:
* DoesNotExist

"""

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.db.models import Q
from django.conf import settings
from django.contrib.gis.db.models import GeoManager

from cc.profile.models import Profile
from cc.geo.models import Location
from cc.post.models import Post
from cc.relate.models import Endorsement
import cc.ripple.api as api
from cc.general.util import cache_on_object

# Classes that can be stored as feed items.
ITEM_TYPES = {
    Post: 'post',
    Profile: 'profile',
    Endorsement: 'endorsement',
    api.RipplePayment: 'promise',
}

# Reverse keys and values in ITEM_TYPES.
MODEL_TYPES = dict(((item_type, model)
                    for model, item_type in ITEM_TYPES.items()))

class FeedManager(GeoManager):
    def get_feed(self, profile, location, radius=settings.DEFAULT_FEED_RADIUS,
                 page=1, limit=settings.FEED_ITEMS_PER_PAGE,
                 item_type_filter=None):
        """
        Get list of dereferenced feed items (actually load the Posts, Profiles,
        etc.) for the given user profile.  Each item gets a `trusted` attribute
        set if its feed_poster is trusted by the requesting profile.
        
        Pass a model class to 'item_type_filter' to only return those types of
        feed items.
        """
        query = self.get_query_set().order_by('-date')
        if profile:
            query = query.filter(Q(user=profile) | Q(user=None))
        else:
            query = query.filter(user=None)
        if item_type_filter:
            query = query.filter(item_type=ITEM_TYPES[item_type_filter])
        if location and radius:
            query = query.filter(
                Q(location__point__dwithin=(location.point, radius)) |
                Q(location__isnull=True))
        if limit is not None:
            offset = limit * (page - 1)
            query = query[offset:offset + limit]
        items = []
        for feed_item in query:
            item = feed_item.item
            if item:
                item.trusted = feed_item.poster_trusted_by(profile)
                items.append(item)
        return items
        
class FeedItem(models.Model):
    """
    A denormalized record of feed data, merged for ease of ordering by date
    and selecting recent items without massive queries on several other tables
    and merging results every time.
    
    Feed items are identified by (item_type, item_id, user) tuple,
    where user is the user whose feed the item is for, and may be null,
    indicating it may go in anyone's feed.
    
    Feed items may have a location used for filtering feeds by proximity.
    """
    date = models.DateTimeField(db_index=True)
    item_type = models.CharField(max_length=16, choices=(
            (ITEM_TYPES[Post], 'Post'),
            (ITEM_TYPES[Profile], 'Profile Update'),
            (ITEM_TYPES[api.RipplePayment], 'Promise'),
            (ITEM_TYPES[Endorsement], 'Endorsement'),
        ))
    item_id = models.PositiveIntegerField()
    user = models.ForeignKey(Profile, null=True, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)

    objects = FeedManager()
    
    class Meta:
        unique_together = ('item_type', 'item_id', 'user')

    def __unicode__(self):
        s = u"Feed %s %d %s" % (self.item_type, self.item_id, self.date)
        if self.user:
            s = u"%s for %s" % (s, self.user)
        return s

    @property
    @cache_on_object
    def item(self):
        model = MODEL_TYPES[self.item_type]
        try:
            item = model.get_by_id(self.item_id)
        except model.DoesNotExist:
            # Feed items have no referential integrity in the db,
            # so catch cases where model record with item_id is gone.
            item = None
        return item

    def poster_trust(self, profile):
        "Returns profile's trust level in poster."
        if not self.item.feed_poster:
            return 0
        return api.credit_reputation(self.item.feed_poster, profile)
    
    def poster_trusted_by(self, profile):
        return self.poster_trust(profile) > 0
    
    @classmethod
    def create_feed_items(cls, sender, instance, created, **kwargs):
        """
        Signal receiver to create or update a feed item automatically when
        a model object is created.
        """
        # Only create feed items for acceptable model types.
        item_type = ITEM_TYPES.get(sender)
        if not item_type:
            return
        if not created:
            # Delete existing feed items.
            cls.objects.filter(
                item_type=item_type, item_id=instance.id).delete()
        for user in instance.get_feed_users():
            # Don't allow public items with no location.
            if user is None and instance.location is None:
                continue
            cls.objects.create(
                date=instance.date,
                item_type=item_type,
                item_id=instance.id,
                user=user,
                location=instance.location)

    @classmethod
    def delete_feed_items(cls, sender, instance, **kwargs):
        "Signal receiver to clean up feed items when an object is deleted."
        item_type = ITEM_TYPES.get(sender)
        if not item_type:
            return
        cls.objects.filter(item_type=item_type, item_id=instance.id).delete()
        
# Check for creating a new feed item whenever anything is saved.
post_save.connect(FeedItem.create_feed_items, dispatch_uid='feed.models')

# Delete associated feed items whenever anything is deleted.
post_delete.connect(FeedItem.delete_feed_items, dispatch_uid='feed.models')
