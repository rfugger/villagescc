from cc.feed.models import FeedItem
from cc.general.util import render
from cc.geo.util import location_required

@location_required
@render()
def feed(request):
    page = request.GET.get('p', 1)
    feed_items = FeedItem.objects.get_feed(
        request.profile, request.location, page=page)
    return locals()

        
