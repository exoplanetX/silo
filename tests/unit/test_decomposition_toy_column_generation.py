from inspect import signature
from pathlib import Path

from silo.core.enums import OptimizationSense
from silo.core.model import Model
from silo.core.status import SolverStatus
from silo.decomposition import (
    ColumnGenerationSolver,
    DecompositionTerminationReason,
    ToyColumnCandidateSpec,
    ToyColumnGenerationDriver,
    ToyColumnGenerationIterationFixture,
)


def _column_spec(
    column_id: str,
    *,
    variable_name: str = "route",
    objective_coefficient: float = 7.0,
    row_coefficients: dict[str, float] | None = None,
    reduced_cost: float = -0.5,
) -> ToyColumnCandidateSpec:
    return ToyColumnCandidateSpec(
        column_id=column_id,
        variable_name=variable_name,
        objective_coefficient=objective_coefficient,
        row_coefficients=row_coefficients or {"demand": 1.0},
        reduced_cost=reduced_cost,
        source_pricing_subproblem="toy_pricing",
    )


def test_toy_column_generation_minimization_accepts_columns_then_stops() -> None:
    driver = ToyColumnGenerationDriver(
        iterations=(
            ToyColumnGenerationIterationFixture(
                column_specs=(
                    _column_spec(
                        "col-b",
                        variable_name="route_b",
                        row_coefficients={"demand-b": 1.0},
                        reduced_cost=-0.3,
                    ),
                    _column_spec(
                        "col-a",
                        variable_name="route_a",
                        row_coefficients={"demand-a": 1.0},
                        reduced_cost=-0.7,
                    ),
                ),
                message="accepted fixture columns",
                metadata={"stage": "columns"},
            ),
            ToyColumnGenerationIterationFixture(
                column_specs=(_column_spec("col-c", reduced_cost=0.0),),
                message="no improving fixture columns",
                metadata={"stage": "stop"},
            ),
        ),
        objective_sense=OptimizationSense.MINIMIZE,
        iteration_limit=3,
        message="toy column fixture run",
    )

    summary = driver.run()

    assert summary.termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN
    assert summary.message == "toy column fixture run"
    assert summary.iteration_count == 2
    assert [entry.iteration_id for entry in summary.iterations] == [0, 1]

    first, second = summary.iterations
    assert first.generated_column_count == 2
    assert first.accepted_column_count == 2
    assert first.duplicate_count == 0
    assert first.generated_cut_count == 0
    assert first.accepted_cut_count == 0
    assert first.column_ids == ("col-a", "col-b")
    assert first.termination_reason == DecompositionTerminationReason.NOT_TERMINATED
    assert first.metadata == (("stage", "columns"),)

    assert second.generated_column_count == 1
    assert second.accepted_column_count == 0
    assert second.duplicate_count == 0
    assert second.generated_cut_count == 0
    assert second.accepted_cut_count == 0
    assert second.termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN
    assert second.message == "no improving fixture columns"
    assert second.metadata == (("stage", "stop"),)


def test_toy_column_generation_maximization_uses_reduced_cost_convention() -> None:
    driver = ToyColumnGenerationDriver(
        iterations=(
            ToyColumnGenerationIterationFixture(
                column_specs=(_column_spec("col-1", reduced_cost=0.2),)
            ),
            ToyColumnGenerationIterationFixture(
                column_specs=(_column_spec("col-2", reduced_cost=-0.2),)
            ),
        ),
        objective_sense="maximize",
        iteration_limit=3,
    )

    summary = driver.run()

    assert summary.termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN
    first, second = summary.iterations
    assert first.generated_column_count == 1
    assert first.accepted_column_count == 1
    assert first.termination_reason == DecompositionTerminationReason.NOT_TERMINATED
    assert second.generated_column_count == 1
    assert second.accepted_column_count == 0
    assert second.termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN


def test_toy_column_generation_stops_on_duplicate_column_canonical_key() -> None:
    driver = ToyColumnGenerationDriver(
        iterations=(
            ToyColumnGenerationIterationFixture(
                column_specs=(
                    _column_spec(
                        "col-1",
                        variable_name="route",
                        row_coefficients={"row-b": 2.0, "row-a": 1.0},
                        reduced_cost=-0.5,
                    ),
                )
            ),
            ToyColumnGenerationIterationFixture(
                column_specs=(
                    _column_spec(
                        "col-2",
                        variable_name="route",
                        row_coefficients={"row-a": 1.0, "row-b": 2.0},
                        reduced_cost=-0.1,
                    ),
                )
            ),
        ),
        objective_sense=OptimizationSense.MINIMIZE,
        iteration_limit=3,
    )

    summary = driver.run()

    assert summary.termination_reason == DecompositionTerminationReason.DUPLICATE_CANDIDATE
    assert summary.iteration_count == 2

    first, second = summary.iterations
    assert first.generated_column_count == 1
    assert first.accepted_column_count == 1
    assert first.duplicate_count == 0
    assert first.termination_reason == DecompositionTerminationReason.NOT_TERMINATED

    assert second.generated_column_count == 1
    assert second.accepted_column_count == 0
    assert second.duplicate_count == 1
    assert second.column_ids == ("col-2",)
    assert second.generated_cut_count == 0
    assert second.accepted_cut_count == 0
    assert second.termination_reason == DecompositionTerminationReason.DUPLICATE_CANDIDATE


def test_toy_column_generation_stops_on_iteration_limit() -> None:
    driver = ToyColumnGenerationDriver(
        iterations=(
            ToyColumnGenerationIterationFixture(
                column_specs=(
                    _column_spec("col-1", variable_name="route_a", reduced_cost=-0.5),
                )
            ),
            ToyColumnGenerationIterationFixture(
                column_specs=(
                    _column_spec("col-2", variable_name="route_b", reduced_cost=-0.5),
                )
            ),
        ),
        objective_sense="minimize",
        iteration_limit=1,
    )

    summary = driver.run()

    assert summary.termination_reason == DecompositionTerminationReason.ITERATION_LIMIT
    assert summary.iteration_count == 1
    entry = summary.iterations[0]
    assert entry.iteration_id == 0
    assert entry.generated_column_count == 1
    assert entry.accepted_column_count == 1
    assert entry.duplicate_count == 0
    assert entry.generated_cut_count == 0
    assert entry.accepted_cut_count == 0
    assert entry.termination_reason == DecompositionTerminationReason.ITERATION_LIMIT


def test_toy_column_generation_run_output_is_deterministic_and_copies_fixture_data() -> None:
    row_coefficients = {"row-b": 2.0, "row-a": 1.0}
    column_spec = _column_spec("col-1", row_coefficients=row_coefficients)
    row_coefficients["row-a"] = 99.0
    driver = ToyColumnGenerationDriver(
        iterations=(
            ToyColumnGenerationIterationFixture(column_specs=(column_spec,)),
            ToyColumnGenerationIterationFixture(column_specs=()),
        ),
        objective_sense=OptimizationSense.MINIMIZE,
        iteration_limit=3,
    )

    assert column_spec.row_coefficients == (("row-a", 1.0), ("row-b", 2.0))
    assert driver.run() == driver.run()


def test_toy_column_generation_requires_no_model_or_solver_input() -> None:
    driver_signature = signature(ToyColumnGenerationDriver)
    run_signature = signature(ToyColumnGenerationDriver.run)
    driver = ToyColumnGenerationDriver(
        iterations=(ToyColumnGenerationIterationFixture(column_specs=()),),
        objective_sense=OptimizationSense.MINIMIZE,
        iteration_limit=1,
    )

    assert "model" not in driver_signature.parameters
    assert list(run_signature.parameters) == ["self"]
    assert driver.run().termination_reason == DecompositionTerminationReason.NO_IMPROVING_COLUMN


def test_public_exports_and_placeholder_column_generation_solver_remains_not_solved() -> None:
    assert ToyColumnCandidateSpec
    assert ToyColumnGenerationIterationFixture
    assert ToyColumnGenerationDriver
    assert ColumnGenerationSolver().solve(Model(name="toy-column-placeholder")).status == (
        SolverStatus.NOT_SOLVED
    )


def test_lower_layers_still_do_not_import_decomposition() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    lower_layer_packages = ("core", "modeling", "presolve", "lp", "mip")

    for package in lower_layer_packages:
        for path in (repo_root / "src" / "silo" / package).rglob("*.py"):
            text = path.read_text(encoding="utf-8")

            assert "silo.decomposition" not in text
            assert "from silo import decomposition" not in text
