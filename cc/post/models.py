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
    user = models.ForeignKey(Profile, related_name='posts')
    date = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    title = VarCharField(max_length=100)
    text = models.TextField()
    image = models.ImageField(
        upload_to='post/%Y/%m', max_length=256, blank=True)
    want = models.BooleanField(
        default=False, help_text="Leave unchecked if your post is an offer.")
    location = models.ForeignKey(Location)

    objects = UndeletedPostManager()
    all_objects = models.Manager()

    FEED_TEMPLATE = 'post_feed_item.html'
    
    def __unicode__(self):
        return u"%s [%s]" % (self.title, self.want and "Want" or "Offer")

    @models.permalink
    def get_absolute_url(self):
        return ('cc.post.views.view_post', (self.id,))

    def can_edit(self, profile):
        return self.user == profile

    @property
    def feed_public(self):
        return True

    @property
    def feed_recipient(self):
        return None

    @property
    def feed_poster(self):
        return self.user

    def get_search_text(self):
        return [(self.title, 'A'),
                (self.text, 'B'),
                (self.user.name, 'C'),
                (self.user.username, 'C'),
               ]
        
    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(pk=id)
    
