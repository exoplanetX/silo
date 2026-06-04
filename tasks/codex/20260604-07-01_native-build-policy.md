# 20260604-07-01 Native Build Policy

## Task metadata

- Task ID: 20260604-07-01
- Slug: native-build-policy
- Mode: SILO-DOS Mode C principal mode / review-gated L3 design task
- Task type: design note
- Risk level: L3 strategic
- Phase reference: Phase 9 native backend
- Design notes:
  - `notes/21_native_backend_boundary_design.md`
  - `notes/22_native_kernel_candidate_selection.md`
- Prior report:
  `tasks/reports/20260604-06-01_ratio-test-native-diagnostics_report.md`
- Git mode: push-on-success
- Expected report:
  `tasks/reports/20260604-07-01_native-build-policy_report.md`

## Objective

Create a design-only Phase 9 native build/dependency and generated-artifact policy note
for the selected `tableau_leaving_row_ratio_test` candidate, without implementing native
code or changing build, packaging, dependency, solver, CLI, JSON schema, roadmap, phase,
or test behavior.

## Review gate

This task is L3 because it constrains a future native implementation line and documents
native build/dependency policy.

The user explicitly approved issuing exactly one L3 planning task for this topic, but
did not approve native implementation. Execute this task only if the user separately asks
to execute this exact task file.

Reclassify and stop before execution if the task would add native dependencies, edit
build or packaging files, create native implementation files, change public CLI behavior,
modify JSON schemas, change solver behavior, close Phase 9, start Phase 10, or approve a
native implementation task.

## Context

Phase 9 has selected `tableau_leaving_row_ratio_test` as the first future native-kernel
candidate and has added passive parity fixtures plus candidate-specific unavailable
native diagnostics. The remaining implementation-readiness blockers include:

- optional native build/dependency policy;
- platform and generated-artifact exclusion policy;
- a decision packet for whether native code should be Python-extension based,
  standalone, or deferred.

This task addresses only the design-policy blocker. It must not implement native code or
change project packaging.

## Scope lock

Create a planning note and matching report only. The note may compare build/dependency
approaches and recommend a policy for future review, but it must not make repository
build-system changes, add dependencies, add native files, or approve implementation.

## Allowed changes

- `notes/23_native_build_dependency_policy.md`
- `tasks/codex/20260604-07-01_native-build-policy.md`
- `tasks/reports/20260604-07-01_native-build-policy_report.md`

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
- Do not close Phase 9.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Design note requirements

Create `notes/23_native_build_dependency_policy.md` covering:

- the selected candidate context: `tableau_leaving_row_ratio_test`;
- current repository state: no native implementation, no required native dependency, and
  no native build-system integration;
- non-goals for this policy task;
- allowed future native implementation forms to consider:
  - Python extension module;
  - standalone native executable or library behind an explicit optional interface;
  - deferred native implementation;
- recommended near-term policy for Phase 9;
- dependency policy:
  - normal installation must not require a compiler or native runtime;
  - native dependencies must remain optional and separately approved;
  - native algorithms must not call external solvers;
  - external solvers may remain only comparison interfaces, examples, or tests;
- build policy:
  - no build backend or packaging changes in this task;
  - future build changes require a separate L3 task and explicit approval;
  - default Python solver path must remain importable without native build products;
- generated-artifact policy:
  - do not commit compiled objects, generated binaries, wheels, local build directories,
    platform-specific outputs, benchmark dumps, or large artifacts;
  - list artifact classes that future native tasks must exclude from git;
- platform policy:
  - future native work must state supported platforms, fallback behavior, and unavailable
    diagnostics;
  - tests must pass without native runtime installed;
- test and CI policy:
  - default CI should keep Python reference tests required;
  - native-specific tests should be optional or availability-gated until native runtime
    support is approved;
- solver-behavior policy:
  - no default solver dispatch to native code;
  - no hidden fallback;
  - no public CLI or JSON schema exposure without separate review;
- decision packet:
  - recommend whether the first native implementation path should be Python extension,
    standalone, or deferred;
  - state why the recommendation is conservative;
  - list required approvals before implementation;
- candidate atomic tasks after this policy, without issuing them.

The note must explicitly state that it does not approve native implementation.

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

- `notes/23_native_build_dependency_policy.md` is created.
- The note covers dependency, build, platform, generated-artifact, test/CI, solver
  behavior, and approval policy.
- The note gives one conservative recommendation for the future native implementation
  strategy.
- The note does not approve or implement native code.
- No source code, tests, examples, CLI behavior, JSON schemas, roadmap files, phase
  files, existing notes, native implementation files, dependencies, build files,
  packaging files, binaries, or generated artifacts are changed.
- The matching report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- completing the note requires source, test, CLI, JSON schema, roadmap, phase,
  dependency, build, packaging, or native implementation changes;
- the policy would need to approve native implementation;
- the policy would need to close Phase 9 or start Phase 10;
- required checks fail in a way that cannot be reported without expanding scope;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260604-07-01_native-build-policy_report.md` with:

- objective;
- risk level and approval confirmation;
- task ID scan result;
- files changed;
- design summary;
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
- design recommendation summary;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no native kernel was implemented or approved;
- confirmation that no solver source, tests, CLI behavior, JSON schema, roadmap, phase,
  existing notes, native, dependency, build, or packaging files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
