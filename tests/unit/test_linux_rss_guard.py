"""Deterministic Linux RSS-state/cleanup tests also executed on Windows."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def resources():
    path = Path(__file__).resolve().parents[2] / "scripts/sparse_program/resources.py"
    spec = importlib.util.spec_from_file_location("r4_resources", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("text,expected", [
    ("Name:\tpython\nVmHWM:\t123 kB\nVmRSS:\t99 kB\n", 123 * 1024),
    ("Name:\tpython\nState:\tZ (zombie)\n", None),
    ("VmRSS:\t99 kB\n", None), ("VmHWM:\t0 kB\n", 0),
])
def test_linux_peak_field_has_explicit_missing_state(text, expected):
    assert resources().linux_peak_from_status(text) == expected


@pytest.mark.parametrize("text", ["VmHWM: -1 kB", "VmHWM: NaN kB", "VmHWM: 1.5 kB",
                                      "VmHWM: 12", "VmHWM: 12 MB", "VmHWM: 12 kB extra",
                                      "VmHWM: 12 kB\nVmHWM: 13 kB", "VmHWM: １２ kB"])
def test_malformed_linux_peak_is_visible_failure(text):
    with pytest.raises(ValueError, match="VmHWM"):
        resources().linux_peak_from_status(text)


class Child:
    pid = 12345

    def __init__(self):
        self.code = None
        self.killed = False
        self.waited = False

    def poll(self):
        return self.code

    def kill(self):
        self.killed, self.code = True, -9

    def wait(self):
        assert self.code is not None, "waiting for live child would block"
        self.waited = True
        return self.code


def simulated(monkeypatch, samples, *, finish=True):
    module, child = resources(), Child()
    monkeypatch.setattr(module, "os", SimpleNamespace(name="posix"))
    monkeypatch.setattr(module, "subprocess", SimpleNamespace(
        Popen=lambda *a, **k: child, STDOUT=subprocess.STDOUT))
    time = [0.0]

    def perf_counter():
        time[0] += 0.01
        return time[0]

    monkeypatch.setattr(module, "time", SimpleNamespace(perf_counter=perf_counter,
                                                        sleep=lambda seconds: None))
    pending = iter(samples)

    def peak(process):
        value = next(pending)
        if isinstance(value, tuple):
            value, last = value
            if last and finish:
                child.code = 7
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(module, "peak_rss", peak)
    return module, child


def test_missing_then_recovery_preserves_real_peak_and_exit(monkeypatch, tmp_path):
    module, child = simulated(monkeypatch, [None, 8192, (4096, True)])
    result = module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 1)
    assert result["peak_rss_bytes"] == 8192
    assert result["valid_rss_samples"] == 2 and result["missing_rss_samples"] == 1
    assert result["memory_verification_valid"] and result["guard_reason"] is None
    assert result["exit_code"] == 7 and child.waited and not child.killed


@pytest.mark.parametrize("missing", [None, FileNotFoundError("gone")])
def test_exit_or_disappeared_status_keeps_prior_peak(monkeypatch, tmp_path, missing):
    module, child = simulated(monkeypatch, [8192, (missing, True)])
    result = module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 1)
    assert result["peak_rss_bytes"] == 8192 and result["exit_code"] == 7
    assert result["memory_verification_valid"] and result["missing_rss_samples"] == 1
    assert result["guard_reason"] is None and child.waited


def test_no_sample_exit_is_unmeasured_not_zero(monkeypatch, tmp_path):
    module, child = simulated(monkeypatch, [(None, True)])
    result = module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 1)
    assert result["exit_code"] == 7 and child.waited
    assert result["peak_rss_bytes"] is None and not result["memory_verification_valid"]
    assert result["guard_reason"] == "harness_rss_unmeasured"
    assert result["rss_sample_status"] == "unmeasured"


def test_empty_windows_tree_is_not_a_measured_zero(monkeypatch, tmp_path):
    module, child = simulated(monkeypatch, [])
    child.code = 0
    monkeypatch.setattr(module, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(module, "windows_tree_peaks", lambda process, peaks: 0)
    result = module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 1)
    assert result["guard_reason"] == "harness_rss_unmeasured"
    assert result["peak_rss_bytes"] is None and not result["memory_verification_valid"]
    assert result["last_missing_reason"] == "Windows_tree_no_samples" and child.waited


def test_missing_samples_do_not_reset_deadline(monkeypatch, tmp_path):
    module, child = simulated(monkeypatch, [None] * 10, finish=False)
    result = module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 0.025)
    assert result["guard_reason"] == "harness_timeout"
    assert result["peak_rss_bytes"] is None and not result["memory_verification_valid"]
    assert result["last_missing_reason"] == "VmHWM_field_missing"
    assert child.killed and child.waited and result["elapsed_seconds"] < 0.1


def test_missing_samples_cannot_erase_measured_rss_limit(monkeypatch, tmp_path):
    module, child = simulated(monkeypatch, [8192], finish=False)
    result = module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 1, rss_limit=4096)
    assert result["guard_reason"] == "harness_peak_rss" and result["peak_rss_bytes"] == 8192
    assert child.killed and child.waited


@pytest.mark.parametrize("error", [ValueError("malformed VmHWM"), PermissionError("read denied"),
                                  RuntimeError("unexpected sampler failure")])
def test_sampling_exception_reaps_child_preserving_primary_error(monkeypatch, tmp_path, error):
    module, child = simulated(monkeypatch, [error], finish=False)
    with pytest.raises(type(error), match=str(error)) as observed:
        module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 1)
    assert observed.value is error and child.killed and child.waited


def test_failed_tree_cleanup_still_reaps_direct_child(monkeypatch, tmp_path):
    error = ValueError("original sampler error")
    module, child = simulated(monkeypatch, [error], finish=False)

    def broken_cleanup(process):
        raise OSError("tree cleanup failed")

    monkeypatch.setattr(module, "kill_tree", broken_cleanup)
    with pytest.raises(ValueError, match="original sampler error"):
        module.guarded(["owned-child"], tmp_path, tmp_path / "child.log", 1)
    assert child.killed and child.waited


@pytest.mark.parametrize("returncode", [0, 1])
def test_taskkill_return_cannot_leave_waiting_for_live_direct_child(monkeypatch, returncode):
    module, child, commands = resources(), Child(), []

    def taskkill(argv, **kwargs):
        commands.append(argv)
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(module, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(module, "subprocess", SimpleNamespace(
        run=taskkill, DEVNULL=subprocess.DEVNULL))
    module.kill_tree(child)
    assert commands == [["taskkill", "/PID", str(child.pid), "/T", "/F"]]
    assert child.killed and child.waited


def test_real_owned_child_is_reaped_after_sampler_error(monkeypatch, tmp_path):
    module, children, native_popen = resources(), [], subprocess.Popen

    def owned(*args, **kwargs):
        child = native_popen(*args, **kwargs)
        children.append(child)
        return child

    def broken(*args):
        raise ValueError("real sampler error")

    monkeypatch.setattr(module, "subprocess", SimpleNamespace(
        Popen=owned, STDOUT=subprocess.STDOUT, DEVNULL=subprocess.DEVNULL, run=subprocess.run))
    monkeypatch.setattr(module, "windows_tree_peaks" if os.name == "nt" else "peak_rss", broken)
    with pytest.raises(ValueError, match="real sampler error"):
        module.guarded([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path,
                       tmp_path / "child.log", 2)
    assert len(children) == 1 and children[0].poll() is not None


def test_current_platform_peak_uses_actual_os_measurement():
    module = resources()
    if os.name == "nt":
        from ctypes import wintypes

        module.ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        process = SimpleNamespace(_handle=module.ctypes.windll.kernel32.GetCurrentProcess())
    else:
        process = SimpleNamespace(pid=os.getpid())
        status = Path(f"/proc/{process.pid}/status").read_text()
        assert module.linux_peak_from_status(status) > 0
    assert module.peak_rss(process) > 0
