"API to Ripple backend."

# TODO: Test this module.

from cc.profile.models import Profile
from cc.account.models import CreditLine, Account, Node
from cc.payment.flow import FlowGraph

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

def get_user_accounts(profile):
    return [UserAccount(cl) for cl in
            CreditLine.objects.filter(node__alias=profile.id)]

def update_credit_limit(endorsement):
    # Get endorsement recipient's creditline.
    account = get_or_create_account_from_endorsement(endorsement)
    creditline = CreditLine.objects.get(
        node=endorsement.recipient_id, account=account)
    creditline.limit = endorsement.weight
    creditline.save()

def get_or_create_account_from_endorsement(endorsement):
    endorser_node, _ = Node.objects.get_or_create(alias=endorsement.endorser_id)
    recipient_node, _ = Node.objects.get_or_create(alias=endorsement.recipient_id)
    return Account.objects.get_or_create_account(endorser_node, recipient_node)

def get_entries_between(profile1, profile2):
    "Give entries between two profiles from POV of profile1."
    node1, _ = Node.objects.get_or_create(alias=profile1.id)
    node2, _ = Node.objects.get_or_create(alias=profile2.id)
    account = Account.objects.get_account(node1, node2)
    if account is None:
        return []
    return account.entries.all()
        
def max_payment(payer_profile, recipient_profile):
    payer, _ = Node.objects.get_or_create(alias=payer_profile.id)
    recipient, _ = Node.objects.get_or_create(alias=recipient_profile.id)
    flow_graph = FlowGraph(payer, recipient)
    return flow_graph.max_flow()
