from django import forms

from cc.geo.models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ('neighborhood', 'city', 'state', 'country', 'point')

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.fields['point'].widget = forms.HiddenInput()
