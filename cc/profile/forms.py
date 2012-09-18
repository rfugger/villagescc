from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from cc.profile.models import (
    Profile, Invitation, Settings, PasswordResetLink)
from cc.general.models import EmailField
from cc.general.mail import send_mail, send_mail_to_admin

ERRORS = {
    'email_dup': _("That email address is registered to another user."),
    'already_invited': _("You have already sent an invitation to %s."),
    'self_invite': _("You can't invite yourself."),
    'over_weight': _("Please ensure this number is below %d."),
    'invalid_username': _("That username or email isn't recognized."),
}

class RegistrationForm(UserCreationForm):
    # Parent class has username, password1, and password2.
    name = forms.CharField(
        max_length=100, required=False, label=_("Name"), help_text=_(
            "Name displayed to other users. You can change this later."))
    email = forms.EmailField(
        max_length=EmailField.MAX_EMAIL_LENGTH, label=_("Email"), help_text=_(
            "The address to receive notifications from Villages."))

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = _(
            "Desired login name. You cannot change this.")
        self.fields['password1'].help_text = _("Desired password.")
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if Settings.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(ERRORS['email_dup'])
        return email    

    def clean_username(self):
        # Adapted from UserCreationForm.clean_username.
        # Make username uniqueness check case-insensitive.
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            _("A user with that username already exists."))
    
    def save(self, location, language):
        data = self.cleaned_data
        user = super(RegistrationForm, self).save(commit=False)
        user.save()
        profile = Profile(user=user, name=data.get('name', ''))
        if not location.id:
            location.save()
        profile.location = location
        profile.save()
        profile.settings.email = data['email']
        profile.settings.language = language
        profile.settings.save()
        return profile

    @property
    def username(self):
        return self.cleaned_data['username']

    @property
    def password(self):
        return self.cleaned_data['password1']

RegistrationForm.base_fields.keyOrder = [
    'name', 'email', 'username', 'password1', 'password2']

class ForgotPasswordForm(forms.Form):
    username_or_email = forms.CharField(label=_("Username or email"))

    def clean_username_or_email(self):
        """
        If username or email is known to the system, set self.profile to
        appropriate value.  If username or email is unknown, and raise
        ValidationError.
        """
        username_or_email = self.cleaned_data['username_or_email']
        try:
            user = User.objects.get(username__iexact=username_or_email)
            self.profile = user.profile
        except User.DoesNotExist:
            try:
                self.profile = Profile.objects.get(
                    settings__email__iexact=username_or_email)
            except Profile.DoesNotExist:
                raise forms.ValidationError(ERRORS['invalid_username'])
        return username_or_email

    def create_reset_link(self):
        link = PasswordResetLink(profile=self.profile)
        link.save()
        link.send()

class InvitationForm(forms.ModelForm):
    # TODO: Merge with EndorseForm somehow, into a common superclass?
    
    class Meta:
        model = Invitation
        fields = ('to_email', 'message', 'endorsement_weight',
                  'endorsement_text')

    def __init__(self, from_profile, *args, **kwargs):
        self.from_profile = from_profile
        super(InvitationForm, self).__init__(*args, **kwargs)
        self.fields['endorsement_weight'].widget = (
            forms.TextInput(attrs={'class': 'int spinner'}))
        self.fields['endorsement_weight'].min_value = 1        
        
    def clean_to_email(self):
        to_email = self.cleaned_data['to_email']
        if Invitation.objects.filter(
            from_profile=self.from_profile, to_email__iexact=to_email).exists():
            raise forms.ValidationError(ERRORS['already_invited'] % to_email)
        if to_email.lower() == self.from_profile.email.lower():
            raise forms.ValidationError(ERRORS['self_invite'])
        return to_email

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
                ERRORS['over_weight'] % self.max_weight)
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
        return data.get('name'), data['email']
    
    def send(self, to_profile=None):
        data = self.cleaned_data
        subject = "Villages.cc Invitation Request"
        context = {'text': data['text'],
                   'email': data['email']}
        if to_profile:
            send_mail(subject, self.sender(), to_profile,
                      'request_invitation_email.txt', context)
        else:
            send_mail_to_admin(
                subject, self.sender(), 'request_invitation_email.txt', context)
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('name', 'photo', 'description')

    def save(self):
        self.instance.set_updated()
        return super(ProfileForm, self).save()
        
class ContactForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

    def send(self, sender, recipient, subject=None,
             template='contact_email.txt', extra_context=None):
        if not subject:
            subject = _("Villages.cc message from %s") % sender
        context = {'message': self.cleaned_data['message'],
                   'sender': sender}
        if extra_context:
            context.update(extra_context)
        send_mail(subject, sender, recipient, template, context)
        
class SettingsForm(forms.ModelForm):
    # Email is required.
    email = forms.EmailField(max_length=EmailField.MAX_EMAIL_LENGTH)

    class Meta:
        model = Settings
        fields = ('email', 'endorsement_limited',
                  'send_notifications', 'send_newsletter', 'language')

    def clean_email(self):
        email = self.cleaned_data['email']
        if Settings.objects.filter(email__iexact=email).exclude(
            pk=self.instance.id).exists():
            raise forms.ValidationError(ERRORS['email_dup'])
        return email
