"""Read-only Windows host observations around a separately authorized warm run."""

import argparse
import ctypes
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sparse_program import ledger  # noqa: E402

COMPUTE = {
    "python.exe",
    "pythonw.exe",
    "xelatex.exe",
    "pdflatex.exe",
    "lualatex.exe",
    "tectonic.exe",
    "r.exe",
    "julia.exe",
    "matlab.exe",
    "kimi.exe",
}


def quiet_decision(samples):
    if len(samples) < 5 or any(row["unreadable_compute"] for row in samples):
        return {"quiet": False, "reason": "insufficient samples or unreadable compute process"}
    cores = {}
    for row in samples:
        for item in row["other_compute"]:
            cores[item["pid"]] = cores.get(item["pid"], 0.0) + item["core_fraction"] / len(samples)
    host = sum(row["host_total_fraction"] for row in samples) / len(samples)
    total = sum(cores.values())
    maximum = max(cores.values(), default=0.0)
    return {
        "quiet": host <= 0.20 and total <= 0.50 and maximum <= 0.20,
        "mean_host_fraction": host,
        "mean_other_compute_cores": total,
        "maximum_process_mean_cores": maximum,
        "limits": {"host_fraction": 0.20, "other_compute_cores": 0.50, "process_cores": 0.20},
    }


class Sampler:
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("The authorized host observer requires Windows")
        from ctypes import wintypes as w

        class Entry(ctypes.Structure):
            _fields_ = [
                ("size", w.DWORD),
                ("uses", w.DWORD),
                ("pid", w.DWORD),
                ("heap", ctypes.c_size_t),
                ("module", w.DWORD),
                ("threads", w.DWORD),
                ("parent", w.DWORD),
                ("priority", ctypes.c_long),
                ("flags", w.DWORD),
                ("name", w.WCHAR * 260),
            ]

        # Keep ctypes function signatures private: the resource guard uses
        # a different PROCESSENTRY32W class in the same process.
        self.w, self.Entry, self.kernel = w, Entry, ctypes.WinDLL("kernel32")
        k = self.kernel
        k.CreateToolhelp32Snapshot.argtypes, k.CreateToolhelp32Snapshot.restype = (
            [w.DWORD, w.DWORD],
            w.HANDLE,
        )
        k.Process32FirstW.argtypes = k.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
        k.CloseHandle.argtypes = [w.HANDLE]
        k.OpenProcess.argtypes, k.OpenProcess.restype = [w.DWORD, w.BOOL, w.DWORD], w.HANDLE
        k.GetProcessTimes.argtypes = [w.HANDLE, *([ctypes.POINTER(w.FILETIME)] * 4)]
        k.GetSystemTimes.argtypes = [ctypes.POINTER(w.FILETIME)] * 3
        self.previous = None

    @staticmethod
    def number(value):
        return ((value.dwHighDateTime << 32) | value.dwLowDateTime) * 1e-7

    def sample(self):
        w, k = self.w, self.kernel
        idle, kernel, user = w.FILETIME(), w.FILETIME(), w.FILETIME()
        if not k.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            raise ctypes.WinError()
        system = self.number(idle), self.number(kernel) + self.number(user)
        handle = k.CreateToolhelp32Snapshot(2, 0)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError()
        entries = []
        try:
            entry = self.Entry()
            entry.size = ctypes.sizeof(entry)
            more = k.Process32FirstW(handle, ctypes.byref(entry))
            while more:
                entries.append((entry.pid, entry.parent, entry.name.lower()))
                more = k.Process32NextW(handle, ctypes.byref(entry))
        finally:
            k.CloseHandle(handle)
        own = {os.getpid()}
        while True:
            expanded = own | {pid for pid, parent, _ in entries if parent in own}
            if own == expanded:
                break
            own = expanded
        processes, unreadable = {}, []
        for pid, _, name in entries:
            if pid in own or name not in COMPUTE:
                continue
            handle = k.OpenProcess(0x1000, False, pid)
            if not handle:
                unreadable.append(pid)
                continue
            try:
                created, exited, kernel, user = (w.FILETIME() for _ in range(4))
                if k.GetProcessTimes(handle, *map(ctypes.byref, (created, exited, kernel, user))):
                    processes[pid] = (
                        name,
                        self.number(created),
                        self.number(kernel) + self.number(user),
                    )
                else:
                    unreadable.append(pid)
            finally:
                k.CloseHandle(handle)
        now = time.perf_counter()
        previous, self.previous = self.previous, (now, system, processes)
        if previous is None:
            return None
        old_time, old_system, old_processes = previous
        elapsed, total = now - old_time, system[1] - old_system[1]
        if elapsed <= 0 or total <= 0:
            raise RuntimeError("Host observer clock did not advance")
        active = []
        for pid, (name, created, cpu) in processes.items():
            old = old_processes.get(pid)
            if old is not None and created == old[1]:
                active.append(
                    {"pid": pid, "name": name, "core_fraction": max(0, (cpu - old[2]) / elapsed)}
                )
        return {
            "utc": ledger.utc(),
            "interval_seconds": elapsed,
            "host_total_fraction": max(0, min(1, 1 - (system[0] - old_system[0]) / total)),
            "other_compute": active,
            "unreadable_compute": unreadable,
        }


def validate_baseline(path):
    path = Path(path).resolve()
    if not path.is_relative_to((ledger.OUT / "host").resolve()):
        raise RuntimeError("Host baseline must belong to the original evidence root")
    baseline = json.loads(path.read_text())
    trace = path.parent / "samples.jsonl"
    if ledger.sha(trace) != baseline["samples_sha256"]:
        raise RuntimeError("Host baseline sample hash changed")
    samples = [json.loads(line) for line in trace.read_text().splitlines()]
    decision = quiet_decision(samples)
    if len(samples) != 10 or decision != baseline["decision"] or not decision["quiet"]:
        raise RuntimeError("Host baseline is busy or incomplete")
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(baseline["utc"])).total_seconds()
    if not 0 <= age <= 300:
        raise RuntimeError("Host baseline is older than five minutes")
    current = ledger.identity()
    if any(baseline["source"][key] != current[key] for key in ("source", "scripts", "inputs")):
        raise RuntimeError("Source, scripts or inputs changed since host baseline")
    if baseline["environment"] != ledger.environment():
        raise RuntimeError("Environment changed since host baseline")
    return baseline


def validate_warm4_parent(events, parent_run, source_sha256):
    return validate_supervised_parent(events, parent_run, source_sha256, warm_round=4)


def validate_supervised_parent(events, parent_run, source_sha256, *, warm_round):
    assert warm_round in (4, 5), "Unsupported supervised child round"
    grant = (
        ledger.warm4_grant(events) if warm_round == 4 else ledger.supervision_recovery_grant(events)
    )
    assert grant is not None, "Supervised child lacks direct human authority"
    assert grant["source_sha256"] == source_sha256, "Supervised child source differs"
    starts = [
        event
        for event in events
        if event["kind"] == "command_started" and event.get("run") == parent_run
    ]
    assert len(starts) == 1, "Supervised child requires one actual accounting parent"
    parent = starts[0]
    assert parent.get("group") == "warm" and parent.get("stage") == "SP3", "Wrong parent group"
    assert parent.get("rounds") == {"warm": 1} and parent.get("warm_round") == warm_round
    assert parent.get(f"warm{warm_round}_authority_sha256") == grant["sha256"]
    assert not any(
        event["kind"] in ("command_finished", f"warm{warm_round}_child_started")
        and event.get("run") == parent_run
        for event in events
    ), "Warm4 parent is finished or its child claim is already consumed"
    return parent


def supervision_decision(
    before, after, environment, final_environment, samples, errors, child_code
):
    frozen = all(before[key] == after[key] for key in ("source", "scripts", "inputs"))
    complete = (
        bool(samples) and not errors and not any(row["unreadable_compute"] for row in samples)
    )
    eligible = frozen and environment == final_environment and complete
    return {
        "source_scripts_inputs_frozen": frozen,
        "environment_frozen": environment == final_environment,
        "host_observation_complete": complete,
        "formal_host_load": quiet_decision(samples),
        "controlled_run_eligible": eligible,
        "original_child_exit_code": child_code,
        "original_acceptance_passed": child_code == 0,
        "accepted": eligible and child_code == 0,
        "load_policy": "quiet preflight; observed runtime load; original acceptance gates",
    }


def execute_supervised_warm(args):
    baseline = validate_baseline(Path(args.host_baseline))
    identity, environment = ledger.identity(), ledger.environment()
    parent_run = os.environ.get("SILO_SPARSE_ACCOUNT_PARENT")
    assert parent_run, "Warm4 requires its real public accounting parent"
    parent = validate_supervised_parent(
        ledger.history(), parent_run, identity["source_sha256"], warm_round=args.round
    )
    parent_identity = json.loads((ledger.ROOT / parent_run / "identity.json").read_text())
    assert ledger.digest(parent_identity) == parent["identity_sha256"]
    assert all(parent_identity[key] == identity[key] for key in ("source", "scripts", "inputs"))
    argv = parent["argv"]
    assert (
        Path(argv[argv.index("--host-baseline") + 1]).resolve()
        == Path(args.host_baseline).resolve()
    )
    assert Path(argv[argv.index("--host-output") + 1]).resolve() == Path(args.host_output).resolve()
    output = Path(args.host_output).resolve()
    assert output.is_relative_to((ledger.OUT / "host").resolve()), (
        "Host evidence escaped original root"
    )
    output.mkdir(parents=True, exist_ok=False)
    ledger.append(
        f"warm{args.round}_child_started",
        run=parent_run,
        source_sha256=identity["source_sha256"],
        authority_sha256=parent[f"warm{args.round}_authority_sha256"],
        fixed_children=80,
        baseline_sha256=ledger.sha(args.host_baseline),
    )
    samples, errors, sampler_cost = [], [], []
    stop = threading.Event()

    def observe():
        start = time.thread_time()
        try:
            sampler = Sampler()
            sampler.sample()
            while not stop.wait(2):
                row = sampler.sample()
                samples.append(row)
                with (output / "samples.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row) + "\n")
        except BaseException as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
        finally:
            sampler_cost.append(time.thread_time() - start)

    observer = threading.Thread(target=observe, daemon=True)
    observer.start()
    code = 1
    existing_summaries = set((ledger.OUT / "warm").glob("*/summary.json"))
    try:
        from sparse_program.warm import execute

        code = execute(args)
    finally:
        stop.set()
        observer.join(timeout=5)
        if observer.is_alive():
            errors.append("Host observer did not finish")
        final_identity, final_environment = ledger.identity(), ledger.environment()
        new_summaries = set((ledger.OUT / "warm").glob("*/summary.json")) - existing_summaries
        warm_summary = None
        if len(new_summaries) == 1:
            path = new_summaries.pop()
            if path.parent.name.startswith(f"round{args.round}_"):
                warm_summary = {
                    "path": path.relative_to(ledger.ROOT).as_posix(),
                    "sha256": ledger.sha(path),
                }
        if warm_summary is None:
            errors.append("Supervised warm did not produce exactly one matching summary")
        decision = supervision_decision(
            identity, final_identity, environment, final_environment, samples, errors, code
        )
        trace = output / "samples.jsonl"
        report = {
            "source": identity,
            "final_source": final_identity,
            "environment": environment,
            "final_environment": final_environment,
            "baseline_path": args.host_baseline,
            "baseline_sha256": ledger.sha(args.host_baseline),
            "baseline_decision": baseline["decision"],
            "parent_run": parent_run,
            "supervised_warm_round": args.round,
            "warm_summary": warm_summary,
            "decision": decision,
            "sample_count": len(samples),
            "errors": errors,
            "sampler_thread_cpu_seconds": sum(sampler_cost),
            "samples_sha256": ledger.sha(trace) if trace.exists() else None,
        }
        (output / "supervision.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if decision["accepted"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("SILO_SPARSE_ACCOUNT_PARENT"):
        raise RuntimeError("Host observation requires the original single accounting parent")
    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"
    args.output.mkdir(parents=True, exist_ok=False)
    identity, environment = ledger.identity(), ledger.environment()
    sampler, samples = Sampler(), []
    sampler.sample()
    for _ in range(10):
        time.sleep(2)
        row = sampler.sample()
        samples.append(row)
        with (args.output / "samples.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
    report = {
        "source": identity,
        "environment": environment,
        "utc": ledger.utc(),
        "decision": quiet_decision(samples),
        "solver_calls": 0,
        "samples_sha256": ledger.sha(args.output / "samples.jsonl"),
    }
    (args.output / "preflight.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["decision"]))
    return 0 if report["decision"]["quiet"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
