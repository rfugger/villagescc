from decimal import Decimal as D

from django.test import TestCase
from django.db import models

from cc.account.models import Node, Account, CreditLine
from cc.payment.models import Payment
from cc.ripple import audit

class RippleTest(TestCase):
    # Tell test framework to rollback all databases after every test,
    # not just default.
    multi_db = True
    
    def reload(self):
        """
        Reload all cached objects from db.  Do this every time you change
        anything, because cached objects abound in the framework.
        """
        for obj_name in self.__dict__:
            obj = getattr(self, obj_name)
            if isinstance(obj, models.Model):
                setattr(self, obj_name, obj.__class__.objects.get(pk=obj.id))    

    def _set_limit(self, creditline, limit):
        creditline.limit = limit
        creditline.save()
        self.reload()        
        
    def _payment(self, payer, recipient, amount, succeed=None):
        payment = Payment.objects.create(
            payer=payer, recipient=recipient, amount=amount)
        payment.attempt()
        self.reload()

        if succeed is not None:
            correct_status = succeed and 'completed' or 'failed'
            self.assertEquals(payment.status, correct_status)
        self.failUnless(audit.all_accounts_check())
        self.failUnless(audit.all_payments_check())
        
class BasicTest(RippleTest):
    """
    One unit, two users, one account, no limits.
    """
    def setUp(self):
        self.node1 = Node.objects.create(alias=1)
        self.node2 = Node.objects.create(alias=2)
        self.account = Account.objects.create_account(self.node1, self.node2)
        self.node1_creditline = CreditLine.objects.get(
            account=self.account, node=self.node1)
        self.node1_creditline.limit = None
        self.node1_creditline.save()
        self.node2_creditline = CreditLine.objects.get(
            account=self.account, node=self.node2)
        self.node2_creditline.limit = None
        self.node2_creditline.save()
        
