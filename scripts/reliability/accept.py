"""Separate exact format and fixed 160-request solver acceptance entrances."""

import argparse
import json
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path

from .check_result import check
from .exact import equivalent
from .freeze import verify
from .runtime import FIXTURE, OUT, ROOT, environment, sha, write_new


def load():
    return (json.loads((FIXTURE / "inputs.json").read_text(encoding="utf-8")),
            json.loads((FIXTURE / "truth.json").read_text(encoding="utf-8")))


def roundtrip(payload, format_name):
    from silo.io import (
        model_from_dict,
        model_to_dict,
        model_to_lp,
        model_to_mps,
        parse_lp,
        parse_mps,
    )

    original = model_from_dict(payload)
    if format_name == "json":
        text = json.dumps(model_to_dict(original), allow_nan=False)
        restored = model_from_dict(json.loads(text))
        assert model_to_dict(original) == model_to_dict(restored)
        second = json.dumps(model_to_dict(restored), allow_nan=False)
    else:
        writer, reader = ((model_to_lp, parse_lp) if format_name == "lp"
                          else (model_to_mps, parse_mps))
        text = writer(original)
        restored = reader(text)
        second = writer(restored)
        if format_name == "mps":
            # MPS can legitimately turn legacy row syntax into explicit sides.
            # The original side-object signature is still exact, without LP split permission.
            equivalent(payload, model_to_dict(restored))
    actual = model_to_dict(restored)
    equivalent(payload, actual, lp=format_name == "lp")
    assert second == text, "unstable serialization"
    return actual, text


def formats(output):
    from silo.io import model_from_dict, model_to_dict, parse_lp, parse_mps

    from .handwritten import INVALID_LP, JSON_CASES, LP_CASES, MPS_CASES

    verify()
    data, _ = load()
    records = []
    for payload in data["models"]:
        for fmt in ("json", "mps", "lp"):
            _, text = roundtrip(payload, fmt)
            records.append({"model": payload["name"], "format": fmt,
                            "text_sha256": __import__("hashlib").sha256(text.encode()).hexdigest()})
    for cases, reader in ((LP_CASES, parse_lp), (MPS_CASES, parse_mps),
                          (JSON_CASES, lambda text: model_from_dict(json.loads(text)))):
        for text, expected in cases:
            equivalent(expected, model_to_dict(reader(text)))
    for text in INVALID_LP:
        try:
            parse_lp(text)
        except ValueError:
            continue
        raise AssertionError("LP rejection fixture accepted")
    perturbations = []
    for field in ("coefficient", "bound"):
        original = data["models"][0]
        changed = deepcopy(original)
        if field == "coefficient":
            changed["objective"]["coefficients"]["x"] += 2**-39
        else:
            changed["variables"][0]["upper"] += 2**-39
        try:
            equivalent(original, changed)
        except AssertionError:
            perturbations.append(field)
        else:
            raise AssertionError("sub-tolerance semantic perturbation escaped")
    write_new(output, {"passed": True, "roundtrips": records, "handwritten": {"lp": 6,
                      "mps": 6, "json": 4}, "rejections": len(INVALID_LP),
                      "perturbations_rejected": perturbations, "silo_requests": 0})
    print("Exact formats: 96/96; handwritten 16/16; rejections 25/25; perturbations 2/2")


def acceptance(output):
    verify()
    data, truth = load()
    output = Path(output).resolve()
    directory = output.parent
    directory.mkdir(parents=True, exist_ok=False)
    source = {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / "src").rglob("*.py")}
    model_map = {p["name"]: p for p in data["models"]}
    requests = []
    for engine in ("dense", "sparse"):
        for p in data["models"]:
            requests.append(("original", p, engine, None, None))
        for name in data["resolve_ids"]:
            for fmt in ("json", "mps", "lp"):
                actual, _ = roundtrip(model_map[name], fmt)
                requests.append((fmt, actual, engine, name, None))
        for edit in data["edits"]:
            requests.append(("session", model_map[edit["initial"]], engine, edit["initial"], edit))
            requests.append(("cold", edit["modified"], engine, None, None))
    records, failures, public, dispatched = [], [], 0, 0
    start = time.perf_counter()
    for i, (group, payload, engine, truth_id, edit) in enumerate(requests):
        if time.perf_counter() - start > 900:
            failures.append({"index": i, "reason": "group timeout"})
            break
        integer = any(v.get("type", "continuous") != "continuous" for v in payload["variables"])
        limit = 30 if integer else 10
        request = {"payload": payload, "options": {**data["options"], "lp_engine": engine,
                   "time_limit": limit}}
        count = 1
        if edit is not None:
            request["session"] = edit
            count = 2
        reqpath, respath = directory / f"{i:03}_request.json", directory / f"{i:03}_result.json"
        write_new(reqpath, request)
        before = time.perf_counter()
        dispatched += count
        record = {"index": i, "group": group, "model": truth_id or payload["name"],
                  "engine": engine, "public_requests": count, "request_sha": sha(reqpath)}
        try:
            process = subprocess.run([sys.executable, "-m", "scripts.reliability.worker",
                                      str(reqpath), str(respath)], cwd=ROOT, env=environment(),
                                     capture_output=True, text=True,
                                     timeout=limit * count + (2 if count == 2 else 0))
            record.update(exit_code=process.returncode, stdout=process.stdout,
                          stderr=process.stderr)
            assert process.returncode == 0, process.stderr
            response = json.loads(respath.read_text(encoding="utf-8"))
            assert response["public_entries"] == count
            assert response["source_origins"]
            assert all(source[path] == digest
                       for path, digest in response["source_origins"].items())
            results = response["results"]
            assert len(results) == count
            record["checks"] = []
            for j, item in enumerate(results):
                name = (edit["modified"]["name"] if edit is not None and j == 1
                        else truth_id or payload["name"])
                assert item["seconds"] <= limit
                record["checks"].append(check(item["payload"], item["result"], truth[name],
                                             branching=name in ("M01", "M02", "M03", "M04")))
            record["result_sha"] = sha(respath)
            record["passed"] = True
        except (AssertionError, ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
            record.update(passed=False, error=f"{type(exc).__name__}: {exc}")
            failures.append(record)
        record["wall_seconds"] = time.perf_counter() - before
        calls_path = respath.with_suffix(".calls.jsonl")
        entries = len(calls_path.read_text(encoding="utf-8").splitlines()) \
            if calls_path.exists() else 0
        record["actual_public_entries"] = entries
        public += entries
        records.append(record)
        write_new(directory / f"{i:03}_check.json", record)
    assert source == {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / "src").rglob("*.py")}
    passed = not failures and public == 160
    receipt = {"passed": passed, "public_requests": public, "dispatched": dispatched,
               "expected": 160,
               "units": len(records), "failures": failures, "records": records,
               "source": source, "freeze_manifest_sha": sha(FIXTURE / "manifest.json"),
               "seconds": time.perf_counter() - start}
    write_new(output, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ("source", "records")}))
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--formats", action="store_true")
    mode.add_argument("--solve", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.formats:
        formats(args.output or OUT / "formats.json")
        return 0
    if args.output is None:
        parser.error("--solve requires an unused --output within a new evidence directory")
    return acceptance(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
