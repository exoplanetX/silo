"""Preserve and reproduce bounded research probes outside SILO's solver API."""

import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUTS = ROOT / "outputs/research/pricing"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(base: Path, relative: str) -> Path:
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or path == base.resolve():
        raise ValueError(f"Path escapes its asset directory: {relative}")
    return path


def verified_assets() -> dict:
    metadata = json.loads((HERE / "provenance.json").read_text(encoding="utf-8"))
    for probe in metadata["probes"].values():
        path = safe_path(ROOT, probe["repo_path"])
        if path.stat().st_size != probe["bytes"] or sha256(path) != probe["sha256"]:
            raise ValueError(f"Archival probe bytes changed: {probe['repo_path']}")
    source = HERE / metadata["inputs"]["manifest"]
    if sha256(source) != metadata["inputs"]["manifest_sha256"]:
        raise ValueError("Pinned input manifest changed")
    inputs = json.loads(source.read_text(encoding="utf-8-sig"))
    if len(inputs) != metadata["inputs"]["file_count"]:
        raise ValueError("Pinned input file count changed")
    prefix = (
        "https://raw.githubusercontent.com/"
        + metadata["inputs"]["repository"]
        + "/"
        + metadata["inputs"]["revision"]
        + "/"
    )
    paths = set()
    for item in inputs:
        safe_path(OUTPUTS, item["path"])
        if item["url"] != prefix + item["path"] or item["path"] in paths:
            raise ValueError("Input URL/revision/path is inconsistent")
        paths.add(item["path"])
    return metadata


def input_files(folder: Path, fetch_missing: bool = False) -> list[dict]:
    verified_assets()
    items = json.loads((HERE / "source_manifest.json").read_text(encoding="utf-8-sig"))
    for item in items:
        target = safe_path(folder, item["path"])
        if not target.exists():
            if not fetch_missing:
                raise ValueError(f"Missing pinned input: {target}; prepare inputs first")
            with urlopen(item["url"], timeout=30) as response:
                data = response.read(item["bytes"] + 1)
            if (
                len(data) != item["bytes"]
                or hashlib.sha256(data).hexdigest() != item["sha256"].lower()
            ):
                raise ValueError(f"Downloaded input hash mismatch: {item['path']}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if target.stat().st_size != item["bytes"] or sha256(target) != item["sha256"].lower():
            raise ValueError(f"Cached input hash mismatch: {item['path']}")
    return items


def execute_archived(probe: str, output: Path) -> None:
    metadata = verified_assets()
    source = safe_path(ROOT, metadata["probes"][probe]["repo_path"])
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    relocated = 0
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "HERE" for target in node.targets
        ):
            expected = ast.parse("Path(__file__).resolve().parent", mode="eval").body
            if ast.dump(node.value) != ast.dump(expected):
                raise ValueError("Unrecognized archival HERE assignment")
            node.value = ast.parse(f"Path({str(output)!r})", mode="eval").body
            relocated += 1
    if relocated != int(probe in {"locality", "application"}):
        raise ValueError("Unexpected number of archival path relocations")
    ast.fix_missing_locations(tree)
    sys.argv = [str(source)]
    exec(compile(tree, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})


def run(probe: str, folder: Path, inputs: Path, timeout: float) -> int:
    metadata = verified_assets()
    if probe == "application":
        items = input_files(inputs)
    folder.mkdir(parents=True, exist_ok=False)
    if probe == "application":
        for item in items:
            destination = safe_path(folder, item["path"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(safe_path(inputs, item["path"]), destination)
        shutil.copy2(HERE / "source_manifest.json", folder / "source_manifest.json")
    record = {
        "probe": probe,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "probe_sha256": metadata["probes"][probe]["sha256"],
        "runner_sha256": sha256(Path(__file__)),
        "input_manifest_sha256": metadata["inputs"]["manifest_sha256"],
        "python": sys.version,
        "timeout_seconds": timeout,
        "scope": "execution relocation of a preserved research probe; no solver promotion",
    }
    status = 1
    try:
        with (folder / "stdout.txt").open("w", encoding="utf-8") as stdout:
            with (folder / "stderr.txt").open("w", encoding="utf-8") as stderr:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        "-u",
                        str(Path(__file__).resolve()),
                        "--worker",
                        probe,
                        "--output",
                        str(folder),
                    ],
                    cwd=folder,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=timeout,
                )
        status = result.returncode
        if status == 0:
            name = Path(metadata["probes"][probe]["historical_result"]["original_relative_path"])
            result_file = folder / name.name
            if probe in {"theory", "signature", "frontier"}:
                payload = json.loads((folder / "stdout.txt").read_text(encoding="utf-8"))
                result_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            json.loads(result_file.read_text(encoding="utf-8"))
            record.update(result_file=result_file.name, result_sha256=sha256(result_file))
    except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
        record["error"] = str(exc)
        status = 1
    record.update(returncode=status, finished_utc=datetime.now(timezone.utc).isoformat())
    (folder / "run_manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(folder), "returncode": status}))
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--verify", action="store_true")
    actions.add_argument("--prepare-inputs", action="store_true")
    names = ("theory", "signature", "frontier", "locality", "application")
    actions.add_argument("--probe", choices=names)
    actions.add_argument("--worker", choices=names, help=argparse.SUPPRESS)
    parser.add_argument("--fetch-missing", action="store_true")
    parser.add_argument("--inputs", type=Path, default=OUTPUTS / "inputs")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    try:
        metadata = verified_assets()
        if args.verify:
            print(f"Research assets OK: {len(metadata['probes'])} immutable probes; pinned inputs")
            return 0
        if args.prepare_inputs:
            inputs = args.inputs.resolve()
            if not inputs.is_relative_to(OUTPUTS.resolve()):
                raise ValueError("Input cache must stay under outputs/research/pricing")
            items = input_files(inputs, args.fetch_missing)
            print(f"Pinned inputs OK: {len(items)} files at {inputs}")
            return 0
        if args.output is None or not args.output.resolve().is_relative_to(OUTPUTS.resolve()):
            raise ValueError("Provide a new --output directory under outputs/research/pricing")
        if args.worker:
            if not args.output.is_dir():
                raise ValueError("Worker output directory is absent")
            execute_archived(args.worker, args.output.resolve())
            return 0
        if args.timeout <= 0:
            raise ValueError("Timeout must be positive")
        return run(args.probe, args.output.resolve(), args.inputs.resolve(), args.timeout)
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
