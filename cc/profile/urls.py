from django.conf.urls.defaults import patterns, url
from django.contrib.auth.views import logout

from cc.feed.views import feed
from cc.profile.models import Profile

urlpatterns = patterns(
    'cc.profile.views',
    url(r'^check_invitation/$', 'check_invitation', name='check_invitation'),
    url(r'^register/$', 'register', name='register'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', logout, name='logout', kwargs=dict(next_page='/')),
    url(r'^settings/$', 'settings', name='settings'),
    url(r'^profiles/edit/$', 'edit_profile', name='edit_profile'),
    url(r'^profiles/$', feed, dict(item_type=Profile, template='profiles.html'),
        name='profiles'),
    url(r'^profiles/([^/]+)/$', 'profile', name='profile'),
    url(r'^profiles/([^/]+)/posts/$', 'profile_posts', name='profile_posts'),
    url(r'^profiles/([^/]+)/endorsements/$', 'profile_endorsements',
        name='profile_endorsements'),
    url(r'^profiles/([^/]+)/contact/$', 'contact', name='contact'),
    url(r'^invite/$', 'invite', name='invite'),    
    url(r'^invitation/([^/]+)/$', 'invitation', name='invitation'),
)
