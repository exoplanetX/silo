import subprocess
import sys


def run(command: list[str]) -> int:
    return subprocess.call(command)


def main() -> int:
    archival_probes = [
        "scripts/research/pricing/probes/pricing_theory_checks_20261011.py",
        "scripts/research/pricing/probes/pricing_signature_checks_20261011.py",
        "scripts/research/pricing/probes/pricing_frontier_state_checks_20261011.py",
        "scripts/research/pricing/probes/verify_boundary_conditions.py",
        "examples/research/pricing_application_probe.py",
    ]
    checks = [
        [sys.executable, "scripts/check_project_structure.py"],
        [sys.executable, "-m", "pytest"],
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src",
            "tests",
            "examples",
            "scripts",
            "--extend-exclude",
            ",".join(archival_probes),
        ],
    ]
    for command in checks:
        code = run(command)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
