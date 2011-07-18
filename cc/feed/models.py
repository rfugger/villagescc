from django.db import models
from django.db.models.signals import post_save, post_delete

from cc.profile.models import Profile
from cc.geo.models import Location
from cc.post.models import Post
from cc.endorse.models import Endorsement

ITEM_TYPES = {
    Post: 'post',
    Profile: 'profile',
    Endorsement: 'endorsement',
    #Payment: 'payment',  -- TODO: Doesn't exist yet.
}

MODEL_TYPES = dict(((item_type, model)
                    for model, item_type in ITEM_TYPES.items()))

class FeedManager(models.Manager):
    def get_feed(self, profile, radius):
        """
        Get list of dereferenced feed items (actually load the posts, profiles,
        etc.) for the given user profile within a certain radius.
        """
        pass

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
        a model object is created.  The original model must have properties
        'date' and 'location', and method get_feed_users(), which returns
        a list of all users who should definitely see the feed item, as well
        as None if the item should potentially be available to anyone.
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
