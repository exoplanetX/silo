"""Independent small-matrix checks of eta order, residuals and actual LU calls."""

import json
import os
from dataclasses import replace
from pathlib import Path
from time import perf_counter

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.sparse import csc_matrix  # noqa: E402

from silo.core.solve_types import SolveOptions  # noqa: E402
from silo.lp import sparse_factor as sf  # noqa: E402

ACTUAL = {"splu_calls": 0, "factor_tests": 0}


@pytest.fixture(autouse=True)
def count_actual(monkeypatch):
    original = sf.splu

    def observed(*args, **kwargs):
        ACTUAL["splu_calls"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(sf, "splu", observed)
    yield
    ACTUAL["factor_tests"] += 1
    if path := os.environ.get("SILO_FACTOR_TEST_COUNTS"):
        Path(path).write_text(json.dumps(ACTUAL), encoding="utf-8")


def make(matrix, **changes):
    return sf.SparseFactor(csc_matrix(matrix), replace(SolveOptions(), **changes), {})


def assert_solves(factor):
    b = factor.matrix
    rhs = np.arange(1, b.shape[0] + 1, dtype=float)
    for values in (rhs, np.column_stack((rhs, rhs[::-1]))):
        x, y = factor.solve_B(values), factor.solve_BT(values)
        assert np.allclose(b @ x, values, rtol=1e-11, atol=1e-11)
        assert np.allclose(b.T @ y, values, rtol=1e-11, atol=1e-11)


def test_noncommuting_etas_force_reverse_transpose_order():
    factor = make(np.eye(2))
    factor.replace_column(0, [1, 1])
    factor.replace_column(1, [1, 2])
    assert factor.counters["eta_updates"] == 2
    assert np.allclose(factor.solve_BT([1, 0]), [2, -1])
    assert not np.allclose(factor.solve_BT([1, 0]), [1, -1])
    assert_solves(factor)


@pytest.mark.parametrize("seed", [3, 11, 27])
def test_short_legal_random_chains_match_current_basis(seed):
    rng = np.random.default_rng(seed)
    factor = make(np.eye(6))
    for i in range(15):
        direction = rng.normal(0, 0.08, 6)
        direction[i % 6] = 1 + rng.uniform(-0.1, 0.1)
        column = factor.matrix @ direction
        factor.replace_column(i % 6, column, direction)
        assert_solves(factor)
    assert len(factor.etas) == 15
    assert factor.counters["base_factorizations"] == 1


def test_twenty_first_update_rebases_actual_current_basis():
    factor = make(np.eye(3))
    for i in range(21):
        direction = np.array([0.01, -0.02, 0.03])
        direction[i % 3] = 1
        factor.replace_column(i % 3, factor.matrix @ direction, direction)
    assert factor.counters["basis_replacements"] == 21
    assert factor.counters["eta_updates"] == 21
    assert factor.counters["refactorizations_by_reason"] == {"chain_limit": 1}
    assert len(factor.etas) == 1
    assert_solves(factor)


def test_updates_zero_use_real_lu_and_do_not_increment_eta():
    before = ACTUAL["splu_calls"]
    factor = make(np.eye(2), max_factor_updates=0)
    factor.replace_column(0, [1, 1])
    assert factor.counters["base_factorizations"] == ACTUAL["splu_calls"] - before == 2
    assert factor.counters.get("eta_updates", 0) == 0
    assert factor.counters["basis_replacements"] == 1
    assert_solves(factor)


def test_bad_direction_is_recomputed_before_committing():
    factor = make(np.eye(2))
    factor.replace_column(0, [1, 1], np.array([9.0, -3.0]))
    assert factor.counters["refactorizations_by_reason"] == {"direction_residual": 1}
    assert_solves(factor)


def test_rejected_pivot_leaves_matrix_unchanged():
    factor = make(np.eye(2))
    original = factor.identity
    with pytest.raises(np.linalg.LinAlgError, match="Unsafe basis pivot"):
        factor.replace_column(0, [1e-12, 1])
    assert factor.identity == original
    assert factor.counters.get("basis_replacements", 0) == 0
    assert factor.counters["refactorizations_by_reason"] == {"pivot": 1}


def test_growth_causes_real_rebuild_and_keeps_full_small_coefficients():
    factor = make(np.eye(2))
    factor.replace_column(0, [1, 1e-15])
    assert factor.etas[0][1][1] == 1e-15
    factor.replace_column(1, [0, 1e9])
    assert factor.counters["refactorizations_by_reason"] == {"growth": 1}
    assert factor.counters["basis_replacements"] == 2
    assert not factor.etas
    assert_solves(factor)


def test_residual_recovery_rebuilds_current_matrix_after_two_refinements():
    factor = make(np.eye(2))
    factor.replace_column(0, [1, 1])

    class WrongLU:
        def solve(self, rhs, trans="N"):
            return np.zeros_like(rhs)

    factor.lu = WrongLU()
    assert np.allclose(factor.solve_BT([1, 0]), [1, 0])
    assert factor.counters["refinement_steps"] == 2
    assert factor.counters["refactorizations_by_reason"] == {"residual": 1}
    assert sf.same_matrix(factor.matrix, csc_matrix([[1, 0], [1, 1]]))


def test_singular_fill_deadline_and_policy_resources_are_distinct():
    with pytest.raises(np.linalg.LinAlgError):
        make([[1, 1], [1, 1]])
    with pytest.raises(sf.FactorResourceError):
        make(np.eye(2), max_factor_nnz=0)
    with pytest.raises(sf.FactorResourceError, match="fill"):
        make(np.eye(2), max_factor_nnz=3)
    with pytest.raises(sf.FactorDeadline):
        sf.SparseFactor(csc_matrix(np.eye(2)), SolveOptions(), {}, deadline=perf_counter() - 1)
    factor = make(np.eye(2))
    factor.replace_column(0, [1, 1])
    newer = replace(factor.options, max_factor_updates=0)
    assert factor.configure(newer, {}, float("inf"))
    assert factor.counters["refactorizations_by_reason"] == {"update_policy": 1}
    assert not factor.etas
    assert factor.configure(replace(newer, pivot_tolerance=2e-10), {}, float("inf"))
    assert factor.counters["refactorizations_by_reason"] == {"pivot_policy": 1}
    with pytest.raises(sf.FactorResourceError):
        factor.configure(replace(newer, max_factor_nnz=0), {}, float("inf"))


def test_factor_owns_actual_matrix_and_immutable_identity():
    matrix = csc_matrix(np.eye(2))
    factor = sf.SparseFactor(matrix, SolveOptions(), {})
    identity = factor.identity
    matrix.data[:] = 17
    assert factor.identity == identity
    assert_solves(factor)
