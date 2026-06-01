from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from silo.core.status import SolverStatus
from silo.decomposition import (
    DecompositionIterationLog,
    DecompositionMethod,
    DecompositionRunSummary,
    DecompositionTerminationReason,
)


def test_iteration_log_construction_normalizes_values() -> None:
    cut_ids = ["cut-b", "cut-a"]
    column_ids = ["col-b", "col-a"]
    metadata = {"z": 2, "a": "alpha"}

    entry = DecompositionIterationLog(
        iteration_id=2,
        method="benders",
        master_status="optimal",
        subproblem_status=SolverStatus.INFEASIBLE,
        master_objective=10,
        best_bound=12,
        generated_cut_count=3,
        generated_column_count=4,
        accepted_cut_count=1,
        accepted_column_count=2,
        duplicate_count=1,
        cut_ids=cut_ids,
        column_ids=column_ids,
        termination_reason="no_cut_generated",
        message="stopped",
        metadata=metadata,
    )
    cut_ids.append("cut-c")
    column_ids.append("col-c")
    metadata["a"] = "changed"

    assert entry.iteration_id == 2
    assert entry.method == DecompositionMethod.BENDERS
    assert entry.master_status == SolverStatus.OPTIMAL
    assert entry.subproblem_status == SolverStatus.INFEASIBLE
    assert entry.master_objective == 10.0
    assert entry.best_bound == 12.0
    assert entry.generated_cut_count == 3
    assert entry.generated_column_count == 4
    assert entry.accepted_cut_count == 1
    assert entry.accepted_column_count == 2
    assert entry.duplicate_count == 1
    assert entry.cut_ids == ("cut-a", "cut-b")
    assert entry.column_ids == ("col-a", "col-b")
    assert entry.termination_reason == DecompositionTerminationReason.NO_CUT_GENERATED
    assert entry.metadata == (("a", "alpha"), ("z", 2))


def test_run_summary_construction_sorts_iteration_logs() -> None:
    later = DecompositionIterationLog(
        iteration_id=2,
        method=DecompositionMethod.COLUMN_GENERATION,
    )
    earlier = DecompositionIterationLog(
        iteration_id=1,
        method=DecompositionMethod.COLUMN_GENERATION,
    )

    summary = DecompositionRunSummary(
        method="column_generation",
        iterations=(later, earlier),
        termination_reason="no_improving_column",
        final_status="optimal",
        final_objective=7,
        message="done",
        metadata={"run": "toy"},
    )

    assert summary.method == DecompositionMethod.COLUMN_GENERATION
    assert summary.iterations == (earlier, later)
    assert summary.iteration_count == 2
    assert summary.termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN
    assert summary.final_status == SolverStatus.OPTIMAL
    assert summary.final_objective == 7.0
    assert summary.metadata == (("run", "toy"),)


def test_log_records_are_immutable_at_dataclass_boundary() -> None:
    entry = DecompositionIterationLog(0, DecompositionMethod.BENDERS)
    summary = DecompositionRunSummary(DecompositionMethod.BENDERS, iterations=(entry,))

    with pytest.raises(FrozenInstanceError):
        entry.message = "changed"
    with pytest.raises(FrozenInstanceError):
        summary.message = "changed"


@pytest.mark.parametrize("iteration_id", [-1, True])
def test_rejects_invalid_iteration_ids(iteration_id: int) -> None:
    expected = ValueError if iteration_id == -1 else TypeError
    with pytest.raises(expected, match="iteration id"):
        DecompositionIterationLog(iteration_id, DecompositionMethod.BENDERS)


def test_rejects_invalid_method_values() -> None:
    with pytest.raises(ValueError, match="supported DecompositionMethod"):
        DecompositionIterationLog(0, "unknown")
    with pytest.raises(ValueError, match="supported DecompositionMethod"):
        DecompositionRunSummary("unknown")


def test_rejects_invalid_termination_reasons() -> None:
    with pytest.raises(ValueError, match="supported DecompositionTerminationReason"):
        DecompositionIterationLog(0, DecompositionMethod.BENDERS, termination_reason="bad")
    with pytest.raises(ValueError, match="supported DecompositionTerminationReason"):
        DecompositionRunSummary(DecompositionMethod.BENDERS, termination_reason="bad")


def test_rejects_invalid_solver_statuses() -> None:
    with pytest.raises(ValueError, match="supported SolverStatus"):
        DecompositionIterationLog(
            0,
            DecompositionMethod.BENDERS,
            master_status="bad",
        )
    with pytest.raises(ValueError, match="supported SolverStatus"):
        DecompositionRunSummary(DecompositionMethod.BENDERS, final_status="bad")


@pytest.mark.parametrize("value", [inf, -inf, nan])
def test_rejects_nonfinite_objective_or_bound_values(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        DecompositionIterationLog(
            0,
            DecompositionMethod.BENDERS,
            master_objective=value,
        )
    with pytest.raises(ValueError, match="finite"):
        DecompositionIterationLog(0, DecompositionMethod.BENDERS, best_bound=value)
    with pytest.raises(ValueError, match="finite"):
        DecompositionRunSummary(DecompositionMethod.BENDERS, final_objective=value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"generated_cut_count": -1},
        {"generated_column_count": -1},
        {"accepted_cut_count": -1},
        {"accepted_column_count": -1},
        {"duplicate_count": -1},
    ],
)
def test_rejects_negative_counts(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="must be nonnegative"):
        DecompositionIterationLog(0, DecompositionMethod.BENDERS, **kwargs)


def test_rejects_invalid_cut_and_column_ids() -> None:
    with pytest.raises(ValueError, match="cut ids"):
        DecompositionIterationLog(0, DecompositionMethod.BENDERS, cut_ids=[" "])
    with pytest.raises(TypeError, match="column ids"):
        DecompositionIterationLog(
            0,
            DecompositionMethod.BENDERS,
            column_ids="col-1",
        )


def test_rejects_invalid_run_summary_iterations() -> None:
    with pytest.raises(TypeError, match="iterable"):
        DecompositionRunSummary(
            DecompositionMethod.BENDERS,
            iterations=DecompositionIterationLog(0, DecompositionMethod.BENDERS),
        )
    with pytest.raises(TypeError, match="DecompositionIterationLog"):
        DecompositionRunSummary(DecompositionMethod.BENDERS, iterations=(object(),))
    with pytest.raises(ValueError, match="methods must match"):
        DecompositionRunSummary(
            DecompositionMethod.BENDERS,
            iterations=(
                DecompositionIterationLog(0, DecompositionMethod.COLUMN_GENERATION),
            ),
        )
    with pytest.raises(ValueError, match="unique"):
        DecompositionRunSummary(
            DecompositionMethod.BENDERS,
            iterations=(
                DecompositionIterationLog(0, DecompositionMethod.BENDERS),
                DecompositionIterationLog(0, DecompositionMethod.BENDERS),
            ),
        )


def test_public_exports_and_log_construction_need_no_solver_loops() -> None:
    entry = DecompositionIterationLog(
        0,
        DecompositionMethod.BENDERS,
        termination_reason=DecompositionTerminationReason.NOT_TERMINATED,
    )
    summary = DecompositionRunSummary(DecompositionMethod.BENDERS, iterations=(entry,))

    assert DecompositionMethod.BENDERS.value == "benders"
    assert DecompositionTerminationReason.ITERATION_LIMIT.value == "iteration_limit"
    assert summary.iterations == (entry,)
