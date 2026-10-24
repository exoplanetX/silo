"""Canonical mathematical cases, passive snapshots and session-cache isolation."""

import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.sparse import csr_matrix  # noqa: E402

from silo.core.solve_types import SolveOptions  # noqa: E402
from silo.lp import sparse_factor as sf  # noqa: E402
from silo.lp import sparse_kernel as sk  # noqa: E402
from silo.lp.kernel import BasisSnapshot  # noqa: E402

CALLS = {"kernel_started": 0, "kernel_completed": 0, "native_roots": 0, "splu_calls": 0}


@pytest.fixture(autouse=True)
def observed_lu(monkeypatch):
    original = sf.splu

    def observed(*args, **kwargs):
        CALLS["splu_calls"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(sf, "splu", observed)


def call(*args, **kwargs):
    CALLS["kernel_started"] += 1
    result = sk.solve_canonical(*args, **kwargs)
    CALLS["kernel_completed"] += 1
    if path := os.environ.get("SILO_KERNEL_TEST_COUNTS"):
        Path(path).write_text(json.dumps(CALLS), encoding="utf-8")
    return result


def norm(matrix, rhs, costs, senses=None):
    a = csr_matrix(matrix, dtype=float)
    m, n = a.shape
    names = tuple(f"x{i}" for i in range(n))
    lower, upper = np.zeros(n), np.full(n, np.inf)
    senses = tuple(senses or ["<="] * m)
    row_lower = np.array(
        [rhs[i] if side in (">=", "=") else -np.inf for i, side in enumerate(senses)]
    )
    row_upper = np.array(
        [rhs[i] if side in ("<=", "=") else np.inf for i, side in enumerate(senses)]
    )
    return SimpleNamespace(
        matrix=a,
        rhs=np.array(rhs, dtype=float),
        costs=np.array(costs, dtype=float),
        senses=senses,
        row_keys=tuple(("row", f"r{i}", "upper") for i in range(m)),
        column_origins=tuple((i, 1) for i in range(n)),
        row_scale=np.ones(m),
        col_scale=np.ones(n),
        lower=lower,
        upper=upper,
        offset=np.zeros(n),
        data=SimpleNamespace(
            names=names,
            a=a,
            row_names=tuple(f"r{i}" for i in range(m)),
            row_lower=row_lower,
            row_upper=row_upper,
        ),
    )


def ordinary():
    return norm([[1, 1], [1, 0], [0, 1]], [4, 2, 3], [3, 2])


@pytest.mark.parametrize(
    "model,status,expected",
    [
        (ordinary(), "optimal", [2, 2]),
        (norm([[1, 1], [1, 0]], [2, 3], [-1, -2], [">=", "<="]), "optimal", [2, 0]),
        (norm([[1], [1]], [1, 2], [1], ["<=", ">="]), "infeasible", None),
        (norm([[-1]], [0], [1]), "unbounded", None),
        (norm([[1, 1], [2, 2]], [2, 4], [-1, -2], ["=", "="]), "optimal", [2, 0]),
        (norm(csr_matrix((0, 2)), [], [-1, -2]), "optimal", [0, 0]),
        (norm(csr_matrix((0, 2)), [], [1, -2]), "unbounded", None),
    ],
)
def test_canonical_cases(model, status, expected):
    result = call(model, SolveOptions())
    assert result.status == status, result.reason
    if expected is not None:
        assert np.allclose(result.point, expected)
    if status == "optimal":
        assert result.snapshot.version == 3
        assert isinstance(result.snapshot.matrix, sk.SparseCoefficients)
        assert result.matrix is not None
    if status == "infeasible":
        assert result.diagnostics["proof_kind"] == "farkas"


def test_unchanged_rhs_cache_reuses_real_lu_and_clears_bland_history():
    model = ordinary()
    first = call(model, SolveOptions())
    cache = first._factor_state
    cache["pricing"].bland = True
    cache["pricing"].visited.add(("artificial stale history",))
    second_model = ordinary()
    second_model.rhs[0] = 4.25
    second = call(second_model, SolveOptions(), first.snapshot, factor_state=cache)
    assert second.status == "optimal" and np.allclose(second.point, [2, 2.25])
    assert second.diagnostics["base_factorizations"] == 0
    assert second.diagnostics["cross_solve_reuses"] == 1
    assert not second._factor_state["pricing"].bland
    assert cache["factor"].lu is second._factor_state["factor"].lu


def test_appended_nonbasic_column_preserves_basis_factor_then_pivots():
    first = call(ordinary(), SolveOptions())
    bigger = norm([[1, 1, 1], [1, 0, 0], [0, 1, 0]], [4, 2, 3], [3, 2, 10])
    result = call(bigger, SolveOptions(), first.snapshot, factor_state=first._factor_state)
    assert result.status == "optimal" and np.allclose(result.point, [0, 0, 4])
    assert result.diagnostics["cross_solve_reuses"] == 1
    assert result.diagnostics["eta_updates"] > 0


def test_appended_row_changes_dimension_and_builds_new_lu():
    first = call(ordinary(), SolveOptions())
    larger = norm([[1, 1], [1, 0], [0, 1], [1, 0]], [4, 2, 3, 1.5], [3, 2])
    result = call(larger, SolveOptions(), first.snapshot, factor_state=first._factor_state)
    assert result.status == "optimal" and np.allclose(result.point, [1.5, 2.5])
    assert result.diagnostics["cross_solve_reuses"] == 0
    assert result.diagnostics["base_factorizations"] > 0


def test_public_matrix_mutation_cannot_change_private_factor():
    first = call(ordinary(), SolveOptions())
    identity = first._factor_state["factor"].identity
    first.matrix.data[:] = 891
    assert first._factor_state["factor"].identity == identity
    second = call(ordinary(), SolveOptions(), first.snapshot, factor_state=first._factor_state)
    assert second.status == "optimal" and np.allclose(second.point, [2, 2])
    assert second.diagnostics["cross_solve_reuses"] == 1


def test_direct_or_distinct_session_states_do_not_share_lu():
    first, second = call(ordinary(), SolveOptions()), call(ordinary(), SolveOptions())
    assert first._factor_state["factor"].lu is not second._factor_state["factor"].lu
    assert first.diagnostics["cross_solve_reuses"] == second.diagnostics["cross_solve_reuses"] == 0


def test_legacy_v2_import_verifies_semantics_and_refactorizes():
    first = call(ordinary(), SolveOptions())
    dense_passive = tuple(
        tuple(float(first.matrix[i, j]) for j in range(first.matrix.shape[1]))
        for i in range(first.matrix.shape[0])
    )
    legacy = BasisSnapshot(
        2, first.row_keys, first.column_keys, dense_passive, first.snapshot.basic_keys
    )
    second = call(ordinary(), SolveOptions(), legacy, factor_state=first._factor_state)
    assert second.status == "optimal"
    assert second.diagnostics["warm_starts"] == 1
    assert second.diagnostics["base_factorizations"] > 0
    assert second.diagnostics["cross_solve_reuses"] == 0
    stale = replace(legacy, basic_keys=(("variable", "missing", 1),) * len(legacy.basic_keys))
    third = call(ordinary(), SolveOptions(), stale)
    assert third.status == "optimal" and third.diagnostics["cold_fallbacks"] == 1


def test_changed_coefficients_or_row_order_refuse_stale_snapshot():
    first = call(ordinary(), SolveOptions())
    changed = ordinary()
    changed.matrix = changed.data.a = csr_matrix([[2, 1], [1, 0], [0, 1]])
    second = call(changed, SolveOptions(), first.snapshot, factor_state=first._factor_state)
    assert second.status == "optimal" and np.allclose(second.point, [0.5, 3])
    assert second.diagnostics["cold_fallbacks"] == 1
    assert second.diagnostics["cross_solve_reuses"] == 0


def test_limits_recheck_existing_factor_and_disable_eta():
    first = call(ordinary(), SolveOptions())
    no_factor = call(
        ordinary(),
        replace(SolveOptions(), max_factor_nnz=0),
        first.snapshot,
        factor_state=first._factor_state,
    )
    assert (no_factor.status, no_factor.reason) == ("limit", "resource_limit")
    assert not no_factor._factor_state
    no_updates = call(ordinary(), replace(SolveOptions(), max_factor_updates=0))
    assert no_updates.status == "optimal" and no_updates.diagnostics["eta_updates"] == 0
    assert no_updates.diagnostics["base_factorizations"] > 1
    no_matrix = call(ordinary(), replace(SolveOptions(), max_sparse_nnz=0))
    assert (no_matrix.status, no_matrix.reason) == ("limit", "resource_limit")


@pytest.mark.parametrize("epsilon", [2**-40, 2**-36])
def test_small_nonzero_equation_is_not_deleted_as_dependent(epsilon):
    model = norm([[1, 1], [1, 1 + epsilon]], [1, 1], [0, 1], ["=", "="])
    result = call(model, SolveOptions())
    assert result.status == "numerical_failure", (result.status, result.point)
    assert result.diagnostics["dependent_rows_removed"] == 0
    assert "Unproved near-dependent" in result.reason


def test_nearby_distinct_ratios_are_not_false_bland_ties():
    result = call(norm([[1], [1]], [5e-11, 0], [1]), SolveOptions())
    assert result.status == "optimal" and result.point[0] == 0


def test_unsafe_true_blocker_cannot_be_skipped_for_larger_ratio():
    result = call(norm([[1e-8], [1e4]], [0, 1e4], [1]), SolveOptions())
    assert result.status == "numerical_failure"
    assert "Unsafe blocking pivot" in result.reason


@pytest.mark.parametrize("bland", [False, True])
def test_rejected_entering_does_not_prevent_other_safe_improving_column(monkeypatch, bland):
    if bland:
        original = sk.Devex.fresh_phase

        def sticky(self, *args, **kwargs):
            original(self, *args, **kwargs)
            self.bland = True

        monkeypatch.setattr(sk.Devex, "fresh_phase", sticky)
    model = norm([[1e-8, 0], [1e4, 1], [0, 1]], [0, 1, 1], [2, 1])
    result = call(model, SolveOptions())
    assert result.status == "optimal" and np.allclose(result.point, [0, 1])
    assert result.diagnostics["rejected_entering_columns"] == 1
    assert result.diagnostics["primal_pivots"] == 1
    if bland:
        assert result.diagnostics["bland_pricings"] >= 2
