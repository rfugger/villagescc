"""
Models for user-submitted posts.
"""

from django.db import models

from cc.profile.models import Profile
from cc.general.models import VarCharField
from cc.geo.models import Location

class UndeletedPostManager(models.Manager):
    def get_query_set(self):
        return super(UndeletedPostManager, self).get_query_set().filter(
            deleted=False)
    
class Post(models.Model):
    user = models.ForeignKey(Profile)
    date = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    text = models.TextField()
    want = models.BooleanField(
        default=False, help_text="Leave unchecked if your post is an offer.")
    location = models.ForeignKey(Location)

    objects = UndeletedPostManager()
    all_objects = models.Manager()

    FEED_TEMPLATE = 'post_feed_item.html'
    
    def __unicode__(self):
        return u"Post by %s at %s" % (self.user, self.date)

    @models.permalink
    def get_absolute_url(self):
        return ('cc.post.views.view_post', (self.id,))

    def can_edit(self, user):
        return user.is_staff or user == self.user

    def get_feed_users(self):
        "Make post available in poster's feed, and publicly."
        return (self.user, None)
