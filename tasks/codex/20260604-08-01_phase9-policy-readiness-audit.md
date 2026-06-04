# 20260604-08-01 Phase 9 Policy Readiness Audit

## Task metadata

- Task ID: 20260604-08-01
- Slug: phase9-policy-readiness-audit
- Mode: SILO-DOS Mode A auto-one
- Task type: audit
- Risk level: L0 safe
- Phase reference: Phase 9 native backend
- Design notes:
  - `notes/21_native_backend_boundary_design.md`
  - `notes/22_native_kernel_candidate_selection.md`
  - `notes/23_native_build_dependency_policy.md`
- Prior report: `tasks/reports/20260604-07-01_native-build-policy_report.md`
- Git mode: push-on-success
- Expected report:
  `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md`

## Objective

Create a Phase 9 implementation-readiness audit after the native build/dependency and
generated-artifact policy note, determining whether the selected
`tableau_leaving_row_ratio_test` candidate is ready for native implementation review or
should remain deferred.

## Review gate

This task is L0 because it creates an audit report only. Mode A may auto-execute it if
the repository state is clean and the scope remains limited to the allowed files.

Reclassify and stop before execution as L3 if the task would approve native
implementation, issue a native implementation task, choose a binding native build
strategy beyond the existing policy note, close Phase 9, start Phase 10, add native
dependencies, or modify roadmap/phase-transition files.

## Context

Phase 9 has now completed the conservative backend boundary, selected
`tableau_leaving_row_ratio_test` as the first candidate, added passive parity fixtures,
added candidate-specific unavailable-native diagnostics, and created the native
build/dependency and generated-artifact policy note.

The policy note recommends deferring native implementation for now. This audit should
record whether that recommendation still governs the next step and what approval gate
would be needed before any implementation.

## Scope lock

Create only the issued task and the matching audit report. The audit may inspect source,
tests, notes, roadmap, phase files, native placeholders, dependency files, build files,
and recent reports, but it must not modify any of them except the allowed task/report
files.

## Allowed changes

- `tasks/codex/20260604-08-01_phase9-policy-readiness-audit.md`
- `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md`

## Forbidden changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify notes.
- Do not modify `pyproject.toml`.
- Do not modify build-system or packaging files.
- Do not create or modify native implementation files.
- Do not add native dependencies.
- Do not add generated build artifacts, binary files, wheels, compiled objects, or
  platform-local artifacts.
- Do not implement a native kernel.
- Do not approve native implementation.
- Do not implement solver dispatch.
- Do not add backend fallback behavior.
- Do not call LP or MIP solvers except through explicitly required tests.
- Do not call external solvers.
- Do not run build commands or native tooling.
- Do not close Phase 9.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Audit requirements

The audit report must cover:

- task ID scan result;
- repository status before the audit;
- Phase 9 artifacts completed through the build/dependency policy note;
- whether the selected candidate has passive fixtures and candidate-specific
  unavailable-native diagnostics;
- whether a native build/dependency and generated-artifact policy now exists;
- whether the policy recommends deferring native implementation or moving to
  implementation review;
- whether any native implementation appears to exist;
- whether default Python reference solver behavior remains the source of truth;
- whether public CLI behavior and JSON schemas remain unchanged;
- whether native dependencies remain optional and absent from normal installation;
- readiness classification, using one of:
  - `not_ready_for_native_kernel`;
  - `ready_for_user_native_kernel_design_review`;
  - `ready_for_user_native_kernel_implementation_decision_review`;
  - `ready_for_user_native_kernel_implementation_review`;
- explicit blockers or prerequisites before native kernel implementation;
- recommended next atomic task and risk level.

The report must not mark Phase 9 complete and must not treat native implementation as
approved.

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

- The matching audit report is created.
- The report states that no native kernel implementation was started by this task.
- The report gives a clear readiness classification.
- The report lists blockers or prerequisites before any native kernel implementation.
- The report recommends exactly one next atomic task, without issuing or executing it.
- No source code, tests, examples, CLI behavior, JSON schemas, roadmap files, phase
  files, notes, native implementation files, dependencies, build files, packaging files,
  binaries, or generated artifacts are changed.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- completing the audit requires source, test, CLI, JSON schema, roadmap, phase, note,
  dependency, build, packaging, native implementation, or generated-artifact changes;
- the audit would need to approve or implement a native kernel;
- the audit would need to close Phase 9 or start Phase 10;
- required checks reveal a failure that cannot be reported without expanding scope;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md` with:

- objective;
- risk level;
- task ID scan result;
- files changed;
- audit findings;
- readiness classification;
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
- risk level;
- files changed;
- readiness classification;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no native kernel was implemented or approved;
- confirmation that no source, tests, CLI behavior, JSON schema, roadmap, phase, notes,
  native, dependency, build, packaging, binary, or generated-artifact files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
