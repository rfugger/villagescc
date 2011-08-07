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
    
