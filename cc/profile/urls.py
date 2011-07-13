from django.conf.urls.defaults import patterns, url
from django.contrib.auth.views import login, logout

urlpatterns = patterns(
    'cc.profile.views',
    url(r'^register/$', 'register', name='register'),
    url(r'^login/$', login, name='login', kwargs=dict(
            template_name='login.html', redirect_field_name='next')),
    url(r'^logout/$', logout, name='logout', kwargs=dict(next_page='/')),
    url(r'^profiles/edit/$', 'edit_profile', name='edit_profile'),
    url(r'^profiles/$', 'profiles', name='profiles'),
    url(r'^profiles/([^/]+)/$', 'profile', name='profile'),
)
