from django.contrib.auth.decorators import login_required

from cc.feed.models import FeedItem
from cc.general.util import render
from cc.ripple.api import RipplePayment

@login_required
@render()
def promises(request):
    promises = FeedItem.objects.get_feed(
        request.profile, radius=None, item_type_filter=RipplePayment)
    return locals()    

