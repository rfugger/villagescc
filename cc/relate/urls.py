from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.relate.views',
    url(r'^$', 'relationships', name='relationships'),
)
