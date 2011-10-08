from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from cc.feed.views import feed
from cc.relate.models import Endorsement
from cc.ripple.api import RipplePayment

urlpatterns = patterns(
    'cc.relate.views',
    url(r'^endorse/([^/]+)/$', 'endorse_user', name='endorse_user'),
    url(r'^endorsements/$', login_required(feed),
        dict(item_type=Endorsement, template='endorsements.html'),
        name='endorsements'),
    url(r'^endorsements/(\d+)/$', 'endorsement', name='endorsement'),
    url(r'^relationships/$', 'relationships', name='relationships'),
    url(r'^relationships/([^/]+)/$', 'relationship', name='relationship'),
    url(r'^acknowledge/([^/]+)/$', 'acknowledge_user', name='acknowledge_user'),
    url(r'^acknowledgements/$', login_required(feed),
        dict(item_type=RipplePayment, template='acknowledgements.html'),
        name='acknowledgements'),
    url(r'^acknowledgements/(\d+)/$', 'view_acknowledgement',
        name='view_acknowledgement'),
)
