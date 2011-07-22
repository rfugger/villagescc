from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from cc.general.util import render
from cc.post.models import Post
from cc.post.forms import PostForm
from cc.geo.util import location_required
from cc.profile.util import profile_location_required
from cc.feed.models import FeedItem

@login_required
@profile_location_required
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
def posts(request):
    posts = FeedItem.objects.get_feed(
        request.profile, radius=None, item_type_filter=Post)
    return locals()    

@render('post.html')
def view_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return locals()
