"""Independent OS RSS sampling and child wall guards, not solver status logic."""

import ctypes
import os
import subprocess
import time
from pathlib import Path


def peak_rss(process):
    if os.name == "nt":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
                (name, ctypes.c_size_t)
                for name in (
                    "peak_working",
                    "working",
                    "peak_paged",
                    "paged",
                    "peak_nonpaged",
                    "nonpaged",
                    "pagefile",
                    "peak_pagefile",
                )
            ]

        info = Counters()
        info.cb = ctypes.sizeof(info)
        function = ctypes.windll.psapi.GetProcessMemoryInfo
        function.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
        function.restype = wintypes.BOOL
        if not function(int(process._handle), ctypes.byref(info), info.cb):
            raise ctypes.WinError()
        return int(info.peak_working)
    text = Path(f"/proc/{process.pid}/status").read_text()
    return (
        int(next(line.split()[1] for line in text.splitlines() if line.startswith("VmHWM:"))) * 1024
    )


def kill_tree(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.kill()
    process.wait()


def guarded(argv, cwd, log, seconds, rss_limit=1 << 30):
    start = time.perf_counter()
    peak, guard_reason = 0, None
    with Path(log).open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
        while True:
            try:
                peak = max(peak, peak_rss(process))
            except (OSError, StopIteration):
                if process.poll() is None:
                    raise
            if peak > rss_limit:
                guard_reason = "harness_peak_rss"
            elif time.perf_counter() - start > seconds:
                guard_reason = "harness_timeout"
            if guard_reason:
                kill_tree(process)
                break
            if process.poll() is not None:
                break
            time.sleep(0.01)
        code = process.wait()
    return {
        "pid": process.pid,
        "exit_code": code,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_rss_bytes": peak,
        "guard_reason": guard_reason,
        "os_peak_method": "PeakWorkingSetSize" if os.name == "nt" else "/proc VmHWM",
    }
