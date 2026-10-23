"""Finite-pass activity propagation with reverse-adjoint dual provenance."""

from dataclasses import dataclass
from fractions import Fraction
from math import ceil, floor, isfinite

import numpy as np


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


def propagate(data, lower=None, upper=None, enabled=True, integral=False, max_passes=8):
    lo = data.lower.copy() if lower is None else lower.copy()
    hi = data.upper.copy() if upper is None else upper.copy()
    result = ActivityResult(lo, hi, [], np.zeros(len(data.row_names), dtype=bool))
    if not enabled:
        return result
    for pass_id in range(max_passes):
        changed = False
        for i, row in enumerate(data.a):
            indices = np.flatnonzero(row)
            for side, bound, sign in (
                ("upper", data.row_upper[i], 1),
                ("lower", data.row_lower[i], -1),
            ):
                if not isfinite(bound):
                    continue
                coeff = sign * row
                for j in indices:
                    minimum, others, finite = Fraction(0), [], True
                    for k in indices:
                        if k == j:
                            continue
                        value, bside = (lo[k], "lower") if coeff[k] > 0 else (hi[k], "upper")
                        if not isfinite(value):
                            finite = False
                            break
                        minimum += Fraction(float(coeff[k])) * Fraction(float(value))
                        others.append((int(k), bside, abs(coeff[k] / coeff[j])))
                    if not finite:
                        continue
                    exact = (sign * Fraction(float(bound)) - minimum) / Fraction(float(coeff[j]))
                    target_side = "upper" if coeff[j] > 0 else "lower"
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
                                int(j), target_side, i, side, 1 / abs(coeff[j]), tuple(others)
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
    for i, row in enumerate(data.a):
        minimum, maximum = Fraction(0), Fraction(0)
        for j in np.flatnonzero(row):
            small, large = (lo[j], hi[j]) if row[j] > 0 else (hi[j], lo[j])
            minimum += (
                Fraction(float(row[j])) * Fraction(float(small))
                if isfinite(small)
                else -float("inf")
            )
            maximum += (
                Fraction(float(row[j])) * Fraction(float(large))
                if isfinite(large)
                else float("inf")
            )
        # Exact comparison keeps dropping conservative, without tolerance enlargement.
        result.redundant[i] = minimum >= data.row_lower[i] and maximum <= data.row_upper[i]
    return result
