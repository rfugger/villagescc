from datetime import datetime

from django.db import models, transaction
from django.db.models import F

from cc.account.models import AmountField, Node, CreditLine, Account
from cc.payment.flow import (
    FlowGraph, PaymentError, update_creditline_in_cached_graphs)


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
        """
        self.last_attempted_at = datetime.now()
        # Write attempted date now so if something happens we can see this
        # payment was interrupted.
        self.save()
        changed_accounts = []
        try:
            flow_graph = FlowGraph(self.payer, self.recipient)
            flow_links = flow_graph.min_cost_flow(self.amount)
            with transaction.commit_on_success(using='ripple'):
                for creditline_id, amount in flow_links:
                    creditline = CreditLine.objects.get(pk=creditline_id)
                    Entry.objects.create_entry(
                        self, creditline.account, -amount * creditline.bal_mult,
                        creditline.limit)
                    changed_accounts.append(creditline.account)
                self.status = 'completed'
                self.save()
        except BaseException as exc:

            # TODO: Handle collisions better here so we can retry or give the
            # user an informative error message, rather than the server error page.
            
            self.status = 'failed'
            self.save()
            if not isinstance(exc, PaymentError):
                raise

        # Update cached graphs.
        for account in changed_accounts:
            for creditline in (account.pos_creditline, account.neg_creditline):
                update_creditline_in_cached_graphs(creditline)

    @transaction.commit_on_success(using='ripple')
    def as_entry(self):
        """
        Performs this payment as a direct entry between payer and recipient.
        Creates account between them if one does not exist.
        """
        account = Account.objects.get_or_create_account(
            self.payer, self.recipient)
        self.last_attempted_at = datetime.now()
        payer_creditline = account.creditlines.get(node=self.payer)
        Entry.objects.create_entry(
            self, account, -self.amount * payer_creditline.bal_mult, limit=None)
        self.status = 'completed'
        self.save()

class EntryManager(models.Manager):
    def create_entry(self, payment, account, amount, limit):
        "Updates account balance, and creates corresponding Entry."
        bal_upd_query = Account.objects.filter(pk=account.id)
        if limit is not None:
            # Put a limit check in update query so this is safe even
            # with concurrent transactions.

            # TODO: Test with concurrent transactions.
            
            if amount > 0:  # Test against positive account limit.
                bal_upd_query = bal_upd_query.filter(
                    balance__lte=limit - amount)
            else:  # Test against negative account limit.
                bal_upd_query = bal_upd_query.filter(
                    balance__gte=-limit - amount)
        rows = bal_upd_query.update(balance=F('balance') + amount)
        if rows != 1:
            raise PaymentError("Limit exceeded on account %d." % account.id)

        # TODO: What if some other transaction alters the balance right here?
        
        account = Account.objects.get(pk=account.id)  # Reload balance.
        new_balance = account.balance
        self.create(payment=payment, account=account, amount=amount,
                    new_balance=new_balance)

class Entry(models.Model):
    "An entry on an account for a payment."
    payment = models.ForeignKey(Payment, related_name='entries')
    account = models.ForeignKey(Account, related_name='entries')
    amount = AmountField()
    new_balance = AmountField()

    objects = EntryManager()

    class Meta:
        verbose_name_plural = 'Entries'
    
    def __unicode__(self):
        return u"%s entry on %s" % (self.amount, self.account)

    @property
    def date(self):
        return self.payment.last_attempted_at

