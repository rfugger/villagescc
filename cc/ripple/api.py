"API to Ripple backend."

# TODO: Test this module.

from django.core.exceptions import ObjectDoesNotExist

from cc.profile.models import Profile
from cc.account.models import CreditLine, Account, Node
from cc.payment.flow import FlowGraph, PaymentError
from cc.payment.models import Payment

class UserAccount(object):
    "Wrapper around CreditLine."
    def __init__(self, creditline):
        self.creditline = creditline

    def partner(self):
        # TODO: Cache this.
        return Profile.objects.get(pk=self.creditline.partner.alias)

    def out_limit(self):
        return self.creditline.limit

    def balance(self):
        return self.creditline.balance

    def in_limit(self):
        return self.creditline.in_limit

class UserAccountEntry(object):
    """
    Wrapper around AccountEntry, with amounts from point of view of one partner.
    """
    def __init__(self, entry, user):
        self.entry = entry
        creditline = entry.account.creditlines.get(node__alias=user.id)
        self.bal_mult = creditline.bal_mult

    @property
    def date(self):
        return self.entry.date

    @property
    def amount(self):
        return self.entry.amount * self.bal_mult

    @property
    def received(self):
        if self.amount > 0:
            return self.amount
        else:
            return None

    @property
    def sent(self):
        if self.amount < 0:
            return -1 * self.amount
        else:
            return None

    @property
    def new_balance(self):
        return self.entry.new_balance * self.bal_mult
    
class RipplePayment(object):
    "Wrapper around Payment.  Implements feed item model interface."

    FEED_TEMPLATE = 'promise_feed_item.html'

    DoesNotExist = ObjectDoesNotExist
    
    def __init__(self, payment):
        self.payment = payment

    def __getattr__(self, name):
        "Proxy attribute lookups to self.payment."
        # TODO: Make more explicit the attributes accessible here, so
        # interface is better-defined.
        if name in ('id', 'amount', 'memo'):
            return getattr(self.payment, name)
        raise AttributeError("%s does not have attribute '%s'." % (
                self.__class__, name))
        
    @property
    def date(self):
        return self.payment.last_attempted_at or self.payment.submitted_at

    @property
    def location(self):
        return None

    @property
    def feed_poster(self):
        return self.payer()
    
    def get_feed_users(self):
        return (self.payer(), self.recipient())

    def payer(self):
        return Profile.objects.get(pk=self.payment.payer.alias)
        
    def recipient(self):
        return Profile.objects.get(pk=self.payment.recipient.alias)
    
    @classmethod
    def get_by_id(cls, payment_id):
        try:
            return get_payment(payment_id)
        except Payment.DoesNotExist:
            raise self.DoesNotExist


def accept_profiles(func):
    """
    Decorator for function that takes two Nodes, allowing it to take
    two Profiles instead.  Makes sure nodes exist for the profiles,
    and passes the nodes to the original function.
    """
    def profile_accepting_wrapper(profile1, profile2, *args, **kwargs):
        node1, _ = Node.objects.get_or_create(alias=profile1.id)
        node2, _ = Node.objects.get_or_create(alias=profile2.id)
        return func(node1, node2, *args, **kwargs)
    return profile_accepting_wrapper
    
def get_user_accounts(profile):
    return [UserAccount(cl) for cl in
            CreditLine.objects.filter(node__alias=profile.id)]

def update_credit_limit(endorsement):
    # Get endorsement recipient's creditline.
    account = get_or_create_account_from_profiles(
        endorsement.endorser, endorsement.recipient)
    creditline = CreditLine.objects.get(
        node=endorsement.recipient_id, account=account)
    creditline.limit = endorsement.weight
    creditline.save()

@accept_profiles
def get_or_create_account_from_profiles(node1, node2):
    return Account.objects.get_or_create_account(node1, node2)

@accept_profiles
def get_entries_between(node, partner):
    "Give entries between two nodes from POV of the first."
    account = Account.objects.get_account(node, partner)
    if account is None:
        return []
    return [UserAccountEntry(entry, node) for entry in account.entries.all()]

@accept_profiles
def max_payment(payer, recipient):
    flow_graph = FlowGraph(payer, recipient)
    return flow_graph.max_flow()

@accept_profiles
def pay(payer, recipient, amount, memo, routed):
    """
    Performs payment.  Routed=False just creates an entry on account between
    payer and recipient, and creates the account with limits=0 if it does not
    already exist.
    """
    payment = Payment.objects.create(
        payer=payer, recipient=recipient, amount=amount, memo=memo)
    if routed:
        payment.attempt()
    else:
        payment.as_entry()
    return RipplePayment(payment)

def get_payment(payment_id):
    payment = Payment.objects.get(pk=payment_id)
    return RipplePayment(payment)

