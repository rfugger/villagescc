import networkx as nx
from networkx.utils import generate_unique_node

def min_cost_flow(G, demand='demand', capacity='capacity', weight='weight'):
    """
    Uses successive shortest path algorithm:
    http://community.topcoder.com/tc?module=Static&d1=tutorials&d2=minimumCostFlow2
    """
    if not G.is_directed():
        raise nx.NetworkXError("Undirected graph not supported (yet).")
    if not nx.is_connected(G.to_undirected()):
        raise nx.NetworkXError("Not connected graph not supported (yet).")
    demand_sum = sum(d[demand] for v, d in G.nodes_iter(data=True)
                     if demand in d)
    if demand_sum != 0:
        raise nx.NetworkXUnfeasible("Sum of the demands should be 0.")

    H = nx.MultiDiGraph(G)

    for u, v, key in H.edges_iter(keys=True):
        if not isinstance(key, (int, long)):
            raise nx.NetworkXError("Edge keys must be integers.")
    
    # Add source and sink nodes.
    source = generate_unique_node()
    sink = generate_unique_node()
    for node, data in H.nodes_iter(data=True):
        node_demand = data.get(demand)
        if node_demand:
            if node_demand > 0:
                H.add_edge(node, sink, capacity=node_demand, weight=0)
            else:
                H.add_edge(source, node, capacity=-node_demand, weight=0)

    # TODO: Transform R weights to be nonnegative at each iteration,
    # using bellman-ford shortest-path length source -> n as the potential
    # for each node.  Then can use dijskstra_path instead of bellman_ford.

    flow_cost = 0
    search = source in H.nodes()  # No source => no demand => no flow.
    while search:
        R = _residual_graph(H, capacity=capacity, weight=weight)
        try:
            #path = nx.dijkstra_path(R, source, sink, weight=weight)
            path = _bellman_ford_path(R, source, sink, weight=weight)
        except nx.NetworkXNoPath:
            # Check that demands have been satisfied.
            for node, edge_dict in H[source].items():
                # Only one edge to each supply node from source.
                data = edge_dict[0]
                if data['capacity'] != data.get('flow', 0):
                    raise nx.NetworkXUnfeasible(
                        "No flow satisfying all demands.")
            break

        new_flow, path_edges = _max_path_flow(
            R, path, capacity=capacity, weight=weight)
        new_cost =  _augment_flow(H, path_edges, new_flow, R)
        flow_cost += new_cost

    if search:
        H.remove_node(source)
        H.remove_node(sink)
    flow_dict = _create_flow_dict(H)
    return flow_cost, flow_dict
        
def _residual_graph(G, capacity, weight):
    """
    Create a residual flow graph with the same nodes as G and edges as follows:

    For each edge e of G,

    1) if flow is less than capacity, then the residual has an edge in the same
    direction as e, with capacity equal to remaining capacity on e, and weight
    equal to e.

    2) if flow is greater than zero, then the residual has an edge in the
    opposite direction as e, with capacity equal to flow on e, and weight
    the negative of e's.

    Each edge of the residual graph stores the key of the corresponding edge in
    the original flow graph in the orig_key attribute, and edges that represent
    potentially reversed flows have an 'is_reversed' attribute set to True.
    
    """
    R = nx.MultiDiGraph()
    for u, v, key, data in G.edges_iter(keys=True, data=True):
        flow = data.get('flow', 0)
        edge_weight = data.get(weight, 0)
        edge_capacity = data.get(capacity)
        if edge_capacity == 0:
            continue
        if edge_capacity is None:  # Infinite.
            new_capacity = None
        else:
            new_capacity = edge_capacity - flow
        if new_capacity is None or new_capacity > 0:
            edge_attrs = {capacity: new_capacity,
                          weight: edge_weight,
                          'orig_key': key}
            R.add_edge(u, v, **edge_attrs)
        if flow > 0:
            edge_attrs = {capacity: flow,
                          weight: -edge_weight,
                          'orig_key': key,
                          'is_reversed': True}
            R.add_edge(v, u, **edge_attrs)
    return R
    

# TODO: Remove this once we're using dijkstra to find shortest paths.
def _bellman_ford_path(G, source, target, weight):
    "Returns shortest path using bellman_ford algorithm."
    pred, dist = nx.bellman_ford(G, source, weight)
    if target not in pred:
        raise nx.NetworkXNoPath(
            "Node %s not reachable from %s." % (source, target))
    # Since predecessors are given, build path backwards, then reverse.
    path = []
    curr = target
    while curr != source:
        path.append(curr)
        curr = pred[curr]
    path.append(source)
    path.reverse()
    return path
            
def _max_path_flow(G, path, capacity, weight):
    """
    Returns max flow on path, as well as list of edges with keys for path,
    and whether each edge represents a reversal of present flow.
    """
    min_edge_capacity = float('inf')
    flow_edges = []
    for index, u in enumerate(path[:-1]):
        v = path[index + 1]
        # Use only minimum weight edge, because that's the only one considered
        # when finding shortest path.
        
        # TODO: Build own shortest path finder that returns specific
        # edges used form multigraph, not just nodes in path -- saves
        # getting min-weight edge all over again...?
        key, data = _min_weight_edge(G[u][v], weight)
        edge_capacity = data.get(capacity)
        if edge_capacity is None: edge_capacity = float('inf')
        min_edge_capacity = min(edge_capacity, min_edge_capacity)
        flow_edges.append((u, v, key, data.get('is_reversed', False)))
    return min_edge_capacity, flow_edges

def _min_weight_edge(edge_dict, weight):
    "Returns key and data for min. weight edge in multi-edge dict."
    min_weight = float('inf')
    min_weight_edge = None
    for key, data in edge_dict.items():
        edge_weight = data[weight]
        if edge_weight < min_weight:
            min_weight = edge_weight
            min_weight_edge = (key, data)
    return min_weight_edge
        
def _augment_flow(G, flow_edges, flow, R):
    "Add flow across flow_edges to G."
    cost = 0
    for u, v, residual_key, is_reversed in flow_edges:
        key = R[u][v][residual_key]['orig_key']
        if not is_reversed:
            data = G[u][v][key]
            edge_flow = flow
        else:
            data = G[v][u][key]
            edge_flow = -flow
        data['flow'] = data.get('flow', 0) + edge_flow
        cost += edge_flow * data.get('weight', 0)
    return cost

def _create_flow_dict(G):
    "Creates the flow dict of dicts of dicts for graph G."
    H = nx.MultiDiGraph(G)
    flowDict = dict([(u,
                      dict([(v, {}) for v in H[u]]))
                     for u in H])
    for u, v, key, data in H.edges_iter(keys=True, data=True):
        flowDict[u][v][key] = data.get('flow', 0)
    return flowDict

