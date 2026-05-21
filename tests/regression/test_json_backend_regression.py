import json
from pathlib import Path
from typing import Any

import pytest

from silo.cli.main import main
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.io.json_reader import read_json_model
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

EXAMPLE_ROOT = Path("examples/json")
SOLUTION_JSON_FIELDS = {
    "status",
    "objective_value",
    "primal_values",
    "slack_values",
    "dual_values",
    "reduced_costs",
    "basis_status",
    "message",
}
EXAMPLE_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "production.json": {
        "status": SolverStatus.OPTIMAL,
        "objective_value": 21.0,
        "unique_primal": {"x1": 2.0, "x2": 3.0},
    },
    "ge_row.json": {
        "status": SolverStatus.OPTIMAL,
        "objective_value": 5.0,
        "unique_primal": {"x": 5.0},
    },
    "equality_row.json": {
        "status": SolverStatus.OPTIMAL,
        "objective_value": 4.0,
        "degenerate": True,
        "binding_slacks": {"balance": 0.0},
    },
    "infeasible.json": {
        "status": SolverStatus.INFEASIBLE,
    },
    "fixed_var_recovery.json": {
        "status": SolverStatus.ERROR,
    },
    "presolve_infeasible_after_fixed.json": {
        "status": SolverStatus.ERROR,
    },
    "repeated_empty_row.json": {
        "status": SolverStatus.ERROR,
    },
}


def test_all_json_examples_have_backend_expectations() -> None:
    example_names = {path.name for path in EXAMPLE_ROOT.glob("*.json")}

    assert example_names
    assert example_names == set(EXAMPLE_EXPECTATIONS)


@pytest.mark.parametrize("example_name", sorted(EXAMPLE_EXPECTATIONS))
def test_tableau_and_revised_backends_match_json_examples(example_name: str) -> None:
    expectation = EXAMPLE_EXPECTATIONS[example_name]
    model = read_json_model(EXAMPLE_ROOT / example_name)
    tableau, revised = _solve_with_both_backends(EXAMPLE_ROOT / example_name)

    expected_status = expectation["status"]
    assert tableau.status == revised.status == expected_status
    assert tableau.dual_values == revised.dual_values == {}

    if expected_status != SolverStatus.OPTIMAL:
        return

    expected_objective = expectation["objective_value"]
    assert tableau.objective_value == pytest.approx(expected_objective)
    assert revised.objective_value == pytest.approx(expected_objective)
    assert tableau.objective_value == pytest.approx(revised.objective_value)

    if expectation.get("degenerate"):
        _assert_solution_feasible(model, tableau)
        _assert_solution_feasible(model, revised)
        for name, expected_slack in expectation["binding_slacks"].items():
            assert tableau.slack_values[name] == pytest.approx(expected_slack)
            assert revised.slack_values[name] == pytest.approx(expected_slack)
        return

    expected_primal = expectation["unique_primal"]
    _assert_close_mapping(tableau.primal_values, expected_primal)
    _assert_close_mapping(revised.primal_values, expected_primal)
    _assert_close_mapping(tableau.primal_values, revised.primal_values)
    _assert_close_mapping(tableau.slack_values, revised.slack_values)


def test_reduced_cost_sign_parity_for_deterministic_model() -> None:
    tableau = TableauSimplexSolver().solve(_reduced_cost_sign_model())
    revised = RevisedSimplexSolver().solve(_reduced_cost_sign_model())

    assert tableau.status == revised.status == SolverStatus.OPTIMAL
    assert tableau.primal_values == {"x": pytest.approx(1.0), "y": pytest.approx(0.0)}
    assert revised.primal_values == {"x": pytest.approx(1.0), "y": pytest.approx(0.0)}
    assert tableau.reduced_costs == revised.reduced_costs
    assert tableau.reduced_costs == {"x": pytest.approx(0.0), "y": pytest.approx(-1.0)}
    assert tableau.dual_values == revised.dual_values == {}


@pytest.mark.parametrize("solver_name", ("tableau", "revised"))
def test_cli_backend_regression_production(capsys, solver_name: str) -> None:
    exit_code = main(
        ["solve", str(EXAMPLE_ROOT / "production.json"), "--solver", solver_name]
    )
    payload = _json_stdout(capsys)

    assert exit_code == 0
    _assert_json_solution_fields(payload)
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)


@pytest.mark.parametrize("solver_name", ("tableau", "revised"))
def test_cli_backend_regression_infeasible(capsys, solver_name: str) -> None:
    exit_code = main(
        ["solve", str(EXAMPLE_ROOT / "infeasible.json"), "--solver", solver_name]
    )
    payload = _json_stdout(capsys)

    assert exit_code == 1
    _assert_json_solution_fields(payload)
    assert payload["status"] == "infeasible"


def test_cli_backends_return_same_solution_json_schema(capsys) -> None:
    payloads = []
    for solver_name in ("tableau", "revised"):
        exit_code = main(
            ["solve", str(EXAMPLE_ROOT / "production.json"), "--solver", solver_name]
        )
        payload = _json_stdout(capsys)
        assert exit_code == 0
        payloads.append(payload)

    assert set(payloads[0]) == set(payloads[1]) == SOLUTION_JSON_FIELDS


def _solve_with_both_backends(path: Path) -> tuple[Solution, Solution]:
    model = read_json_model(path)
    return TableauSimplexSolver().solve(model), RevisedSimplexSolver().solve(model)


def _assert_close_mapping(actual: dict[str, float], expected: dict[str, float]) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        assert actual[key] == pytest.approx(expected_value)


def _assert_solution_feasible(model: Model, solution: Solution) -> None:
    assert set(solution.primal_values) == set(model.variable_names())
    for constraint in model.constraints:
        activity = sum(
            coefficient * solution.primal_values[variable_name]
            for variable_name, coefficient in constraint.coefficients.items()
        )
        if constraint.sense == ConstraintSense.LE:
            assert activity <= constraint.rhs + 1e-9
        elif constraint.sense == ConstraintSense.GE:
            assert activity >= constraint.rhs - 1e-9
        else:
            assert activity == pytest.approx(constraint.rhs)


def _assert_json_solution_fields(payload: dict[str, object]) -> None:
    assert set(payload) == SOLUTION_JSON_FIELDS


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)


def _reduced_cost_sign_model() -> Model:
    model = Model(name="reduced_cost_sign")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="x_capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="y_capacity",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 1.0, "y": -1.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model
