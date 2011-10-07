from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template

urlpatterns = patterns(
    'cc.pages.views',
    url(r'^$', 'intro', name='home'),
    url(r'^feedback/$', 'feedback', name='feedback'),
    url(r'^about/$', direct_to_template, {'template': 'about.html'},
        name='about'),
    url(r'^about/ripple/$', direct_to_template,
        {'template': 'about_ripple.html'}, name='about_ripple'),
)
