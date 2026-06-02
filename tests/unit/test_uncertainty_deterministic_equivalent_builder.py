from pathlib import Path

import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.deterministic_equivalent import (
    DeterministicEquivalentResult,
    build_deterministic_equivalent,
)
from silo.uncertainty.naming import scenario_constraint_name
from silo.uncertainty.scenario import Scenario
from silo.uncertainty.stochastic_model import StochasticModel


def _base_model() -> Model:
    return Model(
        name="tiny_stochastic_lp",
        variables=[Variable("x"), Variable("y")],
        constraints=[
            Constraint("capacity", {"x": 1.0}, rhs=8.0),
            Constraint("demand", {"x": 1.0, "y": 1.0}, rhs=10.0),
        ],
        objective=Objective({"x": 1.0, "y": 1.0}),
    )


def _tiny_stochastic_model() -> StochasticModel:
    return StochasticModel(
        base_model=_base_model(),
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


def test_tiny_builder_returns_result_model_and_diagnostics() -> None:
    stochastic_model = _tiny_stochastic_model()

    result = build_deterministic_equivalent(stochastic_model)

    assert isinstance(result, DeterministicEquivalentResult)
    assert result.model is not stochastic_model.base_model
    assert result.model.name == "tiny_stochastic_lp_deterministic_equivalent"
    assert [variable.name for variable in result.model.variables] == ["x", "y"]
    assert [constraint.name for constraint in result.model.constraints] == [
        "capacity",
        scenario_constraint_name("demand", "high"),
        scenario_constraint_name("demand", "low"),
    ]
    assert result.diagnostics.scenario_ids == ("high", "low")
    assert result.diagnostics.generated_variables == 0
    assert result.diagnostics.generated_constraints == 2
    assert result.diagnostics.nonanticipativity_constraints == 0
    assert result.diagnostics.probability_total == pytest.approx(1.0)
    assert result.diagnostics.metadata == (("builder", "tiny_objective_rhs"),)


def test_tiny_builder_applies_rhs_overrides_to_generated_constraints() -> None:
    result = build_deterministic_equivalent(_tiny_stochastic_model())
    constraints_by_name = {constraint.name: constraint for constraint in result.model.constraints}

    assert constraints_by_name["capacity"].rhs == 8.0
    assert constraints_by_name[scenario_constraint_name("demand", "high")].rhs == 12.0
    assert constraints_by_name[scenario_constraint_name("demand", "low")].rhs == 9.0
    assert constraints_by_name[scenario_constraint_name("demand", "high")].coefficients == {
        "x": 1.0,
        "y": 1.0,
    }


def test_tiny_builder_uses_expected_value_objective_coefficients() -> None:
    result = build_deterministic_equivalent(_tiny_stochastic_model())

    assert result.model.objective.coefficients["x"] == pytest.approx(2.2)
    assert result.model.objective.coefficients["y"] == pytest.approx(3.8)
    assert result.model.objective.sense == _base_model().objective.sense
    assert result.model.objective.constant == 0.0


def test_tiny_builder_does_not_mutate_base_model_or_scenarios() -> None:
    stochastic_model = _tiny_stochastic_model()
    base_model = stochastic_model.base_model
    base_constraint_coefficients = [
        dict(constraint.coefficients) for constraint in base_model.constraints
    ]
    scenario_rhs_values = [
        tuple(scenario.rhs_values) for scenario in stochastic_model.scenarios.scenarios
    ]

    result = build_deterministic_equivalent(stochastic_model)
    result.model.constraints[0].coefficients["x"] = 99.0

    assert [variable.name for variable in base_model.variables] == ["x", "y"]
    assert [constraint.name for constraint in base_model.constraints] == [
        "capacity",
        "demand",
    ]
    assert [dict(constraint.coefficients) for constraint in base_model.constraints] == (
        base_constraint_coefficients
    )
    assert [tuple(scenario.rhs_values) for scenario in stochastic_model.scenarios.scenarios] == (
        scenario_rhs_values
    )


@pytest.mark.parametrize("variable_type", [VariableType.INTEGER, VariableType.BINARY])
def test_tiny_builder_rejects_noncontinuous_variables(variable_type: VariableType) -> None:
    bounds = Bounds(0.0, 1.0) if variable_type == VariableType.BINARY else Bounds()
    base_model = Model(
        variables=[Variable("x", bounds=bounds, var_type=variable_type)],
        constraints=[Constraint("demand", {"x": 1.0})],
        objective=Objective({"x": 1.0}),
    )
    stochastic_model = StochasticModel(
        base_model=base_model,
        scenarios=(Scenario("base", objective_coefficients={"x": 2.0}),),
    )

    with pytest.raises(ValueError, match="continuous LPs"):
        build_deterministic_equivalent(stochastic_model)


def test_tiny_builder_rejects_scenario_dependent_variables() -> None:
    stochastic_model = StochasticModel(
        base_model=_base_model(),
        scenarios=(Scenario("base"),),
        scenario_dependent_variables=("y",),
    )

    with pytest.raises(ValueError, match="scenario-dependent variables"):
        build_deterministic_equivalent(stochastic_model)


def test_tiny_builder_rejects_unknown_objective_override_variables() -> None:
    stochastic_model = StochasticModel(
        base_model=_base_model(),
        scenarios=(Scenario("base", objective_coefficients={"missing": 1.0}),),
    )

    with pytest.raises(ValueError, match="Unknown objective override variable"):
        build_deterministic_equivalent(stochastic_model)


def test_tiny_builder_rejects_unknown_rhs_override_constraints() -> None:
    stochastic_model = StochasticModel(
        base_model=_base_model(),
        scenarios=(Scenario("base", rhs_values={"missing": 1.0}),),
        scenario_dependent_constraints=("demand",),
    )

    with pytest.raises(ValueError, match="Unknown RHS override constraint"):
        build_deterministic_equivalent(stochastic_model)


def test_tiny_builder_rejects_undeclared_rhs_override_constraints() -> None:
    stochastic_model = StochasticModel(
        base_model=_base_model(),
        scenarios=(Scenario("base", rhs_values={"demand": 1.0}),),
    )

    with pytest.raises(ValueError, match="declared scenario-dependent constraints"):
        build_deterministic_equivalent(stochastic_model)


def test_tiny_builder_rejects_constraint_coefficient_overrides() -> None:
    stochastic_model = StochasticModel(
        base_model=_base_model(),
        scenarios=(
            Scenario(
                "base",
                constraint_coefficients={"demand": {"x": 2.0}},
            ),
        ),
        scenario_dependent_constraints=("demand",),
    )

    with pytest.raises(ValueError, match="constraint coefficient overrides"):
        build_deterministic_equivalent(stochastic_model)


def test_tiny_builder_rejects_generated_constraint_name_collisions() -> None:
    base_model = Model(
        variables=[Variable("x")],
        constraints=[
            Constraint("demand", {"x": 1.0}, rhs=1.0),
            Constraint(scenario_constraint_name("demand", "high"), {"x": 1.0}, rhs=2.0),
        ],
        objective=Objective({"x": 1.0}),
    )
    stochastic_model = StochasticModel(
        base_model=base_model,
        scenarios=(Scenario("high", rhs_values={"demand": 3.0}),),
        scenario_dependent_constraints=("demand",),
    )

    with pytest.raises(ValueError, match="collides"):
        build_deterministic_equivalent(stochastic_model)


def test_noop_builder_placeholder_behavior_is_preserved_for_empty_wrappers() -> None:
    stochastic_model = StochasticModel(
        base_model=_base_model(),
        scenarios=(Scenario("base"),),
    )

    assert build_deterministic_equivalent(stochastic_model) is stochastic_model.base_model


def test_builder_module_has_no_solver_cli_or_schema_integration() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (
        repo_root / "src" / "silo" / "uncertainty" / "deterministic_equivalent.py"
    ).read_text(encoding="utf-8")
    forbidden_patterns = (
        "silo.lp",
        "silo.mip",
        "silo.presolve",
        "silo.cuts",
        "silo.decomposition",
        "silo.interfaces",
        "build_parser",
        "Solution(",
        "solve(",
        "LPSolver",
        "BranchAndBoundSolver",
        "Presolver",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source
