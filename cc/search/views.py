from cc.general.util import render
from cc.search.forms import PostSearchForm

@render()
def search_posts(request):
    form = PostSearchForm(request.GET)
    if form.is_valid():
        results = form.get_results()
    return locals()

@render()
def search_profiles(request):
    return locals()
