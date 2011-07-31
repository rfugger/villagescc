from datetime import datetime

from django.db import models

from cc.account.models import AmountField, Node, CreditLine, AccountEntry
from cc.payment.flow import FlowGraph, PaymentError


STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
)


class Payment(models.Model):
    payer = models.ForeignKey(Node, related_name='sent_payments')
    recipient = models.ForeignKey(Node, related_name='received_payments')
    amount = AmountField()
    memo = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    last_attempted_at = models.DateTimeField(null=True)
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default='pending')

    def __unicode__(self):
        return u"%s payment from %s to %s" % (
            self.amount, self.payer, self.recipient)

    def attempt(self):
        """
        Try to perform this payment.

        WARNING: All payments must be performed by a single process in
        serial fashion.  No checks are performed to account for the possibility
        of parallel payments.
        """
        self.last_attempted_at = datetime.now()
        self.save()
        try:
            flow_graph = FlowGraph(self.payer, self.recipient)
            flow_links = flow_graph.min_cost_flow(self.amount)
        except PaymentError:
            self.status = 'failed'
            self.save()
            raise
        # Commit to database.
        for flow_link in flow_links:
            PaymentLink.objects.create_link(flow_link, self)
        self.status = 'completed'
        self.save()
        
class PaymentLinkManager(models.Manager):
    def create_link(self, flow_link, payment):
        # TODO: Make sure we're staying within account limits?
        entry = flow_link.account.create_entry(
            amount=flow_link.amount,
            date=payment.last_attempted_at,
            memo='Payment %s' % payment.id)
        self.create(payment=payment, entry=entry)

class PaymentLink(models.Model):
    payment = models.ForeignKey(Payment, related_name='links')
    entry = models.ForeignKey(AccountEntry, unique=True, related_name='links')
    
    objects = PaymentLinkManager()
    
    def __unicode__(self):
        return u"Link for %s: %s" % (self.payment, self.entry)

