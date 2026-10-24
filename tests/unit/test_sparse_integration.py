"""Public selection, cache ownership and optimizer separation contracts."""

import json
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from silo import SolveOptions, solve
from silo.io import model_from_dict
from silo.lp.session import LPSession


def payload():
    return {
        "name": "owned_sparse_session",
        "sense": "minimize",
        "variables": [{"name": "x"}, {"name": "y"}],
        "constraints": [
            {"name": "cap", "coefficients": {"x": 1, "y": 1}, "rhs": 4},
            {"name": "mix", "coefficients": {"x": 1, "y": 2}, "rhs": 6},
        ],
        "objective": {"coefficients": {"x": -2, "y": -3}, "constant": 3},
    }


@pytest.mark.parametrize(
    "name,value",
    [
        ("lp_engine", "auto"),
        ("max_sparse_nnz", True),
        ("max_factor_nnz", -1),
        ("max_factor_updates", 21),
        ("max_factor_updates", 1.0),
    ],
)
def test_sparse_options_validate_without_numerical_import(name, value):
    with pytest.raises(ValueError):
        SolveOptions(**{name: value})


def test_numpy_only_import_and_selected_missing_sparse_dependency():
    root = str(Path(__file__).resolve().parents[2] / "src")
    code = f"""
import importlib.abc,json,sys
sys.path.insert(0,{root!r})
class DenyScipy(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname == 'scipy' or fullname.startswith('scipy.'):
   raise ModuleNotFoundError('deliberately absent optional dependency')
sys.meta_path.insert(0,DenyScipy())
from silo import solve,SolveOptions
from silo.io import model_from_dict
m=model_from_dict({payload()!r})
d=solve(m)
s=solve(m,SolveOptions(lp_engine='sparse'))
assert d.status == 'optimal'
assert (s.status,s.termination_reason) == ('unsupported','sparse_dependency_missing')
assert not any(n == 'scipy' or n.startswith('scipy.') for n in sys.modules)
print(json.dumps({{'dense':d.status,'sparse':s.status}}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"dense": "optimal", "sparse": "unsupported"}


def test_factor_cache_is_owned_and_results_expose_no_mutable_cache(monkeypatch):
    optimize = pytest.importorskip("scipy.optimize")

    def forbidden(*args, **kwargs):
        raise AssertionError("Native solve called an optimizer")

    monkeypatch.setattr(optimize, "linprog", forbidden)
    monkeypatch.setattr(optimize, "milp", forbidden)
    options = SolveOptions(lp_engine="sparse", presolve=False, scaling=False)
    source = model_from_dict(payload())
    first, other = LPSession(source, options), LPSession(source, options)
    initial, independent = first.solve(), other.solve()
    assert initial.status == independent.status == "optimal"
    assert initial.objective_value == pytest.approx(-7)
    assert initial.basis.version == 3
    assert not hasattr(initial, "_factor_state")
    assert not hasattr(initial._lp[1], "_factor_state")
    assert first._factor_state is not other._factor_state
    # Modifying a returned matrix or copied model cannot alter an owned LU/eta.
    initial._lp[1].matrix.data[:] = 77
    source.objective.coefficients["x"] = 100
    copied = first.model
    copied.constraints[0].coefficients["x"] = 30
    first.change_rhs("cap", 3.75)
    warm = first.solve()
    cold = solve(first.model, options)
    assert warm.status == cold.status == "optimal"
    assert warm.objective_value == pytest.approx(cold.objective_value)
    assert warm.diagnostics["cross_solve_reuses"] > 0
    assert other.solve().objective_value == pytest.approx(-7)


def test_engine_resource_policies_and_basis_mapping():
    pytest.importorskip("scipy")
    model = model_from_dict(payload())
    options = SolveOptions(lp_engine="sparse", presolve=False, scaling=False, max_dense_cells=0)
    session = LPSession(model, options)
    result = session.solve()
    assert result.status == "optimal"
    session.options = replace(options, max_factor_nnz=0)
    limited = session.solve()
    assert (limited.status, limited.termination_reason) == ("limit", "resource_limit")
    session.options = replace(options, max_factor_updates=0)
    restored = session.solve()
    assert restored.status == "optimal" and restored.diagnostics["eta_updates"] == 0
    session.options = replace(options, lp_engine="dense", max_dense_cells=2000000)
    assert session.solve().status == "optimal"
    dense_basis = solve(model).basis
    imported = solve(model, options, basis=dense_basis)
    assert imported.status == "optimal" and imported.basis.version == 3
    assert solve(model, replace(options, max_sparse_nnz=0)).status == "limit"


def test_actual_full_pool_and_nested_basis_share_workspace(monkeypatch):
    from silo.decomposition.general_master import MasterColumn, _full_pool_certificate
    from silo.lp import tableau_view
    from silo.utils.rational import ProofBudget, ProofLimitError

    # The exact denominator exceeds the rational-guess ceiling, forcing the
    # real full-pool -> exact-basis fallback, including its elimination copies.
    raw = {
        "variables": [{"name": "x"}],
        "constraints": [{"name": "eq", "coefficients": {"x": 100000007}, "sense": "=", "rhs": 1}],
        "objective": {"coefficients": {"x": 1}},
    }
    model = model_from_dict(raw)
    options = SolveOptions(presolve=False, scaling=False)
    result = solve(model, options)
    assert result.status == "optimal"
    pool = (MasterColumn("x", 1, {"eq": 100000007}),)
    inner = tableau_view.proof_workspace_cells(*result._lp[:2])
    outer = 4 * len(result.primal_values) + 4 * len(result.dual_values) + 2 * len(pool) + 32
    budget = ProofBudget()
    with budget.workspace(65536 - outer - inner):
        proof = _full_pool_certificate(model, pool, result, options, budget)
    assert Fraction(proof["primal_objective"]) == Fraction(1, 100000007)
    assert budget.peak_cells == 65536 and budget.live_cells == 0

    def forbidden(*args, **kwargs):
        raise AssertionError("Basis Fraction allocation preceded the workspace gate")

    monkeypatch.setattr(tableau_view, "_exact_basis_data", forbidden)
    budget = ProofBudget()
    with budget.workspace(65537 - outer - inner), pytest.raises(ProofLimitError, match="workspace"):
        _full_pool_certificate(model, pool, result, options, budget)
    assert budget.live_cells == 0
