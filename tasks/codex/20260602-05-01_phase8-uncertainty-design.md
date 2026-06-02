# Codex Task: Phase 8 Uncertainty Boundary Design

## Task Metadata

Task ID: 20260602-05-01
Task slug: phase8-uncertainty-design
Task type: design-note
Risk level: L3 strategic
Related phase: Phase 8 / Stochastic and Robust Optimization Extensions
Git mode: push-on-success
Expected report path: tasks/reports/20260602-05-01_phase8-uncertainty-design_report.md

## Objective

Create a Phase 8 planning/design note for stochastic and robust optimization extensions,
focused on representing uncertainty as explicit deterministic model transformations, not
as a separate solver.

## User Approval

The user explicitly approved starting Phase 8 planning, but did not approve Phase 8
implementation.

## Context

Phase 7 is closed for the current conservative decomposition boundary scope. Phase 8 in
`ROADMAP.md` and `tasks/phases/phase_08_stochastic_robust.md` is about stochastic and
robust optimization extensions:

- finite scenarios;
- stochastic model wrappers;
- robust model wrappers;
- uncertainty sets;
- deterministic equivalents;
- small transformation examples.

The phase rule is to represent uncertainty first as model transformation into ordinary
SILO model objects, not as a separate black-box solver.

## Scope Lock

This task is atomic and design-only.

Primary objective:

- Add one Phase 8 boundary design note and record the planning step.

Allowed changes:

- `notes/20_uncertainty_boundary_design.md`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/reports/20260602-05-01_phase8-uncertainty-design_report.md`

Supporting allowed change:

- `tasks/codex/20260602-05-01_phase8-uncertainty-design.md` may be committed as the
  issued task contract for this execution.

Forbidden changes:

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify LP solver behavior.
- Do not modify MIP solver behavior.
- Do not modify presolve behavior.
- Do not modify cut, callback, or decomposition behavior.
- Do not implement scenario records.
- Do not implement stochastic model wrappers.
- Do not implement robust model wrappers.
- Do not implement uncertainty sets.
- Do not implement deterministic equivalents.
- Do not create Phase 8 implementation files under `src/silo/uncertainty/`.
- Do not create Phase 8 tests.
- Do not create examples.
- Do not issue or execute any Phase 8 implementation task.
- Do not start Phase 9.

## Required Design Note Content

Create:

```text
notes/20_uncertainty_boundary_design.md
```

The design note must cover:

1. Phase 8 purpose and conservative scope.
2. Dependency direction and package boundary for `uncertainty`.
3. Finite-scenario data model:
   - scenario ids;
   - probabilities;
   - parameter overrides or coefficients;
   - deterministic validation rules;
   - probability normalization policy.
4. Stochastic model wrapper boundary:
   - first-stage versus scenario-dependent data;
   - nonanticipativity representation;
   - variable and constraint naming conventions;
   - what metadata may cross into deterministic equivalents.
5. Deterministic equivalent boundary:
   - how ordinary SILO `Model` objects should be produced;
   - objective aggregation convention;
   - scenario constraint replication;
   - nonanticipativity constraints;
   - dimensions and diagnostics expected from small examples.
6. Robust model and uncertainty-set boundary:
   - supported early uncertainty-set shapes;
   - documented assumptions for simple robust counterparts;
   - what remains out of scope.
7. Interaction with existing LP/MIP/presolve/decomposition layers:
   - uncertainty transforms may produce ordinary models;
   - existing solvers must not know uncertainty exists;
   - no public CLI or JSON schema changes in early Phase 8 unless separately approved.
8. Testing strategy for future implementation tasks:
   - scenario validation;
   - probability checks;
   - deterministic equivalent dimensions;
   - variable naming conventions;
   - robust counterpart smoke tests.
9. Non-goals:
   - separate stochastic solver;
   - chance constraints;
   - distributionally robust optimization;
   - sampling/SAA engine;
   - external solver calls inside native code;
   - large datasets or performance claims;
   - public CLI/schema changes.
10. Candidate atomic implementation task sequence.

Update `tasks/phases/phase_08_stochastic_robust.md` with only a brief Phase 8A note
stating that the design note was added. Do not mark implementation as started.

## Required Checks

Run at least:

```bash
git status --short
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. `notes/20_uncertainty_boundary_design.md` exists.
2. The design note covers stochastic, robust, and deterministic-equivalent boundaries.
3. The design note defines non-goals and candidate atomic implementation tasks.
4. `tasks/phases/phase_08_stochastic_robust.md` receives only a brief Phase 8A planning
   note.
5. No solver source code is changed.
6. No tests are changed.
7. No examples are changed.
8. No CLI behavior or JSON schemas are changed.
9. No Phase 8 implementation task is issued or executed.
10. A report is created at the expected report path.
11. Required checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260602-05-01_phase8-uncertainty-design_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and approval:
Files changed:
Design summary:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that no Phase 8 implementation was started and that no
solver source code, tests, examples, CLI behavior, or JSON schemas were modified.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful design-note work and checks:

```bash
git add notes/20_uncertainty_boundary_design.md tasks/phases/phase_08_stochastic_robust.md tasks/codex/20260602-05-01_phase8-uncertainty-design.md tasks/reports/20260602-05-01_phase8-uncertainty-design_report.md
git commit -m "docs(uncertainty): add phase 8 boundary design"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether the Phase 8 design note was created;
- whether Phase 8 implementation was not started;
- whether solver source code and tests were not modified;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
