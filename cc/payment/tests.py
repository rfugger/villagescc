from decimal import Decimal as D

from cc.ripple.tests import BasicTest
from cc.payment.models import Payment
from cc.ripple import audit

class OneHopPaymentTest(BasicTest):
    def test_entry(self):
        payment = Payment.objects.create(
            payer=self.node2, recipient=self.node1, amount=D('5.00'))

        self.assertEqual(self.account.balance, D('0'))
        payment.as_entry()
        self.reload()
        self.assertEqual(self.account.balance, D('5'))
        entries = self.account.entries.all()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.new_balance, D('5'))
        self.assertEqual(self.node1_creditline.balance, D('5'))
        self.assertEqual(self.node2_creditline.balance, D('-5'))
        unicode(entry)

    def test_payment(self):
        payment = Payment.objects.create(
            payer=self.node1, recipient=self.node2, amount=D('1.00'))
        self.assertEquals(payment.status, 'pending')
        payment.attempt()
        unicode(payment)
        
        self.reload()
        payment = Payment.objects.get(pk=payment.id)

        # High-level checks.
        self.failUnless(audit.all_accounts_check())
        self.failUnless(audit.all_payments_check())
        
        # Fine-grained checks.
        # TODO: Decide which of these are no longer necessary.
        self.assertEquals(payment.status, 'completed')
        self.failUnless(payment.last_attempted_at >= payment.submitted_at)
        self.assertEquals(self.node1_creditline.balance, D('-1.0'))
        self.assertEquals(self.node2_creditline.balance, D('1.0'))
        entries = self.account.entries.all()
        self.assertEquals(len(entries), 1)
        entry = entries[0]
        self.assertEquals(
            entry.amount, D('1.0') * self.node2_creditline.bal_mult)
        self.assertEquals(entry.date, payment.last_attempted_at)
        entries = payment.entries.all()
        self.assertEquals(len(entries), 1)
        
# TODO: Test zero limits.  Might be problems with non-terminating simplex...
