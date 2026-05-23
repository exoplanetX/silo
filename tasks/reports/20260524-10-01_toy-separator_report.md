# Deterministic Toy Separator Report

Task ID: 20260524-10-01

Objective:
Add one deterministic toy separator for a tiny fixture, with explicit validity
documentation and no performance claims.

Risk classification:

- L1 controlled implementation.
- Reason: the task is narrow, backed by the Phase 6A design note, limited to the `cuts`
  layer and deterministic tests, and does not modify branch-and-bound behavior, LP
  solvers, presolve, CLI behavior, or JSON schemas.

Files changed:

- `tasks/codex/20260524-10-01_toy-separator.md`
- `src/silo/cuts/separator.py`
- `src/silo/cuts/__init__.py`
- `tests/unit/test_toy_separator.py`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-10-01_toy-separator_report.md`

Implementation summary:

- Added `ToyUpperBoundSeparator`.
- The toy separator emits at most one global `CutCandidate`.
- The emitted cut has coefficient `{variable_name: 1.0}`, sense `<=`, and the configured
  upper-bound RHS.
- The separator emits a cut only when the configured variable is present in relaxation
  values and exceeds the configured upper bound by more than tolerance.
- The cut metadata includes deterministic source, cut id, tolerance, global scope, and a
  validity message stating that the cut is valid only for fixtures where the bound is
  documented as globally valid.
- Exported `ToyUpperBoundSeparator` from `silo.cuts`.
- Added a brief Phase 6G note to `tasks/phases/phase_06_cut_callbacks.md`.

Tests added:

- `ToyUpperBoundSeparator` satisfies the separator protocol.
- It returns no cuts when the relaxation value is absent.
- It returns no cuts when the relaxation value is within tolerance.
- It returns exactly one deterministic global cut when violated.
- The emitted cut has stable coefficients, sense, RHS, source, cut id, validity scope,
  tolerance, validity message, and canonical key.
- Repeated separation returns stable canonical keys and cut ids.
- Missing context variables and invalid contexts are rejected.
- Invalid configuration values are rejected.
- Public exports from `silo.cuts` include the toy separator.

Checks run:

- `git status --short`
- `pytest tests/unit/test_toy_separator.py`
- `git diff --check`
- `python scripts/check_quality.py`
- `git diff --check`

Results:

- Targeted toy separator tests passed with 15 tests.
- Full quality check passed with 539 tests and ruff checks.
- `git diff --check` passed.
- No branch-and-bound search logic was modified.
- No MIP node ordering, pruning, branching, or incumbent behavior was modified.
- No LP solver or presolve behavior was modified.
- No cuts were materialized into LP relaxations.
- No broad cut generation family was implemented.
- No performance claims were added.
- No CLI behavior was changed.
- No JSON schemas were changed.
- No examples were changed.
- No additional Phase 6 task was issued or executed.

Deviations from scope:

- None.

Git status before execution:

```text
## main...origin/main
```

Git status after implementation before report:

```text
 M src/silo/cuts/__init__.py
 M src/silo/cuts/separator.py
 M tasks/phases/phase_06_cut_callbacks.md
?? tasks/codex/20260524-10-01_toy-separator.md
?? tests/unit/test_toy_separator.py
```

Local commit hash:

```text
Created after this report is staged; the final response records the final commit hash.
```

Push attempted:

```text
Pending final push attempt because the task Git mode is `push-on-success`; the final
response records whether push completed or failed.
```

Unresolved issues:

- None for this atomic task.

Next recommended atomic task:

Run a Phase 6 completion audit to decide whether the current conservative cut/callback
boundary is ready for closure review or needs one final documentation pass.
