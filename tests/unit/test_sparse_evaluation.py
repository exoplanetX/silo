"""Fail-closed receipt logic only; no solver, reference, build or install runs."""

import copy
import json
from hashlib import sha256
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from sparse_program import evaluation

    monkeypatch.setattr(evaluation.ledger, "ROOT", tmp_path)
    monkeypatch.setattr(evaluation.ledger, "OUT", tmp_path / "outputs")
    (tmp_path / "outputs").mkdir(exist_ok=True)
    return evaluation


def identity(module, files):
    return {"source": files, "source_sha256": module.ledger.digest(files), "inputs": {}}


def test_source_match_rejects_algorithm_changes_even_with_bridge(monkeypatch, tmp_path):
    m = module(monkeypatch, tmp_path)
    old = identity(m, {"src/silo/solver.py": "a" * 64})
    new = identity(m, {"src/silo/solver.py": "b" * 64})
    with pytest.raises(m.EvidenceError, match="Algorithm source changed"):
        m.source_match(old, new, {"changes": []})
    wrong_digest = {**old, "source_sha256": "0" * 64}
    with pytest.raises(m.EvidenceError, match="digest"):
        m.source_match(wrong_digest, old)


@pytest.mark.parametrize(
    "name,before,after",
    [
        (
            "src/silo/__init__.py",
            b"__version__ = '0.2.0a2'\nfrom silo.solver import solve\n",
            b"__version__ = '0.3.0a1'\nfrom silo.solver import solve\n",
        ),
        (
            "pyproject.toml",
            b'[project]\nversion="0.2.0a2"\ndescription="dense"\ndependencies=["numpy"]\n',
            b'[project]\nversion="0.3.0a1"\ndescription="sparse"\ndependencies=["numpy"]\n',
        ),
    ],
)
def test_metadata_bridge_requires_actual_bytes_and_only_allowed_literals(
    monkeypatch, tmp_path, name, before, after
):
    m = module(monkeypatch, tmp_path)
    a, b = tmp_path / "outputs/before", tmp_path / "outputs/after"
    a.write_bytes(before)
    b.write_bytes(after)
    old, new = (
        identity(m, {name: sha256(before).hexdigest()}),
        identity(m, {name: sha256(after).hexdigest()}),
    )
    bridge = {
        "changes": [
            {
                "path": name,
                "before_path": "outputs/before",
                "after_path": "outputs/after",
                "before_sha256": old["source"][name],
                "after_sha256": new["source"][name],
            }
        ]
    }
    assert len(m.source_match(old, new, bridge)["metadata_bridges"]) == 1
    with pytest.raises(m.EvidenceError, match="unique byte bridge"):
        m.source_match(old, new, {"changes": []})
    bad = after + b"# unrelated byte drift\n"
    b.write_bytes(bad)
    new = identity(m, {name: sha256(bad).hexdigest()})
    bridge["changes"][0]["after_sha256"] = new["source"][name]
    with pytest.raises(m.EvidenceError, match="outside allowed metadata"):
        m.source_match(old, new, bridge)


def test_fixed_denominator_rejects_duplicates_missing_ids_and_failures(monkeypatch, tmp_path):
    m = module(monkeypatch, tmp_path)
    m._fixed_records([{"id": "a", "pass": True}, {"id": "b", "pass": True}], {"a", "b"})
    for records in (
        [{"id": "a", "pass": True}] * 2,
        [{"id": "a", "pass": True}],
        [{"id": "a", "pass": True}, {"id": "b", "pass": False}],
    ):
        with pytest.raises(m.EvidenceError):
            m._fixed_records(records, {"a", "b"})


def test_request_result_and_input_hash_binding_detects_tampering(monkeypatch, tmp_path):
    m = module(monkeypatch, tmp_path)
    folder = tmp_path / "outputs/case"
    folder.mkdir()
    payload = folder / "input.json"
    payload.write_text("{}", encoding="utf-8")
    entry = {
        "id": "PRESS-LIMIT-TIME",
        "group": "pressure",
        "options": {"time_limit": 0},
        "payload_path": "outputs/case/input.json",
        "payload_sha256": m.ledger.sha(payload),
        "expected_statuses": ["limit"],
        "metadata": {"expected_reason": "time_limit"},
    }
    request, output = (
        folder / (entry["id"] + ".request.json"),
        folder / (entry["id"] + ".result.json"),
    )
    request.write_text(
        json.dumps({"entry": entry, "engine": "sparse", "seconds": 10}), encoding="utf-8"
    )
    packet = {
        "id": entry["id"],
        "engine": "sparse",
        "options": {"time_limit": 0, "lp_engine": "sparse"},
        "native_root_calls_started": 1,
        "native_root_calls_completed": 1,
        "native_lp_calls_started": 0,
        "native_lp_calls_completed": 0,
        "result": {"status": "limit", "termination_reason": "time_limit", "diagnostics": {}},
    }
    output.write_text(json.dumps(packet), encoding="utf-8")
    record = {
        "input_sha256": entry["payload_sha256"],
        "request_sha256": m.ledger.sha(request),
        "result_path": str(output.relative_to(tmp_path)),
        "result_sha256": m.ledger.sha(output),
        "status": "limit",
        "monitor": {
            "exit_code": 0,
            "guard_reason": None,
            "elapsed_seconds": 0.001,
            "peak_rss_bytes": 1024,
        },
    }
    assert m._record_files(record, entry, "sparse")["result"]["status"] == "limit"
    packet["options"]["time_limit"] = 1
    output.write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(m.EvidenceError, match="hash mismatch"):
        m._record_files(record, entry, "sparse")
    record["result_sha256"] = m.ledger.sha(output)
    with pytest.raises(m.EvidenceError, match="Actual options"):
        m._record_files(record, entry, "sparse")


def test_bound_files_rejects_unregistered_extra_file(monkeypatch, tmp_path):
    m = module(monkeypatch, tmp_path)
    folder = tmp_path / "outputs/group"
    folder.mkdir()
    result, summary = folder / "result.json", folder / "summary.json"
    result.write_text("{}", encoding="utf-8")
    summary.write_text("{}", encoding="utf-8")
    declared = {"bound_files": {str(result.relative_to(tmp_path)): m.ledger.sha(result)}}
    m._tree_bound(summary, declared)
    (folder / "extra.txt").write_text("not pinned", encoding="utf-8")
    with pytest.raises(m.EvidenceError, match="inventory"):
        m._tree_bound(summary, declared)


def test_independent_review_requires_eight_go_items_source_and_current_evidence(
    monkeypatch, tmp_path
):
    m = module(monkeypatch, tmp_path)
    current = identity(m, {"src/silo/solver.py": "a" * 64})
    items = []
    for i in range(1, 9):
        path = tmp_path / f"outputs/item{i}.json"
        path.write_text(str(i), encoding="utf-8")
        items.append({"id": i, "pass": True, "evidence_refs": [m._ref(path)]})
    raw = tmp_path / "outputs/review.txt"
    raw.write_text("Independent review", encoding="utf-8")
    review = {
        "schema_version": 1,
        "program": m.ledger.PROGRAM,
        "decision": "GO",
        "source": current,
        "reviewer": {
            "id": "/root/independent_gate",
            "independent": True,
            "read_only": True,
            "files_modified": [],
            "write_attempts": 0,
        },
        "unresolved_required": [],
        "criteria": [
            {"id": item["id"], "decision": "GO", "evidence": item["evidence_refs"]}
            for item in items
        ],
        "review_record": m._ref(raw),
    }
    assert m.validate_final_review(review, items, current)["decision"] == "GO"
    for mutation in ("writer", "missing_item", "unresolved", "evidence"):
        bad = copy.deepcopy(review)
        if mutation == "writer":
            bad["reviewer"]["id"] = "/root"
        elif mutation == "missing_item":
            bad["criteria"].pop()
        elif mutation == "unresolved":
            bad["unresolved_required"].append("capacity")
        else:
            bad["criteria"][0]["evidence"] = []
        with pytest.raises(m.EvidenceError):
            m.validate_final_review(bad, items, current)


def test_sp4_missing_evidence_reports_all_eight_obligations(monkeypatch, tmp_path):
    m = module(monkeypatch, tmp_path)

    def missing():
        raise m.EvidenceError("required evidence missing")

    for name in (
        "frozen_sp1_gate",
        "capacity_check",
        "mechanism_check",
        "warm_check",
        "mip_cg_check",
        "historical_check",
        "quality_check",
        "delivery_check",
        "docs_budget_check",
    ):
        monkeypatch.setattr(m, name, missing)
    checked = m.sp4()
    assert not checked["mechanical_checks_pass"] and checked["unmet_ids"] == list(range(1, 9))
    assert checked["technical_review_required"]
