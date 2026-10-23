"""Identity-bound append history for the prototype's scarce verification calls."""

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import evidence as ev

PROGRAM = "SILO-PROTOTYPE-20261023"


def identity(environment):
    return {key: environment[key] for key in ("commit", "runner_sha256", "checker_sha256")} | {
        "source_tree_sha256": ev.digest(environment["source_hashes"]),
    }


def audit(data):
    assert data["program"] == PROGRAM and data["schema"] == 2
    assert data["manifest_sha256"] in ev.FROZEN_HASHES["tests/fixtures/prototype_manifest.json"]
    scale, diagnostics, previous = 0, 0, None
    calls = set()
    for original in data["history"]:
        event = dict(original)
        checksum = event.pop("event_sha256")
        assert checksum == ev.digest(event), "Ledger event hash mismatch"
        assert event["previous_event_sha256"] == previous, "Ledger history chain mismatch"
        previous = checksum
        scale += event["scale_runs"]
        diagnostics += event["diagnostic_calls"]
        if event["diagnostic_calls"]:
            assert event["call_id"] not in calls, "Duplicate diagnostic solve ID"
            calls.add(event["call_id"])
    assert (data["scale_runs"], data["diagnostic_calls"]) == (scale, diagnostics)
    assert scale <= 3 and diagnostics <= 64
    return data


def append(data, kind, environment, output, run_uuid, call_id, *, legacy=None):
    audit(data)
    event = {
        "kind": kind,
        "run_uuid": run_uuid,
        "call_id": call_id,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_directory": str(Path(output).resolve()),
        "identity": identity(environment),
        "scale_runs": int(kind == "scale_run" or legacy == "scale_run"),
        "diagnostic_calls": int(kind == "diagnostic_call" or legacy == "diagnostic_call"),
        "previous_event_sha256": data["history"][-1]["event_sha256"] if data["history"] else None,
    }
    if legacy:
        event["legacy_import"] = {
            "original_run_uuid": None,
            "original_issue_time": None,
            "note": "Imported existing consumption; UUID/time were not recorded at execution.",
        }
    event["event_sha256"] = ev.digest(event)
    data["history"].append(event)
    data["scale_runs"] += event["scale_runs"]
    data["diagnostic_calls"] += event["diagnostic_calls"]
    return audit(data)


def save(path, data):
    audit(data)
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def load(path):
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("schema") == 2:
            return audit(old)
    else:
        old = {"scale_runs": 0, "diagnostic_calls": 0}
    data = {
        "program": PROGRAM,
        "schema": 2,
        "manifest_sha256": ev.sha256(
            (ev.ROOT / "tests/fixtures/prototype_manifest.json").read_bytes()
        ),
        "scale_runs": 0,
        "diagnostic_calls": 0,
        "history": [],
    }
    # Only this known pre-history run can be imported. No guessed consumed calls.
    if old["scale_runs"]:
        assert old["scale_runs"] == 1, "Unknown legacy scale history"
        folder = path.parent / "validation/core"
        summary_path = folder / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert summary["ledger"]["scale_runs"] == 1 and summary["records"] == 288
        environment = json.loads((folder / "environment.json").read_text(encoding="utf-8"))
        append(
            data, "legacy_import", environment, folder, None, "legacy-core-1", legacy="scale_run"
        )
        data["history"][-1]["legacy_import"]["summary_sha256"] = ev.sha256(
            summary_path.read_bytes()
        )
        event = data["history"][-1]
        event["event_sha256"] = ev.digest({k: v for k, v in event.items() if k != "event_sha256"})
    if old["diagnostic_calls"]:
        folder = path.parent / "validation/diagnostics"
        saved = sorted(folder.glob("D-*_output.json"))
        assert len(saved) == old["diagnostic_calls"], "Unknown legacy diagnostic consumption"
        environment = json.loads((folder / "environment.json").read_text(encoding="utf-8"))
        for output in saved:
            append(
                data,
                "legacy_import",
                environment,
                folder,
                None,
                output.name.removesuffix("_output.json"),
                legacy="diagnostic_call",
            )
            event = data["history"][-1]
            event["legacy_import"]["output_sha256"] = ev.sha256(output.read_bytes())
            event["event_sha256"] = ev.digest(
                {k: v for k, v in event.items() if k != "event_sha256"}
            )
    data["import_receipt_uuid"] = str(uuid4()) if data["history"] else None
    save(path, data)
    return data
