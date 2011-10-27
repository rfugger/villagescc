from django.core.mail import EmailMessage
from django.template import loader, Context
from django.conf import settings

def send_mail(subject, sender, recipient, template, context):
    """
    Takes email subject, sender profile or email, recipient profile or email,
    and template/context pair for the body, and sends an email.
    """
    context.update({'domain': settings.SITE_DOMAIN})
    body = loader.render_to_string(
        template, context, context_instance=Context(autoescape=False))
    from_email = make_email(sender)
    to_email = make_email(recipient)

    # Set headers to avoid SPF errors as per
    # http://www.openspf.org/Best_Practices/Webgenerated
    headers = {'Sender': settings.DEFAULT_FROM_EMAIL}
    msg = EmailMessage(subject=subject, body=body, from_email=from_email,
                       to=(to_email,), headers=headers)
    msg.send()

    # TODO: Queue email for sending by worker process.
    
    # TODO: Relay bounces back to original sender?  See
    # http://www.openspf.org/svn/software/php-mail-bounce/trunk/mail-bounce.php

def send_mail_to_admin(subject, sender, template, context):
    "Send mail to first listed manager."
    recipient = settings.MANAGERS[0][1]
    from cc.profile.models import Profile
    if isinstance(sender, Profile):
        subject = u"%s (from user: %s)" % (subject, sender.username)
    send_mail(subject, sender, recipient, template, context)

def send_notification(subject, sender, recipient, template, context):
    "Sends mail only if recipient has notifications on."
    if recipient.settings.send_notifications:
        send_mail(subject, sender, recipient, template, context)

def send_mail_from_system(subject, recipient, template, context):
    sender = u'"Villages.cc" <%s>' % settings.DEFAULT_FROM_EMAIL
    send_mail(subject, sender, recipient, template, context)
        
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
