"""RR08 authorization and actual receipt validation; no solver calls."""

import copy
import json
from pathlib import Path

import pytest


def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from sparse_program import evaluation, ledger

    return evaluation, ledger


def grant(ledger):
    return {
        "kind": "human_original_goal_closure",
        "sha256": "d" * 64,
        "active_revision": "RR08",
        "source_thread": "01a1254a-b349-77d0-8c66-d4b711cd511f",
        "source_user_message": "01a172de-5ccd-74e1-b085-089b9b7d2ee9",
        "revision_contract": ledger.RR08_CONTRACT,
        "revision_contract_sha256": ledger.RR08_CONTRACT_SHA,
        "source_sha256": ledger.RR08_SOURCE_SHA,
        "accepted_evidence": ledger.RR08_WARM_REF.copy(),
        "previous_quality_ceiling": 5,
        "new_quality_ceiling": 7,
        "additional_quality_rounds": 2,
        "quality_batch_seconds": 180,
        "evidence_batches": 2,
        "evidence_batch_seconds": 180,
        "independent_review_seconds": 180,
        "maximum_added_validation_seconds": 900,
        "warm6_closed": True,
        "host_permissions_closed": True,
        "new_formal_solver_runs": 0,
        "new_installations": 0,
        "original_eight_criteria_unchanged": True,
        "goal_thread": "01a15208-bea9-7030-aacc-95d785e8fa58",
        "human_instruction": "direct approval",
        "baseline_seconds": dict.fromkeys(ledger.STAGE_SECONDS, 0),
        "baseline_total_seconds": 0,
    }


def selection_fixture(e, ledger):
    refs = {k: {"path": p, "sha256": "a" * 64} for k, p in e.RR08_DISCLOSURES.items()}
    selection = {
        "schema_version": 1,
        "program": ledger.PROGRAM,
        "active_revision": "RR08",
        "authority_sha256": "d" * 64,
        "source_sha256": ledger.RR08_SOURCE_SHA,
        "accepted_evidence": ledger.RR08_WARM_REF.copy(),
        "disclosures": refs,
        "claim_scope": "fixed_warm4_run_only",
        "auxiliary_status": "HOLD",
    }
    events = [
        grant(ledger),
        {
            "kind": "rr08_c0_disclosures_pinned",
            "authority_sha256": "d" * 64,
            "references": copy.deepcopy(refs),
        },
    ]
    return selection, events


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "path",
        "hash",
        "source",
        "missing_failure",
        "aux_go",
        "general_claim",
        "missing_authority",
        "duplicate_authority",
        "forged_user",
        "duplicate_pin",
    ],
)
def test_rr08_selection_accepts_only_the_explicit_approved_candidate(monkeypatch, bad):
    e, ledger = modules(monkeypatch)
    packet, events = selection_fixture(e, ledger)
    if bad == "path":
        packet["accepted_evidence"]["path"] = e.RR08_DISCLOSURES["warm5"]
    elif bad == "hash":
        packet["accepted_evidence"]["sha256"] = "b" * 64
    elif bad == "source":
        packet["source_sha256"] = "b" * 64
    elif bad == "missing_failure":
        del packet["disclosures"]["warm3"]
    elif bad == "aux_go":
        packet["auxiliary_status"] = "GO"
    elif bad == "general_claim":
        packet["claim_scope"] = "stable_across_runs"
    elif bad == "missing_authority":
        events = events[1:]
    elif bad == "duplicate_authority":
        events.append(grant(ledger))
    elif bad == "forged_user":
        events[0]["source_user_message"] = "unverified user"
    elif bad == "duplicate_pin":
        events.append(events[-1].copy())
    if bad:
        with pytest.raises((AssertionError, e.EvidenceError)):
            e.validate_rr08_selection(packet, events, ledger.RR08_SOURCE_SHA)
    else:
        assert (
            e.validate_rr08_selection(packet, events, ledger.RR08_SOURCE_SHA)["sha256"] == "d" * 64
        )


@pytest.mark.parametrize("first_exit", [None, 0, 1])
def test_quality7_requires_a_real_failed_quality6(monkeypatch, first_exit):
    _, ledger = modules(monkeypatch)
    events = [grant(ledger)]
    argv = ["python", str(ledger.ROOT / "scripts/check_quality.py")]
    assert (
        ledger.validate_extended_quality_request(
            events, ledger.RR08_SOURCE_SHA, stage="SP4", used=5, argv=argv, ordinal=6
        )
        == "d" * 64
    )
    events.append({"kind": "command_started", "run": "q6", "quality6_authority_sha256": "d" * 64})
    with pytest.raises(AssertionError):
        ledger.validate_extended_quality_request(
            events, ledger.RR08_SOURCE_SHA, stage="SP4", used=5, argv=argv, ordinal=6
        )
    if first_exit is not None:
        events.append({"kind": "command_finished", "run": "q6", "exit_code": first_exit})
    if first_exit == 1:
        assert (
            ledger.validate_extended_quality_request(
                events, ledger.RR08_SOURCE_SHA, stage="SP4", used=6, argv=argv, ordinal=7
            )
            == "d" * 64
        )
    else:
        with pytest.raises(AssertionError):
            ledger.validate_extended_quality_request(
                events, ledger.RR08_SOURCE_SHA, stage="SP4", used=6, argv=argv, ordinal=7
            )


@pytest.mark.parametrize("bad", [None, "missing", "duplicate", "round", "output", "gap"])
def test_original_rr04_observer_schema_uses_its_real_parent(monkeypatch, tmp_path, bad):
    e, ledger = modules(monkeypatch)
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    observer = {
        "parent_run": "runs/actual",
        "sample_count": 0,
        "errors": ["ctypes failure"],
        "decision": {"accepted": False},
    }
    parent = {
        "kind": "command_started",
        "run": "runs/actual",
        "group": "warm",
        "stage": "SP3",
        "warm_round": 4,
        "rounds": {"warm": 1},
        "argv": ["python", "program.py", "--round", "4", "--host-output", "outputs/host"],
    }
    events = [parent]
    if bad == "missing":
        events = []
    elif bad == "duplicate":
        events.append(parent.copy())
    elif bad == "round":
        parent["warm_round"] = 5
    elif bad == "output":
        parent["argv"][-1] = "outputs/other"
    elif bad == "gap":
        observer["decision"]["accepted"] = True
    if bad:
        with pytest.raises(e.EvidenceError):
            e.validate_rr08_observer(observer, events, "outputs/host/supervision.json")
    else:
        e.validate_rr08_observer(observer, events, "outputs/host/supervision.json")


@pytest.mark.parametrize("group", ["warm", "runtime-host", "diagnostic", "install-checks"])
def test_rr08_refuses_closed_execution_before_spawning(monkeypatch, group):
    _, ledger = modules(monkeypatch)
    monkeypatch.delenv("SILO_SPARSE_ACCOUNT_PARENT", raising=False)
    monkeypatch.setattr(ledger, "history", lambda: [grant(ledger)])
    monkeypatch.setattr(ledger, "identity", lambda: {"source_sha256": ledger.RR08_SOURCE_SHA})
    monkeypatch.setattr(
        ledger,
        "totals",
        lambda: {
            "seconds": dict.fromkeys(ledger.STAGE_SECONDS, 0),
            "total_seconds": 0,
            "rounds": {"quality": 5, "warm": 5, "diagnostic": 22},
        },
    )
    monkeypatch.setattr(
        ledger.subprocess, "Popen", lambda *a, **k: pytest.fail("Spawned closed work")
    )
    with pytest.raises(AssertionError, match="RR08 closes"):
        ledger.command(["python", "unused"], stage="SP4", group=group, timeout=60)


def warm_fixture(monkeypatch, tmp_path, cold_segment=2):
    e, ledger = modules(monkeypatch)
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(ledger, "OUT", tmp_path / "outputs")
    folder = ledger.OUT / "warm/round1_fixture"
    folder.mkdir(parents=True)
    (tmp_path / "tests/fixtures").mkdir(parents=True)
    code = tmp_path / "source.py"
    code.write_text("# fixture source")
    drivers = {}
    for name in ("cases", "oracles", "runner", "checker", "resources", "warm"):
        path = tmp_path / (name + ".py")
        path.write_text("# fixture driver")
        drivers["scripts/sparse_program/" + name + ".py"] = path

    def current_identity():
        source = {"src/silo/solver.py": ledger.sha(code)}
        return {
            "source": source,
            "source_sha256": ledger.digest(source),
            "inputs": {},
            "scripts": {k: ledger.sha(p) for k, p in drivers.items()},
        }

    monkeypatch.setattr(ledger, "identity", current_identity)
    payload = {
        "variables": [{"name": "x", "lower": 0, "upper": 1}],
        "constraints": [],
        "objective": {"coefficients": {}},
    }
    model = tmp_path / "model.json"
    model.write_text(json.dumps(payload))
    point = {
        "status": "optimal",
        "objective_value": 0,
        "primal_values": {"x": 0},
        "side_multipliers": {
            "row_lower": {},
            "row_upper": {},
            "variable_lower": {"x": 0},
            "variable_upper": {"x": 0},
        },
        "diagnostics": {"lp_engine": "sparse", "cross_solve_reuses": 1},
    }
    chains = [
        {
            "id": f"T{i}",
            "initial_path": "model.json",
            "initial_sha256": ledger.sha(model),
            "options": {},
            "states": [
                {
                    "id": f"T{i}-{j}",
                    "payload_path": "model.json",
                    "payload_sha256": ledger.sha(model),
                }
                for j in range(20)
            ],
        }
        for i in range(8)
    ]
    monkeypatch.setattr(e, "manifest", lambda: {"trajectories": chains})
    monkeypatch.setattr(e, "oracle", lambda *args: {"status": "optimal", "objective": 0})
    references = {
        "trajectories": {
            c["id"]: {"initial": {"truth": {"status": "optimal", "objective": 0}}} for c in chains
        }
    }
    (tmp_path / "tests/fixtures/sparse_program_oracles.json").write_text(json.dumps(references))
    records = []
    for index, chain in enumerate(chains):
        for rep in range(5):
            for mode in ("cold", "warm") if (index + rep) % 2 == 0 else ("warm", "cold"):
                stem = f"{chain['id']}_{rep}_{mode}"
                request, response = folder / (stem + ".request.json"), folder / (stem + ".json")
                request.write_text(json.dumps({"chain": chain, "mode": mode, "repetition": rep}))
                segment = cold_segment if mode == "cold" else 1
                packet = {
                    "id": chain["id"],
                    "mode": mode,
                    "repetition": rep,
                    "native_roots_started": 21,
                    "native_roots_completed": 21,
                    "initial": {"result": point},
                    "states": [
                        {
                            "id": s["id"],
                            "payload_sha256": s["payload_sha256"],
                            "result": point,
                            "seconds": 0.01,
                        }
                        for s in chain["states"]
                    ],
                    "segment_seconds": segment,
                    "total_seconds_including_import_initial": segment + 1,
                }
                response.write_text(json.dumps(packet))
                records.append(
                    {
                        "id": chain["id"],
                        "mode": mode,
                        "repetition": rep,
                        "pass": True,
                        "result_path": str(response.relative_to(tmp_path)),
                        "result_sha256": ledger.sha(response),
                        "request_sha256": ledger.sha(request),
                        "monitor": {
                            "exit_code": 0,
                            "guard_reason": None,
                            "elapsed_seconds": 3,
                            "peak_rss_bytes": 1024,
                            "process_scope": "root_and_descendants",
                        },
                    }
                )
    summary = {
        "source": current_identity(),
        "records": records,
        "all_correct": True,
        "trajectory_ratios": {c["id"]: cold_segment for c in chains},
        "bound_files": {str(p.relative_to(tmp_path)): ledger.sha(p) for p in folder.iterdir()},
    }
    path = folder / "summary.json"
    path.write_text(json.dumps(summary))
    return e, path, summary, code, drivers


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "missing",
        "order",
        "failed",
        "wall",
        "rss",
        "ratio",
        "source",
        "driver",
        "speed",
        "tamper",
    ],
)
def test_warm_original_validation_body_remains_strict(monkeypatch, tmp_path, bad):
    e, path, packet, code, drivers = warm_fixture(
        monkeypatch, tmp_path, cold_segment=0.5 if bad == "speed" else 2
    )
    if bad == "missing":
        packet["records"].pop()
    elif bad == "order":
        packet["records"][:2] = packet["records"][1::-1]
    elif bad == "failed":
        packet["records"][0]["pass"] = False
    elif bad == "wall":
        packet["records"][0]["monitor"]["elapsed_seconds"] = 60.001
    elif bad == "rss":
        packet["records"][0]["monitor"]["peak_rss_bytes"] = (1 << 30) + 1
    elif bad == "ratio":
        packet["trajectory_ratios"]["T0"] = 99
    elif bad == "source":
        code.write_text("# changed algorithm")
    elif bad == "driver":
        next(iter(drivers.values())).write_text("# changed driver")
    elif bad == "tamper":
        (tmp_path / packet["records"][0]["result_path"]).write_text("{}")
    path.write_text(json.dumps(packet))
    if bad:
        with pytest.raises((e.EvidenceError, AssertionError)):
            e.warm_check()
    else:
        result = e.warm_check()
        assert result["median_ratio"] == 2 and result["state_solves"] == 1600
        assert "accepted_evidence" not in result
