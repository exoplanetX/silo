"""Append-only accounting; production solvers and old evidence are never imported."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/sparse_lp_program_20261024"
PROGRAM = "SILO-SPARSE-LP-20261024"
CONTRACT = "20261024-02-01_sparse-lp-program"
STAGE_SECONDS = {"SP1": 1800, "SP2": 3600, "SP3": 10800, "SP4": 10800, "reserve": 1800}
TOTAL_SECONDS = 28800
GROUP_ROUNDS = {"capacity": 2, "netlib": 2, "warm": 3, "quality": 3, "diagnostic": 20}


def warm4_grant(events):
    grants = [event for event in events if event["kind"] == "human_warm4_recheck"]
    if not grants:
        return None
    assert len(grants) == 1, "Warm4 requires one unique direct human grant"
    grant = grants[0]
    expected = {
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
    assert all(grant.get(key) == value for key, value in expected.items()), "Warm4 scope differs"
    assert grant.get("question_call"), "Warm4 lacks the direct human reply identity"
    source = grant.get("source_sha256", "")
    assert len(source) == 64 and set(source) <= set("0123456789abcdef"), "Warm4 source missing"
    return grant


def supervision_recovery_grant(events):
    grants = [event for event in events if event["kind"] == "human_supervision_recovery"]
    if not grants:
        return None
    assert len(grants) == 1, "Supervision recovery requires one unique direct human grant"
    grant = grants[0]
    expected = {
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
    assert all(grant.get(k) == v for k, v in expected.items()), "Recovery scope differs"
    previous = warm4_grant(events)
    assert previous is not None, "Recovery lacks its prior warm authority"
    assert grant.get("question_call"), "Recovery lacks the direct human reply identity"
    assert grant.get("source_sha256") == previous["source_sha256"], "Recovery source differs"
    return grant


def runtime_stability_grant(events):
    grants = [e for e in events if e["kind"] == "human_runtime_stability_recovery"]
    if not grants:
        return None
    assert len(grants) == 1, "Runtime recovery requires one unique direct human grant"
    grant = grants[0]
    previous = supervision_recovery_grant(events)
    expected = {
        "previous_warm_ceiling": 5,
        "new_warm_ceiling": 6,
        "additional_warm_rounds": 1,
        "previous_quality_ceiling": 4,
        "new_quality_ceiling": 5,
        "additional_quality_rounds": 1,
        "previous_diagnostic_ceiling": 20,
        "new_diagnostic_ceiling": 22,
        "additional_diagnostic_batches": 2,
        "diagnostic_batch_seconds": 75,
        "diagnostic_child_seconds": 60,
        "diagnostic_public_calls": 21,
        "diagnostic_maximum_child_wall_seconds": 45,
        "frequency_relative_difference": 0.1,
        "maximum_host_windows": 4,
        "inherited_host_windows": 1,
        "additional_host_windows": 3,
        "host_sample_seconds": 20,
        "fixed_children": 80,
        "modified_states": 1600,
        "initial_states": 80,
        "repetitions": 5,
        "child_seconds": 60,
        "child_memory_bytes": 1 << 30,
        "pause_onedrive_authorized": True,
        "exit_client_if_needed_authorized": True,
        "restore_original_sync_state_required": True,
    }
    assert all(grant.get(k) == v for k, v in expected.items()), "Runtime scope differs"
    assert previous is not None and grant.get("question_call"), "Runtime authority incomplete"
    assert grant.get("source_sha256") == previous["source_sha256"], "Runtime source differs"
    assert grant.get("predecessor_host_authority_sha256") == previous["sha256"]
    return grant


def runtime_freeze(events, source_sha256):
    grant = runtime_stability_grant(events)
    assert grant is not None, "Runtime recovery has no direct human authority"
    assert grant["source_sha256"] == source_sha256, "Runtime source differs"
    freezes = [e for e in events if e["kind"] == "runtime_tools_frozen"]
    assert len(freezes) == 1, "Runtime tools require one post-quality freeze"
    frozen = freezes[0]
    assert frozen.get("authority_sha256") == grant["sha256"]
    assert frozen.get("source_sha256") == source_sha256
    quality = next(e for e in events if e.get("sha256") == frozen["quality_finished_sha256"])
    assert quality["kind"] == "command_finished" and quality.get("exit_code") == 0
    assert quality.get("stage") == "SP4" and quality.get("group") == "quality"
    start = next(
        e for e in events if e["kind"] == "command_started" and e.get("run") == quality["run"]
    )
    assert start.get("quality5_authority_sha256") == grant["sha256"]
    return frozen


def check_runtime_freeze(events, ident):
    from .evaluation import quality_check

    frozen = runtime_freeze(events, ident["source_sha256"])
    assert frozen["scripts"] == ident["scripts"] and frozen["inputs"] == ident["inputs"]
    assert frozen["environment"] == environment(), "Runtime environment changed"
    checked = quality_check()
    assert checked["command_finished_sha256"] == frozen["quality_finished_sha256"]
    assert checked["evidence_refs"][0] == frozen["quality_scope"], "Quality scope differs"
    scope = frozen["quality_scope"]
    assert sha(ROOT / scope["path"]) == scope["sha256"], "Quality scope pin changed"
    for name, checksum in json.loads((ROOT / scope["path"]).read_text())["files"].items():
        assert sha(ROOT / name) == checksum, "Tested code or input changed"
    for name, checksum in frozen["components"].items():
        assert sha(ROOT / name) == checksum, "Runtime component changed"
    review = frozen["engineering_review"]
    assert sha(ROOT / review["path"]) == review["sha256"], "Engineering review changed"
    return frozen


def await_runtime_parent_ready(parent_run, timeout=5):
    """Read the ledger only after the parent has finished its last startup append."""
    assert parent_run, "Runtime child requires an accounting parent"
    folder = (ROOT / parent_run).resolve()
    assert folder.is_relative_to((OUT / "runs").resolve()), "Invalid runtime parent folder"
    ready = folder / "runtime_parent_ready.json"
    deadline = time.perf_counter() + timeout
    while not ready.exists():
        if time.perf_counter() >= deadline:
            raise RuntimeError("Runtime parent readiness barrier timed out")
        time.sleep(0.01)
    receipt = json.loads(ready.read_text())
    events = history()
    started = next(e for e in events if e["sha256"] == receipt["command_started_sha256"])
    process = next(e for e in events if e["sha256"] == receipt["process_started_sha256"])
    assert started["kind"] == "command_started" and process["kind"] == "process_started"
    assert started["run"] == process["run"] == parent_run
    assert not any(e["kind"] == "command_finished" and e.get("run") == parent_run for e in events)
    return started


def validate_runtime_probe_request(events, source_sha256, *, stage, used, argv, timeout, calls):
    grant = runtime_stability_grant(events)
    assert grant is not None and source_sha256 == grant["source_sha256"]
    assert stage == "SP3" and used in (20, 21), "Only the two fixed probes are authorized"
    assert timeout == 75 and calls == 21, "Probe guard or calls differ"
    assert Path(argv[1]).resolve() == (OUT / "components/rr07_runtime_probe.py").resolve()
    assert argv[2] == "--run" and argv[argv.index("--ordinal") + 1] == str(used - 19)
    runtime_freeze(events, source_sha256)
    prior = [e for e in events if e["kind"] == "runtime_probe_finished"]
    assert len(prior) == used - 20 and all(e.get("qualified") for e in prior), (
        "A failed or unfinished first probe stops the package"
    )
    assert all(e.get("authority_sha256") == grant["sha256"] for e in prior)
    return grant["sha256"]


def validate_runtime_host_request(events, source_sha256, *, stage, argv):
    grant = runtime_stability_grant(events)
    assert grant is not None and grant["source_sha256"] == source_sha256
    assert stage == "SP4" and len(argv) == 5 and argv[2] == "--preflight"
    assert Path(argv[1]).resolve() == (ROOT / "scripts/sparse_program/host_load.py").resolve()
    assert argv[3] == "--output"
    starts = [
        e
        for e in events
        if e["kind"] == "command_started"
        and e.get("runtime_host_authority_sha256") == grant["sha256"]
    ]
    assert len(starts) < 4, "Runtime recovery host windows exhausted"
    return grant["sha256"]


def round_limits(events):
    limits = GROUP_ROUNDS.copy()
    if warm4_grant(events) is not None:
        limits["warm"] = 4
    if supervision_recovery_grant(events) is not None:
        limits.update(warm=5, quality=4)
    if runtime_stability_grant(events) is not None:
        limits.update(warm=6, quality=5, diagnostic=22)
    return limits


def validate_warm4_request(events, source_sha256, *, group, stage, reserve_round, used, argv):
    return validate_supervised_request(
        events,
        source_sha256,
        round_number=4,
        group=group,
        stage=stage,
        reserve_round=reserve_round,
        used=used,
        argv=argv,
    )


def validate_supervised_request(
    events, source_sha256, *, round_number, group, stage, reserve_round, used, argv
):
    assert round_number in (4, 5, 6), "Unsupported supervised warm round"
    grant = {4: warm4_grant, 5: supervision_recovery_grant, 6: runtime_stability_grant}[
        round_number
    ](events)
    assert grant is not None, "Supervised warm has no direct human authority"
    assert group == "warm" and stage == "SP3" and reserve_round, "Wrong warm accounting group"
    assert used == round_number - 1, "Supervised warm must reserve its exact next round"
    assert grant["source_sha256"] == source_sha256, "Warm source differs from human grant"
    authority_field = f"warm{round_number}_authority_sha256"
    assert not any(
        event["kind"] == "command_started" and event.get(authority_field) == grant["sha256"]
        for event in events
    ), "Supervised warm authority already consumed"
    assert (
        len(argv) >= 8 and Path(argv[1]).resolve() == (ROOT / "scripts/sparse_program.py").resolve()
    )
    assert list(argv[2:4]) == ["--internal", "warm"], "Warm requires the public CLI parent"
    assert argv[argv.index("--round") + 1] == str(round_number)
    assert argv[argv.index("--repetitions") + 1] == "5"
    if round_number == 6:
        runtime_freeze(events, source_sha256)
        qualified = [e for e in events if e["kind"] == "runtime_probe_pair_qualified"]
        assert len(qualified) == 1 and qualified[0].get("qualified") is True
        assert qualified[0].get("authority_sha256") == grant["sha256"]
        assert qualified[0].get("source_sha256") == source_sha256
    return grant["sha256"]


def validate_quality4_request(events, source_sha256, *, stage, used, argv):
    return validate_extended_quality_request(
        events, source_sha256, stage=stage, used=used, argv=argv, ordinal=4
    )


def validate_extended_quality_request(events, source_sha256, *, stage, used, argv, ordinal):
    assert ordinal in (4, 5)
    grant = (supervision_recovery_grant if ordinal == 4 else runtime_stability_grant)(events)
    assert grant is not None, "Extended quality lacks direct human authority"
    assert stage == "SP4" and used == ordinal - 1, "Quality requires its exact stage and ordinal"
    assert source_sha256 == grant["source_sha256"], "Quality source differs"
    assert (
        len(argv) == 2 and Path(argv[1]).resolve() == (ROOT / "scripts/check_quality.py").resolve()
    ), "Extended quality must run the complete quality entry"
    assert not any(
        event["kind"] == "command_started"
        and event.get(f"quality{ordinal}_authority_sha256") == grant["sha256"]
        for event in events
    ), "Extended quality authority already consumed"
    return grant["sha256"]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def identity():
    files = [*sorted((ROOT / "src/silo").rglob("*.py")), ROOT / "pyproject.toml"]
    source = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    scripts = [ROOT / "scripts/sparse_program.py", *sorted(Path(__file__).parent.rglob("*.py"))]
    manifests = sorted((ROOT / "tests/fixtures").glob("sparse_program_*.json"))
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source": source,
        "source_sha256": digest(source),
        "scripts": {p.relative_to(ROOT).as_posix(): sha(p) for p in scripts if p.exists()},
        "inputs": {p.name: sha(p) for p in manifests},
    }


def environment():
    versions = {}
    for name in ("numpy", "scipy"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "packages": versions,
        "threads": {
            n: os.environ.get(n)
            for n in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }


def history():
    path = OUT / "ledger.jsonl"
    events, previous = [], None
    for line in path.read_text(encoding="utf-8").splitlines() if path.exists() else ():
        event = json.loads(line)
        checksum = event.pop("sha256")
        assert event["previous_sha256"] == previous, "Broken ledger chain"
        if digest(event) != checksum:
            # SP1's first pin receipt accidentally used the reserved sha256
            # detail name. Retain its original bytes and verify its exact hash
            # preimage, whose shadowed value is the preserved pin-file hash.
            pin = OUT / "preserved_old_evidence.json"
            assert event["kind"] == "old_evidence_pinned" and len(events) == 1
            assert digest({**event, "sha256": sha(pin)}) == checksum, "Ledger event changed"
        previous = checksum
        events.append({**event, "sha256": checksum})
    return events


def totals():
    seconds = dict.fromkeys(STAGE_SECONDS, 0.0)
    rounds = dict.fromkeys(GROUP_ROUNDS, 0)
    events = history()
    by_hash = {e["sha256"]: e for e in events}
    covered = set()
    for event in events:
        if event["kind"] == "nested_timer_coverage":
            child = by_hash[event["child_finished_sha256"]]
            parent = by_hash[event["parent_finished_sha256"]]
            assert child["kind"] == parent["kind"] == "command_finished"
            assert child["stage"] == parent["stage"]
            assert child["elapsed_seconds"] <= parent["elapsed_seconds"]
            starts = {e.get("run"): e for e in events if e["kind"] == "command_started"}
            assert starts[parent["run"]]["utc"] <= starts[child["run"]]["utc"]
            assert child["utc"] <= parent["utc"]
            assert child["sha256"] not in covered
            covered.add(child["sha256"])
    for event in events:
        if event["sha256"] not in covered:
            for stage, value in event.get("seconds", {}).items():
                seconds[stage] += value
        for group, value in event.get("rounds", {}).items():
            rounds[group] += value
    assert all(seconds[k] <= v for k, v in STAGE_SECONDS.items()), seconds
    assert sum(seconds.values()) <= TOTAL_SECONDS, seconds
    assert all(rounds[k] <= v for k, v in round_limits(events).items()), rounds
    return {"seconds": seconds, "total_seconds": sum(seconds.values()), "rounds": rounds}


def append(kind, *, seconds=None, rounds=None, **details):
    reserved = {
        "program",
        "contract",
        "kind",
        "utc",
        "previous_sha256",
        "seconds",
        "rounds",
        "sha256",
    }
    assert not reserved.intersection(details), "Reserved ledger field in details"
    OUT.mkdir(parents=True, exist_ok=True)
    used = totals()
    seconds, rounds = seconds or {}, rounds or {}
    assert all(0 <= v <= STAGE_SECONDS[k] - used["seconds"][k] for k, v in seconds.items())
    assert sum(seconds.values()) <= TOTAL_SECONDS - used["total_seconds"]
    events = history()
    limits = round_limits(events)
    assert all(0 <= v <= limits[k] - used["rounds"][k] for k, v in rounds.items())
    event = {
        "program": PROGRAM,
        "contract": CONTRACT,
        "kind": kind,
        "utc": utc(),
        "previous_sha256": events[-1]["sha256"] if events else None,
        "seconds": seconds,
        "rounds": rounds,
        **details,
    }
    event["sha256"] = digest(event)
    with (OUT / "ledger.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, allow_nan=False) + "\n")
    return event


def command(
    argv, *, stage, group, timeout=None, reserve_round=False, calls=None, cwd=ROOT, warm_round=None
):
    """Run one top-level check, charge it once, retain failures and process identity.

    Caller-supplied call counts are declared reservations, not claims of completed
    calls. Child case records provide actual started/completed counts. This wrapper
    cannot double-charge the child's timers. Long groups must give a bounded timeout.
    """
    assert not os.environ.get("SILO_SPARSE_ACCOUNT_PARENT"), (
        "Do not nest accounting parents; invoke budgeted CLI directly."
    )
    used = totals()
    ident = identity()
    warm_authority, quality_authority = None, None
    probe_authority, host_authority, quality_ordinal = None, None, None
    if warm_round in (4, 5, 6) or (
        group == "warm" and reserve_round and used["rounds"]["warm"] >= 3
    ):
        assert warm_round in (4, 5, 6), "Only a specifically authorized supervised round may follow"
        warm_authority = validate_supervised_request(
            history(),
            ident["source_sha256"],
            round_number=warm_round,
            group=group,
            stage=stage,
            reserve_round=reserve_round,
            used=used["rounds"]["warm"],
            argv=argv,
        )
    if group == "quality" and reserve_round and used["rounds"]["quality"] >= 3:
        quality_ordinal = used["rounds"]["quality"] + 1
        quality_authority = validate_extended_quality_request(
            history(),
            ident["source_sha256"],
            stage=stage,
            used=used["rounds"]["quality"],
            argv=argv,
            ordinal=quality_ordinal,
        )
    if group == "diagnostic" and reserve_round and used["rounds"]["diagnostic"] >= 20:
        probe_authority = validate_runtime_probe_request(
            history(),
            ident["source_sha256"],
            stage=stage,
            used=used["rounds"]["diagnostic"],
            argv=argv,
            timeout=timeout,
            calls=calls,
        )
        check_runtime_freeze(history(), ident)
    if group == "runtime-host":
        host_authority = validate_runtime_host_request(
            history(), ident["source_sha256"], stage=stage, argv=argv
        )
    if warm_round == 6:
        check_runtime_freeze(history(), ident)
        pair = next(e for e in history() if e["kind"] == "runtime_probe_pair_qualified")
        assert sha(ROOT / pair["path"]) == pair["file_sha256"], "Probe qualification changed"
        assert json.loads((ROOT / pair["path"]).read_text())["qualified"] is True
    remaining = min(
        STAGE_SECONDS[stage] - used["seconds"][stage], TOTAL_SECONDS - used["total_seconds"]
    )
    limit = remaining - 1 if timeout is None else min(timeout, remaining - 1)
    assert limit > 0, "No verification budget remains"
    if timeout is not None:
        assert timeout <= remaining - 1, "Insufficient budget for the entire planned batch"
    folder = OUT / "runs" / (utc().replace(":", "-") + "_" + str(uuid4()))
    folder.mkdir(parents=True)
    (folder / "identity.json").write_text(json.dumps(ident, indent=2), encoding="utf-8")
    started_receipt = append(
        "command_started",
        rounds={group: 1} if reserve_round else {},
        stage=stage,
        group=group,
        argv=argv,
        run=str(folder.relative_to(ROOT)),
        identity_sha256=digest(ident),
        declared_calls=calls,
        timeout=limit,
        started_at=utc(),
        warm_round=warm_round,
        warm4_authority_sha256=warm_authority if warm_round == 4 else None,
        warm5_authority_sha256=warm_authority if warm_round == 5 else None,
        warm6_authority_sha256=warm_authority if warm_round == 6 else None,
        quality4_authority_sha256=quality_authority if quality_ordinal == 4 else None,
        quality5_authority_sha256=quality_authority if quality_ordinal == 5 else None,
        runtime_probe_authority_sha256=probe_authority,
        runtime_host_authority_sha256=host_authority,
    )
    start = time.perf_counter()
    log = folder / "console.log"
    with log.open("w", encoding="utf-8") as stream:
        try:
            child_env = {**os.environ, "SILO_SPARSE_ACCOUNT_PARENT": str(folder.relative_to(ROOT))}
            process = subprocess.Popen(
                argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, env=child_env
            )
            process_receipt = append(
                "process_started",
                stage=stage,
                group=group,
                pid=process.pid,
                run=str(folder.relative_to(ROOT)),
            )
            if warm_round == 6 or probe_authority is not None:
                temporary_ready = folder / "runtime_parent_ready.json.tmp"
                temporary_ready.write_text(
                    json.dumps(
                        {
                            "command_started_sha256": started_receipt["sha256"],
                            "process_started_sha256": process_receipt["sha256"],
                        }
                    ),
                    encoding="utf-8",
                )
                temporary_ready.replace(folder / "runtime_parent_ready.json")
            try:
                code = process.wait(timeout=limit)
            except subprocess.TimeoutExpired:
                from .resources import kill_tree

                kill_tree(process)
                stream.write("\nHarness timeout: not a solver-returned limit.\n")
                code = 124
        except OSError as exc:
            stream.write(str(exc))
            code = 127
    elapsed = time.perf_counter() - start
    receipt = append(
        "command_finished",
        seconds={stage: elapsed},
        stage=stage,
        group=group,
        argv=argv,
        exit_code=code,
        elapsed_seconds=elapsed,
        ended_at=utc(),
        log=str(log.relative_to(ROOT)),
        log_sha256=sha(log),
        run=str(folder.relative_to(ROOT)),
    )
    (folder / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("group", "exit_code", "elapsed_seconds", "log")}))
    return code
