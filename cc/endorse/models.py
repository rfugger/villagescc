from django.db import models
from django.db.models.signals import post_save

from cc.profile.models import Profile
import cc.ripple.api as ripple

class Endorsement(models.Model):
    endorser = models.ForeignKey(Profile, related_name='endorsements_made')
    recipient = models.ForeignKey(
        Profile, related_name='endorsements_received')
    weight = models.PositiveIntegerField()
    text = models.TextField(blank=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('endorser', 'recipient')

    FEED_TEMPLATE = 'endorsement_feed_item.html'
        
    def __unicode__(self):
        return u'%s endorses %s (%d)' % (
            self.endorser, self.recipient, self.weight)

    @property
    def date(self):
        """
        For FeedItem source interface, returns last updated date as the
        feed item date.
        """
        return self.updated

    @property
    def location(self):
        "For FeedItem source interface.  Endorsements have no location."
        return None

    def get_feed_users(self):
        "Endorsement should show up in endorser's and recipient's feeds."
        return (self.endorser, self.recipient)

    @property
    def feed_poster(self):
        return self.endorser

    def can_edit(self, profile):
        return self.endorser == profile

    @classmethod
    def get_by_id(cls, id):
        return cls.objects.get(pk=id)
    
    @classmethod
    def update_credit_limit(cls, sender, instance, created, **kwargs):
        ripple.update_credit_limit(instance)

# Create new empty profile when a new user is created.
post_save.connect(Endorsement.update_credit_limit, sender=Endorsement,
                  dispatch_uid='endorse.models')
# TODO: Propagate Endorsement delete through to ripple backend using post_delete.
