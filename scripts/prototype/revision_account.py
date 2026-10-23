"""Append-only verification receipts for the single bounded revision contract."""

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/prototype_revision_20261024"
CAPS = {
    # Direct human approval on 2026-10-24 raises only this task's original128 cap.
    "targeted_public_calls": 144,
    "new_matrix_rounds": 2,
    "old_matrix_rounds": 2,
    "full_quality_runs": 3,
    "verification_seconds": 3600,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot():
    paths = [
        *sorted((ROOT / "src/silo").rglob("*.py")),
        ROOT / "tests/fixtures/prototype_revision_manifest.json",
    ]
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in paths},
    }


def totals():
    result = {name: 0 for name in CAPS}
    previous = None
    path = OUT / "ledger.jsonl"
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        checksum = event.pop("sha256")
        assert event["previous_sha256"] == previous
        assert (
            checksum
            == hashlib.sha256(
                json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            ).hexdigest()
        )
        previous = checksum
        for name in CAPS:
            result[name] += event.get("consumption", {}).get(name, 0)
    assert all(result[k] <= cap for k, cap in CAPS.items()), result
    return result


def append(category, consumption=None, **details):
    OUT.mkdir(exist_ok=True)
    path = OUT / "ledger.jsonl"
    used = totals()
    consumption = {} if consumption is None else consumption
    assert all(used[k] + consumption.get(k, 0) <= cap for k, cap in CAPS.items()), used
    old = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    event = {
        "program": "SILO-PROTOTYPE-REVISION-20261024",
        "category": category,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "previous_sha256": json.loads(old[-1])["sha256"] if old else None,
        "consumption": consumption,
        **details,
    }
    event["sha256"] = hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, allow_nan=False) + "\n")
    return event


def run(command, category, *, targeted_calls=0, **consumption):
    """Reserve calls before running; charge actual wall even on a failed process."""
    run_id = str(uuid4())
    append(
        category + "_started",
        {"targeted_public_calls": targeted_calls, **consumption},
        run_uuid=run_id,
        command=command,
        identity=snapshot(),
    )
    start = time.perf_counter()
    log = OUT / (category + "_" + run_id + ".log")
    with log.open("w", encoding="utf-8") as stream:
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=max(
                    0.001, CAPS["verification_seconds"] - totals()["verification_seconds"] - 1
                ),
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            stream.write("\nRevision verification wall budget expired.\n")
            code = 124
    elapsed = time.perf_counter() - start
    append(
        category + "_finished",
        {"verification_seconds": elapsed},
        run_uuid=run_id,
        exit_code=code,
        log=str(log.relative_to(ROOT)),
        log_sha256=sha(log),
    )
    print(
        json.dumps(
            {
                "category": category,
                "exit_code": code,
                "seconds": elapsed,
                "log": str(log),
            }
        )
    )
    return code
