"""Standard-library-only artifact/path gates; no solver/build/install execution."""

import ast
import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def delivery(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from sparse_program import delivery

    return delivery


def project():
    return {
        "project": {
            "name": "silo-solver",
            "version": "0.3.0a1",
            "requires-python": ">=3.10",
            "dependencies": ["numpy>=1.24"],
            "optional-dependencies": {"sparse": ["scipy==1.16.3; python_version >= '3.11'"]},
        }
    }


def metadata():
    return (
        b"Metadata-Version: 2.4\nName: silo-solver\nVersion: 0.3.0a1\nRequires-Python: >=3.10\n"
        b"Requires-Dist: numpy>=1.24\nProvides-Extra: sparse\n"
        b'Requires-Dist: scipy==1.16.3; python_version >= "3.11" and extra == "sparse"\n\n'
    )


def test_delivery_refuses_before_sp3_go_version_or_clean_commit(monkeypatch):
    module = delivery(monkeypatch)
    go = [{"kind": "stage_gate", "stage": "SP3", "decision": "GO"}]
    citation = 'version: "0.3.0a1"\n'
    with pytest.raises(RuntimeError, match="SP3 GO"):
        module.validate_activation([], project(), "0.3.0a1", citation, [])
    with pytest.raises(RuntimeError, match="metadata/runtime"):
        module.validate_activation(go, project(), "0.2.0a2", citation, [])
    with pytest.raises(RuntimeError, match="CITATION"):
        module.validate_activation(go, project(), "0.3.0a1", 'version: "0.2.0a2"', [])
    with pytest.raises(RuntimeError, match="clean committed"):
        module.validate_activation(go, project(), "0.3.0a1", citation, ["src/silo/solver.py"])
    module.validate_activation(go, project(), "0.3.0a1", citation, ["AGENTS.md"])
    assert len(module.KEYS) == 8


@pytest.mark.parametrize("name", ["../escape.py", "/absolute.py", "C:/escape.py", "a\\b.py"])
def test_archive_member_cannot_escape_destination(monkeypatch, name):
    with pytest.raises(ValueError, match="Unsafe"):
        delivery(monkeypatch).safe_member(name)


def test_only_crlf_transport_can_change_artifact_bytes(monkeypatch):
    module = delivery(monkeypatch)
    assert module.equivalent_text(b"x=1\n", b"x=1\n")["comparison"] == "raw_equal"
    record = module.equivalent_text(b"x=1\n", b"x=1\r\n")
    assert record["comparison"] == "CRLF_to_LF_only"
    assert record["source_sha256"] != record["artifact_sha256"]
    for invalid in (b"x=2\n", b"x=1\r", b"x=1\r\r\n", b"x=1"):
        with pytest.raises(ValueError, match="beyond"):
            module.equivalent_text(b"x=1\n", invalid)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_artifact_module_inventory_metadata_and_pyproject(monkeypatch, tmp_path, kind):
    module = delivery(monkeypatch)
    snapshot = tmp_path / "snapshot"
    (snapshot / "src/silo").mkdir(parents=True)
    files = {"silo/__init__.py": b'__version__="0.3.0a1"\n', "silo/solver.py": b"VALUE = 1\n"}
    for name, value in files.items():
        (snapshot / "src" / name).write_bytes(value)
    pyproject = b'[project]\nname="silo-solver"\nversion="0.3.0a1"\n'
    (snapshot / "pyproject.toml").write_bytes(pyproject)
    artifact = tmp_path / ("candidate.whl" if kind == "wheel" else "candidate.tar.gz")

    def write(changed=False):
        payload = {**files, "silo/solver.py": b"VALUE = 2\n" if changed else b"VALUE = 1\r\n"}
        if kind == "wheel":
            with zipfile.ZipFile(artifact, "w") as archive:
                for name, value in payload.items():
                    archive.writestr(name, value)
                archive.writestr("silo_solver-0.3.0a1.dist-info/METADATA", metadata())
        else:
            payload = {"src/" + name: value for name, value in payload.items()}
            payload.update({"pyproject.toml": pyproject, "PKG-INFO": metadata()})
            with tarfile.open(artifact, "w:gz") as archive:
                for name, value in payload.items():
                    info = tarfile.TarInfo("silo_solver-0.3.0a1/" + name)
                    info.size = len(value)
                    archive.addfile(info, io.BytesIO(value))

    write()
    record = module.audit_artifact(artifact, kind, snapshot, project())
    assert record["module_count"] == 2 and record["metadata_check"]["version"] == "0.3.0a1"
    assert record["module_checks"]["silo/solver.py"]["comparison"] == "CRLF_to_LF_only"
    write(changed=True)
    with pytest.raises(ValueError, match="beyond"):
        module.audit_artifact(artifact, kind, snapshot, project())


def test_installed_checker_top_level_dependencies_are_standard_library():
    import sys

    tree = ast.parse((ROOT / "scripts/sparse_program/check_installed.py").read_text())
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module.split(".")[0])
    assert imported <= sys.stdlib_module_names
    assert not imported.intersection({"silo", "scipy", "numpy"})


def test_same_archive_provenance_recheck_requires_unique_unconsumed_human_authority(monkeypatch):
    module = delivery(monkeypatch)
    authorization = {
        "kind": "human_delivery_provenance_recheck",
        "prior_summary_sha256": "a" * 64,
        "sha256": "b" * 64,
    }
    for events in (
        [],
        [authorization, authorization],
        [{**authorization, "prior_summary_sha256": "c"}],
    ):
        with pytest.raises(RuntimeError, match="unique direct human authority"):
            module._provenance_recheck_authority(events, "a" * 64)
    assert module._provenance_recheck_authority([authorization], "a" * 64) == "b" * 64
    consumed = {"kind": "delivery_provenance_recheck_started", "authority_sha256": "b" * 64}
    with pytest.raises(RuntimeError, match="already consumed"):
        module._provenance_recheck_authority([authorization, consumed], "a" * 64)


def test_existing_delivery_cannot_be_rebuilt_by_omitting_reuse_flag(monkeypatch):
    module = delivery(monkeypatch)
    module.validate_delivery_route([], None)
    module.validate_delivery_route(["prior/summary.json"], "prior")
    with pytest.raises(RuntimeError, match="authorized same-SHA reuse"):
        module.validate_delivery_route(["prior/summary.json"], None)


@pytest.mark.parametrize("checker_passes", [True, False])
def test_candidate_archive_uses_seeded_pip_and_provenance_failure_is_not_retried(
    monkeypatch, tmp_path, checker_passes
):
    module = delivery(monkeypatch)
    artifact = tmp_path / "candidate.whl"
    artifact.write_bytes(b"immutable candidate archive")
    checker = tmp_path / "checker.py"
    checker.write_text("# read-only checker", encoding="utf-8")
    commands = []

    def fake_run(argv, cwd, folder, label, timeout):
        commands.append((label, list(map(str, argv))))
        if label.endswith("_check"):
            Path(argv[-1]).write_text(
                json.dumps({"status": "passed" if checker_passes else "failed", "provenance": {}}),
                encoding="utf-8",
            )
            return {"returncode": 0 if checker_passes else 1}
        return {"returncode": 0}

    monkeypatch.setattr(module, "_run", fake_run)
    result = module._install_combination(
        "3.13-sparse-wheel",
        {"path": str(artifact), "sha256": module.ledger.sha(artifact)},
        "sparse",
        "3.13",
        tmp_path / "outside",
        tmp_path,
        checker,
    )
    jobs = {label.rsplit("_", 1)[-1]: argv for label, argv in commands}
    assert jobs["seed-pip"][1:] == ["-I", "-m", "ensurepip", "--upgrade"]
    assert str(artifact) not in jobs["install-runtime"]
    assert jobs["install-artifact"][1:5] == ["-I", "-m", "pip", "install"]
    assert jobs["install-artifact"][-1] == str(artifact)
    assert "--no-deps" in jobs["install-artifact"]
    assert result["pass"] is checker_passes and len(result["attempts"]) == 1
