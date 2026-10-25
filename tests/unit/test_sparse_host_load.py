"""Pure preflight decisions; no OS sampling or solver execution."""

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
