from dataclasses import FrozenInstanceError

import pytest

from silo.presolve import PresolveWarning
from silo.presolve.scaling import ScalingDiagnostics, empty_scaling_diagnostics


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
