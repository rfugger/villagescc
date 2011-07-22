from cc.feed.models import FeedItem
from cc.general.util import render

@render()
def feed(request):
    feed_items = FeedItem.objects.get_feed(request.profile, radius=None)
    return locals()

        
