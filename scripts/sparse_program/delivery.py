"""Guarded, source-pinned local artifacts and eight fresh installation checks.

The public program CLI supplies the sole ledger/accounting parent. This module
never calls ledger.command, publishes artifacts, or reuses an installation.
"""

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from uuid import uuid4

from . import ledger
from .resources import kill_tree

CANDIDATE = "0.3.0a1"
NUMPY = "2.3.5"
SCIPY = "1.16.3"
UV = Path(
    "C:/Users/xuning/AppData/Local/Microsoft/WinGet/Packages/"
    "astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe/uv.EXE"
)
PYTHON_311 = Path(
    "C:/Users/xuning/AppData/Roaming/uv/python/cpython-3.11-windows-x86_64-none/python.exe"
)
NOTICE = "研究主题固定_严重反面案例通告_20261020.md"
GOVERNANCE = {
    "AGENTS.md": "2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638",
    NOTICE: "0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221",
}
KEYS = {
    f"{python}-{mode}-{kind}"
    for python in ("3.11", "3.13")
    for mode in ("dense", "sparse")
    for kind in ("wheel", "sdist")
}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def equivalent_text(expected, actual):
    """Accept only exact bytes or the explicitly recorded CRLF/LF transport rule."""
    record = {"source_sha256": sha_bytes(expected), "artifact_sha256": sha_bytes(actual)}
    if expected == actual:
        return {**record, "comparison": "raw_equal"}
    expected.decode("utf-8")
    actual.decode("utf-8")
    source_lf, artifact_lf = expected.replace(b"\r\n", b"\n"), actual.replace(b"\r\n", b"\n")
    if b"\r" in source_lf or b"\r" in artifact_lf or source_lf != artifact_lf:
        raise ValueError("Artifact bytes differ beyond CRLF/LF transport")
    return {**record, "comparison": "CRLF_to_LF_only", "normalized_sha256": sha_bytes(source_lf)}


def safe_member(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe archive member {name!r}")
    return path


def _git(*args):
    return subprocess.check_output(["git", *args], cwd=ledger.ROOT)


def _status_paths(raw):
    records = raw.decode("utf-8").split("\0")
    paths, i = [], 0
    while i < len(records):
        record = records[i]
        i += 1
        if not record:
            continue
        status, path = record[:2], record[3:]
        paths.append(path)
        if "R" in status or "C" in status:
            # Rename source is a second NUL record in porcelain -z.
            paths.append(records[i])
            i += 1
    return paths


def _literal_version(source):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("No literal runtime version in committed package")


def validate_activation(events, project, runtime_version, citation, dirty_paths):
    """Pure gate, also tested without installing/building/importing SILO."""
    if not any(
        e.get("kind") == "stage_gate" and e.get("stage") == "SP3" and e.get("decision") == "GO"
        for e in events
    ):
        raise RuntimeError("Installation requires recorded SP3 GO")
    if project["project"]["version"] != CANDIDATE or runtime_version != CANDIDATE:
        raise RuntimeError("Installation requires committed candidate0.3.0a1 metadata/runtime")
    if not re.search(r"^version:\s*[\"\']?0\.3\.0a1[\"\']?\s*$", citation, re.MULTILINE):
        raise RuntimeError("Committed CITATION must identify0.3.0a1")
    if set(dirty_paths) - GOVERNANCE.keys():
        raise RuntimeError(
            "Installation requires clean committed source (accepted governance only)"
        )


def ready():
    if not os.environ.get("SILO_SPARSE_ACCOUNT_PARENT"):
        raise RuntimeError("Invoke install-checks through the single budgeted program CLI")
    import tomllib

    project_bytes = _git("show", "HEAD:pyproject.toml")
    project = tomllib.loads(project_bytes.decode("utf-8"))
    runtime = _literal_version(_git("show", "HEAD:src/silo/__init__.py").decode("utf-8"))
    citation = _git("show", "HEAD:CITATION.cff").decode("utf-8")
    dirty = _status_paths(_git("status", "--porcelain=v1", "-z", "--untracked-files=all"))
    validate_activation(ledger.history(), project, runtime, citation, dirty)
    for path in dirty:
        if ledger.sha(ledger.ROOT / path) != GOVERNANCE[path]:
            raise RuntimeError(f"Accepted governance bytes changed: {path}")
    if not UV.is_file() or not PYTHON_311.is_file():
        raise RuntimeError("Locked Windows UV/Python3.11 runtime is unavailable")
    return {
        "commit": _git("rev-parse", "HEAD").decode().strip(),
        "project": project,
        "pyproject_sha256": sha_bytes(project_bytes),
        "accepted_governance": dirty,
    }


def _run(argv, cwd, folder, label, timeout):
    log = folder / (label + ".log")
    record = {
        "argv": list(map(str, argv)),
        "cwd": str(cwd),
        "started_at": ledger.utc(),
        "log": str(log),
        "started": True,
        "completed": False,
    }
    start = time.perf_counter()
    with log.open("w", encoding="utf-8") as stream:
        try:
            process = subprocess.Popen(
                record["argv"], cwd=cwd, stdout=stream, stderr=subprocess.STDOUT
            )
            record["pid"] = process.pid
            try:
                record["returncode"] = process.wait(timeout=timeout)
                record["completed"] = True
            except subprocess.TimeoutExpired:
                kill_tree(process)
                record.update(returncode=124, guard_reason="harness_timeout")
        except OSError as exc:
            stream.write(f"{type(exc).__name__}: {exc}\n")
            record.update(returncode=127, failure="process_start")
    record.update(
        ended_at=ledger.utc(),
        elapsed_seconds=time.perf_counter() - start,
        log_sha256=ledger.sha(log),
    )
    (folder / (label + ".command.json")).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def _must_run(commands, argv, cwd, folder, label, timeout):
    record = _run(argv, cwd, folder, label, timeout)
    commands.append(record)
    if record["returncode"] != 0:
        raise RuntimeError(f"{label} failed, see {record['log']}")
    return record


def _canonical_requirement(value):
    return re.sub(r"[\s()]", "", value).replace("'", '"').lower()


def _metadata_check(raw, project):
    metadata = BytesParser().parsebytes(raw)
    declared = project["project"]
    if metadata["Name"] != declared["name"] or metadata["Version"] != CANDIDATE:
        raise ValueError("Artifact distribution name/version does not match snapshot")
    if metadata["Requires-Python"] != declared["requires-python"]:
        raise ValueError("Artifact Python requirement differs from snapshot pyproject")
    extras = declared.get("optional-dependencies", {})
    if set(metadata.get_all("Provides-Extra", [])) != set(extras):
        raise ValueError("Artifact extras differ from snapshot pyproject")
    expected = [_canonical_requirement(d) for d in declared.get("dependencies", [])]
    for extra, dependencies in extras.items():
        for dependency in dependencies:
            specification, _, marker = dependency.partition(";")
            combined = f'{specification};{marker + " and " if marker else ""}extra=="{extra}"'
            expected.append(_canonical_requirement(combined))
    actual = list(map(_canonical_requirement, metadata.get_all("Requires-Dist", [])))
    if sorted(expected) != sorted(actual):
        raise ValueError(f"Artifact dependencies differ from pyproject: {actual} vs {expected}")
    return {
        "name": metadata["Name"],
        "version": metadata["Version"],
        "requires_python": metadata["Requires-Python"],
        "requires_dist": metadata.get_all("Requires-Dist", []),
        "pyproject_mapping": "distribution metadata and all base/extra requirements matched",
    }


def audit_artifact(path, kind, snapshot, project):
    modules = {
        p.relative_to(snapshot / "src").as_posix(): p.read_bytes()
        for p in (snapshot / "src/silo").rglob("*.py")
    }
    if kind == "wheel":
        with zipfile.ZipFile(path) as archive:
            if len(archive.namelist()) != len(set(archive.namelist())):
                raise ValueError("Duplicate wheel members")
            contents = {
                str(safe_member(name)): archive.read(name)
                for name in archive.namelist()
                if not name.endswith("/")
            }
        actual = {name for name in contents if name.startswith("silo/") and name.endswith(".py")}
        metadata = [name for name in contents if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise ValueError("Wheel metadata identity is ambiguous")
        raw_metadata = contents[metadata[0]]
        pyproject = {
            "present_in_wheel": False,
            "snapshot_sha256": ledger.sha(snapshot / "pyproject.toml"),
            "mapping": "METADATA checked against committed pyproject; wheels omit source pyproject",
        }
    elif kind == "sdist":
        with tarfile.open(path, "r:gz") as archive:
            members = [m for m in archive.getmembers() if m.isfile()]
            names = [str(safe_member(m.name)) for m in members]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate sdist members")
            roots = {PurePosixPath(name).parts[0] for name in names}
            if len(roots) != 1:
                raise ValueError("Ambiguous sdist root")
            contents = {
                str(PurePosixPath(name).relative_to(next(iter(roots)))): archive.extractfile(
                    member
                ).read()
                for name, member in zip(names, members, strict=True)
            }
        actual = {
            name.removeprefix("src/")
            for name in contents
            if name.startswith("src/silo/") and name.endswith(".py")
        }
        raw_metadata = contents["PKG-INFO"]
        pyproject = equivalent_text(
            (snapshot / "pyproject.toml").read_bytes(), contents["pyproject.toml"]
        )
        contents = {
            name.removeprefix("src/") if name.startswith("src/") else name: raw
            for name, raw in contents.items()
        }
    else:
        raise ValueError("Unknown artifact kind")
    if actual != set(modules):
        raise ValueError(
            f"Artifact module inventory mismatch: missing{set(modules) - actual}, "
            f"extra{actual - set(modules)}"
        )
    checked = {name: equivalent_text(raw, contents[name]) for name, raw in modules.items()}
    return {
        "path": str(path),
        "sha256": ledger.sha(path),
        "module_count": len(checked),
        "module_checks": checked,
        "pyproject": pyproject,
        "metadata_check": _metadata_check(raw_metadata, project),
    }


def environmental_failure(record):
    if record.get("guard_reason") == "harness_timeout":
        return True
    text = Path(record["log"]).read_text(encoding="utf-8", errors="replace").lower()
    return any(
        token in text
        for token in (
            "failed to download",
            "connection reset",
            "connection refused",
            "connection timed out",
            "certificate verify failed",
            "dns error",
            "temporary failure in name resolution",
            "failed to acquire lock",
            "os error 32",
            "sharing violation",
        )
    )


def _install_combination(key, artifact, mode, requested_python, outside, folder, checker):
    record = {
        "key": key,
        "python_requested": requested_python,
        "mode": mode,
        "artifact_kind": "wheel" if key.endswith("wheel") else "sdist",
        "artifact_sha256": artifact["sha256"],
        "attempts": [],
        "pass": False,
    }
    base = PYTHON_311 if requested_python == "3.11" else ledger.ROOT / ".venv/Scripts/python.exe"
    for attempt_number in (1, 2):
        attempt_path = outside / key / f"attempt{attempt_number}"
        attempt_path.mkdir(parents=True, exist_ok=False)
        env = attempt_path / "venv"
        interpreter = env / "Scripts/python.exe"
        attempt = {
            "number": attempt_number,
            "fresh_environment": str(env),
            "commands": [],
            "pass": False,
        }
        record["attempts"].append(attempt)
        if ledger.sha(artifact["path"]) != artifact["sha256"]:
            raise RuntimeError("Artifact changed before installation/retry")
        jobs = [
            ("venv", [UV, "venv", "--python", base, env], 60),
            (
                "version",
                [
                    interpreter,
                    "-I",
                    "-c",
                    "import platform,sys;print(platform.python_version());"
                    "assert sys.version_info[:2]=="
                    + repr(tuple(map(int, requested_python.split(".")))),
                ],
                20,
            ),
            (
                "seed-pip",
                [interpreter, "-I", "-m", "ensurepip", "--upgrade"],
                60,
            ),
            (
                "install-runtime",
                [
                    UV,
                    "--native-tls",
                    "pip",
                    "install",
                    "--python",
                    interpreter,
                    "--index-url",
                    "https://pypi.org/simple",
                    "--no-deps",
                    f"numpy=={NUMPY}",
                    *([f"scipy=={SCIPY}"] if mode == "sparse" else []),
                ],
                120,
            ),
            (
                "install-artifact",
                [
                    interpreter,
                    "-I",
                    "-m",
                    "pip",
                    "install",
                    "--index-url",
                    "https://pypi.org/simple",
                    "--no-deps",
                    "--no-cache-dir",
                    artifact["path"],
                ],
                120,
            ),
        ]
        failure = None
        for label, argv, seconds in jobs:
            command = _run(argv, attempt_path, folder, f"{key}_{attempt_number}_{label}", seconds)
            attempt["commands"].append(command)
            if command["returncode"] != 0:
                failure = command
                break
        if failure is None:
            local_checker = attempt_path / "check_installed.py"
            shutil.copyfile(checker, local_checker)
            report = folder / f"{key}_{attempt_number}_installed.json"
            command = _run(
                [
                    interpreter,
                    "-I",
                    local_checker,
                    "--source-root",
                    ledger.ROOT,
                    "--artifact",
                    artifact["path"],
                    "--mode",
                    mode,
                    "--python-minor",
                    requested_python,
                    "--report",
                    report,
                ],
                attempt_path,
                folder,
                f"{key}_{attempt_number}_check",
                180,
            )
            attempt["commands"].append(command)
            if report.exists():
                attempt.update(
                    check_report_path=str(report), check_report_sha256=ledger.sha(report)
                )
            if command["returncode"] == 0 and report.exists():
                checked = json.loads(report.read_text())
                if checked.get("status") == "passed":
                    attempt["actual_environment"] = checked["provenance"]
                    attempt["pass"] = record["pass"] = True
                    record.update(
                        check_report_path=str(report), check_report_sha256=ledger.sha(report)
                    )
            # Solver/provenance/assertion failures are never environmental retries.
            break
        attempt["environmental_failure"] = environmental_failure(failure)
        if attempt_number == 2 or not attempt["environmental_failure"]:
            break
        attempt["retry_reason"] = (
            "same artifact SHA, fresh environment, network/lock process failure"
        )
    return record


def _provenance_recheck_authority(events, previous_sha256):
    authorized = [
        event
        for event in events
        if event["kind"] == "human_delivery_provenance_recheck"
        and event.get("prior_summary_sha256") == previous_sha256
    ]
    if len(authorized) != 1:
        raise RuntimeError("Same-archive provenance recheck requires unique direct human authority")
    authority = authorized[0]["sha256"]
    if any(
        event["kind"] == "delivery_provenance_recheck_started"
        and event.get("authority_sha256") == authority
        for event in events
    ):
        raise RuntimeError("Same-archive provenance recheck authority is already consumed")
    return authority


def _reuse_delivery(previous, folder, activation):
    previous = Path(previous).resolve()
    if not previous.is_relative_to((ledger.OUT / "delivery").resolve()):
        raise ValueError("Reused delivery must stay inside the original program delivery root")
    path = previous / "summary.json"
    authority = _provenance_recheck_authority(ledger.history(), ledger.sha(path))
    old = json.loads(path.read_text(encoding="utf-8"))
    source = old["source"]
    if old["candidate"] != CANDIDATE or source["project"] != activation["project"]:
        raise ValueError("Reused candidate/project metadata differs from current committed source")
    snapshot = Path(source["snapshot"])
    if not snapshot.resolve().is_relative_to(previous):
        raise ValueError("Reused snapshot escaped its original delivery")
    current = ledger.identity()["source"]
    if source["source_sha256"] != ledger.digest(source["files"]):
        raise ValueError("Reused source digest differs from its module map")
    if set(current) != set(source["files"]):
        raise ValueError("Reused source module inventory differs")
    for name, digest in source["files"].items():
        if ledger.sha(snapshot / name) != digest:
            raise ValueError("Reused snapshot bytes changed")
        equivalent_text((snapshot / name).read_bytes(), (ledger.ROOT / name).read_bytes())
    checker = snapshot / "scripts/sparse_program/check_installed.py"
    if (
        ledger.sha(checker) != old["checker_sha256"]
        or ledger.sha(ledger.ROOT / "scripts/sparse_program/check_installed.py")
        != old["checker_sha256"]
    ):
        raise ValueError("Reused installation checker changed")
    for kind in ("wheel", "sdist"):
        artifact = old["artifacts"][kind]
        if audit_artifact(Path(artifact["path"]), kind, snapshot, source["project"]) != artifact:
            raise ValueError("Reused artifact bytes or metadata changed")
    archive = previous / "source.zip"
    if ledger.sha(archive) != source["archive_sha256"]:
        raise ValueError("Reused committed archive changed")
    shutil.copyfile(archive, folder / "source.zip")
    ledger.append(
        "delivery_provenance_recheck_started",
        authority_sha256=authority,
        prior_summary_sha256=ledger.sha(path),
        candidate=CANDIDATE,
        artifacts={kind: old["artifacts"][kind]["sha256"] for kind in ("wheel", "sdist")},
    )
    return (
        source,
        old["artifacts"],
        {
            "path": str(path),
            "sha256": ledger.sha(path),
            "authority_sha256": authority,
        },
    )


def validate_delivery_route(previous_summaries, reuse_delivery):
    if previous_summaries and not reuse_delivery:
        raise RuntimeError("Existing candidate delivery requires authorized same-SHA reuse")


def execute(args):
    validate_delivery_route(
        list((ledger.OUT / "delivery").glob("*/summary.json")),
        getattr(args, "reuse_delivery", None),
    )
    folder = ledger.OUT / "delivery" / str(uuid4())
    folder.mkdir(parents=True)
    summary = {
        "schema_version": 1,
        "candidate": CANDIDATE,
        "source": {},
        "artifacts": {},
        "installations": [],
        "commands": [],
        "all_pass": False,
        "started_at": ledger.utc(),
        "execution_scripts": ledger.identity()["scripts"],
    }
    try:
        if args.candidate != CANDIDATE:
            raise ValueError("Only the issued candidate0.3.0a1 is authorized")
        activation = ready()
        if getattr(args, "reuse_delivery", None):
            source, artifacts, reused = _reuse_delivery(args.reuse_delivery, folder, activation)
            summary.update(source=source, artifacts=artifacts, reused_from=reused)
            return _finish_installations(folder, summary)
        source = activation
        summary["source"] = source
        archive_path = folder / "source.zip"
        _must_run(
            summary["commands"],
            ["git", "archive", "--format=zip", "--output", archive_path, source["commit"]],
            ledger.ROOT,
            folder,
            "archive",
            60,
        )
        snapshot = folder / "snapshot"
        snapshot.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                safe_member(info.filename)
            archive.extractall(snapshot)
        source["archive_sha256"] = ledger.sha(archive_path)
        source["snapshot"] = str(snapshot)
        source["files"] = {
            p.relative_to(snapshot).as_posix(): ledger.sha(p)
            for p in [*sorted((snapshot / "src/silo").rglob("*.py")), snapshot / "pyproject.toml"]
        }
        source["source_sha256"] = ledger.digest(source["files"])
        dist = folder / "dist"
        dist.mkdir()
        _must_run(summary["commands"], [UV, "--version"], folder, folder, "uv_version", 20)
        _must_run(
            summary["commands"],
            [
                UV,
                "--native-tls",
                "build",
                "--sdist",
                "--wheel",
                "--python",
                sys.executable,
                "--out-dir",
                dist,
                snapshot,
            ],
            folder,
            folder,
            "build",
            180,
        )
        wheels, sdists = list(dist.glob("*.whl")), list(dist.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise RuntimeError("Build must produce exactly one wheel and one sdist")
        for kind, path in (("wheel", wheels[0]), ("sdist", sdists[0])):
            summary["artifacts"][kind] = audit_artifact(path, kind, snapshot, source["project"])
        return _finish_installations(folder, summary)
    except (RuntimeError, ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        summary["failure"] = f"{type(exc).__name__}: {exc}"
    finally:
        summary["ended_at"] = ledger.utc()
        (folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {"delivery_summary": str(folder / "summary.json"), "all_pass": summary["all_pass"]}
            )
        )
    return 1


def _finish_installations(folder, summary):
    source = summary["source"]
    outside = Path(tempfile.mkdtemp(prefix="silo-sparse-install-"))
    if outside.resolve().is_relative_to(ledger.ROOT.resolve()):
        raise RuntimeError("Installation workspace must be outside the source checkout")
    summary["outside_workspace"] = str(outside)
    checker = Path(source["snapshot"]) / "scripts/sparse_program/check_installed.py"
    summary["checker_sha256"] = ledger.sha(checker)
    for requested_python in ("3.11", "3.13"):
        for mode in ("dense", "sparse"):
            for kind in ("wheel", "sdist"):
                key = f"{requested_python}-{mode}-{kind}"
                record = _install_combination(
                    key,
                    summary["artifacts"][kind],
                    mode,
                    requested_python,
                    outside,
                    folder,
                    checker,
                )
                summary["installations"].append(record)
                (folder / "progress.json").write_text(
                    json.dumps(summary, indent=2), encoding="utf-8"
                )
                print(json.dumps({"installation": key, "pass": record["pass"]}), flush=True)
    summary["all_pass"] = (
        len(summary["installations"]) == 8
        and {r["key"] for r in summary["installations"]} == KEYS
        and all(r["pass"] for r in summary["installations"])
    )
    return 0 if summary["all_pass"] else 1
