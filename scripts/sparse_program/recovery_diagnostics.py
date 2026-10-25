"""RR02 bounded, read-only prefix observations; run under the outer OS tree guard.

Example: python scripts/sparse_program/recovery_diagnostics.py --mode eta
  --output outputs/sparse_lp_program_20261024/diagnostics/rr02-eta-01
This entry never reads or imports oracles, changes a pivot, or updates the ledger.
The no-updates trajectory is a separate intervention, not a same-B paired probe.
"""

from time import perf_counter

ENTRY_TIME = perf_counter()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import traceback  # noqa: E402
from dataclasses import asdict  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from pathlib import Path  # noqa: E402

for _variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_variable] = "1"

import numpy as np  # noqa: E402
from scipy.sparse import csc_matrix  # noqa: E402
from scipy.sparse.linalg import splu  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CASES = ("CAP-FLOW-01", "CAP-TRANS-01")


class PrefixStop(BaseException):
    """Explicit observer stop, never a completed native optimization result."""


class ObserverFailure(BaseException):
    """Do not let a diagnostic fault become a native numerical/resource result."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(
        json.dumps(clean(value), allow_nan=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def check_time(deadline, clock=None):
    if (perf_counter if clock is None else clock)() >= deadline:
        raise PrefixStop("observer_deadline")


def norm(value):
    return float(np.max(np.abs(value), initial=0))


def candidate(xb, direction, position, primal_tolerance):
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        rho = float(xb[position] / direction[position])
        y = xb - rho * direction
        y[position] = rho
        size, minimum = norm(y), float(np.min(y, initial=0))
        threshold = primal_tolerance * (1 + size)
    finite = bool(
        np.isfinite(xb).all()
        and np.isfinite(direction).all()
        and np.isfinite(y).all()
        and np.isfinite([rho, size, threshold]).all()
    )
    return y, {
        "rho": rho,
        "minimum": minimum,
        "norm": size,
        "ptol": threshold,
        "finite": finite,
        "algebraic_feasible": finite and minimum >= -threshold,
    }


def blockers(xb, direction, primal_tolerance, pivot_tolerance, deadline=float("inf")):
    """All d>0 rows, using O(m) storage; alternatives are observational only.

    Each candidate is checked in its NEW basis coordinates. A deadline can leave
    candidate summaries partial, while the complete positive blocker set remains.
    """
    positions = np.flatnonzero(direction > 0)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        rho = xb[positions] / direction[positions]
        selected_ratio = np.maximum(xb[positions], 0) / direction[positions]
        relative = abs(direction[positions]) / (1 + norm(direction))
    count = len(positions)
    safe = np.isfinite(direction).all() & (relative > pivot_tolerance)
    arrays = {
        "positions": positions,
        "rho": rho,
        "clamped_ratio": selected_ratio,
        "relative_pivot": relative,
        "pivot_safe": safe,
        **{
            name: np.full(count, np.nan)
            for name in ("candidate_min", "candidate_norm", "candidate_ptol")
        },
        "candidate_finite": np.zeros(count, dtype=bool),
        "candidate_feasible": np.zeros(count, dtype=bool),
        "candidate_examined": np.zeros(count, dtype=bool),
    }
    minimum = float(np.min(selected_ratio)) if count else None
    alternatives, stable_count, examined = [], 0, 0
    for k, position in enumerate(positions):
        if perf_counter() >= deadline:
            break
        _, info = candidate(xb, direction, int(position), primal_tolerance)
        arrays["candidate_min"][k], arrays["candidate_norm"][k], arrays["candidate_ptol"][k] = (
            info["minimum"],
            info["norm"],
            info["ptol"],
        )
        arrays["candidate_finite"][k] = info["finite"]
        arrays["candidate_feasible"][k] = info["algebraic_feasible"]
        arrays["candidate_examined"][k] = True
        examined += 1
        if safe[k] and info["algebraic_feasible"] and selected_ratio[k] > minimum:
            stable_count += 1
            if len(alternatives) < 8:
                alternatives.append(
                    {
                        "position": int(position),
                        "clamped_ratio": float(selected_ratio[k]),
                        "relative_pivot": float(relative[k]),
                        **info,
                    }
                )
    tied = np.flatnonzero(selected_ratio == minimum) if count else np.array([], dtype=int)
    return arrays, {
        "strictly_positive_rows": count,
        "candidate_rows_examined": examined,
        "all_candidates_examined": examined == count,
        "minimum_clamped_ratio": minimum,
        "true_minimal_positions": positions[tied].tolist(),
        "all_true_minimal_pivots_unsafe": bool(count and not np.any(safe[tied])),
        "stable_feasible_nonminimal_count": stable_count,
        "stable_feasible_nonminimal_first8": alternatives,
    }


def backward(matrix, rhs, value, transpose=False):
    matrix = matrix.T if transpose else matrix
    residual = rhs - matrix @ value
    denominator = 1 + norm(rhs) + norm(abs(matrix) @ abs(value))
    return {
        "residual_inf": norm(residual),
        "denominator": denominator,
        "normalized_residual": norm(residual) / denominator,
        "factor_bound": 1e-10 * denominator,
    }


def load_input(root, identifier):
    """Only manifest and its SHA-bound payload are read; no reference file."""
    path = root / "tests/fixtures/sparse_program_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entry = next(e for e in manifest["cases"] if e["id"] == identifier)
    payload_path = (root / entry["payload_path"]).resolve()
    if not payload_path.is_relative_to(root.resolve()):
        raise ValueError("Payload escaped repository")
    if sha(payload_path) != entry["payload_sha256"]:
        raise ValueError("Frozen payload SHA mismatch")
    return (
        json.loads(payload_path.read_text(encoding="utf-8")),
        dict(entry.get("options", {})),
        {
            "manifest_path": str(path),
            "manifest_sha256": sha(path),
            "payload_path": str(payload_path),
            "payload_sha256": entry["payload_sha256"],
        },
    )


def source_identity(root):
    paths = [*sorted((root / "src/silo").rglob("*.py")), root / "pyproject.toml"]
    source = {p.relative_to(root).as_posix(): sha(p) for p in paths}
    digest = hashlib.sha256(
        json.dumps(source, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=2
        ).strip(),
        "source": source,
        "source_sha256": digest,
        "observer_sha256": sha(__file__),
    }


def run_frame(frame):
    while frame is not None:
        if (
            frame.f_code.co_name == "run"
            and frame.f_globals.get("__name__") == "silo.lp.sparse_kernel"
        ):
            return frame
        frame = frame.f_back
    return None


def factor_from_frame(frame):
    function = frame.f_locals["get_factor"]
    # Never call get_factor(): observing must not construct or reconfigure a LU.
    return dict(
        zip(
            function.__code__.co_freevars,
            (c.cell_contents for c in function.__closure__),
            strict=True,
        )
    )["factor"]


def signature(frame):
    values, factor = frame.f_locals, factor_from_frame(frame)
    outer = canonical_frame(frame)
    return (
        values["run_identity"],
        outer.f_locals["run_number"],
        values["iterations"],
        tuple(values["keys"][j] for j in values["basis"]),
        factor.generation,
        values["generation"],
        id(values["a"]),
    )


def canonical_frame(frame):
    outer = frame.f_back
    while outer is not None and outer.f_code.co_name != "solve_canonical":
        outer = outer.f_back
    if outer is None:
        raise ValueError("Missing canonical frame")
    return outer


def state_from_frame(frame, position):
    values, factor = frame.f_locals, factor_from_frame(frame)
    matrix, entering, basis, keys = values["a"], values["entering"], values["basis"], values["keys"]
    outer = canonical_frame(frame)
    canonical = outer.f_locals
    column = np.zeros(matrix.shape[0])
    lo, hi = matrix.indptr[entering : entering + 2]
    column[matrix.indices[lo:hi]] = matrix.data[lo:hi]
    row_map = np.array(canonical["row_map"], dtype=int)
    normalized = canonical["norm"]
    return {
        "B": factor.matrix,
        "b": values["b"],
        "xb": values["xb"],
        "d": values["direction"],
        "dual": values["lam"],
        "rc": values["rc"],
        "working_cost": values["cost"],
        "standard_cost": canonical["c"],
        "cB": values["cost"][basis],
        "entering_column": column,
        "row_scale": normalized.row_scale[row_map],
        "row_flips": canonical["flips"][row_map],
        "col_scale": normalized.col_scale,
        "row_map": row_map,
        "meta": {
            "basis_indices": tuple(basis),
            "basis_keys": tuple(keys[j] for j in basis),
            "column_keys": keys,
            "row_keys": canonical["row_keys"],
            "column_origins": normalized.column_origins,
            "entering_index": entering,
            "entering_key": keys[entering],
            "trigger_position": position,
            "iterations": values["iterations"],
            "phase": values["run_identity"][1],
            "run_identity": values["run_identity"],
            "generation": factor.generation,
            "state_generation": values["generation"],
            "primal_tolerance": values["options"].primal_tolerance,
            "pivot_tolerance": values["options"].pivot_tolerance,
            "eta_chain_length": len(factor.etas),
            "native_factor_nnz": factor._lu_nnz,
            "native_counters": clean(factor.counters),
            "pricing_bland": values["pricing"].bland,
            "pricing_degenerate": values["pricing"].degenerate,
            "pricing_visited_count": len(values["pricing"].visited),
            "current_rejected_entering": sorted(values["rejected"]),
        },
    }


class Recorder:
    """Three sparse states and one live caller frame at most, with durable costs."""

    def __init__(self, output, deadline, identifier, probe_lu=splu):
        self.output, self.deadline, self.identifier, self.probe_lu = (
            output,
            deadline,
            identifier,
            probe_lu,
        )
        self.snapshots, self.slots, self.counts = [], set(), {}
        self.last_frame, self.last_signature, self.last_position = None, None, None
        self.terminal_unavailable_reason = None

    def event(self, name):
        self.counts[name] = self.counts.get(name, 0) + 1
        with (self.output / "calls.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(
                    {
                        "event": name,
                        "at_seconds": perf_counter() - ENTRY_TIME,
                        "number": self.counts[name],
                    }
                )
                + "\n"
            )

    def checkpoint(self):
        write_json(
            self.output / "prefix.json",
            {
                "case": self.identifier,
                "snapshots": self.snapshots,
                "counts": self.counts,
                "oracle_reads": 0,
            },
        )

    def capture(self, kind, state):
        if kind in self.slots or len(self.snapshots) >= 3:
            return None
        check_time(self.deadline)
        started = perf_counter()
        matrix = csc_matrix(state["B"], copy=True)
        vectors = {
            name: np.array(value, copy=True)
            for name, value in state.items()
            if name not in ("B", "meta")
        }
        number = len(self.snapshots)
        raw_path = self.output / f"state-{number}.npz"
        np.savez(
            raw_path,
            B_shape=np.array(matrix.shape),
            B_indptr=matrix.indptr,
            B_indices=matrix.indices,
            B_data=matrix.data,
            **vectors,
        )
        meta = {
            "kind": kind,
            **state["meta"],
            "state_path": raw_path.name,
            "state_sha256": sha(raw_path),
            "capture_started_seconds": started - ENTRY_TIME,
            "probe_status": "not_started",
            "observational_only": True,
            "candidate_coordinate_rule": "y=xB-rho*d; y[r]=rho",
        }
        self.slots.add(kind)
        self.snapshots.append(meta)
        self.checkpoint()  # Raw CSC/vectors survive a deadline in analysis or LU.
        try:
            arrays, meta["blockers"] = blockers(
                vectors["xb"],
                vectors["d"],
                meta["primal_tolerance"],
                meta["pivot_tolerance"],
                self.deadline,
            )
            block_path = self.output / f"state-{number}-blockers.npz"
            np.savez(block_path, **arrays)
            meta["blockers_path"], meta["blockers_sha256"] = block_path.name, sha(block_path)
            position = meta["trigger_position"]
            _, meta["trigger_raw_candidate"] = candidate(
                vectors["xb"], vectors["d"], position, meta["primal_tolerance"]
            )
            meta["current_state_residual"] = backward(matrix, vectors["b"], vectors["xb"])
            meta["current_dual_residual"] = backward(matrix, vectors["cB"], vectors["dual"], True)
            meta["current_direction_residual"] = backward(
                matrix, vectors["entering_column"], vectors["d"]
            )
            row_contribution = abs(matrix) @ abs(vectors["xb"])
            with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                meta["undo_row_scale_contribution_inf"] = norm(
                    row_contribution / abs(vectors["row_scale"])
                )
            meta["original_scale_note"] = (
                "Undo row_scale only; affine/original-space proof remains external."
            )
            self.checkpoint()
            check_time(self.deadline)
            self.event("probe_lu_started")
            direct = self.probe_lu(matrix, permc_spec="COLAMD")
            self.event("probe_lu_completed")
            meta["probe_factor_nnz"] = int(direct.L.nnz + direct.U.nnz)
            meta["probe_plus_owner_factor_nnz"] = (
                meta["native_factor_nnz"] + meta["probe_factor_nnz"]
            )
            check_time(self.deadline)
            probe = {}
            for name, rhs, trans in (
                ("xb", vectors["b"], "N"),
                ("dual", vectors["cB"], "T"),
                ("d", vectors["entering_column"], "N"),
            ):
                check_time(self.deadline)
                self.event(f"probe_{name}_started")
                value = direct.solve(rhs, trans=trans)
                self.event(f"probe_{name}_completed")
                probe[name] = value
                meta[f"probe_{name}_difference_inf"] = norm(value - vectors[name])
                meta[f"probe_{name}_residual"] = backward(matrix, rhs, value, trans == "T")
                check_time(self.deadline)
            probe_path = self.output / f"state-{number}-probe.npz"
            np.savez(probe_path, **probe)
            meta["probe_path"], meta["probe_sha256"] = probe_path.name, sha(probe_path)
            meta["probe_status"] = "completed_same_B_independent_sparse_LU"
        except PrefixStop:
            meta["probe_status"] = "observer_deadline_partial"
            raise
        except (RuntimeError, MemoryError) as exc:
            meta["probe_status"], meta["probe_error"] = "probe_failed", repr(exc)
        finally:
            meta["capture_seconds_including_probes"] = perf_counter() - started
            self.checkpoint()
        return meta

    def observe(self, frame, position, kind=None):
        check_time(self.deadline)
        if frame is None or frame.f_locals.get("mode") != "primal":
            return
        self.last_frame, self.last_signature, self.last_position = frame, signature(frame), position
        if kind is None:
            return
        values = frame.f_locals
        if kind in self.slots:
            latest = max(s["iterations"] for s in self.snapshots)
            if (
                len(self.snapshots) != 2
                or values["run_identity"][1] != "phase_two"
                or values["iterations"] <= latest
            ):
                return
            kind = "later_phase_two_harmful"
        self.capture(kind, state_from_frame(frame, position))
        if len(self.snapshots) == 3:
            raise PrefixStop("three_sparse_snapshots_captured")

    def terminal(self):
        frame = self.last_frame
        if len(self.snapshots) == 3:
            return
        if frame is None:
            self.terminal_unavailable_reason = "no_observed_primal_frame"
        elif factor_from_frame(frame) is None:
            self.terminal_unavailable_reason = "factor_cleared_after_observation"
        elif signature(frame) != self.last_signature:
            self.terminal_unavailable_reason = "basis_phase_or_generation_changed_after_observation"
        else:
            self.capture("terminal_coherent_state", state_from_frame(frame, self.last_position))


class Hooks:
    """Original results are returned by identity; probes cannot feed decisions."""

    def __init__(self, recorder, kernel, factor):
        self.recorder, self.kernel, self.factor = recorder, kernel, factor

    def __enter__(self):
        self.original = (
            self.kernel.pivot_safe,
            self.kernel._raw_primal_candidate,
            self.kernel.solve_canonical,
            self.factor.splu,
        )
        safe, raw, kernel, native_lu = self.original
        recorder = self.recorder

        def observed_safe(direction, position, tolerance):
            result = safe(direction, position, tolerance)
            caller = inspect.currentframe().f_back
            try:
                frame = run_frame(caller)
                kind = None
                if frame is not None and not result:
                    values = frame.f_locals
                    positive = np.flatnonzero(direction > 0)
                    ratios = np.maximum(values["xb"][positive], 0) / direction[positive]
                    ties = positive[ratios == np.min(ratios)] if len(positive) else []
                    if len(ties) and (
                        not np.isfinite(direction).all()
                        or not np.any(abs(direction[ties]) > tolerance * (1 + norm(direction)))
                    ):
                        kind = "first_unsafe_true_minimal_blocker"
                recorder.observe(frame, position, kind)
            except Exception as exc:
                raise ObserverFailure("Observer predicate failed") from exc
            finally:
                del caller
            return result

        def observed_raw(*args, **kwargs):
            result = raw(*args, **kwargs)
            caller = inspect.currentframe().f_back
            try:
                kind = (
                    "first_negative_rho_or_raw_amplification"
                    if result["rho"] < 0 or not result["valid"]
                    else None
                )
                recorder.observe(
                    run_frame(caller), args[2] if len(args) > 2 else kwargs["leaving"], kind
                )
            except Exception as exc:
                raise ObserverFailure("Observer raw-candidate capture failed") from exc
            finally:
                del caller
            return result

        def observed_kernel(*args, **kwargs):
            recorder.event("native_kernel_started")
            result = kernel(*args, **kwargs)
            recorder.event("native_kernel_completed")
            return result

        def observed_lu(*args, **kwargs):
            recorder.event("native_lu_started")
            result = native_lu(*args, **kwargs)
            recorder.event("native_lu_completed")
            return result

        self.kernel.pivot_safe, self.kernel._raw_primal_candidate = observed_safe, observed_raw
        self.kernel.solve_canonical, self.factor.splu = observed_kernel, observed_lu
        return self

    def __exit__(self, *args):
        (
            self.kernel.pivot_safe,
            self.kernel._raw_primal_candidate,
            self.kernel.solve_canonical,
            self.factor.splu,
        ) = self.original
        self.recorder.last_frame = None


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--output", type=Path, required=True)
    value.add_argument("--mode", choices=("eta", "no-updates"))
    value.add_argument("--max-factor-updates", type=int, choices=(0, 20))
    value.add_argument("--case", action="append", choices=CASES)
    value.add_argument("--seconds", type=float, default=55)
    value.add_argument("--case-seconds", type=float, default=25)
    return value


def main(argv=None):
    args = parser().parse_args(argv)
    if not 0 < args.seconds <= 55 or not 0 < args.case_seconds <= 25:
        raise ValueError(
            "Internal budget must be <=55s, each case <=25s; outer OS guard is required"
        )
    mode = args.mode or ("no-updates" if args.max_factor_updates == 0 else "eta")
    updates = 0 if mode == "no-updates" else 20
    if args.max_factor_updates is not None and args.max_factor_updates != updates:
        raise ValueError("Conflicting diagnostic mode/update limit")
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "outputs/sparse_lp_program_20261024/diagnostics"):
        raise ValueError("Use a new directory in this program's diagnostics root")
    output.mkdir(parents=True, exist_ok=True)
    if any((output / name).exists() for name in ("batch.json", "batch.json.partial", *CASES)):
        raise FileExistsError("Observer files already exist; choose a new output directory")
    deadline = ENTRY_TIME + args.seconds
    batch = {
        "mode": mode,
        "max_factor_updates": updates,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "seconds_including_import_limit": args.seconds,
        "cases": [],
        "oracle_reads": 0,
        "comparison_scope": (
            "paired same-B independent sparse LU; no-updates is a separate trajectory"
        ),
        "module_import_seconds": perf_counter() - ENTRY_TIME,
        "status": "started",
    }
    write_json(output / "batch.json", batch)
    try:
        check_time(deadline)
        batch["source_identity"] = source_identity(ROOT)
        sys.path.insert(0, str(ROOT / "src"))
        import scipy.optimize

        from silo import SolveOptions, solve
        from silo.io import model_from_dict
        from silo.lp import sparse_factor, sparse_kernel

        def forbidden_optimizer(*args, **kwargs):
            raise AssertionError("External optimizer called during native prefix observation")

        scipy.optimize.linprog = scipy.optimize.milp = forbidden_optimizer

        batch["native_import_finished_seconds"] = perf_counter() - ENTRY_TIME
        for identifier in dict.fromkeys(args.case or CASES):
            check_time(deadline - 2)
            case_started = perf_counter()
            case_deadline = min(deadline - 2, case_started + args.case_seconds)
            folder = output / identifier
            folder.mkdir()
            recorder = Recorder(folder, case_deadline, identifier)
            packet = {
                "id": identifier,
                "status": "started",
                "prefix_stopped": False,
                "result": None,
                "options": None,
            }
            batch["cases"].append(packet)
            write_json(folder / "case.json", packet)
            try:
                payload, options, packet["input_identity"] = load_input(ROOT, identifier)
                options.update(
                    lp_engine="sparse",
                    max_factor_updates=updates,
                    time_limit=max(
                        0, min(options.get("time_limit", 120), case_deadline - perf_counter() - 1)
                    ),
                )
                model, native_options = model_from_dict(payload), SolveOptions(**options)
                packet["options"] = asdict(native_options)
                write_json(folder / "case.json", packet)
                with Hooks(recorder, sparse_kernel, sparse_factor):
                    recorder.event("public_solve_started")
                    result = solve(model, native_options)
                    recorder.event("public_solve_completed")
                    packet["result"] = result.to_dict()
                    packet["status"] = "public_solve_returned"
                    recorder.terminal()
            except PrefixStop as exc:
                packet["prefix_stopped"], packet["stop_reason"] = True, str(exc)
                packet["status"] = "observed_prefix_only"
                # Never publish a prefix as completed optimal, even if the
                # deadline fired during optional observations after the solve.
                if packet["result"] is not None:
                    packet["public_return_before_observer_stop"] = packet["result"]
                packet["result"] = None
            finally:
                recorder.last_frame = None
                packet.update(
                    elapsed_seconds_including_observations=perf_counter() - case_started,
                    counts=recorder.counts,
                    snapshots=recorder.snapshots,
                    prefix_coverage={
                        "first_unsafe_observed": "first_unsafe_true_minimal_blocker"
                        in recorder.slots,
                        "negative_rho_or_raw_failure_observed": (
                            "first_negative_rho_or_raw_amplification" in recorder.slots
                        ),
                        "later_or_terminal_observed": bool(
                            recorder.slots & {"later_phase_two_harmful", "terminal_coherent_state"}
                        ),
                        "absence_of_unobserved_mechanisms_proven": False,
                        "terminal_unavailable_reason": recorder.terminal_unavailable_reason,
                    },
                )
                write_json(folder / "case.json", packet)
                write_json(output / "batch.json", batch)
        batch["status"] = "diagnostic_batch_finished"
        batch["source_identity_unchanged"] = (
            source_identity(ROOT)["source_sha256"] == batch["source_identity"]["source_sha256"]
        )
    except PrefixStop as exc:
        batch["status"], batch["stop_reason"] = "batch_deadline_prefix", str(exc)
    except BaseException:
        batch["status"], batch["exception"] = "failed", traceback.format_exc()
        raise
    finally:
        batch["elapsed_seconds_including_import"] = perf_counter() - ENTRY_TIME
        write_json(output / "batch.json", batch)
    print(
        json.dumps(
            {
                "output": str(output),
                "status": batch["status"],
                "elapsed_seconds_including_import": batch["elapsed_seconds_including_import"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
