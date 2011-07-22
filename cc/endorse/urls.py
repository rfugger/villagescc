from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.endorse.views',
    url(r'^(\d+)/$', 'endorse_user', name='endorse_user'),
    url(r'^$', 'endorsements', name='endorsements'),
)
