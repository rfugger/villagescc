from django import template

from mediagenerator.utils import media_url

from cc.general.templatetags.image import resize

register = template.Library()

@register.simple_tag
def profile_image_url(profile, size):
    if profile and profile.photo:
        return resize(profile.photo, size)
    else:
        square_side = min((int(i) for i in size.split('x')))
        return media_url('img/generic_user_%dx%d.png' % (
                square_side, square_side))
