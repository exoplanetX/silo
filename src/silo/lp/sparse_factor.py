"""Sparse basis linear equations with a bounded product-form eta chain.

SuperLU solves linear equations only. All pivoting decisions belong to SILO.
The factor owns its current basis; callers receive immutable identities/copies.
"""

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.sparse import csc_matrix, hstack
from scipy.sparse.linalg import splu

RESIDUAL_TOLERANCE = 1e-10
REFINEMENTS = 2
GROWTH_LIMIT = 1e8
FACTOR_POLICY = ("silo-sparse-lu-eta-v2", "COLAMD", RESIDUAL_TOLERANCE, REFINEMENTS, GROWTH_LIMIT)


@dataclass(frozen=True)
class SparseCoefficients:
    """Passive canonical CSC identity, containing no mutable numerical state."""

    shape: tuple[int, int]
    indptr: tuple[int, ...]
    indices: tuple[int, ...]
    values: tuple[float, ...]


def canonical(matrix):
    value = csc_matrix(matrix, dtype=np.float64, copy=True)
    value.sum_duplicates()
    value.eliminate_zeros()
    value.sort_indices()
    return value


def coefficients(matrix):
    value = canonical(matrix)
    return SparseCoefficients(
        tuple(value.shape),
        tuple(map(int, value.indptr)),
        tuple(map(int, value.indices)),
        tuple(map(float, value.data)),
    )


def same_matrix(left, right):
    """Compare actual canonical coefficients, not a mutable-container digest."""
    a, b = canonical(left), canonical(right)
    return (
        a.shape == b.shape
        and np.array_equal(a.indptr, b.indptr)
        and np.array_equal(a.indices, b.indices)
        and np.array_equal(a.data, b.data)
    )


def increment(counters, name, amount=1):
    counters[name] = counters.get(name, 0) + amount


def pivot_safe(direction, position, tolerance):
    """Shared acceptance predicate for a numerically usable basis pivot."""
    size = float(np.max(np.abs(direction), initial=0))
    return isfinite_array(direction) and abs(float(direction[position])) > tolerance * (1 + size)


def isfinite_array(value):
    return bool(np.isfinite(value).all())


class FactorDeadline(TimeoutError):
    pass


class FactorResourceError(MemoryError):
    pass


class FactorRetry(RuntimeError):
    """Current B was rebased; the caller must discard every uncommitted choice."""

    def __init__(self, reason, generation):
        super().__init__(reason)
        self.reason, self.generation = reason, generation


class SparseFactor:
    """Owned B=B0 E1...Ek; apply inverse etas in the mathematically required order."""

    def __init__(self, matrix, options, counters=None, deadline=float("inf")):
        self.options = options
        self.counters = {} if counters is None else counters
        self.deadline = deadline
        self.matrix = canonical(matrix)
        self.etas = []
        self.lu = None
        self.scope_calls = 0
        self.generation = 0
        self.last_refactor_reason = None
        self.refactor(self.matrix, "initial")

    @property
    def identity(self):
        return coefficients(self.matrix)

    def _deadline(self):
        if perf_counter() >= self.deadline:
            raise FactorDeadline("time_limit")

    def _resource(self, matrix=None):
        value = self.matrix if matrix is None else matrix
        if value.nnz > self.options.max_factor_nnz:
            raise FactorResourceError("Basis input exceeds max_factor_nnz.")
        if value.shape[0] and self.options.max_factor_nnz == 0:
            raise FactorResourceError("A nonempty factor requires max_factor_nnz > 0.")

    def _statistics(self):
        n = 0 if self.lu is None else self.lu.L.nnz + self.lu.U.nnz
        self.counters.update(
            basis_nnz=int(self.matrix.nnz),
            factor_nnz=int(n),
            factor_l_nnz=0 if self.lu is None else int(self.lu.L.nnz),
            factor_u_nnz=0 if self.lu is None else int(self.lu.U.nnz),
            factor_fill_ratio=n / max(1, self.matrix.nnz),
            eta_chain_length=len(self.etas),
            eta_storage_bytes=sum(d.nbytes + 8 for _, d in self.etas),
            factor_generation=self.generation,
        )
        self.counters["factor_nnz_peak"] = max(self.counters.get("factor_nnz_peak", 0), n)
        self.counters["eta_chain_peak"] = max(
            self.counters.get("eta_chain_peak", 0), len(self.etas)
        )
        self.counters["eta_storage_peak_bytes"] = max(
            self.counters.get("eta_storage_peak_bytes", 0), self.counters["eta_storage_bytes"]
        )

    def refactor(self, current_B=None, reason="structure"):
        self._deadline()
        matrix = canonical(self.matrix if current_B is None else current_B)
        if matrix.shape[0] != matrix.shape[1] or not np.isfinite(matrix.data).all():
            raise np.linalg.LinAlgError("Basis must be finite and square.")
        self._resource(matrix)
        if matrix.shape[0]:
            increment(self.counters, "base_factorizations")
            increment(self.counters, "factorizations")
        if reason != "initial" and matrix.shape[0]:
            increment(self.counters, "refactorizations")
            reasons = self.counters.setdefault("refactorizations_by_reason", {})
            increment(reasons, reason)
        try:
            lu = splu(matrix, permc_spec="COLAMD") if matrix.shape[0] else None
        except RuntimeError as exc:
            raise np.linalg.LinAlgError(str(exc)) from exc
        self._deadline()
        if lu is not None and lu.L.nnz + lu.U.nnz > self.options.max_factor_nnz:
            self.counters["rejected_factor_nnz"] = int(lu.L.nnz + lu.U.nnz)
            raise FactorResourceError("Sparse LU fill exceeds max_factor_nnz.")
        self.matrix, self.lu, self.etas, self.scope_calls = matrix, lu, [], 0
        self.generation += 1
        self.last_refactor_reason = reason
        self._statistics()

    def configure(self, options, counters, deadline):
        """Bind a fresh public solve; resource tightening precedes cache reuse."""
        previous = self.options
        self.options, self.counters, self.deadline, self.scope_calls = (
            options,
            counters,
            deadline,
            0,
        )
        self._deadline()
        self._resource()
        if self.lu is not None and self.lu.L.nnz + self.lu.U.nnz > options.max_factor_nnz:
            raise FactorResourceError("Retained sparse LU exceeds tightened max_factor_nnz.")
        rebuilt = False
        if options.pivot_tolerance != previous.pivot_tolerance:
            self.refactor(reason="pivot_policy")
            rebuilt = True
        elif len(self.etas) > options.max_factor_updates:
            self.refactor(reason="update_policy")
            rebuilt = True
        self._statistics()
        return rebuilt

    def _raw(self, rhs, transpose=False):
        self._deadline()
        increment(self.counters, "triangular_solves")
        if self.scope_calls:
            increment(self.counters, "within_solve_reuses")
            increment(self.counters, "factor_reuses")
        self.scope_calls += 1
        work = np.array(rhs, dtype=float, copy=True)
        if transpose:
            for position, direction in reversed(self.etas):
                pivot = direction[position]
                # E^-T changes only coordinate r. Keep the original r value
                # while evaluating the dot product, for vectors and multiple RHS.
                work[position] = (
                    work[position] - direction @ work + pivot * work[position]
                ) / pivot
            value = work if self.lu is None else self.lu.solve(work, trans="T")
        else:
            value = work if self.lu is None else self.lu.solve(work)
            for position, direction in self.etas:
                pivot_value = value[position].copy() / direction[position]
                value -= (
                    direction * pivot_value
                    if value.ndim == 1
                    else direction[:, None] * pivot_value[None, :]
                )
                value[position] = pivot_value
        self._deadline()
        return value

    def _residual(self, rhs, solution, transpose):
        matrix = self.matrix.T if transpose else self.matrix
        residual = rhs - matrix @ solution

        def norm(value):
            return float(np.max(np.abs(value), initial=0))

        bound = RESIDUAL_TOLERANCE * (1 + norm(rhs) + norm(abs(matrix) @ abs(solution)))
        good = bool(
            np.isfinite(solution).all() and np.isfinite(residual).all() and norm(residual) <= bound
        )
        increment(self.counters, "residual_checks")
        self.counters["maximum_basis_residual"] = max(
            self.counters.get("maximum_basis_residual", 0.0), norm(residual)
        )
        return good, residual

    def solve(self, rhs, transpose=False):
        rhs = np.asarray(rhs, dtype=float)
        if rhs.ndim not in (1, 2) or rhs.shape[0] != self.matrix.shape[0]:
            raise ValueError("Basis RHS has an incompatible shape.")
        value = self._raw(rhs, transpose)
        for attempt in range(REFINEMENTS + 1):
            valid, residual = self._residual(rhs, value, transpose)
            if valid:
                return value
            if attempt < REFINEMENTS:
                increment(self.counters, "refinement_steps")
                value += self._raw(residual, transpose)
        # Exactly one rebuild using the actual CURRENT B, never the old base.
        self.refactor(reason="residual")
        value = self._raw(rhs, transpose)
        if not self._residual(rhs, value, transpose)[0]:
            raise np.linalg.LinAlgError("Current-basis residual failed after recovery.")
        return value

    def solve_B(self, rhs):
        return self.solve(rhs)

    def solve_BT(self, rhs):
        return self.solve(rhs, transpose=True)

    def replace_column(self, position, column, direction=None, *, expected_generation=None):
        """Commit a verified same-size replacement, then eta or a real rebuild.

        Return whether a base rebuild occurred, so pricing can reset its frame.
        Recovery of OLD B returns an uncommitted FactorRetry: a newly computed
        direction must never inherit the caller's previously chosen leaving row.
        Planned chain-limit and next-B rebuilds are atomic commits of the
        already verified direction, with no intervening recomputation.
        All accepted replacements, including safety/periodic rebuilds, enter the
        denominator. A rejected pivot never changes the owned current matrix.
        """
        self._deadline()
        generation = self.generation if expected_generation is None else expected_generation
        if generation != self.generation:
            raise FactorRetry("stale_commit_generation", self.generation)
        n = self.matrix.shape[0]
        column = np.asarray(column, dtype=float)
        if column.shape != (n,) or not 0 <= position < n or not np.isfinite(column).all():
            raise ValueError("Invalid basis-column replacement.")
        before = self.counters.get("base_factorizations", 0)
        direction = self.solve_B(column) if direction is None else np.array(direction, copy=True)
        if self.generation != generation:
            raise FactorRetry("direction_solve_rebased", self.generation)
        if direction.shape != (n,) or not self._residual(column, direction, False)[0]:
            self.refactor(reason="direction_residual")
            raise FactorRetry("direction_residual", self.generation)
        size = float(np.max(np.abs(direction), initial=0))
        pivot = float(direction[position])
        if not pivot_safe(direction, position, self.options.pivot_tolerance):
            self.refactor(reason="pivot")
            raise FactorRetry("unsafe_pivot", self.generation)
        indices = np.flatnonzero(column)
        sparse_column = csc_matrix(
            (column[indices], (indices, np.zeros(len(indices), dtype=int))), shape=(n, 1)
        )
        next_basis = hstack(
            (self.matrix[:, :position], sparse_column, self.matrix[:, position + 1 :]), format="csc"
        )
        self._resource(next_basis)
        if self.options.max_factor_updates == 0:
            self.refactor(next_basis, "updates_disabled")
        elif max(size, 1 / abs(pivot)) > GROWTH_LIMIT:
            self.refactor(next_basis, "growth")
        else:
            if len(self.etas) >= self.options.max_factor_updates:
                self.refactor(reason="chain_limit")
            self.matrix = next_basis
            self.etas.append((position, direction.copy()))
            increment(self.counters, "eta_updates")
            self._statistics()
        increment(self.counters, "basis_replacements")
        return self.counters.get("base_factorizations", 0) != before
