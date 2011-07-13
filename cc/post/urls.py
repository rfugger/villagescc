from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.post.views',
    url(r'^$', 'home', name='home'),
    url(r'^posts/new/$', 'edit_post', name='new_post'),
    url(r'^posts/$', 'posts', name='posts'),
    url(r'^posts/(\d+)/$', 'view_post', name='view_post'),
    url(r'^posts/(\d+)/edit/$', 'edit_post', name='edit_post'),
)
