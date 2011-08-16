import random

import networkx as nx

def generate_edges(nodes, n_edges, max_cap=10, min_weight=0, max_weight=10,
                   p_reverse=0.5):
    edges = []
    edge_set = set()
    for i in xrange(n_edges):
        u = random.choice(nodes)
        while True:
            v = random.choice(nodes)
            if v != u:
                break
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

