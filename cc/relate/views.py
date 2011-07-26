from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from cc.general.util import render
import cc.ripple.api as ripple

@login_required
@render()
def relationships(request):
    profile = request.profile
    accounts = ripple.get_user_accounts(profile)
    return locals()
