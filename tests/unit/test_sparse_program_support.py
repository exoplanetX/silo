"""Evidence guards are independent of the not-yet-implemented sparse solver."""

import importlib.util
import json
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
