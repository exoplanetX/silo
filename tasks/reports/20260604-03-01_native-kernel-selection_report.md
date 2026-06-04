# Task Report: 20260604-03-01 Phase 9 Native Kernel Candidate Selection

Task ID: 20260604-03-01

Objective: Create a design-only Phase 9 native kernel candidate selection note that
chooses and scopes at most one first native-kernel candidate for later user review,
without implementing native code or approving implementation.

Risk level and approval confirmation:

- Risk level: L3 strategic.
- The user explicitly approved issuing and executing exactly one L3 design-only native
  kernel candidate selection task.
- The approval boundaries prohibited native implementation, solver source changes, test
  changes, CLI or JSON schema changes, native dependencies, build or packaging changes,
  Phase 9 closure, and Phase 10 work.
- This task did not approve native implementation. Any implementation still requires a
  separate issued task and separate explicit user approval.

Task ID scan result:

- Existing `20260604-*` task/report prefixes before execution:
  - `20260604-01-01_parity-result-records`
  - `20260604-02-01_phase9-readiness-audit`
  - issued unexecuted task `20260604-03-01_native-kernel-selection`
- No matching report existed before execution.
- No collision was found for `20260604-03-01_native-kernel-selection`.

Files changed:

- `notes/22_native_kernel_candidate_selection.md`
- `tasks/codex/20260604-03-01_native-kernel-selection.md`
- `tasks/reports/20260604-03-01_native-kernel-selection_report.md`

Design summary:

- Created `notes/22_native_kernel_candidate_selection.md`.
- Used the Phase 9 readiness audit as the basis for candidate selection.
- Screened required candidate classes:
  - tableau or revised-simplex pivot and ratio-test primitives;
  - small canonical or vector arithmetic helpers;
  - branch-and-bound search-control primitives;
  - presolve reductions;
  - cut separation or callback mutation;
  - decomposition loops;
  - uncertainty transformations.
- Rejected policy-heavy areas such as branch-and-bound, presolve, cuts/callbacks,
  decomposition, and uncertainty transformations.
- Deferred small canonical/vector arithmetic helpers because current standard-form and
  canonical code is still tied to model validation, row normalization, naming, and
  artificial-variable conventions.
- Selected exactly one first candidate for later review:
  `tableau_leaving_row_ratio_test`.

Selected candidate:

- Recommended first candidate: `tableau_leaving_row_ratio_test`.
- Python reference source: `silo.lp.simplex.ratio_test.choose_leaving_row`.
- Boundary:
  - input rows: normalized finite tableau row sequences with right-hand side in the final
    column;
  - input entering column: zero-based tableau column index excluding the right-hand-side
    column;
  - input tolerance: tolerance for deciding whether a pivot coefficient is positive;
  - output: zero-based leaving-row index, or `None` if no row has pivot coefficient
    greater than tolerance.
- Required behavior:
  - treat rows as read-only;
  - ignore pivot coefficients less than or equal to tolerance;
  - compute candidate ratios as row right-hand side divided by pivot coefficient;
  - choose the minimum ratio;
  - break exact ratio ties by smaller row index;
  - avoid model, basis, solver, status, file path, CLI, JSON, and native runtime inputs.

Implementation status:

- No native kernel was implemented.
- No native implementation was approved.
- No native build, dependency, packaging, or dispatch decision was made.
- The note recommends a passive parity-fixture task before any native implementation.

Checks run:

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `git diff --check`

Results:

- Initial status:

```text
?? tasks/codex/20260604-03-01_native-kernel-selection.md
```

- Status after design note before report:

```text
?? notes/22_native_kernel_candidate_selection.md
?? tasks/codex/20260604-03-01_native-kernel-selection.md
```

- Branch:

```text
main
```

- Recent commits:

```text
2ff9c8a docs(tasks): audit phase 9 native readiness
8d6414d feat(interfaces): add backend parity records
29dbd65 feat(interfaces): add noop backend selector
ab7a88c test(interfaces): add unavailable native diagnostics
592ab7f test(interfaces): add backend conformance fixtures
```

- `git diff --check`: passed.
- Solver test suites were not run because this design task changed no executable files.

Deviations from scope: None.

Scope confirmation:

- No solver source code under `src/` was modified.
- No tests were modified.
- No examples were modified.
- No public CLI behavior was modified.
- No JSON model or solution schemas were modified.
- `ROADMAP.md` was not modified.
- No files under `tasks/phases/` were modified.
- `notes/21_native_backend_boundary_design.md` was not modified.
- No native implementation files were created or modified.
- No native dependencies were added.
- No build-system or packaging files were modified.
- No generated build artifacts were added.
- No native kernel was implemented.
- No solver dispatch was implemented.
- No backend fallback behavior was added.
- No LP or MIP solvers were called.
- No external solvers were called.
- Phase 9 was not closed.
- Phase 10 was not started.
- No second task was issued or executed.

Git status after report before commit:

```text
?? notes/22_native_kernel_candidate_selection.md
?? tasks/codex/20260604-03-01_native-kernel-selection.md
?? tasks/reports/20260604-03-01_native-kernel-selection_report.md
```

Local commit hash:

- Initial local commit before recording push failure: `7492c9a`.
- This report was amended after the push failure; the final local commit hash is recorded
  in the final response.

Push attempted:

- Yes. `git push` failed with:

```text
fatal: unable to access 'https://github.com/exoplanetX/silo.git/': Failed to connect to github.com port 443 after 21093 ms: Couldn't connect to server
```

The local commit was preserved.

Unresolved issues:

- Native implementation remains approval-gated.
- The selected candidate still needs passive candidate-specific parity fixtures before
  native implementation should be considered.
- A native build/dependency plan remains unapproved and out of scope.

Next recommended atomic task:

- Add passive parity fixture records for the tableau leaving-row ratio-test candidate.
- Suggested risk level: L1 controlled implementation if limited to passive fixture
  records and tests, with no native implementation, no solver dispatch, no CLI or JSON
  schema changes, no build or packaging changes, and no default solver behavior changes.
- Approval required: Yes before execution, because it continues Phase 9 native-kernel
  preparation.

Boundary status:

- No native kernel was implemented or approved.
- Phase 9 was not closed.
- Phase 10 was not started.
- No second task was issued or executed.
