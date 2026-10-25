"""Mapped feasibility uses actual original bounds and residual-aware row sides."""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.sparse import csr_matrix  # noqa: E402

from silo import SolveOptions  # noqa: E402
from silo.io import model_from_dict  # noqa: E402
from silo.lp import sparse_factor as sf  # noqa: E402
from silo.lp.session import LPSession  # noqa: E402
from silo.lp.sparse_dual import mapped_blockers  # noqa: E402

COUNTS = {"root_started": 0, "root_completed": 0, "lu_started": 0, "lu_completed": 0}


@pytest.fixture(autouse=True)
def counted_lu(monkeypatch):
    original = sf.splu

    def lu(*args, **kwargs):
        COUNTS["lu_started"] += 1
        value = original(*args, **kwargs)
        COUNTS["lu_completed"] += 1
        return value

    monkeypatch.setattr(sf, "splu", lu)
    yield
    if path := os.environ.get("SILO_DUAL_TEST_COUNTS"):
        Path(path).write_text(json.dumps(COUNTS), encoding="utf-8")


def public_solve(session):
    COUNTS["root_started"] += 1
    value = session.solve()
    COUNTS["root_completed"] += 1
    return value


def test_dual_continues_when_large_other_coordinate_masks_a_bound_violation():
    payload = {
        "sense": "minimize",
        "variables": [{"name": "x", "upper": 2}, {"name": "y"}, {"name": "w"}],
        "objective": {"coefficients": {"x": -1}},
        "constraints": [
            {"name": "balance", "coefficients": {"x": 1, "y": 1}, "sense": "=", "rhs": 1},
            {"name": "fixed_w", "coefficients": {"w": 1}, "sense": "=", "rhs": 10},
        ],
    }
    session = LPSession(model_from_dict(payload), SolveOptions(lp_engine="sparse", presolve=False))
    assert public_solve(session).status == "optimal"
    upper = 1 - 4e-7
    session.change_bounds("x", 0, upper)
    result = public_solve(session)
    assert result.status == "optimal" and result.optimality["valid"]
    assert abs(result.primal_values["x"] - upper) < 1e-12
    assert abs(result.primal_values["y"] - 4e-7) < 1e-12
    assert result.diagnostics["mapped_dual_pivots"] == 1
    assert result.diagnostics["cross_solve_reuses"] == 1


@pytest.mark.parametrize("direction,bound,scale", [(1, 0, 4), (-1, 2, 0.25)])
def test_structural_bound_uses_actual_column_scale(direction, bound, scale):
    lower, upper = (bound, np.inf) if direction == 1 else (-np.inf, bound)
    data = SimpleNamespace(
        names=("x",), lower=np.array([lower]), upper=np.array([upper]),
        a=csr_matrix((0, 1)), row_names=(), row_lower=np.array([]), row_upper=np.array([]),
    )
    model = SimpleNamespace(
        data=data, offset=np.array([bound]), column_origins=((0, direction),),
        col_scale=np.array([scale]), row_scale=np.array([]), row_keys=(), senses=(),
    )
    deficit = 1.1e-7 * (1 + 2 * abs(bound))
    xb = np.array([-deficit / scale])
    result = mapped_blockers(
        model, csr_matrix([[1.0]]), xb.copy(), [0], (), (("variable", "x", direction),), xb, 1e-7
    )
    assert result.rows == (0,) and not result.primal_feasible and result.violations == 1


@pytest.mark.parametrize("side", ["upper", "lower"])
def test_scaled_slack_includes_nonzero_equation_residual_with_correct_sign(side):
    delta, q = 2.2501e-7, 1e-10
    sigma = 1 if side == "upper" else -1
    value = 1 + sigma * delta
    rows = (("row", "cut", side), ("row", "fixed_x", "equal"), ("row", "fixed_w", "equal"))
    data = SimpleNamespace(
        names=("x", "w"), lower=np.zeros(2), upper=np.full(2, np.inf),
        a=csr_matrix([[4, 0], [1, 0], [0, 1]]), row_names=("cut", "fixed_x", "fixed_w"),
        row_lower=np.array([-np.inf if side == "upper" else 4, value, 10]),
        row_upper=np.array([4 if side == "upper" else np.inf, value, 10]),
    )
    model = SimpleNamespace(
        data=data, offset=np.zeros(2), column_origins=((0, 1), (1, 1)), col_scale=np.ones(2),
        row_scale=np.array([0.25, 1, 1]), row_keys=rows,
        senses=("<=" if side == "upper" else ">=", "=", "="),
    )
    matrix = csr_matrix([[1, 0, sigma], [1, 0, 0], [0, 1, 0]], dtype=float)
    basis, xb = [2, 0, 1], np.array([-delta + q, value, 10])
    rhs = np.array([1, value, 10])
    keys = (("variable", "x", 1), ("variable", "w", 1), ("slack", rows[0]))
    result = mapped_blockers(model, matrix, rhs, basis, rows, keys, xb, 1e-7)
    assert min(xb) >= -1e-7 * (1 + max(abs(xb)))
    # Ignoring q would put this blocker just inside the original side allowance.
    denominator = 1 + 4 * value + 4
    assert -xb[0] / 0.25 < 1e-7 * denominator
    assert result.rows == (0,) and not result.primal_feasible


def test_free_split_does_not_acquire_a_fictitious_original_bound():
    data = SimpleNamespace(
        names=("x",), lower=np.array([-np.inf]), upper=np.array([np.inf]),
        a=csr_matrix((0, 1)), row_names=(), row_lower=np.array([]), row_upper=np.array([]),
    )
    model = SimpleNamespace(
        data=data, offset=np.zeros(1), column_origins=((0, 1), (0, -1)),
        col_scale=np.ones(2), row_scale=np.array([]), row_keys=(), senses=(),
    )
    result = mapped_blockers(
        model, csr_matrix([[1.0, -1.0]]), np.array([-1e-8]), [0], (),
        (("variable", "x", 1), ("variable", "x", -1)), np.array([-1e-8]), 1e-7,
    )
    assert result.rows == () and result.primal_feasible
