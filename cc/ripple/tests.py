from decimal import Decimal as D

from django.test import TestCase
from django.db import models

from cc.account.models import Node, Account, CreditLine

class BasicTest(TestCase):
    """
    One unit, two users, one account, no limits.
    """
    def setUp(self):
        self.node1 = Node.objects.create(name='node1')
        self.node2 = Node.objects.create(name='node2')
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
