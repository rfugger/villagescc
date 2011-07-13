from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.geo.views',
    url(r'^locator/$', 'locator', name='locator'),
)
