from django import template

register = template.Library()

@register.simple_tag
def render_in_feed(feed_item):
    if not feed_item.FEED_TEMPLATE:
        raise Exception("Feed item model needs to define FEED_TEMPLATE.")
    t = template.loader.get_template(feed_item.FEED_TEMPLATE)
    c = template.Context(dict(item=feed_item))
    return t.render(c)
    
