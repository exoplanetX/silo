# Phase 6 Cut and Callback Design Report

Task ID: 20260524-04-01

Objective:
Draft a conservative Phase 6 design note for cut generation and callback boundaries that
can later guide implementation without disrupting the pure branch-and-bound path.

Files changed:

- `tasks/codex/20260524-04-01_phase6-cut-callback-design.md`
- `notes/18_cut_callback_boundary_design.md`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-04-01_phase6-cut-callback-design_report.md`

Design decisions:

- Created `notes/18_cut_callback_boundary_design.md` as the Phase 6A design note.
- Preserved pure branch-and-bound as the default behavior.
- Stated that cuts must be optional and disabled by default.
- Preserved the dependency direction
  `core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty`.
- Stated that native algorithms must not call external solvers.
- Defined cuts as linear constraints with documented validity scope.
- Distinguished globally valid cuts from node-local cuts.
- Listed proposed cut metadata, including deterministic id/source key, coefficients,
  sense, RHS, validity scope, separator name, optional node id, tolerance, message, and
  activity state.
- Defined separators as read-only components that inspect model/solution context and
  return candidate cuts without mutating core model state.
- Recommended starting with a no-op separator or deterministic toy separator before real
  cut families.
- Defined the cut-pool lifecycle for validation, duplicate detection, deterministic
  activation, and clearing of expired node-local cuts.
- Defined callback hook points and read-only observation boundaries.
- Stated that callbacks must not mutate models, LP internals, node ordering, branching
  rules, pruning rules, incumbent comparison, CLI contracts, or JSON schemas.
- Added deterministic testing guidance for cut validity, duplicate detection, cut-pool
  lifecycle, callback hook ordering, and no-regression behavior when cuts are disabled.
- Added explicit non-goals, including branch-and-cut performance claims, broad cut
  families, lazy constraints, arbitrary mutation callbacks, commercial solver callbacks,
  external solver calls, parallel tree search, large benchmarks, automatic MIP presolve,
  CLI contract changes, JSON schema changes, and hidden branch-and-bound default changes.
- Updated `tasks/phases/phase_06_cut_callbacks.md` with only a brief Phase 6A design-note
  entry.

Future candidate tasks:

- Add immutable cut candidate and cut metadata dataclasses under `src/silo/cuts/`, with
  validation and canonical-key tests.
- Add a deterministic cut pool with duplicate detection, activation, and scope-clearing
  tests.
- Add no-op separator and separator protocol tests, without changing branch-and-bound
  behavior.
- Add read-only callback event records and hook-order tests using no-op callbacks.
- Integrate optional no-op cut/callback components into branch-and-bound while proving
  no-regression behavior when cuts are disabled.
- Add one deterministic toy separator for a tiny fixture, with explicit validity
  documentation and no performance claims.

Checks run:

- `git status --short`
- `git diff --check`

Results:

- The Phase 6 cut/callback boundary design note was created.
- The Phase 6 phase record was updated with a brief Phase 6A note.
- No solver source code was modified.
- No tests were modified.
- No examples were modified.
- No CLI behavior was modified.
- No JSON schemas were modified.
- `ROADMAP.md` was not modified.
- No Phase 6 implementation task was issued or executed.
- No cuts or callbacks were implemented.
- `git diff --check` passed.

Git status before:

```text
## main...origin/main
?? tasks/codex/20260524-04-01_phase6-cut-callback-design.md
```

Git status after:

```text
 M tasks/phases/phase_06_cut_callbacks.md
?? notes/18_cut_callback_boundary_design.md
?? tasks/codex/20260524-04-01_phase6-cut-callback-design.md
?? tasks/reports/20260524-04-01_phase6-cut-callback-design_report.md
```

Local commit hash:

```text
Created locally; the final response records the final amended commit hash.
```

Push attempted:

```text
Yes. Two push attempts failed after the local commit because GitHub could not be reached
over HTTPS. The first attempt failed with a connection reset, and the second attempt could
not connect to `github.com` on port 443. The local commit is preserved.
```

Issues or conflicts:

- This task is design-only and intentionally does not issue any Phase 6 implementation
  task.
- The issued task Git mode is `local-commit`, but the user explicitly requested push if
  possible for this execution.
- A commit cannot record its own final hash inside the report without changing that hash,
  so the final response records the created commit hash.
- Push did not complete because the connection to GitHub failed.
- No unrelated dirty changes were present before execution.

Next recommended atomic task:

After explicit user approval, issue exactly one Phase 6 implementation task to add
immutable cut candidate and cut metadata dataclasses with validation and canonical-key
tests.
