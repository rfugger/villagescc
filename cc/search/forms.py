from django import forms

from cc.post.models import Post
from cc.profile.models import Profile

class SearchForm(forms.Form):
    q = forms.CharField(required=False)
    # TODO: Search within radius of location.
    
    def get_results(self):
        query_text = self.cleaned_data['q']
        if not query_text.strip():
            return []
        results = self._results_query(query_text)
        return results

    def _results_query(self, query_text):
        return []

    def searched(self):
        return len(self.data.keys()) != 0

class PostSearchForm(SearchForm):
    def _results_query(self, query_text):
        return Post.objects.order_by('-date').extra(
            where=["to_tsvector('english', text) @@ plainto_tsquery(%s)"],
            params=[query_text])
    
class ProfileSearchForm(SearchForm):
    TSVECTOR_CLAUSE = ("setweight(to_tsvector('english', name), 'A') || "
                       "setweight(to_tsvector('english', description), 'B')")

    def _results_query(self, query_text):
        return Profile.objects.extra(
            select={'rank': "ts_rank(" + self.TSVECTOR_CLAUSE +
                    ", plainto_tsquery(%s), 32)"},
            select_params=[query_text],
            where=[self.TSVECTOR_CLAUSE + " @@ plainto_tsquery(%s)"],
            params=[query_text],
            order_by=('-rank',))
