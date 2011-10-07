from django import forms

from cc.general.models import EmailField
from cc.general.mail import send_mail_to_admin, email_str

class FeedbackForm(forms.Form):
    feedback = forms.CharField(widget=forms.Textarea)

    def get_sender(self):
        return NotImplementedError  # Implement in subclasses.

    def send(self):
        send_mail_to_admin(
            "Villages.cc Feedback", self.get_sender(), 'feedback_email.txt',
            {'feedback': self.cleaned_data['feedback']})
    
class AnonymousFeedbackForm(FeedbackForm):
    name = forms.CharField(required=False)
    email = forms.EmailField(max_length=EmailField.MAX_EMAIL_LENGTH)

    def get_sender(self):
        data = self.cleaned_data
        return email_str(data.get('name'), data['email'])
    
AnonymousFeedbackForm.base_fields.keyOrder = ['name', 'email', 'feedback']

class UserFeedbackForm(FeedbackForm):
    def __init__(self, profile, *args, **kwargs):
        self.profile = profile
        super(UserFeedbackForm, self).__init__(*args, **kwargs)

    def get_sender(self):
        return self.profile
