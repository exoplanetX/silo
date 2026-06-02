from dataclasses import FrozenInstanceError
from math import inf, nan
from pathlib import Path

import pytest

import silo.uncertainty as uncertainty
from silo.uncertainty.uncertainty_set import (
    CONSTRAINT_COEFFICIENT_TARGET,
    OBJECTIVE_TARGET,
    PARAMETER_TARGET,
    RHS_TARGET,
    UNCERTAINTY_TARGETS,
    IntervalUncertainty,
    UncertaintySet,
)


def test_interval_uncertainty_normalizes_values_and_copies_inputs() -> None:
    metadata = {" z ": 2, "a": "alpha"}

    interval = IntervalUncertainty(
        name=" demand radius ",
        target=" rhs ",
        lower=1,
        upper=3,
        nominal=2,
        constraint_name=" demand ",
        variable_name=" ",
        metadata=metadata,
        message="rhs interval",
    )
    metadata[" z "] = 99

    assert interval.name == "demand radius"
    assert interval.target == RHS_TARGET
    assert interval.lower == 1.0
    assert interval.upper == 3.0
    assert interval.nominal == 2.0
    assert interval.width == 2.0
    assert interval.constraint_name == "demand"
    assert interval.variable_name == ""
    assert interval.metadata == (("a", "alpha"), ("z", 2))
    assert interval.message == "rhs interval"


def test_interval_uncertainty_is_immutable() -> None:
    interval = IntervalUncertainty("cost", OBJECTIVE_TARGET, 1.0, 2.0)

    with pytest.raises(FrozenInstanceError):
        interval.upper = 3.0


@pytest.mark.parametrize(
    "kwargs, error_type, error_message",
    [
        ({"name": ""}, ValueError, "interval name"),
        ({"name": 1}, TypeError, "interval name"),
        ({"target": "unsupported"}, ValueError, "target"),
        ({"target": 1}, TypeError, "target"),
        ({"lower": inf}, ValueError, "lower bound"),
        ({"upper": nan}, ValueError, "upper bound"),
        ({"lower": True}, TypeError, "lower bound"),
        ({"lower": 3.0, "upper": 1.0}, ValueError, "lower bound"),
        ({"nominal": inf}, ValueError, "nominal value"),
        ({"nominal": 4.0}, ValueError, "nominal value"),
        ({"nominal": True}, TypeError, "nominal value"),
        ({"constraint_name": 1}, TypeError, "constraint name"),
        ({"variable_name": object()}, TypeError, "variable name"),
    ],
)
def test_interval_uncertainty_rejects_invalid_values(
    kwargs: dict[str, object],
    error_type: type[Exception],
    error_message: str,
) -> None:
    values: dict[str, object] = {
        "name": "bad",
        "target": OBJECTIVE_TARGET,
        "lower": 1.0,
        "upper": 3.0,
    }
    values.update(kwargs)

    with pytest.raises(error_type, match=error_message):
        IntervalUncertainty(**values)


def test_interval_uncertainty_validates_metadata_and_message() -> None:
    with pytest.raises(ValueError, match="metadata key"):
        IntervalUncertainty("bad", PARAMETER_TARGET, 0.0, 1.0, metadata={"": 1})

    with pytest.raises(ValueError, match="metadata float"):
        IntervalUncertainty("bad", PARAMETER_TARGET, 0.0, 1.0, metadata={"value": inf})

    with pytest.raises(TypeError, match="metadata values"):
        IntervalUncertainty(
            "bad",
            PARAMETER_TARGET,
            0.0,
            1.0,
            metadata={"value": object()},
        )

    with pytest.raises(TypeError, match="message"):
        IntervalUncertainty("bad", PARAMETER_TARGET, 0.0, 1.0, message=object())


def test_uncertainty_set_orders_intervals_and_copies_inputs() -> None:
    intervals = [
        IntervalUncertainty("zeta", PARAMETER_TARGET, -1.0, 1.0),
        IntervalUncertainty("cost", OBJECTIVE_TARGET, 2.0, 5.0, variable_name="x"),
    ]
    metadata = {" z ": 2, "a": "alpha"}

    uncertainty_set = UncertaintySet(
        name=" box ",
        intervals=intervals,
        metadata=metadata,
        message="independent box",
    )
    intervals.append(IntervalUncertainty("extra", RHS_TARGET, 0.0, 1.0))
    metadata[" z "] = 99

    assert uncertainty_set.name == "box"
    assert uncertainty_set.dimension == 2
    assert uncertainty_set.interval_names == ("cost", "zeta")
    assert uncertainty_set.intervals[0].target == OBJECTIVE_TARGET
    assert uncertainty_set.metadata == (("a", "alpha"), ("z", 2))
    assert uncertainty_set.message == "independent box"


def test_uncertainty_set_is_immutable() -> None:
    uncertainty_set = UncertaintySet(
        "box",
        (IntervalUncertainty("zeta", PARAMETER_TARGET, -1.0, 1.0),),
    )

    with pytest.raises(FrozenInstanceError):
        uncertainty_set.message = "changed"


def test_uncertainty_set_rejects_invalid_interval_collections() -> None:
    interval = IntervalUncertainty("zeta", PARAMETER_TARGET, -1.0, 1.0)

    with pytest.raises(TypeError, match="sequence"):
        UncertaintySet("bad", interval)

    with pytest.raises(TypeError, match="IntervalUncertainty"):
        UncertaintySet("bad", ("zeta",))

    with pytest.raises(ValueError, match="at least one"):
        UncertaintySet("bad", ())

    with pytest.raises(ValueError, match="unique"):
        UncertaintySet("bad", (interval, interval))


def test_uncertainty_set_validates_name_metadata_and_message() -> None:
    interval = IntervalUncertainty("zeta", PARAMETER_TARGET, -1.0, 1.0)

    with pytest.raises(ValueError, match="uncertainty set name"):
        UncertaintySet("", (interval,))

    with pytest.raises(TypeError, match="uncertainty set name"):
        UncertaintySet(1, (interval,))

    with pytest.raises(ValueError, match="metadata key"):
        UncertaintySet("bad", (interval,), metadata={"": 1})

    with pytest.raises(ValueError, match="metadata float"):
        UncertaintySet("bad", (interval,), metadata={"value": inf})

    with pytest.raises(TypeError, match="metadata values"):
        UncertaintySet("bad", (interval,), metadata={"value": object()})

    with pytest.raises(TypeError, match="message"):
        UncertaintySet("bad", (interval,), message=object())


def test_uncertainty_targets_are_documented_constants() -> None:
    assert UNCERTAINTY_TARGETS == (
        OBJECTIVE_TARGET,
        RHS_TARGET,
        CONSTRAINT_COEFFICIENT_TARGET,
        PARAMETER_TARGET,
    )


def test_uncertainty_package_exports_remain_finite_scenario_only() -> None:
    assert uncertainty.__all__ == [
        "DEFAULT_PROBABILITY_TOLERANCE",
        "Scenario",
        "ScenarioSet",
    ]
    assert not hasattr(uncertainty, "IntervalUncertainty")
    assert not hasattr(uncertainty, "UncertaintySet")


def test_uncertainty_set_module_has_no_solver_or_transformation_integration() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "uncertainty" / "uncertainty_set.py").read_text(
        encoding="utf-8"
    )
    forbidden_patterns = (
        "silo.core",
        "silo.modeling",
        "silo.lp",
        "silo.mip",
        "silo.presolve",
        "silo.cuts",
        "silo.decomposition",
        "silo.interfaces",
        "Model(",
        "Constraint(",
        "Objective(",
        "build_deterministic_equivalent",
        "LPSolver",
        "BranchAndBoundSolver",
        "Presolver",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source
