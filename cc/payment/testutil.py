import random

import networkx as nx

def generate_edges(nodes, n_edges, max_cap=10, min_weight=0, max_weight=10,
                   p_reverse=0.5):
    edges = []
    edge_set = set()
    multi = 0
    for i in xrange(n_edges):
        u = random.choice(nodes)
        while True:
            v = random.choice(nodes)
            if v != u:
                break
        if (u, v) in edge_set:
            multi += 1
        else:
            edge_set.add((u, v))
        edges.append(
            (u, v, {'capacity': random.randint(1, max_cap),
                    'weight': random.randint(min_weight, max_weight)}))
        if random.random() < p_reverse:
            edges.append(
                (v, u, {'capacity': random.randint(1, max_cap),
                        'weight': random.randint(min_weight, max_weight)}))
    return edges

def unmulti(G):
    # Convert multidigraph to regular digraph by inserting nodes in the middle
    # of each edge.
    H = nx.DiGraph()
    for n, data in G.nodes(data=True):
        H.add_node(n, **data)
    for u, v, k, data in G.edges(keys=True, data=True):
        i = '%s__%s__%s' % (u, v, k)
        H.add_edge(u, i, **data)
        H.add_edge(i, v)
    return H

