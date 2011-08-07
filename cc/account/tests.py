from decimal import Decimal as D
from datetime import datetime

from cc.ripple.tests import BasicTest, LimitsTest

class BasicAccountTest(BasicTest):
    def test_display(self):
        unicode(self.account)
        unicode(self.node1_creditline)
    
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

