"""Toy finite-scenario deterministic-equivalent example.

This example demonstrates the conservative Phase 8 stochastic transformation boundary.
It builds a tiny continuous LP, applies scenario objective/RHS overrides, and inspects
the transformed ordinary SILO model. It does not call an LP or MIP solver.
"""

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.deterministic_equivalent import (
    DeterministicEquivalentResult,
    build_deterministic_equivalent,
)
from silo.uncertainty.scenario import Scenario
from silo.uncertainty.stochastic_model import StochasticModel


def build_base_model() -> Model:
    return Model(
        name="toy_stochastic_lp",
        variables=[Variable("x"), Variable("y")],
        constraints=[
            Constraint(
                name="capacity",
                coefficients={"x": 1.0},
                sense=ConstraintSense.LE,
                rhs=8.0,
            ),
            Constraint(
                name="demand",
                coefficients={"x": 1.0, "y": 1.0},
                sense=ConstraintSense.LE,
                rhs=10.0,
            ),
        ],
        objective=Objective({"x": 1.0, "y": 1.0}),
    )


def build_stochastic_model() -> StochasticModel:
    return StochasticModel(
        base_model=build_base_model(),
        scenarios=(
            Scenario(
                "high",
                probability=0.6,
                objective_coefficients={"x": 3.0, "y": 5.0},
                rhs_values={"demand": 12.0},
            ),
            Scenario(
                "low",
                probability=0.4,
                objective_coefficients={"x": 1.0, "y": 2.0},
                rhs_values={"demand": 9.0},
            ),
        ),
        scenario_dependent_constraints=("demand",),
    )


def main() -> None:
    result = build_deterministic_equivalent(build_stochastic_model())
    if not isinstance(result, DeterministicEquivalentResult):
        raise TypeError("expected a deterministic-equivalent result")

    constraint_names = ",".join(constraint.name for constraint in result.model.constraints)
    objective_terms = ",".join(
        f"{name}={coefficient:g}"
        for name, coefficient in sorted(result.model.objective.coefficients.items())
    )
    diagnostics = result.diagnostics

    print(
        f"toy_stochastic_de model={result.model.name} scenarios="
        f"{','.join(diagnostics.scenario_ids)} generated_constraints="
        f"{diagnostics.generated_constraints}"
    )
    print(f"constraints={constraint_names}")
    print(f"objective={objective_terms}")
    print(
        f"diagnostics variables={diagnostics.generated_variables} "
        f"nonanticipativity={diagnostics.nonanticipativity_constraints}"
    )


if __name__ == "__main__":
    main()
