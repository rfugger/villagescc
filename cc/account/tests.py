from decimal import Decimal as D
from datetime import datetime

from cc.ripple.tests import BasicTest, LimitsTest

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
