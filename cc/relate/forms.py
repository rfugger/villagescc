from decimal import Decimal as D

from django import forms

from cc.ripple import PRECISION, SCALE
import cc.ripple.api as ripple
from cc.feed.models import FeedItem

# TODO: Move to cc.promise app?
class PromiseForm(forms.Form):
    ripple = forms.ChoiceField(
        choices=((True, 'Routed Promise'), (False, 'Personal Promise')),
        widget=forms.RadioSelect)
    amount = forms.DecimalField(
        max_digits=PRECISION, decimal_places=SCALE,
        min_value=D('0.' + '0' * (SCALE - 1) + '1'))
    memo = forms.CharField(required=False, widget=forms.Textarea)
    
    ERRORS = {
        'max_ripple': ("This is higher than the maximum possible routed "
                       "promise amount."),
    }
    
    def __init__(self, *args, **kwargs):
        self.max_ripple = kwargs.pop('max_ripple')
        super(PromiseForm, self).__init__(*args, **kwargs)
        if self.max_ripple == 0:
            del self.fields['ripple']

    def clean(self):
        data = self.cleaned_data
        # Enforce max_ripple amount.
        if data.get('ripple'):
            if data['amount'] > self.max_ripple:
                self._errors['amount'] = self.error_class(
                    [self.ERRORS['max_ripple']])
        return data

    def send_promise(self, payer, recipient):
        data = self.cleaned_data
        routed = data.get('ripple', False)
        obj = ripple.pay(
            payer, recipient, data['amount'], data['memo'], routed=routed)
        # Create feed item
        FeedItem.create_feed_items(
            sender=RipplePayment, instance=obj, created=True)
        
