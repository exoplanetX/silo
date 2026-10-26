"""Independent OS RSS sampling and child wall guards, not solver status logic."""

import ctypes
import os
import subprocess
import time
from pathlib import Path


def linux_peak_from_status(text):
    """Return a genuine VmHWM in bytes, or None when this field is absent.

    A short-lived/zombie process can still have a readable status without memory
    fields. Missing, malformed and unreadable samples are distinct states; VmRSS
    is deliberately not substituted for an OS high-water mark.
    """
    fields = [line.split() for line in text.splitlines() if line.startswith("VmHWM:")]
    if not fields:
        return None
    if (len(fields) != 1 or len(fields[0]) != 3 or fields[0][0] != "VmHWM:"
            or fields[0][2] != "kB" or not fields[0][1].isascii()
            or not fields[0][1].isdigit()):
        raise ValueError("Invalid /proc VmHWM sample")
    return int(fields[0][1]) * 1024


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
    return linux_peak_from_status(text)


def windows_tree_peaks(process, peaks):
    """Include Windows venv redirector children, using OS peak working sets.

    The sum of per-process historical peaks is a conservative upper bound on
    tree peak RSS. Monitoring just the venv python.exe redirector misses Python
    and native library allocations in its real-interpreter child.
    """
    from ctypes import wintypes
    from types import SimpleNamespace

    class Entry(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("pid", wintypes.DWORD),
            ("heap", ctypes.c_size_t),
            ("module", wintypes.DWORD),
            ("threads", wintypes.DWORD),
            ("parent", wintypes.DWORD),
            ("priority", wintypes.LONG),
            ("flags", wintypes.DWORD),
            ("exe", wintypes.WCHAR * 260),
        ]

    kernel = ctypes.windll.kernel32
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise ctypes.WinError()
    pairs = []
    try:
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            pairs.append((entry.pid, entry.parent))
            more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    family = {process.pid}
    while True:
        extended = family | {pid for pid, parent in pairs if parent in family}
        if extended == family:
            break
        family = extended
    for pid in family:
        if pid == process.pid:
            try:
                peaks[pid] = max(peaks.get(pid, 0), peak_rss(process))
            except OSError:
                if process.poll() is None:
                    raise
            continue
        handle = kernel.OpenProcess(0x1410, False, pid)
        if not handle:
            # A child may exit between the process snapshot and OpenProcess.
            continue
        try:
            value = peak_rss(SimpleNamespace(_handle=handle))
            peaks[pid] = max(peaks.get(pid, 0), value)
        except OSError:
            pass
        finally:
            kernel.CloseHandle(handle)
    return sum(peaks.values())


def kill_tree(process):
    if process.poll() is not None:
        process.wait()
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if process.poll() is None:
            # taskkill can return nonzero without raising. Reap our direct
            # child even when that external tree-cleanup command did not work.
            process.kill()
    else:
        try:
            process.kill()
        except ProcessLookupError:
            # The owned child can exit between poll() and kill(). Still reap it.
            pass
    process.wait()


def guarded(argv, cwd, log, seconds, rss_limit=1 << 30):
    start = time.perf_counter()
    peak, guard_reason, process_peaks = None, None, {}
    valid_samples, missing_samples, missing_reason = 0, 0, None
    with Path(log).open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
        try:
            while True:
                try:
                    measured = (
                        windows_tree_peaks(process, process_peaks)
                        if os.name == "nt"
                        else peak_rss(process)
                    )
                    if os.name == "nt" and not process_peaks:
                        measured = None
                    if measured is None:
                        missing_samples += 1
                        missing_reason = ("Windows_tree_no_samples" if os.name == "nt"
                                          else "VmHWM_field_missing")
                    else:
                        peak = measured if peak is None else max(peak, measured)
                        valid_samples += 1
                except FileNotFoundError:
                    if os.name == "nt" and process.poll() is None:
                        raise
                    missing_samples += 1
                    missing_reason = "process_status_disappeared"
                except OSError:
                    if process.poll() is None:
                        raise
                    missing_samples += 1
                    missing_reason = "status_read_failed_after_exit"
                # Missing samples never restart the absolute child deadline.
                if peak is not None and peak > rss_limit:
                    guard_reason = "harness_peak_rss"
                elif time.perf_counter() - start > seconds:
                    guard_reason = "harness_timeout"
                if guard_reason:
                    kill_tree(process)
                    break
                if process.poll() is not None:
                    if peak is None:
                        guard_reason = "harness_rss_unmeasured"
                    break
                time.sleep(0.01)
            code = process.wait()
        except BaseException:
            # Own only this Popen child (and the existing Windows tree scope).
            # Cleanup must not replace the original sampling/parser exception.
            try:
                try:
                    kill_tree(process)
                finally:
                    # Even a failed tree-cleanup command must not leave the
                    # direct child we created running or unreaped.
                    if process.poll() is None:
                        process.kill()
                    process.wait()
            except BaseException:
                pass
            raise
    return {
        "pid": process.pid,
        "exit_code": code,
        "elapsed_seconds": time.perf_counter() - start,
        "peak_rss_bytes": peak,
        "guard_reason": guard_reason,
        "os_peak_method": "PeakWorkingSetSize" if os.name == "nt" else "/proc VmHWM",
        "process_scope": "root_and_descendants" if os.name == "nt" else "root",
        "conservative_sum_of_os_peaks": os.name == "nt",
        "monitored_processes": len(process_peaks) if os.name == "nt" else 1,
        "process_peak_bytes": process_peaks,
        "rss_sample_status": "measured" if valid_samples else "unmeasured",
        "valid_rss_samples": valid_samples,
        "missing_rss_samples": missing_samples,
        "last_missing_reason": missing_reason,
        "memory_verification_valid": valid_samples > 0,
    }
