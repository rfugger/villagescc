from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from cc.general.util import render
from cc.endorse.forms import EndorseForm
from cc.endorse.models import Endorsement
from cc.profile.models import Profile
from cc.feed.models import FeedItem

@login_required
@render()
def endorse_user(request, recipient_id):
    recipient = get_object_or_404(Profile, pk=recipient_id)
    try:
        endorsement = Endorsement.objects.get(
            endorser=request.profile, recipient=recipient)
    except Endorsement.DoesNotExist:
        endorsement = None
    if request.method == 'POST':
        form = EndorseForm(request.POST, instance=endorsement)
        if form.is_valid():
            form.save(endorser=request.profile, recipient=recipient)
            return HttpResponseRedirect(recipient.get_absolute_url())
    else:
        form = EndorseForm(instance=endorsement)
    return locals()

@render()
def endorsements(request):
    endorsements = FeedItem.objects.get_feed(
        request.profile, radius=None, item_type_filter=Endorsement)
    return locals()
    
