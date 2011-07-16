from django import forms
from django.contrib.auth.forms import UserCreationForm

from cc.profile.models import Profile
from cc.general.models import EmailField

class RegistrationForm(UserCreationForm):
    # Parent class has username, password1, and password2.
    name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(max_length=EmailField.MAX_EMAIL_LENGTH)

    def save(self):
        data = self.cleaned_data
        user = super(RegistrationForm, self).save(commit=False)
        # TODO: Reactivate this line when confirmation emails are implemented.
        #user.is_active = False
        user.save()
        # Profile is auto-created when User is saved.
        profile = user.get_profile()
        profile.name = data.get('name', '')
        profile.email = data['email'] 
        profile.save()

RegistrationForm.base_fields.keyOrder = [
    'username', 'name', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user', 'location', 'endorsements_remaining')
        
