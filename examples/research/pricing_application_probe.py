"""Research-only reference checks, not a SILO native solver or speed benchmark.

Data: BartvanRossum/rcsp-benchmark, pinned in source_manifest.json.
All pricing/state algorithms below are local Python reference algorithms.
SciPy/HiGHS is used only as an external RMP reference in this isolated test.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import statistics
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import csc_matrix

HERE = Path(__file__).resolve().parent
REVISION = "698703dd98607b3f010bdd859a608be1d3b08133"
MAX_DUTY = 34200
MAX_WORK = 19800
BREAK = 1800
TOL = 1e-7


class StateBudgetExceeded(RuntimeError):
    def __init__(self, states, edges, last_task):
        super().__init__("Explicit state budget exceeded; no sampling or full-graph claim.")
        self.counts = dict(partial_source_reachable_N=states, partial_source_reachable_M=edges,
                           last_processed_task=last_task, full_graph_completed=False,
                           coreachable_counts_unknown=True)


def bits(mask):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1
        mask -= b


def load_instance(name):
    tasks = {}
    for line in (HERE / "instances" / name / "tasks.txt").read_text().splitlines():
        if line.strip():
            k, start, end, a, b, duration = map(int, line.split())
            assert duration == end - start > 0
            tasks[k] = (start, end, a, b, duration)
    assert set(tasks) == set(range(len(tasks)))
    bases = {int(x.split()[0]) for x in (HERE / "instances" / name / "crewBases.txt").read_text().splitlines() if x.strip()}
    actions = []
    outgoing = defaultdict(list)
    source = []
    marked = 0
    for line in (HERE / "instances" / name / "connections.txt").read_text().splitlines():
        if not line.strip():
            continue
        k, kind, u, v, before, after, duration, cost = line.split()
        k, u, v, before, after, duration, cost = map(int, (k, u, v, before, after, duration, cost))
        assert k == len(actions)
        assert duration >= 0
        assert cost == duration + (28800 if kind == "SOURCE" else 0)
        if before >= 0:
            assert after >= 0 and duration - before - after == BREAK
            marked += 1
        else:
            assert before == after == -1
        if kind == "SOURCE":
            assert u in bases and tasks[v][2] == u
            assert duration == tasks[v][4]
            source.append(k)
        elif kind == "SINK":
            assert v in bases and tasks[u][3] == v
            assert duration == 0
            outgoing[u].append(k)
        else:
            assert kind == "CONNECTION"
            assert tasks[u][3] == tasks[v][2]
            assert tasks[v][0] >= tasks[u][1]
            assert duration == tasks[v][1] - tasks[u][1]
            outgoing[u].append(k)
        actions.append((kind, u, v, before, after, duration, cost))
    paths = [list(map(int, x.split())) for x in (HERE / "solutions" / f"solution_{name}.txt").read_text().splitlines() if x.strip()]
    return dict(name=name, tasks=tasks, actions=actions, outgoing=outgoing,
                source=source, bases=bases, official_paths=paths, marked_arcs=marked)


def check_path(data, path):
    actions = data["actions"]
    elapsed = 0
    witnesses = []
    mask = 0
    cost = 0
    last = None
    depot = None
    for p, aid in enumerate(path):
        kind, u, v, before, after, duration, c = actions[aid]
        if p == 0:
            assert kind == "SOURCE"
            depot = u
        else:
            assert kind != "SOURCE" and u == last
        assert (kind == "SINK") == (p == len(path) - 1)
        if before >= 0:
            witnesses.append((elapsed + before, elapsed + before + BREAK))
        elapsed += duration
        cost += c
        if kind != "SINK":
            assert not (mask & (1 << v))
            mask |= 1 << v
            last = v
        else:
            assert depot == v
    assert elapsed <= MAX_DUTY
    valid = [(a, b) for a, b in witnesses if a <= MAX_WORK and elapsed - b <= MAX_WORK]
    assert valid, (data["name"], path, elapsed, witnesses)
    return mask, cost, len(valid)


def build_graph(data):
    """Exact existential one-break witness expansion, independent of duals.

    Key per task: (elapsed duty time, time since chosen break or -1, depot).
    A marked arc may be traversed without selecting its break. Every feasible
    duty has at least one valid selected witness; extra witnesses duplicate paths.
    """
    by_task = defaultdict(dict)
    states = [(-1, 0, -1, -1)]
    edges = []
    sink_edges = []
    order = [0]

    def state(task, elapsed, post, depot):
        key = (elapsed, post, depot)
        if key not in by_task[task]:
            by_task[task][key] = len(states)
            states.append((task, elapsed, post, depot))
        return by_task[task][key]

    for aid in data["source"]:
        _, depot, v, _, _, dur, _ = data["actions"][aid]
        if dur <= min(MAX_WORK, MAX_DUTY):
            edges.append((0, state(v, dur, -1, depot), aid))

    for task in sorted(data["tasks"], key=lambda x: (data["tasks"][x][1], x)):
        # Positive task durations and nonnegative gaps imply strict end-time order.
        for (elapsed, post, depot), uid in list(by_task[task].items()):
            order.append(uid)
            for aid in data["outgoing"][task]:
                kind, _, v, before, after, dur, _ = data["actions"][aid]
                if kind == "SINK":
                    if v == depot and post >= 0:
                        sink_edges.append((uid, aid))
                    continue
                if elapsed + dur > MAX_DUTY:
                    continue
                if post < 0:
                    if elapsed + dur <= MAX_WORK:
                        edges.append((uid, state(v, elapsed + dur, -1, depot), aid))
                    if before >= 0 and elapsed + before <= MAX_WORK and after <= MAX_WORK:
                        edges.append((uid, state(v, elapsed + dur, after, depot), aid))
                elif post + dur <= MAX_WORK:
                    edges.append((uid, state(v, elapsed + dur, post + dur, depot), aid))
        if len(edges) > 3000000 or len(states) > 500000:
            raise StateBudgetExceeded(len(states), len(edges), task)
    sink = len(states)
    states.append((-2, 0, 0, -1))
    order.append(sink)
    edges.extend((u, sink, a) for u, a in sink_edges)
    assert len(order) == len(states)
    incoming = [[] for _ in states]
    for u, v, a in edges:
        incoming[v].append(u)
    # All states are source-reachable. Remove states that cannot finish a duty.
    good = {sink}
    queue = deque([sink])
    while queue:
        v = queue.popleft()
        for u in incoming[v]:
            if u not in good:
                good.add(u)
                queue.append(u)
    assert 0 in good
    remap = {v: i for i, v in enumerate(v for v in order if v in good)}
    old_counts = (len(states), len(edges))
    states = [states[v] for v in order if v in good]
    edges = [(remap[u], remap[v], a) for u, v, a in edges if u in good and v in good]
    edges.sort(key=lambda x: (x[1], x[0], x[2]))
    incoming = [[] for _ in states]
    outgoing = [[] for _ in states]
    for eid, (u, v, a) in enumerate(edges):
        assert u < v
        incoming[v].append(eid)
        outgoing[u].append(eid)
    return dict(states=states, edges=edges, incoming=incoming, outgoing=outgoing,
                raw_N=old_counts[0], raw_M=old_counts[1], N=len(states), M=len(edges),
                used_actions=sorted({a for _, _, a in edges}), sink=len(states) - 1)


def weights(data, pi):
    return [c - (pi[v] if kind != "SINK" else 0) for kind, u, v, b, a, d, c in data["actions"]]


def cold(data, graph, pi):
    w = weights(data, pi)  # action sharing; not one recomputation per expanded arc
    distance = [math.inf] * graph["N"]
    parent = [-1] * graph["N"]
    cprefix = [0] * graph["N"]
    qprefix = [0] * graph["N"]
    distance[0] = 0
    for v in range(1, graph["N"]):
        for eid in graph["incoming"][v]:
            u, _, aid = graph["edges"][eid]
            candidate = distance[u] + w[aid]
            if candidate < distance[v]:
                distance[v] = candidate
                parent[v] = eid
        assert parent[v] >= 0
        u, _, aid = graph["edges"][parent[v]]
        kind, _, task, _, _, _, c = data["actions"][aid]
        cprefix[v] = cprefix[u] + c
        qprefix[v] = qprefix[u] | (0 if kind == "SINK" else 1 << task)
    return dict(D=distance, parent=parent, C=cprefix, Q=qprefix, w=w)


def tree_index(data, graph, tree):
    groups = defaultdict(list)
    for eid, (u, v, aid) in enumerate(graph["edges"]):
        kind, _, task, _, _, _, c = data["actions"][aid]
        mask = tree["Q"][u] | (0 if kind == "SINK" else 1 << task)
        positive = mask & ~tree["Q"][v]
        negative = tree["Q"][v] & ~mask
        b = tree["C"][u] + c - tree["C"][v]
        groups[positive, negative].append((b, eid))
    for rows in groups.values():
        rows.sort()
    return dict(groups=groups, K=len(groups),
                signature_nnz=sum(p.bit_count() + n.bit_count() for p, n in groups),
                signature_max=max((p.bit_count() + n.bit_count() for p, n in groups), default=0),
                binary_search_levels=sum(math.ceil(math.log2(len(x) + 1)) for x in groups.values()))


def repair(data, graph, tree, index, pi, target):
    """Reference full index query plus closure repair. Not a fast implementation.

    Includes ALL currently negative margins, even ones negative in an earlier query.
    Returns separate abstract operation counts, never claims measured speed savings.
    """
    bad = []
    binary_comparisons = 0
    for (positive, negative), rows in index["groups"].items():
        projection = sum(pi[j] for j in bits(positive)) - sum(pi[j] for j in bits(negative))
        # b - projection < -TOL. Count actual binary-search comparisons.
        lo, hi = 0, len(rows)
        while lo < hi:
            mid = (lo + hi) // 2
            binary_comparisons += 1
            if rows[mid][0] < projection - TOL:
                lo = mid + 1
            else:
                hi = mid
        bad.extend(eid for _, eid in rows[:lo])
    direct = []
    dtree = [tree["C"][v] - sum(pi[j] for j in bits(tree["Q"][v])) for v in range(graph["N"])]
    for eid, (u, v, a) in enumerate(graph["edges"]):
        if dtree[u] + target["w"][a] - dtree[v] < -TOL:
            direct.append(eid)
    assert set(direct) == set(bad), (len(direct), len(bad))
    affected = {graph["edges"][e][1] for e in bad}
    queue = deque(affected)
    closure_edges = 0
    while queue:
        u = queue.popleft()
        for eid in graph["outgoing"][u]:
            closure_edges += 1
            v = graph["edges"][eid][1]
            if v not in affected:
                affected.add(v)
                queue.append(v)
    repaired = dtree[:]
    internal = boundary = 0
    boundary_sources = set()
    for v in sorted(affected):
        repaired[v] = math.inf
        for eid in graph["incoming"][v]:
            u, _, a = graph["edges"][eid]
            if u in affected:
                internal += 1
            else:
                boundary += 1
                boundary_sources.add(u)
            repaired[v] = min(repaired[v], repaired[u] + target["w"][a])
    error = max(abs(a - b) for a, b in zip(repaired, target["D"]))
    assert error <= TOL, error
    boundary_nnz = sum(tree["Q"][v].bit_count() for v in boundary_sources)
    # Count critical primitive families separately; their relative costs differ.
    row = dict(B=len(bad), A=len(affected), A_fraction=len(affected) / graph["N"],
               internal_edges=internal, boundary_edges=boundary,
               repaired_incoming_fraction=(internal + boundary) / graph["M"],
               boundary_states=len(boundary_sources), boundary_projection_nnz=boundary_nnz,
               closure_edge_visits=closure_edges, max_all_state_error=error,
               K=index["K"], signature_nnz=index["signature_nnz"],
               signature_max=index["signature_max"], binary_search_levels=index["binary_search_levels"],
               binary_search_comparisons=binary_comparisons,
               report_primitive_proxy=index["signature_nnz"] + binary_comparisons + len(bad),
               cold_primitive_proxy=len(graph["used_actions"]) + graph["N"] + graph["M"])
    row["maintenance_count_proxy"] = (row["report_primitive_proxy"] + row["closure_edge_visits"]
                                        + len(affected) + internal + boundary + boundary_nnz)
    # Excludes sorting, tree/index rebuild and output; not a prediction of walltime.
    return row


def extract_path(graph, tree):
    v = graph["sink"]
    path = []
    while v:
        eid = tree["parent"][v]
        u, _, aid = graph["edges"][eid]
        path.append(aid)
        v = u
    return path[::-1]


def structural_checks(data, graph):
    official = [check_path(data, p) for p in data["official_paths"]]
    mask = 0
    for q, c, w in official:
        mask |= q
    assert mask == (1 << len(data["tasks"])) - 1
    zero = [0] * len(data["tasks"])
    tree = cold(data, graph, zero)
    index = tree_index(data, graph, tree)
    # Exact DAG path counts test whole-graph mandatory synchronization states.
    # This says nothing about task-local postdominators. Big integers are exact.
    forward = [0] * graph["N"]
    backward = [0] * graph["N"]
    forward[0] = backward[-1] = 1
    for v in range(1, graph["N"]):
        forward[v] = sum(forward[graph["edges"][e][0]] for e in graph["incoming"][v])
    for u in range(graph["N"] - 2, -1, -1):
        backward[u] = sum(backward[graph["edges"][e][1]] for e in graph["outgoing"][u])
    assert forward[-1] == backward[0]
    strict_sync = sum(forward[v] * backward[v] == forward[-1] for v in range(1, graph["N"] - 1))
    return dict(instance=data["name"], tasks=len(data["tasks"]), original_actions=len(data["actions"]),
                marked_break_actions=data["marked_arcs"], w=0, raw_N=graph["raw_N"], raw_M=graph["raw_M"],
                N=graph["N"], M=graph["M"], action_evaluations=len(graph["used_actions"]),
                expansion_per_action=graph["M"] / len(graph["used_actions"]),
                K_at_zero=index["K"], K_over_M_at_zero=index["K"] / graph["M"],
                signature_nnz_at_zero=index["signature_nnz"],
                official_duties=len(official), official_solution_cost=sum(x[1] for x in official),
                official_solution_coverage=True, all_official_duties_feasible=True,
                nontrivial_whole_graph_synchronizers=strict_sync,
                minimum_cost_duty_at_zero=tree["D"][-1])


def run_cg(data, graph, max_iterations=200):
    """Unstabilized, single globally best column, complete original instance.

    The LP is min c*x, coverage>=1, x>=0. linprog <= duals are negated.
    No branching, cuts, column pool deletion or author trajectory reproduction.
    Cold DP alone chooses columns. Equal binary64 candidates retain the first
    incoming edge sorted by (predecessor state ID, action ID, edge ID). The repair
    is a non-intervening audit of distances, not a second column-generating run.
    """
    columns = {}
    for path in data["official_paths"]:
        q, c, _ = check_path(data, path)
        columns[q] = min(columns.get(q, math.inf), c)
    m = len(data["tasks"])
    previous = cold(data, graph, [0] * m)
    index = tree_index(data, graph, previous)
    rows = []
    pi_trace = []
    epoch_lengths = []
    epoch_length = 0
    t0 = time.perf_counter()
    for iteration in range(max_iterations):
        keys = list(columns)
        rr, cc, vv = [], [], []
        for j, q in enumerate(keys):
            for k in bits(q):
                rr.append(k)
                cc.append(j)
                vv.append(-1.0)
        matrix = csc_matrix((vv, (rr, cc)), shape=(m, len(keys)))
        result = linprog([columns[q] for q in keys], A_ub=matrix, b_ub=-np.ones(m),
                         bounds=(0, None), method="highs-ds", options={"presolve": True})
        assert result.success, result.message
        pi = (-result.ineqlin.marginals).tolist()
        assert min(pi) >= -1e-7
        assert abs(sum(pi) - result.fun) <= 1e-5
        current = cold(data, graph, pi)
        row = repair(data, graph, previous, index, pi, current)
        row.update(iteration=iteration, RMP_columns=len(keys), RMP_objective=float(result.fun),
                   minimum_reduced_cost=current["D"][-1], reference_epoch_reset=bool(row["B"]))
        pi_trace.append(pi)
        rows.append(row)
        epoch_length += 1
        # Explicit strict reset policy, not a correctness requirement for repair.
        if row["B"]:
            epoch_lengths.append(epoch_length)
            epoch_length = 0
            previous = current
            index = tree_index(data, graph, previous)
        if current["D"][-1] >= -TOL:
            status = "root_LP_pricing_terminated"
            break
        path = extract_path(graph, current)
        q, c, _ = check_path(data, path)
        assert abs(c - sum(pi[j] for j in bits(q)) - current["D"][-1]) <= 1e-6
        assert q not in columns or c < columns[q] - TOL
        columns[q] = c
    else:
        status = "iteration_cap"
    if epoch_length:
        epoch_lengths.append(epoch_length)
    return dict(status=status, iterations=len(rows), iteration_cap=max_iterations,
                tie_break="cold DP first incoming edge in deterministic (u, action_id, edge_id) order; strict binary64 <",
                repair_role="non-intervening all-state distance audit; never adds or selects RMP columns",
                final_RMP_objective=rows[-1]["RMP_objective"],
                final_minimum_reduced_cost=rows[-1]["minimum_reduced_cost"], final_columns=len(columns),
                strict_reset_epoch_lengths=epoch_lengths, rows=rows, dual_trajectory=pi_trace,
                reference_total_seconds=time.perf_counter() - t0)


def summarize(rows):
    result = {}
    for key in ("A_fraction", "repaired_incoming_fraction", "K", "signature_nnz", "B", "boundary_states",
                "boundary_projection_nnz", "report_primitive_proxy", "cold_primitive_proxy", "maintenance_count_proxy"):
        xs = [r[key] for r in rows]
        result[key] = dict(min=min(xs), median=statistics.median(xs), max=max(xs), mean=statistics.mean(xs))
    ratios = [r["maintenance_count_proxy"] / r["cold_primitive_proxy"] for r in rows]
    result["maintenance_count_proxy_over_cold"] = dict(min=min(ratios), median=statistics.median(ratios), max=max(ratios))
    result["maximum_all_state_distance_error"] = max(r["max_all_state_error"] for r in rows)
    return result


def stress(data, graph):
    m = len(data["tasks"])
    # These are artificial exact-integer duals, not RMP observations.
    vectors = [[0] * m, [12000] * m, [6000 if j % 2 else 18000 for j in range(m)]]
    one = [0] * m
    one[min(data["tasks"], key=lambda j: (data["tasks"][j][0], j))] = 100000
    vectors.extend([one, [0] * m])
    tree = cold(data, graph, vectors[0])
    index = tree_index(data, graph, tree)
    rows = []
    for k, pi in enumerate(vectors[1:]):
        target = cold(data, graph, pi)
        row = repair(data, graph, tree, index, pi, target)
        row.update(query=k, minimum_reduced_cost=target["D"][-1])
        rows.append(row)
    return dict(reference="fixed_zero_dual_tree", duals=vectors[1:], rows=rows, summary=summarize(rows))


def independent_slice_oracle(data, selected_override=None):
    """Small induced time-prefix graph. DFS uses absolute break-start witnesses.

    No expanded-state transitions or break feasibility helpers are used. This
    independently tests the implementation on the slice, not the full optimum.
    """
    selected = (set(selected_override) if selected_override is not None else
                set(sorted(data["tasks"], key=lambda j: (data["tasks"][j][0], j))[:18]))
    original_ids = [i for i, a in enumerate(data["actions"])
                    if (a[0] == "SOURCE" and a[2] in selected)
                    or (a[0] == "SINK" and a[1] in selected)
                    or (a[0] == "CONNECTION" and a[1] in selected and a[2] in selected)]
    induced = dict(data)
    induced["actions"] = [data["actions"][i] for i in original_ids]
    induced["source"] = [i for i, a in enumerate(induced["actions"]) if a[0] == "SOURCE"]
    induced["outgoing"] = defaultdict(list)
    for i, a in enumerate(induced["actions"]):
        if a[0] != "SOURCE":
            induced["outgoing"][a[1]].append(i)
    induced["tasks"] = {j: data["tasks"][j] for j in selected}
    valid = []
    explored = 0

    def dfs(task, depot, elapsed, witness_starts, mask, cost, path):
        nonlocal explored
        explored += 1
        if explored > 500000:
            raise RuntimeError("Independent slice enumeration budget exceeded")
        for aid in induced["outgoing"][task]:
            kind, _, v, before, after, duration, c = induced["actions"][aid]
            total = elapsed + duration
            if total > MAX_DUTY:
                continue
            choices = witness_starts + ((elapsed + before,) if before >= 0 else ())
            if kind == "SINK":
                if v == depot and any(q <= MAX_WORK and total - q - BREAK <= MAX_WORK for q in choices):
                    valid.append((mask, cost + c, path + (aid,)))
            else:
                assert not (mask & (1 << v))
                dfs(v, depot, total, choices, mask | (1 << v), cost + c, path + (aid,))

    for aid in induced["source"]:
        kind, depot, v, before, after, duration, c = induced["actions"][aid]
        dfs(v, depot, duration, (), 1 << v, c, (aid,))
    if not valid:
        assert selected_override is None, "Official-duty-induced slice should be feasible"
        # Some earliest time prefixes cannot return to the depot. Explicitly
        # record a deterministic feasible slice selected from an official duty.
        # This is an oracle slice, never a sample used for performance inference.
        duty = max(data["official_paths"], key=lambda p: (len(p), tuple(-i for i in p)))
        selected = [data["actions"][aid][2] for aid in duty if data["actions"][aid][0] != "SINK"]
        answer = independent_slice_oracle(data, selected)
        answer["empty_first18_slice"] = True
        answer["selection_rule"] = "tasks of longest official duty; connection-ID tie-break"
        return answer
    graph = build_graph(induced)
    vectors = [[0] * len(data["tasks"]), [12000] * len(data["tasks"]),
               [6000 if j % 2 else 18000 for j in data["tasks"]]]
    tree = cold(induced, graph, vectors[0])
    index = tree_index(induced, graph, tree)
    comparisons = []
    for pi in vectors:
        optimum = min(c - sum(pi[j] for j in bits(q)) for q, c, p in valid)
        current = cold(induced, graph, pi)
        row = repair(induced, graph, tree, index, pi, current)
        assert current["D"][-1] == optimum
        # Validate the actual selected original path independently in enumeration.
        chosen = tuple(extract_path(graph, current))
        assert any(p == chosen and c - sum(pi[j] for j in bits(q)) == optimum for q, c, p in valid)
        comparisons.append(dict(oracle_min=optimum, DP_min=current["D"][-1],
                                all_state_repair_error=row["max_all_state_error"],
                                selected_DP_path_in_oracle_optima=True))
    return dict(role="induced oracle slice only; not full-instance enumeration",
                selection_rule="first 18 tasks by (startTime, task ID)" if selected_override is None else "provided duty-task set",
                selected_original_task_ids=sorted(selected), original_action_ids=original_ids,
                explored_prefixes=explored, valid_original_paths=len(valid),
                N=graph["N"], M=graph["M"], comparisons=comparisons)


def width_zero_failure_family(n):
    """Binding-capacity w=0 family; a counterexample to a width-only inference.

    This is not an algorithm lower bound. Task 0 and task 1 are alternative
    first-layer service actions. The reference tree chooses first r tasks.
    """
    cap = n // 2
    states = [(i, r) for i in range(n + 1) for r in range(min(i, cap) + 1)]
    ids = {s: i for i, s in enumerate(states)}
    # Features on the explicitly chosen canonical shortest tree at zero duals.
    q = [(1 << (r + 1)) - 2 for i, r in states]
    edges = []
    for i in range(1, n + 1):
        for r in range(min(i - 1, cap) + 1):
            edges.append((ids[i - 1, r], ids[i, r], 0))
            if r < cap:
                edges.append((ids[i - 1, r], ids[i, r + 1], 1 << i))
        if i == 1:
            edges.append((ids[0, 0], ids[1, 1], 1))
    groups = set()
    bad = []
    outgoing = defaultdict(list)
    for u, v, feature in edges:
        mask = q[u] | feature
        groups.add((mask & ~q[v], q[v] & ~mask))
        if feature == 1:  # pi_0 rises from 0 to 1; all other pi stay zero
            bad.append(v)
        outgoing[u].append(v)
    affected = set(bad)
    queue = deque(bad)
    while queue:
        for v in outgoing[queue.popleft()]:
            if v not in affected:
                affected.add(v)
                queue.append(v)
    assert len(affected) == sum(min(i, cap) for i in range(1, n + 1))
    # All r>=1 states have a feasible prefix using task 0, so their true distance
    # decreases from 0 to -1; capacity cap<n makes the resource nonredundant.
    assert all(states[v][1] >= 1 for v in affected)
    return dict(n=n, capacity=cap, w=0, N=len(states), M=len(edges), K=len(groups),
                A=len(affected), A_fraction=len(affected) / len(states),
                note="binding resource; representation-specific counterexample, not an algorithm lower bound")


def main():
    manifest = json.loads((HERE / "source_manifest.json").read_text(encoding="utf-8-sig"))
    for item in manifest:
        actual = hashlib.sha256((HERE / item["path"]).read_bytes()).hexdigest().upper()
        assert actual == item["sha256"]
    output = dict(data_revision=REVISION, source_manifest="source_manifest.json", date="2026-10-11",
                  probe_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  environment=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__, platform=platform.platform()),
                  parameters=dict(max_duty_seconds=MAX_DUTY, max_work_seconds=MAX_WORK, break_seconds=BREAK,
                                  negative_margin_tolerance=TOL, all_state_error_acceptance=TOL,
                                  explicit_source_reachable_state_budget=500000,
                                  explicit_edge_budget=3000000, CG_iteration_cap=200),
                  scope="Full original instance attempts with explicit budget statuses; separate induced oracle slices. No speed claim.",
                  width_zero_failure_family=[width_zero_failure_family(n) for n in (4, 8, 16, 32, 64)], instances=[])
    for name in ("s2_t90", "s3_t168", "s6_t450"):
        started = time.perf_counter()
        data = load_instance(name)
        oracle = independent_slice_oracle(data)
        try:
            graph = build_graph(data)
        except StateBudgetExceeded as exc:
            record = dict(instance=name, tasks=len(data["tasks"]), original_actions=len(data["actions"]),
                          status="explicit_state_budget_exceeded", independent_slice_oracle=oracle,
                          **exc.counts)
            output["instances"].append(record)
            print(json.dumps(record), flush=True)
            (HERE / "pricing_application_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
            continue
        record = structural_checks(data, graph)
        record["independent_slice_oracle"] = oracle
        record["artificial_dual_stress"] = stress(data, graph)
        print(json.dumps({k: v for k, v in record.items() if k not in ("artificial_dual_stress", "independent_slice_oracle")}), flush=True)
        if name == "s2_t90":
            record["closed_loop_root_CG"] = run_cg(data, graph)
            record["closed_loop_summary"] = summarize(record["closed_loop_root_CG"]["rows"])
            print(json.dumps(dict(instance=name, CG_status=record["closed_loop_root_CG"]["status"],
                                  iterations=record["closed_loop_root_CG"]["iterations"],
                                  objective=record["closed_loop_root_CG"]["final_RMP_objective"],
                                  summary=record["closed_loop_summary"])), flush=True)
        record["reference_total_seconds"] = time.perf_counter() - started
        output["instances"].append(record)
        (HERE / "pricing_application_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("COMPLETED bounded checks; inspect explicit budget and iteration-cap statuses. No speed claim.", flush=True)


if __name__ == "__main__":
    main()
