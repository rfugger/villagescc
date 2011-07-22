from django import template
from django.core.exceptions import ImproperlyConfigured

register = template.Library()

class FeedItemNode(template.Node):
    def __init__(self, item_var_name):
        self.item_var = template.Variable(item_var_name)

    def render(self, context):
        item = self.item_var.resolve(context)
        if not item.FEED_TEMPLATE:
            raise ImproperlyConfigured(
                "Feed item type %s needs to define FEED_TEMPLATE." % (
                    item.__class__))
        request = context['request']
        if hasattr(item, 'can_edit') and request.profile:
            can_edit = item.can_edit(request.profile)
        else:
            can_edit = False
            
        t = template.loader.get_template(item.FEED_TEMPLATE)
        c = template.Context(dict(
                item=item, can_edit=can_edit, request=request))
        return t.render(c)

@register.tag('render_in_feed')
def compile_feed_item_node(parser, token):
    try:
        tag_name, item_var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0])
    return FeedItemNode(item_var_name)
     
