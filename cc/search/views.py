from cc.general.util import render
from cc.search.forms import PostSearchForm, ProfileSearchForm

@render()
def search_posts(request):
    return _search(request, PostSearchForm)

@render()
def search_profiles(request):
    return _search(request, ProfileSearchForm)

def _search(request, form_class):
    form = form_class(request.GET)
    if form.is_valid():
        # TODO: Paginate results.
        results = form.get_results()
    return locals()
    
