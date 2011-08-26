from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login

from cc.general.util import render
from cc.profile.forms import RegistrationForm, ProfileForm, ContactForm
from cc.profile.models import Profile
from cc.feed.models import FeedItem
from cc.post.models import Post
import cc.ripple.api as ripple
from cc.geo.util import location_required
from cc.geo.models import Location

MESSAGES = {
    'profile_saved': "Profile saved.",
    'contact_sent': "Message sent.",
    'registration_done': ("Thank you for registering.  Please continue filling "
                          "out your profile by uploading a photo and describing "
                          "yourself for other users."),
}

@location_required
@render()
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save(request.location)
            # Auto login.
            user = authenticate(username=form.username, password=form.password)
            login(request, user)
            Location.clear_session(request)  # Location is in profile now.
            messages.info(request, MESSAGES['registration_done'])

            # TODO: Maybe validate email before allowing posts?
            
            return redirect(edit_profile)
    else:
        form = RegistrationForm()
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
def profiles(request):
    profiles = FeedItem.objects.get_feed(
        request.profile, request.location, item_type_filter=Profile)
    return locals()

@render()
def profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    if request.profile:
        my_endorsement = request.profile.endorsement_for(profile)
    if profile == request.profile:
        template = 'my_profile.html'
    else:
        template = 'profile.html'
    return locals(), template

# TODO: Move to post app?
@render()
def profile_posts(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    posts = profile.posts.order_by('-date')
    if profile == request.profile:
        template = 'my_posts.html'
    else:
        template = 'profile_posts.html'    
    return locals(), template

# TODO: Move to relate app?
@render()
def profile_endorsements(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    endorsements = profile.endorsements_received.order_by('-updated')
    trusted_endorsement_sum = profile.trusted_endorsement_sum(request.profile)
    return locals()

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
