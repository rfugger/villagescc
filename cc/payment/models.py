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
        # TODO: Some kind of transaction management here.
        # Django's transaction middleware only handles the default db,
        # and this will probably eventually be done as an asynchronous task
        # in a separate process anyway...
        # Maybe transaction should be controlled at a higher level?
        
        self.last_attempted_at = datetime.now()
        # Write attempted date now so if something happens we can see this
        # payment was interrupted.
        self.save()
        try:
            flow_graph = FlowGraph(self.payer, self.recipient)
            flow_links = flow_graph.min_cost_flow(self.amount)
            for flow_link in flow_links:
                PaymentLink.objects.create_link(
                    self, flow_link.account, flow_link.amount)
            self.status = 'completed'
            self.save()
        except BaseException as exc:
            self.status = 'failed'
            self.save()
            if not isinstance(exc, PaymentError):
                raise

    def as_entry(self):
        """
        Performs this payment as a direct entry between payer and recipient.
        Creates account between them if one does not exist.
        """
        account = Account.objects.get_or_create_account(payer, recipient)
        self.last_attempted_at = datetime.now()
        PaymentLink.objects.create_link(self, account, -self.amount)
        self.status = 'completed'
        self.save()
        
class PaymentLinkManager(models.Manager):
    def create_link(self, payment, account, amount):
        # TODO: Make sure we're staying within account limits?
        entry = account.create_entry(
            amount=amount,
            date=payment.last_attempted_at,
            memo='Payment %s' % payment.id)
        self.create(payment=payment, entry=entry)

# TODO: Remove this class entirely.  Just put payment_id field on AccountEntry.
class PaymentLink(models.Model):
    payment = models.ForeignKey(Payment, related_name='links')
    entry = models.ForeignKey(AccountEntry, unique=True, related_name='links')
    
    objects = PaymentLinkManager()
    
    def __unicode__(self):
        return u"Link for %s: %s" % (self.payment, self.entry)

