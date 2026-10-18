"""Exact finite research probes, outside the SILO implementation.

Contracts: finite topologically numbered DAG; fixed actions; binary task service;
nonnegative additive integer resources. Dense arrays and rebuilt sorted snapshots
are reference representations, not an efficient dynamic-index implementation.
"""
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
import json
import random


@dataclass(frozen=True)
class Edge:
    eid: int
    u: int
    v: int
    cost: F
    q: tuple
    resource: tuple = ()


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), F(0))


def weights(edges, dual):
    return {e.eid: e.cost-dot(e.q, dual) for e in edges}


def shortest(vertices, edges, dual):
    incoming = defaultdict(list)
    for edge in edges:
        incoming[edge.v].append(edge)
    w = weights(edges, dual)
    dist, parent = {0: F(0)}, {}
    for v in range(1, vertices):
        candidates = [(dist[e.u]+w[e.eid], e.eid, e) for e in incoming[v] if e.u in dist]
        if candidates:
            value, _, edge = min(candidates, key=lambda item: (item[0], item[1]))
            dist[v], parent[v] = value, edge
    return dist, parent


def tree_data(vertices, parents, dimension):
    costs, features = {0: F(0)}, {0: (0,)*dimension}
    for v in range(1, vertices):
        e = parents[v]
        costs[v] = costs[e.u]+e.cost
        features[v] = tuple(a+b for a, b in zip(features[e.u], e.q))
    return costs, features


def tree_index(edges, costs, features):
    groups = defaultdict(list)
    for e in edges:
        d = tuple(a+b-c for a, b, c in zip(features[e.u], e.q, features[e.v]))
        b = costs[e.u]+e.cost-costs[e.v]
        groups[d].append((b, e.eid))
    return {d: sorted(rows) for d, rows in groups.items()}


def all_negative(index, dual):
    result = set()
    for d, rows in index.items():
        z = dot(d, dual)
        end = bisect_left(rows, (z, -1))  # edge IDs are nonnegative; strict b < z
        result.update(eid for _, eid in rows[:end])
    return result


def reference_repair(vertices, edges, dual, costs, features, negative_ids):
    w = weights(edges, dual)  # reference probe computes all weights; cost is counted separately in theory
    outgoing, incoming = defaultdict(list), defaultdict(list)
    for e in edges:
        outgoing[e.u].append(e)
        incoming[e.v].append(e)
    affected = {e.v for e in edges if e.eid in negative_ids}
    queue = list(affected)
    while queue:
        u = queue.pop()
        for e in outgoing[u]:
            if e.v not in affected:
                affected.add(e.v)
                queue.append(e.v)
    dist = {v: costs[v]-dot(features[v], dual) for v in range(vertices) if v not in affected}
    for v in sorted(affected):
        dist[v] = min(dist[e.u]+w[e.eid] for e in incoming[v])
    return dist, affected


def future_sets(vertices, edges):
    outgoing = defaultdict(list)
    for e in edges:
        assert e.u < e.v
        outgoing[e.u].append(e)
    coreachable = {vertices-1}
    future = {v: frozenset() for v in range(vertices)}
    for v in reversed(range(vertices-1)):
        found = set()
        for e in outgoing[v]:
            if e.v in coreachable:
                coreachable.add(v)
                found.update(i for i, a in enumerate(e.q) if a)
                found.update(future[e.v])
        future[v] = frozenset(found)
    return future, coreachable


def expanded_graph(vertices, edges, capacities, remember_all=False, forget_all=False):
    future, coreachable = future_sets(vertices, edges)
    outgoing = defaultdict(list)
    for e in edges:
        outgoing[e.u].append(e)
    zero = (0,)*len(capacities)
    source = (0, zero, frozenset())
    by_vertex = defaultdict(set)
    by_vertex[0].add(source)
    lifted = []
    for v in range(vertices):
        for state in sorted(by_vertex[v], key=lambda x: (x[1], tuple(sorted(x[2])))):
            _, r, memory = state
            for e in outgoing[v]:
                if e.v not in coreachable:
                    continue
                served = frozenset(i for i, a in enumerate(e.q) if a)
                assert all(a in (0, 1) for a in e.q)
                if memory & served:
                    continue
                updated_r = tuple(a+b for a, b in zip(r, e.resource))
                if any(a > b for a, b in zip(updated_r, capacities)):
                    continue
                updated_m = memory | served
                if forget_all:
                    updated_m = frozenset()
                elif not remember_all:
                    updated_m &= future[e.v]
                target = (e.v, updated_r, updated_m)
                by_vertex[e.v].add(target)
                lifted.append((state, target, e))
    states = [state for v in range(vertices) for state in sorted(by_vertex[v], key=lambda x: (x[1], tuple(sorted(x[2]))))]
    number = {state: i for i, state in enumerate(states)}
    converted = [Edge(i, number[a], number[b], e.cost, e.q) for i, (a, b, e) in enumerate(lifted)]
    return states, converted, future


def terminal_minimum(states, converted, dual, terminal):
    dist, _ = shortest(len(states), converted, dual)
    return min(dist[i] for i, state in enumerate(states) if state[0] == terminal)


def enumerate_legal(vertices, edges, capacities):
    outgoing = defaultdict(list)
    for e in edges:
        outgoing[e.u].append(e)
    prefixes, completed = [], []
    def visit(v, resource, served, cost, coverage, path):
        prefixes.append((v, resource, served, cost, coverage, path))
        if v == vertices-1:
            completed.append((cost, coverage, path))
            return
        for e in outgoing[v]:
            tasks = frozenset(i for i, a in enumerate(e.q) if a)
            new_r = tuple(a+b for a, b in zip(resource, e.resource))
            if served & tasks or any(a > b for a, b in zip(new_r, capacities)):
                continue
            visit(e.v, new_r, served | tasks, cost+e.cost,
                  tuple(a+b for a, b in zip(coverage, e.q)), path+(e.eid,))
    dimension = len(edges[0].q)
    visit(0, (0,)*len(capacities), frozenset(), F(0), (0,)*dimension, ())
    return prefixes, completed


def verify_suffix_sufficiency(vertices, edges, capacities, prefixes, future):
    outgoing = defaultdict(list)
    for e in edges:
        outgoing[e.u].append(e)
    grouped, checked = {}, 0
    def legal_suffixes(v, resource, served):
        if v == vertices-1:
            return {()}
        result = set()
        for e in outgoing[v]:
            tasks = frozenset(i for i, a in enumerate(e.q) if a)
            new_r = tuple(a+b for a, b in zip(resource, e.resource))
            if served & tasks or any(a > b for a, b in zip(new_r, capacities)):
                continue
            result.update((e.eid,)+suffix for suffix in legal_suffixes(e.v, new_r, served | tasks))
        return result
    for v, r, served, _, _, _ in prefixes:
        key = (v, r, served & future[v])
        suffixes = legal_suffixes(v, r, served)
        if key in grouped:
            assert suffixes == grouped[key]
            checked += 1
        else:
            grouped[key] = suffixes
    return checked


def parity_graph(n):
    dimension = 2*n
    rows = []
    def add(u, v, cost=0, tasks=(), use=0):
        q = tuple(int(j in tasks) for j in range(dimension))
        rows.append(Edge(len(rows), u, v, F(cost), q, (use,)))
    # Each block: current parity states 6*i,6*i+1; four internal task copies;
    # next layer parity states 6*i+6,6*i+7.
    for i in range(n):
        for p in (0, 1):
            first, second = 6*i+2+2*p, 6*i+3+2*p
            add(6*i+p, 6*(i+1)+p)
            add(6*i+p, first, tasks=(2*i,))
            add(first, second, cost=1, tasks=(2*i+1,), use=1)
            add(second, 6*(i+1)+(1-p))
    terminal = 6*n+2
    add(6*n, terminal)
    return terminal+1, rows


out = {}
combined_state_repair_queries = 0

# The parity family: exact resource states versus proved redundant resource.
family = []
for n in range(2, 11):
    vertices, edges = parity_graph(n)
    states, lifted, future = expanded_graph(vertices, edges, (n,))
    projected_edges = [Edge(e.eid, e.u, e.v, e.cost, e.q, ()) for e in edges]
    projected, projected_lifted, _ = expanded_graph(vertices, projected_edges, ())
    full, _, _ = expanded_graph(vertices, edges, (n,), remember_all=True)
    prefixes, complete = enumerate_legal(vertices, edges, (n,))
    assert len(complete) == 2**(n-1)
    assert all(not memory for _, _, memory in states)
    assert all(r[0] <= n for _, r, _, _, _, _ in prefixes)  # whole-path redundancy
    assert sum(v == vertices-1 for v, _, _ in states) == n//2+1
    assert sum(v == vertices-1 for v, _, _ in projected) == 1
    _, anchor_parent = shortest(len(states), lifted, (F(0),)*(2*n))
    anchor_costs, anchor_features = tree_data(len(states), anchor_parent, 2*n)
    anchor_index = tree_index(lifted, anchor_costs, anchor_features)
    for dual in [(F(0),)*(2*n), tuple(F((-1)**j*(j % 3)) for j in range(2*n)), (F(1),)*(2*n)]:
        exact = min(c-dot(q, dual) for c, q, _ in complete)
        assert terminal_minimum(states, lifted, dual, vertices-1) == exact
        assert terminal_minimum(projected, projected_lifted, dual, vertices-1) == exact
        repaired, _ = reference_repair(len(states), lifted, dual, anchor_costs,
                                       anchor_features, all_negative(anchor_index, dual))
        full_dist, _ = shortest(len(states), lifted, dual)
        assert repaired == full_dist
        assert min(repaired[i] for i, state in enumerate(states) if state[0] == vertices-1) == exact
        combined_state_repair_queries += 1
    if n <= 5:
        assert verify_suffix_sufficiency(vertices, edges, (n,), prefixes, future) > 0
    family.append({
        'decisions': n, 'accepted_paths': len(complete),
        'full_memory_states': len(full), 'frontier_exact_resource_states': len(states),
        'frontier_projected_resource_states': len(projected),
        'accepted_exact_resource_states': n//2+1, 'accepted_projected_resource_states': 1,
        'frontier_width': 0,
    })
out['parity_family'] = family
out['combined_state_repair_queries'] = combined_state_repair_queries

# A repeated task on a later branch must not be forgotten at the merge.
repeat = [
    Edge(0, 0, 1, F(-2), (1,)), Edge(1, 0, 2, F(0), (0,)),
    Edge(2, 1, 3, F(0), (0,)), Edge(3, 2, 3, F(0), (0,)),
    Edge(4, 3, 4, F(-3), (1,)), Edge(5, 4, 5, F(0), (0,)),
    Edge(6, 3, 5, F(0), (0,)),
]
states, lifted, future = expanded_graph(6, repeat, ())
wrong_states, wrong_lifted, _ = expanded_graph(6, repeat, (), forget_all=True)
prefixes, complete = enumerate_legal(6, repeat, ())
checked_merges = verify_suffix_sufficiency(6, repeat, (), prefixes, future)
assert future[3] == frozenset({0})
assert min(c for c, _, _ in complete) == terminal_minimum(states, lifted, (F(0),), 5) == -3
assert terminal_minimum(wrong_states, wrong_lifted, (F(0),), 5) == -5
out['premature_forgetting'] = {'exact_minimum': '-3', 'illegal_relaxed_minimum': '-5', 'future_at_merge': [0], 'same_state_suffix_checks': checked_merges}

# Repeated task memory and binding two-dimensional resources in one graph.
coupled = [
    Edge(0, 0, 1, F(-2), (1, 0, 0), (1, 2)),
    Edge(1, 0, 2, F(0), (0, 1, 0), (2, 1)),
    Edge(2, 1, 3, F(0), (0, 0, 0), (0, 0)),
    Edge(3, 2, 3, F(0), (0, 0, 0), (0, 0)),
    Edge(4, 3, 4, F(-3), (1, 0, 0), (0, 1)),
    Edge(5, 3, 5, F(-1), (0, 0, 1), (1, 0)),
    Edge(6, 4, 6, F(0), (0, 0, 0), (0, 0)),
    Edge(7, 5, 6, F(0), (0, 0, 0), (0, 0)),
    Edge(8, 3, 6, F(0), (0, 0, 0), (0, 0)),
]
coupled_states, coupled_lifted, coupled_future = expanded_graph(7, coupled, (2, 2))
coupled_prefixes, coupled_complete = enumerate_legal(7, coupled, (2, 2))
assert len(coupled_complete) == 4 and coupled_future[3] == frozenset({0, 2})
coupled_suffix_checks = verify_suffix_sufficiency(7, coupled, (2, 2), coupled_prefixes, coupled_future)
past = {v: set() for v in range(7)}
for v in range(7):
    for e in coupled:
        if e.u == v:
            past[e.v].update(past[v] | {i for i, a in enumerate(e.q) if a})
assert max(len(past[v] & coupled_future[v]) for v in range(7)) == 1
_, coupled_parents = shortest(len(coupled_states), coupled_lifted, (F(0),)*3)
coupled_costs, coupled_features = tree_data(len(coupled_states), coupled_parents, 3)
coupled_index = tree_index(coupled_lifted, coupled_costs, coupled_features)
coupled_queries = 0
for dual in product(map(F, (-2, 0, 2)), repeat=3):
    exact = min(c-dot(q, dual) for c, q, _ in coupled_complete)
    repaired, _ = reference_repair(len(coupled_states), coupled_lifted, dual,
                                   coupled_costs, coupled_features, all_negative(coupled_index, dual))
    full_dist, _ = shortest(len(coupled_states), coupled_lifted, dual)
    assert repaired == full_dist
    assert min(repaired[i] for i, state in enumerate(coupled_states) if state[0] == 6) == exact
    coupled_queries += 1
out['binding_resources_and_repeated_task'] = {
    'vertices': 7, 'capacities': [2, 2], 'frontier_width': 1,
    'feasible_complete_paths': 4, 'expanded_states': len(coupled_states),
    'expanded_edges': len(coupled_lifted), 'dual_queries': coupled_queries,
    'same_state_suffix_checks': coupled_suffix_checks,
}

# A task can influence precedence after its last service occurrence.
assert (frozenset({'a'}) & frozenset({'b'})) == (frozenset() & frozenset({'b'}))
assert ('a' in frozenset({'a'})) != ('a' in frozenset())
out['precedence_requires_extra_mode'] = True

# Keeping only an old representative fails even when the state is sufficient.
switch = [Edge(0, 0, 1, F(0), (0,)), Edge(1, 0, 1, F(1), (1,))]
old_dist, old_parent = shortest(2, switch, (F(0),))
new_dist, new_parent = shortest(2, switch, (F(2),))
assert old_parent[1].eid == 0 and new_parent[1].eid == 1 and new_dist[1] == -1
assert old_dist[1]-dot(old_parent[1].q, (F(2),)) == 0
out['old_representative_only_fails'] = True

# Fixed-epoch index must report ALL current negative slacks, not only new ones.
persist = [Edge(0, 0, 1, F(0), (0,)), Edge(1, 1, 2, F(0), (0,)), Edge(2, 0, 2, F(1), (1,))]
_, parents = shortest(3, persist, (F(0),))
costs, features = tree_data(3, parents, 1)
index = tree_index(persist, costs, features)
first, second = all_negative(index, (F(2),)), all_negative(index, (F(3),))
assert first == second == {2}
repaired, _ = reference_repair(3, persist, (F(3),), costs, features, second)
wrong, _ = reference_repair(3, persist, (F(3),), costs, features, second-first)
assert repaired[2] == -2 and wrong[2] == 0
out['persistent_negative_epoch'] = {'complete_negative_set_minimum': '-2', 'newly_negative_only_wrong_minimum': '0'}

# A topological recomputation that drops outside incoming edges can overestimate.
boundary = [Edge(0, 0, 1, F(0), (0,)), Edge(1, 0, 2, F(0), (0,)), Edge(2, 0, 3, F(0), (0,)), Edge(3, 1, 2, F(-1), (0,)), Edge(4, 2, 3, F(10), (0,))]
chosen = {v: next(e for e in boundary if e.u == 0 and e.v == v) for v in range(1, 4)}
costs, features = tree_data(4, chosen, 1)
negative = all_negative(tree_index(boundary, costs, features), (F(0),))
repaired, affected = reference_repair(4, boundary, (F(0),), costs, features, negative)
assert affected == {2, 3} and repaired[3] == 0 and repaired[2]+10 == 9
out['outside_incoming_boundary'] = {'correct_last_distance': '0', 'internal_predecessor_only_candidate': '9'}

# Property probes on fixed small DAGs, including nonoptimal reference trees.
rng, queries, arbitrary_trees = random.Random(20261011), 0, 0
for case in range(64):
    vertices, dimension = 7, 3
    edges = []
    for u in range(vertices-1):
        for v in range(u+1, vertices):
            if v == u+1 or rng.random() < 0.35:
                edges.append(Edge(len(edges), u, v, F(rng.randint(-3, 5)), tuple(rng.randint(0, 1) for _ in range(dimension))))
    _, parents = shortest(vertices, edges, (F(0),)*dimension)
    if case % 2:
        parents = {v: rng.choice([e for e in edges if e.v == v]) for v in range(1, vertices)}
        arbitrary_trees += 1
    costs, features = tree_data(vertices, parents, dimension)
    index = tree_index(edges, costs, features)
    for dual in product(map(F, (-2, 0, 2)), repeat=dimension):
        negative = all_negative(index, dual)
        direct_negative = {e.eid for e in edges if costs[e.u]-dot(features[e.u], dual)+e.cost-dot(e.q, dual)-costs[e.v]+dot(features[e.v], dual) < 0}
        assert negative == direct_negative
        repaired, affected = reference_repair(vertices, edges, dual, costs, features, negative)
        exact, _ = shortest(vertices, edges, dual)
        assert repaired == exact
        for v in range(vertices):
            if v not in affected:
                assert exact[v] == costs[v]-dot(features[v], dual)
        for e in edges:
            assert repaired[e.v] <= repaired[e.u]+e.cost-dot(e.q, dual)
        queries += 1
out['fixed_tree_repair_property_checks'] = {'dags': 64, 'vertices_each': 7, 'arbitrary_reference_trees': arbitrary_trees, 'dual_queries': queries, 'all_state_distances_match_full_dp': True}

print(json.dumps({'scope': 'finite exact state and repair semantics; no runtime or implementation claim', 'checks': out}, indent=2))
