"""Recheck frozen prototype evidence without accessing its exhausted ledger.

The old 288 cases get at most two separately reserved revision rounds. Saved
diagnostics are checked as data only; this driver never resolves them.
"""

import argparse
import json
from collections import Counter
from time import perf_counter

import evidence as ev
from revision_account import OUT, ROOT
from validate import Runner, environment, write_json
from validate_results import validate


def saved_diagnostic(record):
    entry = next(e for e in ev.load_manifest()["cases"] if e["id"] == record["case_id"])
    base = ev.diagnostic_payload(ev.raw_payload(entry), record["prepare_model"])
    payload = ev.diagnostic_payload(base, record["actions"])
    assert ev.digest(payload) == record["model_sha256"]
    path = ROOT / "outputs/prototype/validation/diagnostics" / (record["id"] + "_output.json")
    output = json.loads(path.read_text(encoding="utf-8"))
    check = validate(payload, output, record["reference_proof"])
    stats = output["diagnostics"]
    if record["case_id"].startswith("LP"):
        if record["expected"]["reuse_attempt_required"]:
            assert stats.get("warm_starts", 0) + bool(stats.get("fallback_reason")) == 1
        if record["variant"] == "invalid_basis_fallback":
            assert stats["fallback_reason"] and stats["cold_starts"] == 1
    else:
        assert stats["cuts_enabled"] == record["options"]["cuts"]
        assert stats["heuristics_enabled"] == record["options"]["heuristics"]
        if not record["options"]["cuts"]:
            assert stats["gmi_attempts"] == stats["cuts_added"] == 0
        if not record["options"]["heuristics"]:
            assert stats["heuristic_calls"] == 0
    return {"check": check, "source_sha256": ev.sha256(path.read_bytes()), "new_native_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("old", "saved"), required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    folder = (OUT / args.name).resolve()
    if not folder.is_relative_to(OUT.resolve()):
        parser.error("Use a fresh folder in the revision output directory")
    folder.mkdir(parents=True, exist_ok=False)
    start = perf_counter()
    evidence = ev.build_evidence()
    write_json(folder / "raw_evidence.json", evidence)
    write_json(folder / "environment.json", environment())
    runner = Runner(folder, None, evidence)
    if args.group == "old":
        for entry in evidence["cases"]:
            runner.record(entry["id"], lambda entry=entry: runner.case(entry))
        for boundary, reference in zip(
            ev.load_manifest()["boundaries"], evidence["boundaries"], strict=True
        ):
            runner.record(boundary["id"], lambda b=boundary, r=reference: runner.boundary(b, r))
        assert len(runner.records) == 288
        runner.record("two_public_research_examples", runner.integration)
    else:
        assert len(evidence["diagnostics"]) == 64
        for record in evidence["diagnostics"]:
            runner.record(record["id"], lambda record=record: saved_diagnostic(record))
        assert runner.native_calls == 0
    summary = {
        "group": args.group,
        "all_pass": all(r["pass"] for r in runner.records),
        "records": len(runner.records),
        "failed": [r for r in runner.records if not r["pass"]],
        "native_calls": runner.native_calls,
        "passed_by_suite": dict(
            Counter(r.get("suite", args.group) for r in runner.records if r["pass"])
        ),
        "elapsed_seconds": perf_counter() - start,
        "old_ledger_accessed": False,
    }
    write_json(folder / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
