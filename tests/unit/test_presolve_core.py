from dataclasses import FrozenInstanceError

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.presolve import (
    PresolveDiagnostics,
    Presolver,
    PresolveResult,
    PresolveStatus,
    PresolveWarning,
    ReductionRecord,
    ReductionType,
    ScalingDiagnostics,
    reduction_data,
)


def test_no_op_presolver_returns_same_model() -> None:
    model = _small_lp_model()

    result = Presolver().run(model)

    assert result.model is model
    assert result.original_model is model
    assert result.reductions == ()
    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert result.scaling.max_abs_coefficient == 1.0
    assert result.scaling.min_abs_nonzero_coefficient == 1.0
    assert result.scaling.coefficient_ratio == 1.0
    assert result.changed is False


def test_no_op_presolver_validates_model() -> None:
    model = Model(name="invalid")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="unknown_reference",
            coefficients={"missing": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    with pytest.raises(ValueError, match="Unknown variable"):
        Presolver().run(model)


def test_presolve_diagnostics_defaults_are_empty_tuples() -> None:
    diagnostics = PresolveDiagnostics()

    assert diagnostics.status == PresolveStatus.NOT_RUN
    assert diagnostics.warnings == ()
    assert diagnostics.removed_rows == ()
    assert diagnostics.removed_variables == ()
    assert diagnostics.fixed_variables == ()
    assert diagnostics.notes == ()


def test_presolve_warning_fields() -> None:
    warning = PresolveWarning(
        code="coefficient_range",
        message="Large coefficient range.",
        source="row:capacity",
    )

    assert warning.code == "coefficient_range"
    assert warning.message == "Large coefficient range."
    assert warning.source == "row:capacity"


def test_reduction_record_stores_data_deterministically() -> None:
    data = reduction_data(z_value=3.0, a_value=1.0, m_value=2.0)
    record = ReductionRecord(
        reduction_type=ReductionType.FIXED_VARIABLE,
        target="x",
        description="Fixed variable x.",
        data=data,
    )

    assert record.data == (
        ("a_value", 1.0),
        ("m_value", 2.0),
        ("z_value", 3.0),
    )


def test_reduction_record_is_immutable() -> None:
    record = ReductionRecord(
        reduction_type=ReductionType.NO_OP,
        target="model",
        description="No change.",
    )

    with pytest.raises(FrozenInstanceError):
        record.target = "other"


def test_manual_presolve_result_contains_diagnostics_and_scaling() -> None:
    model = _small_lp_model()
    diagnostics = PresolveDiagnostics(
        status=PresolveStatus.NO_CHANGE,
        notes=("validated",),
    )
    scaling = ScalingDiagnostics(max_abs_coefficient=1.0)
    result = PresolveResult(
        model=model,
        reductions=(),
        diagnostics=diagnostics,
        scaling=scaling,
    )

    assert result.model is model
    assert result.diagnostics is diagnostics
    assert result.scaling is scaling
    assert result.changed is False
    assert result.message == ""


def _small_lp_model() -> Model:
    model = Model(name="small")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model
