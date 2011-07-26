from decimal import Decimal as D
from datetime import datetime

from django.test import TestCase
from django.db import models

from cc.account.models import Node, Account, CreditLine

class BasicTest(TestCase):
    """
    One unit, two users, one account, no limits.
    """
    def setUp(self):
        self.node1 = Node.objects.create()
        self.node2 = Node.objects.create()
        self.account = Account.objects.create_account(self.node1, self.node2)
        self.node1_creditline = CreditLine.objects.get(
            account=self.account, node=self.node1)
        self.node2_creditline = CreditLine.objects.get(
            account=self.account, node=self.node2)

    def tearDown(self):
        self.account.delete()  # Deletes accounts, entries, etc.
        Node.objects.all().delete()

    def reload(self):
        """
        Reload all cached objects from db.  Do this every time you change
        anything, because cached objects abound in the framework.
        """
        for obj_name in self.__dict__:
            obj = getattr(self, obj_name)
            if isinstance(obj, models.Model):
                setattr(self, obj_name, obj.__class__.objects.get(pk=obj.id))
        
class LimitsTest(BasicTest):
    """
    Add limits to account.
    """
    def setUp(self):
        super(LimitsTest, self).setUp()
        self.node1_creditline.limit = D('5')
        self.node1_creditline.save()

        
class BasicAccountTest(BasicTest):
    def test_display(self):
        unicode(self.account)
        unicode(self.node1_creditline)
    
    def test_payment_functions(self):
        self.assertEqual(self.node1_creditline.payment_cost(),
                         ((float('inf'), 0.0),))

    def test_entry(self):
        self.assertEqual(self.account.balance, D('0'))
        self.account.create_entry(D('5'), datetime.now())
        self.reload()
        self.assertEqual(self.account.balance, D('5'))
        entries = self.account.entries.all()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.new_balance, D('5'))
        self.assertEqual(self.node1_creditline.balance, D('5'))
        self.assertEqual(self.node2_creditline.balance, D('-5'))
        unicode(entry)
    
class AccountLimitsTest(LimitsTest):
    def test_payment_functions(self):
        self.assertEqual(self.node1_creditline.payment_cost(), ((D('5'), 0.0),))
        self.assertEqual(self.node2_creditline.in_limit, D('5'))
        
        # Set a nonzero balance and test.
        self.account.create_entry(D('3'), datetime.now())
        self.reload()
        self.assertEqual(self.node1_creditline.payment_cost(),
                         ((D('3'), 1.0 - float(D('8') / D('5'))),
                          (D('5'), 0.0)))
        self.assertEqual(self.node2_creditline.payment_cost(),
                        ((float('inf'), 0.0),))
