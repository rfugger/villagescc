from decimal import Decimal as D
import random

from django.test import TestCase
import networkx as nx

from cc.ripple.tests import BasicTest, RippleTest
from cc.payment.models import Payment
from cc.ripple import audit
from cc.account.models import Node, Account, CreditLine
from cc.payment.mincost import min_cost_flow
from cc.payment.testutil import generate_edges, unmulti

class OneHopPaymentTest(BasicTest):
    def test_entry(self):
        payment = Payment.objects.create(
            payer=self.node2, recipient=self.node1, amount=D('5.00'))

        self.assertEqual(self.account.balance, D('0'))
        payment.as_entry()
        self.reload()
        self.assertEqual(self.account.balance, D('5'))
        entries = self.account.entries.all()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.new_balance, D('5'))
        self.assertEqual(self.node1_creditline.balance, D('5'))
        self.assertEqual(self.node2_creditline.balance, D('-5'))
        unicode(entry)

    def test_payment(self):
        payment = Payment.objects.create(
            payer=self.node1, recipient=self.node2, amount=D('1.00'))
        self.assertEquals(payment.status, 'pending')
        payment.attempt()
        unicode(payment)
        
        self.reload()
        payment = Payment.objects.get(pk=payment.id)

        # High-level checks.
        self.failUnless(audit.all_accounts_check())
        self.failUnless(audit.all_payments_check())
        
        # Fine-grained checks.
        self.assertEquals(payment.status, 'completed')
        self.failUnless(payment.last_attempted_at >= payment.submitted_at)
        self.assertEquals(self.node1_creditline.balance, D('-1.0'))
        self.assertEquals(self.node2_creditline.balance, D('1.0'))
        entries = self.account.entries.all()
        self.assertEquals(len(entries), 1)
        entry = entries[0]
        self.assertEquals(
            entry.amount, D('1.0') * self.node2_creditline.bal_mult)
        self.assertEquals(entry.date, payment.last_attempted_at)
        entries = payment.entries.all()
        self.assertEquals(len(entries), 1)

    def _creditline_payment(self, creditline, amount, succeed=True):
        initial_balance = creditline.balance
        self._payment(creditline.node, creditline.partner, amount, succeed)
        creditline = CreditLine.objects.get(pk=creditline.id)  # Reload.
        
        if succeed:
            correct_balance = initial_balance - amount
        else:
            correct_balance = initial_balance
        self.assertEquals(creditline.balance, correct_balance)
        
    def test_limit(self):
        self._set_limit(self.node1_creditline, 5)
        self._creditline_payment(self.node1_creditline, 1)

    def test_over_limit(self):
        self._set_limit(self.node1_creditline, 5)
        self._creditline_payment(self.node1_creditline, 10, succeed=False)

    def test_zero_limit(self):
        self._set_limit(self.node1_creditline, 0)
        self._creditline_payment(self.node1_creditline, 1, succeed=False)

    def test_exact_limit(self):
        self._set_limit(self.node1_creditline, 5)
        self._creditline_payment(self.node1_creditline, 5)
        
    def test_multi_payment(self):
        self._set_limit(self.node1_creditline, 10)
        self._set_limit(self.node2_creditline, 0)
        self._creditline_payment(self.node1_creditline, D('6.4'))
        self._creditline_payment(self.node1_creditline, D('1.3'))
        self._creditline_payment(self.node2_creditline, D('10'), succeed=False)
        self._creditline_payment(self.node2_creditline, D('4'))
        self.assertEquals(self.node1_creditline.balance, D('-3.7'))

class SimpleMultiHopPaymentTest(RippleTest):
    multi_db = True

    def setUp(self):
        self.n1 = Node.objects.create(alias=1)
        self.n2 = Node.objects.create(alias=2)
        self.n3 = Node.objects.create(alias=3)
        self.a12 = Account.objects.create_account(self.n1, self.n2)
        self.a23 = Account.objects.create_account(self.n2, self.n3)
        self.cl12 = CreditLine.objects.get(account=self.a12, node=self.n1)
        self.cl21 = CreditLine.objects.get(account=self.a12, node=self.n2)
        self.cl23 = CreditLine.objects.get(account=self.a23, node=self.n2)
        self.cl32 = CreditLine.objects.get(account=self.a23, node=self.n3)

        self._set_limit(self.cl12, D('5'))
        self._set_limit(self.cl21, D('10'))
        self._set_limit(self.cl23, D('7'))
        
    def test_payment(self):
        self._payment(self.n1, self.n3, 1)

    def test_over_limit(self):
        self._payment(self.n1, self.n3, 6, succeed=False)

    def test_against_zero_limit(self):
        self._payment(self.n3, self.n1, 1, succeed=False)

    def test_multi_payment(self):
        self._payment(self.n1, self.n3, 3)
        self._payment(self.n3, self.n1, 1)
        self._payment(self.n2, self.n3, 4)
        self._payment(self.n1, self.n3, 10, succeed=False)
        self._payment(self.n2, self.n1, 5)
        
class MinCostFlowTest(TestCase):
    def test_one_edge(self):
        G = nx.DiGraph()
        nodes = [(1, {'demand': -1}),
                 (2, {'demand': 1}),
                 ]
        weight = 3
        edges = [(1, 2, {'capacity': 2, 'weight': weight}),
                 ]

        G.add_nodes_from(nodes)
        G.add_edges_from(edges)

        cost, flow_dict = min_cost_flow(G)
        self.assertEquals(cost, 3)
        self.assertEquals(flow_dict, {1: {2: {0: 1}}, 2: {}})

    def test_simple_digraph(self):
        G = nx.DiGraph()
        G.add_node('a', demand=-5)
        G.add_node('d', demand=5)
        G.add_edge('a', 'b', weight=3, capacity=4)
        G.add_edge('a', 'c', weight=6, capacity=10)
        G.add_edge('b', 'd', weight=1, capacity=9)
        G.add_edge('c', 'd', weight=2, capacity=5)
        cost, flow_dict = min_cost_flow(G)
        soln = {'a': {'b': {0: 4}, 'c': {0: 1}},
                'b': {'d': {0: 4}},
                'c': {'d': {0: 1}},
                'd': {}}
        self.assertEquals(cost, 24)
        self.assertEquals(flow_dict, soln)
        
    def test_negcycle_infcap(self):
        G = nx.DiGraph()
        G.add_node('s', demand = -5)
        G.add_node('t', demand = 5)
        G.add_edge('s', 'a', weight = 1, capacity = 3)
        G.add_edge('a', 'b', weight = 3)
        G.add_edge('c', 'a', weight = -6)
        G.add_edge('b', 'd', weight = 1)
        G.add_edge('d', 'c', weight = -2)
        G.add_edge('d', 't', weight = 1, capacity = 3)
        self.assertRaises(nx.NetworkXUnbounded, min_cost_flow, G)

    def test_sum_demands_not_zero(self):
        G = nx.DiGraph()
        G.add_node('s', demand = -5)
        G.add_node('t', demand = 4)
        G.add_edge('s', 'a', weight = 1, capacity = 3)
        G.add_edge('a', 'b', weight = 3)
        G.add_edge('a', 'c', weight = -6)
        G.add_edge('b', 'd', weight = 1)
        G.add_edge('c', 'd', weight = -2)
        G.add_edge('d', 't', weight = 1, capacity = 3)
        self.assertRaises(nx.NetworkXUnfeasible, min_cost_flow, G)

    def test_no_flow_satisfying_demands(self):
        G = nx.DiGraph()
        G.add_node('s', demand = -5)
        G.add_node('t', demand = 5)
        G.add_edge('s', 'a', weight = 1, capacity = 3)
        G.add_edge('a', 'b', weight = 3)
        G.add_edge('a', 'c', weight = -6)
        G.add_edge('b', 'd', weight = 1)
        G.add_edge('c', 'd', weight = -2)
        G.add_edge('d', 't', weight = 1, capacity = 3)
        self.assertRaises(nx.NetworkXUnfeasible, nx.network_simplex, G)

    def test_transshipment(self):
        G = nx.DiGraph()
        G.add_node('a', demand = 1)
        G.add_node('b', demand = -2)
        G.add_node('c', demand = -2)
        G.add_node('d', demand = 3)
        G.add_node('e', demand = -4)
        G.add_node('f', demand = -4)
        G.add_node('g', demand = 3)
        G.add_node('h', demand = 2)
        G.add_node('r', demand = 3)
        G.add_edge('a', 'c', weight = 3)
        G.add_edge('r', 'a', weight = 2)
        G.add_edge('b', 'a', weight = 9)
        G.add_edge('r', 'c', weight = 0)
        G.add_edge('b', 'r', weight = -6)
        G.add_edge('c', 'd', weight = 5)
        G.add_edge('e', 'r', weight = 4)
        G.add_edge('e', 'f', weight = 3)
        G.add_edge('h', 'b', weight = 4)
        G.add_edge('f', 'd', weight = 7)
        G.add_edge('f', 'h', weight = 12)
        G.add_edge('g', 'd', weight = 12)
        G.add_edge('f', 'g', weight = -1)
        G.add_edge('h', 'g', weight = -10)
        flowCost, H = min_cost_flow(G)
        soln = {'a': {'c': {0: 0}},
                'b': {'a': {0: 0}, 'r': {0: 2}},
                'c': {'d': {0: 3}},
                'd': {},
                'e': {'r': {0: 3}, 'f': {0: 1}},
                'f': {'d': {0: 0}, 'g': {0: 3}, 'h': {0: 2}},
                'g': {'d': {0: 0}},
                'h': {'b': {0: 0}, 'g': {0: 0}},
                'r': {'a': {0: 1}, 'c': {0: 1}}}
        self.assertEquals(flowCost, 41)
        self.assertEquals(H, soln)
    
    def test_digraph1(self):
        # From Bradley, S. P., Hax, A. C. and Magnanti, T. L. Applied
        # Mathematical Programming. Addison-Wesley, 1977.
        G = nx.DiGraph()
        G.add_node(1, demand = -20)
        G.add_node(4, demand = 5)
        G.add_node(5, demand = 15)
        G.add_edges_from([(1, 2, {'capacity': 15, 'weight': 4}),
                          (1, 3, {'capacity': 8, 'weight': 4}),
                          (2, 3, {'weight': 2}),
                          (2, 4, {'capacity': 4, 'weight': 2}),
                          (2, 5, {'capacity': 10, 'weight': 6}),
                          (3, 4, {'capacity': 15, 'weight': 1}),
                          (3, 5, {'capacity': 5, 'weight': 3}),
                          (4, 5, {'weight': 2}),
                          (5, 3, {'capacity': 4, 'weight': 1})])
        flowCost, H = min_cost_flow(G)
        soln = {1: {2: {0:12}, 3: {0:8}},
                2: {3: {0:8}, 4: {0:4}, 5: {0:0}},
                3: {4: {0:11}, 5: {0:5}},
                4: {5: {0:10}},
                5: {3: {0:0}}}
        self.assertEquals(flowCost, 150)
        self.assertEquals(H, soln)

    def test_networkx_simplex_killer(self):
        G = nx.DiGraph()
        nodes = [(1, {}),
                 (2, {'demand': -4}),
                 (3, {'demand': 4}),
                 ]
        edges = [(1, 2, {'capacity': 3, 'weight': 600000}),
                 (2, 1, {'capacity': 2, 'weight': 0}),
                 (2, 3, {'capacity': 5, 'weight': 714285}),
                 (3, 2, {'capacity': 2, 'weight': 0}),
                 ]
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        flow_cost, flow_dict = min_cost_flow(G)
        soln = {1: {2: {0: 0}},
                2: {1: {0: 0}, 3: {0: 4}},
                3: {2: {0: 0}}}
        self.assertEquals(flow_dict, soln)
        self.assertEquals(flow_cost, 714285 * 4)
        
    def test_simple_multi(self):
        G = nx.MultiDiGraph()
        nodes = [(1, {'demand': -2}),
                 (2, {'demand': 2}),
                 ]
        edges = [(1, 2, {'capacity': 2, 'weight': 1}),
                 (1, 2, {'capacity': 1, 'weight': 0}),
                 ]
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        flow_cost, flow_dict = min_cost_flow(G)
        soln = {1: {2: {0: 1, 1: 1}},
                2: {}}
        self.assertEquals(flow_dict, soln)
        self.assertEquals(flow_cost, 1)
        
    def test_random(self):
        random.seed(0)
        for i in range(10):
            self.run_random_trial()
    
    def run_random_trial(self):
        G = nx.MultiDiGraph()
        nodes = range(1, 10)
        edges = generate_edges(nodes, 50)
        G.add_edges_from(edges)
        source = random.choice(G.nodes())
        while True:
            target = random.choice(G.nodes())
            if target != source:
                break
        amount = random.randint(1, 10)
        G.node[source]['demand'] = -amount
        G.node[target]['demand'] = amount

        cost, flow_dict, exception = None, None, None
        try:
            cost, flow_dict = min_cost_flow(G)
        except nx.NetworkXException as e:
            exception = e

        H = unmulti(G)
        try:
            cost2, flow_dict2 = nx.network_simplex(H)
        except nx.NetworkXException as e:
            self.assertEquals(type(e) != type(exception))
            self.assertEquals(cost, None)
        else:
            self.assertEquals(cost, cost2)
            self.assertEquals(exception, None)
        
