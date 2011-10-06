from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

from cc.profile.models import Profile, Invitation
from cc.general.models import EmailField
from cc.general.mail import send_mail

class RegistrationForm(UserCreationForm):
    # Parent class has username, password1, and password2.
    name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(max_length=EmailField.MAX_EMAIL_LENGTH)

    def clean_email(self):
        email = self.cleaned_data['email']
        if Profile.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "That email address is registered to another user.")
        return email    
    
    def save(self, location):

        # TODO: Test registration.
        
        data = self.cleaned_data
        user = super(RegistrationForm, self).save(commit=False)
        user.save()
        profile = Profile(name=data.get('name', ''), email=data['email'])
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

class InvitationForm(forms.ModelForm):
    endorsement_weight = forms.IntegerField(
        label="Endorsement hearts", min_value=1,
        widget=forms.TextInput(attrs={'class': 'int spinner'}))

    # TODO: Merge with EndorseForm somehow, into a common superclass?
    
    MESSAGES = {
        'over_weight': "Please ensure this number is below %d."
    }
    
    class Meta:
        model = Invitation
        fields = ('to_email', 'endorsement_weight', 'endorsement_text')

    def __init__(self, from_profile, *args, **kwargs):
        self.from_profile = from_profile
        super(InvitationForm, self).__init__(*args, **kwargs)
        
    def clean_to_email(self):
        to_email = self.cleaned_data['to_email']
        if Invitation.objects.filter(
            from_profile=self.from_profile, to_email__iexact=to_email).exists():
            raise forms.ValidationError(
                "You have already invited %s." % to_email)
        if to_email.lower() == self.from_profile.email.lower():
            raise forms.ValidationError("You can't invite yourself.")
        return to_email

    # TODO: Also, create nice spinner for weight like on endorsement form.
    
    @property
    def max_weight(self):
        if not self.from_profile.endorsement_limited:
            return None
        max_weight = self.from_profile.endorsements_remaining
        if self.instance.id:
            max_weight += self.instance.weight
        return max_weight
        
    def clean_endorsement_weight(self):
        weight = self.cleaned_data['endorsement_weight']
        if self.from_profile.endorsement_limited and weight > self.max_weight:
            raise forms.ValidationError(
                self.MESSAGES['over_weight'] % self.max_weight)
        return weight
    
    def save(self):
        invitation = super(InvitationForm, self).save(commit=False)
        invitation.from_profile = self.from_profile
        invitation.save()
        return invitation

class RequestInvitationForm(forms.Form):
    name = forms.CharField(required=False)
    email = forms.EmailField(max_length=EmailField.MAX_EMAIL_LENGTH)
    text = forms.CharField(widget=forms.Textarea, label="Why I want to join")

    def sender(self):
        "Returns appropriate text for email sender field."
        data = self.cleaned_data
        sender = u'<%s>' % data['email']
        if data.get('name'):
            sender = u'"%s" %s' % (data['name'], sender)
        return sender
    
    def send(self):
        data = self.cleaned_data
        send_mail("Villages.cc Invitation Request",
                  self.sender(), settings.MANAGERS[0][1],
                  'request_invitation_email.txt',
                  {'text': data['text']})
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('name', 'photo', 'description')
        
class ContactForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

    def send(self, sender, recipient, subject=None,
             template='contact_email.txt', extra_context=None):
        if not subject:
            subject = "Villages.cc message from %s" % sender
        context = {'message': self.cleaned_data['message']}
        if extra_context:
            context.update(extra_context)
        send_mail(subject, sender, recipient, template, context)
        
class SettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('email',)    

    def __init__(self, profile, *args, **kwargs):
        self.profile = profile
        super(SettingsForm, self).__init__(*args, **kwargs)
        
    def clean_email(self):
        email = self.cleaned_data['email']
        if Profile.objects.filter(email__iexact=email).exclude(
            pk=self.profile.id).exists():
            raise forms.ValidationError(
                "That email address is registered to another user.")
        return email
        
    def save(self):
        self.instance.save(set_updated=False)
        return self.instance
