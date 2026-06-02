from dataclasses import FrozenInstanceError
from math import inf, nan
from pathlib import Path

import pytest

import silo.uncertainty as uncertainty
from silo.core.constraint import Constraint
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.deterministic_equivalent import (
    DEFAULT_DETERMINISTIC_EQUIVALENT_NAMING,
    EXPECTED_VALUE_OBJECTIVE,
    DeterministicEquivalentDiagnostics,
    DeterministicEquivalentResult,
    build_deterministic_equivalent,
)
from silo.uncertainty.scenario import (
    DEFAULT_PROBABILITY_TOLERANCE,
    Scenario,
)
from silo.uncertainty.stochastic_model import StochasticModel


def _base_model() -> Model:
    return Model(
        name="two_stage",
        variables=[Variable("x"), Variable("y")],
        constraints=[Constraint("demand", {"x": 1.0, "y": 1.0})],
        objective=Objective({"x": 1.0, "y": 2.0}),
    )


def test_diagnostics_normalizes_values_and_copies_inputs() -> None:
    metadata = {" z ": 2, "a": "alpha"}

    diagnostics = DeterministicEquivalentDiagnostics(
        scenario_ids=(" low ", "high"),
        generated_variables=3,
        generated_constraints=4,
        nonanticipativity_constraints=1,
        probability_total=1,
        metadata=metadata,
        message="record only",
    )
    metadata[" z "] = 99

    assert diagnostics.scenario_ids == ("high", "low")
    assert diagnostics.scenario_count == 2
    assert diagnostics.generated_variables == 3
    assert diagnostics.generated_constraints == 4
    assert diagnostics.nonanticipativity_constraints == 1
    assert diagnostics.objective_aggregation == EXPECTED_VALUE_OBJECTIVE
    assert diagnostics.probability_total == 1.0
    assert diagnostics.probability_tolerance == DEFAULT_PROBABILITY_TOLERANCE
    assert diagnostics.naming_convention == DEFAULT_DETERMINISTIC_EQUIVALENT_NAMING
    assert diagnostics.metadata == (("a", "alpha"), ("z", 2))
    assert diagnostics.message == "record only"


def test_diagnostics_is_immutable() -> None:
    diagnostics = DeterministicEquivalentDiagnostics(("base",))

    with pytest.raises(FrozenInstanceError):
        diagnostics.generated_variables = 1


@pytest.mark.parametrize(
    "scenario_ids, error_type, error_message",
    [
        ("base", TypeError, "sequence"),
        ((), ValueError, "at least one"),
        (("",), ValueError, "must not be empty"),
        ((1,), TypeError, "must be a string"),
        (("base", " base "), ValueError, "unique"),
    ],
)
def test_diagnostics_rejects_invalid_scenario_ids(
    scenario_ids: object,
    error_type: type[Exception],
    error_message: str,
) -> None:
    with pytest.raises(error_type, match=error_message):
        DeterministicEquivalentDiagnostics(scenario_ids)


@pytest.mark.parametrize(
    "field_name",
    [
        "generated_variables",
        "generated_constraints",
        "nonanticipativity_constraints",
    ],
)
def test_diagnostics_rejects_invalid_counts(field_name: str) -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        DeterministicEquivalentDiagnostics(("base",), **{field_name: -1})

    with pytest.raises(TypeError, match="integer"):
        DeterministicEquivalentDiagnostics(("base",), **{field_name: True})

    with pytest.raises(TypeError, match="integer"):
        DeterministicEquivalentDiagnostics(("base",), **{field_name: 1.5})


@pytest.mark.parametrize(
    "kwargs, error_type, error_message",
    [
        ({"probability_total": 0.0}, ValueError, "positive"),
        ({"probability_total": -1.0}, ValueError, "positive"),
        ({"probability_total": inf}, ValueError, "finite"),
        ({"probability_total": nan}, ValueError, "finite"),
        ({"probability_total": True}, TypeError, "numeric"),
        ({"probability_tolerance": 0.0}, ValueError, "positive"),
        ({"probability_tolerance": -1.0}, ValueError, "positive"),
        ({"probability_tolerance": inf}, ValueError, "finite"),
        ({"probability_tolerance": nan}, ValueError, "finite"),
        ({"probability_tolerance": True}, TypeError, "numeric"),
    ],
)
def test_diagnostics_rejects_invalid_probability_values(
    kwargs: dict[str, object],
    error_type: type[Exception],
    error_message: str,
) -> None:
    with pytest.raises(error_type, match=error_message):
        DeterministicEquivalentDiagnostics(("base",), **kwargs)


def test_diagnostics_validates_text_metadata_and_message() -> None:
    with pytest.raises(ValueError, match="objective aggregation"):
        DeterministicEquivalentDiagnostics(("base",), objective_aggregation=" ")

    with pytest.raises(ValueError, match="naming convention"):
        DeterministicEquivalentDiagnostics(("base",), naming_convention="")

    with pytest.raises(ValueError, match="metadata key"):
        DeterministicEquivalentDiagnostics(("base",), metadata={"": 1})

    with pytest.raises(ValueError, match="metadata float"):
        DeterministicEquivalentDiagnostics(("base",), metadata={"value": inf})

    with pytest.raises(TypeError, match="metadata values"):
        DeterministicEquivalentDiagnostics(("base",), metadata={"value": object()})

    with pytest.raises(TypeError, match="message"):
        DeterministicEquivalentDiagnostics(("base",), message=object())


def test_result_pairs_valid_model_with_diagnostics_and_copies_metadata() -> None:
    metadata = {" z ": 2, "a": "alpha"}
    model = _base_model()
    diagnostics = DeterministicEquivalentDiagnostics(("base",))

    result = DeterministicEquivalentResult(
        model=model,
        diagnostics=diagnostics,
        metadata=metadata,
        message="passive result",
    )
    metadata[" z "] = 99

    assert result.model is model
    assert result.diagnostics is diagnostics
    assert result.metadata == (("a", "alpha"), ("z", 2))
    assert result.message == "passive result"


def test_result_is_immutable() -> None:
    result = DeterministicEquivalentResult(
        model=_base_model(),
        diagnostics=DeterministicEquivalentDiagnostics(("base",)),
    )

    with pytest.raises(FrozenInstanceError):
        result.message = "changed"


def test_result_rejects_invalid_model_and_diagnostics() -> None:
    diagnostics = DeterministicEquivalentDiagnostics(("base",))

    with pytest.raises(TypeError, match="model"):
        DeterministicEquivalentResult(object(), diagnostics)

    with pytest.raises(TypeError, match="diagnostics"):
        DeterministicEquivalentResult(_base_model(), object())

    bad_model = Model(
        variables=[Variable("x")],
        constraints=[Constraint("bad", {"missing": 1.0})],
    )
    with pytest.raises(ValueError, match="Unknown variable"):
        DeterministicEquivalentResult(bad_model, diagnostics)


def test_result_validates_metadata_and_message() -> None:
    diagnostics = DeterministicEquivalentDiagnostics(("base",))

    with pytest.raises(ValueError, match="metadata key"):
        DeterministicEquivalentResult(_base_model(), diagnostics, metadata={"": 1})

    with pytest.raises(ValueError, match="metadata float"):
        DeterministicEquivalentResult(_base_model(), diagnostics, metadata={"value": inf})

    with pytest.raises(TypeError, match="metadata values"):
        DeterministicEquivalentResult(
            _base_model(),
            diagnostics,
            metadata={"value": object()},
        )

    with pytest.raises(TypeError, match="message"):
        DeterministicEquivalentResult(_base_model(), diagnostics, message=object())


def test_existing_builder_placeholder_behavior_is_unchanged() -> None:
    base_model = _base_model()
    stochastic_model = StochasticModel(
        base_model=base_model,
        scenarios=(Scenario("base"),),
    )

    assert build_deterministic_equivalent(stochastic_model) is base_model


def test_uncertainty_package_exports_remain_finite_scenario_only() -> None:
    assert uncertainty.__all__ == [
        "DEFAULT_PROBABILITY_TOLERANCE",
        "Scenario",
        "ScenarioSet",
    ]
    assert not hasattr(uncertainty, "DeterministicEquivalentDiagnostics")
    assert not hasattr(uncertainty, "DeterministicEquivalentResult")


def test_deterministic_equivalent_module_has_no_solver_or_builder_logic() -> None:
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
        "add_variable(",
        "add_constraint(",
        "set_objective(",
        "scenario_variable_name(",
        "scenario_constraint_name(",
        "nonanticipativity_constraint_name(",
        "LPSolver",
        "BranchAndBoundSolver",
        "Presolver",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source
    assert "return model.base_model" in source
