from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.promise.views',
    url(r'^$', 'promises', name='promises'),
)
