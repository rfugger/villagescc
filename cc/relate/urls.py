from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.relate.views',
    url(r'^endorse/([^/]+)/$', 'endorse_user', name='endorse_user'),
    url(r'^endorsements/$', 'endorsements', name='endorsements'),
    url(r'^endorsements/(\d+)/$', 'endorsement', name='endorsement'),
    url(r'^relationships/$', 'relationships', name='relationships'),
    url(r'^relationships/([^/]+)/$', 'relationship', name='relationship'),
    url(r'^promise/([^/]+)/$', 'promise_user', name='promise_user'),
    url(r'^promises/$', 'promises', name='promises'),
    url(r'^promises/(\d+)/$', 'view_promise', name='view_promise'),
)
