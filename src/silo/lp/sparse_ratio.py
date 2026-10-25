"""Bounded candidate ordering for SILO's unchanged primal feasibility gate.

The common window includes every positive blocker. It proposes leaving rows;
actual new coordinates and a private full factor state still decide acceptance.
"""

from dataclasses import dataclass
from math import isfinite

import numpy as np

ROUNDOFF_WINDOW = 64.0 * np.finfo(np.float64).eps
PRIMAL_POLICY = (
    "silo-guarded-two-pass-row-window-v2",
    2,
    ROUNDOFF_WINDOW,
    "shared-actual-start-credit",
    "original-entering",
)
FULL_TRIAL_LIMIT = 2


@dataclass(frozen=True)
class RatioOrder:
    positive: tuple[int, ...]
    rows: tuple[int, ...]
    window: float
    allowance: float
    strict_minimum: float


def leaving_order(xb, direction, basic_keys, primal_tolerance, pivot_tolerance, safe_pivot):
    """Return deterministic stable rows inside a current-scale Harris window.

    No positive direction entry is dropped from the first pass, including a
    subnormal or unsafe pivot. A +inf ratio is nonbinding; it is not a ray.
    The caller must use actual rho, predict every coordinate, and verify B'.
    """
    if xb.ndim != 1 or direction.shape != xb.shape or len(basic_keys) != len(xb):
        raise ValueError("Invalid primal ratio dimensions.")
    if not np.isfinite(xb).all() or not np.isfinite(direction).all():
        raise np.linalg.LinAlgError("Nonfinite primal ratio state or direction.")
    size = float(np.max(abs(xb), initial=0))
    with np.errstate(over="ignore", invalid="ignore"):
        allowance = float(np.float64(primal_tolerance) * (1 + np.float64(size)))
    if not isfinite(allowance) or allowance < 0:
        raise np.linalg.LinAlgError("Nonfinite primal ratio allowance.")
    if np.min(xb, initial=0) < -allowance:
        raise np.linalg.LinAlgError("Primal ratio requires the current feasible state.")
    positive = np.flatnonzero(direction > 0)
    if not len(positive):
        return RatioOrder((), (), float("inf"), allowance, float("inf"))
    # Existing tolerated negative coordinates retain their deficit, but an
    # unrelated large basic value cannot enlarge a nonnegative row's leeway.
    # Compute the equivalent nonnegative headroom rather than cancelling a
    # negative coordinate against its deficit or overflowing x_i+delta_i.
    x, d = xb[positive], direction[positive]
    negative = x < 0
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        local = ROUNDOFF_WINDOW * (1 + abs(x))
        headroom = allowance + x[negative]
        if np.any(headroom < 0) or not np.isfinite(local).all():
            raise np.linalg.LinAlgError("Invalid row-level ratio headroom.")
        relaxed = np.empty(len(positive))
        relaxed[negative] = np.minimum(local[negative], headroom) / d[negative]
        relaxed[~negative] = x[~negative] / d[~negative] + (
            np.minimum(allowance, local[~negative]) / d[~negative]
        )
        selection = np.maximum(x, 0) / d
    if np.isnan(relaxed).any() or np.any(relaxed < 0) or np.isnan(selection).any():
        raise np.linalg.LinAlgError("Invalid positive-blocker ratio.")
    window = max(0.0, float(np.min(relaxed)))
    rows = [
        int(i)
        for i, ratio in zip(positive, selection, strict=True)
        if ratio <= window and safe_pivot(direction, int(i), pivot_tolerance)
    ]
    rows.sort(key=lambda i: (-float(abs(direction[i])), basic_keys[i], i))
    return RatioOrder(
        tuple(map(int, positive)), tuple(rows), window, allowance, float(np.min(selection))
    )
