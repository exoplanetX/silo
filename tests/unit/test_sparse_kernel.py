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


def test_state_recomputes_both_vectors_when_second_solve_rebases(monkeypatch):
    original = sf.SparseFactor.solve
    seen, fired = [], False

    def injected(self, rhs, transpose=False):
        nonlocal fired
        if not transpose and np.array_equal(rhs, [1, 1]) and self.matrix.nnz == 2:
            seen.append(self.generation)
            answer = original(self, rhs, transpose)
            return np.array([100.0, 1.0]) if not fired else answer
        if transpose and not fired:
            fired = True
            self.refactor(reason="injected_second_state_solve")
        return original(self, rhs, transpose)

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "optimal" and result.point[0] == 0.5
    assert len(seen) >= 2 and seen[0] < seen[1]
    assert result.diagnostics["state_generation_restarts"] == 1


@pytest.mark.parametrize("stage", ["direction", "devex_btran", "before_commit"])
def test_primal_generation_change_never_commits_the_old_blocker(monkeypatch, stage):
    original_solve, original_replace = sf.SparseFactor.solve, sf.SparseFactor.replace_column
    fired, old_direction = False, False
    attempted, committed = [], []
    observed = []
    original_observation = sk._PivotObservation.__init__

    def observe(self, *args, **kwargs):
        original_observation(self, *args, **kwargs)
        observed.append(self.leaving)

    def injected_solve(self, rhs, transpose=False):
        nonlocal fired, old_direction
        answer = original_solve(self, rhs, transpose)
        if not fired and not transpose and np.array_equal(rhs, [1, 2]):
            old_direction = True
            if stage == "direction":
                fired = True
                self.refactor(reason="injected_direction")
            return np.array([1.0, 0.1])
        if stage == "devex_btran" and old_direction and not fired and transpose:
            fired = True
            self.refactor(reason="injected_devex_btran")
            return original_solve(self, rhs, transpose)
        return answer

    def injected_replace(self, position, *args, **kwargs):
        nonlocal fired
        attempted.append(position)
        if stage == "before_commit" and not fired:
            fired = True
            self.refactor(reason="injected_before_commit")
        value = original_replace(self, position, *args, **kwargs)
        committed.append(position)
        return value

    monkeypatch.setattr(sf.SparseFactor, "solve", injected_solve)
    monkeypatch.setattr(sf.SparseFactor, "replace_column", injected_replace)
    monkeypatch.setattr(sk._PivotObservation, "__init__", observe)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert fired and result.status == "optimal" and result.point[0] == 0.5
    assert committed == [1] and 0 not in committed
    assert observed == [1]  # Uncommitted retries never replace last-pivot data.
    assert result.diagnostics["pivot_generation_restarts"] == 1
    if stage == "before_commit":
        assert attempted == [0, 1]


@pytest.mark.parametrize("stage", ["dual_tableau", "dual_direction"])
def test_dual_witness_and_direction_rebase_restart_the_complete_choice(monkeypatch, stage):
    first = call(ordinary(), SolveOptions())
    original = sf.SparseFactor.solve
    fired = False

    def injected(self, rhs, transpose=False):
        nonlocal fired
        answer = original(self, rhs, transpose)
        target = (
            transpose and np.count_nonzero(rhs) == 1 and np.max(rhs) == 1
            if stage == "dual_tableau"
            else not transpose and not np.array_equal(rhs, [4, 2, 3, 1.5])
        )
        if self.matrix.shape == (4, 4) and not fired and target:
            fired = True
            self.refactor(reason="injected_" + stage)
            return original(self, rhs, transpose)
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    larger = norm([[1, 1], [1, 0], [0, 1], [1, 0]], [4, 2, 3, 1.5], [3, 2])
    result = call(larger, SolveOptions(), first.snapshot, factor_state=first._factor_state)
    assert fired and result.status == "optimal" and np.allclose(result.point, [1.5, 2.5])
    assert result.diagnostics["pivot_generation_restarts"] == 1
    assert result.diagnostics["dual_pivots"] == 1


@pytest.mark.parametrize("stage", ["cleanup_tableau", "cleanup_direction"])
def test_cleanup_rechecks_phase_state_after_generation_change(monkeypatch, stage):
    original = sf.SparseFactor.solve
    fired = False

    def injected(self, rhs, transpose=False):
        nonlocal fired
        answer = original(self, rhs, transpose)
        target = (
            transpose and np.array_equal(rhs, [1])
            if stage == "cleanup_tableau"
            else not transpose and np.array_equal(rhs, [-1])
        )
        if not fired and target:
            fired = True
            self.refactor(reason="injected_" + stage)
            return original(self, rhs, transpose)
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    result = call(norm([[-1, -1]], [0], [-1, -2], ["="]), SolveOptions())
    assert fired and result.status == "optimal" and np.allclose(result.point, [0, 0])
    assert result.diagnostics["cleanup_generation_restarts"] == 1
    assert result.diagnostics["artificial_cleanup_pivots"] == 1


def test_repeated_generation_change_has_a_finite_current_basis_retry_limit(monkeypatch):
    original = sf.SparseFactor.solve

    def injected(self, rhs, transpose=False):
        answer = original(self, rhs, transpose)
        if not transpose and np.array_equal(rhs, [1, 2]):
            self.refactor(reason="injected_repeated_direction")
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "numerical_failure" and result.iterations == 0
    assert "factor-generation retry limit" in result.reason
    assert result.diagnostics["pivot_generation_restarts"] == 4


def test_rejected_history_survives_rebase_when_new_reduced_costs_disappear(monkeypatch):
    original = sf.SparseFactor.solve
    fired = False

    def injected(self, rhs, transpose=False):
        nonlocal fired
        answer = original(self, rhs, transpose)
        if not fired and not transpose and np.array_equal(rhs, [0, 1, 1]):
            fired = True
            self.refactor(reason="injected_after_rejection")
            return original(self, rhs, transpose)
        if fired and transpose:
            return np.full(3, 1e9)
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    result = call(norm([[1e-8, 0], [1e4, 1], [0, 1]], [0, 2, 1], [2, 1]), SolveOptions())
    assert fired and result.status == "numerical_failure" and result.iterations == 0
    assert "Rejected entering history" in result.reason
    assert result.diagnostics["rejected_entering_columns"] == 1


@pytest.mark.parametrize("kind", ["eta", "growth"])
def test_one_current_basis_recheck_recovers_and_observes_last_pivot(monkeypatch, kind):
    original = sf.SparseFactor.solve
    original_step, original_reset = sk.Devex.step, sk.Devex.reset
    fired, reset_seen = False, []
    rhs = [1, 1] if kind == "eta" else [1, 1e9]
    matrix = [[1], [2]] if kind == "eta" else [[1], [1e9]]

    def injected(self, values, transpose=False):
        nonlocal fired
        answer = original(self, values, transpose)
        if not fired and not transpose and self.matrix.nnz == 3 and np.array_equal(values, rhs):
            fired = True
            answer = answer.copy()
            answer[0] = -1
        return answer

    def sticky(self, *args):
        original_step(self, *args)
        self.bland, self.degenerate = True, 2
        self.visited.add(("retained through feasibility recheck",))

    def observe_reset(self, basis, reason):
        if reason == "primal_feasibility":
            history = self.bland, self.visited.copy(), self.degenerate
        original_reset(self, basis, reason)
        if reason == "primal_feasibility":
            assert history == (self.bland, self.visited, self.degenerate)
            assert self.bland and self.degenerate == 2
            assert all(value == 1 for value in self.weights.values())
            assert self.reference == set(self.keys) - {self.keys[j] for j in basis}
            reset_seen.append(reason)

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    monkeypatch.setattr(sk.Devex, "step", sticky)
    monkeypatch.setattr(sk.Devex, "reset", observe_reset)
    result = call(norm(matrix, rhs, [1]), SolveOptions())
    assert fired and result.status == "optimal"
    assert result.diagnostics["primal_feasibility_rechecks"] == 1
    assert result.diagnostics["primal_feasibility_recoveries"] == 1
    assert reset_seen == ["primal_feasibility"]
    trace = result.diagnostics["last_pivot_trace"]
    assert trace["outcome"] == "recovered" and trace["run_identity"][1] == "phase_two"
    leaving = next(
        p for p in trace["coordinate_projections"] if p["position"] == trace["leaving_position"]
    )
    assert leaving["predicted_new_basic"] == trace["theta"] > 0
    assert trace["old_state_residual"]["within_bound"]
    assert trace["direction_residual"]["within_bound"]
    assert trace["predicted_new_state_residual"]["within_bound"]
    assert trace["fresh_after_residual"]["within_bound"]
    assert (
        trace["after_recheck_factor"]["generation"] > trace["before_recheck_factor"]["generation"]
    )
    assert trace["after_recheck_factor"]["last_refactor_reason"] == "primal_feasibility"
    assert trace["predicted_primal_threshold"] == pytest.approx(
        1e-7 * (1 + max(abs(p["predicted_new_basic"]) for p in trace["coordinate_projections"]))
    )
    if kind == "eta":
        assert trace["committed_factor"]["eta_chain_length"] == 1
        assert trace["minimum_computed_ratio"] == 0.5
        assert trace["second_computed_ratio_including_ties"] == 1
    else:
        assert trace["committed_factor"]["eta_chain_length"] == 0
        assert trace["committed_factor"]["last_refactor_reason"] == "growth"


def test_persistent_primal_failure_rebuilds_current_basis_once_and_retains_trace(monkeypatch):
    original = sf.SparseFactor.solve

    def injected(self, rhs, transpose=False):
        answer = original(self, rhs, transpose)
        if not transpose and self.matrix.nnz == 3 and np.array_equal(rhs, [1, 1]):
            answer = answer.copy()
            answer[0] = -1
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "numerical_failure" and result.iterations == 1
    assert result.diagnostics["primal_feasibility_rechecks"] == 1
    assert result.diagnostics["refactorizations_by_reason"]["primal_feasibility"] == 1
    trace = result.diagnostics["last_pivot_trace"]
    assert trace["outcome"] == "persistent_failure"
    assert trace["before_argmin_position"] == trace["after_argmin_position"] == 0
    assert trace["coordinate_projections"][0]["fresh_after_rebase"] == -1
    assert not trace["fresh_after_residual"]["within_bound"]


def test_ordinary_pivots_do_not_compute_observation_residuals_or_extra_lu(monkeypatch):
    def forbidden(*args):
        raise AssertionError("Observation residual computed on the ordinary pivot path")

    monkeypatch.setattr(sk, "_residual_observation", forbidden)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "optimal" and result.diagnostics["base_factorizations"] == 1
    assert "last_pivot_trace" not in result.diagnostics


def test_phase_one_pivot_observation_cannot_authorize_phase_two_recovery(monkeypatch):
    original = sf.SparseFactor.solve

    def injected(self, rhs, transpose=False):
        answer = original(self, rhs, transpose)
        if not transpose and self.counters["base_factorizations"] >= 2:
            return -np.ones_like(answer)
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    result = call(norm([[1]], [1], [-1], [">="]), SolveOptions())
    assert result.status == "numerical_failure" and result.diagnostics["primal_pivots"] == 1
    assert result.diagnostics["lost_feasibility_without_matching_pivot"]
    assert "primal_feasibility_rechecks" not in result.diagnostics
    assert "last_pivot_trace" not in result.diagnostics


def test_backward_error_bound_is_observed_separately_from_primal_sign():
    matrix = csr_matrix([[1, 1], [1, 1 + 1e-8]])
    truth = np.array([0.001, 1.0])
    bad = np.array([-0.001, 1.002])
    rhs = matrix @ truth
    observed = sk._residual_observation(matrix, rhs, bad)
    assert observed["within_bound"]
    expected = 1e-10 * (1 + np.max(abs(rhs)) + np.max(abs(matrix) @ abs(bad)))
    assert observed["bound"] == expected
    assert min(bad) < -1e-7 * (1 + np.max(abs(bad)))


def test_primal_recheck_preserves_rejected_candidates_and_blocks_false_optimal(monkeypatch):
    original = sf.SparseFactor.solve
    fired, bad_sent = False, False

    def injected(self, rhs, transpose=False):
        nonlocal fired, bad_sent
        answer = original(self, rhs, transpose)
        if (
            not fired
            and not transpose
            and self.counters.get("basis_replacements") == 1
            and np.array_equal(rhs, [0, 0, 0, 1])
        ):
            fired = True
            self.refactor(reason="injected_rebase_with_rejected_candidate")
            return original(self, rhs, transpose)
        if fired and not bad_sent and not transpose and np.array_equal(rhs, [0, 1e4, 1, 1]):
            bad_sent = True
            answer = answer.copy()
            answer[0] = -1
        if fired and transpose and self.last_refactor_reason == "primal_feasibility":
            return np.full(4, 1e9)
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    model = norm([[1e-8, 0, 0], [1e4, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 1e4, 1, 1], [3, 2, 1])
    result = call(model, SolveOptions())
    assert fired and bad_sent and result.status == "numerical_failure"
    assert "Rejected entering history" in result.reason
    trace = result.diagnostics["last_pivot_trace"]
    assert trace["outcome"] == "recovered"
    assert (
        trace["rejected_before_recheck"]
        == trace["rejected_after_recheck"]
        == (("variable", "x0", 1),)
    )


def test_pivot_trace_keeps_both_pre_and_post_rebase_failure_coordinates():
    n, leaving = 20, 19
    old_matrix = sk.canonical(np.eye(n))
    dense_new = np.eye(n)
    dense_new[:, leaving] = 1
    new_matrix = sk.canonical(dense_new)
    old_keys = tuple(("old", i) for i in range(n))
    new_keys = tuple(("new", i) for i in range(n))
    observation = sk._PivotObservation(
        old_matrix,
        np.ones(n),
        np.ones(n),
        np.ones(n),
        np.ones(n),
        1,
        leaving,
        old_keys,
        new_keys,
        new_keys[leaving],
        (1, "phase_two", "primal"),
        "primal",
        1e-10,
        1e-7,
        {"generation": 1},
        new_matrix,
        {"generation": 1},
    )
    before_values = np.r_[-np.arange(1, 9), np.ones(12)]
    after_values = np.r_[np.arange(100, 108), np.arange(12)]
    before = {
        "xb": before_values,
        "matrix": new_matrix,
        "metadata": {"generation": 1},
        "ptol": 1e-7 * (1 + max(abs(before_values))),
    }
    after = {
        "xb": after_values,
        "matrix": new_matrix,
        "metadata": {"generation": 2},
        "ptol": 1e-7 * (1 + max(abs(after_values))),
    }
    trace = observation.trace(before, after, "recovered")
    projections = {p["position"]: p for p in trace["coordinate_projections"]}
    assert len(projections) == 17
    assert set(projections) == set(range(16)) | {leaving}
    assert trace["before_argmin_position"] == 7 and trace["after_argmin_position"] == 8
    original_failure = projections[7]
    assert original_failure["old_xb"] == original_failure["old_direction"] == 1
    assert original_failure["old_raw_ratio"] == 1
    assert original_failure["predicted_new_basic"] == 0
    assert original_failure["fresh_before_rebase"] == -8
    assert original_failure["fresh_after_rebase"] == 107
