from django import forms

from cc.post.models import Post

class PostSearchForm(forms.Form):
    q = forms.CharField(required=False)

    def get_results(self):
        query_text = self.cleaned_data['q']
        if not query_text.strip():
            return []
        results = Post.objects.all().order_by('-date').extra(
            where=["to_tsvector(text) @@ plainto_tsquery(%s)"],
            params=[query_text])
        return results
