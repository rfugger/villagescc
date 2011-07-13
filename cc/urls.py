import sys

from django.conf.urls.defaults import patterns, url, include
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'', include('cc.geo.urls')),
    (r'', include('cc.profile.urls')),
    (r'', include('cc.post.urls')),
    (r'^endorse/', include('cc.endorse.urls')),
    (r'^admin/', include(admin.site.urls)),
)

# Handle user-uploaded media for dev server.
if 'runserver' in sys.argv:
    urlpatterns += patterns(
        '',
        url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
