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


def test_bad_direction_rebases_without_committing_old_leaving_row():
    factor = make(np.eye(2))
    identity, generation = factor.identity, factor.generation
    with pytest.raises(sf.FactorRetry, match="direction_residual"):
        factor.replace_column(1, [2, 0.1], np.array([0.1, 2.0]))
    assert factor.identity == identity and factor.generation == generation + 1
    assert factor.counters.get("basis_replacements", 0) == 0
    direction = factor.solve_B([2, 0.1])
    assert np.argmin(1 / direction) == 0  # The new true blocker differs.
    factor.replace_column(0, [2, 0.1], direction, expected_generation=factor.generation)
    assert factor.counters["refactorizations_by_reason"] == {"direction_residual": 1}
    assert_solves(factor)


def test_rejected_pivot_leaves_matrix_unchanged():
    factor = make(np.eye(2))
    original = factor.identity
    with pytest.raises(sf.FactorRetry, match="unsafe_pivot"):
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


def test_generation_changes_only_after_successful_rebase():
    factor = make(np.eye(2))
    first = factor.generation
    factor.refactor(reason="test_success")
    assert factor.generation == first + 1
    assert factor.last_refactor_reason == "test_success"
    identity = factor.identity
    with pytest.raises(np.linalg.LinAlgError):
        factor.refactor(csc_matrix([[1, 1], [1, 1]]), "test_failure")
    assert factor.generation == first + 1 and factor.identity == identity
    assert factor.last_refactor_reason == "test_success"


def test_stale_generation_never_commits_even_with_valid_direction():
    factor = make(np.eye(2))
    generation = factor.generation
    direction = factor.solve_B([1, 1])
    factor.refactor(reason="before_commit")
    identity = factor.identity
    with pytest.raises(sf.FactorRetry, match="stale_commit_generation"):
        factor.replace_column(0, [1, 1], direction, expected_generation=generation)
    assert factor.identity == identity and factor.counters.get("basis_replacements", 0) == 0


def test_chain_limit_failed_rebuild_is_an_uncommitted_atomic_operation(monkeypatch):
    factor = make(np.eye(2), max_factor_updates=1)
    factor.replace_column(0, [1, 1])
    identity, generation = factor.identity, factor.generation

    def fail(*args, **kwargs):
        raise RuntimeError("injected chain-limit failure")

    monkeypatch.setattr(sf, "splu", fail)
    with pytest.raises(np.linalg.LinAlgError, match="injected chain-limit"):
        factor.replace_column(1, [1, 2])
    assert factor.identity == identity and factor.generation == generation
    assert factor.counters["basis_replacements"] == factor.counters["eta_updates"] == 1
    assert len(factor.etas) == 1


def test_staged_eta_shares_readonly_numerics_but_owns_mutable_containers():
    owner = make(np.eye(3))
    owner.replace_column(0, [1, 0.1, 0.2])
    identity, lu, generation, etas = owner.identity, owner.lu, owner.generation, owner.etas
    direction = np.array([0.1, 1, 0.2])
    staged = owner.stage_column(
        1, owner.matrix @ direction, direction, expected_generation=owner.generation
    )
    trial = staged.factor
    assert trial.lu is lu and trial.etas is not etas and len(trial.etas) == 2
    assert trial.etas[0][1] is etas[0][1]
    assert trial.counters is not owner.counters
    assert trial.counters["refactorizations_by_reason"] is not owner.counters.get(
        "refactorizations_by_reason"
    )
    assert owner.identity == identity and owner.lu is lu and owner.generation == generation
    assert len(owner.etas) == 1 and owner.counters["basis_replacements"] == 1
    trial.solve_B([1, 2, 3])
    staged.close()
    staged.close()
    assert owner.identity == identity and owner.lu is lu and owner.etas is etas
    assert owner.counters["basis_replacements"] == owner.counters["eta_updates"] == 1
    assert owner.counters["trial_eta_updates"] == owner.counters["rejected_trial_eta_updates"] == 1


def test_staged_growth_discard_keeps_old_lu_and_counts_actual_work():
    owner = make(np.eye(2))
    old_lu, old_matrix, old_generation = owner.lu, owner.matrix, owner.generation
    before = ACTUAL["splu_calls"]
    staged = owner.stage_column(0, [1e9, 0.1], [1e9, 0.1], expected_generation=owner.generation)
    assert staged.factor.lu is not old_lu and staged.factor.generation > old_generation
    assert owner.lu is old_lu and owner.matrix is old_matrix and owner.generation == old_generation
    assert owner.counters["base_factorizations"] == 1
    staged.factor.solve_B([1, 1])
    trial_lu = staged.factor.lu
    staged.factor.refactor(reason="second_trial_rebase")
    staged.close()
    assert owner.counters["base_factorizations"] == 1 + ACTUAL["splu_calls"] - before == 3
    assert owner.counters.get("basis_replacements", 0) == owner.counters.get("eta_updates", 0) == 0
    assert owner.counters["rejected_trial_refactorizations"] == 2
    assert owner.counters["simultaneous_factor_nnz_peak"] >= (
        old_lu.L.nnz
        + old_lu.U.nnz
        + trial_lu.L.nnz
        + trial_lu.U.nnz
        + staged.factor.lu.L.nnz
        + staged.factor.lu.U.nnz
    )
    assert owner.lu is old_lu and owner.matrix is old_matrix


def test_accepting_staged_eta_publishes_once_without_copying_lu():
    owner = make(np.eye(2))
    staged = owner.stage_column(0, [1, 1], [1, 1], expected_generation=owner.generation)
    assert owner.counters.get("basis_replacements", 0) == owner.counters.get("eta_updates", 0) == 0
    staged.close(accepted=True)
    assert staged.factor.lu is owner.lu and not staged.factor._staged
    assert staged.factor.counters is owner.counters
    assert staged.factor._retained_lu is None
    assert owner.counters["basis_replacements"] == owner.counters["eta_updates"] == 1
    assert owner.counters["candidate_basis_acceptances"] == 1
    assert owner.counters.get("rejected_trial_eta_updates", 0) == 0


def test_candidate_over_budget_lu_fill_remains_in_actual_peak_after_discard():
    owner = make(np.eye(3), max_factor_updates=0, max_factor_nnz=6)
    old_lu, old_matrix, old_generation = owner.lu, owner.matrix, owner.generation
    with pytest.raises(sf.FactorResourceError, match="fill"):
        owner.stage_column(0, [1, 1, 1], [1, 1, 1], expected_generation=owner.generation)
    assert owner.lu is old_lu and owner.matrix is old_matrix and owner.generation == old_generation
    assert owner.counters["base_factorizations"] == 2
    assert owner.counters["rejected_factor_nnz"] == owner.counters["factor_nnz_peak"] == 8
    assert owner.counters["simultaneous_factor_nnz_peak"] == 14
    assert owner.counters.get("basis_replacements", 0) == owner.counters.get("eta_updates", 0) == 0


def test_post_splu_deadline_keeps_actual_fill_peaks_without_publishing_candidate(monkeypatch):
    owner = make(np.eye(3), max_factor_updates=0)
    lu, matrix, etas, generation = owner.lu, owner.matrix, owner.etas, owner.generation
    cache = {"factor": owner, "basis": (0, 1, 2)}
    original_splu = sf.splu
    now, produced = [0.0], []
    owner.deadline = 1.0
    monkeypatch.setattr(sf, "perf_counter", lambda: now[0])

    def late_splu(*args, **kwargs):
        result = original_splu(*args, **kwargs)
        produced.append(result.L.nnz + result.U.nnz)
        now[0] = 2.0  # Real LU exists before the next explicit deadline check.
        return result

    monkeypatch.setattr(sf, "splu", late_splu)
    before = ACTUAL["splu_calls"]
    with pytest.raises(sf.FactorDeadline, match="time_limit"):
        owner.stage_column(0, [1, 1, 1], [1, 1, 1], expected_generation=generation)
    assert produced == [8] and ACTUAL["splu_calls"] - before == 1
    assert owner.lu is lu and owner.matrix is matrix and owner.etas is etas
    assert owner.generation == generation and cache == {"factor": owner, "basis": (0, 1, 2)}
    assert owner.counters["base_factorizations"] == 2
    assert owner.counters["factor_nnz_peak"] == 8
    assert owner.counters["simultaneous_factor_nnz_peak"] == 14
    assert owner.counters.get("basis_replacements", 0) == owner.counters.get("eta_updates", 0) == 0
    assert "candidate_entering_rejections" not in owner.counters
