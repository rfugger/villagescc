from django import template

register = template.Library()

@register.filter
def trim_zeroes(amount):
    amount = unicode(amount)
    while '.' in amount and amount[-1] in ('0', '.'):
        amount = amount[:-1]
    return amount
