"""
Models for storing feed items.  This is a denormalized merged list of all
feed items sorted by date.

Classes that are referenced by feed items must implement the following
interface:

Properties:
* id

TODO: Change these to feed_date, feed_location, feed_text

* date
* location
* text
* feed_poster - Profile that created this feed item.
* feed_recipient - Profile that is the target of this feed item (eg,
	payment recipient, endorsement recipient)
* feed_public - Boolean indicating whether this feed item is public.
* FEED_TEMPLATE - template for rendering this item in a feed.

Methods:
* get_absolute_url
* get_search_text - Returns a list of (text, weight) pairs for the text search
    index, where weight is in ('A', 'B', 'C', 'D') (as per postgres text
    search weightings).

Class Methods:
* get_by_id - Model instance with given ID.

Exceptions:
* DoesNotExist

TODO: Feed item expiry.

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
    api.RipplePayment: 'acknowledgement',
}

# Reverse keys and values in ITEM_TYPES.
MODEL_TYPES = dict(((item_type, model)
                    for model, item_type in ITEM_TYPES.items()))

TRUSTED_SUBQUERY = (
    "feed_feeditem.poster_id in "
    "(select to_profile_id from profile_profile_trusted_profiles "
    "    where from_profile_id = %s)")
                    

class FeedManager(GeoManager):
    def get_feed_and_remaining(self, *args, **kwargs):
        """
        Returns feed and count of remaining items not returned after
        limiting the query.
        """
        count_kwargs = kwargs.copy()
        count_kwargs.pop('limit', None)
        count = self.get_feed_count(*args, **count_kwargs)
        if count > 0:
            items = self.get_feed(*args, **kwargs)
        else:
            items = []
        return items, count - len(items)
    
    def get_feed_count(self, *args, **kwargs):
        return self._feed_query(*args, **kwargs).count()

    def get_feed(self, *args, **kwargs):
        """
        Get list of dereferenced feed items (actually load the Posts, Profiles,
        etc.) for the given user profile.  Each item gets a `trusted` attribute
        set if its feed_poster is trusted by the requesting profile.

        Takes a `limit` parameter that is the maximum number of items to return.
        """
        limit = kwargs.pop('limit', settings.FEED_ITEMS_PER_PAGE)        
        query = self._feed_query(*args, **kwargs)[:limit]
        items = []
        for feed_item in query:
            item = feed_item.item
            if item:
                item.trusted = getattr(feed_item, 'trusted', None)
                items.append(item)
            else:
                # Orphan feed item -- delete.
                # TODO: Move deletion of orphan feed items to cron job.
                feed_item.delete()
        return items
    
    def _feed_query(self, profile=None, location=None,
                    radius=settings.DEFAULT_FEED_RADIUS,
                    item_type=None, tsearch=None, trusted_only=False,
                    poster=None, recipient=None, up_to_date=None):
        "Build a query for feed items corresponding to a particular feed."
        query = self.get_query_set().order_by('-date')
        if up_to_date:
            query = query.filter(date__lt=up_to_date)

        if not poster and not recipient:
            if profile:
                query = query.filter(
                    Q(poster=profile) | Q(recipient=profile) | Q(public=True))
            else:
                query = query.filter(public=True)
        if poster:
            query = query.filter(poster=poster)
        if recipient:
            query = query.filter(recipient=recipient)
        if item_type:
            query = query.filter(item_type=ITEM_TYPES[item_type])
        if profile:
            # Add extra `trusted` attribute which is True when
            # requester trusts poster.
            query = query.extra(
                select={'trusted': TRUSTED_SUBQUERY},
                select_params=[profile.id])
        if trusted_only and profile:
            query = query.extra(where=[TRUSTED_SUBQUERY], params=[profile.id])
            
        if location and radius:
            query = query.filter(
                # TODO: Bounding box query might be faster?
                Q(location__point__dwithin=(location.point, radius)) |
                Q(location__isnull=True))
        if tsearch:
            query = query.extra(
                where=["tsearch @@ plainto_tsquery(%s)"],
                params=[tsearch])            
        return query
            
    def create_from_item(self, item):
        item_type = ITEM_TYPES[type(item)]
        feed_item = self.create(
            date=item.date,
            poster=item.feed_poster,
            recipient=item.feed_recipient,
            item_type=item_type,
            item_id=item.id,
            public=item.feed_public,
            location=item.location)
        feed_item.update_tsearch(item.get_search_text())

    
class FeedItem(models.Model):
    """
    A denormalized record of feed data, merged for ease of ordering by date
    and selecting recent items without massive queries on several other tables
    and merging results every time.
    
    Feed items are identified by (item_type, item_id) tuple.  They may have a
    location used for filtering feeds by proximity.  They may also specify
    particular recipient profiles whose feed they will appear in.  If the feed
    item is marked public, then the recipients are ignored.
    """
    date = models.DateTimeField(db_index=True)
    poster = models.ForeignKey(Profile, related_name='posted_feed_items')
    recipient = models.ForeignKey(
        Profile, related_name='received_feed_items', null=True, blank=True)
    item_type = models.CharField(max_length=16, choices=(
            (ITEM_TYPES[Post], 'Post'),
            (ITEM_TYPES[Profile], 'Profile Update'),
            (ITEM_TYPES[api.RipplePayment], 'Acknowledgement'),
            (ITEM_TYPES[Endorsement], 'Endorsement'),
        ))
    item_id = models.PositiveIntegerField()
    location = models.ForeignKey(Location, null=True, blank=True)
    public = models.BooleanField()
                               
    objects = FeedManager()
    
    class Meta:
        unique_together = ('item_type', 'item_id')

    def __unicode__(self):
        return u"Feed %s %d %s" % (self.item_type, self.item_id, self.date)

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
            # Delete existing feed item.
            cls.objects.filter(
                item_type=item_type, item_id=instance.id).delete()
        cls.objects.create_from_item(instance)
            
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
