#!/usr/bin/env python

from cc.feed.models import FeedItem

for feed_item in FeedItem.objects.iterator():
    if not feed_item.item:
        feed_item.delete()
        continue
    feed_item.update_tsearch(feed_item.item.get_search_text())
