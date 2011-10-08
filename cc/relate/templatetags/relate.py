from django import template

import cc.ripple.api as ripple

register = template.Library()

@register.simple_tag
def trusted_endorsement_sum(profile, asker):
    return profile.trusted_endorsement_sum(asker)

@register.tag
def load_user_account(parser, token):
    """
    Loads a UserAccount Ripple API object into the current context.

    Example:
    {% load_user_account profile partner as target_var %}
    """
    try:
        tag_name, profile_var, partner_var, as_token, target_var = (
            token.split_contents())
    except ValueError:
        raise template.TemplateSyntaxError(
            "load_user_account tag must contain five elements.")
    if as_token != 'as':
        raise template.TemplateSyntaxError(
            "load_user_account tag must have 'as' as the 4th element.")
    return LoadUserAccountNode(profile_var, partner_var, target_var)

class LoadUserAccountNode(template.Node):
    def __init__(self, profile_var, partner_var, target_var):
        self.profile_var = template.Variable(profile_var)
        self.partner_var = template.Variable(partner_var)
        self.target_var_name = target_var

    def render(self, context):
        profile = self.profile_var.resolve(context)
        partner = self.partner_var.resolve(context)
        user_account = ripple.get_account(profile, partner)
        context[self.target_var_name] = user_account
        return ''

@register.simple_tag
def entry_description(entry, profile):
    if entry.payment.payer == profile:
        desc = "Sent acknowledgement to %s" % entry.payment.recipient
    elif entry.payment.recipient == profile:
        desc = "Received acknowledgement from %s" % entry.payment.payer
    else:

        # TODO: Maybe "acknowledged %s in exchange for acknowledgement from %s"?
        # Something else with "exchanged"?
        
        desc = "Helped route acknowledgement from %s to %s" % (
            entry.payment.payer, entry.payment.recipient)
    return desc
