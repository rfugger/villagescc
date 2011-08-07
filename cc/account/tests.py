from decimal import Decimal as D
from datetime import datetime

from cc.ripple.tests import BasicTest, LimitsTest

class BasicAccountTest(BasicTest):
    def test_display(self):
        unicode(self.account)
        unicode(self.node1_creditline)
    

