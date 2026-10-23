"""Deterministic source projection and read-only boundary checks for the workbench."""

import hashlib
import importlib.util
import json
import threading
from http.client import HTTPConnection
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "silo_workbench", Path(__file__).resolve().parents[2] / "scripts/workbench.py"
)
assert SPEC is not None and SPEC.loader is not None
workbench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workbench)


@pytest.fixture
def repository(tmp_path):
    files = {
        ".silo-dos/project_profile.md": "# Snapshot\n\n| 项目 | 当前状态 / 依据 |\n"
        "|---|---|\n| Phase 9 | open / parked |\n",
        "ROADMAP.md": "# Roadmap\n\n## Phase 2: LP\n\nStatus: bounded complete.\n"
        "\nGoal: reference solver.\n",
        "pyproject.toml": '[project]\nversion = "0.1.0"\n',
        "tasks/README.md": "# Task rules\n",
        "learning/lessons/L0042-example/README.md": "---\nlesson_id: L0042\n"
        "title: 固定篇目\nstatus: checked\nverified_code: abc123\n"
        "verified_on: 2026-10-20\n---\n\n# 正文\n",
        "learning/lessons/L0042-example/exercises.md": "# 练习\n",
        "tasks/codex/20261023-01-01_example.md": "# A contract\n",
        "tasks/codex/20261023-02-01_other.md": "# Another contract\n",
        "tasks/reports/20261023-01-01_example_report.md": "# Failed execution\n",
        "src/silo/example.py": '"""Source, never executed by the viewer."""\n',
    }
    for name, text in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_source_fingerprint_and_missing_are_distinct(repository):
    name = ".silo-dos/project_profile.md"
    actual = hashlib.sha256((repository / name).read_bytes()).hexdigest()
    assert workbench.source_record(repository, name, actual)["state"] == "available"
    assert workbench.source_record(repository, name, "old")["state"] == "changed"
    assert workbench.source_record(repository, "docs/absent.md")["state"] == "missing"
    item = {"id": "A", "sources": [name]}
    assert not workbench.enrich_record(repository, item, {name: actual})["needs_review"]
    assert workbench.enrich_record(repository, item, {name: "old"})["needs_review"]


@pytest.mark.parametrize("name", [
    "../outside.md", "/outside.md", "C:/secret.md", ".git/config", ".venv/key.md",
    "scripts/workbench.py", "tasks/history_exceptions.json", "docs/../pyproject.toml",
    "AGENTS.md", "docs/no-such-file.md",
])
def test_viewer_rejects_nonallowlisted_paths(repository, name):
    with pytest.raises((ValueError, OSError)):
        workbench.read_document(repository, name)


def test_viewer_returns_exact_text_and_hash(repository):
    doc = workbench.read_document(repository, "src/silo/example.py")
    assert doc["text"].startswith('"""Source')
    assert doc["path"] == "src/silo/example.py"
    assert len(doc["sha256"]) == 64
    assert workbench.read_document(repository, "tasks/README.md")["text"].splitlines() == [
        "# Task rules"
    ]


def test_profile_and_phase_status_are_preserved(repository):
    profile = (repository / ".silo-dos/project_profile.md").read_text(encoding="utf-8")
    assert workbench.profile_rows(profile)["Phase 9"] == "open / parked"
    roadmap = (repository / "ROADMAP.md").read_text(encoding="utf-8")
    phases = workbench.phases_from(roadmap)
    assert phases == [{"number": 2, "title": "LP", "status": "bounded complete.",
                       "goal": "reference solver.", "source": "ROADMAP.md"}]


def test_report_presence_does_not_infer_success(repository):
    tasks = workbench.tasks_from(repository)
    assert len(tasks) == 2
    with_report = next(item for item in tasks if item["report"])
    assert with_report["title"] == "A contract"
    assert "status" not in with_report
    assert "accepted" not in with_report
    assert next(item for item in tasks if not item["report"])["title"] == "Another contract"


def test_learning_identity_baseline_and_exercises(repository):
    lesson, = workbench.lessons_from(repository)
    assert lesson["lesson_id"] == "L0042"
    assert lesson["verified_code"] == "abc123"
    assert lesson["verified_on"] == "2026-10-20"
    assert lesson["title"] == "固定篇目"
    assert lesson["exercises"] is True
    assert lesson["solutions"] is False


def test_state_surfaces_changed_and_missing_sources(repository, monkeypatch):
    catalog = {
        "source_hashes": {".silo-dos/project_profile.md": "old", "docs/missing.md": "old"},
        "reviewed_on": "2026-10-23", "baseline": "snapshot", "assessment_note": "proposal",
        "units": [{"id": "C", "status": "HOLD", "sources": [".silo-dos/project_profile.md"]}],
        "dimensions": [], "capabilities": [], "delivery": [], "boundaries": [],
        "milestones": [], "budgets": [],
    }
    config = repository / "catalog.json"
    config.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(workbench, "git_info", lambda root: {"head": "example"})
    state = workbench.build_state(repository, config)
    assert len(state["warnings"]) == 2
    assert state["units"][0]["needs_review"] is True
    assert state["units"][0]["status"] == "HOLD"
    assert state["assessment_note"] == "proposal"


def test_http_read_only_routes_and_host_boundary(repository, tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><title>SILO</title>", encoding="utf-8")
    server = workbench.ThreadingHTTPServer(
        ("127.0.0.1", 0), workbench.make_handler(repository, assets)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        connection.request("GET", "/")
        response = connection.getresponse()
        assert response.status == 200
        assert "default-src 'self'" in response.getheader("Content-Security-Policy")
        assert response.getheader("Cache-Control") == "no-store"
        assert b"SILO" in response.read()
        connection.request("GET", "/api/document?path=pyproject.toml")
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read())["path"] == "pyproject.toml"
        connection.request("GET", "/api/document?path=..%2Foutside.md")
        response = connection.getresponse()
        assert response.status == 400
        response.read()
        connection.request("POST", "/api/state", body=b"{}")
        response = connection.getresponse()
        assert response.status == 405
        response.read()
        connection.request("GET", "/", headers={"Host": "untrusted.example"})
        response = connection.getresponse()
        assert response.status == 403
        response.read()
        connection.request("GET", "/catalog.json")
        response = connection.getresponse()
        assert response.status == 404
        response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
