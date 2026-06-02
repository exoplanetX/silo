from dataclasses import FrozenInstanceError
from math import inf
from pathlib import Path

import pytest

from silo.core.constraint import Constraint
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.scenario import Scenario, ScenarioSet
from silo.uncertainty.stochastic_model import StochasticModel


def _base_model() -> Model:
    return Model(
        name="two_stage",
        variables=[Variable("x"), Variable("y")],
        constraints=[Constraint("demand", {"x": 1.0, "y": 1.0})],
        objective=Objective({"x": 1.0, "y": 2.0}),
    )


def test_stochastic_model_normalizes_records_and_copies_inputs() -> None:
    first_stage_variables = [" x "]
    scenario_dependent_variables = [" y "]
    scenario_dependent_constraints = [" demand "]
    metadata = {" z ": 2, "a": "alpha"}
    base_model = _base_model()

    stochastic_model = StochasticModel(
        base_model=base_model,
        scenarios=(Scenario("high", 0.3), Scenario("low", 0.7)),
        first_stage_variables=first_stage_variables,
        scenario_dependent_variables=scenario_dependent_variables,
        scenario_dependent_constraints=scenario_dependent_constraints,
        metadata=metadata,
        message="finite two-stage wrapper",
    )
    first_stage_variables.append("y")
    scenario_dependent_variables.append("x")
    scenario_dependent_constraints.append("other")
    metadata[" z "] = 99

    assert stochastic_model.base_model is base_model
    assert stochastic_model.scenario_ids == ("high", "low")
    assert stochastic_model.first_stage_variables == ("x",)
    assert stochastic_model.scenario_dependent_variables == ("y",)
    assert stochastic_model.scenario_dependent_constraints == ("demand",)
    assert stochastic_model.metadata == (("a", "alpha"), ("z", 2))
    assert stochastic_model.message == "finite two-stage wrapper"
    assert stochastic_model.variable_names == ("x", "y")
    assert stochastic_model.constraint_names == ("demand",)
    assert len(base_model.variables) == 2
    assert len(base_model.constraints) == 1


def test_stochastic_model_accepts_existing_scenario_set() -> None:
    scenario_set = ScenarioSet((Scenario("base"),))

    stochastic_model = StochasticModel(_base_model(), scenario_set)

    assert stochastic_model.scenarios is scenario_set
    assert stochastic_model.scenario_ids == ("base",)


def test_stochastic_model_is_immutable() -> None:
    stochastic_model = StochasticModel(_base_model(), (Scenario("base"),))

    with pytest.raises(FrozenInstanceError):
        stochastic_model.message = "changed"


def test_stochastic_model_validates_base_model_type() -> None:
    with pytest.raises(TypeError, match="base_model"):
        StochasticModel(object(), (Scenario("base"),))


def test_stochastic_model_validates_base_model_contents() -> None:
    bad_model = Model(
        variables=[Variable("x")],
        constraints=[Constraint("bad", {"missing": 1.0})],
    )

    with pytest.raises(ValueError, match="Unknown variable"):
        StochasticModel(bad_model, (Scenario("base"),))


@pytest.mark.parametrize(
    "scenarios, error_type, error_message",
    [
        ((), ValueError, "at least one"),
        ((Scenario("base", 0.6),), ValueError, "sum to one"),
        ((Scenario("base", 0.5), Scenario(" base ", 0.5)), ValueError, "unique"),
        (("base",), TypeError, "Scenario records"),
    ],
)
def test_stochastic_model_validates_scenario_collection(
    scenarios: object,
    error_type: type[Exception],
    error_message: str,
) -> None:
    with pytest.raises(error_type, match=error_message):
        StochasticModel(_base_model(), scenarios)


def test_stochastic_model_rejects_unknown_declared_variables() -> None:
    with pytest.raises(ValueError, match="Unknown first-stage variable"):
        StochasticModel(
            _base_model(),
            (Scenario("base"),),
            first_stage_variables=("missing",),
        )

    with pytest.raises(ValueError, match="Unknown scenario-dependent variable"):
        StochasticModel(
            _base_model(),
            (Scenario("base"),),
            scenario_dependent_variables=("missing",),
        )


def test_stochastic_model_rejects_unknown_declared_constraints() -> None:
    with pytest.raises(ValueError, match="Unknown scenario-dependent constraint"):
        StochasticModel(
            _base_model(),
            (Scenario("base"),),
            scenario_dependent_constraints=("missing",),
        )


def test_stochastic_model_rejects_overlapping_variable_declarations() -> None:
    with pytest.raises(ValueError, match="must not overlap"):
        StochasticModel(
            _base_model(),
            (Scenario("base"),),
            first_stage_variables=("x",),
            scenario_dependent_variables=("x",),
        )


@pytest.mark.parametrize(
    "kwargs, error_type, error_message",
    [
        ({"first_stage_variables": "x"}, TypeError, "sequence of names"),
        ({"first_stage_variables": ("x", " x ")}, ValueError, "duplicate"),
        ({"first_stage_variables": ("",)}, ValueError, "must not be empty"),
        ({"first_stage_variables": (1,)}, TypeError, "must be a string"),
        (
            {"scenario_dependent_variables": ("y", " y ")},
            ValueError,
            "duplicate",
        ),
        (
            {"scenario_dependent_constraints": ("demand", " demand ")},
            ValueError,
            "duplicate",
        ),
    ],
)
def test_stochastic_model_rejects_invalid_declaration_names(
    kwargs: dict[str, object],
    error_type: type[Exception],
    error_message: str,
) -> None:
    with pytest.raises(error_type, match=error_message):
        StochasticModel(_base_model(), (Scenario("base"),), **kwargs)


def test_stochastic_model_validates_metadata_and_message() -> None:
    with pytest.raises(ValueError, match="metadata key"):
        StochasticModel(_base_model(), (Scenario("base"),), metadata={"": 1})

    with pytest.raises(ValueError, match="metadata float"):
        StochasticModel(_base_model(), (Scenario("base"),), metadata={"value": inf})

    with pytest.raises(TypeError, match="metadata values"):
        StochasticModel(_base_model(), (Scenario("base"),), metadata={"value": object()})

    with pytest.raises(TypeError, match="message"):
        StochasticModel(_base_model(), (Scenario("base"),), message=object())


def test_stochastic_model_module_has_no_solver_or_transformation_integration() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "uncertainty" / "stochastic_model.py").read_text(
        encoding="utf-8"
    )
    forbidden_patterns = (
        "silo.lp",
        "silo.mip",
        "silo.presolve",
        "silo.cuts",
        "silo.decomposition",
        "silo.interfaces",
        "build_deterministic_equivalent",
        "LPSolver",
        "BranchAndBoundSolver",
        "Presolver",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source
