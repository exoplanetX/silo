from pathlib import Path

import pytest

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
from silo.uncertainty.uncertainty_set import (
    CONSTRAINT_COEFFICIENT_TARGET,
    OBJECTIVE_TARGET,
    PARAMETER_TARGET,
    RHS_TARGET,
    IntervalUncertainty,
    UncertaintySet,
)


def _base_model() -> Model:
    return Model(
        name="robust_rhs_lp",
        variables=[Variable("x"), Variable("y")],
        constraints=[
            Constraint("capacity", {"x": 1.0, "y": 1.0}, ConstraintSense.LE, 10.0),
            Constraint("demand", {"x": 1.0}, ConstraintSense.GE, 3.0),
            Constraint("balance", {"x": 1.0, "y": -1.0}, ConstraintSense.EQ, 0.0),
            Constraint("unchanged", {"y": 1.0}, ConstraintSense.LE, 8.0),
        ],
        objective=Objective({"x": 2.0, "y": 1.0}),
    )


def _robust_model(*intervals: IntervalUncertainty) -> RobustModel:
    return RobustModel(
        base_model=_base_model(),
        uncertainty_set=UncertaintySet("rhs_box", intervals),
        assumptions=("independent RHS intervals",),
    )


def _rhs_interval(
    name: str,
    constraint_name: str,
    lower: float,
    upper: float,
    *,
    nominal: float | None = None,
) -> IntervalUncertainty:
    return IntervalUncertainty(
        name=name,
        target=RHS_TARGET,
        lower=lower,
        upper=upper,
        nominal=nominal,
        constraint_name=constraint_name,
    )


def test_rhs_counterpart_applies_le_ge_and_degenerate_equality_conventions() -> None:
    robust_model = _robust_model(
        _rhs_interval("capacity_rhs", "capacity", 7.0, 12.0, nominal=10.0),
        _rhs_interval("demand_rhs", "demand", 1.0, 4.0, nominal=3.0),
        _rhs_interval("balance_rhs", "balance", 0.0, 0.0, nominal=0.0),
    )

    result = build_robust_counterpart(robust_model)

    assert isinstance(result, RobustCounterpartResult)
    assert result.model is not robust_model.base_model
    assert result.model.name == "robust_rhs_lp_robust_counterpart"
    constraints = {constraint.name: constraint for constraint in result.model.constraints}
    assert constraints["capacity"].rhs == 7.0
    assert constraints["demand"].rhs == 4.0
    assert constraints["balance"].rhs == 0.0
    assert constraints["unchanged"].rhs == 8.0
    assert constraints["capacity"].coefficients == {"x": 1.0, "y": 1.0}
    assert result.model.objective.coefficients == {"x": 2.0, "y": 1.0}
    assert result.diagnostics.interval_names == (
        "balance_rhs",
        "capacity_rhs",
        "demand_rhs",
    )
    assert result.diagnostics.adjusted_constraints == (
        "balance",
        "capacity",
        "demand",
    )
    assert result.diagnostics.adjusted_constraint_count == 3
    assert result.diagnostics.generated_constraints == 0
    assert result.diagnostics.metadata == (("builder", "toy_interval_rhs"),)


def test_rhs_counterpart_does_not_mutate_base_model_or_uncertainty_records() -> None:
    interval = _rhs_interval("capacity_rhs", "capacity", 7.0, 12.0, nominal=10.0)
    robust_model = _robust_model(interval)
    base_model = robust_model.base_model
    base_constraint_data = [
        (constraint.name, dict(constraint.coefficients), constraint.sense, constraint.rhs)
        for constraint in base_model.constraints
    ]
    interval_snapshot = (
        interval.name,
        interval.target,
        interval.lower,
        interval.upper,
        interval.nominal,
        interval.constraint_name,
        interval.variable_name,
    )

    result = build_robust_counterpart(robust_model)
    result.model.constraints[0].coefficients["x"] = 99.0

    assert [
        (constraint.name, dict(constraint.coefficients), constraint.sense, constraint.rhs)
        for constraint in base_model.constraints
    ] == base_constraint_data
    assert (
        interval.name,
        interval.target,
        interval.lower,
        interval.upper,
        interval.nominal,
        interval.constraint_name,
        interval.variable_name,
    ) == interval_snapshot


def test_rhs_counterpart_rejects_nondegenerate_equality_intervals() -> None:
    robust_model = _robust_model(_rhs_interval("balance_rhs", "balance", -1.0, 1.0))

    with pytest.raises(ValueError, match="equality RHS intervals"):
        build_robust_counterpart(robust_model)


@pytest.mark.parametrize(
    "target",
    [OBJECTIVE_TARGET, CONSTRAINT_COEFFICIENT_TARGET, PARAMETER_TARGET],
)
def test_rhs_counterpart_rejects_unsupported_targets(target: str) -> None:
    robust_model = RobustModel(
        base_model=_base_model(),
        uncertainty_set=UncertaintySet(
            "unsupported",
            (
                IntervalUncertainty(
                    name="unsupported_interval",
                    target=target,
                    lower=1.0,
                    upper=2.0,
                    constraint_name="capacity",
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="RHS intervals only"):
        build_robust_counterpart(robust_model)


def test_rhs_counterpart_rejects_missing_constraint_name() -> None:
    robust_model = RobustModel(
        base_model=_base_model(),
        uncertainty_set=UncertaintySet(
            "missing_name",
            (IntervalUncertainty("rhs", RHS_TARGET, 1.0, 2.0),),
        ),
    )

    with pytest.raises(ValueError, match="constraint name"):
        build_robust_counterpart(robust_model)


def test_rhs_counterpart_rejects_unknown_constraints() -> None:
    robust_model = _robust_model(_rhs_interval("missing_rhs", "missing", 1.0, 2.0))

    with pytest.raises(ValueError, match="Unknown RHS interval constraint"):
        build_robust_counterpart(robust_model)


def test_rhs_counterpart_rejects_duplicate_constraint_intervals() -> None:
    robust_model = _robust_model(
        _rhs_interval("capacity_a", "capacity", 7.0, 12.0),
        _rhs_interval("capacity_b", "capacity", 6.0, 11.0),
    )

    with pytest.raises(ValueError, match="Duplicate RHS interval constraint"):
        build_robust_counterpart(robust_model)


def test_rhs_counterpart_rejects_variable_names_on_rhs_intervals() -> None:
    robust_model = RobustModel(
        base_model=_base_model(),
        uncertainty_set=UncertaintySet(
            "bad_rhs",
            (
                IntervalUncertainty(
                    "capacity_rhs",
                    RHS_TARGET,
                    7.0,
                    12.0,
                    constraint_name="capacity",
                    variable_name="x",
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="variable name"):
        build_robust_counterpart(robust_model)


def test_rhs_counterpart_rejects_nominal_base_rhs_mismatches() -> None:
    robust_model = _robust_model(
        _rhs_interval("capacity_rhs", "capacity", 7.0, 12.0, nominal=9.0),
    )

    with pytest.raises(ValueError, match="nominal value"):
        build_robust_counterpart(robust_model)


def test_rhs_counterpart_requires_robust_model_input() -> None:
    with pytest.raises(TypeError, match="RobustModel"):
        build_robust_counterpart(object())


def test_robust_counterpart_module_has_no_solver_cli_or_schema_integration() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "uncertainty" / "robust_counterpart.py").read_text(
        encoding="utf-8"
    )
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
