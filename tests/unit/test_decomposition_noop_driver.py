from dataclasses import FrozenInstanceError
from inspect import signature

import pytest

from silo.core.model import Model
from silo.core.status import SolverStatus
from silo.decomposition import (
    BendersSolver,
    ColumnGenerationSolver,
    DecompositionMethod,
    DecompositionTerminationReason,
    NoOpDecompositionDriver,
)


def test_benders_noop_driver_returns_one_deterministic_iteration() -> None:
    driver = NoOpDecompositionDriver(
        method=DecompositionMethod.BENDERS,
        message="dry run",
        metadata={"z": 2, "a": "alpha"},
    )

    summary = driver.run()

    assert summary.method == DecompositionMethod.BENDERS
    assert summary.iteration_count == 1
    assert summary.termination_reason == DecompositionTerminationReason.NO_CUT_GENERATED
    assert summary.message == "dry run"
    assert summary.metadata == (("a", "alpha"), ("z", 2))
    assert summary.final_status is None

    entry = summary.iterations[0]
    assert entry.iteration_id == 0
    assert entry.method == DecompositionMethod.BENDERS
    assert entry.termination_reason == DecompositionTerminationReason.NO_CUT_GENERATED
    assert entry.generated_cut_count == 0
    assert entry.accepted_cut_count == 0
    assert entry.generated_column_count == 0
    assert entry.accepted_column_count == 0
    assert entry.duplicate_count == 0
    assert entry.message == "dry run"
    assert entry.metadata == (("a", "alpha"), ("z", 2))


def test_column_generation_noop_driver_returns_one_deterministic_iteration() -> None:
    driver = NoOpDecompositionDriver(method="column_generation")

    summary = driver.run()

    assert summary.method == DecompositionMethod.COLUMN_GENERATION
    assert summary.iteration_count == 1
    assert summary.termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN
    assert summary.message == "No-op column-generation driver found no improving columns."

    entry = summary.iterations[0]
    assert entry.iteration_id == 0
    assert entry.method == DecompositionMethod.COLUMN_GENERATION
    assert entry.termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN
    assert entry.generated_cut_count == 0
    assert entry.accepted_cut_count == 0
    assert entry.generated_column_count == 0
    assert entry.accepted_column_count == 0
    assert entry.duplicate_count == 0


def test_noop_driver_is_immutable_at_dataclass_boundary() -> None:
    driver = NoOpDecompositionDriver(method=DecompositionMethod.BENDERS)

    with pytest.raises(FrozenInstanceError):
        driver.message = "changed"


def test_rejects_invalid_method_values() -> None:
    with pytest.raises(ValueError, match="DecompositionMethod"):
        NoOpDecompositionDriver(method="bad")


@pytest.mark.parametrize("iteration_limit", [0, -1])
def test_rejects_nonpositive_iteration_limits(iteration_limit: int) -> None:
    with pytest.raises(ValueError, match="iteration limit"):
        NoOpDecompositionDriver(method=DecompositionMethod.BENDERS, iteration_limit=iteration_limit)


@pytest.mark.parametrize("iteration_limit", [True, 1.5])
def test_rejects_noninteger_iteration_limits(iteration_limit: object) -> None:
    with pytest.raises(TypeError, match="iteration limit"):
        NoOpDecompositionDriver(method=DecompositionMethod.BENDERS, iteration_limit=iteration_limit)


def test_rejects_invalid_message_values() -> None:
    with pytest.raises(TypeError, match="message"):
        NoOpDecompositionDriver(method=DecompositionMethod.BENDERS, message=object())


def test_run_output_is_deterministic_across_repeated_calls() -> None:
    driver = NoOpDecompositionDriver(
        method="benders",
        metadata={"run": "noop", "order": 1},
    )

    assert driver.run() == driver.run()


def test_no_model_is_required_to_run_noop_driver() -> None:
    run_signature = signature(NoOpDecompositionDriver.run)
    summary = NoOpDecompositionDriver(method="benders").run()

    assert list(run_signature.parameters) == ["self"]
    assert summary.iteration_count == 1


def test_public_exports_and_placeholder_solvers_remain_not_solved() -> None:
    driver = NoOpDecompositionDriver(method=DecompositionMethod.BENDERS)
    model = Model(name="noop-placeholder")

    assert driver.run().termination_reason == DecompositionTerminationReason.NO_CUT_GENERATED
    assert BendersSolver().solve(model).status == SolverStatus.NOT_SOLVED
    assert ColumnGenerationSolver().solve(model).status == SolverStatus.NOT_SOLVED
