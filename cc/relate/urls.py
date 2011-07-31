from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.relate.views',
    url(r'^relationships/$', 'relationships', name='relationships'),
    url(r'^relationships/([^/]+)/$', 'relationship', name='relationship'),
    url(r'^acknowledge/([^/]+)/$', 'acknowledge_user', name='acknowledge_user'),
)
