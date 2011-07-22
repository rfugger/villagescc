"""
Models for storing feed items.  This is a denormalized merged list of all
feed items sorted by date.

Classes that are referenced by feed items must implement the following
interface:

Properties:
* date
* location
* feed_poster - Profile that created this feed item.

Methods:
* get_feed_users - All users who can have this feed item in their feed,
    including None if feed item is public.
* TODO: get object by ID. (implemented as model.objects.get, but won't work
    for payment backend?)
"""

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.db.models import Q
from django.conf import settings

from cc.profile.models import Profile
from cc.geo.models import Location
from cc.post.models import Post
from cc.endorse.models import Endorsement

# Classes that can be stored as feed items.
ITEM_TYPES = {
    Post: 'post',
    Profile: 'profile',
    Endorsement: 'endorsement',
    #Payment: 'payment',  -- TODO: Doesn't exist yet.
}

# Reverse keys and values in ITEM_TYPES.
MODEL_TYPES = dict(((item_type, model)
                    for model, item_type in ITEM_TYPES.items()))

class FeedManager(models.Manager):
    def get_feed(self, profile, radius,
                 limit=settings.FEED_ITEMS_PER_PAGE, offset=0,
                 item_type_filter=None):
        """
        Get list of dereferenced feed items (actually load the Posts, Profiles,
        etc.) for the given user profile within a certain radius.
        
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
        item_ids = query.values_list('item_type', 'item_id').distinct()
        if limit is not None:
            item_ids = item_ids[offset:offset + limit]
        return self._load_feed_items(item_ids)
        
    def _load_feed_items(self, item_ids):
        """
        Returns a list of actual model objects from a list of tuples
        (item_type, item_id).
        """
        feed_items = []
        for item_type, item_id in item_ids:
            model = MODEL_TYPES[item_type]
            try:
                obj = model.objects.get(pk=item_id)
            except model.DoesNotExist:
                # Feed items have no referential integrity in the db,
                # so catch cases where model record with item_id is gone.
                pass
            else:
                feed_items.append(obj)
        return feed_items

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
            ('post', 'Post'),
            ('profile', 'Profile Update'),
            ('payment', 'Promise'),
            ('endorsement', 'Endorsement'),
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
