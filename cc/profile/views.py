from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from cc.general.util import render
from cc.profile.forms import RegistrationForm, ProfileForm
from cc.profile.models import Profile
from cc.feed.models import FeedItem

MESSAGES = {
    'profile_saved': "Profile saved.",
}

@render()
def register(request):
    if 'done' in request.GET:
        return {}, 'register_done.html'
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('?done=1')
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
        request.profile, radius=None, item_type_filter=Profile)
    return locals()

@render()
def profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    endorsements = profile.endorsements_made.all()
    if request.profile:
        my_endorsement = request.profile.endorsement_for(profile)
    return locals()
        
    
