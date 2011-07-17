from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.post.views',
    url(r'^$', 'posts', name='posts'),
    url(r'^new/$', 'edit_post', name='new_post'),
    url(r'^(\d+)/$', 'view_post', name='view_post'),
    url(r'^(\d+)/edit/$', 'edit_post', name='edit_post'),
)
