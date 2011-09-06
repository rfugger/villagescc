from django.conf.urls.defaults import patterns, url
from django.contrib.auth.views import login, logout

from cc.feed.views import feed
from cc.profile.models import Profile

urlpatterns = patterns(
    'cc.profile.views',
    url(r'^register/$', 'register', name='register'),
    url(r'^login/$', login, name='login', kwargs=dict(
            template_name='login.html', redirect_field_name='next')),
    url(r'^logout/$', logout, name='logout', kwargs=dict(next_page='/')),
    url(r'^profiles/edit/$', 'edit_profile', name='edit_profile'),
    url(r'^profiles/$', feed, dict(item_type=Profile, template='profiles.html'),
        name='profiles'),
    url(r'^profiles/([^/]+)/$', 'profile', name='profile'),
    url(r'^profiles/([^/]+)/posts/$', 'profile_posts', name='profile_posts'),
    url(r'^profiles/([^/]+)/endorsements/$', 'profile_endorsements',
        name='profile_endorsements'),
    url(r'^profiles/([^/]+)/contact/$', 'contact', name='contact'),

    # TODO: Change password view.
)
