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

CALLS = {
    "kernel_started": 0,
    "kernel_completed": 0,
    "native_roots": 0,
    "splu_calls": 0,
    "candidate_state_started": 0,
    "candidate_state_completed": 0,
    "same_basis_refresh_started": 0,
    "same_basis_refresh_completed": 0,
}


@pytest.fixture(autouse=True)
def observed_lu(monkeypatch):
    original = sf.splu
    original_state = sk._candidate_state
    original_refresh = sf.SparseFactor.stage_refactor

    def observed(*args, **kwargs):
        CALLS["splu_calls"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(sf, "splu", observed)

    def candidate(*args, **kwargs):
        CALLS["candidate_state_started"] += 1
        result = original_state(*args, **kwargs)
        CALLS["candidate_state_completed"] += 1
        return result

    monkeypatch.setattr(sk, "_candidate_state", candidate)

    def refreshed(*args, **kwargs):
        CALLS["same_basis_refresh_started"] += 1
        result = original_refresh(*args, **kwargs)
        CALLS["same_basis_refresh_completed"] += 1
        return result

    monkeypatch.setattr(sf.SparseFactor, "stage_refactor", refreshed)
    yield
    if path := os.environ.get("SILO_KERNEL_TEST_COUNTS"):
        Path(path).write_text(json.dumps(CALLS), encoding="utf-8")


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
        [rhs[i] if side in (">=", "=") else -np.inf for i, side in enumerate(senses)], dtype=float
    )
    row_upper = np.array(
        [rhs[i] if side in ("<=", "=") else np.inf for i, side in enumerate(senses)], dtype=float
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
            lower=lower,
            upper=upper,
            a=a,
            row_names=tuple(f"r{i}" for i in range(m)),
            row_lower=row_lower,
            row_upper=row_upper,
        ),
    )


def ordinary():
    return norm([[1, 1], [1, 0], [0, 1]], [4, 2, 3], [3, 2])


def test_rr02_second_predicted_leaving_can_succeed_without_same_basis_refresh(monkeypatch):
    original = sk._candidate_state
    attempted = []

    def checked(factor, matrix, rhs, cost, basis):
        result = original(factor, matrix, rhs, cost, basis)
        attempted.append(tuple(basis))
        if basis[0] == 0:
            return -2 * np.ones(len(rhs)), *result[1:]
        return result

    monkeypatch.setattr(sk, "_candidate_state", checked)
    result = call(norm([[1], [1]], [1, 1], [1]), SolveOptions())
    assert result.status == "optimal" and result.point[0] == pytest.approx(1)
    assert len(attempted) == 2 and attempted[0][0] == attempted[1][1] == 0
    d = result.diagnostics
    assert d["candidate_basis_attempts"] == d["full_candidate_trials"] == 2
    assert d["candidate_basis_discards"] == d["candidate_basis_acceptances"] == 1
    assert d["full_candidate_trials_per_entering_basis_peak"] == 2
    assert d.get("same_basis_refresh_attempts", 0) == 0 and result.iterations == 1


def test_rr02_two_rejections_do_not_try_a_possible_third_row(monkeypatch):
    original = sk._candidate_state
    attempted = []

    def checked(factor, matrix, rhs, cost, basis):
        result = original(factor, matrix, rhs, cost, basis)
        attempted.append(tuple(basis))
        if basis[2] != 0:
            return -2 * np.ones(len(rhs)), *result[1:]
        return result  # This feasible third candidate must remain untried.

    monkeypatch.setattr(sk, "_candidate_state", checked)
    result = call(norm([[1], [1], [1]], [1, 1, 1], [1]), SolveOptions())
    d = result.diagnostics
    assert result.status == "numerical_failure" and result.point is None
    assert len(attempted) == 2 and all(b[2] != 0 for b in attempted)
    assert d["candidate_basis_attempts"] == d["candidate_basis_discards"] == 2
    assert d["full_candidate_trials"] == d["full_candidate_trials_per_entering_basis_peak"] == 2
    assert d["last_entering_rejection"]["reason"] == "candidate_budget_exhausted"
    assert d["last_entering_rejection"]["untried_rows_not_proved_infeasible"]
    assert d.get("same_basis_refresh_attempts", 0) == 0 and result.iterations == 0


def test_rr02_same_basis_refresh_leaves_only_one_new_basis_trial(monkeypatch):
    raw, stage, state = (
        sk._raw_primal_candidate,
        sf.SparseFactor.stage_refactor,
        sk._candidate_state,
    )
    refreshed = []

    def observed_stage(self, *args, **kwargs):
        result = stage(self, *args, **kwargs)
        refreshed.append(result)
        return result

    def predicted(*args):
        result = raw(*args)
        return result if refreshed else {**result, "valid": False}

    def checked(factor, matrix, rhs, cost, basis):
        result = state(factor, matrix, rhs, cost, basis)
        return (-2 * np.ones(len(rhs)), *result[1:]) if 0 in basis else result

    monkeypatch.setattr(sf.SparseFactor, "stage_refactor", observed_stage)
    monkeypatch.setattr(sk, "_raw_primal_candidate", predicted)
    monkeypatch.setattr(sk, "_candidate_state", checked)
    result = call(norm([[1], [1]], [1, 1], [1]), SolveOptions())
    d = result.diagnostics
    assert result.status == "numerical_failure" and result.iterations == 0
    assert d["same_basis_refresh_attempts"] == d["same_basis_refresh_acceptances"] == 1
    assert d["candidate_basis_attempts"] == d["candidate_basis_discards"] == 1
    assert d["full_candidate_trials"] == d["full_candidate_trials_per_entering_basis_peak"] == 2
    assert d["pending_state_consumptions"] == 1


def test_rr02_prestage_generation_mismatch_does_not_consume_credit(monkeypatch):
    original = sf.SparseFactor.stage_column
    calls = []

    def stage(self, *args, **kwargs):
        calls.append(self.generation)
        if len(calls) == 1:
            self.refactor(reason="prestage_generation_test")
            raise sf.FactorRetry("prestage_generation_test", self.generation)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(sf.SparseFactor, "stage_column", stage)
    result = call(norm([[1], [1]], [1, 1], [1]), SolveOptions())
    d = result.diagnostics
    assert result.status == "optimal" and len(calls) == 2 and calls[1] > calls[0]
    assert d["candidate_basis_attempts"] == d["full_candidate_trials"] == 1
    assert d["full_candidate_trials_per_entering_basis_peak"] == 1


def test_rr02_old_primal_policy_frame_cannot_reuse_numeric_cache():
    model = ordinary()
    first = call(model, SolveOptions())
    old = {
        **first._factor_state,
        "frame": {**first._factor_state["frame"], "policy": sf.FACTOR_POLICY},
    }
    result = call(model, SolveOptions(), snapshot=first.snapshot, factor_state=old)
    assert result.status == "optimal" and np.allclose(result.point, [2, 2])
    assert result.diagnostics["cache_invalidations"] == 1
    assert result.diagnostics["cross_solve_reuses"] == 0
    assert result._factor_state["frame"]["policy"] == (
        sf.FACTOR_POLICY,
        sk.PRIMAL_POLICY,
        sk.DUAL_EXIT_POLICY,
        sk.PRICING_POLICY,
    )


def test_degenerate_steps_do_not_replace_actual_repeated_basis_evidence():
    keys = (("variable", "x0", 1), ("variable", "x1", 1), ("variable", "x2", 1))
    counters = {}
    pricing = sk.Devex(keys, [0], counters)
    for index in range(3):
        pricing.basis_seen([index])
        pricing.step(0, 1e-7)
    assert pricing.degenerate == 3 and not pricing.bland
    pricing.basis_seen([0])
    pricing.basis_seen([0])
    assert pricing.bland and counters["bland_triggers"] == 1
    assert counters["bland_trigger_reasons"] == {"repeated_basis": 1}
    history = pricing.visited.copy()
    pricing.reset([0], "residual")
    assert pricing.bland and pricing.visited == history
    assert pricing.entering([1, 2], np.array([0, 1, 100]), [0]) == 1
    pricing.fresh_phase(keys, [0], "public_solve", preserve=True)
    assert not pricing.bland and not pricing.visited and pricing.degenerate == 0
    assert pricing.entering([1, 2], np.array([0, 1, 100]), [0]) == 2


@pytest.mark.parametrize("has_blocker", [False, True])
def test_mapped_only_failure_never_issues_farkas_or_silently_cold_retries(monkeypatch, has_blocker):
    first = call(norm([[1]], [1], [1]), SolveOptions())
    mapped = SimpleNamespace(
        rows=(0,) if has_blocker else (), primal_feasible=False,
        violations=1, maximum_scaled_violation=2e-7,
    )
    monkeypatch.setattr(sk, "mapped_blockers", lambda *args: mapped)
    result = call(norm([[1]], [1], [1]), SolveOptions(), first.snapshot)
    assert result.status == "numerical_failure" and result.diagnostics["proof_kind"] is None
    assert result.diagnostics["cold_fallbacks"] == 0
    assert result.reason == (
        "mapped_dual_no_safe_pivot" if has_blocker else "unmapped_original_primal_violation"
    )


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
    second_model.data.row_upper[0] = 4.25
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
    original_take = sk._PendingState.take
    original_step, original_reset = sk.Devex.step, sk.Devex.reset
    fired, reset_seen = False, []
    rhs = [1, 1] if kind == "eta" else [1, 1e9]
    matrix = [[1], [2]] if kind == "eta" else [[1], [1e9]]

    def injected(self, values, transpose=False):
        nonlocal fired
        answer = original(self, values, transpose)
        if (
            not self._staged
            and not fired
            and not transpose
            and self.matrix.nnz == 3
            and np.array_equal(values, rhs)
        ):
            fired = True
            answer = answer.copy()
            answer[0] = -1
        return answer

    def corrupted_after_publication(self, identity):
        nonlocal fired
        values = original_take(self, identity)
        if values is not None and not fired:
            fired = True
            xb = values[0].copy()
            xb[0] = -1
            return (xb, *values[1:])
        return values

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
    monkeypatch.setattr(sk._PendingState, "take", corrupted_after_publication)
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
    original_take = sk._PendingState.take

    def injected(self, rhs, transpose=False):
        answer = original(self, rhs, transpose)
        if (
            not self._staged
            and not transpose
            and self.matrix.nnz == 3
            and np.array_equal(rhs, [1, 1])
        ):
            answer = answer.copy()
            answer[0] = -1
        return answer

    def corrupted_after_publication(self, identity):
        values = original_take(self, identity)
        if values is not None:
            xb = values[0].copy()
            xb[0] = -1
            return (xb, *values[1:])
        return values

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    monkeypatch.setattr(sk._PendingState, "take", corrupted_after_publication)
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


@pytest.mark.parametrize(
    "xb,direction",
    [
        ([-3e-8, 1], [0.1, -1e8]),
        ([-4.928232505779105e-14, 1], [2.788239580513479e-10, 1.0696428176597692]),
    ],
)
def test_raw_gate_catches_negative_zero_step_and_tiny_safe_pivot_amplification(xb, direction):
    xb, direction = np.array(xb), np.array(direction)
    assert min(xb) >= -1e-7 * (1 + max(abs(xb)))
    assert sf.pivot_safe(direction, 0, 1e-10)
    assert max(xb[0], 0) / direction[0] == 0
    checked = sk._raw_primal_candidate(xb, direction, 0, 1e-7)
    assert checked["rho"] < 0 and not checked["valid"]
    assert checked["reason"] == "raw_primal_infeasible"
    assert checked["minimum_basic"] < -checked["primal_threshold"]


@pytest.mark.parametrize(
    "xb,direction,tolerance,reason",
    [
        ([1e308, 1], [1e-308, 1], 1e-7, "nonfinite_raw_step"),
        ([1e308, 1], [1, 1e308], 1e-7, "nonfinite_raw_coordinates"),
        ([1e308, 0], [1, 0], 1e308, "nonfinite_raw_threshold"),
    ],
)
def test_raw_gate_conservatively_handles_nonfinite_intermediate_values(
    xb, direction, tolerance, reason
):
    checked = sk._raw_primal_candidate(np.array(xb), np.array(direction), 0, tolerance)
    assert not checked["valid"] and checked["reason"] == reason


@pytest.mark.parametrize("bland", [False, True])
def test_raw_failure_refreshes_old_basis_once_and_fully_recomputes_state(monkeypatch, bland):
    original = sf.SparseFactor.solve
    original_phase, original_reset = sk.Devex.fresh_phase, sk.Devex.reset
    fired, old_state_generations, update_calls = False, [], []
    original_update = sk.Devex.update

    def injected(self, rhs, transpose=False):
        nonlocal fired
        answer = original(self, rhs, transpose)
        if not transpose and np.array_equal(rhs, [0, 1]) and self.matrix.nnz == 2:
            old_state_generations.append(self.generation)
            if not fired:
                fired = True
                answer = answer.copy()
                answer[0] = -3e-8
        return answer

    def history(self, *args, **kwargs):
        original_phase(self, *args, **kwargs)
        self.bland, self.degenerate = bland, 2
        self.visited.add(("raw gate retains history",))

    def reset(self, basis, reason):
        if reason == "raw_candidate_feasibility":
            previous = self.bland, self.visited.copy(), self.degenerate
        original_reset(self, basis, reason)
        if reason == "raw_candidate_feasibility":
            assert previous == (self.bland, self.visited, self.degenerate)
            assert all(v == 1 for v in self.weights.values())

    def update(self, *args):
        update_calls.append(True)
        return original_update(self, *args)

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    monkeypatch.setattr(sk.Devex, "fresh_phase", history)
    monkeypatch.setattr(sk.Devex, "reset", reset)
    monkeypatch.setattr(sk.Devex, "update", update)
    result = call(norm([[0.1], [-1e8]], [0, 1], [1]), SolveOptions())
    assert fired and result.status == "optimal" and result.point[0] == 0
    assert len(old_state_generations) == 2 and old_state_generations[0] < old_state_generations[1]
    assert result.diagnostics["raw_candidate_failures"] == 1
    assert result.diagnostics["raw_candidate_refreshes"] == 1
    assert result.diagnostics["refactorizations_by_reason"]["raw_candidate_feasibility"] == 1
    assert result.diagnostics["basis_replacements"] == result.iterations == 1
    assert update_calls == [True]  # Failed raw candidate never reaches the Devex BTRAN.
    assert result.diagnostics.get("raw_candidate_rejections", 0) == 0


def test_all_raw_candidates_rejected_cannot_commit_or_declare_optimal(monkeypatch):
    original = sf.SparseFactor.solve

    def injected(self, rhs, transpose=False):
        answer = original(self, rhs, transpose)
        if not transpose and np.array_equal(rhs, [0, 1]):
            answer = answer.copy()
            answer[0] = -3e-8
        return answer

    def forbidden(*args, **kwargs):
        raise AssertionError("Rejected raw candidate reached an unapproved mutation")

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    monkeypatch.setattr(sf.SparseFactor, "replace_column", forbidden)
    monkeypatch.setattr(sk.Devex, "update", forbidden)
    monkeypatch.setattr(sk._PivotObservation, "__init__", forbidden)
    result = call(norm([[0.1], [-1e8]], [0, 1], [1]), SolveOptions())
    assert result.status == "numerical_failure" and result.iterations == 0
    assert result.diagnostics["raw_candidate_refreshes"] == 1
    assert result.diagnostics["raw_candidate_rejections"] == 1
    assert result.diagnostics["raw_candidate_failures"] == 2
    assert result.diagnostics["basis_replacements"] == result.diagnostics["eta_updates"] == 0
    assert result.diagnostics["last_raw_candidate_rejection"]["entering_key"] == (
        "variable",
        "x0",
        1,
    )


def test_raw_rejection_selects_another_entering_and_resets_after_accepted_pivot(monkeypatch):
    original = sf.SparseFactor.solve
    original_replace = sf.SparseFactor.replace_column
    accepted_from_initial_basis = []

    def injected(self, rhs, transpose=False):
        answer = original(self, rhs, transpose)
        if (
            not transpose
            and self.counters.get("basis_replacements", 0) == 0
            and self.scope_calls == 1  # Corrupt state BTRAN's partner, never a direction RHS.
            and np.array_equal(rhs, [0, 1, 1])
        ):
            answer = answer.copy()
            answer[0] = -3e-8
        return answer

    def replaced(self, position, column, *args, **kwargs):
        if self.counters.get("basis_replacements", 0) == 0:
            accepted_from_initial_basis.append(tuple(column))
        return original_replace(self, position, column, *args, **kwargs)

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    monkeypatch.setattr(sf.SparseFactor, "replace_column", replaced)
    result = call(norm([[0.1, 0], [-1e8, 1], [0, 1]], [0, 1, 1], [2, 1]), SolveOptions())
    assert result.status == "optimal" and np.allclose(result.point, [0, 1])
    assert result.diagnostics["raw_candidate_rejections"] == 1
    assert accepted_from_initial_basis == [(0, 1, 1)]
    assert result.diagnostics["basis_replacements"] == 2


def test_passing_raw_gate_commits_once_without_extra_linear_equations():
    before = CALLS["splu_calls"]
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "optimal" and result.point[0] == 0.5
    assert result.diagnostics["raw_candidate_checks"] == result.iterations == 1
    assert result.diagnostics["basis_replacements"] == result.diagnostics["eta_updates"] == 1
    assert result.diagnostics["triangular_solves"] == 6
    assert CALLS["splu_calls"] - before == result.diagnostics["base_factorizations"] == 1


@pytest.mark.parametrize("phase", ["dual", "cleanup"])
def test_raw_primal_gate_is_not_applied_to_dual_or_cleanup(monkeypatch, phase):
    if phase == "dual":
        first = call(ordinary(), SolveOptions())

    def forbidden(*args):
        raise AssertionError("Primal raw gate was invoked outside the primal run")

    monkeypatch.setattr(sk, "_raw_primal_candidate", forbidden)
    if phase == "dual":
        larger = norm([[1, 1], [1, 0], [0, 1], [1, 0]], [4, 2, 3, 1.5], [3, 2])
        result = call(larger, SolveOptions(), first.snapshot, factor_state=first._factor_state)
        assert result.diagnostics["dual_pivots"] == 1
    else:
        result = call(norm([[-1, -1]], [0], [-1, -2], ["="]), SolveOptions())
        assert result.diagnostics["artificial_cleanup_pivots"] == 1
    assert result.status == "optimal"


def test_zero_artificial_cleanup_can_change_phase_one_dual_feasibility():
    # The only nonnegative solution is zero. Phase I starts optimal at zero;
    # replacing artificial0 by x0 is a legal zero pivot with rc(x0)=-1.
    # The new basis has Phase-I rc(x1)=1/2, yet its primal objective stays zero.
    model = norm([[-2, -1], [1, 1]], [0, 0], [-1, -2], ["=", "="])
    result = call(model, SolveOptions())
    assert result.status == "optimal", result.reason
    assert np.array_equal(result.point, [0, 0])
    assert result.diagnostics["artificial_cleanup_pivots"] == 2
    assert all(key[0] != "artificial" for key in result.column_keys)


@pytest.mark.parametrize("fault", ["primal", "artificial", "nonfinite"])
def test_cleanup_invalid_full_state_cannot_drop_artificials_or_issue_farkas(monkeypatch, fault):
    original_solve, original_replace = sf.SparseFactor.solve, sf.SparseFactor.replace_column
    replacements, injected = [], []

    def replaced(self, *args, **kwargs):
        value = original_replace(self, *args, **kwargs)
        replacements.append(True)
        return value

    def solve(self, rhs, transpose=False):
        value = original_solve(self, rhs, transpose)
        if replacements and not injected and not transpose:
            value = value.copy()
            if fault == "primal":
                value[0] = -1
            elif fault == "artificial":
                value[1] = 1
            else:
                value[1] = np.nan
            injected.append(True)
        return value

    monkeypatch.setattr(sf.SparseFactor, "replace_column", replaced)
    monkeypatch.setattr(sf.SparseFactor, "solve", solve)
    result = call(norm([[-2, -1], [1, 1]], [0, 0], [-1, -2], ["=", "="]), SolveOptions())
    assert injected and len(replacements) == 1
    assert result.status == "numerical_failure"
    assert result.diagnostics["proof_kind"] is None and result.snapshot is None


def test_cleanup_positive_artificial_mass_cannot_cancel_with_tolerated_negative(monkeypatch):
    original_solve, original_replace = sf.SparseFactor.solve, sf.SparseFactor.replace_column
    replacements, injected = [], []

    def replaced(self, *args, **kwargs):
        value = original_replace(self, *args, **kwargs)
        replacements.append(True)
        return value

    def solve(self, rhs, transpose=False):
        value = original_solve(self, rhs, transpose)
        if replacements and not injected and not transpose:
            # Signed sum0.75eps passes the old objective test, while positive
            # artificial mass1.5eps must fail. The negative coordinate is legal.
            value = np.array([0, 1.5e-7, -0.75e-7])
            injected.append(True)
        return value

    monkeypatch.setattr(sf.SparseFactor, "replace_column", replaced)
    monkeypatch.setattr(sf.SparseFactor, "solve", solve)
    result = call(norm(-np.eye(3), [0, 0, 0], [-1, -1, -1], ["="] * 3), SolveOptions())
    assert injected and len(replacements) == 1
    assert result.status == "numerical_failure" and "zero artificial mass" in result.reason
    state = result.diagnostics["last_cleanup_state"]
    assert state["minimum_basic"] >= -state["primal_threshold"]
    assert state["positive_artificial_mass"] == 1.5e-7
    assert result.diagnostics["proof_kind"] is None


def test_last_cleanup_pivot_checks_actual_primal_before_removing_artificial(monkeypatch):
    original_solve, original_replace = sf.SparseFactor.solve, sf.SparseFactor.replace_column
    replacements, phases = [], []

    def replaced(self, *args, **kwargs):
        value = original_replace(self, *args, **kwargs)
        replacements.append(True)
        return value

    def solve(self, rhs, transpose=False):
        value = original_solve(self, rhs, transpose)
        return -np.ones_like(value) if replacements and not transpose else value

    original_phase = sk.Devex.fresh_phase

    def phase(self, keys, basis, reason, **kwargs):
        phases.append(reason)
        return original_phase(self, keys, basis, reason, **kwargs)

    monkeypatch.setattr(sf.SparseFactor, "replace_column", replaced)
    monkeypatch.setattr(sf.SparseFactor, "solve", solve)
    monkeypatch.setattr(sk.Devex, "fresh_phase", phase)
    result = call(norm([[-1, -1]], [0], [-1, -2], ["="]), SolveOptions())
    assert len(replacements) == 1 and "phase_two" not in phases
    assert result.status == "numerical_failure" and "primal feasibility" in result.reason
    assert result.snapshot is None and result.diagnostics["proof_kind"] is None


def test_staged_state_can_pass_backward_error_but_fail_primal_without_publishing(monkeypatch):
    owner = sf.SparseFactor(sk.canonical(np.eye(2)), SolveOptions(), {})
    old_lu, old_matrix, old_etas, old_generation = (
        owner.lu,
        owner.matrix,
        owner.etas,
        owner.generation,
    )
    rhs = np.array([1.001, 1e-8])
    direction = np.array([1, 1e-8])
    assert sk._raw_primal_candidate(rhs, direction, 1, 1e-7)["valid"]
    original = sf.SparseFactor.solve

    def injected(self, values, transpose=False):
        answer = original(self, values, transpose)
        if self._staged and self.matrix.nnz == 3 and not transpose:
            answer = np.array([-0.001, 1.002])
            assert self._residual(values, answer, False)[0]
        return answer

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    staged = owner.stage_column(1, direction, direction, expected_generation=owner.generation)
    matrix = sk.canonical([[1, 1, 0], [1e-8, 0, 1]])
    values = sk._candidate_state(staged.factor, matrix, rhs, np.array([1.0, 0.0, 0.0]), [1, 0])
    assert np.min(values[0]) < -1e-7 * (1 + max(abs(values[0])))
    staged.close()
    assert owner.lu is old_lu and owner.matrix is old_matrix and owner.etas is old_etas
    assert owner.generation == old_generation
    assert owner.counters.get("basis_replacements", 0) == owner.counters.get("eta_updates", 0) == 0
    assert owner.counters["rejected_trial_eta_updates"] == 1


@pytest.mark.parametrize("kind", ["eta", "growth"])
def test_staged_primal_rejections_keep_authoritative_state_and_all_real_cost(monkeypatch, kind):
    original_solve, original_stage, original_phase = (
        sf.SparseFactor.solve,
        sf.SparseFactor.stage_column,
        sk.Devex.fresh_phase,
    )
    original_close, original_update = sf.StagedBasis.close, sk.Devex.update
    owners, pricing_objects = [], []
    snapshots = {}

    def staged(self, *args, **kwargs):
        snapshots[id(self)] = self.lu, self.matrix, self.etas, self.generation
        owners.append(self)
        return original_stage(self, *args, **kwargs)

    def closed(self, accepted=False):
        original_close(self, accepted)
        if not accepted:
            lu, matrix, etas, generation = snapshots[id(self.owner)]
            assert self.owner.lu is lu and self.owner.matrix is matrix and self.owner.etas is etas
            assert self.owner.generation == generation

    def solve(self, rhs, transpose=False):
        value = original_solve(self, rhs, transpose)
        if self._staged and self.matrix.nnz == 3 and not transpose:
            value = value.copy()
            value[0] = -1
        return value

    def phase(self, *args, **kwargs):
        original_phase(self, *args, **kwargs)
        self.bland, self.degenerate = True, 2
        self.visited.add(("staged rejection retains history",))
        pricing_objects.append(self)

    def update(self, *args):
        original_update(self, *args)
        return dict.fromkeys(self.keys, 777.0)

    def no_step(*args):
        raise AssertionError("A rejected candidate performed a successful pivot step")

    monkeypatch.setattr(sf.SparseFactor, "stage_column", staged)
    monkeypatch.setattr(sf.StagedBasis, "close", closed)
    monkeypatch.setattr(sf.SparseFactor, "solve", solve)
    monkeypatch.setattr(sk.Devex, "fresh_phase", phase)
    monkeypatch.setattr(sk.Devex, "update", update)
    monkeypatch.setattr(sk.Devex, "step", no_step)
    model = (
        norm([[1], [1e-8]], [1.001, 1e-8], [1])
        if kind == "eta"
        else norm([[1], [1e9]], [1, 1e9], [1])
    )
    result = call(model, SolveOptions())
    assert result.status == "numerical_failure" and result.iterations == 0
    d = result.diagnostics
    attempts = 1 if kind == "eta" else 2
    assert d.get("candidate_old_basis_refreshes", 0) == 0
    assert d["candidate_basis_attempts"] == d["candidate_basis_discards"] == attempts
    assert d["basis_replacements"] == d["eta_updates"] == 0
    assert d.get("pending_state_consumptions", 0) == d.get("same_basis_refresh_acceptances", 0) == 0
    assert (
        d["full_candidate_trials"] == d["full_candidate_trials_per_entering_basis_peak"] == attempts
    )
    assert "last_pivot_trace" not in d
    assert d["triangular_solves"] > 0
    assert pricing_objects[-1].bland and pricing_objects[-1].degenerate == 2
    assert ("staged rejection retains history",) in pricing_objects[-1].visited
    assert all(value == 1 for value in pricing_objects[-1].weights.values())
    if kind == "eta":
        assert d["rejected_trial_eta_updates"] == 1
        assert d["base_factorizations"] == 1
    else:
        assert d["rejected_trial_refactorizations"] == 2
        assert d["base_factorizations"] == 3


@pytest.mark.parametrize("after_rebase", ["feasible", "infeasible", "never_stable"])
def test_candidate_bt_rebase_requires_a_complete_final_generation_state(monkeypatch, after_rebase):
    original_solve, original_update = sf.SparseFactor.solve, sk.Devex.update

    def injected(self, rhs, transpose=False):
        answer = original_solve(self, rhs, transpose)
        if (
            self._staged
            and self.matrix.nnz == 3
            and transpose
            and (after_rebase == "never_stable" or not getattr(self, "_test_bt_rebased", False))
        ):
            self._test_bt_rebased = True
            self.refactor(reason="injected_candidate_bt_rebase")
            return original_solve(self, rhs, transpose)
        if (
            self._staged
            and self.matrix.nnz == 3
            and not transpose
            and getattr(self, "_test_bt_rebased", False)
            and after_rebase == "infeasible"
        ):
            return -np.ones_like(answer)
        return answer

    def update(self, *args):
        original_update(self, *args)
        return dict.fromkeys(self.keys, 777.0)

    monkeypatch.setattr(sf.SparseFactor, "solve", injected)
    monkeypatch.setattr(sk.Devex, "update", update)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    d = result.diagnostics
    if after_rebase == "feasible":
        assert result.status == "optimal" and result.point[0] == 0.5
        assert d["basis_replacements"] == d["eta_updates"] == result.iterations == 1
        assert d["candidate_state_generation_restarts"] == d["pending_state_consumptions"] == 1
        assert d["factor_generation"] == 2 and d["eta_chain_length"] == 0
        assert d["refactorizations_by_reason"]["injected_candidate_bt_rebase"] == 1
        assert all(value == 1 for value in result._factor_state["pricing"].weights.values())
    else:
        assert result.status == "numerical_failure" and result.iterations == 0
        assert d["basis_replacements"] == d["eta_updates"] == 0
        assert d["candidate_entering_rejections"] == 1 and d["rejected_trial_eta_updates"] == 1
        assert d["candidate_basis_attempts"] == d["full_candidate_trials"] == 1
        assert d["candidate_state_generation_restarts"] == (
            3 if after_rebase == "never_stable" else 1
        )


@pytest.mark.parametrize(
    "error,reason",
    [
        (sf.FactorDeadline("injected"), "time_limit"),
        (sf.FactorResourceError("injected"), "resource_limit"),
        (MemoryError("injected"), "resource_limit"),
    ],
)
def test_candidate_deadline_and_resources_are_not_normal_rejections(monkeypatch, error, reason):
    def failed(*args):
        raise error

    monkeypatch.setattr(sk, "_candidate_state", failed)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert (result.status, result.reason) == ("limit", reason)
    assert (
        result.iterations
        == result.diagnostics["basis_replacements"]
        == result.diagnostics["eta_updates"]
        == 0
    )
    assert result.diagnostics["candidate_basis_discards"] == 1
    assert result.diagnostics["rejected_trial_eta_updates"] == 1
    assert "candidate_entering_rejections" not in result.diagnostics


def test_candidate_singular_rebuild_preserves_owner_and_counts_failed_lu(monkeypatch):
    original = sf.splu
    original_stage = sf.SparseFactor.stage_column
    owners = []

    def stage(self, *args, **kwargs):
        owners.append((self, self.lu, self.matrix, self.etas, self.generation))
        return original_stage(self, *args, **kwargs)

    def singular(matrix, **kwargs):
        if matrix.nnz == 3:
            return original(sk.canonical(np.zeros(matrix.shape)), **kwargs)
        return original(matrix, **kwargs)

    monkeypatch.setattr(sf, "splu", singular)
    monkeypatch.setattr(sf.SparseFactor, "stage_column", stage)
    result = call(norm([[1], [2]], [1, 1], [1]), replace(SolveOptions(), max_factor_updates=0))
    d = result.diagnostics
    assert result.status == "numerical_failure" and result.iterations == 0
    assert d["basis_replacements"] == d["eta_updates"] == 0
    assert d["base_factorizations"] == 2
    assert d["refactorizations_by_reason"]["updates_disabled"] == 1
    assert d["candidate_entering_rejections"] == 1
    assert len(owners) == d["candidate_basis_attempts"] == d["full_candidate_trials"] == 1
    owner, lu, matrix, etas, generation = owners[0]
    assert owner.lu is lu and owner.matrix is matrix and owner.etas is etas
    assert owner.generation == generation == 1 and not result._factor_state


@pytest.mark.parametrize(
    "changed", ["public", "run", "phase", "matrix", "basis", "generation", "rhs", "cost"]
)
def test_pending_full_state_identity_changes_discard_it_once(changed):
    context = (object(), (1, "phase_two", "primal"), object())
    basis, generation = (("variable", "x", 1),), 1
    rhs, cost = np.array([1.0]), np.array([2.0])
    initial = sk._pending_identity(context, basis, generation, rhs, cost)
    values = (np.array([1.0]), np.array([2.0]), np.array([0.0]), generation)
    pending = sk._PendingState(initial, values)
    if changed == "public":
        context = object(), context[1], context[2]
    elif changed == "run":
        context = context[0], (2, "phase_two", "primal"), context[2]
    elif changed == "phase":
        context = context[0], (1, "phase_one", "primal"), context[2]
    elif changed == "matrix":
        context = context[0], context[1], object()
    elif changed == "basis":
        basis = (("slack", "r"),)
    elif changed == "generation":
        generation += 1
    elif changed == "rhs":
        rhs[0] += 1  # Same mutable ndarray identity, changed actual content.
    else:
        cost[0] += 1
    assert pending.take(sk._pending_identity(context, basis, generation, rhs, cost)) is None
    assert pending.take(initial) is None
    valid = sk._PendingState(initial, values)
    assert valid.take(initial) is values and valid.take(initial) is None


def test_pending_mismatch_runs_ordinary_complete_state_and_valid_path_adds_no_solves(monkeypatch):
    normal = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert normal.diagnostics["pending_state_consumptions"] == 1
    assert normal.diagnostics["triangular_solves"] == 6
    original = sk._PendingState.take

    def invalidated(self, identity):
        return original(self, None)

    monkeypatch.setattr(sk._PendingState, "take", invalidated)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "optimal" and result.point[0] == 0.5
    assert result.diagnostics["pending_state_invalidations"] == 1
    assert result.diagnostics["triangular_solves"] == 8


@pytest.mark.parametrize("mode", ["dual", "cleanup"])
def test_nonprimal_paths_neither_stage_nor_consume_primal_pending(monkeypatch, mode):
    if mode == "dual":
        first = call(ordinary(), SolveOptions())

    def forbidden(*args, **kwargs):
        raise AssertionError("A nonprimal path accessed staged primal state")

    monkeypatch.setattr(sf.SparseFactor, "stage_column", forbidden)
    monkeypatch.setattr(sk._PendingState, "take", forbidden)
    if mode == "dual":
        model = norm([[1, 1], [1, 0], [0, 1], [1, 0]], [4, 2, 3, 1.5], [3, 2])
        result = call(model, SolveOptions(), first.snapshot, factor_state=first._factor_state)
    else:
        result = call(norm([[-1, -1]], [0], [-1, -2], ["="]), SolveOptions())
    assert result.status == "optimal"


def test_staged_rejection_allows_another_entering_and_clears_r_after_acceptance(monkeypatch):
    original = sk._candidate_state

    def rejected_first_basis(factor, matrix, rhs, cost, basis):
        values = original(factor, matrix, rhs, cost, basis)
        if basis == [0, 3]:
            return (np.array([-1.0, 1.0]), *values[1:])
        return values

    monkeypatch.setattr(sk, "_candidate_state", rejected_first_basis)
    result = call(norm([[1, 0], [0, 1]], [1, 1], [2, 1]), SolveOptions())
    assert result.status == "optimal" and np.allclose(result.point, [1, 1])
    d = result.diagnostics
    assert d["candidate_entering_rejections"] == 1
    assert d.get("candidate_old_basis_refreshes", 0) == 0
    assert d["candidate_basis_attempts"] == 3
    assert d["basis_replacements"] == d["eta_updates"] == result.iterations == 2
    assert d["rejected_trial_eta_updates"] == 1


def test_rejected_later_candidate_does_not_overwrite_last_accepted_pivot(monkeypatch):
    original_state, original_observation, original_step = (
        sk._candidate_state,
        sk._PivotObservation.__init__,
        sk.Devex.step,
    )
    observations, steps = [], []

    def reject_second_entering(factor, matrix, rhs, cost, basis):
        values = original_state(factor, matrix, rhs, cost, basis)
        return (np.array([1.0, -1.0]), *values[1:]) if basis == [0, 1] else values

    def observe(self, *args, **kwargs):
        original_observation(self, *args, **kwargs)
        observations.append(self)

    def step(self, *args):
        original_step(self, *args)
        steps.append(args)

    monkeypatch.setattr(sk, "_candidate_state", reject_second_entering)
    monkeypatch.setattr(sk._PivotObservation, "__init__", observe)
    monkeypatch.setattr(sk.Devex, "step", step)
    result = call(norm([[1, 0], [0, 1]], [1, 1], [2, 1]), SolveOptions())
    assert result.status == "numerical_failure" and result.iterations == 1
    assert result.basis == (0, 3)
    assert len(observations) == len(steps) == 1
    assert observations[0].new_keys == (("variable", "x0", 1), ("slack", ("row", "r1", "upper")))
    assert result.diagnostics["basis_replacements"] == result.diagnostics["eta_updates"] == 1
    assert result.diagnostics["last_candidate_rejection"]["entering_key"] == ("variable", "x1", 1)


def test_candidate_residual_recovery_changes_only_trial_and_publishes_final_generation(monkeypatch):
    original = sf.SparseFactor.stage_column
    owners = []

    def staged(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        owners.append((self, self.lu, self.matrix, self.generation))
        actual = result.factor.lu

        class BadLU:
            L, U = actual.L, actual.U

            def solve(self, rhs, trans="N"):
                return np.zeros_like(rhs)

        result.factor.lu = BadLU()
        return result

    monkeypatch.setattr(sf.SparseFactor, "stage_column", staged)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "optimal" and result.point[0] == 0.5
    d = result.diagnostics
    assert d["candidate_state_generation_restarts"] == 1
    assert d["refinement_steps"] == 2 and d["refactorizations_by_reason"]["residual"] == 1
    assert d["basis_replacements"] == d["eta_updates"] == 1
    assert d["eta_chain_length"] == 0 and d["factor_generation"] == 2
    old_owner, old_lu, old_matrix, old_generation = owners[0]
    assert (
        old_owner.lu is old_lu
        and old_owner.matrix is old_matrix
        and old_owner.generation == old_generation
    )
    assert result._factor_state["factor"] is not old_owner


def test_accepted_trial_without_rebuild_applies_precomputed_devex_weights(monkeypatch):
    original = sk.Devex.update

    def update(self, *args):
        original(self, *args)
        return dict.fromkeys(self.keys, 777.0)

    monkeypatch.setattr(sk.Devex, "update", update)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    assert result.status == "optimal" and result.diagnostics["base_factorizations"] == 1
    assert all(value == 777 for value in result._factor_state["pricing"].weights.values())


def _trigger_voluntary_refresh_once(monkeypatch, reason):
    original_raw, original_safe, original_state = (
        sk._raw_primal_candidate,
        sk.pivot_safe,
        sk._candidate_state,
    )
    fired = []

    def raw(*args):
        result = original_raw(*args)
        if reason == "raw_candidate_feasibility" and not fired:
            fired.append(reason)
            return {**result, "valid": False, "reason": "injected_raw_rejection"}
        return result

    def safe(*args):
        result = original_safe(*args)
        if reason == "pivot_selection" and not fired:
            fired.append(reason)
            return False
        return result

    def state(factor, matrix, rhs, cost, basis):
        values = original_state(factor, matrix, rhs, cost, basis)
        if reason == "candidate_validation" and 0 in basis and not fired:
            fired.append(reason)
            return (-np.ones_like(values[0]), *values[1:])
        return values

    monkeypatch.setattr(sk, "_raw_primal_candidate", raw)
    monkeypatch.setattr(sk, "pivot_safe", safe)
    monkeypatch.setattr(sk, "_candidate_state", state)
    return fired


def _observe_same_basis_refresh(monkeypatch):
    original = sf.SparseFactor.stage_refactor
    owners = []

    def stage(self, *args, **kwargs):
        image = self, self.lu, self.matrix, self.etas, self.generation
        owners.append(image)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(sf.SparseFactor, "stage_refactor", stage)
    return owners


@pytest.mark.parametrize("reason", ["raw_candidate_feasibility", "pivot_selection"])
@pytest.mark.parametrize("accepted", [False, True])
def test_voluntary_preselection_refresh_validates_before_publish_on_both_paths(
    monkeypatch, reason, accepted
):
    fired = _trigger_voluntary_refresh_once(monkeypatch, reason)
    owners = _observe_same_basis_refresh(monkeypatch)
    original_state, original_take = sk._candidate_state, sk._PendingState.take
    original_phase, original_reset = sk.Devex.fresh_phase, sk.Devex.reset
    pending, pricings, resets = [], [], []

    def state(factor, matrix, rhs, cost, basis):
        values = original_state(factor, matrix, rhs, cost, basis)
        if not accepted and basis == [1, 2]:
            return (-np.ones_like(values[0]), *values[1:])
        return values

    def take(self, identity):
        result = original_take(self, identity)
        assert accepted  # A rejected refresh cannot leave consumable state.
        if result is not None:
            assert result[3] == identity[2]
            pending.append(identity)
        return result

    def phase(self, *args):
        original_phase(self, *args)
        self.bland, self.degenerate = True, 2
        self.visited.add(("voluntary refresh retains history",))
        pricings.append(self)

    def reset(self, basis, reset_reason):
        history = self.bland, self.visited.copy(), self.degenerate
        original_reset(self, basis, reset_reason)
        assert history == (self.bland, self.visited, self.degenerate)
        assert all(value == 1 for value in self.weights.values())
        resets.append(reset_reason)

    monkeypatch.setattr(sk, "_candidate_state", state)
    monkeypatch.setattr(sk._PendingState, "take", take)
    monkeypatch.setattr(sk.Devex, "fresh_phase", phase)
    monkeypatch.setattr(sk.Devex, "reset", reset)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    d = result.diagnostics
    assert fired == [reason] and len(owners) == 1
    owner, lu, matrix, etas, generation = owners[0]
    assert owner.lu is lu and owner.matrix is matrix and owner.etas is etas
    assert owner.generation == generation == 1
    assert d["same_basis_refresh_attempts"] == 1
    assert d.get("same_basis_refresh_acceptances", 0) == int(accepted)
    assert d.get("same_basis_refresh_discards", 0) == int(not accepted)
    assert d["base_factorizations"] == 2 and d["refactorizations_by_reason"][reason] == 1
    assert d["trial_refactorizations"] == 1
    assert d.get("rejected_trial_refactorizations", 0) == int(not accepted)
    assert d["simultaneous_factor_nnz_peak"] >= 2 * (lu.L.nnz + lu.U.nnz)
    assert d["basis_replacements"] == d["eta_updates"] == result.iterations == int(accepted)
    assert d.get("candidate_basis_acceptances", 0) == int(accepted)
    assert d.get("candidate_basis_attempts", 0) == int(accepted) + int(
        reason == "candidate_validation"
    )
    if accepted:
        assert result.status == "optimal" and result.point[0] == 0.5
        assert result._factor_state["factor"] is not owner and d["factor_generation"] == 2
        assert reason in resets and len(pending) == d["pending_state_consumptions"] == 2
        assert pending[0][1] == (
            ("slack", ("row", "r0", "upper")),
            ("slack", ("row", "r1", "upper")),
        )
    else:
        assert result.status == "numerical_failure" and result.basis == (1, 2)
        assert d["rejected_entering_columns"] == 1 and not pending
        assert "last_pivot_trace" not in d and not result._factor_state
        assert d["last_same_basis_refresh_rejection"]["authoritative_generation"] == 1
        assert pricings[-1].bland and pricings[-1].degenerate == 2
        assert ("voluntary refresh retains history",) in pricings[-1].visited
        assert "rejected_pivot" in resets


def test_rejected_new_basis_never_automatically_refreshes_same_basis(monkeypatch):
    fired = _trigger_voluntary_refresh_once(monkeypatch, "candidate_validation")
    owners = _observe_same_basis_refresh(monkeypatch)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    d = result.diagnostics
    assert fired == ["candidate_validation"] and not owners
    assert result.status == "numerical_failure" and result.basis == (1, 2)
    assert d["candidate_basis_attempts"] == d["candidate_basis_discards"] == 1
    assert d["full_candidate_trials"] == 1 and result.iterations == 0
    assert d["basis_replacements"] == d["eta_updates"] == 0
    assert d.get("same_basis_refresh_attempts", 0) == d.get("pending_state_consumptions", 0) == 0
    assert "last_pivot_trace" not in d and not result._factor_state


@pytest.mark.parametrize(
    "order",
    [
        ("raw_candidate_feasibility", "pivot_selection", "candidate_validation"),
        ("pivot_selection", "candidate_validation", "raw_candidate_feasibility"),
        ("candidate_validation", "raw_candidate_feasibility", "pivot_selection"),
    ],
)
def test_three_voluntary_paths_share_one_credit_and_keep_whole_entering_rejections(
    monkeypatch, order
):
    original_raw, original_safe, original_state = (
        sk._raw_primal_candidate,
        sk.pivot_safe,
        sk._candidate_state,
    )

    def raw(xb, direction, leaving, tolerance):
        result = original_raw(xb, direction, leaving, tolerance)
        return (
            {**result, "valid": False} if order[leaving] == "raw_candidate_feasibility" else result
        )

    def safe(direction, position, tolerance):
        return (
            original_safe(direction, position, tolerance) and order[position] != "pivot_selection"
        )

    def state(factor, matrix, rhs, cost, basis):
        values = original_state(factor, matrix, rhs, cost, basis)
        if basis == [3, 4, 5] or any(j < 3 and order[j] == "candidate_validation" for j in basis):
            return (-np.ones_like(values[0]), *values[1:])
        return values

    monkeypatch.setattr(sk, "_raw_primal_candidate", raw)
    monkeypatch.setattr(sk, "pivot_safe", safe)
    monkeypatch.setattr(sk, "_candidate_state", state)
    result = call(norm(np.eye(3), [1, 1, 1], [3, 2, 1]), SolveOptions())
    d = result.diagnostics
    assert (
        result.status == "numerical_failure"
        and result.iterations == 0
        and result.basis == (3, 4, 5)
    )
    assert d["same_basis_refresh_attempts"] == d["same_basis_refresh_discards"] == 1
    assert d["rejected_entering_columns"] == 3 and d["candidate_basis_attempts"] == 1
    assert d["basis_replacements"] == d["eta_updates"] == 0
    assert d["pivot_rejection_reasons"] == {
        "raw_candidate_feasibility": 1,
        "no_stable_harris_candidate": 1,
        "staged_basis_validation": 1,
    }
    expected_refresh = next(reason for reason in order if reason != "candidate_validation")
    assert d["last_same_basis_refresh_rejection"]["refresh_reason"] == expected_refresh
    assert d["full_candidate_trials"] == 2
    assert d["full_candidate_trials_per_entering_basis_peak"] == 1
    assert "pending_state_consumptions" not in d and d["factor_generation"] == 1


@pytest.mark.parametrize("after_rebase", ["feasible", "infeasible", "never_stable"])
def test_same_basis_bt_rebase_restarts_full_state_before_publish(monkeypatch, after_rebase):
    _trigger_voluntary_refresh_once(monkeypatch, "raw_candidate_feasibility")
    owners = _observe_same_basis_refresh(monkeypatch)
    original_state, original_solve = sk._candidate_state, sf.SparseFactor.solve

    def state(factor, matrix, rhs, cost, basis):
        if basis == [1, 2]:
            factor._test_refresh = True
        return original_state(factor, matrix, rhs, cost, basis)

    def solve(self, rhs, transpose=False):
        answer = original_solve(self, rhs, transpose)
        if getattr(self, "_test_refresh", False):
            if transpose and (
                after_rebase == "never_stable" or not getattr(self, "_test_done", False)
            ):
                self._test_done = True
                self.refactor(reason="injected_refresh_bt")
                return original_solve(self, rhs, transpose)
            if (
                not transpose
                and getattr(self, "_test_done", False)
                and after_rebase == "infeasible"
            ):
                return -np.ones_like(answer)
        return answer

    monkeypatch.setattr(sk, "_candidate_state", state)
    monkeypatch.setattr(sf.SparseFactor, "solve", solve)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    d = result.diagnostics
    assert d["candidate_state_generation_restarts"] == (3 if after_rebase == "never_stable" else 1)
    assert d["refactorizations_by_reason"]["injected_refresh_bt"] == (
        3 if after_rebase == "never_stable" else 1
    )
    assert "primal_feasibility" not in d["refactorizations_by_reason"]
    owner, lu, matrix, etas, generation = owners[0]
    assert (
        owner.lu is lu
        and owner.matrix is matrix
        and owner.etas is etas
        and owner.generation == generation
    )
    if after_rebase == "feasible":
        assert result.status == "optimal" and result.point[0] == 0.5
        assert d["factor_generation"] == 3 and d["pending_state_consumptions"] == 2
        assert d["basis_replacements"] == d["eta_updates"] == result.iterations == 1
    else:
        assert result.status == "numerical_failure" and result.iterations == 0
        assert d["same_basis_refresh_discards"] == d["rejected_entering_columns"] == 1
        assert d["basis_replacements"] == d["eta_updates"] == 0
        assert d["rejected_trial_refactorizations"] == (4 if after_rebase == "never_stable" else 2)


def test_rejected_same_basis_refresh_keeps_old_lu_and_allows_another_entering(monkeypatch):
    _trigger_voluntary_refresh_once(monkeypatch, "raw_candidate_feasibility")
    owners = _observe_same_basis_refresh(monkeypatch)
    original = sk._candidate_state

    def state(factor, matrix, rhs, cost, basis):
        values = original(factor, matrix, rhs, cost, basis)
        if basis == [2, 3]:
            return (-np.ones_like(values[0]), *values[1:])
        return values

    monkeypatch.setattr(sk, "_candidate_state", state)
    result = call(norm(np.eye(2), [1, 1], [2, 1]), SolveOptions())
    owner, old_lu, matrix, etas, generation = owners[0]
    d = result.diagnostics
    assert result.status == "optimal" and np.array_equal(result.point, [1, 1])
    assert owner.lu is old_lu and owner.matrix is matrix and owner.etas is etas
    assert owner.generation == generation == 1
    assert result._factor_state["factor"].lu is old_lu and d["factor_generation"] == 1
    assert d["same_basis_refresh_attempts"] == d["same_basis_refresh_discards"] == 1
    assert d["raw_candidate_rejections"] == 1 and d["candidate_basis_attempts"] == 2
    assert d["basis_replacements"] == d["eta_updates"] == result.iterations == 2


@pytest.mark.parametrize(
    "error,reason",
    [
        (sf.FactorDeadline("injected_refresh"), "time_limit"),
        (sf.FactorResourceError("injected_refresh"), "resource_limit"),
        (MemoryError("injected_refresh"), "resource_limit"),
        (np.linalg.LinAlgError("injected_refresh"), "numerical_failure"),
        (ValueError("programming_error"), None),
    ],
)
def test_same_basis_refresh_classifies_only_numeric_failures_as_rejections(
    monkeypatch, error, reason
):
    _trigger_voluntary_refresh_once(monkeypatch, "raw_candidate_feasibility")
    owners = _observe_same_basis_refresh(monkeypatch)
    original = sk._candidate_state

    def state(*args):
        original(*args)  # Real staged B/BT work must survive the failure.
        raise error

    monkeypatch.setattr(sk, "_candidate_state", state)
    if reason is None:
        with pytest.raises(ValueError, match="programming_error"):
            call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    else:
        result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
        assert result.status == ("numerical_failure" if reason == "numerical_failure" else "limit")
        if result.status == "limit":
            assert result.reason == reason and "rejected_entering_columns" not in result.diagnostics
        else:
            assert result.diagnostics["rejected_entering_columns"] == 1
    owner, lu, matrix, etas, generation = owners[0]
    assert (
        owner.lu is lu
        and owner.matrix is matrix
        and owner.etas is etas
        and owner.generation == generation
    )
    assert owner.counters["base_factorizations"] == 2 and owner.counters["triangular_solves"] == 5
    assert owner.counters["same_basis_refresh_discards"] == 1
    assert owner.counters["simultaneous_factor_nnz_peak"] == 8
    assert owner.counters["basis_replacements"] == owner.counters["eta_updates"] == 0


def test_failed_authoritative_residual_recovery_never_restores_untrusted_owner(monkeypatch):
    original_refactor = sf.SparseFactor.refactor
    owners = []

    def refactor(self, current_B=None, reason="structure"):
        original_refactor(self, current_B, reason)
        if reason == "initial":
            owners.append((self, self.lu, self.generation))

    def bad_raw(self, rhs, transpose=False):
        self._deadline()
        sf.increment(self.counters, "triangular_solves")
        return np.zeros_like(rhs)

    def forbidden(*args, **kwargs):
        raise AssertionError("Untrusted residual recovery tried a voluntary rollback")

    monkeypatch.setattr(sf.SparseFactor, "refactor", refactor)
    monkeypatch.setattr(sf.SparseFactor, "_raw", bad_raw)
    monkeypatch.setattr(sf.SparseFactor, "stage_refactor", forbidden)
    result = call(norm([[1], [2]], [1, 1], [1]), SolveOptions())
    owner, old_lu, old_generation = owners[0]
    assert result.status == "numerical_failure" and result.iterations == 0
    assert owner.lu is not old_lu and owner.generation == old_generation + 1
    assert result.diagnostics["refactorizations_by_reason"]["residual"] == 1
    assert result.diagnostics["base_factorizations"] == 2
    assert result.diagnostics["refinement_steps"] == 2
    assert "same_basis_refresh_attempts" not in result.diagnostics
