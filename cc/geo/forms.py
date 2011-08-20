from django import forms

from cc.geo.models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ('neighborhood', 'city', 'state', 'country', 'point')

    set_home = forms.BooleanField(
        required=False, initial=True, label="Save as Home Location")
        
    def __init__(self, *args, **kwargs):
        hide_set_home = kwargs.pop('hide_set_home', False)
        super(LocationForm, self).__init__(*args, **kwargs)
        if hide_set_home:
            del self.fields['set_home']
        self.fields['point'].widget = forms.HiddenInput()
