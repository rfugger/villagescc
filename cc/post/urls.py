from django.conf.urls.defaults import patterns, url

from cc.feed.views import feed
from cc.post.models import Post

urlpatterns = patterns(
    'cc.post.views',
    url(r'^$', feed, dict(item_type=Post, template='posts.html'), name='posts'),
    url(r'^new/$', 'edit_post', name='new_post'),
    url(r'^(\d+)/$', 'view_post', name='view_post'),
    url(r'^(\d+)/edit/$', 'edit_post', name='edit_post'),
)
