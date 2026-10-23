"""Finite-pass activity propagation with reverse-adjoint dual provenance."""

from dataclasses import dataclass
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
                    minimum, others, finite = 0.0, [], True
                    for k in indices:
                        if k == j:
                            continue
                        value, bside = (lo[k], "lower") if coeff[k] > 0 else (hi[k], "upper")
                        if not isfinite(value):
                            finite = False
                            break
                        minimum += coeff[k] * value
                        others.append((int(k), bside, abs(coeff[k] / coeff[j])))
                    if not finite:
                        continue
                    new = (sign * bound - minimum) / coeff[j]
                    if not isfinite(new):
                        continue
                    target_side = "upper" if coeff[j] > 0 else "lower"
                    if integral and data.integer[j]:
                        rounded = floor(new) if target_side == "upper" else ceil(new)
                        result.integer_roundings += rounded != new
                        new = rounded
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
        minimum, maximum = 0.0, 0.0
        for j in np.flatnonzero(row):
            minimum += row[j] * (lo[j] if row[j] > 0 else hi[j])
            maximum += row[j] * (hi[j] if row[j] > 0 else lo[j])
        # Exact comparison keeps dropping conservative, without tolerance enlargement.
        result.redundant[i] = minimum >= data.row_lower[i] and maximum <= data.row_upper[i]
    return result
