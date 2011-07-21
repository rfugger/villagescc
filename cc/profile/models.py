from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from cc.general.models import VarCharField, EmailField
from cc.geo.models import Location

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    name = VarCharField(blank=True)
    email = EmailField(blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to='user_photos', max_length=256, blank=True)
    endorsements_remaining = models.PositiveIntegerField(
        default=settings.INITIAL_ENDORSEMENTS)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    FEED_TEMPLATE = 'profile_feed_item.html'
    
    def __unicode__(self):
        return self.name or self.user.username

    @models.permalink
    def get_absolute_url(self):
        return ('profile', (self.user.username,))

    def endorsement_for(self, recipient):
        "Returns this profile's endorsement of recipient, or None."
        try:
            return self.endorsements_made.get(recipient=recipient)
        except ObjectDoesNotExist:
            return None

    @property
    def date(self):
        """
        For FeedItem source interface, returns last updated date as the
        feed item date.
        """
        return self.updated

    def get_feed_users(self):
        "Make profile updates available in poster's feed, and publicly."
        return (self, None)
    
    @classmethod
    def create_profile(cls, sender, instance, created, **kwargs):
        if created:
            cls.objects.create(user=instance)

# Create new empty profile when a new user is created.
post_save.connect(Profile.create_profile, sender=User,
                  dispatch_uid='profile.models')
                  
