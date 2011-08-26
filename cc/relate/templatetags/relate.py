from django import template

register = template.Library()

@register.simple_tag
def trusted_endorsement_sum(profile, asker):
    return profile.trusted_endorsement_sum(asker)
