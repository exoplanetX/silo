from dataclasses import FrozenInstanceError

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.presolve import PresolveWarning
from silo.presolve.scaling import ScalingDiagnostics, analyze_scaling, empty_scaling_diagnostics
from silo.utils.numerics import DEFAULT_TOLERANCE


def test_scaling_diagnostics_defaults() -> None:
    diagnostics = ScalingDiagnostics()

    assert diagnostics.max_abs_coefficient == 0.0
    assert diagnostics.min_abs_nonzero_coefficient is None
    assert diagnostics.coefficient_ratio is None
    assert diagnostics.max_abs_rhs == 0.0
    assert diagnostics.max_abs_objective == 0.0
    assert diagnostics.warnings == ()


def test_scaling_diagnostics_warnings_are_tuples() -> None:
    warning = PresolveWarning(
        code="near_zero",
        message="Near-zero coefficient.",
        source="constraint:capacity",
    )
    diagnostics = ScalingDiagnostics(warnings=(warning,))

    assert diagnostics.warnings == (warning,)


def test_empty_scaling_diagnostics_helper() -> None:
    diagnostics = empty_scaling_diagnostics()

    assert diagnostics == ScalingDiagnostics()
    assert diagnostics.coefficient_ratio is None


def test_scaling_diagnostics_is_immutable() -> None:
    diagnostics = ScalingDiagnostics()

    with pytest.raises(FrozenInstanceError):
        diagnostics.max_abs_coefficient = 1.0


def test_analyze_scaling_empty_model_or_no_coefficients() -> None:
    diagnostics = analyze_scaling(Model(name="empty"))

    assert diagnostics.max_abs_coefficient == 0.0
    assert diagnostics.min_abs_nonzero_coefficient is None
    assert diagnostics.coefficient_ratio is None


def test_analyze_scaling_basic_coefficient_range() -> None:
    model = _model_with_coefficients(
        constraints=[
            Constraint(
                name="row1",
                coefficients={"x": 2.0, "y": 10.0},
                sense=ConstraintSense.LE,
                rhs=1.0,
            ),
            Constraint(
                name="row2",
                coefficients={"x": -5.0},
                sense=ConstraintSense.LE,
                rhs=1.0,
            ),
        ]
    )

    diagnostics = analyze_scaling(model)

    assert diagnostics.max_abs_coefficient == pytest.approx(10.0)
    assert diagnostics.min_abs_nonzero_coefficient == pytest.approx(2.0)
    assert diagnostics.coefficient_ratio == pytest.approx(5.0)


def test_analyze_scaling_rhs_magnitude() -> None:
    model = _model_with_coefficients(
        constraints=[
            Constraint(name="row1", coefficients={"x": 1.0}, rhs=-3.0),
            Constraint(name="row2", coefficients={"x": 1.0}, rhs=10.0),
        ]
    )

    diagnostics = analyze_scaling(model)

    assert diagnostics.max_abs_rhs == pytest.approx(10.0)


def test_analyze_scaling_objective_magnitude() -> None:
    model = _model_with_coefficients(objective_coefficients={"x": 3.0, "y": -12.0})

    diagnostics = analyze_scaling(model)

    assert diagnostics.max_abs_objective == pytest.approx(12.0)


def test_analyze_scaling_warns_for_near_zero_constraint_coefficient() -> None:
    model = _model_with_coefficients(
        constraints=[
            Constraint(
                name="near",
                coefficients={"x": DEFAULT_TOLERANCE / 10},
                rhs=1.0,
            )
        ]
    )

    diagnostics = analyze_scaling(model)

    assert diagnostics.max_abs_coefficient == 0.0
    assert diagnostics.warnings[0].code == "near_zero_coefficient"
    assert diagnostics.warnings[0].source == "near:x"


def test_analyze_scaling_warns_for_near_zero_objective_coefficient() -> None:
    model = _model_with_coefficients(
        objective_coefficients={"x": DEFAULT_TOLERANCE / 10}
    )

    diagnostics = analyze_scaling(model)

    assert diagnostics.max_abs_objective == pytest.approx(DEFAULT_TOLERANCE / 10)
    assert diagnostics.warnings[0].code == "near_zero_objective"
    assert diagnostics.warnings[0].source == "objective:x"


def test_analyze_scaling_warns_for_large_coefficient_ratio() -> None:
    model = _model_with_coefficients(
        constraints=[
            Constraint(name="small", coefficients={"x": 1.0}, rhs=1.0),
            Constraint(name="large", coefficients={"y": 1e9}, rhs=1.0),
        ]
    )

    diagnostics = analyze_scaling(model)

    assert diagnostics.coefficient_ratio == pytest.approx(1e9)
    assert [warning.code for warning in diagnostics.warnings] == [
        "large_coefficient_ratio"
    ]


def test_analyze_scaling_warns_for_large_rhs() -> None:
    model = _model_with_coefficients(
        constraints=[Constraint(name="large_rhs", coefficients={"x": 1.0}, rhs=1e9)]
    )

    diagnostics = analyze_scaling(model)

    assert diagnostics.max_abs_rhs == pytest.approx(1e9)
    assert [warning.code for warning in diagnostics.warnings] == ["large_rhs"]


def test_analyze_scaling_warns_for_large_objective() -> None:
    model = _model_with_coefficients(objective_coefficients={"x": 1e9})

    diagnostics = analyze_scaling(model)

    assert diagnostics.max_abs_objective == pytest.approx(1e9)
    assert [warning.code for warning in diagnostics.warnings] == ["large_objective"]


def test_analyze_scaling_warning_order_is_deterministic() -> None:
    model = _model_with_coefficients(
        constraints=[
            Constraint(
                name="row1",
                coefficients={"x": DEFAULT_TOLERANCE / 10, "y": 1.0},
                rhs=1e9,
            ),
            Constraint(
                name="row2",
                coefficients={"y": DEFAULT_TOLERANCE / 20, "x": 1e9},
                rhs=1.0,
            ),
        ],
        objective_coefficients={
            "x": DEFAULT_TOLERANCE / 10,
            "y": 1e9,
        },
    )

    diagnostics = analyze_scaling(model)

    assert [warning.code for warning in diagnostics.warnings] == [
        "near_zero_coefficient",
        "near_zero_coefficient",
        "near_zero_objective",
        "large_coefficient_ratio",
        "large_rhs",
        "large_objective",
    ]
    assert [warning.source for warning in diagnostics.warnings[:3]] == [
        "row1:x",
        "row2:y",
        "objective:x",
    ]


def _model_with_coefficients(
    constraints: list[Constraint] | None = None,
    objective_coefficients: dict[str, float] | None = None,
) -> Model:
    model = Model(name="scaling")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    for constraint in constraints or []:
        model.add_constraint(constraint)
    model.set_objective(
        Objective(
            coefficients=objective_coefficients or {},
            sense=OptimizationSense.MAXIMIZE,
        )
    )
    return model
