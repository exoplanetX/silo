# 20260604-05-01 Phase 9 Implementation Readiness Audit

## Task metadata

- Task ID: 20260604-05-01
- Slug: phase9-implementation-readiness-audit
- Mode: SILO-DOS Mode A auto-one
- Task type: audit
- Risk level: L0 safe
- Phase reference: Phase 9 native backend
- Design notes:
  - `notes/21_native_backend_boundary_design.md`
  - `notes/22_native_kernel_candidate_selection.md`
- Prior report: `tasks/reports/20260604-04-01_ratio-test-parity-fixtures_report.md`
- Git mode: push-on-success
- Expected report:
  `tasks/reports/20260604-05-01_phase9-implementation-readiness-audit_report.md`

## Objective

Create a Phase 9 implementation readiness audit after the passive ratio-test parity
fixtures, determining whether the selected `tableau_leaving_row_ratio_test` candidate is
ready for user native-kernel implementation review or remains blocked by prerequisite
boundary work.

## Review gate

This task is L0 because it creates an audit report only. Mode A may auto-execute it if
the repository state is clean and the scope remains limited to the allowed files.

Reclassify and stop before execution as L3 if the task would approve native
implementation, start a native implementation task, choose a native build strategy as a
binding implementation decision, close Phase 9, start Phase 10, add native dependencies,
or modify roadmap/phase-transition files.

## Context

The earlier Phase 9 readiness audit classified the project as
`ready_for_user_native_kernel_design_review`. The subsequent candidate-selection note
selected `tableau_leaving_row_ratio_test` as the first candidate and listed prerequisites
before native implementation. The latest completed task added passive parity fixtures for
that candidate. This audit should check whether those additions are enough to move from
design review toward native-kernel implementation review, while keeping implementation
blocked unless every prerequisite and explicit approval boundary is satisfied.

## Scope lock

Create only the issued task and the matching audit report. The audit may inspect source,
tests, notes, roadmap, phase files, native placeholders, dependency files, build files,
and recent reports, but it must not modify any of them except the allowed task/report
files.

## Allowed changes

- `tasks/codex/20260604-05-01_phase9-implementation-readiness-audit.md`
- `tasks/reports/20260604-05-01_phase9-implementation-readiness-audit_report.md`

## Forbidden changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify notes.
- Do not create or modify native implementation files.
- Do not add native dependencies.
- Do not add build-system or packaging changes.
- Do not add generated build artifacts.
- Do not approve or implement any native kernel.
- Do not implement solver dispatch.
- Do not add backend fallback behavior.
- Do not call LP or MIP solvers except through the required test commands.
- Do not call external solvers.
- Do not close Phase 9.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Audit requirements

The audit report must cover:

- task ID scan result;
- repository status before the audit;
- latest Phase 9 artifacts completed since the first readiness audit;
- whether passive candidate-specific parity fixtures now exist for
  `tableau_leaving_row_ratio_test`;
- whether candidate-specific unavailable-native diagnostics exist;
- whether a documented optional native build/dependency policy exists;
- whether a platform and generated-artifact exclusion policy exists for native work;
- whether a native implementation strategy decision packet exists;
- whether any native kernel implementation appears to exist;
- whether default Python reference solver behavior remains the source of truth;
- whether public CLI behavior and JSON schemas remain unchanged;
- whether native dependencies remain optional and absent from normal installation;
- whether current tests cover boundary, capability, adapter, conformance, diagnostics,
  selector, parity records, and the ratio-test passive fixture set;
- readiness classification, using one of:
  - `not_ready_for_native_kernel`;
  - `ready_for_user_native_kernel_design_review`;
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
pytest tests/unit/test_backend_capability_records.py
pytest tests/unit/test_python_backend_adapter.py
pytest tests/unit/test_backend_conformance.py
pytest tests/unit/test_unavailable_native_backend_diagnostics.py
pytest tests/unit/test_backend_selector.py
pytest tests/unit/test_backend_parity_records.py
pytest tests/unit/test_tableau_ratio_parity.py
pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- The matching audit report is created.
- The report states that no native kernel implementation was started by this task.
- The report gives a clear readiness classification.
- The report lists blockers or prerequisites before any native kernel implementation.
- The report recommends exactly one next atomic task, without issuing or executing it.
- No source code, tests, examples, roadmap files, phase files, notes, CLI behavior, JSON
  schemas, native implementation files, dependencies, build files, or packaging files are
  changed.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- completing the audit requires modifying source code, tests, roadmap files, phase
  files, notes, examples, CLI behavior, JSON schemas, native files, dependencies, build
  files, or packaging files;
- the audit would need to approve or implement a native kernel;
- the audit would need to choose a binding native build/dependency strategy;
- the audit would need to close Phase 9 or start Phase 10;
- required checks reveal a failure that cannot be reported without expanding scope;
- the task ID collides with an existing task or report.

## Report requirements

Create
`tasks/reports/20260604-05-01_phase9-implementation-readiness-audit_report.md` with:

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
- confirmation that no source, tests, CLI, JSON schema, roadmap, phase, notes, native,
  dependency, build, or packaging files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
