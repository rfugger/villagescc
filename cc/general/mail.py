from django.core.mail import EmailMessage
from django.template import loader
from django.conf import settings

def send_mail(subject, sender, recipient, template, context):
    """
    Takes email subject, sender profile, recipient profile or email,
    and template/context pair for the body, and sends an email.
    """
    body = loader.render_to_string(template, context)
    
    # TODO: Consider security implications of putting profile name directly
    # into email address below (is escaping needed?)
    from_email = '"%s" <%s>' % (sender.name, sender.email)
    if isinstance(recipient, basestring):
        to_email = recipient
    else:
        # recipient is a Profile.
        to_email = '"%s" <%s>' % (recipient.name, recipient.email)

    # Set headers to avoid SPF errors as per
    # http://www.openspf.org/Best_Practices/Webgenerated
    headers = {'Sender': settings.DEFAULT_FROM_EMAIL}
    msg = EmailMessage(subject=subject, body=body, from_email=from_email,
                       to=(to_email,), headers=headers)
    msg.send()

    # TODO: Queue email for sending by worker process.
    
    # TODO: Relay bounces back to original sender?  See
    # http://www.openspf.org/svn/software/php-mail-bounce/trunk/mail-bounce.php

    
