"""Toy interval-RHS robust counterpart example.

This example demonstrates the conservative Phase 8 robust transformation boundary. It
builds a tiny continuous LP, applies interval RHS uncertainty, and inspects the transformed
ordinary SILO model. It does not call an LP or MIP solver.
"""

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.robust_counterpart import (
    RobustCounterpartResult,
    build_robust_counterpart,
)
from silo.uncertainty.robust_model import RobustModel
from silo.uncertainty.uncertainty_set import RHS_TARGET, IntervalUncertainty, UncertaintySet


def build_base_model() -> Model:
    return Model(
        name="toy_robust_rhs_lp",
        variables=[Variable("x"), Variable("y")],
        constraints=[
            Constraint(
                name="capacity",
                coefficients={"x": 1.0, "y": 1.0},
                sense=ConstraintSense.LE,
                rhs=10.0,
            ),
            Constraint(
                name="demand",
                coefficients={"x": 1.0},
                sense=ConstraintSense.GE,
                rhs=3.0,
            ),
        ],
        objective=Objective({"x": 2.0, "y": 1.0}),
    )


def build_robust_model() -> RobustModel:
    return RobustModel(
        base_model=build_base_model(),
        uncertainty_set=UncertaintySet(
            "rhs_box",
            (
                IntervalUncertainty(
                    "capacity_rhs",
                    RHS_TARGET,
                    lower=7.0,
                    upper=12.0,
                    nominal=10.0,
                    constraint_name="capacity",
                ),
                IntervalUncertainty(
                    "demand_rhs",
                    RHS_TARGET,
                    lower=1.0,
                    upper=4.0,
                    nominal=3.0,
                    constraint_name="demand",
                ),
            ),
        ),
        assumptions=("independent RHS intervals",),
    )


def main() -> None:
    result = build_robust_counterpart(build_robust_model())
    if not isinstance(result, RobustCounterpartResult):
        raise TypeError("expected a robust-counterpart result")

    rhs_terms = ",".join(
        f"{constraint.name}={constraint.rhs:g}" for constraint in result.model.constraints
    )
    diagnostics = result.diagnostics

    print(
        f"toy_robust_rhs model={result.model.name} adjusted="
        f"{','.join(diagnostics.adjusted_constraints)} intervals="
        f"{','.join(diagnostics.interval_names)}"
    )
    print(f"rhs={rhs_terms}")
    print(
        f"diagnostics generated_constraints={diagnostics.generated_constraints} "
        f"convention={diagnostics.rhs_convention}"
    )


if __name__ == "__main__":
    main()
