"""Read-only local SILO workbench. Run: python scripts/workbench.py --port 8765."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import subprocess
from datetime import datetime, timezone
from fractions import Fraction
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).resolve().parent / "workbench"
PROFILE = ".silo-dos/project_profile.md"
ROOT_DOCS = {
    "README.md", "ROADMAP.md", "CHANGELOG.md", "CITATION.cff", "pyproject.toml",
    "tasks/README.md", "tasks/INDEX.md",
}
DOC_DIRS = {"docs", "notes", "learning", ".silo-dos"}
TASK_DIRS = {"codex", "reports", "phases"}
RELIABILITY_DIR = "learning/lessons/L0016-reliable-solver"
RELIABILITY_DATA = {
    f"{RELIABILITY_DIR}/web_outline.json",
    f"{RELIABILITY_DIR}/examples.py",
}


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def document_path(root: Path, name: str) -> Path:
    """Allow only known text source trees; resolve symlinks before containment checks."""
    parts = Path(name.replace("\\", "/")).parts
    if not parts or any(part in {"..", ".git"} or ":" in part for part in parts):
        raise ValueError("Document path is outside the source allowlist")
    target = (root / Path(*parts)).resolve()
    relative = target.relative_to(root.resolve())
    permitted = (
        relative.as_posix() in ROOT_DOCS
        or relative.as_posix() in RELIABILITY_DATA
        or (relative.parts[0] in DOC_DIRS and target.suffix == ".md")
        or (
            len(relative.parts) > 2
            and relative.parts[0] == "tasks"
            and relative.parts[1] in TASK_DIRS
            and target.suffix == ".md"
        )
        or (
            len(relative.parts) > 2
            and relative.parts[:2] == ("src", "silo")
            and target.suffix == ".py"
        )
        or (relative.parts[0] in {"examples", "tests"} and target.suffix == ".py")
    )
    if not permitted or not target.is_file():
        raise ValueError("Document is missing or outside the source allowlist")
    return target


def read_document(root: Path, name: str) -> dict:
    path = document_path(root, name)
    raw = path.read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError("Document exceeds the 2 MB viewer limit")
    return {
        "path": path.relative_to(root.resolve()).as_posix(),
        "text": raw.decode("utf-8-sig"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "modified": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def source_record(root: Path, name: str, expected: str | None = None) -> dict:
    try:
        doc = read_document(root, name)
        doc.pop("text")
        doc["state"] = "changed" if expected and doc["sha256"] != expected else "available"
        return doc
    except (OSError, ValueError, UnicodeError) as exc:
        return {"path": name, "state": "missing", "error": str(exc)}


def enrich_record(root: Path, item: dict, hashes: dict) -> dict:
    sources = [source_record(root, name, hashes.get(name)) for name in item.get("sources", [])]
    changed = any(source["state"] != "available" for source in sources)
    return {**item, "evidence": sources, "needs_review": changed}


def profile_rows(text: str) -> dict[str, str]:
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 2 and cells[0] not in {"项目", "---"}:
            rows.setdefault(cells[0], cells[1])
    return rows


def phases_from(text: str) -> list[dict]:
    phases = []
    for match in re.finditer(r"^## Phase (\d+): ([^\n]+)\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        status = re.search(r"^Status:\s*(.+)", match[3], re.M)
        goal = re.search(r"^Goal:\s*(.+)", match[3], re.M)
        phases.append({
            "number": int(match[1]), "title": match[2],
            "status": status[1] if status else "未登记",
            "goal": goal[1] if goal else "", "source": "ROADMAP.md",
        })
    return phases


def lessons_from(root: Path) -> list[dict]:
    lessons = []
    for path in sorted((root / "learning/lessons").glob("L*/README.md")):
        name = path.relative_to(root).as_posix()
        try:
            text = read_document(root, name)["text"]
        except (OSError, ValueError, UnicodeError):
            continue
        meta = {}
        if text.startswith("---"):
            for line in text.split("---", 2)[1].splitlines():
                key, sep, value = line.partition(":")
                if sep:
                    meta[key.strip()] = value.strip()
        title = meta.get("title") or next(
            (line[2:] for line in text.splitlines() if line.startswith("# ")), path.parent.name
        )
        lessons.append({
            **meta, "title": title, "path": name,
            "exercises": (path.parent / "exercises.md").is_file(),
            "solutions": (path.parent / "solutions.md").is_file(),
        })
    return lessons


def reliability_lesson(root: Path) -> dict:
    """Read canonical teaching data, never import or execute its example program."""
    documents = {
        name: read_document(root, f"{RELIABILITY_DIR}/{filename}")
        for name, filename in {
            "body": "README.md", "exercises": "exercises.md", "solutions": "solutions.md",
            "outline": "web_outline.json", "examples": "examples.py",
        }.items()
    }
    outline = json.loads(documents["outline"]["text"])
    if outline.get("lesson_id") != "L0016":
        raise ValueError("Unexpected teaching identity")
    for name, filename in {
        "body": "README.md", "exercises": "exercises.md", "solutions": "solutions.md"
    }.items():
        if outline.get(name) != f"{RELIABILITY_DIR}/{filename}":
            raise ValueError("Teaching source paths must match the canonical lesson")
    modules = outline.get("modules", [])
    if [item.get("id") for item in modules] != [f"R{i:02}" for i in range(1, 9)]:
        raise ValueError("The lesson must contain the eight canonical units")
    for item in modules:
        if "### " + item["heading"] not in documents["body"]["text"].splitlines():
            raise ValueError("A teaching unit heading was not found in the canonical body")
        if not all(re.fullmatch(r"L\d{4}", name) for name in item["related_lessons"]):
            raise ValueError("Invalid related lesson identity")
    scenarios = outline.get("scenarios", [])
    if [item.get("id") for item in scenarios] != [f"S{i}" for i in range(5)]:
        raise ValueError("The fixed demonstration requires S0 through S4")
    for item in scenarios:
        values = [
            item.get("rhs"), item.get("y_upper"), item.get("objective"),
            *item.get("point", []), item.get("x_row_upper"), item.get("z_upper"),
        ]
        if len(item.get("point", [])) != 3:
            raise ValueError("The teaching point needs three coordinates")
        for value in values:
            if value is not None:
                if not isinstance(value, str) or not re.fullmatch(r"-?\d+(?:/\d+)?", value):
                    raise ValueError("Teaching numbers must be bounded rational literals")
                if len(value) > 40:
                    raise ValueError("Teaching number is too long")
                try:
                    Fraction(value)
                except ZeroDivisionError as exc:
                    raise ValueError("Teaching denominator must be nonzero") from exc
    exercise_text = documents["exercises"]["text"]
    matrices = []
    for name in ("E₁", "E₂"):
        match = re.search(re.escape(name) + r"=(\[\[[\d,\s+-]+\],\[[\d,\s+-]+\]\])",
                          exercise_text)
        if match is None:
            raise ValueError("Eta matrix is missing from L0016-E03")
        matrix = json.loads(match[1])
        if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
            raise ValueError("Eta demonstration needs 2 by 2 matrices")
        matrices.append(matrix)
    vectors = []
    for name in ("B₂t", "B₂ᵀt"):
        match = re.search(re.escape(name) + r"=\(([\d,−+\-\s]+)\)", exercise_text)
        if match is None:
            raise ValueError("Eta right-hand side is missing from L0016-E03")
        vector = [int(value) for value in match[1].replace("−", "-").split(",")]
        if len(vector) != 2:
            raise ValueError("Eta right-hand side needs two entries")
        vectors.append(vector)
    meta = next(item for item in lessons_from(root) if item.get("lesson_id") == "L0016")
    if outline.get("version") != meta.get("version"):
        raise ValueError("Teaching outline and body versions disagree")
    return {
        "outline": outline, "metadata": meta, "documents": documents,
        "eta": {"e1": matrices[0], "e2": matrices[1],
                "ordinary_rhs": vectors[0], "transpose_rhs": vectors[1],
                "source": f"{RELIABILITY_DIR}/exercises.md"},
    }


def tasks_from(root: Path) -> list[dict]:
    tasks = []
    for path in sorted((root / "tasks/codex").glob("*.md"), reverse=True):
        try:
            text = read_document(root, path.relative_to(root).as_posix())["text"]
        except (OSError, ValueError, UnicodeError):
            continue
        report = root / "tasks/reports" / (path.stem + "_report.md")
        title = next((line[2:] for line in text.splitlines() if line.startswith("# ")), path.stem)
        tasks.append({
            "id": path.stem, "title": title, "date": path.stem[:8],
            "path": path.relative_to(root).as_posix(),
            "report": report.relative_to(root).as_posix() if report.is_file() else None,
        })
    return tasks


def git_info(root: Path) -> dict:
    def run(*args: str) -> str | None:
        try:
            return subprocess.run(
                ["git", *args], cwd=root, capture_output=True, text=True,
                encoding="utf-8", errors="replace", check=True, timeout=4,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

    counts = run("rev-list", "--left-right", "--count", "origin/main...HEAD")
    status = run("-c", "core.quotepath=false", "status", "--short", "--untracked-files=normal")
    head = run("rev-parse", "HEAD")
    branch = run("branch", "--show-current")
    log = run("log", "-6", "--format=%h%x09%cs%x09%s") or ""
    return {
        "head": head, "branch": branch, "working_tree": status,
        "behind": int(counts.split()[0]) if counts else None,
        "ahead": int(counts.split()[1]) if counts else None,
        "remote_basis": "本地缓存 origin/main；未 fetch，不代表即时远端",
        "checked_at": timestamp(),
        "recent": [dict(zip(("hash", "date", "subject"), line.split("\t", 2), strict=True))
                   for line in log.splitlines()],
    }


def build_state(root: Path = ROOT, catalog_path: Path | None = None) -> dict:
    root = root.resolve()
    catalog = json.loads((catalog_path or ASSETS / "catalog.json").read_text(encoding="utf-8"))
    sources = catalog["source_hashes"]
    inventory = [source_record(root, name, digest) for name, digest in sources.items()]
    warnings = [source for source in inventory if source["state"] != "available"]
    try:
        profile = read_document(root, PROFILE)["text"]
    except (OSError, ValueError, UnicodeError):
        profile = ""
    try:
        roadmap = read_document(root, "ROADMAP.md")["text"]
    except (OSError, ValueError, UnicodeError):
        roadmap = ""
    rows = profile_rows(profile)
    version_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version\s*=\s*"([^"]+)"', version_text, re.M)
    return {
        "generated_at": timestamp(), "repository": str(root),
        "version": version[1] if version else "未登记", "profile": rows,
        "snapshot_date": catalog["reviewed_on"],
        "baseline": catalog["baseline"], "assessment_note": catalog["assessment_note"],
        "project_position": catalog.get("project_position", {}),
        "sources": inventory, "warnings": warnings,
        "units": [enrich_record(root, item, sources) for item in catalog["units"]],
        "dimensions": [enrich_record(root, item, sources) for item in catalog["dimensions"]],
        "capabilities": [enrich_record(root, item, sources) for item in catalog["capabilities"]],
        "delivery": [enrich_record(root, item, sources) for item in catalog["delivery"]],
        "boundaries": catalog["boundaries"], "budgets": catalog["budgets"],
        "milestones": catalog["milestones"],
        "phases": phases_from(roadmap), "lessons": lessons_from(root),
        "tasks": tasks_from(root), "git": git_info(root),
    }


def make_handler(root: Path = ROOT, assets: Path = ASSETS) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def send_body(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "SAMEORIGIN")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def json_body(self, status: int, value: dict) -> None:
            self.send_body(status, json.dumps(value, ensure_ascii=False).encode(),
                           "application/json; charset=utf-8")

        def do_GET(self) -> None:
            allowed_hosts = {"127.0.0.1", "localhost"}
            hostname = urlsplit("//" + self.headers.get("Host", "")).hostname
            if hostname not in allowed_hosts:
                self.json_body(403, {"error": "Only loopback hosts are accepted"})
                return
            url = urlsplit(self.path)
            try:
                if url.path == "/api/state":
                    self.json_body(200, build_state(root, assets / "catalog.json"))
                elif url.path == "/api/lesson/L0016":
                    self.json_body(200, reliability_lesson(root))
                elif url.path == "/api/document":
                    name = parse_qs(url.query).get("path", [""])[0]
                    self.json_body(200, read_document(root, name))
                elif url.path in {
                    "/", "/index.html", "/app.js", "/style.css", "/math.js", "/reliability.js"
                }:
                    path = assets / ("index.html" if url.path == "/" else unquote(url.path[1:]))
                    mime = mimetypes.guess_type(path.name)[0] or "text/plain"
                    self.send_body(200, path.read_bytes(), mime + "; charset=utf-8")
                else:
                    self.json_body(404, {"error": "Not found"})
            except (ValueError, OSError, UnicodeError, KeyError) as exc:
                self.json_body(400, {"error": str(exc)})

        def do_POST(self) -> None:
            self.json_body(405, {"error": "Read-only workbench"})

        def log_message(self, format: str, *args: object) -> None:
            pass

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler())
    print(f"SILO workbench: http://127.0.0.1:{server.server_port}", flush=True)
    print("Read-only local preview. Stop with Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
