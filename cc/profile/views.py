from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.views import login as django_login_view
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied

from cc.general.util import render, deflect_logged_in
from cc.profile.forms import (
    RegistrationForm, ProfileForm, ContactForm, SettingsForm, InvitationForm,
    RequestInvitationForm)
from cc.profile.models import Profile, Invitation
from cc.post.models import Post
import cc.ripple.api as ripple
from cc.geo.util import location_required
from cc.geo.models import Location
from cc.relate.models import Endorsement
from cc.feed.views import feed
from cc.general.mail import send_mail_from_system

# Session key to store invite code for later signing up.
INVITE_CODE_KEY = 'invite_code'

# Session key for profile ID of link sharer.
SHARED_BY_PROFILE_ID_KEY = 'shared_by'

# URL param key for username of link sharer.
SHARED_BY_USERNAME_KEY = 'u'

MESSAGES = {
    'profile_saved': "Profile saved.",
    'contact_sent': "Message sent.",
    'registration_done': ("Thank you for registering.<br><br>"
                          "Please continue filling out your profile by "
                          "uploading a photo and describing yourself for other "
                          "users.<br><br>"
                          "We have sent a welcome email to your address. "
                          "If you do not receive it, please verify your email "
                          "address under account settings."),
    'password_changed': "Password changed.",
    'settings_changed': "Settings saved.",
    'email_updated': ("Settings saved.<br><br>"
                      "A confirmation email has been sent to your new address. "
                      "If you do not receive it, please verify that you have "
                      "entered the correct email."),
    'invitation_sent': "Invitation sent to %s.",
    'invitation_deleted': "Invitation deleted.",
    'invitation_request_sent': "Invitation request sent.",
    'invitation_landing': ("%s has invited you to Villages.cc.<br>"
                           "Please take a look around and then use the "
                           "<em>Join</em> link on the right to register."),
}

def get_invitation(request):
    """
    Get invitation code saved in session by invitation view (shown
    when clicking on invitation link).
    """
    invitation = None
    invite_code = request.session.get(INVITE_CODE_KEY)
    if invite_code:
        try:
            invitation = Invitation.objects.get(code=invite_code)
        except Invitation.DoesNotExist:
            pass
    return invitation

@deflect_logged_in
def check_invitation(request):
    """
    Check for invitation in session before proceeding to registration.
    If no invitation, redirect to request_invitation.
    """
    invitation = get_invitation(request)
    if invitation:
        return redirect(register)
    else:
        return redirect(request_invitation)

@deflect_logged_in
@location_required
@render()
def register(request):
    """
    Registration form.  Requires invitation code in session (from
    invitation view).
    """
    invitation = get_invitation(request)
    if not invitation:
        raise PermissionDenied
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save(request.location)
            # Turn invitation into endorsement.
            Endorsement.objects.create(
                endorser = invitation.from_profile,
                recipient = profile,
                weight = invitation.endorsement_weight,
                text = invitation.endorsement_text)
            invitation.delete()
            # Auto login.
            user = authenticate(username=form.username, password=form.password)
            django_login(request, user)
            Location.clear_session(request)  # Location is in profile now.
            # Notifications.
            send_registration_email(profile)
            messages.info(request, MESSAGES['registration_done'])            
            return redirect(edit_profile)
    else:
        initial = {'email': invitation.to_email}
        form = RegistrationForm(initial=initial)
    return locals()

def send_registration_email(profile):
    subject = "Welcome to Villages.cc"
    send_mail_from_system(subject, profile, 'registration_email.txt',
                          {'profile': profile})

@deflect_logged_in
def login(request):
    response = django_login_view(
        request, template_name='login.html', redirect_field_name='next')
    # Don't redirect to locator view upon login.
    if (isinstance(response, HttpResponseRedirect) and
        response['Location'] == reverse('locator')):
        return redirect('home')
    return response

@login_required
@render('settings.html')
def edit_settings(request):
    if request.method == 'POST':
        if 'change_settings' in request.POST:
            old_email = request.profile.settings.email
            settings_form = SettingsForm(
                request.POST, instance=request.profile.settings)
            if settings_form.is_valid():
                settings_obj = settings_form.save()
                if settings_obj.email != old_email:
                    send_new_address_email(settings_obj)
                    messages.info(request, MESSAGES['email_updated'])
                else:
                    messages.info(request, MESSAGES['settings_changed'])
                return redirect(edit_settings)
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.info(request, MESSAGES['password_changed'])
                return redirect(edit_settings)
        
    if 'change_settings' not in request.POST:
        settings_form = SettingsForm(instance=request.profile.settings)
    if 'change_password' not in request.POST:
        password_form = PasswordChangeForm(request.user)
    return locals()

def send_new_address_email(settings):
    subject = "Your Villages.cc email address has been updated"
    send_mail_from_system(subject, settings.profile, 'new_email.txt',
                          {'new_email': settings.email})

@login_required
@render()
def edit_profile(request):
    profile = request.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.info(request, MESSAGES['profile_saved'])
            return HttpResponseRedirect(profile.get_absolute_url())
    else:
        form = ProfileForm(instance=profile)
    return locals()

@render()
def profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    if profile == request.profile:
        template = 'my_profile.html'
    else:
        template = 'profile.html'
        if request.profile:
            my_endorsement = request.profile.endorsement_for(profile)
            account = profile.account(request.profile)
    return locals(), template

# TODO: Move to post app?
def profile_posts(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    if profile == request.profile:
        template = 'my_posts.html'
        extra_context = {}
    else:
        template = 'profile_posts.html'    
        extra_context = {'profile': profile}
    return feed(request, item_type=Post, poster=profile, template=template,
                extra_context=extra_context)

# TODO: Move to relate app?
@login_required
def profile_endorsements(request, username):
    eligible_profiles = Profile.objects.exclude(pk=request.profile.id)
    profile = get_object_or_404(
        eligible_profiles, user__username=username)
    return feed(request, item_type=Endorsement, recipient=profile,
                template='profile_endorsements.html',
                extra_context={'profile': profile})

@render()
def contact(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.send(sender=request.profile, recipient=profile)
            messages.info(request, MESSAGES['contact_sent'])
            return redirect(profile, (username,))
    else:
        form = ContactForm()
    return locals()

@login_required
@render()
def invite(request):
    if request.method == 'POST':
        form = InvitationForm(request.profile, request.POST)
        if form.is_valid():
            
            # TODO: Check for email belonging to existing user,
            # call endorse_user(request), make sure it works.
            
            invitation = form.save()
            invitation.send()
            messages.info(request, MESSAGES['invitation_sent'] % (
                    invitation.to_email))
            return redirect(invite)
    else:
        initial = {'to_email': request.GET.get('email', '')}
        form = InvitationForm(request.profile, initial=initial)
    return locals()

@deflect_logged_in
@render()
def invitation(request, code):
    """
    Saves invitation code to session so user can register later and
    redirects to intro page with a message reflecting invite.
    """
    try:
        invitation = Invitation.objects.get(code=code)
    except Invitation.DoesNotExist:
        invitation = None
    if invitation is None:
        return {}, 'bad_invite_code.html'

    # TODO: Allow logged in users to convert an invitation to an endorsement.
    
    request.session[INVITE_CODE_KEY] = code
    messages.info(request, MESSAGES['invitation_landing'] % (
            invitation.from_profile))
    return redirect('home')

@login_required
@render()
def invitations_sent(request):
    if request.method == 'POST':
        # Keys of interest in request.POST are be 'resend_NNN' and 'delete_NNN',
        # where NNN is the invitation ID to act on.
        key = None
        for k in request.POST.keys():
            if k.startswith('resend') or k.startswith('delete'):
                key = k
                break
        if key is None:
            raise Exception("Missing resend or delete paramter.")
        invitation_id = key.split('_')[1]
        invitation = get_object_or_404(
            request.profile.invitations_sent, pk=invitation_id)
        if key.startswith('resend'):
            invitation.send()
            messages.info(request, MESSAGES['invitation_sent'] %
                          invitation.to_email)
        elif key.startswith('delete'):
            invitation.delete()
            messages.info(request, MESSAGES['invitation_deleted'])
        return redirect(invitations_sent)
    invitations = request.profile.invitations_sent.all()
    return locals()

@deflect_logged_in
@render()
def request_invitation(request):
    if request.method == 'POST':
        form = RequestInvitationForm(request.POST)
        if form.is_valid():
            to_profile = get_shared_by_profile(request)
            form.send(to_profile)
            messages.info(request, MESSAGES['invitation_request_sent'])
            return redirect('home')
    else:
        form = RequestInvitationForm()
    return locals()

def get_shared_by_profile(request):
    profile = None
    if SHARED_BY_PROFILE_ID_KEY in request.session:
        try:
            profile = Profile.objects.get(
                pk=request.session[SHARED_BY_PROFILE_ID_KEY])
        except Profile.DoesNotExist:
            pass
    return profile

@login_required
@render()
def share(request):
    return locals()
