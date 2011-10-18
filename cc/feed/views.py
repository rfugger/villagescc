from cc.general.util import render
from cc.geo.util import location_required
from cc.feed.forms import FeedFilterForm, DATE_FORMAT

@location_required
@render()
def feed(request, item_type=None, template='feed.html', poster=None,
         recipient=None, extra_context=None, do_filter=False):
    """
    Generic view for displaying feed items.

    Set sticky_prefs=True to save filter choices to profile settings.
    Warning: this will reset them to defaults if the form doesn't
    provide any values for filter choices.
    """
    form = FeedFilterForm(
        request.GET, request.profile, request.location, item_type,
        poster, recipient, do_filter)
    if form.is_valid():
        feed_items, remaining_count = form.get_results()
        if do_filter:
            form.update_sticky_filter_prefs()
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
