"API to Ripple backend."

# TODO: Test this module.
# TODO: Import * into __init__.py so `from cc import ripple` works.
# TODO: Don't use 'user' when I really mean 'profile' (here and everywhere).
# TODO: Test transaction handling here, think more deeply about it.

from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db import models, transaction

from cc.account.models import CreditLine, Account, Node
from cc.payment.flow import FlowGraph, PaymentError
from cc.payment.models import Payment
from cc.general.util import cache_on_object

REPUTATION_VERSION_KEY = 'credit_reputation_version'

class UserAccount(object):
    "Wrapper around CreditLine."
    def __init__(self, creditline, user):
        self.creditline = creditline
        self.user = user

    @property
    @cache_on_object
    def partner(self):
        from cc.profile.models import Profile
        return Profile.objects.get(pk=self.creditline.partner.alias)

    @property
    def out_limit(self):
        return int(self.creditline.limit)

    @property
    def balance(self):
        return self.creditline.balance

    @property
    def in_limit(self):
        return int(self.creditline.in_limit)

    @property
    @cache_on_object
    def endorsement(self):
        from cc.relate.models import Endorsement
        try:
            return Endorsement.objects.get(
                endorser=self.user, recipient=self.partner)
        except Endorsement.DoesNotExist:
            return None

    @property
    @cache_on_object
    def partner_endorsement(self):
        from cc.relate.models import Endorsement
        try:
            return Endorsement.objects.get(
                endorser=self.partner, recipient=self.user)
        except Endorsement.DoesNotExist:
            return None

    @property
    def health(self):
        """
        Returns (1 - ratio of credits used in balance direction) as a
        percentage, or zero, whichever is larger.  If there is no credit
        limit in balance direction, returns None.
        """
        if self.balance > 0:
            if self.in_limit:
                used_ratio = self.balance / self.in_limit
            else:
                return None
        else:
            if self.out_limit:
                used_ratio = -self.balance / self.out_limit
            else:
                return None
        return max(int((1 - used_ratio) * 100), 0)

    @property
    def owed_to_you(self):
        return self.balance >= 0 and self.balance or None
    
    @property
    def owed_to_them(self):
        return self.balance < 0 and -self.balance or None

    @property
    def entries(self):
        # TODO: Paginate entries.
        return [UserEntry(entry, self.user) for entry
                in self.creditline.account.entries.all().order_by(
                '-payment__last_attempted_at')]
        
    
class UserEntry(object):
    """
    Wrapper around Entry, with amounts from point of view of one partner.
    """
    def __init__(self, entry, user):
        self.entry = entry
        creditline = entry.account.creditlines.get(node__alias=user.id)
        self.bal_mult = creditline.bal_mult
        self.account = UserAccount(creditline, user)

    def __getattr__(self, name):
        "Proxy attribute lookups to self.entry."
        if name in ('id', 'date', 'payment_id'):
            return getattr(self.entry, name)
        raise AttributeError("%s does not have attribute '%s'." % (
                self.__class__, name))

    @property
    def amount(self):
        return self.entry.amount * self.bal_mult

    @property
    def abs_amount(self):
        return abs(self.entry.amount)
    
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

    @property
    @cache_on_object
    def payment(self):
        return RipplePayment(self.entry.payment)


class RipplePayment(object):
    "Wrapper around Payment.  Implements feed item model interface."

    FEED_TEMPLATE = 'acknowledgement_feed_item.html'

    DoesNotExist = ObjectDoesNotExist
    
    def __init__(self, payment):
        self.payment = payment

    def __getattr__(self, name):
        "Proxy attribute lookups to self.payment."
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
    def text(self):
        return self.memo
    
    @property
    def feed_poster(self):
        return self.payer

    @property
    def feed_recipient(self):
        return self.recipient

    @property
    def feed_public(self):
        return False
    
    def get_search_text(self):
        return [(self.memo, 'B'),
                (self.payer.name, 'C'),
                (self.payer.username, 'C'),
                (self.recipient.name, 'C'),
                (self.recipient.username, 'C'),
               ]
        
    @property
    @cache_on_object
    def payer(self):
        from cc.profile.models import Profile
        return Profile.objects.get(pk=self.payment.payer.alias)
        
    @property
    @cache_on_object
    def recipient(self):
        from cc.profile.models import Profile
        return Profile.objects.get(pk=self.payment.recipient.alias)
    
    @models.permalink
    def get_absolute_url(self):
        return 'view_acknowledgement', (self.id,)

    def entries_for_user(self, user):
        return [UserEntry(entry, user) for entry in
                self.payment.entries.filter(
                    account__creditlines__node__alias=user.id)]
    
    @classmethod
    def get_by_id(cls, payment_id):
        try:
            return get_payment(payment_id)
        except Payment.DoesNotExist:
            raise cls.DoesNotExist

    @classmethod
    def get_all(cls):
        return (cls(pmt) for pmt in Payment.objects.iterator())

def get_nodes(profile1, profile2):
    node1, _ = Node.objects.get_or_create(alias=profile1.id)
    node2, _ = Node.objects.get_or_create(alias=profile2.id)
    return node1, node2
    
def accept_profiles(func):
    """
    Decorator for function that takes two Nodes, allowing it to take
    two Profiles instead.  Makes sure nodes exist for the profiles,
    and passes the nodes to the original function.
    """
    def profile_accepting_wrapper(profile1, profile2, *args, **kwargs):
        node1, node2 = get_nodes(profile1, profile2)
        return func(node1, node2, *args, **kwargs)
    profile_accepting_wrapper.__name__ = func.__name__
    profile_accepting_wrapper.__module__ = func.__module__
    return profile_accepting_wrapper
    
def get_user_accounts(profile):
    return [UserAccount(cl, profile) for cl in
            CreditLine.objects.filter(node__alias=profile.id)]

def get_account(profile, partner_profile):
    node, partner = get_nodes(profile, partner_profile)
    account = Account.objects.get_account(node, partner)
    if not account:
        return None
    cl = CreditLine.objects.get(node=node, account=account)
    return UserAccount(cl, profile)

@transaction.commit_on_success(using='ripple')
def update_credit_limit(endorsement):
    # Get endorsement recipient's creditline.
    account = get_or_create_account_from_profiles(
        endorsement.endorser, endorsement.recipient)
    creditline = CreditLine.objects.get(
        node__alias=endorsement.recipient_id, account=account)
    creditline.limit = endorsement.weight
    creditline.save()
    
    _invalidate_reputation_cache()

@accept_profiles
def get_or_create_account_from_profiles(node1, node2):
    return Account.objects.get_or_create_account(node1, node2)

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
    try:
        payment = Payment.objects.get(pk=payment_id)
    except Payment.DoesNotExist:
        raise RipplePayment.DoesNotExist
    return RipplePayment(payment)

@accept_profiles
def credit_reputation(target, asker):
    version = _reputation_cache_version()
    key = 'credit_reputation(%s,%s)' % (repr(target), repr(asker))
    val = cache.get(key, version=version)
    if val is None:
        flow_graph = FlowGraph(target, asker, ignore_balances=True)
        val = flow_graph.max_flow()
        cache.set(key, val, None, version=version)
    return val

def overall_balance(profile):
    node, _ = Node.objects.get_or_create(alias=profile.id)
    return node.overall_balance()

def trusted_balance(profile):
    node, _ = Node.objects.get_or_create(alias=profile.id)
    return node.trusted_balance()

def delete_node(profile):
    try:
        node = Node.objects.get(alias=profile.id)
    except Node.DoesNotExist:
        return
    node.delete()

##### Helpers #####

def _reputation_cache_version():
    return cache.get(REPUTATION_VERSION_KEY, 1)

def _invalidate_reputation_cache():
    cache.add(REPUTATION_VERSION_KEY, 1)
    cache.incr(REPUTATION_VERSION_KEY)
    
