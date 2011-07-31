from decimal import Decimal as D

from django import forms

from cc.ripple import PRECISION, SCALE
import cc.ripple.api as ripple

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
        if data.get('ripple'):
            # Routed promise.
            # TODO: Handle errors.
            ripple.pay(payer, recipient, data['amount'], data['memo'])
        else:
            # Direct promise.
            ripple.record_entry(payer, recipient, data['amount'], data['memo'])
        # Create feed item
        # WORKING ON...
