"""Small append-only per-contract check budget, subprocess timeout and receipts."""

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/reliability_io_20261026"
FIXTURE = ROOT / "tests/fixtures/reliability_20261026"
LIMITS = {"local": 20, "quality": 2, "accept": 2, "external": 2, "build": 2,
          "install": 2, "freeze": 2}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def environment():
    result = os.environ.copy()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                "BLIS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        result[key] = "1"
    result["PYTHONUTF8"] = "1"
    # Activating only this child lets existing console-script regressions find
    # the same installed entry point as its selected interpreter.
    result["PATH"] = str(Path(sys.executable).parent) + os.pathsep + result.get("PATH", "")
    return result


def events():
    path = OUT / "ledger.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] \
        if path.exists() else []


def append(value):
    OUT.mkdir(parents=True, exist_ok=True)
    value = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), **value}
    with (OUT / "ledger.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def run(kind, command, *, timeout=900):
    history = events()
    used = sum(e.get("seconds", 0) for e in history if e.get("event") == "end")
    ordinal = 1 + sum(e.get("kind") == kind and e.get("event") == "start" for e in history)
    if kind not in LIMITS or ordinal > LIMITS[kind] or used >= 3600:
        raise RuntimeError("contract check budget exhausted")
    timeout = min(timeout, 3600 - used)
    directory = OUT / f"{kind}{ordinal}"
    directory.mkdir(parents=True, exist_ok=False)
    append({"event": "start", "kind": kind, "ordinal": ordinal, "command": command,
            "timeout": timeout, "prior_seconds": used})
    started = time.perf_counter()
    with (directory / "console.log").open("wb") as log:
        process = subprocess.Popen(command, cwd=ROOT, env=environment(), stdout=log,
                                   stderr=subprocess.STDOUT)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=log, stderr=subprocess.STDOUT, check=False)
            else:
                process.kill()
            process.wait()
            code = 124
    seconds = time.perf_counter() - started
    receipt = {"event": "end", "kind": kind, "ordinal": ordinal, "exit_code": code,
               "seconds": seconds, "total_seconds": used + seconds,
               "log": str((directory / "console.log").relative_to(ROOT)),
               "log_sha256": sha(directory / "console.log")}
    write_new(directory / "receipt.json", receipt)
    append(receipt)
    print(json.dumps(receipt))
    print((directory / "console.log").read_text(encoding="utf-8", errors="replace")[-10000:])
    return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=LIMITS)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("command required")
    return run(args.kind, command, timeout=args.timeout)


if __name__ == "__main__":
    sys.exit(main())
