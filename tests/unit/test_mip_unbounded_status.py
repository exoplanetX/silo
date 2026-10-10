import json

import pytest

from silo.cli.main import main
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.mip.branch_and_bound import BranchAndBoundSolver


def _model(rhs: float, sense: ConstraintSense = ConstraintSense.EQ) -> Model:
    return Model(
        name="unbounded_relaxation",
        variables=[Variable("x", Bounds(0.0, 1.0), VariableType.BINARY), Variable("y")],
        constraints=[Constraint("restrict_x", {"x": 1.0}, sense, rhs)],
        objective=Objective({"y": 1.0}, OptimizationSense.MAXIMIZE, constant=7.0),
    )


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
@pytest.mark.parametrize("rhs", [0.5, 1e-7])
def test_integer_infeasibility_is_not_hidden_by_unbounded_relaxation(backend, rhs) -> None:
    result = BranchAndBoundSolver(lp_solver=backend()).solve_with_details(_model(rhs))
    assert result.solution.status == SolverStatus.INFEASIBLE
    assert result.nodes_processed == 3
    assert result.incumbent_value is None
    assert result.best_bound is None


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_integer_feasible_unbounded_relaxation_proves_mip_unbounded(backend) -> None:
    model = _model(0.0)
    result = BranchAndBoundSolver(lp_solver=backend()).solve_with_details(model)
    assert result.solution.status == SolverStatus.UNBOUNDED
    assert result.nodes_processed == 1
    assert model.objective.coefficients == {"y": 1.0}
    assert model.objective.constant == 7.0


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_fractional_feasibility_point_branches_before_proving_unbounded(backend) -> None:
    result = BranchAndBoundSolver(lp_solver=backend()).solve_with_details(
        _model(0.5, ConstraintSense.GE)
    )
    assert result.solution.status == SolverStatus.UNBOUNDED
    assert result.nodes_processed == 3
    assert result.nodes_created == 3
    assert result.incumbent_value is None
    assert result.log[0].branching_variable == "x"
    assert result.log[0].lp_status == SolverStatus.UNBOUNDED
    assert result.log[0].lp_objective is None


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_node_limit_after_fractional_probe_has_no_finite_bound_or_incumbent(backend) -> None:
    result = BranchAndBoundSolver(lp_solver=backend(), node_limit=1).solve_with_details(
        _model(0.5, ConstraintSense.GE)
    )
    assert result.solution.status == SolverStatus.ITERATION_LIMIT
    assert result.solution.objective_value is None
    assert result.best_bound is None
    assert result.incumbent_value is None
    assert result.nodes_created == 3


class _ProbeBackend:
    def __init__(self, response: Solution) -> None:
        self.response = response
        self.calls = []

    def solve(self, model: Model) -> Solution:
        self.calls.append(model)
        if len(self.calls) == 1:
            return Solution(status=SolverStatus.UNBOUNDED)
        return self.response


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (SolverStatus.ERROR, SolverStatus.ERROR),
        (SolverStatus.NUMERICAL_ISSUE, SolverStatus.NUMERICAL_ISSUE),
        (SolverStatus.INFEASIBLE, SolverStatus.NUMERICAL_ISSUE),
        (SolverStatus.UNBOUNDED, SolverStatus.NUMERICAL_ISSUE),
        (SolverStatus.ITERATION_LIMIT, SolverStatus.ERROR),
    ],
)
def test_probe_failure_does_not_claim_mip_unbounded(status, expected) -> None:
    backend = _ProbeBackend(Solution(status=status, message="probe stopped"))
    result = BranchAndBoundSolver(lp_solver=backend).solve_with_details(_model(0.5))
    assert result.solution.status == expected
    assert result.incumbent_value is None
    original, probe = backend.calls
    assert probe.constraints == original.constraints
    assert probe.variables == original.variables
    assert probe.objective.coefficients == {}
    assert probe.objective.constant == 0.0


@pytest.mark.parametrize(
    "values", [{"x": 0.0}, {"x": 0.0, "y": float("nan")}, {"x": 0.0, "y": 0.0}]
)
def test_invalid_probe_primal_is_not_an_unboundedness_witness(values) -> None:
    backend = _ProbeBackend(Solution(status=SolverStatus.OPTIMAL, primal_values=values))
    result = BranchAndBoundSolver(lp_solver=backend).solve_with_details(_model(0.5))
    assert result.solution.status == SolverStatus.NUMERICAL_ISSUE


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
@pytest.mark.parametrize(
    "rhs, sense, expected",
    [
        (0.5, ConstraintSense.EQ, SolverStatus.INFEASIBLE),
        (1.5, ConstraintSense.GE, SolverStatus.UNBOUNDED),
    ],
)
def test_bounded_general_integer_unbounded_relaxation(backend, rhs, sense, expected) -> None:
    model = _model(rhs, sense)
    model.variables[0] = Variable("x", Bounds(0.0, 2.0), VariableType.INTEGER)
    assert BranchAndBoundSolver(lp_solver=backend()).solve(model).status == expected


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_pure_continuous_unbounded_model_keeps_correct_status(backend) -> None:
    model = _model(0.5)
    model.variables[0] = Variable("x")
    assert BranchAndBoundSolver(lp_solver=backend()).solve(model).status == SolverStatus.UNBOUNDED


@pytest.mark.parametrize("backend", ["tableau", "revised"])
@pytest.mark.parametrize("rhs, expected", [(0.5, "infeasible"), (0.0, "unbounded")])
def test_cli_reports_correct_terminal_status_and_details(tmp_path, capsys, backend, rhs, expected):
    path = tmp_path / "status.json"
    path.write_text(
        json.dumps(
            {
                "sense": "maximize",
                "variables": [
                    {"name": "x", "type": "binary", "lower": 0.0, "upper": 1.0},
                    {"name": "y", "lower": 0.0, "upper": None},
                ],
                "constraints": [
                    {"name": "fix_x", "coefficients": {"x": 1.0}, "sense": "=", "rhs": rhs}
                ],
                "objective": {"coefficients": {"y": 1.0}},
            }
        ),
        encoding="utf-8",
    )
    code = main(["mip-solve", str(path), "--lp-solver", backend, "--details", "--node-log"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["solution"]["status"] == expected
    assert payload["diagnostics"]["termination_reason"] == expected
    assert payload["diagnostics"]["best_bound"] is None
    assert payload["diagnostics"]["incumbent_value"] is None
    assert payload["diagnostics"]["relative_gap"] is None
