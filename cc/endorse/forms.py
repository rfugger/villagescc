from django import forms

from cc.endorse.models import Endorsement

class EndorseForm(forms.ModelForm):
    class Meta:
        model = Endorsement
        exclude = ('endorser', 'recipient', 'updated')

    # TODO: Limit weight to endorser.endorsements_remaining.
        
    def save(self, endorser=None, recipient=None):
        endorsement = super(EndorseForm, self).save(commit=False)
        if not self.instance.id:
            endorsement.endorser = endorser
            endorsement.recipient = recipient
        endorsement.save()
        return endorsement
        
