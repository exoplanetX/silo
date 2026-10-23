"""Budget resets, duplicate IDs and broken identities cannot grant extra calls."""

import copy
import runpy
from pathlib import Path

import pytest


@pytest.fixture
def ledger_api(monkeypatch):
    folder = Path(__file__).resolve().parents[2] / "scripts/prototype"
    monkeypatch.syspath_prepend(str(folder))
    return runpy.run_path(str(folder / "run_ledger.py"))


def empty(api):
    return {
        "program": api["PROGRAM"],
        "schema": 2,
        "manifest_sha256": next(
            iter(api["ev"].FROZEN_HASHES["tests/fixtures/prototype_manifest.json"])
        ),
        "scale_runs": 0,
        "diagnostic_calls": 0,
        "history": [],
    }


def environment():
    return {
        "commit": "test",
        "runner_sha256": "a",
        "checker_sha256": "b",
        "source_hashes": {"x": "c"},
    }


@pytest.mark.parametrize("tamper", ["counter", "event", "manifest", "program"])
def test_tampered_history_or_identity_is_rejected(ledger_api, tmp_path, tamper):
    data = empty(ledger_api)
    ledger_api["append"](data, "diagnostic_call", environment(), tmp_path, "run-1", "D-1")
    bad = copy.deepcopy(data)
    if tamper == "counter":
        bad["diagnostic_calls"] = 0
    elif tamper == "event":
        bad["history"][0]["run_uuid"] = "changed"
    elif tamper == "manifest":
        bad["manifest_sha256"] = "changed"
    else:
        bad["program"] = "changed"
    with pytest.raises(AssertionError):
        ledger_api["audit"](bad)
    path = tmp_path / "ledger.json"
    ledger_api["save"](path, data)
    assert ledger_api["load"](path) == data


def test_duplicate_ids_and_over_budget_calls_are_rejected(ledger_api, tmp_path):
    data = empty(ledger_api)
    for i in range(64):
        ledger_api["append"](data, "diagnostic_call", environment(), tmp_path, "run-1", f"D-{i}")
    assert data["diagnostic_calls"] == 64
    with pytest.raises(AssertionError, match="Duplicate"):
        ledger_api["append"](
            copy.deepcopy(data), "diagnostic_call", environment(), tmp_path, "run-2", "D-0"
        )
    with pytest.raises(AssertionError):
        ledger_api["append"](
            copy.deepcopy(data), "diagnostic_call", environment(), tmp_path, "run-2", "D-64"
        )
