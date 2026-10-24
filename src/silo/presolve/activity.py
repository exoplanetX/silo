"""Finite-pass activity propagation with reverse-adjoint dual provenance."""

from dataclasses import dataclass
from fractions import Fraction
from math import ceil, floor, isfinite
from time import perf_counter

import numpy as np

from silo.modeling.matrix_ops import row_support


@dataclass(frozen=True)
class BoundDerivation:
    variable: int
    side: str
    row: int
    row_side: str
    factor: float
    others: tuple[tuple[int, str, float], ...]


@dataclass
class ActivityResult:
    lower: np.ndarray
    upper: np.ndarray
    history: list[BoundDerivation]
    redundant: np.ndarray
    passes: int = 0
    conflict: bool = False
    integer_roundings: int = 0
    timed_out: bool = False

    def recover_multipliers(self, multipliers):
        yl, yu, zl, zu = [x.copy() for x in multipliers]
        for entry in reversed(self.history):
            target = zl if entry.side == "lower" else zu
            mu = target[entry.variable]
            target[entry.variable] = 0.0
            (yl if entry.row_side == "lower" else yu)[entry.row] += mu * entry.factor
            for j, side, weight in entry.others:
                (zl if side == "lower" else zu)[j] += mu * weight
        return yl, yu, zl, zu


def propagate(
    data, lower=None, upper=None, enabled=True, integral=False, max_passes=8, deadline=float("inf")
):
    lo = data.lower.copy() if lower is None else lower.copy()
    hi = data.upper.copy() if upper is None else upper.copy()
    result = ActivityResult(lo, hi, [], np.zeros(len(data.row_names), dtype=bool))
    if not enabled:
        return result
    for pass_id in range(max_passes):
        changed = False
        for i in range(len(data.row_names)):
            if perf_counter() >= deadline:
                result.timed_out = True
                return result
            indices, coefficients = row_support(data.a, i)
            for side, bound, sign in (
                ("upper", data.row_upper[i], 1),
                ("lower", data.row_lower[i], -1),
            ):
                if not isfinite(bound):
                    continue
                # The bound inferred for j is opposite to the bound used by its
                # own minimum contribution. Consequently these contributions
                # stay current throughout this row-side's sequential updates.
                coeff = sign * coefficients
                exact_coeff = [Fraction(float(value)) for value in coeff]
                contributions, source_sides = [], []
                minimum, unbounded = Fraction(0), 0
                for j, a in zip(indices, exact_coeff, strict=True):
                    if perf_counter() >= deadline:
                        result.timed_out = True
                        return result
                    value, bside = (lo[j], "lower") if a > 0 else (hi[j], "upper")
                    term = a * Fraction(float(value)) if isfinite(value) else None
                    contributions.append(term)
                    source_sides.append(bside)
                    if term is None:
                        unbounded += 1
                    else:
                        minimum += term
                for position, j in enumerate(indices):
                    if perf_counter() >= deadline:
                        result.timed_out = True
                        return result
                    term = contributions[position]
                    if unbounded - (term is None):
                        continue
                    other_minimum = minimum - (term if term is not None else 0)
                    exact = (sign * Fraction(float(bound)) - other_minimum) / exact_coeff[position]
                    target_side = "upper" if coeff[position] > 0 else "lower"
                    if integral and data.integer[j]:
                        rounded = floor(exact) if target_side == "upper" else ceil(exact)
                        result.integer_roundings += rounded != exact
                        exact = Fraction(rounded)
                    try:
                        new = float(exact)
                    except OverflowError:
                        continue
                    if not isfinite(new):
                        continue
                    # Round the inferred side OUTWARD. An inward float rounding
                    # would silently exclude exact feasible points or integers.
                    if target_side == "upper" and Fraction(new) < exact:
                        new = np.nextafter(new, np.inf)
                    elif target_side == "lower" and Fraction(new) > exact:
                        new = np.nextafter(new, -np.inf)
                    old = hi[j] if target_side == "upper" else lo[j]
                    better = new < old if target_side == "upper" else new > old
                    if better and (not isfinite(old) or abs(new - old) > 1e-10 * (1 + abs(new))):
                        (hi if target_side == "upper" else lo)[j] = new
                        result.history.append(
                            BoundDerivation(
                                int(j),
                                target_side,
                                i,
                                side,
                                1 / abs(coeff[position]),
                                tuple(
                                    (int(k), source_sides[p], abs(coeff[p] / coeff[position]))
                                    for p, k in enumerate(indices)
                                    if k != j
                                ),
                            )
                        )
                        changed = True
                    if lo[j] > hi[j] + 1e-9 * (1 + abs(new)):
                        result.conflict = True
                        # A conflict is not itself an original-space LP witness.
                        return result
        result.passes = pass_id + 1
        if not changed:
            break
    for i in range(len(data.row_names)):
        if perf_counter() >= deadline:
            result.timed_out = True
            return result
        minimum, maximum = Fraction(0), Fraction(0)
        indices, coefficients = row_support(data.a, i)
        for j, coefficient in zip(indices, coefficients, strict=True):
            if perf_counter() >= deadline:
                result.timed_out = True
                return result
            small, large = (lo[j], hi[j]) if coefficient > 0 else (hi[j], lo[j])
            minimum += (
                Fraction(float(coefficient)) * Fraction(float(small))
                if isfinite(small)
                else -float("inf")
            )
            maximum += (
                Fraction(float(coefficient)) * Fraction(float(large))
                if isfinite(large)
                else float("inf")
            )
        # Exact comparison keeps dropping conservative, without tolerance enlargement.
        result.redundant[i] = minimum >= data.row_lower[i] and maximum <= data.row_upper[i]
    return result
