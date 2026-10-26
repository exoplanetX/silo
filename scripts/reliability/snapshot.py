"""One lightweight resource/identity snapshot; no host operations or quiet gate."""

import ctypes
import importlib.metadata
import os
import platform
import subprocess
import sys
import time

from .runtime import OUT, ROOT, environment, sha, write_new


def main():
    start = time.perf_counter()
    memory = None
    if os.name == "nt":
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong),
                        ("page", ctypes.c_ulonglong), ("page_free", ctypes.c_ulonglong),
                        ("virtual", ctypes.c_ulonglong), ("virtual_free", ctypes.c_ulonglong),
                        ("extended", ctypes.c_ulonglong)]
        status = Memory()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            memory = {"total": status.total, "available": status.available, "load": status.load}
    dependencies = {}
    for package in ("numpy", "scipy", "pytest", "ruff", "build"):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependencies[package] = None
    source = {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / "src").rglob("*.py")}
    value = {"platform": platform.platform(), "machine": platform.machine(),
             "processor": platform.processor(), "logical_cpus": os.cpu_count(),
             "python": sys.version, "executable": sys.executable, "memory": memory,
             "dependencies": dependencies, "source": source,
             "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
             "governance": {p: sha(ROOT / p) for p in
                            ("AGENTS.md", "研究主题固定_严重反面案例通告_20261020.md")},
             "child_threads": {k: v for k, v in environment().items() if k.endswith("THREADS")},
             "host_policy": "OneDrive remains exited; no process/power/global-env operations",
             "seconds": time.perf_counter() - start}
    assert value["seconds"] <= 10
    write_new(OUT / "start.json", value)
    print({k: v for k, v in value.items() if k != "source"})


if __name__ == "__main__":
    main()
