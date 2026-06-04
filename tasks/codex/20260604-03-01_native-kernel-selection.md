# 20260604-03-01 Phase 9 Native Kernel Candidate Selection

## Task metadata

- Task ID: 20260604-03-01
- Slug: native-kernel-selection
- Mode: SILO-DOS Mode B / Mode C design gate
- Task type: strategic design note
- Risk level: L3 strategic
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Readiness audit: `tasks/reports/20260604-02-01_phase9-readiness-audit_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260604-03-01_native-kernel-selection_report.md`

## Objective

Create a design-only Phase 9 native kernel candidate selection note that chooses and
scopes at most one first native-kernel candidate for later user review, without
implementing native code or approving implementation.

## Review gate

This task is L3 because it selects or scopes the first possible native implementation
line. It may be executed only after the user explicitly approves this specific design
task.

Executing this task does not approve native implementation. Any later implementation
requires a separate issued task and separate explicit user approval.

Reclassify and stop before execution if the requested work would implement a native
kernel, add dependencies, change build or packaging files, expose backend selection
through public CLI or JSON schemas, close Phase 9, start Phase 10, or modify solver
behavior.

## Context

Phase 9 has completed a conservative Python-reference boundary:

- backend boundary smoke tests;
- immutable backend capability and availability records;
- passive Python-reference backend records;
- passive conformance fixture records;
- unavailable-native diagnostics tests;
- a no-op backend selector boundary;
- passive parity result records;
- a readiness audit classified as `ready_for_user_native_kernel_design_review`.

The readiness audit explicitly says Phase 9 is ready for user review of a design-only
native-kernel candidate selection task, but not ready for direct native-kernel
implementation.

## Scope lock

Produce a design note that selects and scopes at most one candidate native kernel for
future review. The design note must remain planning-only and must not implement,
prototype, scaffold, dispatch to, build, package, or expose any native kernel.

## Allowed changes

- `notes/22_native_kernel_candidate_selection.md`
- `tasks/codex/20260604-03-01_native-kernel-selection.md`
- `tasks/reports/20260604-03-01_native-kernel-selection_report.md`

## Forbidden changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify `notes/21_native_backend_boundary_design.md`.
- Do not create or modify native implementation files.
- Do not add native dependencies.
- Do not add build-system or packaging changes.
- Do not add generated build artifacts.
- Do not implement a native kernel.
- Do not implement solver dispatch.
- Do not add backend fallback behavior.
- Do not call LP or MIP solvers.
- Do not call external solvers.
- Do not close Phase 9.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Design-note requirements

Create `notes/22_native_kernel_candidate_selection.md` with:

- a short purpose statement;
- the Phase 9 readiness basis, citing the readiness audit;
- candidate-selection criteria from `notes/21_native_backend_boundary_design.md`;
- a candidate screen covering at least:
  - tableau or revised-simplex pivot/ratio-test primitives;
  - small canonical/vector arithmetic helpers;
  - branch-and-bound search-control primitives;
  - presolve reductions;
  - cut separation or callback mutation;
  - decomposition loops;
  - uncertainty transformations;
- exactly one recommended first candidate or a clear recommendation to defer native
  implementation if no candidate is safe enough;
- the selected candidate's input/output boundary;
- why the candidate does not alter default Python solver behavior;
- parity fixture requirements;
- tolerance, ordering, status, and diagnostic conventions that must be fixed before
  implementation;
- explicit non-goals;
- implementation prerequisites;
- review gates before implementation;
- a recommended next atomic task and risk level.

The note must not include implementation pseudocode that is detailed enough to be treated
as a native implementation plan. Keep it at boundary, contract, fixture, and review-gate
level.

## Required checks

Run:

```powershell
git status --short
git branch --show-current
git log --oneline -5
git diff --check
```

Do not run solver test suites unless the design note unexpectedly changes executable
files. If executable files would need to change, stop instead because that is outside
this task's scope.

## Acceptance criteria

- `notes/22_native_kernel_candidate_selection.md` is created.
- The note selects and scopes at most one first native-kernel candidate, or explicitly
  recommends deferring native implementation.
- The note records candidate-selection criteria, rejected risky areas, parity fixture
  requirements, conventions, non-goals, prerequisites, and review gates.
- The note does not implement or approve native implementation.
- No source code, tests, examples, roadmap files, phase files, CLI behavior, JSON
  schemas, native implementation files, dependencies, build files, or packaging files are
  changed.
- Phase 9 is not closed.
- Phase 10 is not started.
- The matching report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- choosing a candidate requires source-code or test changes;
- completing the design would require changing public CLI behavior or JSON schemas;
- completing the design would require native dependencies, build files, packaging files,
  or native implementation files;
- the design would implicitly approve implementation;
- the design would close Phase 9 or start Phase 10;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260604-03-01_native-kernel-selection_report.md` with:

- objective;
- risk level and approval confirmation;
- task ID scan result;
- files changed;
- design summary;
- selected candidate or deferral recommendation;
- checks run and results;
- deviations from scope, if any;
- Git status before and after;
- local commit hash;
- push attempted and result;
- unresolved issues;
- next recommended atomic task.

## Final response requirements

Report:

- task path;
- risk level and approval confirmation;
- files changed;
- selected candidate or deferral recommendation;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no native kernel was implemented or approved;
- confirmation that no source, tests, CLI, JSON schema, roadmap, phase, native,
  dependency, build, or packaging files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
