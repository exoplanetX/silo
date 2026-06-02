"""Toy Benders-style fixture example.

This example demonstrates SILO's educational toy Benders driver. The cuts are
precomputed fixture placeholders; they are not validity proofs for arbitrary models.
The example does not call LP or MIP solvers and does not mutate any model object.
"""

from silo.core.enums import ConstraintSense
from silo.decomposition import (
    BendersCutType,
    ToyBendersCutSpec,
    ToyBendersDriver,
    ToyBendersIterationFixture,
)


def build_driver() -> ToyBendersDriver:
    return ToyBendersDriver(
        iterations=(
            ToyBendersIterationFixture(
                cut_specs=(
                    ToyBendersCutSpec(
                        cut_id="toy_cut_1",
                        cut_type=BendersCutType.FEASIBILITY,
                        coefficients={"x_master": 1.0},
                        sense=ConstraintSense.LE,
                        rhs=4.0,
                        source_subproblem="toy_subproblem",
                    ),
                ),
                message="accepted one fixture cut",
            ),
            ToyBendersIterationFixture(
                cut_specs=(),
                message="no fixture cuts remain",
            ),
        ),
        iteration_limit=3,
        message="toy Benders example",
    )


def main() -> None:
    summary = build_driver().run()

    print(
        f"toy_benders termination={summary.termination_reason.value} "
        f"iterations={summary.iteration_count}"
    )
    for entry in summary.iterations:
        print(
            f"iteration={entry.iteration_id} generated_cuts={entry.generated_cut_count} "
            f"accepted_cuts={entry.accepted_cut_count} duplicates={entry.duplicate_count} "
            f"reason={entry.termination_reason.value}"
        )


if __name__ == "__main__":
    main()
