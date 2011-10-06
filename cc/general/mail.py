from django.core.mail import EmailMessage
from django.template import loader
from django.conf import settings

def send_mail(subject, sender, recipient, template, context):
    """
    Takes email subject, sender profile, recipient profile or email,
    and template/context pair for the body, and sends an email.
    """
    body = loader.render_to_string(template, context)
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

def make_email(email_or_profile):
    if isinstance(email_or_profile, basestring):
        email = email_or_profile
    else:
        # Create email from Profile.
        
        # TODO: Consider security implications of putting profile name directly
        # into email address below (is escaping needed?)
        
        email = '"%s" <%s>' % (email_or_profile.name, email_or_profile.email)
    return email
    
