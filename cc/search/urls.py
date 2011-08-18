from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'cc.search.views',
    url(r'^posts/$', 'search_posts', name='search_posts'),
    url(r'^profiles/$', 'search_profiles', name='search_profiles'),
)
