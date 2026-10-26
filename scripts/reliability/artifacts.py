"""Build once or install the same candidate into the prescribed fresh environments."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .runtime import ROOT, environment, sha, write_new


def build(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run([sys.executable, "-m", "build", "--outdir", str(output)], cwd=ROOT,
                   check=True, env=environment(), timeout=300)
    files = sorted(output.glob("*.whl")) + sorted(output.glob("*.tar.gz"))
    assert len(files) == 2 and all("0.3.0a2" in p.name for p in files)
    write_new(output / "manifest.json", {"artifacts": {p.name: sha(p) for p in files},
              "source": {p.relative_to(ROOT).as_posix(): sha(p)
                         for p in (ROOT / "src").rglob("*.py")},
              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                  cwd=ROOT, text=True).strip()})


def installed(dist, output, engine):
    dist, output = dist.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((dist / "manifest.json").read_text(encoding="utf-8"))
    outside = Path(tempfile.mkdtemp(prefix="silo-a2-installed-"))
    checker = outside / "check_installed.py"
    shutil.copy2(ROOT / "scripts/reliability/check_installed.py", checker)
    records = []
    engines = ("dense", "sparse") if engine == "both" else (engine,)
    for selected in engines:
        for index, (name, digest) in enumerate(manifest["artifacts"].items()):
            artifact = dist / name
            assert sha(artifact) == digest
            env_path = outside / f"{selected}-{index}"
            subprocess.run([sys.executable, "-m", "venv", str(env_path)], check=True,
                           env=environment(), timeout=120)
            python = env_path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            command = [str(python), "-m", "pip", "install", "numpy==2.3.5"]
            if selected == "sparse":
                command.append("scipy==1.16.3")
            command.append(str(artifact))
            subprocess.run(command, check=True, cwd=outside, env=environment(), timeout=300)
            report = output / f"{selected}-{index}.json"
            subprocess.run([str(python), "-I", str(checker), "--source-root", str(ROOT),
                            "--artifact", str(artifact), "--engine", selected,
                            "--report", str(report)], check=True, cwd=outside,
                           env=environment(), timeout=180)
            actual = json.loads(report.read_text(encoding="utf-8"))
            # All loaded SILO modules must be those built from the recorded source map.
            for module, info in actual["loaded_modules"].items():
                module_path = "src/" + module.replace(".", "/")
                key = module_path + ".py"
                if key not in manifest["source"]:
                    key = module_path + "/__init__.py"
                assert info["sha256"] == manifest["source"][key], module
            records.append({"report": report.name, "sha": sha(report),
                            "artifact": name, "engine": selected,
                            "public_requests": actual["public_requests"],
                            "python": actual["python"], "platform": actual["platform"]})
    write_new(output / "summary.json", {"passed": True, "environments": len(records),
              "records": records, "outside": str(outside), "checker_sha": sha(checker),
              "artifact_manifest_sha": sha(dist / "manifest.json")})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--dist", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine", choices=("dense", "sparse", "both"), default="both")
    args = parser.parse_args()
    if args.build:
        build(args.output)
    else:
        if args.dist is None:
            parser.error("--dist required for installation checks")
        installed(args.dist, args.output, args.engine)


if __name__ == "__main__":
    main()
