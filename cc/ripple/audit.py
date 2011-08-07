"""
Auditing functions.
"""
from decimal import Decimal as D

from django.db.models import Sum

from cc.account.models import Account
from cc.payment.models import Payment, Entry

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

def payment_check(payment):
    """
    Verify that payer and recipient payment entries sum to payment amount,
    and intermediaries' payment entries sum to zero.
    """
    # Assign each payment entry to the two account partners.
    amounts_by_node = {}
    for entry in payment.entries.all().select_related(depth=1):
        pos_node = entry.account.pos_node
        amounts_by_node.setdefault(pos_node, []).append(entry.amount)
        neg_node = entry.account.neg_node
        amounts_by_node.setdefault(neg_node, []).append(-entry.amount)
    # Sum entries for each node.
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
                    "%s: intermediary's entry amounts do not sum to zero." %
                    payment)
    return True

def all_payments_check():
    for payment in Payment.objects.filter(status='completed'):
        payment_check(payment)
    return True
