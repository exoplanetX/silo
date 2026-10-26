"""One 24-file external parsing group in a fresh isolated highspy environment."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .accept import load, roundtrip
from .exact import equivalent
from .runtime import ROOT, environment, sha, write_new


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=False)
    data, _ = load()
    models = {p["name"]: p for p in data["models"]}
    requests = []
    for name in data["external_ids"]:
        for fmt in ("mps", "lp"):
            _, text = roundtrip(models[name], fmt)
            path = output.parent / f"{name}.{fmt}"
            path.write_text(text, encoding="utf-8")
            requests.append({"id": name, "format": fmt, "path": str(path), "sha": sha(path)})
    requests_path = output.parent / "requests.json"
    write_new(requests_path, requests)
    outside = Path(tempfile.mkdtemp(prefix="silo-external-"))
    venv = outside / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, timeout=120,
                   env=environment())
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "numpy==2.3.5", "highspy==1.15.1"],
                   check=True, cwd=outside, env=environment(), timeout=300)
    checker = outside / "parse_external.py"
    shutil.copy2(ROOT / "scripts/reliability/parse_external.py", checker)
    raw = output.parent / "raw.json"
    subprocess.run([str(python), "-I", str(checker), "--requests", str(requests_path),
                    "--output", str(raw)], check=True, cwd=outside, env=environment(), timeout=120)
    actual = json.loads(raw.read_text(encoding="utf-8"))
    failures = []
    for item in actual["records"]:
        try:
            equivalent(models[item["id"]], item["payload"], lp=item["format"] == "lp")
        except AssertionError:
            failures.append({"id": item["id"], "format": item["format"]})
    passed = not failures and actual["reads"] == 24
    write_new(output, {"passed": passed, "reads": actual["reads"], "failures": failures,
                       "optimization_calls": 0, "outside_environment": str(outside),
                       "raw_sha": sha(raw), "checker_sha": sha(checker),
                       "requests_sha": sha(requests_path)})
    assert passed, failures
    print("External highspy1.15.1: 24 readModel/getLp exact comparisons; zero optimization")


if __name__ == "__main__":
    main()
