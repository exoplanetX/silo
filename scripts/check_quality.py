import subprocess
import sys


def run(command: list[str]) -> int:
    return subprocess.call(command)


def main() -> int:
    checks = [
        [sys.executable, "-m", "pytest"],
        [sys.executable, "-m", "ruff", "check", "src", "tests", "examples", "scripts"],
    ]
    for command in checks:
        code = run(command)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
