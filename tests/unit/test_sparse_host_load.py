"""Preflight gates and Windows observer/resource signature isolation."""

import copy
from pathlib import Path

import pytest


def test_quiet_host_requires_complete_readable_low_load_samples(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program.host_load import quiet_decision

    sample = {
        "host_total_fraction": 0.1,
        "other_compute": [{"pid": 123, "name": "python.exe", "core_fraction": 0.1}],
        "unreadable_compute": [],
    }
    samples = [copy.deepcopy(sample) for _ in range(10)]
    assert quiet_decision(samples)["quiet"]
    assert not quiet_decision(samples[:4])["quiet"]
    for key, value in (("host_total_fraction", 0.9), ("unreadable_compute", [123])):
        assert not quiet_decision([{**sample, key: value}] * 10)["quiet"]
    busy = copy.deepcopy(samples)
    for row in busy:
        row["other_compute"][0]["core_fraction"] = 0.8
    assert not quiet_decision(busy)["quiet"]


def test_quiet_host_counts_concurrent_processes_together(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program.host_load import quiet_decision

    row = {
        "host_total_fraction": 0.1,
        "unreadable_compute": [],
        "other_compute": [
            {"pid": i, "name": "python.exe", "core_fraction": 0.18} for i in range(4)
        ],
    }
    result = quiet_decision([row] * 10)
    assert result["maximum_process_mean_cores"] == pytest.approx(0.18)
    assert not result["quiet"] and result["mean_other_compute_cores"] == pytest.approx(0.72)


def grant():
    return {
        "kind": "human_warm4_recheck",
        "sha256": "b" * 64,
        "source_sha256": "a" * 64,
        "question_call": "explicit-human-reply",
        "previous_ceiling": 3,
        "new_ceiling": 4,
        "additional_rounds": 1,
        "fixed_children": 80,
        "modified_states": 1600,
        "initial_states": 80,
        "repetitions": 5,
        "child_seconds": 60,
        "child_memory_bytes": 1 << 30,
    }


def recovery_grant():
    return {
        "kind": "human_supervision_recovery",
        "sha256": "c" * 64,
        "source_sha256": "a" * 64,
        "question_call": "explicit-recovery-reply",
        "previous_warm_ceiling": 4,
        "new_warm_ceiling": 5,
        "additional_warm_rounds": 1,
        "previous_quality_ceiling": 3,
        "new_quality_ceiling": 4,
        "additional_quality_rounds": 1,
        "maximum_host_windows": 3,
        "inherited_host_windows": 1,
        "additional_host_windows": 2,
        "host_sample_seconds": 20,
        "fixed_children": 80,
        "modified_states": 1600,
        "initial_states": 80,
        "repetitions": 5,
        "child_seconds": 60,
        "child_memory_bytes": 1 << 30,
    }


def runtime_grant():
    return {
        **recovery_grant(),
        "kind": "human_runtime_stability_recovery",
        "sha256": "d" * 64,
        "previous_warm_ceiling": 5,
        "new_warm_ceiling": 6,
        "previous_quality_ceiling": 4,
        "new_quality_ceiling": 5,
        "previous_diagnostic_ceiling": 20,
        "new_diagnostic_ceiling": 22,
        "additional_diagnostic_batches": 2,
        "diagnostic_batch_seconds": 75,
        "diagnostic_child_seconds": 60,
        "diagnostic_public_calls": 21,
        "diagnostic_maximum_child_wall_seconds": 45,
        "frequency_relative_difference": 0.1,
        "maximum_host_windows": 4,
        "additional_host_windows": 3,
        "pause_onedrive_authorized": True,
        "exit_client_if_needed_authorized": True,
        "restore_original_sync_state_required": True,
        "predecessor_host_authority_sha256": "c" * 64,
    }


def runtime_events():
    return [grant(), recovery_grant(), runtime_grant()]


def runtime_frozen_events():
    return [
        *runtime_events(),
        {"kind": "command_started", "run": "q5", "quality5_authority_sha256": "d" * 64},
        {
            "kind": "command_finished",
            "sha256": "e" * 64,
            "run": "q5",
            "exit_code": 0,
            "stage": "SP4",
            "group": "quality",
        },
        {
            "kind": "runtime_tools_frozen",
            "authority_sha256": "d" * 64,
            "source_sha256": "a" * 64,
            "quality_finished_sha256": "e" * 64,
        },
    ]


def test_runtime_extension_keeps_original_caps_and_rejects_scope_or_lineage_drift(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    assert ledger.round_limits(runtime_events()) == {
        "capacity": 2,
        "netlib": 2,
        "warm": 6,
        "quality": 5,
        "diagnostic": 22,
    }
    for changed in (
        {"child_seconds": 75},
        {"new_diagnostic_ceiling": 23},
        {"predecessor_host_authority_sha256": "f" * 64},
    ):
        with pytest.raises(AssertionError):
            ledger.round_limits([grant(), recovery_grant(), {**runtime_grant(), **changed}])
    with pytest.raises(AssertionError):
        ledger.round_limits([*runtime_events(), runtime_grant()])


@pytest.mark.parametrize("bad", [None, "source", "command", "consumed", "ordinal"])
def test_fifth_quality_is_one_use_complete_command(monkeypatch, bad):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    events, source, used = runtime_events(), "a" * 64, 4
    argv = ["python", str(ledger.ROOT / "scripts/check_quality.py")]
    if bad == "source":
        source = "f" * 64
    elif bad == "command":
        argv = ["python", "-m", "pytest"]
    elif bad == "ordinal":
        used = 5
    elif bad == "consumed":
        events.append({"kind": "command_started", "quality5_authority_sha256": "d" * 64})
    if bad:
        with pytest.raises(AssertionError):
            ledger.validate_extended_quality_request(
                events, source, stage="SP4", used=used, argv=argv, ordinal=5
            )
    else:
        assert (
            ledger.validate_extended_quality_request(
                events, source, stage="SP4", used=used, argv=argv, ordinal=5
            )
            == "d" * 64
        )


@pytest.mark.parametrize("first_pass", [True, False, None])
def test_second_probe_requires_completed_qualified_first_probe(monkeypatch, first_pass):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    events = runtime_frozen_events()
    if first_pass is not None:
        events.append(
            {
                "kind": "runtime_probe_finished",
                "qualified": first_pass,
                "authority_sha256": "d" * 64,
            }
        )
    argv = [
        "python",
        str(ledger.OUT / "components/rr07_runtime_probe.py"),
        "--run",
        "--ordinal",
        "2",
    ]
    if first_pass:
        assert (
            ledger.validate_runtime_probe_request(
                events, "a" * 64, stage="SP3", used=21, argv=argv, timeout=75, calls=21
            )
            == "d" * 64
        )
    else:
        with pytest.raises(AssertionError):
            ledger.validate_runtime_probe_request(
                events, "a" * 64, stage="SP3", used=21, argv=argv, timeout=75, calls=21
            )


def test_sixth_warm_requires_quality_freeze_and_one_qualified_probe_pair(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    pair = {
        "kind": "runtime_probe_pair_qualified",
        "qualified": True,
        "authority_sha256": "d" * 64,
        "source_sha256": "a" * 64,
    }
    argv = [
        "python",
        str(ledger.ROOT / "scripts/sparse_program.py"),
        "--internal",
        "warm",
        "--round",
        "6",
        "--repetitions",
        "5",
    ]
    opts = dict(round_number=6, group="warm", stage="SP3", reserve_round=True, used=5, argv=argv)
    assert (
        ledger.validate_supervised_request([*runtime_frozen_events(), pair], "a" * 64, **opts)
        == "d" * 64
    )
    for events in (
        runtime_events(),
        runtime_frozen_events(),
        [*runtime_frozen_events(), {**pair, "qualified": False}],
        [*runtime_frozen_events(), pair, pair],
    ):
        with pytest.raises(AssertionError):
            ledger.validate_supervised_request(events, "a" * 64, **opts)


def test_runtime_host_windows_are_shared_and_capped_at_four(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger
    from sparse_program.host_load import COMPUTE

    assert {"onedrive.exe", "onedrive.sync.service.exe", "nutstoreclient.exe"} <= COMPUTE
    argv = [
        "python",
        str(ledger.ROOT / "scripts/sparse_program/host_load.py"),
        "--preflight",
        "--output",
        "new-folder",
    ]
    starts = [{"kind": "command_started", "runtime_host_authority_sha256": "d" * 64}] * 4
    assert (
        ledger.validate_runtime_host_request(
            [*runtime_events(), *starts[:3]], "a" * 64, stage="SP4", argv=argv
        )
        == "d" * 64
    )
    with pytest.raises(AssertionError):
        ledger.validate_runtime_host_request(
            [*runtime_events(), *starts], "a" * 64, stage="SP4", argv=argv
        )


def test_runtime_freeze_detects_changes_to_tested_files(monkeypatch, tmp_path):
    import json

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import evaluation, ledger

    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    tested, scope, review = tmp_path / "tested.py", tmp_path / "scope.json", tmp_path / "review.md"
    tested.write_text("original test")
    scope.write_text(json.dumps({"files": {"tested.py": ledger.sha(tested)}}))
    review.write_text("independent GO")
    identity = {"source_sha256": "a" * 64, "scripts": {}, "inputs": {}}
    frozen = {
        "scripts": {},
        "inputs": {},
        "environment": ledger.environment(),
        "components": {},
        "quality_scope": {"path": "scope.json", "sha256": ledger.sha(scope)},
        "engineering_review": {"path": "review.md", "sha256": ledger.sha(review)},
        "quality_finished_sha256": "e" * 64,
    }
    monkeypatch.setattr(
        evaluation,
        "quality_check",
        lambda: {"command_finished_sha256": "e" * 64, "evidence_refs": [frozen["quality_scope"]]},
    )
    monkeypatch.setattr(ledger, "runtime_freeze", lambda *args: frozen)
    assert ledger.check_runtime_freeze([], identity) is frozen
    monkeypatch.setattr(
        evaluation,
        "quality_check",
        lambda: {"command_finished_sha256": "f" * 64, "evidence_refs": [frozen["quality_scope"]]},
    )
    with pytest.raises(AssertionError):
        ledger.check_runtime_freeze([], identity)
    monkeypatch.setattr(
        evaluation,
        "quality_check",
        lambda: {"command_finished_sha256": "e" * 64, "evidence_refs": [frozen["quality_scope"]]},
    )
    tested.write_text("unverified change")
    with pytest.raises(AssertionError, match="Tested code or input changed"):
        ledger.check_runtime_freeze([], identity)


def test_runtime_ready_barrier_rejects_missing_parent_before_reading_ledger(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(ledger, "OUT", tmp_path / "outputs")
    monkeypatch.setattr(ledger, "history", lambda: pytest.fail("Read unready parent ledger"))
    with pytest.raises(RuntimeError, match="readiness barrier timed out"):
        ledger.await_runtime_parent_ready("outputs/runs/not-ready", timeout=0)


def test_recovery_enables_only_exact_fifth_warm_and_fourth_quality(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    assert ledger.round_limits([grant()])["quality"] == 3
    limits = ledger.round_limits([grant(), recovery_grant()])
    assert limits == {"capacity": 2, "netlib": 2, "warm": 5, "quality": 4, "diagnostic": 20}
    for events in (
        [recovery_grant()],
        [grant(), recovery_grant(), recovery_grant()],
        [grant(), {**recovery_grant(), "additional_warm_rounds": 2}],
        [grant(), {**recovery_grant(), "source_sha256": "d" * 64}],
    ):
        with pytest.raises(AssertionError):
            ledger.round_limits(events)


@pytest.mark.parametrize("bad", [None, "missing", "source", "used", "consumed", "sixth"])
def test_recovery_warm_gate_requires_exact_one_use_grant(monkeypatch, bad):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    events = [grant(), recovery_grant()]
    source, ordinal, used = "a" * 64, 5, 4
    if bad == "missing":
        events = [grant()]
    elif bad == "source":
        source = "d" * 64
    elif bad == "used":
        used = 3
    elif bad == "consumed":
        events.append({"kind": "command_started", "warm5_authority_sha256": "c" * 64})
    elif bad == "sixth":
        ordinal = 6
    options = dict(
        round_number=ordinal,
        group="warm",
        stage="SP3",
        reserve_round=True,
        used=used,
        argv=[
            "python",
            str(ledger.ROOT / "scripts/sparse_program.py"),
            "--internal",
            "warm",
            "--round",
            str(ordinal),
            "--repetitions",
            "5",
        ],
    )
    if bad:
        with pytest.raises(AssertionError):
            ledger.validate_supervised_request(events, source, **options)
    else:
        assert ledger.validate_supervised_request(events, source, **options) == "c" * 64


@pytest.mark.parametrize("bad", [None, "missing", "source", "used", "command", "consumed"])
def test_recovery_quality_gate_requires_one_complete_command(monkeypatch, bad):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    events = [grant(), recovery_grant()]
    source, used = "a" * 64, 3
    argv = ["python", str(ledger.ROOT / "scripts/check_quality.py")]
    if bad == "missing":
        events = [grant()]
    elif bad == "source":
        source = "d" * 64
    elif bad == "used":
        used = 4
    elif bad == "command":
        argv = ["python", "-m", "pytest"]
    elif bad == "consumed":
        events.append({"kind": "command_started", "quality4_authority_sha256": "c" * 64})
    if bad:
        with pytest.raises(AssertionError):
            ledger.validate_quality4_request(events, source, stage="SP4", used=used, argv=argv)
    else:
        assert (
            ledger.validate_quality4_request(events, source, stage="SP4", used=used, argv=argv)
            == "c" * 64
        )


def test_fifth_child_cannot_borrow_fourth_parent_or_repeat_its_claim(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program.host_load import validate_supervised_parent

    events = [grant(), recovery_grant()]
    parent = {
        "kind": "command_started",
        "run": "fifth-parent",
        "group": "warm",
        "stage": "SP3",
        "rounds": {"warm": 1},
        "warm_round": 5,
        "warm5_authority_sha256": "c" * 64,
    }
    assert (
        validate_supervised_parent([*events, parent], "fifth-parent", "a" * 64, warm_round=5)
        == parent
    )
    for invalid in (
        [*events, {**parent, "warm_round": 4}],
        [*events, parent, {"kind": "warm5_child_started", "run": "fifth-parent"}],
        [*events, parent, {"kind": "command_finished", "run": "fifth-parent"}],
    ):
        with pytest.raises(AssertionError):
            validate_supervised_parent(invalid, "fifth-parent", "a" * 64, warm_round=5)


def test_fourth_round_cap_requires_exact_unique_human_grant(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    assert ledger.round_limits([])["warm"] == 3
    assert ledger.round_limits([grant()])["warm"] == 4
    assert ledger.round_limits([grant()])["capacity"] == 2
    for events in ([grant(), grant()], [{**grant(), "fixed_children": 79}]):
        with pytest.raises(AssertionError):
            ledger.round_limits(events)


@pytest.mark.parametrize("bad", ["missing", "source", "group", "used", "consumed", "scope"])
def test_fourth_round_is_rejected_before_spawn_without_its_exact_authority(monkeypatch, bad):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import ledger

    events = [grant()]
    options = {
        "group": "warm",
        "stage": "SP3",
        "reserve_round": True,
        "used": 3,
        "argv": [
            "python",
            str(ledger.ROOT / "scripts/sparse_program.py"),
            "--internal",
            "warm",
            "--round",
            "4",
            "--repetitions",
            "5",
        ],
    }
    source = "a" * 64
    if bad == "missing":
        events = []
    elif bad == "source":
        source = "c" * 64
    elif bad == "group":
        options["group"] = "component"
    elif bad == "used":
        options["used"] = 4
    elif bad == "scope":
        events[0]["repetitions"] = 4
    else:
        events.append({"kind": "command_started", "warm4_authority_sha256": "b" * 64})
    with pytest.raises(AssertionError):
        ledger.validate_warm4_request(events, source, **options)


def test_fourth_child_claim_requires_live_warm_parent_and_can_be_used_only_once(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program.host_load import validate_warm4_parent

    parent = {
        "kind": "command_started",
        "run": "parent",
        "group": "warm",
        "stage": "SP3",
        "rounds": {"warm": 1},
        "warm_round": 4,
        "warm4_authority_sha256": "b" * 64,
    }
    assert validate_warm4_parent([grant(), parent], "parent", "a" * 64) == parent
    for events in (
        [grant(), {**parent, "group": "diagnostic"}],
        [grant(), parent, {"kind": "warm4_child_started", "run": "parent"}],
        [grant(), parent, {"kind": "command_finished", "run": "parent"}],
    ):
        with pytest.raises(AssertionError):
            validate_warm4_parent(events, "parent", "a" * 64)


def test_observed_run_rejects_identity_drift_or_incomplete_sampling_without_redefining_gate(
    monkeypatch,
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program.host_load import supervision_decision

    identity = {"source": {"s": "hash"}, "scripts": {"d": "hash"}, "inputs": {"i": "hash"}}
    row = {"host_total_fraction": 0.1, "other_compute": [], "unreadable_compute": []}
    samples, env = [row] * 10, {"threads": 1}
    assert supervision_decision(identity, identity, env, env, samples, [], 0)["accepted"]
    for key in ("source", "scripts", "inputs"):
        changed = {**identity, key: {"different": "hash"}}
        assert not supervision_decision(identity, changed, env, env, samples, [], 0)["accepted"]
    assert not supervision_decision(identity, identity, env, {}, samples, [], 0)["accepted"]
    assert not supervision_decision(identity, identity, env, env, samples, ["gap"], 0)["accepted"]
    unreadable = [{**row, "unreadable_compute": [42]}] * 10
    assert not supervision_decision(identity, identity, env, env, unreadable, [], 0)["accepted"]
    busy = [{**row, "host_total_fraction": 0.9}] * 10
    decision = supervision_decision(identity, identity, env, env, busy, [], 0)
    assert not decision["formal_host_load"]["quiet"] and decision["accepted"]
    assert not supervision_decision(identity, identity, env, env, samples, [], 1)["accepted"]


def test_windows_host_observer_survives_actual_resource_guard_rebinding(monkeypatch):
    import ctypes
    import os
    import queue
    import threading
    import time
    from types import SimpleNamespace

    if os.name != "nt":
        pytest.skip("Actual Windows ctypes signature regression")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program.host_load import Sampler
    from sparse_program.resources import windows_tree_peaks

    ready, proceed = queue.Queue(), queue.Queue()
    samples, errors = [], []

    def observe():
        try:
            sampler = Sampler()
            assert sampler.sample() is None
            ready.put("ready")
            for _ in range(5):
                proceed.get(timeout=5)
                time.sleep(0.025)
                samples.append(sampler.sample())
                ready.put("sampled")
        except BaseException as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            ready.put("error")

    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    current = SimpleNamespace(
        pid=os.getpid(), _handle=kernel.GetCurrentProcess(), poll=lambda: None
    )
    observer = threading.Thread(target=observe, daemon=True)
    observer.start()
    assert ready.get(timeout=5) == "ready", errors
    for _ in range(5):
        # This is the exact production resource monitor that overwrites the
        # shared ctypes function argtypes; no solver or dummy child is needed.
        assert windows_tree_peaks(current, {}) > 0
        proceed.put("sample")
        result = ready.get(timeout=5)
        if result == "error":
            break
        assert result == "sampled"
    observer.join(timeout=5)
    assert not observer.is_alive(), "Observer thread did not finish"
    assert not errors, errors
    assert len(samples) == 5 and all(row is not None for row in samples)
    assert all("host_total_fraction" in row and "other_compute" in row for row in samples)
