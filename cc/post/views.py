from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from cc.general.util import render
from cc.post.models import Post
from cc.post.forms import PostForm
from cc.geo.util import location_required
from cc.feed.models import FeedItem
from cc.profile.forms import ContactForm

MESSAGES = {
    'post_message_sent': _("Message sent."),
}

@login_required
@render('post_form.html')
def edit_post(request, post_id=None):
    if post_id is not None:
        post = get_object_or_404(Post, pk=post_id)
    else:
        post = None
    if request.method == 'POST':
        if post and 'delete' in request.POST:
            post.delete()
            return redirect('posts')
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
        # Process contact form if submitted.
        if request.method == 'POST':
            contact_form = ContactForm(request.POST)
            if contact_form.is_valid():
                contact_form.send(
                    sender=request.profile, recipient=post.user,
                    subject=_("Villages.cc message "
                              "from %(from)s Re: %(title)s") % {
				    'from': request.profile,
				    'title': post.title},
                    template='post_contact_email.txt',
                    extra_context={'post': post})
                messages.info(request, MESSAGES['post_message_sent'])
                return HttpResponseRedirect('.')
        else:
            contact_form = ContactForm()
        template = 'post.html'
        profile = post.user  # For profile_base.html.
    return locals(), template

