"""Read-only exact checks of existing original-model unboundedness candidates.

Floats mean their actual binary values; integers retain their original value.
Every scalar is converted before arithmetic. No solving or candidate repair.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from math import inf
from numbers import Integral

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class LPUnboundednessCheck:
    passed: bool
    message: str


def check_lp_unboundedness(
    model: Model,
    point: Mapping[str, float],
    direction: Mapping[str, float],
) -> LPUnboundednessCheck:
    """Check x0+t*d for all t>=0 in the native MAX LP domain, without tolerance.

    The existing near-zero lower-bound domain check is retained, but point
    feasibility uses the actual bound. A rounded point (e.g. 1/3 for 3*x=1)
    can be rejected even when the LP is unbounded. Inputs are never modified.
    """
    try:
        model.validate()
    except (ValueError, TypeError, OverflowError) as exc:
        return LPUnboundednessCheck(False, f"Invalid model coordinates/domain: {exc}")
    if model.objective.sense != OptimizationSense.MAXIMIZE:
        return LPUnboundednessCheck(False, "Model domain requires maximization.")
    names = set(model.variable_names())
    if (not isinstance(point, Mapping) or not isinstance(direction, Mapping)
            or set(point) != names or set(direction) != names):
        return LPUnboundednessCheck(False, "Incomplete or unexpected point/direction coordinates.")
    try:
        x = {n: _fraction(point[n], f"point variable {n!r}") for n in names}
        d = {n: _fraction(direction[n], f"direction variable {n!r}") for n in names}
        _fraction(model.objective.constant, "objective constant")
        costs = {n: _fraction(c, f"objective variable {n!r}")
                 for n, c in model.objective.coefficients.items()}
        for variable in model.variables:
            name = variable.name
            lower = _fraction(variable.bounds.lower, f"lower bound {name!r}")
            if (variable.var_type != VariableType.CONTINUOUS
                    or abs(lower) > DEFAULT_TOLERANCE or variable.bounds.upper != inf):
                return LPUnboundednessCheck(False, f"Unsupported model domain at {name!r}.")
            if x[name] < lower:
                return LPUnboundednessCheck(False, f"Point violates lower bound at {name!r}.")
            if d[name] < 0:
                return LPUnboundednessCheck(False, f"Direction violates lower bound at {name!r}.")
        for row in model.constraints:
            if row.lower_bound is not None or row.upper_bound is not None:
                return LPUnboundednessCheck(False, "General rows require the unified checker.")
            rhs = _fraction(row.rhs, f"RHS row {row.name!r}")
            coefficients = {n: _fraction(a, f"coefficient row {row.name!r}, variable {n!r}")
                            for n, a in row.coefficients.items()}
            activity = sum((a * x[n] for n, a in coefficients.items()), Fraction(0))
            slope = sum((a * d[n] for n, a in coefficients.items()), Fraction(0))
            if not _satisfies(activity - rhs, row.sense):
                return LPUnboundednessCheck(False, f"Point violates original row {row.name!r}.")
            if not _satisfies(slope, row.sense):
                return LPUnboundednessCheck(False, f"Direction violates original row {row.name!r}.")
        improvement = sum((c * d[n] for n, c in costs.items()), Fraction(0))
    except _InvalidScalar as exc:
        return LPUnboundednessCheck(False, str(exc))
    if improvement <= 0:
        return LPUnboundednessCheck(
            False, "Direction has no strictly positive objective improvement.",
        )
    return LPUnboundednessCheck(
        True, "Original-model point and improving direction verified exactly.",
    )


class _InvalidScalar(ValueError):
    pass


def _fraction(value, context: str) -> Fraction:
    # Do not pass an integer through float on its way to Fraction.
    try:
        if isinstance(value, Integral):
            return Fraction(int(value))
        if isinstance(value, float | Fraction):
            return Fraction(value)
    except (ValueError, OverflowError) as exc:
        raise _InvalidScalar(f"Nonfinite {context}.") from exc
    raise _InvalidScalar(f"Nonnumeric {context}.")


def _satisfies(residual: Fraction, sense: ConstraintSense) -> bool:
    if sense == ConstraintSense.LE:
        return residual <= 0
    if sense == ConstraintSense.GE:
        return residual >= 0
    return residual == 0
