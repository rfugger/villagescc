import sys

from django.conf.urls.defaults import patterns, url, include
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

handler500 = 'cc.pages.views.server_error'

urlpatterns = patterns(
    '',
    (r'', include('cc.pages.urls')),
    (r'^feed/', include('cc.feed.urls')),
    (r'', include('cc.geo.urls')),
    (r'', include('cc.profile.urls')),
    (r'^posts/', include('cc.post.urls')),
    (r'', include('cc.relate.urls')),

    (r'^admin/', include('cc.admin.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
)

# Handle user-uploaded media for dev server.
if 'runserver' in sys.argv:
    urlpatterns += patterns(
        '',
        url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
