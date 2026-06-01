from pathlib import Path

from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.decomposition import (
    BendersSolver,
    ColumnGenerationSolver,
    DecompositionIterationLog,
    DecompositionMethod,
    DecompositionRunSummary,
    DecompositionTerminationReason,
)


def test_placeholder_benders_status_can_be_logged_without_solve_loop() -> None:
    solution = BendersSolver().solve(Model(name="benders-smoke"))

    entry = DecompositionIterationLog(
        iteration_id=0,
        method=DecompositionMethod.BENDERS,
        master_status=solution.status,
        termination_reason=DecompositionTerminationReason.UNSUPPORTED_STATUS,
        message=solution.message,
    )
    summary = DecompositionRunSummary(
        method=DecompositionMethod.BENDERS,
        iterations=(entry,),
        termination_reason=DecompositionTerminationReason.UNSUPPORTED_STATUS,
        final_status=solution.status,
        message=solution.message,
    )

    assert solution.status == SolverStatus.NOT_SOLVED
    assert solution.message == "Benders is not implemented yet."
    assert entry.master_status == SolverStatus.NOT_SOLVED
    assert entry.generated_cut_count == 0
    assert summary.iterations == (entry,)
    assert summary.final_status == SolverStatus.NOT_SOLVED


def test_placeholder_column_generation_status_can_be_logged_without_solve_loop() -> None:
    solution = ColumnGenerationSolver().solve(Model(name="column-generation-smoke"))

    entry = DecompositionIterationLog(
        iteration_id=0,
        method="column_generation",
        master_status=solution.status,
        generated_column_count=0,
        termination_reason="unsupported_status",
        message=solution.message,
    )
    summary = DecompositionRunSummary(
        method="column_generation",
        iterations=(entry,),
        termination_reason="unsupported_status",
        final_status=solution.status,
        message=solution.message,
    )

    assert solution.status == SolverStatus.NOT_SOLVED
    assert solution.message == "Column generation is not implemented yet."
    assert entry.method == DecompositionMethod.COLUMN_GENERATION
    assert entry.generated_column_count == 0
    assert summary.termination_reason == DecompositionTerminationReason.UNSUPPORTED_STATUS
    assert summary.iteration_count == 1


def test_decomposition_logs_are_separate_from_public_solution_schema() -> None:
    solution = Solution(status=SolverStatus.NOT_SOLVED)

    assert "iterations" not in solution.__dataclass_fields__
    assert "termination_reason" not in solution.__dataclass_fields__
    assert "final_status" not in solution.__dataclass_fields__


def test_lower_layers_do_not_import_decomposition() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    lower_layer_packages = ("core", "modeling", "presolve", "lp", "mip")

    for package in lower_layer_packages:
        for path in (repo_root / "src" / "silo" / package).rglob("*.py"):
            text = path.read_text(encoding="utf-8")

            assert "silo.decomposition" not in text
            assert "from silo import decomposition" not in text
