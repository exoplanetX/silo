"""Original-space KKT checks and exact rational LP witnesses."""

from fractions import Fraction
from math import isfinite, lcm

import numpy as np


def primal_check(data, point, tolerance=1e-7, integer=False, integrality_tolerance=None):
    x = np.asarray(point)
    if x.shape != data.c.shape or not np.isfinite(x).all():
        return False
    activity = data.a @ x
    scale = 1 + np.abs(data.a) @ np.abs(x)
    for values, lower, upper, base in (
        (x, data.lower, data.upper, 1 + np.abs(x)),
        (activity, data.row_lower, data.row_upper, scale),
    ):
        for bound, sign in ((lower, -1), (upper, 1)):
            finite = np.isfinite(bound)
            if np.any(
                sign * (values[finite] - bound[finite])
                > tolerance * (base[finite] + np.abs(bound[finite]))
            ):
                return False
    integer_tol = tolerance if integrality_tolerance is None else integrality_tolerance
    return not integer or np.all(np.abs(x[data.integer] - np.rint(x[data.integer])) <= integer_tol)


def check_kkt(
    data,
    x,
    multipliers,
    tolerance=1e-7,
    *,
    primal_tolerance=None,
    dual_tolerance=None,
    complementarity_tolerance=None,
    objective_tolerance=None,
):
    ptol = tolerance if primal_tolerance is None else primal_tolerance
    dtol = tolerance if dual_tolerance is None else dual_tolerance
    ctol = tolerance if complementarity_tolerance is None else complementarity_tolerance
    otol = tolerance if objective_tolerance is None else objective_tolerance
    yl, yu, zl, zu = multipliers
    report = {"valid": False, "primal_feasible": primal_check(data, x, ptol)}
    if not report["primal_feasible"] or not all(np.isfinite(v).all() for v in multipliers):
        return report
    stationarity = data.sign * data.c + data.a.T @ (yu - yl) - zl + zu
    scale = 1 + np.abs(data.c) + np.abs(data.a).T @ (np.abs(yl) + np.abs(yu)) + abs(zl) + abs(zu)
    valid = bool(np.all(np.abs(stationarity) <= dtol * scale))
    activity = data.a @ x
    dual = data.sign * data.constant
    max_complementarity = 0.0
    for value, bound, multiplier, sign in (
        (activity, data.row_lower, yl, 1),
        (activity, data.row_upper, yu, -1),
        (x, data.lower, zl, 1),
        (x, data.upper, zu, -1),
    ):
        finite = np.isfinite(bound)
        valid &= bool(np.all(multiplier >= -dtol * (1 + np.abs(multiplier))))
        valid &= bool(np.all(np.abs(multiplier[~finite]) <= dtol))
        product = multiplier[finite] * (value[finite] - bound[finite])
        valid &= bool(
            np.all(
                np.abs(product)
                <= ctol
                * (
                    1
                    + np.abs(multiplier[finite] * value[finite])
                    + np.abs(multiplier[finite] * bound[finite])
                )
            )
        )
        max_complementarity = max(max_complementarity, np.max(np.abs(product), initial=0))
        dual += sign * bound[finite] @ multiplier[finite]
    objective = data.sign * (data.constant + data.c @ x)
    valid &= isfinite(objective) and isfinite(dual)
    valid &= abs(objective - dual) <= otol * (1 + abs(objective) + abs(dual))
    report.update(
        valid=bool(valid),
        stationarity_residual=float(np.max(abs(stationarity), initial=0)),
        complementarity_residual=float(max_complementarity),
        primal_dual_residual=float(abs(objective - dual)),
        dual_objective=float(data.sign * dual),
    )
    return report


def _fraction(value):
    # Match the historical original-model checker: floats mean their exact
    # binary values, and coefficients are converted BEFORE arithmetic.
    return Fraction(float(value))


def _candidate(value):
    return _fraction(value).limit_denominator(100_000_000)


def exact_ray(data, point, ray, integer=False, proof_limit=1000000):
    """Rational reconstruction is a proposal; every original inequality is exact."""
    x, h = list(map(_candidate, point)), list(map(_candidate, ray))
    if integer:
        if any(x[j].denominator != 1 for j in np.flatnonzero(data.integer)):
            return None
        denominator = 1
        for j in np.flatnonzero(data.integer):
            denominator = lcm(denominator, h[j].denominator)
            if denominator > proof_limit:
                return None
        h = [v * denominator for v in h]
    if not any(h):
        return None
    for j in range(len(x)):
        if isfinite(data.lower[j]) and (x[j] < _fraction(data.lower[j]) or h[j] < 0):
            return None
        if isfinite(data.upper[j]) and (x[j] > _fraction(data.upper[j]) or h[j] > 0):
            return None
    for i, row in enumerate(data.a):
        value = sum(_fraction(a) * v for a, v in zip(row, x, strict=True))
        direction = sum(_fraction(a) * v for a, v in zip(row, h, strict=True))
        if isfinite(data.row_lower[i]) and (value < _fraction(data.row_lower[i]) or direction < 0):
            return None
        if isfinite(data.row_upper[i]) and (value > _fraction(data.row_upper[i]) or direction > 0):
            return None
    improvement = data.sign * sum(_fraction(c) * v for c, v in zip(data.c, h, strict=True))
    if improvement >= 0:
        return None
    return {
        "kind": "integer_point_ray" if integer else "point_ray",
        "exact": True,
        "point": dict(zip(data.names, map(str, x), strict=True)),
        "ray": dict(zip(data.names, map(str, h), strict=True)),
        "improvement": str(improvement),
    }


def exact_farkas(data, multipliers):
    yl, yu, zl, zu = [list(map(_candidate, side)) for side in multipliers]
    normal = [
        sum(_fraction(data.a[i, j]) * (yu[i] - yl[i]) for i in range(len(yl))) - zl[j] + zu[j]
        for j in range(len(zl))
    ]
    if any(normal) or any(v < 0 for side in (yl, yu, zl, zu) for v in side):
        return None
    contradiction = Fraction(0)
    for bounds, side, sign in (
        (data.row_lower, yl, 1),
        (data.row_upper, yu, -1),
        (data.lower, zl, 1),
        (data.upper, zu, -1),
    ):
        for bound, value in zip(bounds, side, strict=True):
            if isfinite(bound):
                contradiction += sign * _fraction(bound) * value
            elif value:
                return None
    if contradiction <= 0:
        return None
    return {
        "kind": "farkas",
        "exact": True,
        "contradiction": str(contradiction),
        "row_lower": list(map(str, yl)),
        "row_upper": list(map(str, yu)),
        "variable_lower": list(map(str, zl)),
        "variable_upper": list(map(str, zu)),
    }
