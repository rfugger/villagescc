from django import template

from mediagenerator.utils import media_url

from cc.general.templatetags.image import resize

register = template.Library()

PROFILE_LINK_TEMPLATE = '''<a href="%s">%s</a>'''

@register.simple_tag
def profile_image_url(profile, size):
    if profile and profile.photo:
        return resize(profile.photo, size)
    else:
        square_side = min((int(i) for i in size.split('x')))
        return media_url('img/generic_user_%dx%d.png' % (
                square_side, square_side))

@register.simple_tag
def profile_display(profile, request, text="you", not_you_text=None):
    if profile == request.profile:
        return text
    else:
        if not_you_text is not None:
            return not_you_text
        else:
            return PROFILE_LINK_TEMPLATE % (profile.get_absolute_url(), profile)
