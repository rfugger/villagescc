from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from cc.general.util import render
import cc.ripple.api as ripple
from cc.profile.models import Profile
from cc.relate.forms import PromiseForm

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
    # TODO: 'profile' is a required template variable for profile_base.html...
    # Take care of this somewhere else?  Decorator?
    profile = request.profile
    partner = get_object_or_404(Profile, user__username=partner_username)
    entries = ripple.get_entries_between(profile, partner)
    return locals()

@login_required
@render()
def promise_user(request, recipient_username):
    recipient = get_object_or_404(Profile, user__username=recipient_username)
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
    return locals()
        
        
