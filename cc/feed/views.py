from django.db.models import Q

from cc.feed.models import FeedItem, MODEL_TYPES
from cc.general.util import render

@render()
def feed(request):
    if request.profile:
        item_ids = FeedItem.objects.filter(
            Q(user=request.profile) | Q(user=None))
    else:
        item_ids = FeedItem.objects.filter(user=None)
    item_ids = item_ids.values_list(
        'item_type', 'item_id').distinct().order_by('-date')
    feed_items = load_feed_items(item_ids)
    return locals()

def load_feed_items(item_ids):
    """
    Returns a list of actual model objects from a list of tuples
    (item_type, item_id).
    """
    feed_items = []
    for item_type, item_id in item_ids:
        model = MODEL_TYPES[item_type]
        try:
            obj = model.objects.get(pk=item_id)
        except model.DoesNotExist:
            # Feed items have no referential integrity in the db,
            # so catch cases where item_id is gone.
            pass
        else:
            feed_items.append(obj)
    return feed_items
        
