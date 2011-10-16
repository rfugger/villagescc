from datetime import datetime
import random

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from cc.general.models import VarCharField, EmailField
from cc.geo.models import Location
import cc.ripple.api as ripple
from cc.general.util import cache_on_object
from cc.general.mail import send_mail, email_str

CODE_LENGTH = 20
CODE_CHARS = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    name = VarCharField(blank=True)
    email = EmailField(blank=True)
    location = models.ForeignKey(Location, null=True, blank=True)
    photo = models.ImageField(
        upload_to='user_photos', max_length=256, blank=True)
    description = models.TextField(
        blank=True, help_text="Be sure to mention any skills you bring "
        "to the community, so others can search for you.")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField()
    endorsement_limited = models.BooleanField(default=True)

    feed_radius = models.IntegerField(null=True, blank=True)
    feed_trusted = models.BooleanField()

    trusted_profiles = models.ManyToManyField(
        'Profile', symmetrical=False, related_name='trusting_profiles')

    # TODO: Should a profile always trust itself?

    # TODO: Update trust checks to use trusted_profiles throughout code.
    
    FEED_TEMPLATE = 'profile_feed_item.html'
    
    def __unicode__(self):
        return self.name or self.username

    @models.permalink
    def get_absolute_url(self):
        return 'profile', (self.username,)

    def save(self, set_updated=True, **kwargs):
        if set_updated:
            self.updated = datetime.now()
        return super(Profile, self).save(**kwargs)
    
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

    # TODO: Consider putting profile at top of feed whenever they come
    # back online?  (Maybe change 'date' -> 'feed_date'?)
    
    @property
    def text(self):
        return self.description
    
    @property
    def feed_public(self):
        return True

    @property
    def feed_recipient(self):
        return None

    @property
    def feed_poster(self):
        return self

    def get_search_text(self):
        return [(self.name, 'A'),
                (self.username, 'A'),
                (self.description, 'B'),
               ]

    @property
    @cache_on_object
    def endorsement_count(self):
        return self.endorsements_received.all().count()
    
    @property
    @cache_on_object
    def endorsement_sum(self):
        return self.endorsements_received.all().aggregate(
            models.Sum('weight')).get('weight__sum') or 0

    @property
    @cache_on_object
    def endorsements_made_sum(self):
        return (
            (self.endorsements_made.all().aggregate(
                models.Sum('weight')).get('weight__sum') or 0) +
            (self.invitations_sent.all().aggregate(
                models.Sum('endorsement_weight')).get(
                'endorsement_weight__sum') or 0))

    @property
    @cache_on_object
    def endorsements_remaining(self):
        return max(((self.endorsement_count + 1) * settings.ENDORSEMENT_BONUS -
                    self.endorsements_made_sum), 0)

    @property
    def can_endorse(self):
        return not self.endorsement_limited or self.endorsements_remaining > 0
    
    def trusted_endorsement_sum(self, asker):
        """"
        Returns max flow of endorsements from asker to self across endorsement
        network.
        """
        return ripple.credit_reputation(self, asker)

    def overall_balance(self):
        return ripple.overall_balance(self)

    def trusted_balance(self):
        "Overall balance minus acknowledgements received beyond trusted limits."
        return ripple.trusted_balance(self)

    def trusts(self, profile):
        return self.trusted_profiles.filter(pk=profile.id).count() > 0

    def account(self, profile):
        return ripple.get_account(self, profile)

    def email_str(self):
        """
        Returns '"Name" <email>' suitable for email headers.
        """
        return email_str(self.name, self.email)
    
    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(pk=id)

class Invitation(models.Model):
    from_profile = models.ForeignKey(Profile, related_name='invitations_sent')
    to_email = EmailField("Friend's email")
    endorsement_weight = models.PositiveIntegerField()
    endorsement_text = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    code = VarCharField(unique=True)

    # TODO: Some help text in fields above.

    # TODO: Cron job to delete old invitations?

    def __unicode__(self):
        return u"%s invites %s" % (self.from_profile, self.to_email)

    @models.permalink
    def get_absolute_url(self):
        return 'invitation', (self.code,)

    def set_code(self):
        self.code = ''.join(
            (random.choice(CODE_CHARS) for i in xrange(CODE_LENGTH)))

    def send(self):
        send_mail("%s Has Endorsed You On Villages.cc" % self.from_profile,
                  self.from_profile, self.to_email, 'invitation_email.txt',
                  {'invitation': self, 'domain': settings.SITE_DOMAIN})
        self.date = datetime.now()
        self.save()
        
    @classmethod
    def pre_save(cls, sender, instance, **kwargs):
        if not instance.code:
            instance.set_code()

# Fill in code before saving.
pre_save.connect(Invitation.pre_save, sender=Invitation,
                 dispatch_uid='profile.models')
