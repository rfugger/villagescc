from django import forms

from cc.post.models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('user', 'date', 'deleted', 'location')

    def save(self, user_profile=None):
        post = super(PostForm, self).save(commit=False)
        if not self.instance.id:
            post.user = user_profile
            post.location = user_profile.location
        post.save()
        return post
