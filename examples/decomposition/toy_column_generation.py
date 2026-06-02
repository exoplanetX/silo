"""Toy column-generation-style fixture example.

This example uses SILO's educational toy column-generation driver. Reduced-cost
conventions are relative to objective sense: minimization accepts negative reduced
cost below tolerance, while maximization accepts positive reduced cost above tolerance.
The example does not solve a restricted master problem, call LP/MIP solvers, or claim
branch-and-price behavior.
"""

from silo.core.enums import OptimizationSense
from silo.decomposition import (
    ToyColumnCandidateSpec,
    ToyColumnGenerationDriver,
    ToyColumnGenerationIterationFixture,
)


def build_driver() -> ToyColumnGenerationDriver:
    return ToyColumnGenerationDriver(
        iterations=(
            ToyColumnGenerationIterationFixture(
                column_specs=(
                    ToyColumnCandidateSpec(
                        column_id="toy_column_1",
                        variable_name="route_a",
                        objective_coefficient=7.0,
                        row_coefficients={"customer_a": 1.0, "customer_b": 1.0},
                        reduced_cost=-0.5,
                        source_pricing_subproblem="toy_pricing",
                    ),
                ),
                message="accepted one fixture column",
            ),
            ToyColumnGenerationIterationFixture(
                column_specs=(
                    ToyColumnCandidateSpec(
                        column_id="toy_column_2",
                        variable_name="route_b",
                        objective_coefficient=6.0,
                        row_coefficients={"customer_a": 1.0},
                        reduced_cost=0.0,
                        source_pricing_subproblem="toy_pricing",
                    ),
                ),
                message="no improving fixture columns remain",
            ),
        ),
        objective_sense=OptimizationSense.MINIMIZE,
        iteration_limit=3,
        message="toy column-generation example",
    )


def main() -> None:
    summary = build_driver().run()

    print(
        f"toy_column_generation termination={summary.termination_reason.value} "
        f"iterations={summary.iteration_count}"
    )
    for entry in summary.iterations:
        print(
            f"iteration={entry.iteration_id} "
            f"generated_columns={entry.generated_column_count} "
            f"accepted_columns={entry.accepted_column_count} "
            f"duplicates={entry.duplicate_count} reason={entry.termination_reason.value}"
        )


if __name__ == "__main__":
    main()
