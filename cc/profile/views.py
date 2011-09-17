from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.views import login as django_login_view
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import PasswordChangeForm

from cc.general.util import render, deflect_logged_in
from cc.profile.forms import (
    RegistrationForm, ProfileForm, ContactForm, SettingsForm)
from cc.profile.models import Profile
from cc.post.models import Post
import cc.ripple.api as ripple
from cc.geo.util import location_required
from cc.geo.models import Location
from cc.relate.models import Endorsement
from cc.feed.views import feed

MESSAGES = {
    'profile_saved': "Profile saved.",
    'contact_sent': "Message sent.",
    'registration_done': ("Thank you for registering.  Please continue filling "
                          "out your profile by uploading a photo and describing "
                          "yourself for other users."),
    'password_changed': "Password changed.",
    'settings_changed': "Settings saved.",
}

@deflect_logged_in
@location_required
@render()
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save(request.location)
            # Auto login.
            user = authenticate(username=form.username, password=form.password)
            django_login(request, user)
            Location.clear_session(request)  # Location is in profile now.
            messages.info(request, MESSAGES['registration_done'])

            # TODO: Maybe validate email before allowing posts?
            
            return redirect(edit_profile)
    else:
        form = RegistrationForm()
    return locals()

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
@render()
def settings(request):
    if request.method == 'POST':
        if 'change_settings' in request.POST:
            settings_form = SettingsForm(request.POST, instance=request.profile)
            if settings_form.is_valid():
                settings_form.save()
                messages.info(request, MESSAGES['settings_changed'])
                return redirect(settings)
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.info(request, MESSAGES['password_changed'])
                return redirect(settings)
        
    if 'change_settings' not in request.POST:
        settings_form = SettingsForm(instance=request.profile)
    if 'change_password' not in request.POST:
        password_form = PasswordChangeForm(request.user)
    return locals()

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
    profile = get_object_or_404(Profile, user__username=username)
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
