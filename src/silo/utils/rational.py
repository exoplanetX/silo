"""Bounded exact sparse-row elimination for proof objects, never an LP solver."""

from contextlib import contextmanager
from fractions import Fraction
from math import inf
from time import perf_counter


class ProofLimitError(ValueError):
    """Bounded exact verification could not finish; this is not bad model data."""


class ProofBudget:
    def __init__(self, operations=2_000_000, deadline=inf, clock=None):
        self.remaining = operations
        self.deadline = deadline
        self.clock = perf_counter if clock is None else clock
        self.live_cells = 0
        self.peak_cells = 0

    @contextmanager
    def workspace(self, cells):
        """Reserve simultaneous rational slots before conversion/allocation.

        An outer reservation remains live throughout any nested proof. The
        ceiling is a fixed policy, independent of basis/operation/bit budgets.
        """
        if type(cells) is not int or cells < 0:
            raise ValueError("Exact proof workspace must be a nonnegative integer.")
        self.charge()
        if self.live_cells + cells > 65536:
            raise ProofLimitError("Exact proof workspace exceeds 65536 rational cells.")
        self.live_cells += cells
        self.peak_cells = max(self.peak_cells, self.live_cells)
        try:
            yield
        finally:
            self.live_cells -= cells

    def charge(self, count=1):
        self.remaining -= count
        if self.remaining < 0 or self.clock() >= self.deadline:
            raise ProofLimitError("Exact proof operation/time budget exhausted.")

    def guard(self, value):
        self.charge()
        if value.numerator.bit_length() + value.denominator.bit_length() > 4096:
            raise ProofLimitError("Exact proof coefficient budget.")
        return value


def exact_solve(matrix, rhs, operation_limit=2_000_000, deadline=inf, budget=None):
    budget = ProofBudget(operation_limit, deadline) if budget is None else budget
    budget.charge()
    n = len(rhs)
    rows = [{j: Fraction(v) for j, v in enumerate(row) if v} for row in matrix]
    values = list(map(Fraction, rhs))
    for k in range(n):
        budget.charge()
        pivot = next((i for i in range(k, n) if rows[i].get(k, 0)), None)
        if pivot is None:
            raise ValueError("Exact basis is singular.")
        rows[k], rows[pivot] = rows[pivot], rows[k]
        values[k], values[pivot] = values[pivot], values[k]
        divisor = rows[k][k]
        rows[k] = {j: v / divisor for j, v in rows[k].items()}
        values[k] /= divisor
        for i in range(n):
            if i == k or not rows[i].get(k, 0):
                continue
            factor = rows[i][k]
            for j, value in rows[k].items():
                budget.charge()
                new = rows[i].get(j, 0) - factor * value
                if new.numerator.bit_length() + new.denominator.bit_length() > 4096:
                    raise ProofLimitError("Exact proof coefficient budget.")
                if new:
                    rows[i][j] = new
                else:
                    rows[i].pop(j, None)
            values[i] -= factor * values[k]
        if any(v.numerator.bit_length() + v.denominator.bit_length() > 4096 for v in values):
            raise ProofLimitError("Exact proof coefficient budget.")
    return values
