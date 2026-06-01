from inspect import signature
from pathlib import Path

from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.status import SolverStatus
from silo.decomposition import (
    BendersCutType,
    BendersSolver,
    DecompositionTerminationReason,
    ToyBendersCutSpec,
    ToyBendersDriver,
    ToyBendersIterationFixture,
)


def _cut_spec(
    cut_id: str,
    coefficients: dict[str, float] | None = None,
    rhs: float = 1.0,
) -> ToyBendersCutSpec:
    return ToyBendersCutSpec(
        cut_id=cut_id,
        cut_type=BendersCutType.FEASIBILITY,
        coefficients=coefficients or {"x": 1.0},
        sense=ConstraintSense.LE,
        rhs=rhs,
        source_subproblem="toy_subproblem",
    )


def test_toy_benders_accepts_fixture_cuts_then_stops_with_no_cut() -> None:
    driver = ToyBendersDriver(
        iterations=(
            ToyBendersIterationFixture(
                cut_specs=(
                    _cut_spec("cut-b", {"y": 2.0}, 2.0),
                    _cut_spec("cut-a", {"x": 1.0}, 1.0),
                ),
                message="accepted fixture cuts",
                metadata={"stage": "cuts"},
            ),
            ToyBendersIterationFixture(
                cut_specs=(),
                message="no fixture cuts",
                metadata={"stage": "stop"},
            ),
        ),
        iteration_limit=3,
        message="toy benders fixture run",
    )

    summary = driver.run()

    assert summary.termination_reason == DecompositionTerminationReason.NO_CUT_GENERATED
    assert summary.message == "toy benders fixture run"
    assert summary.iteration_count == 2
    assert [entry.iteration_id for entry in summary.iterations] == [0, 1]

    first, second = summary.iterations
    assert first.generated_cut_count == 2
    assert first.accepted_cut_count == 2
    assert first.duplicate_count == 0
    assert first.generated_column_count == 0
    assert first.accepted_column_count == 0
    assert first.cut_ids == ("cut-a", "cut-b")
    assert first.termination_reason == DecompositionTerminationReason.NOT_TERMINATED
    assert first.metadata == (("stage", "cuts"),)

    assert second.generated_cut_count == 0
    assert second.accepted_cut_count == 0
    assert second.duplicate_count == 0
    assert second.generated_column_count == 0
    assert second.accepted_column_count == 0
    assert second.termination_reason == DecompositionTerminationReason.NO_CUT_GENERATED
    assert second.message == "no fixture cuts"
    assert second.metadata == (("stage", "stop"),)


def test_toy_benders_stops_on_duplicate_cut_canonical_key() -> None:
    driver = ToyBendersDriver(
        iterations=(
            ToyBendersIterationFixture(cut_specs=(_cut_spec("cut-1", {"x": 1.0}, 1.0),)),
            ToyBendersIterationFixture(cut_specs=(_cut_spec("cut-2", {"x": 1.0}, 1.0),)),
        ),
        iteration_limit=3,
    )

    summary = driver.run()

    assert summary.termination_reason == DecompositionTerminationReason.DUPLICATE_CANDIDATE
    assert summary.iteration_count == 2

    first, second = summary.iterations
    assert first.generated_cut_count == 1
    assert first.accepted_cut_count == 1
    assert first.duplicate_count == 0
    assert first.termination_reason == DecompositionTerminationReason.NOT_TERMINATED

    assert second.generated_cut_count == 1
    assert second.accepted_cut_count == 0
    assert second.duplicate_count == 1
    assert second.cut_ids == ("cut-2",)
    assert second.generated_column_count == 0
    assert second.termination_reason == DecompositionTerminationReason.DUPLICATE_CANDIDATE


def test_toy_benders_stops_on_iteration_limit() -> None:
    driver = ToyBendersDriver(
        iterations=(
            ToyBendersIterationFixture(cut_specs=(_cut_spec("cut-1", {"x": 1.0}, 1.0),)),
            ToyBendersIterationFixture(cut_specs=(_cut_spec("cut-2", {"y": 1.0}, 1.0),)),
        ),
        iteration_limit=1,
    )

    summary = driver.run()

    assert summary.termination_reason == DecompositionTerminationReason.ITERATION_LIMIT
    assert summary.iteration_count == 1
    entry = summary.iterations[0]
    assert entry.iteration_id == 0
    assert entry.generated_cut_count == 1
    assert entry.accepted_cut_count == 1
    assert entry.duplicate_count == 0
    assert entry.generated_column_count == 0
    assert entry.accepted_column_count == 0
    assert entry.termination_reason == DecompositionTerminationReason.ITERATION_LIMIT


def test_toy_benders_run_output_is_deterministic_and_defensively_copies_fixture_data() -> None:
    coefficients = {"y": 2.0, "x": 1.0}
    cut_spec = _cut_spec("cut-1", coefficients, 3.0)
    coefficients["x"] = 99.0
    driver = ToyBendersDriver(
        iterations=(
            ToyBendersIterationFixture(cut_specs=(cut_spec,)),
            ToyBendersIterationFixture(cut_specs=()),
        ),
        iteration_limit=3,
    )

    assert cut_spec.coefficients == (("x", 1.0), ("y", 2.0))
    assert driver.run() == driver.run()


def test_toy_benders_requires_no_model_or_solver_input() -> None:
    driver_signature = signature(ToyBendersDriver)
    run_signature = signature(ToyBendersDriver.run)
    driver = ToyBendersDriver(
        iterations=(ToyBendersIterationFixture(cut_specs=()),),
        iteration_limit=1,
    )

    assert "model" not in driver_signature.parameters
    assert list(run_signature.parameters) == ["self"]
    assert driver.run().termination_reason == DecompositionTerminationReason.NO_CUT_GENERATED


def test_public_exports_and_placeholder_benders_solver_remains_not_solved() -> None:
    assert ToyBendersCutSpec
    assert ToyBendersIterationFixture
    assert ToyBendersDriver
    assert BendersSolver().solve(Model(name="toy-benders-placeholder")).status == (
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
