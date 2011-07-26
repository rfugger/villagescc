from cc.profile.models import Profile
from cc.account.models import CreditLine, Account, Node

class UserAccount(object):
    "Wrapper around CreditLine."
    def __init__(self, creditline):
        self.creditline = creditline

    def partner(self):
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

