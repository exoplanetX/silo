"""Finite exact checks of a fixed-certificate reporter; not a pricing solver.

Sorted arrays implement immutable snapshots. Rebuilding snapshots for insert/
delete checks does NOT implement logarithmic-time balanced-tree lifecycle work.
"""
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
import json


@dataclass(frozen=True)
class Certificate:
    cid: str
    intercept: F
    difference: tuple[int, ...]
    root: str


def dot(difference, dual):
    return sum((value * price for value, price in zip(difference, dual)), F(0))


def snapshot(certificates):
    groups = defaultdict(list)
    for item in certificates:
        groups[item.difference].append((item.intercept, item.cid))
    return {d: (sorted(rows), sorted(b for b, _ in rows)) for d, rows in groups.items()}


def report_cost_failures(index, old_dual, new_dual):
    """Report current-point valid -> invalid for a fixed certificate catalog.

    Structural witness failures and actual subtree restoration are out of scope.
    """
    failed = set()
    for d, (rows, thresholds) in index.items():
        old_projection = dot(d, old_dual)
        new_projection = dot(d, new_dual)
        if new_projection > old_projection:
            left = bisect_left(thresholds, old_projection)
            right = bisect_left(thresholds, new_projection)
            failed.update(cid for _, cid in rows[left:right])
    return failed


def direct_report(certificates, old_dual, new_dual):
    return {
        item.cid for item in certificates
        if item.intercept - dot(item.difference, old_dual) >= 0
        and item.intercept - dot(item.difference, new_dual) < 0
    }


out = {}
normals = [d for d in product((-1, 0, 1), repeat=3) if sum(x != 0 for x in d) <= 2]
certificates = [
    Certificate(f'c{n}_{b}_{copy}', F(b), d, f'root{n}_{b}_{copy}')
    for n, d in enumerate(normals) for b in range(-2, 3) for copy in range(2)
]
index = snapshot(certificates)
points = list(product(map(F, (-2, 0, 2)), repeat=3))
queries = 0
for old in points:
    for new in points:
        assert report_cost_failures(index, old, new) == direct_report(certificates, old, new)
        queries += 1
out['fixed_catalog_exhaustive'] = {
    'dimension': 3, 'support_limit': 2, 'certificates': len(certificates),
    'groups': len(index), 'old_new_queries': queries,
    'includes_zero_negative_normals_duplicate_thresholds_equalities_and_reverse_jumps': True,
}

# One signature: demonstrate projection work separation and explicit-output limit.
many = [Certificate(f'w{i}', F(i + 10), (1,), f'independent_root{i}') for i in range(4096)]
many_index = snapshot(many)
quiet = report_cost_failures(many_index, (F(0),), (F(1),))
worst = report_cost_failures(many_index, (F(0),), (F(5000),))
assert not quiet and len(worst) == len(many)
out['report_layer_separation'] = {
    'certificates': len(many), 'groups': len(many_index),
    'quiet_query_failed_ids': len(quiet), 'worst_query_failed_ids': len(worst),
    'direct_projection_evaluations_per_new_point': len(many),
    'group_projection_evaluations_per_new_point': len(many_index),
    'scope': 'synthetic fixed catalog operation counts, not graph or runtime speedup',
}

# Lifecycle semantics only: each mutation rebuilds the immutable snapshot.
small = [Certificate('a', F(1), (1, 0), 'ra'), Certificate('b', F(2), (1, 0), 'rb')]
small = [item for item in small if item.cid != 'a']
small.append(Certificate('c', F(4), (1, 0), 'rc'))
assert report_cost_failures(snapshot(small), (F(0), F(0)), (F(3), F(0))) == {'b'}
invalid_insert = Certificate('reject', F(1), (1, 0), 'rr')
assert invalid_insert.intercept - dot(invalid_insert.difference, (F(3), F(0))) < 0
out['lifecycle_semantics_only'] = {
    'delete_insert_snapshot_result_valid': True,
    'inserting_an_already_invalid_pruning_witness_must_be_rejected': True,
    'logarithmic_lifecycle_implementation': False,
}

# Observed equality along one direction is insufficient for future grouping.
assert dot((1, 0), (F(1), F(0))) == dot((1, 1), (F(1), F(0)))
assert dot((1, 0), (F(0), F(2))) != dot((1, 1), (F(0), F(2)))
out['historical_projection_grouping_counterexample'] = True

# An actual small two-resource DAG with binary coverage and independent cut roots.
# Edge tuple = (head, original cost, optional task coordinate, resource increments).
graph = defaultdict(list)
for j, cost in enumerate((1, 2, 4), start=1):
    u = f'u{j}'
    graph['s'].append((u, F(0), j - 1, (4*j, 4*(4-j))))
    graph[u].append(('a', F(0), 3, (0, 0)))
    graph[u].append(('b', F(cost), 4, (1, 1)))
graph['a'].append(('v', F(0), None, (0, 0)))
graph['b'].append(('v', F(0), None, (0, 0)))
graph['v'].extend([('x', F(0), None, (8, 0)), ('y', F(0), None, (0, 8))])
graph['x'].append(('t', F(0), None, (0, 0)))
graph['y'].append(('t', F(0), None, (0, 0)))
prefixes, complete = [], []


def enumerate_paths(node, cost, coverage, resource, path):
    if node == 'v':
        prefixes.append((cost, coverage, resource, path))
    if node == 't':
        complete.append((cost, coverage, resource, path))
        return
    for head, edge_cost, task, use in graph[node]:
        updated_resource = tuple(a+b for a, b in zip(resource, use))
        if any(value > 20 for value in updated_resource):
            continue
        updated_coverage = list(coverage)
        if task is not None:
            updated_coverage[task] += 1
        assert all(value in (0, 1) for value in updated_coverage)
        enumerate_paths(head, cost+edge_cost, tuple(updated_coverage), updated_resource, path+(head,))


enumerate_paths('s', F(0), (0,)*5, (0, 0), ('s',))
roots = []
for j in range(1, 4):
    pair = [p for p in prefixes if p[3][1] == f'u{j}']
    first = next(p for p in pair if p[3][2] == 'a')
    second = next(p for p in pair if p[3][2] == 'b')
    assert all(x <= y for x, y in zip(first[2], second[2]))
    d = tuple(y-x for x, y in zip(first[1], second[1]))
    assert d == (0, 0, 0, -1, 1)
    roots.append(Certificate(f'root{j}', second[0]-first[0], d, f'root{j}'))
for p in prefixes:
    for q in prefixes:
        if p[3][1] != q[3][1]:
            assert not all(x <= y for x, y in zip(p[2], q[2]))
old, new = (F(0),)*5, (F(0), F(0), F(0), F(0), F(5, 2))
assert report_cost_failures(snapshot(roots), old, new) == {'root1', 'root2'}
old_value = min(c-dot(q, old) for c, q, _, _ in complete)
new_value = min(c-dot(q, new) for c, q, _, _ in complete)
assert len(prefixes) == 6 and len(complete) == 10
assert old_value == 0 and new_value == F(-3, 2)
assert not any(p[3] == ('s', 'u1', 'b', 'v', 'y', 't') for p in complete)
out['two_resource_binary_coverage_dag'] = {
    'vertices': len(set(graph) | {edge[0] for rows in graph.values() for edge in rows}),
    'prefixes_at_v': len(prefixes), 'feasible_complete_paths': len(complete),
    'coverage_dimension': 5, 'difference_support': 2,
    'independent_roots': 3, 'distinct_signatures': 1,
    'thresholds': ['1', '2', '4'], 'failed_ids': ['root1', 'root2'],
    'old_minimum': str(old_value), 'new_minimum': str(new_value),
    'resources_remove_two_complete_paths': True,
    'scope': 'full path enumeration; no incremental subtree-repair implementation',
}

# Explicit parity-layer family: small signatures can miss all dominance pairs.
# At layer i, the two states remember parity of selected decisions. Selecting
# decision i adds its own pair of task bits, cost 1 and one resource unit.
# The two intermediate task vertices per entering parity can be expanded to an
# ordinary DAG with 6*n+3 vertices including the terminal. Task copies share
# feature coordinates; a path can still use each coordinate only once.
family_results = []
for n in range(2, 11):
    layer = {0: [(0, 0, 0)], 1: []}  # (feature bitmask, cost, resource)
    for i in range(n):
        next_layer = {0: [], 1: []}
        for parity, labels in layer.items():
            for mask, cost, resource in labels:
                next_layer[parity].append((mask, cost, resource))
                next_layer[1-parity].append((mask | (3 << (2*i)), cost+1, resource+1))
        for parity, labels in next_layer.items():
            assert len({mask for mask, _, _ in labels}) == len(labels)
            for mask, cost, resource in labels:
                assert (mask.bit_count() // 2) % 2 == parity
                assert cost == resource == mask.bit_count() // 2
            for first in range(len(labels)):
                for second in range(first):
                    assert (labels[first][0] ^ labels[second][0]).bit_count() >= 4
        layer = next_layer
    accepted = layer[0]
    assert len(accepted) == 2**(n-1)
    assert (0, 0, 0) in accepted
    assert all(cost >= 0 and resource >= 0 for _, cost, resource in accepted)
    family_results.append({
        'decisions': n, 'ordinary_dag_vertices': 6*n+3,
        'accepted_labels_with_only_support_two_dominance': len(accepted),
        'accepted_labels_after_unrestricted_dominance_at_zero_dual': 1,
    })
out['parity_layer_label_inflation_counterexample'] = {
    'checked_decisions': [2, 10], 'instances': family_results,
    'no_support_two_pair_at_any_layer_state': True,
    'scope': 'dominance-policy inflation only; no lower bound against other pruning or state compression',
}

print(json.dumps({'scope': 'finite exact reporter and graph-example checks only', 'checks': out}, indent=2))
