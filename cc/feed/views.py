from cc.general.util import render
from cc.geo.util import location_required
from cc.feed.forms import FeedFilterForm

@location_required
@render()
def feed(request, item_type=None, template='feed.html'):
    form = FeedFilterForm(request.GET, request.profile)
    if form.is_valid():
        feed_items = form.get_results(
            request.profile, request.location, item_type)
    else:
        feed_items = []
        
    # TODO: Make it so clicking different item type filter keeps filter form
    # fields intact.
        
    return locals(), template

        
