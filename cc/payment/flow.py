"Network flow computations."

import networkx as nx
from decimal import Decimal as D

from django.conf import settings

from cc.account.models import CreditLine
from cc.ripple import SCALE

class PaymentError(Exception):
    "Base class for all payment exceptions."
    pass

class NoRoutesError(PaymentError):
    "No possible routes between payer and recipient."
    pass

class InsufficientCreditError(PaymentError):
    "Not enough max flow between payer and recipient to make payment."
    pass


class FlowGraph(object):
    def __init__(self, payer, recipient):
        "Takes payer and recipient nodes."
        self.payer = payer
        self.recipient = recipient
        self.graph = self._build_graph(seed_node=self.payer)

    def min_cost_flow(self, amount):
        """
        Determine minimum cost route for given amount between payer and
        recipient.
        
        Raises NoRoutesError if there is no route from payer to recipient.
        Raises InsufficientCreditError if the network cannot support the
        specified flow amount.
        """
        self._set_endpoint_demand(amount)
        if self.recipient.id not in self.graph.nodes():
            raise NoRoutesError()
        try:
            _, flow_dict = nx.network_simplex(self.graph)
        except nx.NetworkXUnfeasible:
            raise InsufficientCreditError()
        else:
            amounts = creditline_amounts(flow_dict, self.graph)
            return amounts

    def max_flow(self):
        if self.recipient.id not in self.graph.nodes():
            return 0
        try:
            amount = nx.max_flow(
                self.graph, self.payer.id, self.recipient.id)
        except nx.NetworkXUnbounded:
            return D('Infinity')
        else:
            return float_to_decimal(amount)

    def _build_graph(self, seed_node):
        """
        Get flow graph for performing payment computations.
        
        A flow graph is a connected directed networkx DiGraph where the edges
        represent account-halves and exchanges between them performed by various
        users.  Payment always flows from credit line owner to the other
        partner.

        A flow graph contains all credit lines that could possibly be used to
        transfer value from seed_node to anyone else.  It may also contain other
        account-halves so it can be cached and used for other payments.  For
        example, the flow graph might contain the set of all nodes that could
        pay or be paid by the payer.

        The flow graph assigns costs to each credit line edge in order prioritize
        settling balances.

        To use this graph in the min cost demand flow algorithm, assign the payer
        a supply (negative demand) and the recipient a demand equal to the payment
        amount.

        Flow graph nodes are account.models.Node database IDs, not Node.aliases!
        """
        # TODO: Generate complete connected flow graph such that for every
        # vertex in graph, it includes every possible incoming and outgoing
        # edge.  Assign each such flow graph an ID, and store the ID of
        # the unique flow graph it belongs to at each CreditLine so the flow
        # graph can be quickly generated by loading the account halves in one
        # go.  Then cache each complete flow graph for re-use in other payments.

        graph = nx.DiGraph()
        visited_creditline_ids = {}  # Indexed by user profile id.
        pending_creditlines = list(seed_node.out_creditlines())
        while pending_creditlines:
            curr_creditline = pending_creditlines.pop(0)

            # Add creditline edge(s) to graph.
            self._add_creditline_to_graph(graph, curr_creditline)
            visited_creditline_ids.setdefault(
                curr_creditline.node_id, set()).add(curr_creditline.id)
            
            # Add partner's unvisited outgoing credit lines to pending
            # list for eventual visitation.
            partner = curr_creditline.partner
            next_creditlines = partner.out_creditlines().exclude(
                pk__in=visited_creditline_ids.get(partner.id, []))
            pending_creditlines += list(next_creditlines)
        return graph
    
    def _add_creditline_to_graph(self, graph, creditline):
        src = creditline.node_id
        dest = creditline.partner.id
        chunks = edge_weight(creditline)
        # Add first edge normally.
        capacity, weight = chunks[0]
        graph.add_edge(src, dest, weight=weight, creditline=creditline)
        if capacity != float('inf'):
            graph[src][dest]['capacity'] = float(capacity)
        for i, chunk in enumerate(chunks[1:]):
            # For multiple edges between src and dest, network_simplex
            # doesn't handle multigraph (as of 1.5), so insert dummy nodes
            # in the middle of each extra edge as a workaround. (See
            # https://networkx.lanl.gov/trac/ticket/607.
            capacity, weight = chunk
            dummy_node = u'%s__%s' % (dest, i)
            graph.add_edge(src, dummy_node, weight=weight,
                           capacity=float(capacity), creditline=creditline)
            graph.add_edge(dummy_node, dest)  # Zero weight, infinite capacity.
            # Dummy edge has no creditline, so can be ignored later.
            
    def _set_endpoint_demand(self, amount):
        "Add payer and recipient nodes with corresponding demands values."
        # XXX Convert decimal amounts to float for networkx.
        self.graph.node[self.payer.id]['demand'] = float(-amount)
        self.graph.node[self.recipient.id]['demand'] = float(amount)


def edge_weight(creditline):
    """
    Assigns a cost to using this creditline in a payment.  Cashing in existing
    IOUs has zero cost.  Issuing existing IOUs has a cost of 1 + distance of
    current balance from zero relative to the limit.

    Returns a tuple of (capacity, weight) tuples representing chunks of usable
    credit capacity, since when there is a positive balance, using up that
    balance will carry different weight than anything beyond.

    (TODO: Ideally, costs would be in proportion to the amount of credit
    remaining *after* the payment, but that is not known yet, and the naive min
    cost demand flow algorithm used can't factor that in.)
    """
    if creditline.limit is None:
        # No cost if no limit -- treat as if balance is always 0.
        return ((float('inf'), 0),)  # Capacity is infinite.
    if creditline.balance > 0:
        # Return two chunks: one to get to zero balance, one for remainder.
        # Give positive cost only to issuing in new IOUs.
        return ((creditline.balance, 0), (creditline.limit, 1))
    else:
        # No positive balance to cash in.
        capacity = creditline.balance + creditline.limit
        cost = 1.0 + (float(creditline.balance / creditline.limit))
        return ((capacity, cost),)

def creditline_amounts(flow_dict, graph):
    """
    Returns a list of (creditline, amount) tuples that represent the
    flow of a payment. Takes a flow_dict from network_simplex.
    """
    amount_dict = {}  # Index by creditline.
    for src_node, node_flow_dict in flow_dict.items():
        for dest_node, amount in node_flow_dict.items():
            amount = float_to_decimal(amount)
            if amount == 0:  # Ignore zero amounts.
                continue
            creditline = graph[src_node][dest_node].get('creditline')
            if not creditline:  # Dummy edge.
                continue
            amount_dict.setdefault(creditline, 0)
            amount_dict[creditline] += float_to_decimal(amount)
    return amount_dict.items()
            
def float_to_decimal(amount):
    "Convert float to decimal."
    # Convert float to string with number of decimal places stored in db.
    float_interp_str = '%%.%df' % SCALE  # '%.2f'
    amount_str = float_interp_str % amount
    return D(amount_str)

            
