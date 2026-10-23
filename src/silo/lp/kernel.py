"""Dense two-phase primal/dual revised simplex, with cached QR solves.

The kernel knows only MAX c'z, row senses and z>=0. General model semantics,
postsolve and all mathematical claims are checked by the caller in original space.
"""

from dataclasses import dataclass, field
from time import perf_counter

import numpy as np


class QRFactor:
    """One basis factorization reused for primal, dual and pivot directions."""

    def __init__(self, matrix, counters):
        self.matrix, self.counters = matrix, counters
        self.q, self.r = np.linalg.qr(matrix)
        counters["factorizations"] += 1
        if len(matrix) and np.min(np.abs(np.diag(self.r))) < 1e-13:
            raise np.linalg.LinAlgError("Singular/near-singular basis QR.")
        self.calls = 0

    def solve(self, rhs, transpose=False):
        self.counters["triangular_solves"] += 1
        if self.calls:
            self.counters["factor_reuses"] += 1
        self.calls += 1
        n = len(self.r)
        value = np.zeros(n)
        if transpose:
            for i in range(n):
                value[i] = (rhs[i] - self.r[:i, i] @ value[:i]) / self.r[i, i]
            value = self.q @ value
        else:
            work = self.q.T @ rhs
            for i in range(n - 1, -1, -1):
                value[i] = (work[i] - self.r[i, i + 1 :] @ value[i + 1 :]) / self.r[i, i]
        matrix = self.matrix.T if transpose else self.matrix
        residual = matrix @ value - rhs
        if not np.isfinite(value).all() or np.max(np.abs(residual), initial=0) > 1e-7 * (
            1 + np.max(np.abs(rhs), initial=0) + np.max(np.abs(matrix) @ np.abs(value), initial=0)
        ):
            raise np.linalg.LinAlgError("Basis solve residual failed.")
        return value


@dataclass(frozen=True)
class BasisSnapshot:
    """Immutable identities and coefficients; never an unchecked column-index hint."""

    version: int
    row_keys: tuple
    column_keys: tuple
    matrix: tuple[tuple[float, ...], ...]
    basic_keys: tuple


@dataclass
class KernelResult:
    status: str
    reason: str
    point: np.ndarray | None = None
    ray: np.ndarray | None = None
    dual: np.ndarray | None = None
    reduced: np.ndarray | None = None
    iterations: int = 0
    diagnostics: dict = field(default_factory=dict)
    snapshot: BasisSnapshot | None = None
    matrix: np.ndarray | None = None
    rhs: np.ndarray | None = None
    basis: tuple[int, ...] = ()
    column_keys: tuple = ()
    row_keys: tuple = ()


def _standard(norm):
    k, m = len(norm.costs), len(norm.rhs)
    rows, rhs, basis, arts, keys = [], [], [], [], []
    keys.extend(("variable", norm.data.names[i], direction) for i, direction in norm.column_origins)
    flips = np.where(norm.rhs < 0, -1.0, 1.0)
    for i in range(m):
        sense = norm.senses[i]
        if flips[i] < 0:
            sense = {"<=": ">=", ">=": "<=", "=": "="}[sense]
        row = list(flips[i] * norm.matrix[i]) + [0.0] * (len(keys) - k)
        if sense != "=":
            sign = 1 if sense == "<=" else -1
            for previous in rows:
                previous.append(0.0)
            keys.append(("slack", norm.row_keys[i]))
            row.append(float(sign))
        if sense != "<=":
            for previous in rows:
                previous.append(0.0)
            keys.append(("artificial", norm.row_keys[i]))
            row.append(1.0)
            arts.append(len(keys) - 1)
        basis.append(len(keys) - 1)
        rows.append(row)
        rhs.append(abs(norm.rhs[i]))
    a = np.array(rows).reshape(m, len(keys))
    c = np.zeros(len(keys))
    c[:k] = norm.costs
    return a, np.array(rhs), c, basis, set(arts), tuple(keys), flips


def _snapshot(a, rows, keys, basis):
    return BasisSnapshot(
        2, tuple(rows), tuple(keys), tuple(map(tuple, a)), tuple(keys[i] for i in basis)
    )


def _map_basis(snapshot, a, rows, keys):
    if not isinstance(snapshot, BasisSnapshot):
        raise ValueError("Expected an immutable BasisSnapshot.")
    if snapshot.version != 2 or len(snapshot.basic_keys) != len(snapshot.row_keys):
        raise ValueError("Snapshot version/shape mismatch.")
    row_positions = {key: i for i, key in enumerate(rows)}
    if len(row_positions) != len(rows) or any(k not in row_positions for k in snapshot.row_keys):
        raise ValueError("Row identity is not an append-only extension.")
    row_indices = [row_positions[k] for k in snapshot.row_keys]
    positions = {key: i for i, key in enumerate(keys)}
    if len(positions) != len(keys) or any(k not in positions for k in snapshot.column_keys):
        raise ValueError("Column identities changed.")
    indices = [positions[k] for k in snapshot.column_keys]
    old = np.asarray(snapshot.matrix)
    if old.shape != (len(snapshot.row_keys), len(indices)) or not np.array_equal(
        a[np.ix_(row_indices, indices)], old
    ):
        raise ValueError("Existing coefficients/scaling changed.")
    basis = [-1] * len(rows)
    for i, key in zip(row_indices, snapshot.basic_keys, strict=True):
        basis[i] = positions[key]
    for i, r in enumerate(rows):
        if basis[i] != -1:
            continue
        key = ("slack", r)
        if key not in positions:
            raise ValueError("Appended row has no structural slack.")
        basis[i] = positions[key]
    if len(set(basis)) != len(basis):
        raise ValueError("Duplicate basic column identities.")
    return basis


def solve_canonical(norm, options, snapshot=None, deadline=float("inf")):
    counters = dict(
        factorizations=0,
        factor_reuses=0,
        triangular_solves=0,
        refactorizations=0,
        primal_pivots=0,
        dual_pivots=0,
        cold_starts=0,
        warm_starts=0,
        fallback_reason="",
        method="revised",
        requested_method=options.lp_method,
    )
    a, b, c, basis, arts, keys, flips = _standard(norm)
    m, k = len(b), len(norm.costs)
    row_map, row_keys = list(range(m)), list(norm.row_keys)
    iterations = 0
    factor, last_basis = None, None

    # When propagation has removed every original row, the surviving problem is
    # a product of intervals. Solve it analytically and still verify original KKT.
    if m and all(origin[0] == "bound" for origin in norm.origins):
        counters.update(method="separable_presolve", cold_starts=1)
        if perf_counter() >= deadline or options.lp_iteration_limit == 0:
            return KernelResult(
                "limit",
                "time_limit" if perf_counter() >= deadline else "lp_iteration_limit",
                diagnostics=counters,
            )
        upper, source = np.full(k, np.inf), np.full(k, -1, dtype=int)
        for i, row in enumerate(norm.matrix):
            j = int(np.flatnonzero(row)[0])
            upper[j], source[j] = norm.rhs[i] / row[j], i
        point, dual = np.zeros(k), np.zeros(m)
        for j in np.flatnonzero(norm.costs > 0):
            if not np.isfinite(upper[j]):
                ray = np.zeros(k)
                ray[j] = 1.0
                return KernelResult("unbounded", "improving_ray", point, ray, diagnostics=counters)
            point[j] = upper[j]
            i = source[j]
            dual[i] = norm.costs[j] / norm.matrix[i, j]
        reduced = norm.costs - norm.matrix.T @ dual
        return KernelResult(
            "optimal", "separable_bounds", point, dual=dual, reduced=reduced, diagnostics=counters
        )

    def get_factor():
        nonlocal factor, last_basis
        if last_basis != tuple(basis):
            factor = QRFactor(a[:, basis], counters)
            last_basis = tuple(basis)
        return factor

    def state(cost):
        xb = basis_solve(b)
        lam = basis_solve(cost[basis], transpose=True)
        reduced = cost - a.T @ lam
        reduced[basis] = 0.0
        return xb, lam, reduced

    def basis_solve(rhs, transpose=False):
        nonlocal factor, last_basis
        try:
            return get_factor().solve(rhs, transpose)
        except np.linalg.LinAlgError:
            # Rebuild the factor once from the actual basis; the counter denotes
            # a real refactor attempt, never merely a returned failure status.
            factor, last_basis = None, None
            counters["refactorizations"] += 1
            return get_factor().solve(rhs, transpose)

    def finish(status, reason, xb=None, lam=None, reduced=None, ray=None, proof=False):
        point = None
        if xb is not None:
            full = np.zeros(a.shape[1])
            full[basis] = xb
            point = full[:k]
        dual = None
        if lam is not None:
            dual = np.zeros(m)
            dual[row_map] = flips[row_map] * lam
        snap = None
        if status == "optimal":
            snap = _snapshot(a, row_keys, keys, basis)
        counters["proof_kind"] = "farkas" if proof else None
        return KernelResult(
            status,
            reason,
            point,
            None if ray is None else ray[:k],
            dual,
            None if reduced is None else reduced[:k],
            iterations,
            counters.copy(),
            snap,
            a.copy(),
            b.copy(),
            tuple(basis),
            keys,
            tuple(row_keys),
        )

    def run(cost, mode="primal"):
        nonlocal iterations
        while True:
            if perf_counter() >= deadline:
                return "limit", "time_limit", None, None, None, None
            if iterations >= options.lp_iteration_limit:
                return "limit", "lp_iteration_limit", None, None, None, None
            xb, lam, rc = state(cost)
            nonbasic = [j for j in range(len(cost)) if j not in set(basis)]
            ptol = options.primal_tolerance * (1 + np.max(np.abs(xb), initial=0))
            dtol = options.dual_tolerance * (1 + np.abs(cost) + np.abs(a).T @ np.abs(lam))
            if mode == "primal":
                if np.min(xb, initial=0) < -ptol:
                    raise np.linalg.LinAlgError("Primal simplex lost feasibility.")
                entering = next((j for j in nonbasic if rc[j] > dtol[j]), None)
                if entering is None:
                    return "optimal", "optimal", xb, lam, rc, None
                direction = basis_solve(a[:, entering])
                eligible = [i for i, v in enumerate(direction) if v > options.pivot_tolerance]
                if not eligible:
                    ray = np.zeros(len(cost))
                    ray[entering] = 1.0
                    ray[basis] = -direction
                    return "unbounded", "improving_ray", xb, lam, rc, ray
                ratio = min(max(xb[i], 0) / direction[i] for i in eligible)
                ties = [
                    i
                    for i in eligible
                    if max(xb[i], 0) / direction[i] <= ratio + 1e-10 * (1 + abs(ratio))
                ]
                leaving = min(ties, key=lambda i: basis[i])
                counters["primal_pivots"] += 1
            else:
                if any(rc[j] > dtol[j] for j in nonbasic):
                    raise np.linalg.LinAlgError("Dual simplex lost dual feasibility.")
                eligible = [i for i, v in enumerate(xb) if v < -ptol]
                if not eligible:
                    return "optimal", "optimal", xb, lam, rc, None
                leaving = min(eligible, key=lambda i: basis[i])
                unit = np.zeros(len(b))
                unit[leaving] = 1.0
                witness = basis_solve(unit, transpose=True)
                tableau = a.T @ witness
                candidates = [j for j in nonbasic if tableau[j] < -options.pivot_tolerance]
                if not candidates:
                    return "infeasible", "dual_farkas", xb, witness, -a.T @ witness, None
                entering = min(candidates, key=lambda j: (rc[j] / tableau[j], j))
                counters["dual_pivots"] += 1
            basis[leaving] = entering
            iterations += 1

    # Empty row systems need neither a basis nor Phase I.
    if not m:
        if perf_counter() >= deadline or options.lp_iteration_limit == 0:
            return finish(
                "limit", "time_limit" if perf_counter() >= deadline else "lp_iteration_limit"
            )
        positive = np.flatnonzero(c > options.dual_tolerance)
        if len(positive):
            ray = np.zeros(len(c))
            ray[positive[0]] = 1
            return KernelResult(
                "unbounded",
                "improving_ray",
                np.zeros(k),
                ray[:k],
                iterations=0,
                diagnostics=counters,
            )
        return finish("optimal", "optimal", np.empty(0), np.empty(0), c)
    try:
        if snapshot is not None:
            try:
                # Artificial columns are removed from a candidate warm system.
                keep = [j for j in range(a.shape[1]) if j not in arts]
                warm_a, warm_keys = a[:, keep], tuple(keys[j] for j in keep)
                warm_basis = _map_basis(snapshot, warm_a, row_keys, warm_keys)
                saved = a, c, keys, basis
                a, c, keys, basis = warm_a, c[keep], warm_keys, warm_basis
                xb, lam, rc = state(c)
                feasible = np.min(xb, initial=0) >= -options.primal_tolerance
                dual_feasible = np.max(rc, initial=0) <= options.dual_tolerance * (
                    1 + np.max(np.abs(c), initial=0)
                )
                if not feasible and not dual_feasible:
                    raise ValueError("Warm basis is neither primal nor dual feasible.")
                mode = (
                    "dual"
                    if dual_feasible and (not feasible or options.lp_method == "dual")
                    else "primal"
                )
                if options.lp_method == "primal" and not feasible:
                    raise ValueError("Requested primal mode needs a primal-feasible warm basis.")
                counters["warm_starts"] = 1
                counters["warm_mode"] = mode
                out = run(c, mode)
                return finish(*out[:2], *out[2:5], ray=out[5], proof=out[0] == "infeasible")
            except (ValueError, KeyError, IndexError, np.linalg.LinAlgError) as exc:
                counters["fallback_reason"] = str(exc)
                if "saved" in locals():
                    a, c, keys, basis = saved
                factor, last_basis = None, None
        counters["cold_starts"] = 1
        if arts:
            phase = np.zeros(len(c))
            phase[list(arts)] = -1.0
            out = run(phase)
            if out[0] != "optimal":
                return finish(*out[:2], *out[2:5], ray=out[5])
            xb, lam, rc = out[2:5]
            if phase[basis] @ xb < -options.primal_tolerance:
                return finish("infeasible", "phase_one_farkas", xb, lam, rc, proof=True)
            for art in sorted(arts):
                if art not in basis:
                    continue
                position = basis.index(art)
                unit = np.zeros(len(b))
                unit[position] = 1
                tableau = a.T @ basis_solve(unit, transpose=True)
                pivot = next(
                    (
                        j
                        for j in range(len(c))
                        if j not in arts
                        and j not in basis
                        and abs(tableau[j]) > options.pivot_tolerance
                    ),
                    None,
                )
                if pivot is not None:
                    basis[position] = pivot
                else:
                    physical = int(np.flatnonzero(a[:, art])[0])
                    a = np.delete(a, physical, axis=0)
                    b = np.delete(b, physical)
                    row_map.pop(physical)
                    row_keys.pop(physical)
                    basis.pop(position)
                factor, last_basis = None, None
            keep = [j for j in range(len(c)) if j not in arts]
            lookup = {j: i for i, j in enumerate(keep)}
            a, c = a[:, keep], c[keep]
            basis = [lookup[j] for j in basis]
            keys = tuple(keys[j] for j in keep)
            factor, last_basis = None, None
        out = run(c)
        return finish(*out[:2], *out[2:5], ray=out[5], proof=out[0] == "infeasible")
    except (np.linalg.LinAlgError, FloatingPointError, OverflowError) as exc:
        return finish("numerical_failure", str(exc))
