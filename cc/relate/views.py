from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.db.models import Q

from cc.general.util import render
import cc.ripple.api as ripple
from cc.profile.models import Profile
from cc.relate.forms import EndorseForm, PromiseForm
from cc.relate.models import Endorsement
from cc.feed.models import FeedItem


@login_required
@render()
def endorse_user(request, recipient_username):
    recipient = get_object_or_404(Profile, user__username=recipient_username)
    if recipient == request.profile:
        raise Http404()
    try:
        endorsement = Endorsement.objects.get(
            endorser=request.profile, recipient=recipient)
    except Endorsement.DoesNotExist:
        endorsement = None
    if request.method == 'POST':
        form = EndorseForm(request.POST, instance=endorsement)
        if form.is_valid():
            endorsement = form.save(
                endorser=request.profile, recipient=recipient)
            return HttpResponseRedirect(endorsement.get_absolute_url())
    else:
        form = EndorseForm(instance=endorsement)
    profile = recipient  # For profile_base.html.
    return locals()

@login_required
@render()
def endorsements(request):
    endorsements = FeedItem.objects.get_feed(
        request.profile, location=None, item_type_filter=Endorsement)
    return locals()

@login_required
@render()
def endorsement(request, endorsement_id):
    endorsement = get_object_or_404(
        Endorsement, Q(endorser=request.profile) | Q(recipient=request.profile),
        pk=endorsement_id)
    return locals()
    
@login_required
@render()
def relationships(request):
    # TODO: 'profile' is a required template variable for profile_base.html...
    # Take care of this somewhere else?  Decorator?
    profile = request.profile
    accounts = ripple.get_user_accounts(profile)
    return locals()

@login_required
@render()
def relationship(request, partner_username):
    profile = get_object_or_404(Profile, user__username=partner_username)
    if profile == request.profile:
        raise Http404
    entries = ripple.get_entries_between(request.profile, profile)
    return locals()

@login_required
@render()
def promise_user(request, recipient_username):
    recipient = get_object_or_404(Profile, user__username=recipient_username)
    if recipient == request.profile:
        raise Http404
    # TODO: Don't recompute max_amount on form submit?  Cache, or put in form
    # as hidden field?
    max_amount = ripple.max_payment(request.profile, recipient)
    if request.method == 'POST':
        form = PromiseForm(request.POST, max_ripple=max_amount)
        if form.is_valid():
            promise = form.send_promise(request.profile, recipient)
            return HttpResponseRedirect(promise.get_absolute_url())
    else:
        form = PromiseForm(max_ripple=max_amount)
    can_ripple = max_amount > 0
    profile = recipient  # For profile_base.html.
    return locals()

@login_required
@render()
def promises(request):
    promises = FeedItem.objects.get_feed(
        request.profile, location=None, item_type_filter=ripple.RipplePayment)
    return locals()    

@login_required
@render()
def view_promise(request, payment_id):
    payment = ripple.get_payment(payment_id)
    if request.profile not in (payment.payer, payment.recipient):
        raise Http404
    entries = payment.entries_for_user(request.profile)
    sent_entries = []
    received_entries = []
    for entry in entries:
        if entry.amount < 0:
            sent_entries.append(entry)
        else:
            received_entries.append(entry)
    return locals()

# TODO: View payment from POV of intermediary.
