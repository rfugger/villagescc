from django import forms

from cc.profile.models import Profile
from cc.general.mail import send_mail_from_system

class EmailUsersForm(forms.Form):
    subject = forms.CharField()
    body = forms.CharField(widget=forms.Textarea)

    def send(self):
        data = self.cleaned_data
        recipients = Profile.objects.filter(settings__send_newsletter=True)

        # TODO: Implement a send_mass_mail that re-uses the same connection
        # to send multiple mails.

        count = 0
        for recipient in recipients.iterator():
            send_mail_from_system(
                data['subject'], recipient, 'newsletter_email.txt',
                {'body': data['body']})
            count += 1
        return count
