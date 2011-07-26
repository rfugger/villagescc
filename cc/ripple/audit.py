"""
Auditing functions.
"""
from decimal import Decimal as D

from django.db.models import Sum

from cc.account.models import Account
from cc.payment.models import Payment, PaymentLink

class AuditError(Exception):
    pass

def account_check(account):
    """
    Returns True if account balance is the sum of all entries.
    Otherwise raises AuditError.
    """
    entry_sum = (
        account.entries.all().aggregate(Sum('amount'))['amount__sum'] or D('0'))
    if entry_sum != account.balance:
        raise AuditError(
            "%s out of balance: balance is %s; entry sum is %s" % (
                account, account.balance, entry_sum))
    return True

def all_accounts_check():
    for account in Account.objects.all():
        account_check(account)
    return True

def link_check(link):
    """
    Verify that payment link matches entry.
    """
    if link.payment.last_attempted_at != link.entry.date:
        raise AuditError("%s: entry has incorrect date." % link)
    return True
    
def all_links_check():
    for link in PaymentLink.objects.all().select_related(depth=3):
        link_check(link)
    return True

def payment_check(payment):
    """
    Verify that payer and recipient payment links sum to payment amount,
    and intermediaries' payment links sum to zero.
    """
    # Assign each payment link to the two account partners.
    amounts_by_node = {}
    for link in payment.links.all().select_related(depth=2):
        pos_node = link.entry.account.positive_node
        amounts_by_node.setdefault(pos_node, []).append(link.entry.amount)
        neg_node = link.entry.account.negative_node
        amounts_by_node.setdefault(neg_node, []).append(-link.entry.amount)
    # Sum link contributions for each node.
    for node, amounts in amounts_by_node.items():
        if node == payment.payer:
            if sum(amounts) != -payment.amount:
                raise AuditError(
                    "%s: payer did not pay correct amount." % payment)
        elif node == payment.recipient:
            if sum(amounts) != payment.amount:
                raise AuditError(
                    "%s: recipient did not receive correct amount." % payment)
        else:  # Intermediary.
            if sum(amounts) != D('0.0'):
                raise AuditError(
                    "%s: intermediary's link amounts do not sum to zero." %
                    payment)
    return True

def all_payments_check():
    for payment in Payment.objects.filter(status='completed'):
        payment_check(payment)
    return True
