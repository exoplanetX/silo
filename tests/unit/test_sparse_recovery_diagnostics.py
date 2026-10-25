"""Pure observer toys: no public SILO solve, frozen CAP run or external optimizer."""

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.sparse import csc_matrix  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "recovery_diagnostics", ROOT / "scripts/sparse_program/recovery_diagnostics.py"
)
rd = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rd)
COUNTS = {
    "unit_tests": 0,
    "public_solve_started": 0,
    "native_kernel_started": 0,
    "actual_sparse_lu_probes": 0,
    "fake_lu_factories": 0,
}


@pytest.fixture(autouse=True)
def receipt():
    yield
    COUNTS["unit_tests"] += 1
    if path := os.environ.get("SILO_RECOVERY_DIAGNOSTIC_TEST_COUNTS"):
        Path(path).write_text(json.dumps(COUNTS), encoding="utf-8")


def fake_lu(matrix, **kwargs):
    COUNTS["fake_lu_factories"] += 1
    assert isinstance(matrix, csc_matrix) and kwargs == {"permc_spec": "COLAMD"}

    class LU:
        L = U = csc_matrix(np.eye(matrix.shape[0]))

        def solve(self, rhs, trans="N"):
            assert trans in ("N", "T")
            return np.array(rhs, copy=True)  # All probe toys have B=I.

    return LU()


def sample_state():
    return {
        "B": csc_matrix(np.eye(2)),
        "b": np.array([1.0, 2.0]),
        "cB": np.zeros(2),
        "xb": np.array([1.0, 2.0]),
        "d": np.array([0.1, 1.0]),
        "dual": np.zeros(2),
        "rc": np.array([1.0, 0.0, 0.0]),
        "working_cost": np.array([1.0, 0.0, 0.0]),
        "standard_cost": np.array([2.0, 0.0, 0.0]),
        "entering_column": np.array([0.1, 1.0]),
        "row_scale": np.ones(2),
        "row_flips": np.ones(2),
        "col_scale": np.ones(1),
        "row_map": np.arange(2),
        "meta": {
            "trigger_position": 1,
            "primal_tolerance": 1e-7,
            "pivot_tolerance": 1e-10,
            "native_factor_nnz": 4,
            "generation": 3,
            "state_generation": 3,
            "iterations": 7,
            "phase": "phase_two",
            "run_identity": (1, "phase_two", "primal"),
            "basis_keys": (("slack", "r0"), ("slack", "r1")),
        },
    }


def test_all_positive_blockers_keep_tiny_constraint_and_expose_stable_nonminimal():
    xb, direction = np.array([0.0, 1.0]), np.array([1e-12, 1.0])
    arrays, summary = rd.blockers(xb, direction, 1e-7, 1e-10)
    assert arrays["positions"].tolist() == [0, 1]
    assert arrays["clamped_ratio"].tolist() == [0, 1]
    assert summary["all_true_minimal_pivots_unsafe"]
    assert summary["all_candidates_examined"]
    assert summary["stable_feasible_nonminimal_count"] == 1
    assert summary["stable_feasible_nonminimal_first8"][0]["position"] == 1
    assert arrays["candidate_min"][1] == -1e-12
    assert np.array_equal(xb, [0, 1]) and np.array_equal(direction, [1e-12, 1])


def test_near_distinct_computed_ratios_are_observed_without_fuzzy_ties():
    _, summary = rd.blockers(np.array([1.0, 1.0 + 1e-12]), np.ones(2), 1e-7, 1e-10)
    assert summary["true_minimal_positions"] == [0]
    assert not summary["all_true_minimal_pivots_unsafe"]


def test_negative_rho_amplification_uses_actual_new_basic_coordinates():
    xb, direction = np.array([-3e-8, 1.0]), np.array([0.1, -1e8])
    y, info = rd.candidate(xb, direction, 0, 1e-7)
    assert info["rho"] == pytest.approx(-3e-7)
    assert y[0] == info["rho"] and y[1] == pytest.approx(-29)
    assert info["minimum"] < -info["ptol"] and not info["algebraic_feasible"]
    arrays, _ = rd.blockers(xb, direction, 1e-7, 1e-10)
    assert arrays["positions"].tolist() == [0]
    assert arrays["clamped_ratio"].tolist() == [0]


@pytest.mark.parametrize("direction", [np.array([-1.0, 0.0]), np.array([np.inf, 1.0])])
def test_empty_or_nonfinite_blockers_have_strict_json_summaries(direction):
    arrays, summary = rd.blockers(np.ones(2), direction, 1e-7, 1e-10)
    json.dumps(rd.clean(summary), allow_nan=False)
    assert len(arrays["positions"]) == int(np.count_nonzero(direction > 0))
    if np.isinf(direction).any():
        assert not arrays["candidate_finite"].any()


def test_deadline_retains_full_blocker_set_with_explicit_partial_analysis(monkeypatch):
    monkeypatch.setattr(rd, "perf_counter", lambda: 10)
    arrays, summary = rd.blockers(np.ones(3), np.ones(3), 1e-7, 1e-10, deadline=9)
    assert arrays["positions"].tolist() == [0, 1, 2]
    assert summary["candidate_rows_examined"] == 0 and not summary["all_candidates_examined"]
    with pytest.raises(rd.PrefixStop):
        rd.check_time(9)


def test_capture_saves_sparse_data_costs_probes_and_max_three_states(tmp_path):
    recorder = rd.Recorder(tmp_path, float("inf"), "synthetic", fake_lu)
    state = sample_state()
    before = {k: v.copy() for k, v in state.items() if isinstance(v, np.ndarray)}
    for name in ("first_unsafe", "first_negative", "terminal"):
        meta = recorder.capture(name, state)
        assert meta["probe_status"] == "completed_same_B_independent_sparse_LU"
        assert meta["probe_plus_owner_factor_nnz"] == 8
    assert recorder.capture("fourth_forbidden", state) is None
    assert len(list(tmp_path.glob("state-[0-9].npz"))) == 3
    assert recorder.counts["probe_lu_started"] == recorder.counts["probe_lu_completed"] == 3
    for name in ("xb", "dual", "d"):
        assert (
            recorder.counts[f"probe_{name}_started"]
            == recorder.counts[f"probe_{name}_completed"]
            == 3
        )
    for name, expected in before.items():
        assert np.array_equal(state[name], expected)
    with np.load(tmp_path / "state-0.npz", allow_pickle=False) as data:
        assert data["B_shape"].tolist() == [2, 2] and data["B_data"].tolist() == [1, 1]
        assert np.array_equal(data["working_cost"], state["working_cost"])
        assert np.array_equal(data["standard_cost"], state["standard_cost"])
    assert rd.sha(tmp_path / "state-0.npz") == recorder.snapshots[0]["state_sha256"]
    packet = json.loads((tmp_path / "prefix.json").read_text())
    assert packet["oracle_reads"] == 0 and len(packet["snapshots"]) == 3


def test_after_probe_lu_deadline_preserves_partial_raw_files_and_actual_calls(
    tmp_path, monkeypatch
):
    now = [0.0]
    monkeypatch.setattr(rd, "perf_counter", lambda: now[0])

    def late(*args, **kwargs):
        value = fake_lu(*args, **kwargs)
        now[0] = 2
        return value

    recorder = rd.Recorder(tmp_path, 1, "synthetic", late)
    with pytest.raises(rd.PrefixStop):
        recorder.capture("first", sample_state())
    assert (tmp_path / "state-0.npz").exists()
    packet = json.loads((tmp_path / "prefix.json").read_text())
    assert packet["snapshots"][0]["probe_status"] == "observer_deadline_partial"
    assert packet["counts"] == {"probe_lu_started": 1, "probe_lu_completed": 1}


def test_failed_probe_is_observational_and_retains_raw_snapshot(tmp_path):
    def singular(*args, **kwargs):
        raise RuntimeError("synthetic singular factor")

    recorder = rd.Recorder(tmp_path, float("inf"), "synthetic", singular)
    meta = recorder.capture("first", sample_state())
    assert meta["probe_status"] == "probe_failed"
    assert recorder.counts == {"probe_lu_started": 1}
    assert (tmp_path / "state-0.npz").exists()


def test_hooks_return_exact_original_objects_and_restore_on_prefix_stop():
    raw_result = {"rho": 0, "valid": True}
    kernel_result, lu_result = object(), object()
    kernel = SimpleNamespace(
        pivot_safe=lambda *a: False,
        _raw_primal_candidate=lambda *a: raw_result,
        solve_canonical=lambda *a: kernel_result,
    )
    factor = SimpleNamespace(splu=lambda *a: lu_result)
    original = kernel.__dict__.copy(), factor.splu

    class Recorder:
        last_frame = None

        def event(self, name):
            pass

        def observe(self, *args):
            pass

    recorder = Recorder()
    with pytest.raises(rd.PrefixStop), rd.Hooks(recorder, kernel, factor):
        assert kernel.pivot_safe(np.ones(2), 0, 1e-10) is False
        assert kernel._raw_primal_candidate(np.ones(2), np.ones(2), 0, 1e-7) is raw_result
        assert kernel.solve_canonical(None) is kernel_result
        assert factor.splu(None) is lu_result
        raise rd.PrefixStop("synthetic prefix")
    assert kernel.__dict__ == original[0] and factor.splu is original[1]
    assert not issubclass(rd.PrefixStop, Exception)
    recorder.observe = lambda *args: (_ for _ in ()).throw(MemoryError("observer allocation"))
    with pytest.raises(rd.ObserverFailure), rd.Hooks(recorder, kernel, factor):
        kernel.pivot_safe(np.ones(2), 0, 1e-10)
    assert kernel.__dict__ == original[0] and factor.splu is original[1]


def test_manifest_payload_identity_reads_no_oracle(tmp_path, monkeypatch):
    path = tmp_path / "tests/fixtures"
    path.mkdir(parents=True)
    payload = path / "synthetic.json"
    payload.write_text('{"variables": []}')
    manifest = path / "sparse_program_manifest.json"
    record = {
        "id": "CAP-FLOW-01",
        "payload_path": "tests/fixtures/synthetic.json",
        "payload_sha256": rd.sha(payload),
        "options": {"presolve": False},
    }
    manifest.write_text(json.dumps({"cases": [record]}))
    original_bytes, original_text = Path.read_bytes, Path.read_text

    def guarded_bytes(self, *args, **kwargs):
        assert "oracle" not in self.name.lower()
        return original_bytes(self, *args, **kwargs)

    def guarded_text(self, *args, **kwargs):
        assert "oracle" not in self.name.lower()
        return original_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_text)
    model, options, identity = rd.load_input(tmp_path, "CAP-FLOW-01")
    assert model == {"variables": []} and options == {"presolve": False}
    assert identity["payload_sha256"] == record["payload_sha256"]
    payload.write_text('{"variables": [1]}')
    with pytest.raises(ValueError, match="SHA"):
        rd.load_input(tmp_path, "CAP-FLOW-01")


def test_frame_extraction_does_not_call_get_factor_and_keeps_phase_costs_distinct(tmp_path):
    state = sample_state()
    factor = SimpleNamespace(matrix=state["B"], generation=3, etas=[], _lu_nnz=4, counters={})

    def get_factor():
        if factor is not None:
            raise AssertionError("Observer called factor construction")
        return factor

    normalized = SimpleNamespace(
        row_scale=np.ones(2), col_scale=np.ones(1), column_origins=((0, 1),)
    )
    outer = SimpleNamespace(
        f_code=SimpleNamespace(co_name="solve_canonical"),
        f_back=None,
        f_locals={
            "norm": normalized,
            "row_map": [0, 1],
            "row_keys": ("r0", "r1"),
            "flips": np.ones(2),
            "c": state["standard_cost"],
            "run_number": 1,
        },
    )
    values = {
        "get_factor": get_factor,
        "a": csc_matrix([[0.1, 1, 0], [1, 0, 1]]),
        "entering": 0,
        "basis": [1, 2],
        "keys": ("x", "s0", "s1"),
        "b": state["b"],
        "xb": state["xb"],
        "direction": state["d"],
        "lam": state["dual"],
        "rc": state["rc"],
        "cost": state["working_cost"],
        "iterations": 7,
        "run_identity": (1, "phase_one", "primal"),
        "generation": 3,
        "mode": "primal",
        "options": SimpleNamespace(primal_tolerance=1e-7, pivot_tolerance=1e-10),
        "pricing": SimpleNamespace(bland=True, degenerate=2, visited={"old"}),
        "rejected": set(),
    }
    frame = SimpleNamespace(
        f_locals=values,
        f_back=outer,
        f_code=SimpleNamespace(co_name="run"),
        f_globals={"__name__": "silo.lp.sparse_kernel"},
    )
    assert rd.run_frame(frame) is frame
    extracted = rd.state_from_frame(frame, 1)
    assert extracted["meta"]["generation"] == extracted["meta"]["state_generation"] == 3
    assert np.array_equal(extracted["working_cost"], state["working_cost"])
    assert np.array_equal(extracted["standard_cost"], state["standard_cost"])
    recorder = rd.Recorder(tmp_path, float("inf"), "synthetic", fake_lu)
    recorder.observe(frame, 1, "first_unsafe_true_minimal_blocker")
    values["iterations"] += 1
    recorder.observe(frame, 1, "first_unsafe_true_minimal_blocker")
    assert len(recorder.snapshots) == 1  # Repeated phase I observation makes no matrix log.
    recorder.observe(frame, 1, "first_negative_rho_or_raw_amplification")
    values["run_identity"], values["iterations"] = (2, "phase_two", "primal"), 9
    outer.f_locals["run_number"] = 2
    # Ordinary safe/valid events can supply terminal context, but cannot be
    # relabeled as a later harmful observation or consume its reserved slot.
    recorder.observe(frame, 1, None)
    recorder.observe(frame, 1, None)
    assert len(recorder.snapshots) == 2
    with pytest.raises(rd.PrefixStop, match="three_sparse"):
        recorder.observe(frame, 1, "first_unsafe_true_minimal_blocker")
    assert [s["kind"] for s in recorder.snapshots] == [
        "first_unsafe_true_minimal_blocker",
        "first_negative_rho_or_raw_amplification",
        "later_phase_two_harmful",
    ]
    terminal = rd.Recorder(tmp_path, float("inf"), "synthetic", fake_lu)
    terminal.last_frame, terminal.last_signature = frame, rd.signature(frame)
    factor = None  # A real phase boundary can clear this closure after run().
    terminal.terminal()
    assert terminal.terminal_unavailable_reason == "factor_cleared_after_observation"
    assert not terminal.snapshots
    terminal.last_frame = None
    recorder.last_frame = None
