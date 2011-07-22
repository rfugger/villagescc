from django.db import models

from cc.profile.models import Profile

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
