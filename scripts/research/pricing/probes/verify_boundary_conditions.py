"""Finite exact-arithmetic checks of pricing boundary claims; no speed benchmark.

This script uses synthetic DAGs as proof probes, not application evidence.
No solver, pricing implementation or project-native algorithm is modified.
"""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import json
import random

HERE = Path(__file__).resolve().parent


def kernel(n, edges, entries):
    incoming = [[] for _ in range(n)]
    for u, v, c in edges:
        assert u < v
        incoming[v].append((u, F(c)))
    result = []
    for b in entries:
        d = [None] * n
        d[b] = F(0)
        for v in range(n):
            candidates = ([d[v]] if d[v] is not None else [])
            candidates += [d[u] + c for u, c in incoming[v] if d[u] is not None]
            d[v] = min(candidates) if candidates else None
        result.append(d)
    return result


def envelope(kern, eta):
    values, owners = [], []
    for v in range(len(kern[0])):
        candidates = [(eta[b] + kern[b][v], b) for b in range(len(eta)) if kern[b][v] is not None]
        value, owner = min(candidates)
        values.append(value)
        owners.append(owner)
    return values, owners


def compress(kern, eta0, values0, owners):
    k = len(eta0)
    margins = [[None] * k for _ in range(k)]
    for v, a in enumerate(owners):
        for b in range(k):
            if kern[b][v] is None:
                continue
            gap = eta0[b] + kern[b][v] - values0[v]
            assert gap >= 0
            margins[a][b] = gap if margins[a][b] is None else min(gap, margins[a][b])
    return margins


def edge_slack_table(n, edges, entries, eta0, old, owners):
    k = len(entries)
    table = [[None] * k for _ in range(k)]

    def add(a, b, gap):
        assert gap >= 0
        table[a][b] = gap if table[a][b] is None else min(table[a][b], gap)

    for u, v, c in edges:
        add(owners[v], owners[u], old[u] + c - old[v])
    # Virtual-root injections are essential when another entry reaches b cheaply.
    for b, vertex in enumerate(entries):
        add(owners[vertex], b, eta0[b] - old[vertex])
    return table


def passes(table, delta):
    return all(g is None or delta[b] - delta[a] >= -g
               for a, row in enumerate(table) for b, g in enumerate(row))


def oracle_dp(n, edges, entries, eta):
    # Independent direct multi-source DAG recurrence, no kernel or margin table.
    d = [None] * n
    for b, value in zip(entries, eta):
        d[b] = F(value)
    outgoing = [[] for _ in range(n)]
    for u, v, c in edges:
        outgoing[u].append((v, F(c)))
    for u in range(n):
        if d[u] is not None:
            for v, c in outgoing[u]:
                candidate = d[u] + c
                if d[v] is None or candidate < d[v]:
                    d[v] = candidate
    return d


def finite_family():
    rng = random.Random(20261017)
    summaries = []
    for index in range(16):
        n, entries = 9, (0, 1, 2)
        edges = [(b, 3, F(rng.randint(-2, 4))) for b in entries]
        edges += [(u, u + 1, F(rng.randint(-2, 4))) for u in range(3, n - 1)]
        edges += [(u, v, F(rng.randint(-2, 4))) for u in range(n) for v in range(max(3, u + 2), n)
                  if rng.random() < 0.25]
        eta0 = [F(rng.randint(-1, 2)) for _ in entries]
        kern = kernel(n, edges, entries)
        old, owners = envelope(kern, eta0)
        assert old == oracle_dp(n, edges, entries, eta0)
        margins = compress(kern, eta0, old, owners)
        edge_table = edge_slack_table(n, edges, entries, eta0, old, owners)
        accepted = rejected = 0
        for delta in product(range(-2, 3), repeat=3):
            eta = [eta0[b] + delta[b] for b in range(3)]
            current, _ = envelope(kern, eta)
            assert current == oracle_dp(n, edges, entries, eta)
            condition = passes(margins, delta)
            assert passes(edge_table, delta) == condition
            retained = all(eta[a] + kern[a][v] == current[v] for v, a in enumerate(owners))
            assert condition == retained
            if condition:
                accepted += 1
                assert all(current[v] == old[v] + delta[a] for v, a in enumerate(owners))
            else:
                rejected += 1
            # Nonuniform suffix potential, including negative edges; exact reweighting.
            psi = [F((v % 4) - 2, 3) for v in range(n)]
            new_edges = [(u, v, c + psi[v] - psi[u]) for u, v, c in edges]
            eta_with_potential = [eta[b] + psi[entries[b]] for b in range(3)]
            direct = oracle_dp(n, new_edges, entries, eta_with_potential)
            assert direct == [current[v] + psi[v] for v in range(n)]
        summaries.append(dict(index=index, states=n, edges=len(edges), boundary_size=3,
                              queries=125, accepted_owner_region=accepted, rejected_owner_region=rejected))
    return summaries


def injection_case():
    # Entry 1 has an expensive direct injection; its old optimum enters at 0.
    entries = (0, 1)
    edges = [(0, 1, F(1)), (1, 2, F(0)), (0, 3, F(4)), (2, 3, F(0))]
    eta0 = [F(0), F(3)]
    kern = kernel(4, edges, entries)
    old, owners = envelope(kern, eta0)
    g = compress(kern, eta0, old, owners)
    f = edge_slack_table(4, edges, entries, eta0, old, owners)
    for delta in product(range(-3, 2), repeat=2):
        eta = [eta0[b] + delta[b] for b in range(2)]
        exact = oracle_dp(4, edges, entries, eta)
        retained = all(eta[a] + kern[a][v] == exact[v] for v, a in enumerate(owners))
        assert passes(f, delta) == passes(g, delta) == retained
    # Ignoring the root injection would accept this invalid old-owner assignment.
    assert owners == [0, 0, 0, 0]
    assert not passes(f, [0, -3])
    wrong_internal_only = [[None, None], [None, None]]
    for u, v, c in edges:
        gap = old[u] + c - old[v]
        a, b = owners[v], owners[u]
        wrong_internal_only[a][b] = gap if wrong_internal_only[a][b] is None else min(wrong_internal_only[a][b], gap)
    assert passes(wrong_internal_only, [0, -3])
    return dict(queries=25, all_G_F_and_direct_DP_agree=True,
                missed_injection_wrongly_accepts=[0, -3], old_owners=owners)


def counterexamples():
    # Missing bypass: a scalar shift at z cannot be applied to its competitor.
    old_z, new_z = F(-1), F(0)
    old_v, new_v = min(old_z, F(-1, 2)), min(new_z, F(-1, 2))
    wrong = old_v + new_z - old_z
    assert new_v == F(-1, 2) and wrong == 0

    # Two distinct complete resource/memory states at one physical location.
    true_value = F(1)  # only the cost-1 state can subsequently serve task a
    collapsed = min(F(1), F(0))  # illegal reuse of the other state's continuation
    assert true_value != collapsed

    # Boundary minimum loses which entry can reach a target cheaply.
    kern = [[F(0), F(2)], [F(2), F(0)]]
    old, _ = envelope(kern, [F(0), F(0)])
    new, _ = envelope(kern, [F(0), F(1)])
    assert old == [0, 0] and new == [0, 1]

    # Nonuniform upstream path perturbations, followed by an exact local minimum.
    eta0 = min(F(0), F(1))
    eta1 = min(F(0), F(1) - 2)
    assert eta1 == -1 and eta1 + 5 == eta0 + 5 - 1

    # All shortest kernels can stay fixed while a nonoptimal path changes cost.
    edges0 = [(0, 1, F(0)), (0, 2, F(0)), (1, 2, F(1))]
    edges1 = [(0, 1, F(0)), (0, 2, F(0)), (1, 2, F(2))]
    assert kernel(3, edges0, (0,)) == kernel(3, edges1, (0,))
    assert sum(c for u, v, c in edges0 if (u, v) != (0, 2)) == 1
    assert sum(c for u, v, c in edges1 if (u, v) != (0, 2)) == 2

    # Equal kernel values alone do not preserve an old optimal path witness.
    switched = [(0, 1, F(0)), (0, 2, F(1)), (1, 2, F(0))]
    assert kernel(3, edges0, (0,)) == kernel(3, switched, (0,))
    old_witness_new_cost = next(c for u, v, c in switched if (u, v) == (0, 2))
    assert old_witness_new_cost == 1 and kernel(3, switched, (0,))[0][2] == 0

    # A minimum-only entry summary returns one best column, not all negative ones.
    negative_values = [F(0) - 2, F(1) - 2]
    assert all(x < 0 for x in negative_values) and len(negative_values) == 2
    return dict(missing_bypass=dict(true_new=str(new_v), wrong_scalar=str(wrong)),
                physical_state_alias=dict(true=str(true_value), illegal_collapsed=str(collapsed)),
                boundary_minimum=dict(old=list(map(str, old)), new=list(map(str, new))),
                local_reoptimization_without_uniform_prefix_changes=dict(prefix_changes=[0, -2], entry_change=-1),
                unchanged_minima_with_changed_nonoptimal_path=True,
                same_kernel_different_optimal_witness=dict(old_path_new_cost=1, true_new_minimum=0),
                single_minimum_does_not_enumerate_all_negative_columns=True)


def main():
    families = finite_family()
    output = dict(date="2026-10-17", seed=20261017,
                  scope="synthetic exact-arithmetic proof probes; not application or performance evidence",
                  probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  random_DAGs=families, total_boundary_queries=sum(r["queries"] for r in families),
                  potential_reweighting_queries=sum(r["queries"] for r in families),
                  G_and_edge_slack_table_agree=True, injection_boundary_case=injection_case(),
                  counterexamples=counterexamples(), all_checks_passed=True)
    (HERE / "boundary_conditions_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k != "random_DAGs"}, indent=2))


if __name__ == "__main__":
    main()
