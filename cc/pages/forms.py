from django import forms
from django.utils.translation import ugettext_lazy as _

from cc.general.models import EmailField
from cc.general.mail import send_mail_to_admin

class FeedbackForm(forms.Form):
    feedback = forms.CharField(label=_("Feedback"), widget=forms.Textarea)
    
    def get_sender(self):
        return NotImplementedError  # Implement in subclasses.

    def send(self):
        send_mail_to_admin(
            _("Villages.cc Feedback"),
            self.get_sender(), 'feedback_email.txt',
            {'feedback': self.cleaned_data['feedback']})
    
class AnonymousFeedbackForm(FeedbackForm):
    name = forms.CharField(label=_("Name"), required=False)
    email = forms.EmailField(label=_("Email"),
        max_length=EmailField.MAX_EMAIL_LENGTH)

    def get_sender(self):
        data = self.cleaned_data
        return data.get('name'), data['email']
    
AnonymousFeedbackForm.base_fields.keyOrder = ['name', 'email', 'feedback']

class UserFeedbackForm(FeedbackForm):
    def __init__(self, profile, *args, **kwargs):
        self.profile = profile
        super(UserFeedbackForm, self).__init__(*args, **kwargs)

    def get_sender(self):
        return self.profile
