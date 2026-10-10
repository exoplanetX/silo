"""Finite correctness evidence independent of native solver internals."""

from dataclasses import replace
from fractions import Fraction
from itertools import product

import pytest

from silo.cli.main import _solve_model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.mip.branch_and_bound import BranchAndBoundSolver
from tests.verification.oracles import (
    LP_CASES,
    MIP_CASES,
    Case,
    check_solution,
    enumerate_integer_optimum,
    make_model,
)


@pytest.mark.parametrize("case", LP_CASES, ids=lambda case: case.name)
@pytest.mark.parametrize("backend", ["tableau", "revised"])
@pytest.mark.parametrize("presolve", [False, True])
def test_analytical_lp(case, backend, presolve):
    check_solution(case, _solve_model(make_model(case), backend, presolve), case.status, case.value)


@pytest.mark.parametrize("case", MIP_CASES, ids=lambda case: case.name)
@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_enumerated_integer_models(case, backend):
    status, value = enumerate_integer_optimum(case)
    # Hand answers cross-check the enumerator itself.
    assert status == case.status
    assert value == (None if case.value is None else Fraction(case.value))
    check_solution(case, BranchAndBoundSolver(lp_solver=backend()).solve(make_model(case)),
                   status, value)


@pytest.mark.parametrize("rhs, sense, objective", product(
    [0, 1, 3, 5], ["<=", ">=", "="], [(1, 2), (-1, 1), (0, 0)]
))
@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_finite_integer_grid(rhs, sense, objective, backend):
    case = Case("finite-grid", objective, (((2, 1), sense, rhs),),
                "enumerate", constant=-3, upper=(2, 2))
    status, value = enumerate_integer_optimum(case)
    check_solution(case, BranchAndBoundSolver(lp_solver=backend()).solve(make_model(case)),
                   status, value)


@pytest.mark.parametrize("case", LP_CASES, ids=lambda case: case.name)
@pytest.mark.parametrize("backend", ["tableau", "revised"])
@pytest.mark.parametrize("presolve", [False, True])
def test_optional_highs_lp(case, backend, presolve):
    optimize = pytest.importorskip("scipy.optimize")
    # Convert the raw fixture directly; do not call SILO standard-form/matrix code.
    inequalities, inequality_rhs, equalities, equality_rhs = [], [], [], []
    for coefficients, sense, rhs in case.rows:
        row = list(map(float, coefficients))
        if sense == "=":
            equalities.append(row)
            equality_rhs.append(float(rhs))
        else:
            sign = -1 if sense == ">=" else 1
            inequalities.append([sign * a for a in row])
            inequality_rhs.append(sign * float(rhs))
    oracle = optimize.linprog(
        [-float(c) for c in case.objective],
        A_ub=inequalities or None, b_ub=inequality_rhs or None,
        A_eq=equalities or None, b_eq=equality_rhs or None,
        bounds=[(0, None)] * len(case.objective), method="highs",
        options={"presolve": False},
    )
    assert oracle.status in (0, 2, 3), oracle.message
    status = {0: "optimal", 2: "infeasible", 3: "unbounded"}[oracle.status]
    value = -oracle.fun + float(case.constant) if status == "optimal" else None
    assert status == case.status
    if value is not None:
        # The external answer must also satisfy the original specification.
        check_solution(case, Solution(
            status=SolverStatus.OPTIMAL, objective_value=value,
            primal_values={f"x{i}": x for i, x in enumerate(oracle.x)},
        ), case.status, case.value)
    check_solution(case, _solve_model(make_model(case), backend, presolve), status, value)


@pytest.mark.parametrize("mutation", ["wrong-objective", "violates-row", "missing", "nan"])
def test_primal_checker_rejects_bad_answers(mutation):
    case = LP_CASES[0]
    solution = Solution(status=SolverStatus.OPTIMAL, objective_value=9,
                        primal_values={"x0": 1, "x1": 3})
    if mutation == "wrong-objective":
        solution = replace(solution, objective_value=10)
    elif mutation == "violates-row":
        solution = replace(solution, primal_values={"x0": 3, "x1": 0})
    elif mutation == "missing":
        solution = replace(solution, primal_values={"x0": 1})
    else:
        solution = replace(solution, primal_values={"x0": float("nan"), "x1": 3})
    with pytest.raises(AssertionError):
        check_solution(case, solution, "optimal", 9)
