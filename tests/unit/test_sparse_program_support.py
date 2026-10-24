"""Evidence guards are independent of the not-yet-implemented sparse solver."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts/sparse_program" / (name + ".py")
    )
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_append_chain_rejects_reserved_fields_and_tampering(tmp_path, monkeypatch):
    ledger = module("ledger")
    monkeypatch.setattr(ledger, "OUT", tmp_path)
    ledger.append("one", seconds={"SP1": 0.1})
    ledger.append("two", payload_sha256="raw identity")
    path = tmp_path / "ledger.jsonl"
    original = path.read_bytes()
    with pytest.raises(AssertionError, match="Reserved"):
        ledger.append("bad", sha256="shadow")
    assert path.read_bytes() == original
    lines = path.read_text().splitlines()
    event = json.loads(lines[0])
    event["kind"] = "changed"
    path.write_text(json.dumps(event) + "\n" + lines[1] + "\n")
    with pytest.raises(AssertionError):
        ledger.history()


def test_budget_refusal_preserves_prior_consumption(tmp_path, monkeypatch):
    ledger = module("ledger")
    monkeypatch.setattr(ledger, "OUT", tmp_path)
    monkeypatch.setattr(ledger, "STAGE_SECONDS", {"SP1": 1})
    ledger.append("used", seconds={"SP1": 0.75})
    before = (tmp_path / "ledger.jsonl").read_bytes()
    with pytest.raises(AssertionError):
        ledger.append("over", seconds={"SP1": 0.5})
    assert (tmp_path / "ledger.jsonl").read_bytes() == before
    assert ledger.totals()["total_seconds"] == 0.75


def test_warm_metric_pairs_repetitions_and_preserves_initial_cost(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from sparse_program.warm import aggregate

    records = [
        {
            "id": f"chain-{i}",
            "mode": mode,
            "repetition": r,
            "pass": True,
            "segment_seconds": (10 if mode == "warm" else 20) * (r + 1),
            "total_seconds": (30 if mode == "warm" else 20) * (r + 1),
        }
        for i in range(8)
        for r in range(5)
        for mode in ("cold", "warm")
    ]
    measured = aggregate(records)
    assert measured["median_ratio"] == 2 and measured["nonregressing"] == 8
    assert measured["performance_pass"]
    assert all(r == pytest.approx(2 / 3) for r in measured["initial_inclusive_ratios"].values())
    with pytest.raises(AssertionError):
        aggregate(records[:-1] + [records[0]])


@pytest.mark.skipif(os.name != "nt", reason="Windows venv redirector accounting")
def test_os_rss_includes_real_interpreter_and_nested_children(tmp_path):
    guard = module("resources")
    child = "import time; a=bytearray(40*1024*1024); a[:]=b'x'*len(a); time.sleep(.25)"
    parent = f"import subprocess,sys; subprocess.run([sys.executable,'-c',{child!r}],check=True)"
    result = guard.guarded([sys.executable, "-c", parent], tmp_path, tmp_path / "tree.log", 10)
    assert result["exit_code"] == 0 and result["guard_reason"] is None
    assert result["peak_rss_bytes"] >= 40 * 1024 * 1024
    assert result["monitored_processes"] >= 2
    assert result["process_scope"] == "root_and_descendants"


@pytest.mark.parametrize("scenario", ["normal", "timeout", "rss"])
def test_external_guards_report_os_peak_and_never_solver_limit(tmp_path, scenario):
    guard = module("resources")
    code = "import time; a=bytearray(8*1024*1024); time.sleep(0.05)"
    if scenario == "timeout":
        code = "import time; time.sleep(3)"
    result = guard.guarded(
        [sys.executable, "-c", code],
        tmp_path,
        tmp_path / "child.log",
        seconds=0.1 if scenario == "timeout" else 5,
        rss_limit=1 if scenario == "rss" else 1 << 30,
    )
    assert result["peak_rss_bytes"] > 0
    assert result["os_peak_method"] in ("PeakWorkingSetSize", "/proc VmHWM")
    if scenario == "normal":
        assert result["exit_code"] == 0 and result["guard_reason"] is None
    else:
        assert result["guard_reason"] == "harness_" + (
            "timeout" if scenario == "timeout" else "peak_rss"
        )
