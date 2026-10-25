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
    assert all(rounds[k] <= v for k, v in GROUP_ROUNDS.items()), rounds
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
    assert all(0 <= v <= GROUP_ROUNDS[k] - used["rounds"][k] for k, v in rounds.items())
    events = history()
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


def command(argv, *, stage, group, timeout=None, reserve_round=False, calls=None, cwd=ROOT):
    """Run one top-level check, charge it once, retain failures and process identity.

    Caller-supplied call counts are declared reservations, not claims of completed
    calls. Child case records provide actual started/completed counts. This wrapper
    cannot double-charge the child's timers. Long groups must give a bounded timeout.
    """
    assert not os.environ.get("SILO_SPARSE_ACCOUNT_PARENT"), (
        "Do not nest accounting parents; invoke budgeted CLI directly."
    )
    used = totals()
    remaining = min(
        STAGE_SECONDS[stage] - used["seconds"][stage], TOTAL_SECONDS - used["total_seconds"]
    )
    limit = remaining - 1 if timeout is None else min(timeout, remaining - 1)
    assert limit > 0, "No verification budget remains"
    if timeout is not None:
        assert timeout <= remaining - 1, "Insufficient budget for the entire planned batch"
    folder = OUT / "runs" / (utc().replace(":", "-") + "_" + str(uuid4()))
    folder.mkdir(parents=True)
    ident = identity()
    (folder / "identity.json").write_text(json.dumps(ident, indent=2), encoding="utf-8")
    append(
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
    )
    start = time.perf_counter()
    log = folder / "console.log"
    with log.open("w", encoding="utf-8") as stream:
        try:
            child_env = {**os.environ, "SILO_SPARSE_ACCOUNT_PARENT": str(folder.relative_to(ROOT))}
            process = subprocess.Popen(
                argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, env=child_env
            )
            append(
                "process_started",
                stage=stage,
                group=group,
                pid=process.pid,
                run=str(folder.relative_to(ROOT)),
            )
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
