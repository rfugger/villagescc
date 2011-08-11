from decimal import Decimal as D

from cc.ripple.tests import BasicTest
from cc.payment.models import Payment
from cc.ripple import audit
from cc.account.models import CreditLine

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

    def _set_limit(self, creditline, limit):
        creditline.limit = limit
        creditline.save()
        self.reload()        
        
    def _payment(self, creditline, amount, succeed=True):
        initial_balance = creditline.balance

        payment = Payment.objects.create(
            payer=creditline.node, recipient=creditline.partner, amount=amount)
        payment.attempt()
        self.reload()
        creditline = CreditLine.objects.get(pk=creditline.id)
        
        self.failUnless(audit.all_accounts_check())
        self.failUnless(audit.all_payments_check())

        if succeed:
            correct_status = 'completed'
            correct_balance = initial_balance - amount
        else:
            correct_status = 'failed'
            correct_balance = initial_balance
        self.assertEquals(payment.status, correct_status)
        self.assertEquals(creditline.balance, correct_balance)
        
    def test_limit(self):
        self._set_limit(self.node1_creditline, 5)
        self._payment(self.node1_creditline, 1)

    def test_over_limit(self):
        self._set_limit(self.node1_creditline, 5)
        self._payment(self.node1_creditline, 10, succeed=False)

    def test_zero_limit(self):
        self._set_limit(self.node1_creditline, 0)
        self._payment(self.node1_creditline, 1, succeed=False)

    def test_exact_limit(self):
        self._set_limit(self.node1_creditline, 5)
        self._payment(self.node1_creditline, 5)
        
    def test_multi_payment(self):
        self._set_limit(self.node1_creditline, 10)
        self._set_limit(self.node2_creditline, 0)
        self._payment(self.node1_creditline, D('6.4'))
        self._payment(self.node1_creditline, D('1.3'))
        self._payment(self.node2_creditline, D('10'), succeed=False)
        self._payment(self.node2_creditline, D('4'))
        self.assertEquals(self.node1_creditline.balance, D('-3.7'))
