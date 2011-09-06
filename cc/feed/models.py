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
* get_feed_recipients - All users who can have this feed item in their feed,
    including None if feed item is public.
* get_absolute_url
* get_search_text - Returns a list of (text, weight) pairs for the text search
    index, where weight is in ('A', 'B', 'C', 'D') (as per postgres text
    search weightings).

Class Methods:
* get_by_id - Model instance with given ID.

Exceptions:
* DoesNotExist

"""

from django.db import models, connection, transaction
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
                 item_type=None, tsearch=None):
        """
        Get list of dereferenced feed items (actually load the Posts, Profiles,
        etc.) for the given user profile.  Each item gets a `trusted` attribute
        set if its feed_poster is trusted by the requesting profile.
        
        Pass a model class to 'item_type' to only return those types of
        feed items.
        """
        # Build query.
        query = self.get_query_set().order_by('-date')
        if profile:
            query = query.filter(Q(recipient=profile) | Q(recipient=None))
        else:
            query = query.filter(recipient=None)
        if item_type:
            query = query.filter(item_type=ITEM_TYPES[item_type])
        if location and radius:
            query = query.filter(
                Q(location__point__dwithin=(location.point, radius)) |
                Q(location__isnull=True))
        if tsearch:
            query = query.extra(
                where=["tsearch @@ plainto_tsquery(%s)"],
                params=[tsearch])
            
        # Limit query.
        if limit is not None:
            offset = limit * (page - 1)
            query = query[offset:offset + limit]

        # Load items.
        items = []
        for feed_item in query:
            item = feed_item.item
            if item:
                item.trusted = feed_item.poster_trusted_by(profile)
                items.append(item)
            else:
                # Orphan feed item -- delete.
                feed_item.delete()
        return items
        
class FeedItem(models.Model):
    """
    A denormalized record of feed data, merged for ease of ordering by date
    and selecting recent items without massive queries on several other tables
    and merging results every time.
    
    Feed items are identified by (item_type, item_id, recipient) tuple,
    where recipient is the user whose feed the item is for, and may be null,
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
    recipient = models.ForeignKey(Profile, null=True, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)

    objects = FeedManager()
    
    class Meta:
        unique_together = ('item_type', 'item_id', 'recipient')

    def __unicode__(self):
        s = u"Feed %s %d %s" % (self.item_type, self.item_id, self.date)
        if self.recipient:
            s = u"%s for %s" % (s, self.recipient)
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

    def update_tsearch(self, search_text_elements):
        """
        Updates tsearch column (created by custom SQL in feed/sql/feed.sql).
        Takes a list of (text, weight) pairs, where text is a string and
        weight is in ('A', 'B', 'C', 'D') (Postgres tsearch weightings).

        Generated SQL is something like:

            update feed_feeditem
            set tsearch = (
                setweight(to_tsvector('Old Couch'), 'A') ||
                setweight(to_tsvector('Anyone want an old couch?'), 'B'))
            where id = 158;
        """
        snippets = [text for text, weight in search_text_elements]
        weight_statements = ["setweight(to_tsvector(%%s), '%s')" % weight
                             for text, weight in search_text_elements]
        sql = "update feed_feeditem set tsearch = (%s) where id = %%s" % (
            ' || '.join(weight_statements))
        params = snippets + [self.id]
        cursor = connection.cursor()
        cursor.execute(sql, params)
        transaction.commit_unless_managed()
    
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
        for recipient in instance.get_feed_recipients():
            # Don't allow public items with no location.
            if recipient is None and instance.location is None:
                continue
            feed_item = cls.objects.create(
                date=instance.date,
                item_type=item_type,
                item_id=instance.id,
                recipient=recipient,
                location=instance.location)
            # Set text search column.
            feed_item.update_tsearch(instance.get_search_text())

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
