from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.status import SolverStatus
from silo.decomposition import BendersCutCandidate, BendersCutType, BendersSolver


def test_feasibility_cut_construction_normalizes_values() -> None:
    coefficients = {"y": 2, "x": 1.5}

    cut = BendersCutCandidate(
        cut_id=" cut-1 ",
        cut_type="feasibility",
        coefficients=coefficients,
        sense="<=",
        rhs=3,
        source_subproblem=" subproblem-a ",
        iteration_id=2,
        tolerance=1e-7,
        message="fixture cut",
    )
    coefficients["x"] = 99.0

    assert cut.cut_id == "cut-1"
    assert cut.cut_type == BendersCutType.FEASIBILITY
    assert cut.coefficients == (("x", 1.5), ("y", 2.0))
    assert cut.sense == ConstraintSense.LE
    assert cut.rhs == 3.0
    assert cut.source_subproblem == "subproblem-a"
    assert cut.iteration_id == 2
    assert cut.tolerance == 1e-7
    assert cut.message == "fixture cut"


def test_optimality_cut_construction_normalizes_values() -> None:
    cut = BendersCutCandidate(
        cut_id="theta-bound",
        cut_type=BendersCutType.OPTIMALITY,
        coefficients={"theta": 1, "x": -2},
        sense=ConstraintSense.GE,
        rhs=4,
        source_subproblem="recourse",
        iteration_id=0,
    )

    assert cut.cut_type == BendersCutType.OPTIMALITY
    assert cut.coefficients == (("theta", 1.0), ("x", -2.0))
    assert cut.sense == ConstraintSense.GE
    assert cut.rhs == 4.0


def test_benders_cut_candidate_is_immutable() -> None:
    cut = BendersCutCandidate(
        "cut-1",
        BendersCutType.FEASIBILITY,
        {"x": 1.0},
        ConstraintSense.LE,
        1.0,
        "subproblem",
        0,
    )

    with pytest.raises(FrozenInstanceError):
        cut.rhs = 2.0


@pytest.mark.parametrize("cut_id", ["", " "])
def test_rejects_invalid_cut_ids(cut_id: str) -> None:
    with pytest.raises(ValueError, match="cut id"):
        BendersCutCandidate(
            cut_id,
            BendersCutType.FEASIBILITY,
            {"x": 1.0},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
        )


def test_rejects_invalid_cut_type() -> None:
    with pytest.raises(ValueError, match="BendersCutType"):
        BendersCutCandidate(
            "cut-1",
            "bad",
            {"x": 1.0},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
        )


def test_rejects_empty_coefficient_mapping() -> None:
    with pytest.raises(ValueError, match="coefficients must not be empty"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
        )


def test_rejects_empty_variable_name() -> None:
    with pytest.raises(ValueError, match="variable names"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {" ": 1.0},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
        )


@pytest.mark.parametrize("coefficient", [inf, -inf, nan])
def test_rejects_nonfinite_coefficients(coefficient: float) -> None:
    with pytest.raises(ValueError, match="coefficients must be finite"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": coefficient},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
        )


def test_rejects_all_zero_coefficient_vector() -> None:
    with pytest.raises(ValueError, match="nonzero"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": 0.0, "y": 0.0},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
        )


def test_rejects_invalid_constraint_sense() -> None:
    with pytest.raises(ValueError, match="ConstraintSense"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": 1.0},
            "bad",
            1.0,
            "subproblem",
            0,
        )


@pytest.mark.parametrize("rhs", [inf, -inf, nan])
def test_rejects_nonfinite_rhs(rhs: float) -> None:
    with pytest.raises(ValueError, match="RHS must be finite"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": 1.0},
            ConstraintSense.LE,
            rhs,
            "subproblem",
            0,
        )


@pytest.mark.parametrize("source", ["", " "])
def test_rejects_invalid_source_subproblem_labels(source: str) -> None:
    with pytest.raises(ValueError, match="source subproblem"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": 1.0},
            ConstraintSense.LE,
            1.0,
            source,
            0,
        )


@pytest.mark.parametrize("iteration_id", [-1, True])
def test_rejects_invalid_iteration_ids(iteration_id: int) -> None:
    expected_error = ValueError if iteration_id == -1 else TypeError
    with pytest.raises(expected_error, match="iteration id"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": 1.0},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            iteration_id,
        )


@pytest.mark.parametrize("tolerance", [0.0, -1.0, inf, nan])
def test_rejects_nonpositive_or_nonfinite_tolerances(tolerance: float) -> None:
    with pytest.raises(ValueError, match="tolerance"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": 1.0},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
            tolerance=tolerance,
        )


def test_rejects_invalid_message_values() -> None:
    with pytest.raises(TypeError, match="message"):
        BendersCutCandidate(
            "cut-1",
            BendersCutType.FEASIBILITY,
            {"x": 1.0},
            ConstraintSense.LE,
            1.0,
            "subproblem",
            0,
            message=object(),
        )


def test_canonical_key_ignores_nonmathematical_metadata_and_input_order() -> None:
    first = BendersCutCandidate(
        "cut-a",
        BendersCutType.FEASIBILITY,
        {"x": 1.0, "y": 2.0},
        ConstraintSense.LE,
        3.0,
        "subproblem-a",
        0,
        tolerance=1e-7,
        message="first",
    )
    second = BendersCutCandidate(
        "cut-b",
        "feasibility",
        {"y": 2.0, "x": 1.0},
        "<=",
        3.0,
        "subproblem-b",
        3,
        tolerance=1e-5,
        message="second",
    )

    assert first.canonical_key() == second.canonical_key()


def test_canonical_key_respects_explicit_variable_order() -> None:
    cut = BendersCutCandidate(
        "cut-a",
        BendersCutType.OPTIMALITY,
        {"x": 1.0, "y": 2.0, "theta": 3.0},
        ConstraintSense.GE,
        4.0,
        "recourse",
        1,
    )

    assert cut.canonical_key(variable_order=("theta", "x")) == (
        "benders_cut",
        "optimality",
        (("theta", 3.0), ("x", 1.0), ("y", 2.0)),
        ">=",
        4.0,
    )


def test_public_exports_and_placeholder_benders_solver_remains_not_solved() -> None:
    cut = BendersCutCandidate(
        "cut-1",
        BendersCutType.FEASIBILITY,
        {"x": 1.0},
        ConstraintSense.LE,
        1.0,
        "subproblem",
        0,
    )

    assert cut.cut_type == BendersCutType.FEASIBILITY
    assert BendersSolver().solve(Model(name="benders-placeholder")).status == (
        SolverStatus.NOT_SOLVED
    )
