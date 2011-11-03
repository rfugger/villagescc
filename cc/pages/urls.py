from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template, redirect_to

urlpatterns = patterns(
    'cc.pages.views',
    url(r'^$', 'intro', name='home'),
    url(r'^feedback/$', 'feedback', name='feedback'),
    url(r'^about/$', redirect_to, {'url': '/about/motivation/'}, name='about'),
    url(r'^about/how/$', direct_to_template,
        {'template': 'how_it_works.html'}, name='how_it_works'),
    url(r'^about/privacy/$', direct_to_template,
        {'template': 'privacy.html'}, name='privacy'),
    url(r'^about/motivation/$', direct_to_template,
        {'template': 'motivation.html'}, name='motivation'),
    url(r'^about/developers/$', direct_to_template,
        {'template': 'developers.html'}, name='developers'),
    url(r'^about/donate/$', direct_to_template,
        {'template': 'donate.html'}, name='donate'),
)
