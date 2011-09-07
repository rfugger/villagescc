#!/usr/bin/env python

from cc.feed.models import FeedItem
from cc.post.models import Post
from cc.profile.models import Profile
from cc.relate.models import Endorsement
from cc.ripple.api import RipplePayment

# TODO: Check for feed item expiry and don't recreate those items.

FeedItem.objects.all().delete()

for model in (Post, Profile, Endorsement):
    for obj in model.objects.all():
        FeedItem.objects.create_from_item(obj)

for pmt in RipplePayment.get_all():
    FeedItem.objects.create_from_item(pmt)

