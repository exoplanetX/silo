# 20260604-09-01 Native Decision Packet

## Task metadata

- Task ID: 20260604-09-01
- Slug: native-decision-packet
- Mode: SILO-DOS Mode C principal mode / review-gated L3 decision task
- Task type: design note / decision packet
- Risk level: L3 strategic
- Phase reference: Phase 9 native backend
- Selected candidate: `tableau_leaving_row_ratio_test`
- Design notes:
  - `notes/21_native_backend_boundary_design.md`
  - `notes/22_native_kernel_candidate_selection.md`
  - `notes/23_native_build_dependency_policy.md`
- Prior report:
  `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md`
- Git mode: push-on-success
- Expected report:
  `tasks/reports/20260604-09-01_native-decision-packet_report.md`

## Objective

Create a design-only native implementation decision packet for the selected
`tableau_leaving_row_ratio_test` candidate, limited to decision review. The packet should
help the user decide whether to approve, revise, reject, or defer a future native
implementation path, without implementing native code or changing repository behavior.

## Review gate

This task is L3 because it prepares a decision boundary for a future native
implementation line.

The user explicitly approved issuing exactly one L3 decision packet task. This approval
does not approve executing native implementation and does not approve modifying source,
tests, dependencies, build files, CLI behavior, JSON schemas, solver dispatch, roadmap,
phase files, or future phase status.

Execute this task only if the user separately asks to execute this exact task file.

## Context

Phase 9 has completed the conservative native-backend boundary, selected
`tableau_leaving_row_ratio_test` as the first candidate, added passive parity fixtures,
added candidate-specific unavailable-native diagnostics, and created the native
build/dependency and generated-artifact policy note.

The latest readiness audit classified the repository as:

```text
ready_for_user_native_kernel_implementation_decision_review
```

The current policy recommendation is still:

```text
defer native implementation for now
```

This task should convert that state into a self-contained decision packet. It must not
cross from decision review into implementation.

## Scope lock

Create a decision packet note and matching report only. The decision packet may compare
implementation choices, recommend approve/revise/reject/defer, and provide exact future
approval language. It must not implement native code, create native scaffolding, change
source or tests, change build or packaging files, add dependencies, or issue a follow-on
implementation task.

## Allowed changes

- `notes/24_native_implementation_decision_packet.md`
- `tasks/codex/20260604-09-01_native-decision-packet.md`
- `tasks/reports/20260604-09-01_native-decision-packet_report.md`

## Forbidden changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify existing notes.
- Do not modify `pyproject.toml`.
- Do not modify build-system or packaging files.
- Do not create or modify native implementation files.
- Do not add native dependencies.
- Do not add generated build artifacts, binary files, wheels, compiled objects, or
  platform-local artifacts.
- Do not implement a native kernel.
- Do not implement solver dispatch.
- Do not add backend fallback behavior.
- Do not call LP or MIP solvers except through explicitly required tests.
- Do not call external solvers.
- Do not run build commands or native tooling.
- Do not close Phase 9.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Decision packet requirements

Create `notes/24_native_implementation_decision_packet.md` with a self-contained
decision packet covering:

- task and candidate summary;
- current readiness evidence:
  - boundary design;
  - candidate selection;
  - passive parity fixtures;
  - candidate-specific unavailable-native diagnostics;
  - build/dependency and generated-artifact policy;
  - latest readiness audit classification;
- risk level and why the implementation decision is L3;
- candidate implementation options:
  - defer implementation;
  - approve a narrow optional Python extension path later;
  - reject native implementation for the current candidate;
  - revise the candidate or prerequisites before implementation;
- recommended option from the evidence;
- if recommending approval later, exact approval sentence for the user to execute a
  future implementation task;
- if recommending defer/revise/reject, exact sentence for that decision;
- likely files for a future implementation task, without creating them;
- behavior and invariants that must remain unchanged:
  - default Python solver path;
  - `TableauSimplexSolver` behavior;
  - `RevisedSimplexSolver` behavior;
  - MIP branch-and-bound behavior;
  - public CLI behavior;
  - JSON schemas;
  - backend selector behavior unless separately approved;
  - absence of hidden fallback or environment-variable dispatch;
- required no-regression and parity checks for any future implementation task;
- possible failure modes:
  - packaging or compiler failures;
  - platform-specific import failures;
  - tolerance mismatch;
  - row-order tie-breaking mismatch;
  - hidden fallback;
  - default solver-path native import;
  - generated artifacts entering git;
  - public contract creep;
- explicit statement that the packet does not approve implementation;
- exact next recommended atomic task, if any, without issuing it.

The decision packet must preserve the current policy recommendation unless the evidence
in repository files justifies a different recommendation. Any recommendation remains
advisory and must not be treated as user approval.

## Required checks

Run:

```powershell
git status --short
git branch --show-current
git log --oneline -5
pytest tests/unit/test_backend_boundary_smoke.py
pytest tests/unit/test_tableau_ratio_native_diagnostics.py
pytest tests/unit/test_tableau_ratio_parity.py
git diff --check
```

Do not run build commands or native tooling.

## Acceptance criteria

- `notes/24_native_implementation_decision_packet.md` is created.
- The decision packet is design-only and decision-review only.
- The packet recommends one of approve, revise, reject, or defer.
- The packet includes exact future approval or decision language.
- The packet states that it does not approve or implement native code.
- No source code, tests, examples, CLI behavior, JSON schemas, roadmap files, phase
  files, existing notes, native implementation files, dependencies, build files,
  packaging files, binaries, or generated artifacts are changed.
- The matching report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- completing the packet requires source, test, CLI, JSON schema, roadmap, phase,
  dependency, build, packaging, or native implementation changes;
- the packet would need to approve native implementation directly;
- the packet would need to create a native implementation task;
- the packet would need to close Phase 9 or start Phase 10;
- required checks fail in a way that cannot be reported without expanding scope;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260604-09-01_native-decision-packet_report.md` with:

- objective;
- risk level and approval confirmation;
- task ID scan result;
- files changed;
- decision packet summary;
- recommendation summary;
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
- decision packet recommendation summary;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no native kernel was implemented or approved;
- confirmation that no solver source, tests, CLI behavior, JSON schema, roadmap, phase,
  existing notes, native, dependency, build, packaging, binary, or generated-artifact
  files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
