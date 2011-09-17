from django import forms
from django.contrib.auth.forms import UserCreationForm

from cc.profile.models import Profile
from cc.general.models import EmailField

class RegistrationForm(UserCreationForm):
    # Parent class has username, password1, and password2.
    name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(max_length=EmailField.MAX_EMAIL_LENGTH)

    def save(self, location):
        data = self.cleaned_data
        user = super(RegistrationForm, self).save(commit=False)
        # TODO: Reactivate this line when confirmation emails are implemented.
        #user.is_active = False
        user.save()
        # Profile is auto-created when User is saved.
        profile = user.get_profile()
        profile.name = data.get('name', '')
        profile.email = data['email']
        if not location.id:
            location.save()
        profile.location = location
        profile.save()
        return profile

    @property
    def username(self):
        return self.cleaned_data['username']

    @property
    def password(self):
        return self.cleaned_data['password1']

RegistrationForm.base_fields.keyOrder = [
    'username', 'name', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('name', 'photo', 'description')
        
class ContactForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

    def send(self, sender, recipient):
        pass
        
class SettingsForm(forms.ModelForm):
    email = forms.EmailField(max_length=EmailField.MAX_EMAIL_LENGTH)

    class Meta:
        model = Profile
        fields = ('email',)    
        
    def save(self):
        self.instance.save(set_updated=False)
        return self.instance
