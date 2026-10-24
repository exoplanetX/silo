"""Exact original equations and pre-allocation rational workspace boundaries."""

from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest

from silo.io import model_from_dict
from silo.lp import tableau_view
from silo.lp.verification import exact_farkas, exact_ray
from silo.modeling.general import linear_data, normalize
from silo.presolve.activity import propagate
from silo.utils.rational import ProofBudget, ProofLimitError

pytest.importorskip("scipy")


def test_rational_workspace_exact_boundary_and_nested_outer_cells():
    budget = ProofBudget()
    with budget.workspace(65536):
        assert budget.live_cells == 65536
        with pytest.raises(ProofLimitError, match="65536"):
            with budget.workspace(1):
                pytest.fail("Over-budget body entered")
    assert budget.live_cells == 0 and budget.peak_cells == 65536
    with pytest.raises(ProofLimitError, match="65536"):
        with budget.workspace(65537):
            pytest.fail("Over-budget body entered")
    with pytest.raises(RuntimeError), budget.workspace(100):
        raise RuntimeError("release on failure")
    assert budget.live_cells == 0


def test_basis_only_exact_candidates_do_not_build_full_standard_coordinates(monkeypatch):
    n = 300
    model = model_from_dict(
        {
            "variables": [{"name": f"x{i}"} for i in range(n)],
            "constraints": [{"name": "third", "coefficients": {"x0": 3}, "sense": "=", "rhs": 1}],
            "objective": {"coefficients": {"x0": 1}},
        }
    )
    data = linear_data(model, 0, engine="sparse")
    norm = normalize(data, data.lower, data.upper)
    native = SimpleNamespace(
        status="optimal",
        matrix=norm.matrix,
        basis=(0,),
        row_keys=norm.row_keys,
        column_keys=tuple(("variable", name, 1) for name in data.names),
    )
    assert tableau_view.proof_workspace_cells(norm, native, full=True) > 65536
    assert tableau_view.proof_workspace_cells(norm, native) < 65536

    def forbidden(*args, **kwargs):
        raise AssertionError("Unneeded full proof allocation")

    monkeypatch.setattr(tableau_view, "_exact_standard_data", forbidden)
    point, dual = tableau_view.exact_basis_candidates(
        SimpleNamespace(_lp=(norm, native, None)), ProofBudget()
    )
    assert point["x0"] == dual["third"] == F(1, 3)
    assert all(value == 0 for name, value in point.items() if name != "x0")
    assert tableau_view.exact_tableau_rows(norm, native, np.zeros(n, dtype=bool)) == ()


def test_oversized_proof_is_refused_before_fraction_conversion(monkeypatch):
    from scipy.sparse import csr_matrix

    data = SimpleNamespace(
        names=range(22000), row_names=("r",), a=csr_matrix(([1.0], ([0], [0])), shape=(1, 22000))
    )
    norm = SimpleNamespace(data=data)
    native = SimpleNamespace(
        status="optimal",
        matrix=data.a,
        basis=(0,),
        row_keys=(("row", "r", "upper"),),
        column_keys=(("variable", "x", 1),),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Fraction allocated before workspace refusal")

    monkeypatch.setattr(tableau_view, "F", forbidden)
    with pytest.raises(ProofLimitError, match="65536"):
        tableau_view.exact_basis_candidates(
            SimpleNamespace(_lp=(norm, native, None)), ProofBudget()
        )
    assert tableau_view.exact_basis_farkas(norm, native, None) is None


def test_sparse_exact_scaled_phase_one_basis_farkas():
    from scipy.sparse import csr_matrix

    model = model_from_dict(
        {
            "variables": [{"name": "x"}],
            "constraints": [
                {"name": "lo", "coefficients": {"x": 4}, "sense": ">=", "rhs": 8},
                {"name": "up", "coefficients": {"x": 2}, "rhs": 2},
            ],
            "objective": {"coefficients": {}},
        }
    )
    data = linear_data(model, engine="sparse")
    norm = normalize(data, data.lower, data.upper)
    keys = (
        ("variable", "x", 1),
        ("slack", norm.row_keys[0]),
        ("artificial", norm.row_keys[0]),
        ("slack", norm.row_keys[1]),
    )
    native = SimpleNamespace(
        status="infeasible",
        basis=(2, 0),
        row_keys=norm.row_keys,
        column_keys=keys,
        matrix=csr_matrix([[1, -1, 1, 0], [1, 0, 0, 1]]),
    )
    proof = tableau_view.exact_basis_farkas(norm, native, propagate(data, enabled=False))
    assert proof["kind"] == "farkas" and F(proof["contradiction"]) == 1
    sides = [
        list(map(F, proof[name]))
        for name in ("row_lower", "row_upper", "variable_lower", "variable_upper")
    ]
    assert exact_farkas(data, sides) == proof


def test_sparse_exact_ray_checks_original_nonzeros():
    model = model_from_dict(
        {
            "variables": [{"name": "x"}, {"name": "y"}],
            "constraints": [{"name": "third", "coefficients": {"x": 3}, "sense": "=", "rhs": 1}],
            "objective": {"coefficients": {"y": -1}},
        }
    )
    data = linear_data(model, engine="sparse")
    proof = exact_ray(data, [1 / 3, 0], [0, 1])
    assert proof["point"]["x"] == "1/3" and proof["improvement"] == "-1"
    assert exact_ray(data, [0, 0], [0, 1]) is None
