"""SILO's sparse two-phase revised simplex and private factor-session adapter."""

from copy import deepcopy
from math import isfinite
from time import perf_counter

import numpy as np
from scipy.sparse import coo_matrix, csc_matrix, hstack

from silo.lp.kernel import BasisSnapshot, KernelResult
from silo.lp.sparse_factor import (
    FACTOR_POLICY,
    RESIDUAL_TOLERANCE,
    FactorDeadline,
    FactorResourceError,
    FactorRetry,
    SparseCoefficients,
    SparseFactor,
    canonical,
    coefficients,
    increment,
    pivot_safe,
    same_matrix,
)


def _infinity_norm(value):
    return float(np.max(np.abs(value), initial=0))


def _residual_observation(matrix, rhs, solution):
    """Pure observation with the factor's existing scale; no solve or counters."""
    residual = rhs - matrix @ solution
    norm = _infinity_norm(residual)
    bound = RESIDUAL_TOLERANCE * (
        1 + _infinity_norm(rhs) + _infinity_norm(abs(matrix) @ abs(solution))
    )
    return {
        "infinity_norm": norm,
        "bound": bound,
        "within_bound": bool(np.isfinite(residual).all() and norm <= bound),
    }


def _matrix_observation(matrix):
    import hashlib

    digest = hashlib.sha256()
    for value in (
        np.asarray(matrix.shape, dtype=np.int64),
        matrix.indptr,
        matrix.indices,
        matrix.data,
    ):
        digest.update(value.tobytes())
    return {"shape": matrix.shape, "nnz": int(matrix.nnz), "csc_sha256": digest.hexdigest()}


class _PivotObservation:
    """Only the last committed pivot, holding sparse references and O(m) vectors.

    Residual matrix products and serialization happen on failure, never in the
    ordinary pivot path. The factor replaces its CSC object instead of changing
    the old CSC in place, so retaining that read-only reference is safe.
    """

    def __init__(
        self,
        old_matrix,
        rhs,
        xb,
        direction,
        column,
        theta,
        leaving,
        old_keys,
        new_keys,
        entering_key,
        run_identity,
        mode,
        pivot_tolerance,
        primal_tolerance,
        old_metadata,
        new_matrix,
        new_metadata,
    ):
        self.old_matrix, self.new_matrix = old_matrix, new_matrix
        self.rhs, self.xb, self.direction, self.column = (
            np.array(value, copy=True) for value in (rhs, xb, direction, column)
        )
        self.theta, self.leaving = float(theta), leaving
        self.old_keys, self.new_keys = old_keys, new_keys
        self.entering_key, self.run_identity, self.mode = entering_key, run_identity, mode
        self.old_metadata, self.new_metadata = old_metadata, new_metadata
        self.old_ptol = primal_tolerance * (1 + _infinity_norm(xb))
        self.primal_tolerance = primal_tolerance
        self.pivot_tolerance = pivot_tolerance
        self.predicted = self.xb - self.theta * self.direction
        self.predicted[leaving] = self.theta  # This is the ENTERING basic coordinate.

    def matches(self, factor, basis_keys, run_identity):
        return (
            self.run_identity == run_identity
            and self.mode == "primal"
            and self.new_keys == basis_keys
            and same_matrix(self.new_matrix, factor.matrix)
        )

    def trace(self, before, after, outcome, recovery_error=None):
        positive = np.flatnonzero(self.direction > 0)
        ratios = np.maximum(self.xb[positive], 0) / self.direction[positive]
        minimum = float(np.min(ratios)) if len(ratios) else None
        second = float(np.partition(ratios, 1)[1]) if len(ratios) > 1 else None
        larger = ratios[ratios > minimum] if minimum is not None else np.array([])
        positions = set(map(int, np.argsort(before["xb"], kind="stable")[:8]))
        if after is not None:
            positions.update(map(int, np.argsort(after["xb"], kind="stable")[:8]))
        positions = sorted(positions | {self.leaving})  # At most 17 projected coordinates.
        projections = []
        for i in positions:
            d = float(self.direction[i])
            projections.append(
                {
                    "position": i,
                    "old_basic_key": self.old_keys[i],
                    "new_basic_key": self.new_keys[i],
                    "old_xb": float(self.xb[i]),
                    "old_direction": d,
                    "old_raw_ratio": float(self.xb[i] / d) if d else None,
                    "old_selection_ratio": float(max(self.xb[i], 0) / d) if d > 0 else None,
                    "predicted_new_basic": float(self.predicted[i]),
                    "fresh_before_rebase": float(before["xb"][i]),
                    "fresh_after_rebase": None if after is None else float(after["xb"][i]),
                }
            )
        result = {
            "run_identity": self.run_identity,
            "mode": self.mode,
            "outcome": outcome,
            "entering_key": self.entering_key,
            "leaving_key": self.old_keys[self.leaving],
            "leaving_position": self.leaving,
            "theta": self.theta,
            "old_basis_keys": self.old_keys,
            "new_basis_keys": self.new_keys,
            "old_factor": self.old_metadata,
            "committed_factor": self.new_metadata,
            "before_recheck_factor": before["metadata"],
            "after_recheck_factor": None if after is None else after["metadata"],
            "old_matrix": _matrix_observation(self.old_matrix),
            "committed_matrix": _matrix_observation(self.new_matrix),
            "before_recheck_matrix": _matrix_observation(before["matrix"]),
            "after_recheck_matrix": None if after is None else _matrix_observation(after["matrix"]),
            "minimum_computed_ratio": minimum,
            "second_computed_ratio_including_ties": second,
            "next_distinct_computed_ratio": float(np.min(larger)) if len(larger) else None,
            "ratio_convention": "max(old_xb,0)/d for every strictly positive d",
            "direction_infinity_norm": _infinity_norm(self.direction),
            "pivot_value": float(self.direction[self.leaving]),
            "pivot_acceptance_threshold": self.pivot_tolerance
            * (1 + _infinity_norm(self.direction)),
            "growth_indicator": max(
                _infinity_norm(self.direction), 1 / abs(float(self.direction[self.leaving]))
            ),
            "old_state_residual": _residual_observation(self.old_matrix, self.rhs, self.xb),
            "direction_residual": _residual_observation(
                self.old_matrix, self.column, self.direction
            ),
            "predicted_new_state_residual": _residual_observation(
                self.new_matrix, self.rhs, self.predicted
            ),
            "fresh_before_residual": _residual_observation(
                before["matrix"], self.rhs, before["xb"]
            ),
            "fresh_after_residual": None
            if after is None
            else _residual_observation(after["matrix"], self.rhs, after["xb"]),
            "old_primal_threshold": self.old_ptol,
            "predicted_primal_threshold": self.primal_tolerance
            * (1 + _infinity_norm(self.predicted)),
            "old_minimum_basic": float(np.min(self.xb)),
            "predicted_minimum_basic": float(np.min(self.predicted)),
            "before_recheck_primal_threshold": before["ptol"],
            "after_recheck_primal_threshold": None if after is None else after["ptol"],
            "before_argmin_position": int(np.argmin(before["xb"])),
            "before_argmin_basic_key": self.new_keys[int(np.argmin(before["xb"]))],
            "after_argmin_position": None if after is None else int(np.argmin(after["xb"])),
            "after_argmin_basic_key": None
            if after is None
            else self.new_keys[int(np.argmin(after["xb"]))],
            "rejected_before_recheck": before.get("rejected_keys", ()),
            "rejected_after_recheck": None if after is None else after.get("rejected_keys", ()),
            "coordinate_projections": projections,
            "vector_storage": (
                "Only last pivot O(m) vectors retained privately; output is bounded projections."
            ),
        }
        if recovery_error is not None:
            result["recovery_error"] = recovery_error
        return result


def _column(matrix, index):
    """One allowed dense direction vector; never materialize a full matrix."""
    value = np.zeros(matrix.shape[0])
    lo, hi = matrix.indptr[index : index + 2]
    value[matrix.indices[lo:hi]] = matrix.data[lo:hi]
    return value


def _standard(norm, options):
    m, k = len(norm.rhs), len(norm.costs)
    keys = [("variable", norm.data.names[i], direction) for i, direction in norm.column_origins]
    rows, cols, values, basis, arts = [], [], [], [], set()
    flips = np.where(norm.rhs < 0, -1.0, 1.0)
    for i, original_sense in enumerate(norm.senses):
        sense = (
            {"<=": ">=", ">=": "<=", "=": "="}[original_sense] if flips[i] < 0 else original_sense
        )
        if sense != "=":
            keys.append(("slack", norm.row_keys[i]))
            rows.append(i)
            cols.append(len(keys) - k - 1)
            values.append(1.0 if sense == "<=" else -1.0)
        if sense != "<=":
            keys.append(("artificial", norm.row_keys[i]))
            rows.append(i)
            cols.append(len(keys) - k - 1)
            values.append(1.0)
            arts.add(len(keys) - 1)
        basis.append(len(keys) - 1)
    expected = int(norm.matrix.nnz) + len(values)
    if expected > options.max_sparse_nnz:
        raise FactorResourceError("Standard form exceeds max_sparse_nnz.")
    original = norm.matrix.multiply(flips[:, None])
    extra = coo_matrix((values, (rows, cols)), shape=(m, len(keys) - k))
    a = canonical(hstack((original, extra), format="csc"))
    c = np.zeros(len(keys))
    c[:k] = norm.costs
    return a, abs(norm.rhs), c, basis, arts, tuple(keys), flips


def _decode(record, rows, columns):
    if not isinstance(record, SparseCoefficients) or record.shape != (rows, columns):
        raise ValueError("Sparse snapshot coefficient shape mismatch.")
    if (
        len(record.indptr) != columns + 1
        or not record.indptr
        or record.indptr[0] != 0
        or record.indptr[-1] != len(record.values)
        or len(record.indices) != len(record.values)
    ):
        raise ValueError("Malformed sparse snapshot pointers.")
    if (
        any(type(v) is not int for v in record.indptr + record.indices)
        or any(a > b for a, b in zip(record.indptr, record.indptr[1:], strict=False))
        or any(not 0 <= i < rows for i in record.indices)
        or any(not isfinite(v) or v == 0 for v in record.values)
    ):
        raise ValueError("Malformed sparse snapshot coefficients.")
    for j in range(columns):
        support = record.indices[record.indptr[j] : record.indptr[j + 1]]
        if any(a >= b for a, b in zip(support, support[1:], strict=False)):
            raise ValueError("Sparse snapshot indices must be canonical.")
    return csc_matrix((record.values, record.indices, record.indptr), shape=record.shape)


def _map_basis(snapshot, a, rows, keys):
    if not isinstance(snapshot, BasisSnapshot) or snapshot.version not in (2, 3):
        raise ValueError("Expected a supported immutable BasisSnapshot.")
    if len(snapshot.basic_keys) != len(snapshot.row_keys):
        raise ValueError("Snapshot basis shape mismatch.")
    try:
        row_set, column_set = set(snapshot.row_keys), set(snapshot.column_keys)
        if len(row_set) != len(snapshot.row_keys) or len(column_set) != len(snapshot.column_keys):
            raise ValueError("Duplicate snapshot semantic keys.")
        # Insertions are legitimate extensions. Existing semantic order must stay.
        if tuple(r for r in rows if r in row_set) != snapshot.row_keys:
            raise ValueError("Old rows changed or reordered.")
        if tuple(k for k in keys if k in column_set) != snapshot.column_keys:
            raise ValueError("Old columns changed or reordered.")
        row_positions, positions = (
            {r: i for i, r in enumerate(rows)},
            {k: i for i, k in enumerate(keys)},
        )
        if len(row_positions) != len(rows) or len(positions) != len(keys):
            raise ValueError("Duplicate current semantic keys.")
        ri = [row_positions[r] for r in snapshot.row_keys]
        ci = [positions[k] for k in snapshot.column_keys]
        if snapshot.version == 3:
            old = _decode(snapshot.matrix, len(ri), len(ci))
        else:
            # Legacy data already are dense passive tuples. Read their nonzeros
            # directly without allocating another full dense model-sized array.
            rr, cc, vv = [], [], []
            if len(snapshot.matrix) != len(ri):
                raise ValueError("Legacy snapshot row shape mismatch.")
            for i, row in enumerate(snapshot.matrix):
                if len(row) != len(ci):
                    raise ValueError("Legacy snapshot column shape mismatch.")
                for j, value in enumerate(row):
                    if not isfinite(value):
                        raise ValueError("Nonfinite legacy snapshot coefficient.")
                    if value:
                        rr.append(i)
                        cc.append(j)
                        vv.append(value)
            old = coo_matrix((vv, (rr, cc)), shape=(len(ri), len(ci))).tocsc()
        if not same_matrix(a[ri, :][:, ci], old):
            raise ValueError("Existing coefficients/scaling changed.")
        basis = [-1] * len(rows)
        for i, key in zip(ri, snapshot.basic_keys, strict=True):
            basis[i] = positions[key]
        for i, row in enumerate(rows):
            if basis[i] == -1:
                basis[i] = positions[("slack", row)]
        if len(set(basis)) != len(basis):
            raise ValueError("Duplicate mapped basis columns.")
        return basis
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError("Snapshot semantic mapping failed.") from exc


class Devex:
    """Fixed reference-frame Devex, with a fresh sticky Bland history per phase."""

    def __init__(self, keys, basis, counters):
        self.keys, self.counters = keys, counters
        self.reference, self.weights = set(), {}
        self.visited, self.bland, self.degenerate = set(), False, 0
        self.reset(basis, "initial")

    def reset(self, basis, reason):
        basic = {self.keys[j] for j in basis}
        self.reference = set(self.keys) - basic
        self.weights = dict.fromkeys(self.keys, 1.0)
        increment(self.counters, "devex_resets")
        increment(self.counters.setdefault("devex_reset_reasons", {}), reason)

    def fresh_phase(self, keys, basis, reason, preserve=False):
        self.keys = keys
        self.visited, self.bland, self.degenerate = set(), False, 0
        increment(self.counters, "bland_history_resets")
        if not preserve:
            self.reset(basis, reason)
        else:
            present = set(keys)
            new = present - self.weights.keys()
            self.weights = {key: self.weights.get(key, 1.0) for key in keys}
            self.reference.intersection_update(present)
            self.reference.update(new)

    def basis_seen(self, basis):
        signature = tuple(self.keys[j] for j in basis)
        if signature in self.visited and not self.bland:
            self.bland = True
            increment(self.counters, "bland_triggers")
            increment(self.counters.setdefault("bland_trigger_reasons", {}), "repeated_basis")
        self.visited.add(signature)

    def step(self, theta, tolerance):
        self.degenerate = self.degenerate + 1 if theta <= tolerance else 0
        if self.degenerate >= 2 and not self.bland:
            self.bland = True
            increment(self.counters, "bland_triggers")
            increment(self.counters.setdefault("bland_trigger_reasons", {}), "two_degenerate_steps")

    def entering(self, eligible, reduced, basis):
        if any(not isfinite(self.weights.get(self.keys[j], 1)) for j in eligible):
            self.reset(basis, "nonfinite_weight")
        if self.bland:
            increment(self.counters, "bland_pricings")
            return min(eligible, key=lambda j: self.keys[j])
        increment(self.counters, "devex_pricings")
        scale = max(abs(float(reduced[j])) for j in eligible)
        return min(
            eligible,
            key=lambda j: (
                -((float(reduced[j]) / scale) ** 2 / max(1e-12, self.weights[self.keys[j]])),
                self.keys[j],
            ),
        )

    def update(self, a, basis, entering, leaving, direction, basis_solve):
        alpha = direction[leaving]
        unit = np.zeros(len(basis))
        unit[leaving] = 1
        rho = basis_solve(unit, True)
        # A residual recovery in BTRAN may have reset the reference. Evaluate
        # gamma AFTER that solve, using the then-current reference frame.
        gamma = sum(
            float(direction[i]) ** 2 for i, j in enumerate(basis) if self.keys[j] in self.reference
        ) + int(self.keys[entering] in self.reference)
        t = np.asarray(a.T @ rho).reshape(-1) / alpha
        values = {}
        basic = set(basis)
        for j, key in enumerate(self.keys):
            if j not in basic and j != entering:
                values[key] = max(
                    0.99 * self.weights.get(key, 1),
                    float(t[j]) ** 2 * gamma + int(key in self.reference),
                    1e-12,
                )
        values[self.keys[basis[leaving]]] = max(1e-12, gamma / alpha**2)
        if not isfinite(gamma) or any(not isfinite(v) for v in values.values()):
            return None
        return values


def _frame(norm, flips, row_map):
    modes = []
    for i, name in enumerate(norm.data.names):
        mode = (
            "fixed"
            if norm.lower[i] == norm.upper[i]
            else "lower"
            if isfinite(norm.lower[i])
            else "upper"
            if isfinite(norm.upper[i])
            else "free"
        )
        modes.append((name, mode))
    columns = tuple(
        (("variable", norm.data.names[i], direction), float(norm.col_scale[j]))
        for j, (i, direction) in enumerate(norm.column_origins)
    )
    rows = tuple(
        (norm.row_keys[i], norm.senses[i], float(norm.row_scale[i]), float(flips[i]))
        for i in row_map
    )
    return {"rows": rows, "columns": columns, "modes": tuple(modes), "policy": FACTOR_POLICY}


def _compatible_frame(old, current):
    if old["rows"] != current["rows"] or old["policy"] != current["policy"]:
        return False
    if current["modes"][: len(old["modes"])] != old["modes"]:
        return False
    previous = dict(old["columns"])
    filtered = tuple((key, value) for key, value in current["columns"] if key in previous)
    return filtered == old["columns"]


def _dependent_in_original_space(norm, a, b, basis, rows, keys, position, options, deadline):
    """A small floating coefficient is never a proof that a row is dependent."""
    from fractions import Fraction
    from types import SimpleNamespace

    from silo.lp.tableau_view import _exact_basis_data, proof_workspace_cells
    from silo.utils.rational import ProofBudget, ProofLimitError, exact_solve

    native = SimpleNamespace(basis=tuple(basis), row_keys=tuple(rows), column_keys=tuple(keys))
    budget = ProofBudget(options.proof_operation_limit, deadline)
    try:
        with budget.workspace(proof_workspace_cells(norm, native)):
            raw_basis, rhs, raw_rows, _, flips = _exact_basis_data(norm, native, budget)
            unit = [Fraction(int(i == position)) for i in range(len(basis))]
            weights = exact_solve(list(zip(*raw_basis, strict=True)), unit, budget=budget)
            if sum((w * value for w, value in zip(weights, rhs, strict=True)), Fraction(0)):
                return False
            normal = [Fraction(0)] * len(norm.data.names)
            positions = {key: i for i, key in enumerate(rows)}
            for w, row, flip in zip(weights, raw_rows, flips, strict=True):
                if w:
                    for j, coefficient in row.items():
                        normal[j] = budget.guard(normal[j] + w * flip * coefficient)
            names = {name: i for i, name in enumerate(norm.data.names)}
            for key in keys:
                budget.charge()
                if key[0] == "variable" and normal[names[key[1]]]:
                    return False
                if key[0] == "slack" and weights[positions[key[1]]]:
                    return False
            return True
    except (ProofLimitError, ValueError, OverflowError, ZeroDivisionError):
        if perf_counter() >= deadline:
            raise FactorDeadline("time_limit") from None
        return False


def solve_canonical(norm, options, snapshot=None, deadline=float("inf"), factor_state=None):
    counters = dict(
        engine="sparse",
        method="sparse_revised",
        pricing="devex",
        requested_method=options.lp_method,
        base_factorizations=0,
        factorizations=0,
        factor_reuses=0,
        triangular_solves=0,
        refactorizations=0,
        refactorizations_by_reason={},
        eta_updates=0,
        basis_replacements=0,
        within_solve_reuses=0,
        cross_solve_reuses=0,
        cold_fallbacks=0,
        primal_pivots=0,
        dual_pivots=0,
        artificial_cleanup_pivots=0,
        dependent_rows_removed=0,
        cold_starts=0,
        warm_starts=0,
        fallback_reason="",
        input_nnz=int(norm.data.a.nnz),
        normalized_nnz=int(norm.matrix.nnz),
        dense_model_allocations=0,
    )
    try:
        a, b, c, basis, arts, keys, flips = _standard(norm, options)
    except (MemoryError, FactorResourceError) as exc:
        return KernelResult(
            "limit", "resource_limit", diagnostics={**counters, "message": str(exc)}
        )
    m, k = len(b), len(norm.costs)
    row_map, row_keys = list(range(m)), list(norm.row_keys)
    counters["standard_nnz"] = int(a.nnz)
    counters["standard_storage_bytes"] = int(a.data.nbytes + a.indices.nbytes + a.indptr.nbytes)
    iterations, factor = 0, None
    last_pivot, feasibility_rechecked, run_number = None, False, 0
    pricing = Devex(keys, basis, counters)

    def get_factor():
        nonlocal factor
        if factor is None:
            factor = SparseFactor(a[:, basis], options, counters, deadline)
            pricing.reset(basis, "new_factor")
        return factor

    def basis_solve(rhs, transpose=False, expected_generation=None):
        current = get_factor()
        before = current.generation
        answer = current.solve(rhs, transpose)
        if current.generation != before:
            pricing.reset(basis, "factor_recovery")
        if expected_generation is not None and current.generation != expected_generation:
            raise FactorRetry("basis_solve_rebased", current.generation)
        return answer

    def state(cost):
        # Initial construction happens before selecting the token. A rebase in
        # either solve invalidates BOTH vectors, even if each residual is valid.
        for _ in range(3):
            generation = get_factor().generation
            xb = basis_solve(b)
            if get_factor().generation != generation:
                increment(counters, "state_generation_restarts")
                continue
            dual = basis_solve(cost[basis], True)
            if get_factor().generation != generation:
                increment(counters, "state_generation_restarts")
                continue
            reduced = np.asarray(cost - a.T @ dual).reshape(-1)
            reduced[basis] = 0
            return xb, dual, reduced, generation
        raise np.linalg.LinAlgError("State factor-generation retry limit.")

    def same_generation(generation):
        if get_factor().generation != generation:
            raise FactorRetry("uncommitted_generation_changed", get_factor().generation)

    def factor_metadata():
        current = get_factor()
        return {
            "generation": current.generation,
            "eta_chain_length": len(current.etas),
            "last_refactor_reason": current.last_refactor_reason,
            "refactorizations_by_reason": counters["refactorizations_by_reason"].copy(),
        }

    def state_observation(xb):
        return {
            "xb": xb.copy(),
            "matrix": get_factor().matrix,
            "metadata": factor_metadata(),
            "ptol": options.primal_tolerance * (1 + _infinity_norm(xb)),
        }

    def primal_state(cost, values, run_identity, rejected):
        nonlocal feasibility_rechecked
        xb, _, _, _ = values
        tolerance = options.primal_tolerance * (1 + _infinity_norm(xb))
        if np.min(xb, initial=0) >= -tolerance:
            return values
        before = state_observation(xb)
        before["rejected_keys"] = tuple(sorted(keys[j] for j in rejected))
        if last_pivot is None or not last_pivot.matches(
            get_factor(), tuple(keys[j] for j in basis), run_identity
        ):
            counters["lost_feasibility_without_matching_pivot"] = True
            raise np.linalg.LinAlgError("Primal simplex lost feasibility.")
        if feasibility_rechecked:
            previous = counters.get("last_pivot_trace")
            counters["last_pivot_trace"] = last_pivot.trace(before, None, "already_rechecked")
            if previous is not None:
                counters["last_pivot_trace"]["prior_recheck"] = previous
            raise np.linalg.LinAlgError(
                "Primal feasibility failed after its one current-B recheck."
            )
        feasibility_rechecked = True
        increment(counters, "primal_feasibility_rechecks")
        try:
            get_factor().refactor(reason="primal_feasibility")
            pricing.reset(basis, "primal_feasibility")
            fresh = state(cost)
        except (FactorDeadline, MemoryError, np.linalg.LinAlgError) as exc:
            counters["last_pivot_trace"] = last_pivot.trace(
                before, None, "recheck_failed", str(exc)
            )
            raise
        after = state_observation(fresh[0])
        after["rejected_keys"] = tuple(sorted(keys[j] for j in rejected))
        # Backward residuals are recorded below; componentwise feasibility is
        # always decided independently using the unchanged primal threshold.
        recovered = np.min(fresh[0], initial=0) >= -after["ptol"]
        counters["last_pivot_trace"] = last_pivot.trace(
            before, after, "recovered" if recovered else "persistent_failure"
        )
        if not recovered:
            raise np.linalg.LinAlgError("Primal feasibility failed after current-B recheck.")
        increment(counters, "primal_feasibility_recoveries")
        return fresh

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
        snap, cache = None, {}
        if status == "optimal":
            snap = BasisSnapshot(
                3, tuple(row_keys), tuple(keys), coefficients(a), tuple(keys[j] for j in basis)
            )
            if factor is not None:
                cache = {
                    "factor": factor,
                    "basic_keys": snap.basic_keys,
                    "frame": _frame(norm, flips, row_map),
                    "pricing": pricing,
                    "phase": "phase2",
                }
        counters["proof_kind"] = "farkas" if proof else None
        counters["final_basis_rows"] = len(basis)
        result = KernelResult(
            status,
            reason,
            point,
            None if ray is None else ray[:k],
            dual,
            None if reduced is None else reduced[:k],
            iterations,
            deepcopy(counters),
            snap,
            a.copy(),
            b.copy(),
            tuple(basis),
            tuple(keys),
            tuple(row_keys),
        )
        # The parent pipeline consumes and deletes this transfer slot before
        # exposing result._lp, so the session remains the sole mutable owner.
        result._factor_state = cache
        return result

    def pivot(entering, leaving, generation, direction=None, observation=None):
        nonlocal iterations, last_pivot, feasibility_rechecked
        column = _column(a, entering)
        direction = (
            basis_solve(column, expected_generation=generation) if direction is None else direction
        )
        same_generation(generation)
        old_matrix = get_factor().matrix
        old_metadata = factor_metadata()
        old_keys = tuple(keys[j] for j in basis) if observation is not None else None
        try:
            rebuilt = get_factor().replace_column(
                leaving, column, direction, expected_generation=generation
            )
        except FactorRetry:
            pricing.reset(basis, "commit_retry")
            raise
        basis[leaving] = entering
        iterations += 1
        feasibility_rechecked = False
        counters.pop("last_pivot_trace", None)
        if observation is not None:
            xb, theta, run_identity, mode = observation
            if theta is None:
                theta = xb[leaving] / direction[leaving]
            last_pivot = _PivotObservation(
                old_matrix,
                b,
                xb,
                direction,
                column,
                theta,
                leaving,
                old_keys,
                tuple(keys[j] for j in basis),
                keys[entering],
                run_identity,
                mode,
                options.pivot_tolerance,
                options.primal_tolerance,
                old_metadata,
                get_factor().matrix,
                factor_metadata(),
            )
        else:
            last_pivot = None
        return rebuilt

    def run(cost, mode="primal", phase="phase_two"):
        nonlocal last_pivot, run_number
        run_number += 1
        run_identity = (run_number, phase, mode)
        last_pivot = None
        counters.pop("last_pivot_trace", None)
        selected_basis = None
        rejected, refreshed, retries = set(), False, 0
        while True:
            if perf_counter() >= deadline:
                return "limit", "time_limit", None, None, None, None
            if iterations >= options.lp_iteration_limit:
                return "limit", "lp_iteration_limit", None, None, None, None
            if selected_basis != tuple(basis):
                selected_basis = tuple(basis)
                rejected, refreshed, retries = set(), False, 0
                pricing.basis_seen(basis)
            xb, lam, rc, generation = state(cost)
            if mode == "primal":
                xb, lam, rc, generation = primal_state(
                    cost, (xb, lam, rc, generation), run_identity, rejected
                )
            basic = set(basis)
            nonbasic = [j for j in range(len(cost)) if j not in basic]
            ptol = options.primal_tolerance * (1 + np.max(abs(xb), initial=0))
            dtol = options.dual_tolerance * (1 + abs(cost) + abs(a).T @ abs(lam))
            try:
                if mode == "primal":
                    if np.min(xb, initial=0) < -ptol:
                        raise np.linalg.LinAlgError("Primal simplex lost feasibility.")
                    while True:
                        if perf_counter() >= deadline:
                            return "limit", "time_limit", None, None, None, None
                        improving = [j for j in nonbasic if rc[j] > dtol[j]]
                        if not improving:
                            if rejected:
                                raise np.linalg.LinAlgError(
                                    "Rejected entering history cannot establish optimality."
                                )
                            return "optimal", "optimal", xb, lam, rc, None
                        eligible = [j for j in improving if j not in rejected]
                        if not eligible:
                            raise np.linalg.LinAlgError(
                                "Unsafe blocking pivot: all improving columns were rejected."
                            )
                        entering = pricing.entering(eligible, rc, basis)
                        direction = basis_solve(
                            _column(a, entering), expected_generation=generation
                        )
                        candidates = [i for i, value in enumerate(direction) if value > 0]
                        if not candidates:
                            ray = np.zeros(len(cost))
                            ray[entering], ray[basis] = 1, -direction
                            return "unbounded", "improving_ray", xb, lam, rc, ray
                        theta = min(max(xb[i], 0) / direction[i] for i in candidates)
                        ties = [i for i in candidates if max(xb[i], 0) / direction[i] == theta]
                        safe = [
                            i for i in ties if pivot_safe(direction, i, options.pivot_tolerance)
                        ]
                        if safe:
                            break
                        if not refreshed:
                            refreshed = True
                            get_factor().refactor(reason="pivot_selection")
                            pricing.reset(basis, "pivot_selection")
                            raise FactorRetry("pivot_selection", get_factor().generation)
                        rejected.add(entering)
                        increment(counters, "rejected_entering_columns")
                        increment(
                            counters.setdefault("pivot_rejection_reasons", {}),
                            "unsafe_true_blocker",
                        )
                        pricing.reset(basis, "rejected_pivot")
                    leaving = min(safe, key=lambda i: keys[basis[i]])

                    def checked_solve(rhs, transpose=False, token=generation):
                        return basis_solve(rhs, transpose, token)

                    weights = pricing.update(a, basis, entering, leaving, direction, checked_solve)
                    same_generation(generation)
                    rebuilt = pivot(
                        entering, leaving, generation, direction, (xb, theta, run_identity, mode)
                    )
                    if rebuilt or weights is None:
                        pricing.reset(basis, "factor_rebuild" if rebuilt else "nonfinite_weight")
                    else:
                        pricing.weights.update(weights)
                    pricing.step(theta, options.primal_tolerance)
                    increment(counters, "primal_pivots")
                else:
                    if any(rc[j] > dtol[j] for j in nonbasic):
                        raise np.linalg.LinAlgError("Dual simplex lost dual feasibility.")
                    candidates = [i for i, value in enumerate(xb) if value < -ptol]
                    if not candidates:
                        return "optimal", "optimal", xb, lam, rc, None
                    leaving = min(candidates, key=lambda i: keys[basis[i]])
                    unit = np.zeros(len(b))
                    unit[leaving] = 1
                    witness = basis_solve(unit, True, generation)
                    tableau = np.asarray(a.T @ witness).reshape(-1)
                    same_generation(generation)
                    eligible = [j for j in nonbasic if tableau[j] < -options.pivot_tolerance]
                    if not eligible:
                        return "infeasible", "dual_farkas", xb, witness, -a.T @ witness, None
                    entering = min(eligible, key=lambda j: (rc[j] / tableau[j], keys[j]))
                    pivot(entering, leaving, generation, observation=(xb, None, run_identity, mode))
                    pricing.reset(basis, "dual_pivot")
                    increment(counters, "dual_pivots")
            except FactorRetry as exc:
                retries += 1
                increment(counters, "pivot_generation_restarts")
                increment(counters.setdefault("generation_restart_reasons", {}), exc.reason)
                if retries > 3:
                    raise np.linalg.LinAlgError("Current-B factor-generation retry limit.") from exc

    if not m:
        if perf_counter() >= deadline or options.lp_iteration_limit == 0:
            return finish(
                "limit", "time_limit" if perf_counter() >= deadline else "lp_iteration_limit"
            )
        improving = np.flatnonzero(c > options.dual_tolerance)
        if len(improving):
            ray = np.zeros(len(c))
            ray[improving[0]] = 1
            return finish("unbounded", "improving_ray", np.empty(0), ray=ray)
        return finish("optimal", "optimal", np.empty(0), np.empty(0), c)
    try:
        if snapshot is not None:
            saved = a, c, keys, basis
            try:
                keep = [j for j in range(len(c)) if j not in arts]
                warm_a, warm_keys = a[:, keep], tuple(keys[j] for j in keep)
                warm_basis = _map_basis(snapshot, warm_a, row_keys, warm_keys)
                a, c, keys, basis = warm_a, c[keep], warm_keys, warm_basis
                pricing.fresh_phase(keys, basis, "warm_start")
                if (
                    isinstance(factor_state, dict)
                    and snapshot.version == 3
                    and isinstance(factor_state.get("factor"), SparseFactor)
                ):
                    owned = factor_state["factor"]
                    valid = (
                        factor_state.get("basic_keys") == tuple(keys[j] for j in basis)
                        and _compatible_frame(factor_state["frame"], _frame(norm, flips, row_map))
                        and same_matrix(owned.matrix, a[:, basis])
                    )
                    if valid:
                        factor = owned
                        rebuilt = factor.configure(options, counters, deadline)
                        if not rebuilt:
                            increment(counters, "cross_solve_reuses")
                        if factor_state.get("phase") == "phase2" and not rebuilt:
                            previous_pricing = factor_state.get("pricing")
                            if isinstance(previous_pricing, Devex):
                                pricing = previous_pricing
                                pricing.counters = counters
                                pricing.fresh_phase(keys, basis, "public_solve", preserve=True)
                    else:
                        increment(counters, "cache_invalidations")
                        counters["cache_invalidation_reason"] = "basis_or_coordinate_identity"
                xb, lam, rc, _ = state(c)
                primal_feasible = np.min(xb, initial=0) >= -options.primal_tolerance
                dual_feasible = np.max(rc, initial=0) <= options.dual_tolerance * (
                    1 + np.max(abs(c), initial=0)
                )
                if not primal_feasible and not dual_feasible:
                    raise ValueError("Warm basis is neither primal nor dual feasible.")
                mode = "dual" if dual_feasible and options.lp_method != "primal" else "primal"
                if options.lp_method == "primal" and not primal_feasible:
                    raise ValueError("Requested primal method requires a primal-feasible basis.")
                if mode == "dual":
                    pricing.reset(basis, "dual_start")
                counters.update(warm_starts=1, warm_mode=mode)
                out = run(c, mode)
                return finish(*out[:2], *out[2:5], ray=out[5], proof=out[0] == "infeasible")
            except (ValueError, KeyError, IndexError, np.linalg.LinAlgError) as exc:
                counters["fallback_reason"] = str(exc)
                increment(counters, "cold_fallbacks")
                a, c, keys, basis = saved
                factor = None
                pricing.fresh_phase(keys, basis, "cold_fallback")
        counters["cold_starts"] = 1
        if arts:
            increment(counters, "phase_one_starts")
            counters["phase_one_artificials"] = len(arts)
            phase = np.zeros(len(c))
            phase[list(arts)] = -1
            pricing.fresh_phase(keys, basis, "phase_one")
            out = run(phase, phase="phase_one")
            if out[0] != "optimal":
                return finish(*out[:2], *out[2:5], ray=out[5])
            xb, lam, rc = out[2:5]
            if phase[basis] @ xb < -options.primal_tolerance:
                return finish("infeasible", "phase_one_farkas", xb, lam, rc, proof=True)
            last_pivot = None
            counters.pop("last_pivot_trace", None)
            for art in sorted(arts):
                if perf_counter() >= deadline or iterations >= options.lp_iteration_limit:
                    return finish(
                        "limit",
                        "time_limit" if perf_counter() >= deadline else "lp_iteration_limit",
                    )
                if art not in basis:
                    continue
                retries = 0
                while True:
                    try:
                        xb, lam, rc, generation = state(phase)
                        tolerance = options.primal_tolerance * (1 + np.max(abs(xb), initial=0))
                        dual_tolerance = options.dual_tolerance * (
                            1 + abs(phase) + abs(a).T @ abs(lam)
                        )
                        if np.min(xb, initial=0) < -tolerance or np.any(rc > dual_tolerance):
                            raise np.linalg.LinAlgError(
                                "Phase-I cleanup lost a current optimal state."
                            )
                        if phase[basis] @ xb < -options.primal_tolerance:
                            return finish("infeasible", "phase_one_farkas", xb, lam, rc, proof=True)
                        position = basis.index(art)
                        unit = np.zeros(len(b))
                        unit[position] = 1
                        tableau = np.asarray(a.T @ basis_solve(unit, True, generation)).reshape(-1)
                        same_generation(generation)
                        choices = [
                            j
                            for j in range(len(c))
                            if j not in arts
                            and j not in basis
                            and abs(tableau[j]) > options.pivot_tolerance
                        ]
                        if choices:
                            pivot(min(choices, key=lambda j: keys[j]), position, generation)
                            increment(counters, "artificial_cleanup_pivots")
                        else:
                            increment(counters, "exact_dependency_checks")
                            if not _dependent_in_original_space(
                                norm, a, b, basis, row_keys, keys, position, options, deadline
                            ):
                                raise np.linalg.LinAlgError(
                                    "Unproved near-dependent row in artificial cleanup."
                                )
                            same_generation(generation)
                            support = a.indices[a.indptr[art] : a.indptr[art + 1]]
                            if len(support) != 1:
                                raise np.linalg.LinAlgError("Artificial identity column changed.")
                            physical = int(support[0])
                            keep_rows = [i for i in range(len(b)) if i != physical]
                            a, b = a[keep_rows, :].tocsc(), b[keep_rows]
                            row_map.pop(physical)
                            row_keys.pop(physical)
                            basis.pop(position)
                            increment(counters, "dependent_rows_removed")
                        break
                    except FactorRetry as exc:
                        retries += 1
                        increment(counters, "cleanup_generation_restarts")
                        if retries > 3:
                            raise np.linalg.LinAlgError(
                                "Cleanup factor-generation retry limit."
                            ) from exc
                factor = None
                pricing.fresh_phase(keys, basis, "artificial_cleanup")
            keep = [j for j in range(len(c)) if j not in arts]
            lookup = {j: i for i, j in enumerate(keep)}
            a, c = a[:, keep].tocsc(), c[keep]
            basis, keys = [lookup[j] for j in basis], tuple(keys[j] for j in keep)
            factor = None
        pricing.fresh_phase(keys, basis, "phase_two")
        out = run(c)
        return finish(*out[:2], *out[2:5], ray=out[5], proof=out[0] == "infeasible")
    except FactorDeadline:
        return finish("limit", "time_limit")
    except (FactorResourceError, MemoryError) as exc:
        counters["resource_message"] = str(exc)
        return finish("limit", "resource_limit")
    except (np.linalg.LinAlgError, FloatingPointError, OverflowError) as exc:
        return finish("numerical_failure", str(exc))
