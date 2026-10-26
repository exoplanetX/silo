"""Deterministic source projection and read-only boundary checks for the workbench."""

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
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


def test_reliability_sources_are_read_without_running_examples(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Reading a lesson must not run a subprocess")

    monkeypatch.setattr(workbench.subprocess, "run", forbidden)
    data = workbench.reliability_lesson(workbench.ROOT)
    assert data["metadata"]["status"] == "checked"
    assert data["metadata"]["verified_on"] == "2026-10-26"
    assert [item["id"] for item in data["outline"]["modules"]] == [
        f"R{i:02}" for i in range(1, 9)
    ]
    assert len(re.findall(r"^## \d+\.", data["documents"]["body"]["text"], re.M)) == 10
    assert data["eta"]["e1"] == [[2, 0], [1, 1]]
    assert data["eta"]["e2"] == [[1, 3], [0, 2]]
    assert data["eta"]["ordinary_rhs"] == [2, -1]
    assert data["eta"]["transpose_rhs"] == [3, 7]
    assert data["documents"]["examples"]["path"].endswith("examples.py")


@pytest.mark.parametrize("problem", ["path", "heading", "zero", "version", "units"])
def test_reliability_rejects_mismatched_or_invalid_teaching_data(tmp_path, problem):
    lesson = tmp_path / workbench.RELIABILITY_DIR
    shutil.copytree(workbench.ROOT / workbench.RELIABILITY_DIR, lesson)
    path = lesson / "web_outline.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if problem == "path":
        data["body"] = "../private.md"
    elif problem == "heading":
        data["modules"][0]["heading"] = "R01 missing heading"
    elif problem == "zero":
        data["scenarios"][0]["rhs"] = "1/0"
    elif problem == "version":
        data["version"] = "incorrect"
    elif problem == "units":
        data["modules"].pop()
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        workbench.reliability_lesson(tmp_path)


def test_only_canonical_lesson_data_paths_are_readable(tmp_path):
    for name in ("web_outline.json", "examples.py"):
        result = workbench.read_document(workbench.ROOT, f"{workbench.RELIABILITY_DIR}/{name}")
        assert result["text"]
    other = tmp_path / "learning/lessons/L9999-other/web_outline.json"
    other.parent.mkdir(parents=True)
    other.write_text('{"private":"example"}', encoding="utf-8")
    with pytest.raises(ValueError):
        workbench.read_document(tmp_path, other.relative_to(tmp_path).as_posix())


def test_math_and_teaching_interactions_against_canonical_data():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required to check the browser-only teaching algebra")
    data = workbench.reliability_lesson(workbench.ROOT)
    source = data["documents"]["body"]["text"]
    formulas = [a or b for a, b in re.findall(r"\\\((.*?)\\\)|\\\[(.*?)\\\]", source, re.S)]
    script = r"""
const fs = require('fs');
const math = require('./scripts/workbench/math.js');
const demo = require('./scripts/workbench/reliability.js');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
global.window = {SiloMath:math};
const failed = input.formulas.filter(f => math.render(f).includes('math-fallback'));
const sample = math.render(String.raw`\frac{x_i^2}{\sum_{j=1}^n a_j}\leq B^{-T}`);
const matrix = math.render(String.raw`\begin{pmatrix}1&2\\3&4\end{pmatrix}`);
const unsafe = math.render(String.raw`\text{<script>alert(1)</script>}`);
const unknown = math.render(String.raw`\href{javascript:alert(1)}{x}`);
console.log(JSON.stringify({
  failed,
  fraction:sample.includes('<mfrac>'),
  subscript:sample.includes('<msub>'),
  superscript:sample.includes('<msup>'),
  matrix:matrix.includes('<mtable>'),
  escaped:!unsafe.includes('<script>') && unsafe.includes('&lt;script&gt;'),
  fallback:unknown.includes('math-fallback') && !unknown.includes('<a '),
  ordinary:demo.etaCalculation(input.eta),
  transposed:demo.etaCalculation(input.eta,true),
  wrong:demo.etaCalculation(input.eta,true,true),
  prior:input.outline.scenarios.map((_,i)=>demo.previousPoint(input.outline.scenarios,i)),
  objectives:input.outline.scenarios.map(s=>s.objective),
  demoFormula:demo.scenarioHTML(input.outline,4).includes('math-fallback')
}));
"""
    result = subprocess.run(
        [node, "-e", script], input=json.dumps({"eta": data["eta"],
                                              "outline": data["outline"], "formulas": formulas}),
        cwd=workbench.ROOT, capture_output=True, text=True, encoding="utf-8",
        check=True, timeout=15,
    )
    output = json.loads(result.stdout)
    assert len(formulas) >= 20
    assert output["failed"] == []
    assert all(output[key] for key in
               ("fraction", "subscript", "superscript", "matrix", "escaped", "fallback"))
    assert output["ordinary"]["answer"] == ["4", "-1"]
    assert output["transposed"]["answer"] == ["2", "-1"]
    assert output["ordinary"]["residual"] == output["transposed"]["residual"] == ["0", "0"]
    assert output["wrong"]["answer"] == ["-2", "13/2"]
    assert output["wrong"]["residual"] == ["-1/2", "27/2"]
    assert [None if item is None else item["feasible"] for item in output["prior"]] == [
        None, False, False, False, True
    ]
    assert output["objectives"] == ["-1/2", "1", "5/4", "7/5", "1/2"]
    assert output["demoFormula"] is False


def test_current_cards_preserve_the_signed_scope_and_performance_limits():
    catalog = json.loads((workbench.ASSETS / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["project_position"]["title"] == "基础研究工具阶段"
    cards = {item["id"]: item for item in catalog["dimensions"]}
    assert "2000" in cards["performance"]["conclusion"]
    assert "3.503361" in cards["performance"]["conclusion"]
    assert "warm3/5" in cards["performance"]["gap"]
    assert "跨运行时间稳定性" in cards["performance"]["gap"]
    assert "0.3.0a2" in cards["release"]["conclusion"]
    assert "CI pending" in cards["release"]["gap"]
    units = {item["id"]: item for item in catalog["units"]}
    assert [units[name]["status"] for name in "ABCDE"] == [
        "已验收", "已验收", "HOLD", "未启动", "未启动"
    ]
