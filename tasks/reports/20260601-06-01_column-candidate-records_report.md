# Column Candidate Records Report

Task ID: 20260601-06-01

Objective:
Add immutable column-generation candidate records with deterministic canonical-key
behavior and reduced-cost convention tests.

Risk and approval:

- Risk level: L1 controlled implementation.
- Reason: the task is a narrow dataclass/protocol boundary backed by
  `notes/19_decomposition_boundary_design.md`, limited to column candidate records and
  focused tests, and does not implement solve loops, pricing logic, or LP/MIP solver
  calls.
- Mode A policy: auto-executed under the v0.3 user approval profile for L1 dataclasses
  backed by design notes and explicit acceptance criteria.

Files changed:

- `tasks/codex/20260601-06-01_column-candidate-records.md`
- `src/silo/decomposition/column_candidate.py`
- `src/silo/decomposition/__init__.py`
- `tests/unit/test_decomposition_column_candidate.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-06-01_column-candidate-records_report.md`

Implementation summary:

- Added frozen `ColumnCandidate` records with validation for deterministic column ids,
  generated variable names, finite objective coefficients, row coefficient maps, finite
  reduced costs, source pricing subproblem labels, iteration ids, tolerances, and message
  values.
- Added defensive copying and deterministic sorting for restricted-master row
  coefficient mappings.
- Added `is_improving_for(objective_sense)` with the documented convention that
  minimization improves below `-tolerance` and maximization improves above `tolerance`.
- Added `canonical_key()` behavior that is independent of column id, source pricing
  subproblem, iteration id, reduced cost, tolerance, message, and caller-provided row
  coefficient order.
- Added optional row-order support for canonical-key row coefficient ordering.
- Exported `ColumnCandidate` from `silo.decomposition`.
- Added a brief Phase 7F note to `tasks/phases/phase_07_decomposition.md`.
- No LP solver behavior was modified.
- No MIP solver behavior was modified.
- No presolve behavior was modified.
- No Phase 6 cut or callback behavior was modified.
- No public CLI behavior was modified.
- No JSON schemas were modified.
- No examples were modified or created.
- No generated output files were added.
- No column-generation solve loop was implemented.
- No pricing logic was implemented.
- No restricted-master solve behavior was implemented.
- No LP or MIP solver calls were introduced in decomposition code.

Tests added:

- Valid column candidate construction and normalization.
- Immutability at the dataclass boundary.
- Defensive copying and deterministic ordering of row coefficients.
- Rejection of invalid column ids.
- Rejection of invalid variable names.
- Rejection of empty row coefficient mappings.
- Rejection of empty row names.
- Rejection of nonfinite row coefficients.
- Rejection of all-zero row coefficient vectors.
- Rejection of nonfinite objective coefficients.
- Rejection of nonfinite reduced costs.
- Rejection of invalid source pricing subproblem labels.
- Rejection of invalid iteration ids.
- Rejection of nonpositive or nonfinite tolerances.
- Rejection of invalid message values.
- Reduced-cost convention coverage for minimization, maximization, and tolerance
  boundaries.
- Rejection of invalid objective sense values in reduced-cost convention checks.
- Canonical-key independence from nonmathematical metadata and input row order.
- Canonical-key ordering with an explicit row order.
- Public exports from `silo.decomposition`.
- Confirmation that placeholder `ColumnGenerationSolver().solve(model)` remains
  `SolverStatus.NOT_SOLVED`.

Checks run:

- `git status --short`
- `pytest tests/unit/test_decomposition_column_candidate.py`
- `python scripts/check_quality.py`
- `git diff --check`

Results:

- Targeted column candidate record tests passed with 39 tests.
- Full quality check passed with 649 tests and ruff checks.
- `git diff --check` passed.
- Scope lock held: only the allowed implementation, export, test, phase-note, task, and
  report files were changed for this task.

Git status before:

```text
## main...origin/main
?? tasks/codex/20260524-12-01.md
```

Git status after:

```text
 M src/silo/decomposition/__init__.py
 M tasks/phases/phase_07_decomposition.md
?? src/silo/decomposition/column_candidate.py
?? tasks/codex/20260524-12-01.md
?? tasks/codex/20260601-06-01_column-candidate-records.md
?? tasks/reports/20260601-06-01_column-candidate-records_report.md
?? tests/unit/test_decomposition_column_candidate.py
```

Local commit hash:

```text
Created locally; the final response records the amended commit hash.
```

Push attempted:

```text
Yes. Push was attempted twice after the local commit was created, but both attempts failed
before remote synchronization:

1. `fatal: unable to access 'https://github.com/exoplanetX/silo.git/': Recv failure:
   Connection was reset`
2. `fatal: unable to access 'https://github.com/exoplanetX/silo.git/': Failed to connect
   to github.com port 443 after 21083 ms: Couldn't connect to server`
```

Issues or conflicts:

- The user-supplied temporary task input `tasks/codex/20260524-12-01.md` remains
  untracked. It was not edited, deleted, renamed, staged, or committed.
- No unrelated tracked dirty changes blocked this task.
- Push did not complete because the local environment could not connect reliably to
  GitHub over HTTPS. The local commit was preserved.

Next recommended atomic task:

Add a no-op decomposition driver boundary that records one deterministic iteration and
does not call LP or MIP solvers, implement Benders or column-generation solve loops,
change CLI behavior, change JSON schemas, create examples, or add generated output files.
