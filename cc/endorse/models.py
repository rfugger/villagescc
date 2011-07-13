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
    
    def __unicode__(self):
        return u'%s endorses %s (%d)' % (
            self.endorser, self.recipient, self.weight)
