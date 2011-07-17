from django.db.models import Q

from cc.feed.models import FeedItem
from cc.general.util import render

@render()
def feed(request):
    if request.profile:
        feed_items = FeedItem.objects.filter(
            Q(user=request.profile) | Q(user=None))
    else:
        feed_items = FeedItem.objects.filter(user=None)
    feed_items = feed_items.order_by('-date')
    return locals()
