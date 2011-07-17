from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.feed.views',
    url(r'^$', 'feed', name='feed'),
)
