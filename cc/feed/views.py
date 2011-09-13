from cc.general.util import render
from cc.geo.util import location_required
from cc.feed.forms import FeedFilterForm, DATE_FORMAT

@location_required
@render()
def feed(request, item_type=None, template='feed.html', poster=None,
         recipient=None, sticky_prefs=True, extra_context=None):
    """
    Generic view for displaying feed items.

    Set sticky_prefs=False if not showing feed filter form, so
    profile preferences for feed filtering don't get reset to defaults.
    """
    form = FeedFilterForm(
        request.GET, request.profile, request.location, item_type,
        poster, recipient)
    if form.is_valid():
        feed_items, remaining_count = form.get_results()
        if sticky_prefs:
            form.update_sticky_prefs()
    else:
        raise Exception(unicode(form.errors))
    if feed_items:
        next_page_date = feed_items[-1].date
    else:
        next_page_date = None
    url_params = request.GET.copy()
    url_params.pop('d', None)
    url_param_str = url_params.urlencode()
    if next_page_date:
        url_params['d'] = next_page_date.strftime(DATE_FORMAT)
    next_page_param_str = url_params.urlencode()

    context = locals()
    context.update(extra_context or {})
    return context, template
