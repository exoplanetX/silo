from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from silo.core.enums import OptimizationSense
from silo.core.model import Model
from silo.core.status import SolverStatus
from silo.decomposition import ColumnCandidate, ColumnGenerationSolver


def test_column_candidate_construction_normalizes_values() -> None:
    row_coefficients = {"row-b": 2, " row-a ": 1.5}

    candidate = ColumnCandidate(
        column_id=" col-1 ",
        variable_name=" route_a ",
        objective_coefficient=7,
        row_coefficients=row_coefficients,
        reduced_cost=-0.5,
        source_pricing_subproblem=" pricing-a ",
        iteration_id=2,
        tolerance=1e-7,
        message="fixture column",
    )
    row_coefficients["row-b"] = 99.0

    assert candidate.column_id == "col-1"
    assert candidate.variable_name == "route_a"
    assert candidate.objective_coefficient == 7.0
    assert candidate.row_coefficients == (("row-a", 1.5), ("row-b", 2.0))
    assert candidate.reduced_cost == -0.5
    assert candidate.source_pricing_subproblem == "pricing-a"
    assert candidate.iteration_id == 2
    assert candidate.tolerance == 1e-7
    assert candidate.message == "fixture column"


def test_column_candidate_is_immutable() -> None:
    candidate = ColumnCandidate(
        "col-1",
        "x_col",
        1.0,
        {"row": 1.0},
        -0.1,
        "pricing",
        0,
    )

    with pytest.raises(FrozenInstanceError):
        candidate.reduced_cost = 0.0


@pytest.mark.parametrize("column_id", ["", " "])
def test_rejects_invalid_column_ids(column_id: str) -> None:
    with pytest.raises(ValueError, match="column id"):
        ColumnCandidate(column_id, "x", 1.0, {"row": 1.0}, -0.1, "pricing", 0)


@pytest.mark.parametrize("variable_name", ["", " "])
def test_rejects_invalid_variable_names(variable_name: str) -> None:
    with pytest.raises(ValueError, match="variable name"):
        ColumnCandidate("col-1", variable_name, 1.0, {"row": 1.0}, -0.1, "pricing", 0)


def test_rejects_empty_row_coefficient_mapping() -> None:
    with pytest.raises(ValueError, match="row coefficients must not be empty"):
        ColumnCandidate("col-1", "x", 1.0, {}, -0.1, "pricing", 0)


def test_rejects_empty_row_names() -> None:
    with pytest.raises(ValueError, match="row name"):
        ColumnCandidate("col-1", "x", 1.0, {" ": 1.0}, -0.1, "pricing", 0)


@pytest.mark.parametrize("coefficient", [inf, -inf, nan])
def test_rejects_nonfinite_row_coefficients(coefficient: float) -> None:
    with pytest.raises(ValueError, match="row coefficient must be finite"):
        ColumnCandidate("col-1", "x", 1.0, {"row": coefficient}, -0.1, "pricing", 0)


def test_rejects_all_zero_row_coefficient_vector() -> None:
    with pytest.raises(ValueError, match="nonzero"):
        ColumnCandidate("col-1", "x", 1.0, {"row-a": 0.0, "row-b": 0.0}, -0.1, "pricing", 0)


@pytest.mark.parametrize("objective_coefficient", [inf, -inf, nan])
def test_rejects_nonfinite_objective_coefficients(objective_coefficient: float) -> None:
    with pytest.raises(ValueError, match="objective coefficient must be finite"):
        ColumnCandidate("col-1", "x", objective_coefficient, {"row": 1.0}, -0.1, "pricing", 0)


@pytest.mark.parametrize("reduced_cost", [inf, -inf, nan])
def test_rejects_nonfinite_reduced_costs(reduced_cost: float) -> None:
    with pytest.raises(ValueError, match="reduced cost must be finite"):
        ColumnCandidate("col-1", "x", 1.0, {"row": 1.0}, reduced_cost, "pricing", 0)


@pytest.mark.parametrize("source", ["", " "])
def test_rejects_invalid_source_pricing_subproblem_labels(source: str) -> None:
    with pytest.raises(ValueError, match="source pricing subproblem"):
        ColumnCandidate("col-1", "x", 1.0, {"row": 1.0}, -0.1, source, 0)


@pytest.mark.parametrize("iteration_id", [-1, True])
def test_rejects_invalid_iteration_ids(iteration_id: int) -> None:
    expected_error = ValueError if iteration_id == -1 else TypeError
    with pytest.raises(expected_error, match="iteration id"):
        ColumnCandidate("col-1", "x", 1.0, {"row": 1.0}, -0.1, "pricing", iteration_id)


@pytest.mark.parametrize("tolerance", [0.0, -1.0, inf, nan])
def test_rejects_nonpositive_or_nonfinite_tolerances(tolerance: float) -> None:
    with pytest.raises(ValueError, match="tolerance"):
        ColumnCandidate(
            "col-1",
            "x",
            1.0,
            {"row": 1.0},
            -0.1,
            "pricing",
            0,
            tolerance=tolerance,
        )


def test_rejects_invalid_message_values() -> None:
    with pytest.raises(TypeError, match="message"):
        ColumnCandidate(
            "col-1",
            "x",
            1.0,
            {"row": 1.0},
            -0.1,
            "pricing",
            0,
            message=object(),
        )


@pytest.mark.parametrize(
    ("reduced_cost", "sense", "expected"),
    [
        (-1.1e-6, OptimizationSense.MINIMIZE, True),
        (-1e-9, OptimizationSense.MINIMIZE, False),
        (0.0, OptimizationSense.MINIMIZE, False),
        (1.1e-6, OptimizationSense.MINIMIZE, False),
        (1.1e-6, OptimizationSense.MAXIMIZE, True),
        (1e-9, OptimizationSense.MAXIMIZE, False),
        (0.0, OptimizationSense.MAXIMIZE, False),
        (-1.1e-6, OptimizationSense.MAXIMIZE, False),
    ],
)
def test_reduced_cost_improvement_convention(
    reduced_cost: float,
    sense: OptimizationSense,
    expected: bool,
) -> None:
    candidate = ColumnCandidate(
        "col-1",
        "x",
        1.0,
        {"row": 1.0},
        reduced_cost,
        "pricing",
        0,
        tolerance=1e-9,
    )

    assert candidate.is_improving_for(sense) is expected
    assert candidate.is_improving_for(sense.value) is expected


def test_rejects_invalid_objective_sense_in_reduced_cost_check() -> None:
    candidate = ColumnCandidate("col-1", "x", 1.0, {"row": 1.0}, -0.1, "pricing", 0)

    with pytest.raises(ValueError, match="OptimizationSense"):
        candidate.is_improving_for("bad")


def test_canonical_key_ignores_nonmathematical_metadata_and_input_order() -> None:
    first = ColumnCandidate(
        "col-a",
        "route",
        7.0,
        {"row-a": 1.0, "row-b": 2.0},
        -0.5,
        "pricing-a",
        0,
        tolerance=1e-7,
        message="first",
    )
    second = ColumnCandidate(
        "col-b",
        "route",
        7.0,
        {"row-b": 2.0, "row-a": 1.0},
        -0.1,
        "pricing-b",
        3,
        tolerance=1e-5,
        message="second",
    )

    assert first.canonical_key() == second.canonical_key()


def test_canonical_key_respects_explicit_row_order() -> None:
    candidate = ColumnCandidate(
        "col-a",
        "route",
        7.0,
        {"row-a": 1.0, "row-b": 2.0, "row-c": 3.0},
        -0.5,
        "pricing",
        1,
    )

    assert candidate.canonical_key(row_order=("row-c", "row-a")) == (
        "column",
        "route",
        7.0,
        (("row-c", 3.0), ("row-a", 1.0), ("row-b", 2.0)),
    )


def test_public_exports_and_placeholder_column_generation_solver_remains_not_solved() -> None:
    candidate = ColumnCandidate("col-1", "x", 1.0, {"row": 1.0}, -0.1, "pricing", 0)

    assert candidate.variable_name == "x"
    assert ColumnGenerationSolver().solve(Model(name="column-placeholder")).status == (
        SolverStatus.NOT_SOLVED
    )
