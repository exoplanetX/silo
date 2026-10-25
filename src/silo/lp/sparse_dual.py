"""Original-space primal blockers at a potential sparse dual-simplex exit."""

from dataclasses import dataclass
from math import isfinite

import numpy as np

DUAL_EXIT_POLICY = "silo-mapped-component-dual-exit-v1"


@dataclass(frozen=True)
class MappedBlockers:
    rows: tuple[int, ...]
    primal_feasible: bool
    violations: int
    maximum_scaled_violation: float


def mapped_blockers(norm, matrix, rhs, basis, row_keys, keys, xb, tolerance):
    """Observe the current point without another linear solve or any dense matrix.

    The caller keeps its existing global gate. Only a negative basic coordinate
    with an actual mapped bound/side violation can request another dual pivot.
    A primal failure with no such coordinate must remain numerical failure.
    """
    data = norm.data
    full = np.zeros(matrix.shape[1])
    full[basis] = xb
    point = np.array(norm.offset, dtype=float, copy=True)
    origins = norm.column_origins
    np.add.at(
        point,
        [i for i, _ in origins],
        np.array([direction for _, direction in origins]) * norm.col_scale * full[: len(origins)],
    )
    activity = np.asarray(data.a @ point).reshape(-1)
    row_base = 1 + np.asarray(abs(data.a) @ abs(point)).reshape(-1)
    if not all(np.isfinite(v).all() for v in (full, point, activity, row_base)):
        raise np.linalg.LinAlgError("Nonfinite original-space dual-exit point.")
    violations, maximum = 0, 0.0
    for values, lower, upper, base in (
        (point, data.lower, data.upper, 1 + abs(point)),
        (activity, data.row_lower, data.row_upper, row_base),
    ):
        for bound, sign in ((lower, -1), (upper, 1)):
            finite = np.isfinite(bound)
            denominator = base[finite] + abs(bound[finite])
            if not np.isfinite(denominator).all():
                raise np.linalg.LinAlgError("Nonfinite mapped primal allowance.")
            excess = sign * (values[finite] - bound[finite]) / denominator
            violations += int(np.count_nonzero(excess > tolerance))
            maximum = max(maximum, float(np.max(excess, initial=0)))

    residual = rhs - matrix @ full
    if not np.isfinite(residual).all():
        raise np.linalg.LinAlgError("Nonfinite mapped standard-form residual.")
    names = {name: i for i, name in enumerate(data.names)}
    original_rows = {name: i for i, name in enumerate(data.row_names)}
    normalized_rows = {key: i for i, key in enumerate(norm.row_keys)}
    standard_rows = {key: i for i, key in enumerate(row_keys)}
    candidates = []
    for position, column in enumerate(basis):
        if xb[position] >= 0:
            continue
        key = keys[column]
        if key[0] == "variable":
            original = names[key[1]]
            bound = data.lower[original] if key[2] == 1 else data.upper[original]
            if not isfinite(bound):  # A free split has no original finite bound.
                continue
            scale = float(norm.col_scale[column])
            if not isfinite(scale) or scale <= 0:
                raise np.linalg.LinAlgError("Invalid mapped variable scale.")
            difference = key[2] * (bound - point[original])
            allowance = tolerance * (1 + abs(point[original]) + abs(bound)) / scale
            if difference > 0 and difference / scale > allowance:
                candidates.append(position)
        elif key[0] == "slack":
            row_key = key[1]
            physical, normalized = standard_rows[row_key], normalized_rows[row_key]
            scale = float(norm.row_scale[normalized])
            sigma = float(matrix[physical, column])
            if not isfinite(scale) or scale <= 0 or sigma not in (-1, 1):
                raise np.linalg.LinAlgError("Invalid mapped slack scale or sign.")
            difference = (-xb[position] - sigma * residual[physical]) / scale
            if row_key[0] == "bound":
                original = names[row_key[1]]
                bound = data.upper[original]
                if not isfinite(bound):
                    continue
                denominator = 1 + abs(point[original]) + abs(bound)
            else:
                original = original_rows[row_key[1]]
                bound = (
                    data.row_upper[original]
                    if norm.senses[normalized] == "<="
                    else data.row_lower[original]
                )
                if not isfinite(bound):
                    raise np.linalg.LinAlgError("Mapped slack has no original finite side.")
                denominator = row_base[original] + abs(bound)
            if not isfinite(difference) or not isfinite(denominator):
                raise np.linalg.LinAlgError("Nonfinite mapped slack violation.")
            if difference > tolerance * denominator:
                candidates.append(position)
    return MappedBlockers(tuple(candidates), violations == 0, violations, maximum)
