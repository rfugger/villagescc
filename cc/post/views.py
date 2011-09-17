from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from cc.general.util import render
from cc.post.models import Post
from cc.post.forms import PostForm
from cc.geo.util import location_required
from cc.feed.models import FeedItem
from cc.profile.forms import ContactForm

@login_required
@render('post_form.html')
def edit_post(request, post_id=None):
    if post_id is not None:
        post = get_object_or_404(Post, pk=post_id)
    else:
        post = None
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(request.profile)
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)
    return locals()

@render()
def view_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.profile == post.user:
        template = 'my_post.html'
    else:
        template = 'post.html'
        profile = post.user  # For profile_base.html.
        contact_form = ContactForm()
    return locals(), template
