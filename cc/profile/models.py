from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from cc.general.models import VarCharField, EmailField
from cc.geo.models import Location
import cc.ripple.api as ripple

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    name = VarCharField(blank=True)
    email = EmailField(blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)
    photo = models.ImageField(
        upload_to='user_photos', max_length=256, blank=True)
    description = models.TextField(
        blank=True, help_text="Be sure to mention any skills you bring "
        "to the community, so others can search for you.")
    
    endorsements_remaining = models.PositiveIntegerField(
        default=settings.INITIAL_ENDORSEMENTS)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    FEED_TEMPLATE = 'profile_feed_item.html'
    
    def __unicode__(self):
        return self.name or self.username

    @models.permalink
    def get_absolute_url(self):
        return ('profile', (self.username,))

    @property
    def username(self):
        # Username is stored in django User model.
        return self.user.username

    def endorsement_for(self, recipient):
        "Returns this profile's endorsement of recipient, or None."
        try:
            return self.endorsements_made.get(recipient=recipient)
        except ObjectDoesNotExist:
            return None

    @property
    def date(self):
        return self.updated

    @property
    def text(self):
        return self.description
    
    def get_feed_users(self):
        "Make profile updates available publicly."
        return (None,)

    @property
    def feed_poster(self):
        return self

    # TODO: Cache this across requests.
    @property
    def endorsement_sum(self):
        return self.endorsements_received.all().aggregate(
            models.Sum('weight')).get('weight__sum', 0)

    def trusted_endorsement_sum(self, asker):
        """"
        Returns max flow of endorsements from asker to self across endorsement
        network.
        """
        return ripple.credit_reputation(self, asker)

    def overall_balance(self):
        return ripple.overall_balance(self)
    
    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(pk=id)
    
    @classmethod
    def create_profile(cls, sender, instance, created, **kwargs):
        if created:
            cls.objects.create(user=instance)

# Create new empty profile when a new user is created.
post_save.connect(Profile.create_profile, sender=User,
                  dispatch_uid='profile.models')
                  
