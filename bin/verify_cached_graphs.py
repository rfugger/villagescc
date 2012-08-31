#!/usr/bin/env python

import sys
from pprint import pprint as pp

from cc.payment import flow

def verify():
    for ignore_balances in (True, False):
        graph = flow.build_graph(ignore_balances)
        cached = flow.get_cached_graph(ignore_balances)
        if not cached:
            flow.set_cached_graph(graph, ignore_balances)
            continue
        diff = compare(cached, graph)
        if diff:
            pp(diff)
            return False
    return True

def compare(g1, g2):
    e1 = set(normalize(g1.edges(data=True)))
    e2 = set(normalize(g2.edges(data=True)))
    return e1.symmetric_difference(e2)

def normalize(edge_list):
    return ((src, dest, data['capacity'], data['weight'], data['creditline_id'])
            for src, dest, data in edge_list)

if __name__ == '__main__':
    if verify():
        print 'OK.'
        sys.exit(0)
    else:
        print 'Mismatch.'
        sys.exit(1)
