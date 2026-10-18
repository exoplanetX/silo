from dataclasses import replace
from pathlib import Path

import pytest

from silo.cli.main import _solve_model
from silo.io.json_reader import read_json_model
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex.revised import RevisedSimplexSolver
from tests.verification.oracles import LP_CASES, make_model


@pytest.mark.parametrize("case", [case for case in LP_CASES if case.status == "optimal"],
                         ids=lambda case: case.name)
@pytest.mark.parametrize("backend", ["tableau", "revised"])
@pytest.mark.parametrize("presolve", [False, True])
def test_original_analytical_lp_oracles_have_valid_duals(case, backend, presolve):
    model = make_model(case)
    solution = _solve_model(model, backend, presolve)
    checked = check_lp_optimality(model, solution)
    assert checked.passed, checked
    assert checked.primal_objective == pytest.approx(float(case.value))
    assert checked.dual_objective == pytest.approx(float(case.value))


@pytest.mark.parametrize("backend", ["tableau", "revised"])
@pytest.mark.parametrize("name", ["fixed_var_recovery.json", "repeated_empty_row.json"])
def test_original_json_presolve_recovery_has_valid_duals(backend, name):
    model = read_json_model(Path("examples/json") / name)
    assert check_lp_optimality(model, _solve_model(model, backend, True)).passed


def test_revised_warm_start_preserves_dual_evidence():
    model = make_model(LP_CASES[0])
    solver = RevisedSimplexSolver()
    first = solver.solve_with_details(model)
    assert first.basis is not None
    model.objective = replace(model.objective, constant=11)
    warm = solver.solve_with_details(model, basis=first.basis)
    assert warm.used_warm_start
    assert warm.iterations == 0
    assert check_lp_optimality(model, warm.solution).passed


@pytest.mark.parametrize("backend", ["tableau", "revised"])
def test_unique_duals_match_optional_highs_marginals(backend):
    optimize = pytest.importorskip("scipy.optimize")
    # max 3x+2y+7: x+y<=4, 2x+y<=5 has unique x=(1,3), y=(1,1).
    model = make_model(LP_CASES[0])
    model.objective = replace(model.objective, constant=7)
    oracle = optimize.linprog([-3, -2], A_ub=[[1, 1], [2, 1]], b_ub=[4, 5],
                              bounds=[(0, None), (0, None)], method="highs")
    assert oracle.status == 0
    solution = _solve_model(model, backend, False)
    # HiGHS minimizes -c; negate its RHS derivatives to match our max convention.
    assert list(solution.dual_values.values()) == pytest.approx(-oracle.ineqlin.marginals)
    assert solution.dual_values == {"r0": pytest.approx(1), "r1": pytest.approx(1)}
    assert check_lp_optimality(model, solution).passed
