from decimal import Decimal as D

from django import forms
from django.core import validators

from cc.relate.models import Endorsement
from cc.ripple import PRECISION, SCALE
import cc.ripple.api as ripple
from cc.feed.models import FeedItem

ROUTED = 'routed'
DIRECT = 'direct'

class EndorseForm(forms.ModelForm):
    MESSAGES = {
        'over_weight': "Please ensure this number is below %d."
    }
    
    class Meta:
        model = Endorsement
        exclude = ('endorser', 'recipient', 'updated')

    def __init__(self, *args, **kwargs):
        self.endorser = kwargs.pop('endorser')
        self.recipient = kwargs.pop('recipient')
        super(EndorseForm, self).__init__(*args, **kwargs)
        self.fields['weight'].widget = (
            forms.TextInput(attrs={'class': 'int spinner'}))
        self.fields['weight'].min_value = 1

    @property
    def max_weight(self):
        if not self.endorser.endorsement_limited:
            return None
        max_weight = self.endorser.endorsements_remaining
        if self.instance.id:
            max_weight += self.instance.weight
        return max_weight
        
    def clean_weight(self):
        weight = self.cleaned_data['weight']
        if self.endorser.endorsement_limited and weight > self.max_weight:
            raise forms.ValidationError(
                self.MESSAGES['over_weight'] % self.max_weight)
        return weight
    
    def save(self):
        endorsement = super(EndorseForm, self).save(commit=False)
        if not self.instance.id:
            endorsement.endorser = self.endorser
            endorsement.recipient = self.recipient
        endorsement.save()
        return endorsement

class AcknowledgementForm(forms.Form):
    ripple = forms.ChoiceField(
        label="Send as",
        choices=((ROUTED, 'Routed acknowledgement'),
                 (DIRECT, 'Direct acknowledgement')),
        widget=forms.RadioSelect)
    amount = forms.DecimalField(
        label="Hours",
        max_digits=PRECISION, decimal_places=SCALE,
        min_value=D('0.' + '0' * (SCALE - 1) + '1'))
    memo = forms.CharField(required=False, widget=forms.Textarea)
    
    ERRORS = {
        'max_ripple': ("This is higher than the maximum possible routed "
                       "acknowledgement amount."),
    }
    
    def __init__(self, *args, **kwargs):
        self.max_ripple = kwargs.pop('max_ripple')
        super(AcknowledgementForm, self).__init__(*args, **kwargs)
        if self.max_ripple == 0:
            del self.fields['ripple']

    def clean(self):
        data = self.cleaned_data
        # Enforce max_ripple amount.
        if data.get('ripple') == ROUTED:
            if data['amount'] > self.max_ripple:
                self._errors['amount'] = self.error_class(
                    [self.ERRORS['max_ripple']])
        return data

    def send_acknowledgement(self, payer, recipient):
        data = self.cleaned_data
        routed = data.get('ripple') == ROUTED
        obj = ripple.pay(
            payer, recipient, data['amount'], data['memo'], routed=routed)
        # Create feed item
        FeedItem.create_feed_items(
            sender=ripple.RipplePayment, instance=obj, created=True)
        return obj
        
