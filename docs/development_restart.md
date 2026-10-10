# Development Restart — 2026-10-10

SILO remains a Python educational reference solver. Phase 0–8 closure applies to each phase's conservative scope. Phase 9 is open/parked with native implementation deferred; Phase 10 has not started.

## Current authorized maintenance

The user approved baseline organization followed by two separate status-correctness repairs on 2026-10-10. Execute one atomic task/commit at a time: baseline, presolve infeasible-vs-unbounded, then MIP unbounded-relaxation handling. No push, native implementation or phase transition is included. Local-ahead state within this explicit sequence is expected.

The 2026-10-10 audit reproduced two defects despite 975 existing tests passing: an improving empty column can mask infeasible nonempty constraints in presolve, and LP-relaxation unboundedness can mask integer infeasibility in branch-and-bound. The separate presolve and MIP repairs now address both defects; matching task reports record red/green regression evidence and final checks.

## Reading order

1. `.silo-dos/project_profile.md` and `.silo-dos/technical_route.md` for the current route.
2. `tasks/reports/20261010-*` for current execution evidence.
3. `notes/25_native_implementation_defer_decision.md` for the native decision.
4. `tasks/README.md` before issuing/executing further tasks.

## Local historical archive

`resfs/` contains historical discussion sources and is intentionally ignored by Git. Its originals remain in place, unchanged. The v1 guide refers to operator v0.3 and must be read as history; current operator behavior is v0.4. Old command and approval templates do not authorize new work. These local files are not backed up by a Git push.

| Original file | Bytes | SHA-256 |
|---|---:|---|
| `SILO-DOS v0.4-需求讨论.md` | 13815 | `0be3002c121867c4ad9ace758c1003501182789f79ef5f470363e92415344155` |
| `silo_dos_操作指南_v_1.md` | 20908 | `49dab79e3e8e84412bea24f172b005b00a40e482087ea0146ce4e7881902b822` |
| `SILO开发流程优化.md` | 236436 | `f59286bd4ec47283512340c6f0eb0be5134ab01cd220974dceebcc8cb6c4f91b` |

## Development environment

Use a project virtual environment and install the package so console-script regression tests can find `silo`:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$env:PATH = (Join-Path $PWD '.venv\Scripts') + ';' + $env:PATH
& .\.venv\Scripts\python.exe scripts/check_quality.py
```

For this recovery, `.venv` was created with `--system-site-packages` and the existing package installed using `--no-deps --no-build-isolation`; host dependencies were reused without changing dependency/build declarations. This isolates the package entrypoint but is not a fully locked clean-room environment. Python 3.13.9, NumPy 2.3.5 and pytest 8.4.2 were present. Tool versions and test results are recorded in the baseline report.

## Boundaries

Cuts/callbacks are conservative interfaces; complete Benders/column-generation solvers are not implemented. Uncertainty supports only tiny transformations. Avoid interpreting phase completion as production algorithm coverage. Historical task-ID collisions remain recorded debt; preserve immutable contracts.

## Follow-up correctness baseline — 2026-10-10

The user subsequently requested synchronization and the recommended independent
baseline. The recovery commits through a4814f4 were successfully pushed to GitHub,
then task `20261010-04-01_correctness-oracles` established the test-only baseline in
`tests/verification/`. See [correctness baseline](correctness_baseline.md) for exact
coverage, optional SciPy requirements, independent reference methods and limits.
This follow-up has its own local commit and execution report; it does not change
solver algorithms, phase status or the native defer decision.
