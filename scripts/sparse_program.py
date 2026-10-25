"""Fixed, budgeted execution entry for SILO-SPARSE-LP-20261024.

Validation subprocesses stay under one accounting parent and one new output root.
Only explicit native workers import the product. Data recipes import no solver.
"""

import argparse
import json
import os
import sys
from pathlib import Path

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from sparse_program import ledger  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--internal", action="store_true", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    internal = sub.add_parser("_preflight")
    internal.add_argument("--output", required=True)
    native = sub.add_parser("_native-one")
    native.add_argument("--request", required=True)
    native.add_argument("--response", required=True)
    warm_worker = sub.add_parser("_warm-one")
    warm_worker.add_argument("--request", required=True)
    warm_worker.add_argument("--response", required=True)
    sub.add_parser("freeze-inputs")
    sub.add_parser("check-inputs")
    baseline = sub.add_parser("baseline")
    baseline.add_argument("--engine", choices=("dense",), required=True)
    baseline.add_argument("--cohort", choices=("overlap",), required=True)
    run = sub.add_parser("run")
    run.add_argument(
        "--group",
        required=True,
        choices=(
            "tiny",
            "pressure",
            "sp2-smoke",
            "mechanism",
            "capacity",
            "netlib",
            "mip-cg",
            "historical",
        ),
    )
    run.add_argument("--engine", choices=("dense", "sparse"), default="sparse")
    run.add_argument(
        "--stage", choices=("SP2", "SP3", "SP4"), help="Charge an explicit final recheck stage"
    )
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--stage", choices=("SP1", "SP2", "SP3", "SP4"), required=True)
    warm = sub.add_parser("warm")
    warm.add_argument("--round", type=int, choices=(1, 2, 3), required=True)
    warm.add_argument("--repetitions", type=int, choices=(5,), required=True)
    install = sub.add_parser("install-checks")
    install.add_argument("--candidate", choices=("0.3.0a1",), required=True)
    summary = sub.add_parser("summary")
    summary.add_argument("--final", action="store_true")
    args = parser.parse_args()
    if args.command == "_native-one":
        from sparse_program.runner import native_one

        return native_one(args.request, args.response)
    if args.command == "_warm-one":
        from sparse_program.warm import one

        return one(args.request, args.response)
    if args.command == "_preflight":
        from sparse_program.preflight import main as preflight

        preflight(args.output)
        return 0
    if args.command == "preflight":
        return ledger.command(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "_preflight",
                "--output",
                str(ledger.OUT / "preflight.json"),
            ],
            stage="SP1",
            group="preflight",
            timeout=60,
        )
    if args.command == "summary" and not args.final:
        print(json.dumps(ledger.totals(), indent=2))
        return 0
    if not args.internal:
        if args.command in ("freeze-inputs", "check-inputs", "baseline"):
            stage = "SP1"
        elif args.command == "warm":
            stage = "SP3"
        elif args.command == "evaluate":
            stage = args.stage
        elif args.command in ("install-checks", "summary"):
            stage = "SP4"
        else:
            stage = getattr(args, "stage", None) or (
                "SP2"
                if args.group in ("tiny", "pressure", "sp2-smoke")
                else "SP3"
                if args.group == "mechanism"
                else "SP4"
            )
        group = getattr(args, "group", args.command)
        timeout = {
            "baseline": 980,
            "warm": 4800,
            "install-checks": 1200,
            "evaluate": 300,
            "summary": 300,
            "run": {
                "tiny": 500,
                "pressure": 260,
                "sp2-smoke": 740,
                "mechanism": 500,
                "capacity": 1460,
                "netlib": 1460,
                "mip-cg": 980,
                "historical": 1200,
            }.get(group, 60),
        }.get(args.command, 60)
        return ledger.command(
            [sys.executable, str(Path(__file__).resolve()), "--internal", *sys.argv[1:]],
            stage=stage,
            group=group,
            timeout=timeout,
            reserve_round=group in ("capacity", "netlib", "warm"),
        )
    if args.command == "freeze-inputs":
        from sparse_program.cases import write_input_freeze

        frozen = write_input_freeze(ledger.ROOT)
        print(
            json.dumps(
                {"fixed_cases": len(frozen["cases"]), "trajectories": len(frozen["trajectories"])}
            )
        )
        return 0
    if args.command == "summary":
        print(json.dumps(ledger.totals(), indent=2))
        if args.final:
            from sparse_program.evaluation import final

            return final()
        return 0
    from sparse_program.runner import dispatch

    return dispatch(args)


if __name__ == "__main__":
    raise SystemExit(main())
