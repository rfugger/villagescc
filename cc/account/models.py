from decimal import Decimal as D
from datetime import datetime

from django.db import models

from south.modelsinspector import add_introspection_rules

from cc.ripple import PRECISION, SCALE

class AmountField(models.DecimalField):
    "Field for value amounts."    
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = PRECISION
        kwargs['decimal_places'] = SCALE
        super(AmountField, self).__init__(*args, **kwargs)

# Enable south migrations for custom fields.
add_introspection_rules([], ["^cc\.general"])


class Node(models.Model):
    "A node in the Ripple graph."
    alias = models.PositiveIntegerField(unique=True)  # Profile ID.
    
    def __unicode__(self):
        return u"Node %d" % self.alias

    def out_creditlines(self):
        return self.creditlines.all()

class AccountManager(models.Manager):
    def create_account(self, node1, node2):
        """
        Create account between two nodes.
        Also creates the required CreditLine records.
        """
        acct = self.create()
        CreditLine.objects.create(
            account=acct, node=node1, bal_mult=1)
        CreditLine.objects.create(
            account=acct, node=node2, bal_mult=-1)
        return acct

    def get_account(self, node1, node2):
        # TODO: Test this thoroughly.
        acct_list = list(self.raw(
            "select a.* from account_account a "
            "join account_creditline c1 on c1.account_id = a.id "
            "join account_creditline c2 on c2.account_id = a.id "
            "where c1.node_id = %s "
            "and c2.node_id = %s" % (node1.id, node2.id)))
        if len(acct_list) == 0:
            return None
        elif len(acct_list) == 1:
            acct = acct_list[0]
        else:
            raise Account.MultipleObjectsReturned()
        return acct
        
    def get_or_create_account(self, node1, node2):
        acct = self.get_account(node1, node2)
        if acct is None:
            acct = self.create_account(node1, node2)
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

    @property
    def pos_creditline(self):
        return self.creditlines.get(bal_mult=1)
    
    @property
    def neg_creditline(self):
        return self.creditlines.get(bal_mult=-1)

    @property
    def pos_node(self):
        return self.pos_creditline.node
    
    @property
    def neg_node(self):
        return self.neg_creditline.node
    
    def create_entry(self, amount, date=None, memo=''):
        "Create an account entry and update this account's balance."
        if date is None:
            date = datetime.now()
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
    bal_mult = models.SmallIntegerField(
        choices=((1, '+1'), (-1, '-1')))
    # Max obligations node can emit to partner.
    limit = AmountField(null=True, blank=True)

    def __unicode__(self):
        return u"%s's credit line for account %s" % (self.node, self.account_id)

    @property
    def balance(self):
        "Node's balance."
        return self.account.balance * self.bal_mult

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

