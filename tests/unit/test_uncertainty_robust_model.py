from dataclasses import FrozenInstanceError
from math import inf
from pathlib import Path

import pytest

import silo.uncertainty as uncertainty
from silo.core.constraint import Constraint
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.robust_model import RobustModel
from silo.uncertainty.uncertainty_set import (
    OBJECTIVE_TARGET,
    PARAMETER_TARGET,
    IntervalUncertainty,
    UncertaintySet,
)


def _base_model() -> Model:
    return Model(
        name="robust_lp",
        variables=[Variable("x")],
        constraints=[Constraint("demand", {"x": 1.0})],
        objective=Objective({"x": 1.0}),
    )


def _uncertainty_set() -> UncertaintySet:
    return UncertaintySet(
        name="box",
        intervals=(
            IntervalUncertainty("zeta", PARAMETER_TARGET, -1.0, 1.0),
            IntervalUncertainty("cost", OBJECTIVE_TARGET, 2.0, 3.0),
        ),
    )


def test_robust_model_normalizes_records_and_copies_inputs() -> None:
    assumptions = [" linear decision rule not used ", " independent intervals "]
    metadata = {" z ": 2, "a": "alpha"}
    base_model = _base_model()
    uncertainty_set = _uncertainty_set()

    robust_model = RobustModel(
        base_model=base_model,
        uncertainty_set=uncertainty_set,
        assumptions=assumptions,
        metadata=metadata,
        message="passive wrapper",
    )
    assumptions.append("changed")
    metadata[" z "] = 99

    assert robust_model.base_model is base_model
    assert robust_model.uncertainty_set is uncertainty_set
    assert robust_model.uncertainty_set_name == "box"
    assert robust_model.assumptions == (
        "independent intervals",
        "linear decision rule not used",
    )
    assert robust_model.assumption_count == 2
    assert robust_model.metadata == (("a", "alpha"), ("z", 2))
    assert robust_model.message == "passive wrapper"


def test_robust_model_is_immutable() -> None:
    robust_model = RobustModel(_base_model(), _uncertainty_set())

    with pytest.raises(FrozenInstanceError):
        robust_model.message = "changed"


def test_robust_model_validates_base_model_type() -> None:
    with pytest.raises(TypeError, match="base_model"):
        RobustModel(object(), _uncertainty_set())


def test_robust_model_validates_base_model_contents() -> None:
    bad_model = Model(
        variables=[Variable("x")],
        constraints=[Constraint("bad", {"missing": 1.0})],
    )

    with pytest.raises(ValueError, match="Unknown variable"):
        RobustModel(bad_model, _uncertainty_set())


def test_robust_model_validates_uncertainty_set_type() -> None:
    with pytest.raises(TypeError, match="uncertainty_set"):
        RobustModel(_base_model(), object())


@pytest.mark.parametrize(
    "assumptions, error_type, error_message",
    [
        ("convex", TypeError, "sequence"),
        ((1,), TypeError, "assumption"),
        (("",), ValueError, "assumption"),
        (("bounded", " bounded "), ValueError, "duplicates"),
    ],
)
def test_robust_model_rejects_invalid_assumptions(
    assumptions: object,
    error_type: type[Exception],
    error_message: str,
) -> None:
    with pytest.raises(error_type, match=error_message):
        RobustModel(_base_model(), _uncertainty_set(), assumptions=assumptions)


def test_robust_model_validates_metadata_and_message() -> None:
    with pytest.raises(ValueError, match="metadata key"):
        RobustModel(_base_model(), _uncertainty_set(), metadata={"": 1})

    with pytest.raises(ValueError, match="metadata float"):
        RobustModel(_base_model(), _uncertainty_set(), metadata={"value": inf})

    with pytest.raises(TypeError, match="metadata values"):
        RobustModel(_base_model(), _uncertainty_set(), metadata={"value": object()})

    with pytest.raises(TypeError, match="message"):
        RobustModel(_base_model(), _uncertainty_set(), message=object())


def test_uncertainty_package_exports_remain_finite_scenario_only() -> None:
    assert uncertainty.__all__ == [
        "DEFAULT_PROBABILITY_TOLERANCE",
        "Scenario",
        "ScenarioSet",
    ]
    assert not hasattr(uncertainty, "RobustModel")


def test_robust_model_module_has_no_solver_or_transformation_integration() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "uncertainty" / "robust_model.py").read_text(
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
        "build_robust_counterpart",
        "Model(",
        "Constraint(",
        "Objective(",
        "LPSolver",
        "BranchAndBoundSolver",
        "Presolver",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source
