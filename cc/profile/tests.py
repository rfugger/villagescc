from cc.general.tests import BasicTest

class BasicProfileTest(BasicTest):
    def test_display(self):
        unicode(self.user1)

    def test_account_half_getters(self):
        outgoing_account_halves = self.user1.outgoing_account_halves(self.unit)
        self.failUnless(list(outgoing_account_halves) == [self.user1_acct_half])
        incoming_account_halves = self.user1.incoming_account_halves(self.unit)
        self.failUnless(list(incoming_account_halves) == [self.user2_acct_half])
