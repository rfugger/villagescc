"API to Ripple backend."

# TODO: Test this module.

from cc.profile.models import Profile
from cc.account.models import CreditLine, Account, Node
from cc.payment.flow import FlowGraph, PaymentError

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
def get_entries_between(x, y):
    "Give entries between two nodes from POV of the first."
    account = Account.objects.get_account(x, y)
    if account is None:
        return []
    return account.entries.all()

@accept_profiles
def max_payment(payer, recipient):
    flow_graph = FlowGraph(payer, recipient)
    return flow_graph.max_flow()

@accept_profiles
def pay(payer, recipient, amount, memo):
    payment = Payment.objects.create(
        payer=payer, recipient=recipient, amount=amount, memo=memo)
    try:
        payment.attempt()
    except PaymentError:
        return None
    return payment

@accept_profiles
def record_entry(payer, recipient, amount, memo):
    account = Account.objects.get_or_create_account(payer, recipient)
    entry = account.create_entry(-amount, memo=memo)
    return entry


