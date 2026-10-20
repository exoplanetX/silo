"""Two-round resource-feasible reference CG; run from the repository root."""

from silo.core.enums import ConstraintSense as S
from silo.decomposition import (
    DagArc,
    DagColumnGenerationProblem,
    DagColumnGenerationStatus,
    DagMasterRow,
    DagPricingProblem,
    ResourceDagPricingProblem,
    solve_resource_dag_column_generation,
)
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver


def main():
    graph = DagPricingProblem(("s", "u", "t"), (
        DagArc("a", "s", "u", 4), DagArc("b", "s", "u", 1, {"R": 1}),
        DagArc("c", "s", "u", 6, {"R": 2}), DagArc("d", "s", "u", -10, {"R": 0.5}),
        DagArc("z", "u", "t", 0)), "s", "t", ("conv", "R"),
        base_coefficients={"conv": 1})
    problem = DagColumnGenerationProblem(graph, (DagMasterRow("conv", S.EQ, 1),
        DagMasterRow("R", S.EQ, 0.5)), "conv", (("a", "z"), ("c", "z")))
    resources = ResourceDagPricingProblem(graph, (2,), {
        "a": (0,), "b": (1,), "c": (0,), "d": (2,), "z": (1,)})
    for name, solver, reuse in (("revised", RevisedSimplexSolver(), False),
                                ("tableau", TableauSimplexSolver(), False),
                                ("reuse", RevisedSimplexSolver(), True)):
        result = solve_resource_dag_column_generation(problem, resources, solver=solver,
                                                      reoptimize_rmp=reuse)
        assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED
        assert [r.master_result.objective_value for r in result.iterations] == [4.5, 2.5]
        assert [r.rho for r in result.iterations] == [-4, 0]
        assert result.iterations[0].accepted_path == ("b", "z")
        assert ("d", "z") not in result.column_paths.values()
        print(name, "objectives=[4.5, 2.5] prices=[-4, 0]", [
            None if r.rmp_reoptimization is None else r.rmp_reoptimization.used_warm_start
            for r in result.iterations])


if __name__ == "__main__":
    main()
