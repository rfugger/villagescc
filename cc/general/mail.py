from django.core.mail import EmailMessage
from django.template import loader, Context
from django.conf import settings
from django.core.validators import validate_email
from django import forms
from django.utils import translation

def send_mail(subject, sender, recipient, template, context):
    """
    Takes email subject, sender profile or (name, email) tuple, recipient
    profile or email, and template/context pair for the body, and sends an
    email.
    """
    old_language = translation.get_language()
    if not isinstance(recipient, basestring):
	translation.activate(recipient.settings.language)

    context.update({'domain': settings.SITE_DOMAIN})
    body = loader.render_to_string(
        template, context, context_instance=Context(autoescape=False))
    sender_name, sender_email = split_name_email(sender)
    to_email_str = make_email(recipient)

    # Set headers SPF/DKIM/SenderID validation.
    # Email from DEFAULT_FROM_EMAIL, Reply-to sender's email.
    from_email_str = email_str(sender_name, settings.DEFAULT_FROM_EMAIL)
    headers = {'Reply-To': email_str(sender_name, sender_email)}
    
    msg = EmailMessage(subject=subject, body=body, from_email=from_email_str,
                       to=(to_email_str,), headers=headers)
    msg.send()

    translation.activate(old_language)

    # TODO: Queue email for sending by worker process.
    
    # TODO: Relay bounces back to original sender?  See
    # http://www.openspf.org/svn/software/php-mail-bounce/trunk/mail-bounce.php

def send_mail_to_admin(subject, sender, template, context):
    recipient = settings.MANAGERS[0][1]
    send_mail(subject, sender, recipient, template, context)
    
def send_notification(subject, sender, recipient, template, context):
    "Sends mail only if recipient has notifications on."
    if recipient.settings.send_notifications:
        send_mail(subject, sender, recipient, template, context)

def send_mail_from_system(subject, recipient, template, context):
    send_mail(subject, ("Villages.cc", settings.DEFAULT_FROM_EMAIL),
              recipient, template, context)

def split_name_email(profile_or_tuple):
    from cc.profile.models import Profile
    if isinstance(profile_or_tuple, Profile):
        return unicode(profile_or_tuple), profile_or_tuple.email
    else:
        return profile_or_tuple
    
def make_email(email_or_profile):
    "Returns email string from email string or profile input."
    if isinstance(email_or_profile, basestring):
        return email_or_profile
    else:
        # Create email from Profile.        
        return email_or_profile.email_str()
    
def email_str(name, email):
    """
    Returns '"Name" <email>' suitable for email headers.  "Name" is excluded
    if it is blank or None.
    """
    
    # TODO: Consider security implications here (is escaping needed?).
    
    if name:
        return u'"%s" <%s>' % (name, email)
    else:
        return email

def is_valid_email(email):
    try:
        validate_email(email)
    except forms.ValidationError:
        return False
    else:
        return True
