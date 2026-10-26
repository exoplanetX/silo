"""RR02 scope and immutable identity proof; no solver, old ledger or scheduler."""

import argparse
import hashlib
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = "42892035db426c4739b6c1a7ad9648852d2b1dc8"
ISSUANCE = "6a9b5c0"
FROZEN = "f8f00fd60728e0e9314342a3b4e037cfee50f790"
OLD_RESOURCE = "ec3b18199d66ae614643201344898a8026d1c1f0ca0c7914fe82de983708c23c"
OLD_REPORT = "tasks/reports/20261026-03-01_reliability-io_report.md"
OLD_REPORT_SHA = "47989a6252dfb8ba16bb5dd512afdccefc8b0defcaa5fc391d707ae8da886132"
GOVERNANCE = {
    "AGENTS.md": "2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638",
    "研究主题固定_严重反面案例通告_20261020.md":
        "0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221",
}
ALLOWED = {
    "tests/verification/test_dag_cg_bound_consistency.py", "scripts/sparse_program/resources.py",
    "tests/unit/test_sparse_program_support.py", "tests/unit/test_linux_rss_guard.py",
    ".github/workflows/quality.yml", "scripts/reliability/r4_closure.py",
    "scripts/reliability/artifacts.py", "scripts/reliability/check_installed.py",
    "scripts/reliability/external.py", "scripts/reliability/parse_external.py",
    "tests/unit/test_reliability_tools.py", "README.md", "docs/installation.md",
    "docs/research_baseline.md", "scripts/workbench/catalog.json", "tests/unit/test_workbench.py",
    ".silo-dos/project_profile.md", ".silo-dos/technical_route.md", ".silo-dos/decision_log.md",
    ".silo-dos/standing_approval_profile.md", "learning/lessons/L0016-reliable-solver/README.md",
    "learning/lessons/L0016-reliable-solver/exercises.md",
    "learning/lessons/L0016-reliable-solver/solutions.md", "learning/CATALOG.md",
    "tasks/reports/20261026-03-02_reliability-io_report.md", "tasks/INDEX.md",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def strict_lf(data):
    normalized = data.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise ValueError("bare CR is not an approved LF transport change")
    return normalized


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def tracked_snapshot(revision, *paths):
    archive = git("archive", "--format=tar", revision, *paths)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as reader:
        return {member.name: reader.extractfile(member).read()
                for member in reader.getmembers() if member.isfile()}


def local_evidence_reuse():
    """Read-only preservation/reuse proof; never execute a historical driver."""
    old = ROOT / "outputs/reliability_io_20261026"
    start = json.loads((ROOT / "outputs/reliability_io_r4_20261026/start.json")
                       .read_text(encoding="utf-8"))
    for relative, wanted in start["old_outputs"].items():
        assert sha(ROOT / relative) == wanted, relative
    built = json.loads((old / "dist1/manifest.json").read_text(encoding="utf-8"))
    current = {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / "src/silo").rglob("*.py")}
    assert current == built["source"]
    for name, wanted in built["artifacts"].items():
        assert sha(old / "dist1" / name) == wanted, name
    installed = json.loads((old / "installed1/summary.json").read_text(encoding="utf-8"))
    assert installed["passed"] and installed["environments"] == 4
    for item in installed["records"]:
        report = old / "installed1" / item["report"]
        assert sha(report) == item["sha"]
        actual = json.loads(report.read_text(encoding="utf-8"))
        assert actual["passed"] and actual["public_requests"] == 24
        assert actual["artifact_sha256"] == built["artifacts"][item["artifact"]]
        assert actual["direct_url"]["archive_info"]["hashes"]["sha256"] == (
            actual["artifact_sha256"])
        for info in actual["loaded_modules"].values():
            assert sha(info["path"]) == info["sha256"]
    checker = sha(ROOT / "scripts/reliability/check_installed.py")
    return {"original_output_files_unchanged": len(start["old_outputs"]),
            "original_installed_environments": 4, "original_public_requests": 96,
            "artifact_sha256": built["artifacts"], "current_checker_sha256": checker,
            "original_checker_sha256": installed["checker_sha"],
            "eligible": checker == installed["checker_sha"],
            "old_local_seconds": start["old_costs"]["local_seconds"]}


def verify():
    expected = tracked_snapshot(PRODUCTION, "src/silo", "pyproject.toml", "CITATION.cff")
    production_names = {p.relative_to(ROOT).as_posix() for p in (ROOT / "src/silo").rglob("*.py")}
    assert production_names == {p for p in expected if p.startswith("src/")}
    origins = {}
    source_lf = {}
    for relative, old in expected.items():
        actual = (ROOT / relative).read_bytes()
        assert strict_lf(actual) == strict_lf(old), relative
        origins[relative] = {"git_raw_sha256": digest(old), "raw_sha256": digest(actual),
                             "lf_sha256": digest(strict_lf(actual)),
                             "transport": "identical" if actual == old else "strict CRLF/LF"}
        if relative.startswith("src/"):
            source_lf[relative] = digest(strict_lf(actual))
    fixture = ROOT / "tests/fixtures/reliability_20261026"
    manifest = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))
    assert sha(fixture / "manifest.json") == (
        "2fa296f567a96af88796bf0c392830c29740cfc44ea2cd290880a9d03e5a4291")
    for relative, wanted in manifest["files"].items():
        assert sha(ROOT / relative) == wanted, relative
    assert sha(ROOT / OLD_REPORT) == OLD_REPORT_SHA
    assert not git("diff", "315fecb", FROZEN, "--", "src")
    subprocess.run(["git", "merge-base", "--is-ancestor", FROZEN, PRODUCTION],
                   cwd=ROOT, check=True)
    old = git("show", PRODUCTION + ":scripts/sparse_program/resources.py")
    assert digest(old) == OLD_RESOURCE
    changes = set(git("diff", "--name-only", ISSUANCE).decode("utf-8").splitlines())
    changes.update(filter(None, git("ls-files", "--others", "--exclude-standard", "-z")
                          .decode("utf-8").split("\0")))
    unexpected = changes - ALLOWED - GOVERNANCE.keys()
    assert not unexpected, sorted(unexpected)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        # Local governance overlays were explicitly excluded from the public branch.
        # CI checks the committed AGENTS identity; the local receipt checks both overlays.
        assert (ROOT / "AGENTS.md").read_bytes() == git("show", ISSUANCE + ":AGENTS.md")
        governance = {"scope": "committed CI rules", "AGENTS_sha256": sha(ROOT / "AGENTS.md")}
        reuse = {"scope": "local reuse was checked separately; CI runs all fresh installs"}
    else:
        for relative, wanted in GOVERNANCE.items():
            assert sha(ROOT / relative) == wanted, relative
        governance = {"scope": "local protected overlays", **GOVERNANCE}
        reuse = local_evidence_reuse()
    return {
        "passed": True, "production_commit": PRODUCTION,
        "current_commit": git("rev-parse", "HEAD").decode().strip(),
        "issuance_commit": git("rev-parse", ISSUANCE).decode().strip(),
        "source_origins": origins,
        "source_lf_sha256": digest(json.dumps(source_lf, sort_keys=True,
                                              separators=(",", ":")).encode()),
        "frozen_manifest_sha256": sha(fixture / "manifest.json"),
        "old_report_sha256": OLD_REPORT_SHA,
        "resources": {"old_sha256": OLD_RESOURCE,
                      "new_sha256": sha(ROOT / "scripts/sparse_program/resources.py"),
                      "identity_rule": "new tool only; old driver maps/receipts remain immutable"},
        "governance": governance, "allowed_changes": sorted(changes - GOVERNANCE.keys()),
        "local_evidence_reuse": reuse,
        "new_solver_requests": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = verify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in value.items() if k != "source_origins"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
