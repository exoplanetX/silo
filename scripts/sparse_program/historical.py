"""Run historical inputs under the new budget; old evidence is read-only."""

import json
import sys
from uuid import uuid4

from . import checker, ledger


def run():
    # Import functions only. Do not invoke either old CLI or old accounting API.
    sys.path.insert(0, str(ledger.ROOT / "scripts/prototype"))
    sys.path.insert(0, str(ledger.ROOT / "src"))
    import evidence as ev
    from revision_validation import saved_diagnostic
    from validate import Runner, write_json

    from silo import SolveOptions, solve
    from silo.io import model_from_dict

    pins = json.loads((ledger.OUT / "preserved_old_evidence.json").read_text())

    def check_pins():
        for name, digest in pins.items():
            assert ledger.sha(ledger.ROOT / name) == digest, name

    check_pins()
    folder = ledger.OUT / "historical" / str(uuid4())
    folder.mkdir(parents=True)
    evidence = ev.build_evidence()
    runner = Runner(folder, None, evidence)
    for entry in evidence["cases"]:
        runner.record(entry["id"], lambda entry=entry: runner.case(entry))
    for boundary, truth in zip(
        ev.load_manifest()["boundaries"], evidence["boundaries"], strict=True
    ):
        runner.record(boundary["id"], lambda b=boundary, t=truth: runner.boundary(b, t))
    assert len(runner.records) == 288
    runner.record("two_public_research_examples", runner.integration)
    historical_native_calls = runner.native_calls
    for record in evidence["diagnostics"]:
        runner.record(record["id"], lambda record=record: saved_diagnostic(record))
    assert len(evidence["diagnostics"]) == 64 and runner.native_calls == historical_native_calls
    audit_path = ledger.ROOT / "outputs/audit_20261024/probe_models.json"
    references_path = ledger.ROOT / "outputs/audit_20261024/probe_records.json"
    models = json.loads(audit_path.read_text())
    references = {r["id"]: r for r in json.loads(references_path.read_text())}
    assert len(models) == len(references) == 192

    def audit_case(payload, config):
        truth = references[payload["name"]]
        options = {"time_limit": 2}
        if config == "reference_controls":
            options.update(
                presolve=False, scaling=False, cuts=False, heuristics=False, node_strategy="dfs"
            )
        runner.native_calls += 1
        result = solve(model_from_dict(payload), SolveOptions(**options)).to_dict()
        reference = {"status": truth["reference_status"], "objective": truth["reference_objective"]}
        assert result["status"] == reference["status"]
        checked = checker.check(
            payload,
            result,
            truth=reference,
            options=options,
            mip=any(v["type"] != "continuous" for v in payload["variables"]),
        )
        if result["status"] in ("infeasible", "unbounded"):
            checker.certificate(payload, result)
        output = folder / (payload["name"] + "_" + config + ".json")
        write_json(output, result)
        return {
            "check": checked,
            "reference_source_sha256": ledger.sha(references_path),
            "native_calls": 1,
        }

    for payload in models:
        for config in ("default", "reference_controls"):
            runner.record(
                payload["name"] + "_" + config, lambda p=payload, c=config: audit_case(p, c)
            )
    assert len(runner.records) == 288 + 1 + 64 + 384
    check_pins()
    summary = {
        "records": runner.records,
        "all_pass": all(r["pass"] for r in runner.records),
        "old_cases": 288,
        "old_audit_models": 192,
        "old_audit_configurations": 384,
        "saved_diagnostics": 64,
        "saved_diagnostic_new_solves": 0,
        "old_native_calls": historical_native_calls,
        "audit_native_calls": runner.native_calls - historical_native_calls,
        "new_reference_calls": 0,
        "old_evidence_unchanged": True,
        "old_ledger_written": False,
        "source": ledger.identity(),
    }
    write_json(folder / "summary.json", summary)
    return 0 if summary["all_pass"] else 1
