from decimal import Decimal as D

from django.db import models

from south.modelsinspector import add_introspection_rules


class AmountField(models.DecimalField):
    "Field for value amounts."
    PRECISION = 16  # Digits to store.
    SCALE = 6  # Decimal places to reserve.
    
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = self.PRECISION
        kwargs['decimal_places'] = self.SCALE
        super(AmountField, self).__init__(*args, **kwargs)

# Enable south migrations for custom fields.
add_introspection_rules([], ["^cc\.general"])


class Node(models.Model):
    """
    A node in the Ripple graph.  This table exists only for referential
    integrity.  It doesn't store anything other than an ID.
    """

    def __unicode__(self):
        return u"Node %d" % self.id
    
class AccountManager(models.Manager):
    def create_account(self, node1, node2):
        """
        Create account between two nodes.
        Also creates the required CreditLine records.
        """
        acct = self.create()
        CreditLine.objects.create(
            account=acct, node=node1, balance_multiplier=1)
        CreditLine.objects.create(
            account=acct, node=node2, balance_multiplier=-1)
        return acct
        
class Account(models.Model):
    """
    A mutual credit account that tracks IOUs between two nodes.
    This table stores the balance and other data shared between the nodes.
    CreditLine below stores symmetric data that each node has about
    the account.  Each account has two CreditLines.
    """
    balance = AmountField(default=D('0'))
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = AccountManager()
    
    def __unicode__(self):
        return u"Account %s" % self.id

    def create_entry(self, amount, date, memo=''):
        "Create an account entry and update this account's balance."
        new_balance = self.balance + amount
        entry = self.entries.create(
            amount=amount, new_balance=new_balance, date=date, memo=memo)
        self.balance = new_balance
        self.save()
        return entry
        
class CreditLine(models.Model):
    """
    One node's data for and view on a mutual credit account.
    """
    account = models.ForeignKey(Account, related_name='creditlines')
    node = models.ForeignKey(Node, related_name='creditlines')
    balance_multiplier = models.SmallIntegerField(
        choices=((1, '+1'), (-1, '-1')))
    # Max obligations node can emit to partner.
    limit = AmountField(null=True, blank=True)
    
    def __unicode__(self):
        return u"%s's credit line for account %s" % (self.node, self.account_id)

    @property
    def balance(self):
        "Node's balance."
        return self.account.balance * self.balance_multiplier

    @property
    def partner_creditline(self):
        # Cache this to avoid multiple queries returning the same thing.
        if not hasattr(self, '_partner_creditline'):
            self._partner_creditline = CreditLine.objects.exclude(
                node__pk=self.node_id).get(account__pk=self.account_id)
        return self._partner_creditline

    @property
    def partner(self):
        return self.partner_creditline.node
    
    @property
    def in_limit(self):
        "Max obligations node will accept from partner."
        return self.partner_creditline.limit
    
    def payment_cost(self):
        """
        Assigns a cost to using this account in a payment in proportion to
        how little credit is available on the destination credit line vertex of
        that edge, relative to the credit limit in that direction.  So if the
        credit limit was 100 and available credit was 30, the cost would be
        1 - (30/100) = 0.7.  If the credit limit was 100 and available credit
        was 120, the cost would be 1 - (120/100) = -0.2, implying that this
        direction should be preferred (reduces obligations).

        (Ideally, costs would be in proportion to the amount of credit remaining
        *after* the payment, but that is not known yet, and the naive min cost
        demand flow algorithm used can't factor that in.)

        Returns a list of (capacity, cost) pairs referring to separate chunks of
        credit, to allow assigning different costs to each of them.  (Cashing in
        IOUs is preferred to emitting new IOUs.)

        TODO: Factor in:
          - payment amount
          - interest
          - is it better to add 10 obligations to 80/100 or 0/20?
          - it's better to use stale accounts than fresh ones (how recent was
          the last transaction?).
        """
        if self.limit is None:
            # No cost if no limit -- treat as if balance is always 0.
            return ((float('inf'), 0.0),)  # Capacity is infinite.
        capacity = self.balance + self.limit
        cost = 1.0 - (float(capacity / self.limit))
        if self.balance <= 0:
            # No positive balance to cash in.
            return ((capacity, cost),)
        else:
            # Give negative cost only to cashing in existing IOUs.
            return ((self.balance, cost), (self.limit, 0))

class AccountEntry(models.Model):
    account = models.ForeignKey(Account, related_name='entries')
    date = models.DateTimeField()
    amount = AmountField()
    new_balance= AmountField()
    memo = models.TextField(blank=True)

    def __unicode__(self):
        return u"%s entry on %s" % (self.amount, self.account)

