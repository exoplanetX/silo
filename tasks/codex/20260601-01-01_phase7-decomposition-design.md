# Codex Task: Phase 7 Decomposition Boundary Design

## Task Metadata

Task ID: 20260601-01-01
Task slug: phase7-decomposition-design
Task type: design-note
Risk level: L3 strategic planning
Related phase: Phase 7 / Decomposition Layer
Git mode: local-commit
Expected report path: tasks/reports/20260601-01-01_phase7-decomposition-design_report.md

## Objective

Draft a Phase 7 decomposition-layer design note that defines conservative
master-subproblem abstractions, Benders-style and column-generation-style boundaries,
deterministic decomposition logs, dependency boundaries, non-goals, and candidate atomic
implementation tasks.

This is planning only. Do not implement decomposition modules.

## Context

Phase 6 is closed for the current conservative cut/callback boundary scope. The Phase 6
closure bookkeeping report is:

```text
tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md
```

That report states that Phase 7 was not started and recommends using SILO-DOS Mode C
principal mode to draft a Phase 7 decomposition planning/design-note task before any
Phase 7 implementation.

The user has explicitly approved starting Phase 7 planning but has not approved Phase 7
implementation.

Relevant inputs:

- `ROADMAP.md`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`
- existing LP and MIP public/internal APIs by filename and light inspection only, if
  needed to avoid incorrect dependency claims
- existing Phase 6 cut/callback design note only as boundary context, not as a license to
  integrate decomposition with cuts

## Scope Lock

This task is atomic.

Primary objective:

- Create a design note for Phase 7 decomposition boundaries and update the Phase 7 phase
  record with a brief Phase 7A design-note entry.

Allowed changes:

- `notes/19_decomposition_boundary_design.md`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-01-01_phase7-decomposition-design_report.md`

Supporting allowed change:

- `tasks/codex/20260601-01-01_phase7-decomposition-design.md` may be committed as the
  issued task contract for this execution.

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not create `src/silo/decomposition/` implementation files.
- Do not create decomposition tests.
- Do not add generated output files.
- Do not implement Benders decomposition.
- Do not implement column generation.
- Do not implement master/subproblem wrappers.
- Do not integrate decomposition with LP, MIP, cuts, callbacks, presolve, or CLI code.
- Do not add external solver calls.
- Do not issue or execute any Phase 7 implementation task.
- Do not modify existing files under `tasks/codex/`.

## Required Design Content

Create `notes/19_decomposition_boundary_design.md` with the following sections:

1. Purpose and Phase 7 scope.
2. Dependency boundary and allowed dependency direction.
3. Master-subproblem abstraction:
   - master problem role;
   - subproblem role;
   - model/solution exchange boundary;
   - status and diagnostic boundary;
   - what information may cross the boundary.
4. Benders-style boundary:
   - educational iteration structure;
   - master solve boundary;
   - subproblem solve boundary;
   - cut-candidate representation choices;
   - feasibility/optimality cut placeholders;
   - status handling and stopping rules;
   - no claim of industrial Benders performance.
5. Column-generation-style boundary:
   - restricted master problem role;
   - pricing subproblem role;
   - column-candidate representation choices;
   - reduced-cost/sign convention documentation;
   - status handling and stopping rules;
   - no claim of industrial branch-and-price performance.
6. Decomposition logs and iteration records:
   - immutable or append-only iteration summaries;
   - deterministic iteration ids;
   - master/subproblem statuses;
   - objective/bound/cut/column counts;
   - termination reason;
   - diagnostics that do not change public solution schemas.
7. LP/MIP integration boundary:
   - how decomposition may call existing LP/MIP layers;
   - how it must avoid circular dependencies;
   - how it must avoid changing core/modeling/presolve/lp/mip behavior;
   - how it should treat external solvers as out of native algorithm scope.
8. Testing strategy:
   - toy Benders smoke tests;
   - toy column-generation smoke tests;
   - deterministic iteration-log tests;
   - dependency/no-regression checks.
9. Non-goals and out-of-scope items.
10. Candidate atomic task sequence for future Phase 7 implementation work.

The candidate atomic task sequence must be planning-only. It may list future tasks, but it
must not issue those tasks.

## Required Non-Goals

The design note must explicitly keep the following out of scope:

- production-grade decomposition framework;
- large benchmarks or performance claims;
- branch-and-price;
- branch-and-cut-and-price;
- advanced stabilization;
- cut strengthening;
- automatic reformulation;
- callback mutation paths;
- public CLI changes;
- JSON schema changes;
- external solver calls inside native algorithms;
- changes to existing LP/MIP solver behavior;
- changes to presolve behavior;
- Phase 7 implementation inside this task.

## Stop Conditions

Stop and report instead of proceeding if:

- the Phase 6 closure report cannot be found;
- Phase 6 is not marked complete for the conservative cut/callback boundary scope;
- the user approval for Phase 7 planning is no longer clear;
- completing the design note would require modifying solver source code, tests, examples,
  public CLI behavior, JSON schemas, `ROADMAP.md`, or implementation files;
- writing the design note requires issuing or executing Phase 7 implementation work;
- repository state contains unrelated dirty changes that make the design-only scope
  ambiguous.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Do not run the full solver test suite unless executable project files are changed
unexpectedly. Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. `notes/19_decomposition_boundary_design.md` is created.
2. The design note covers master-subproblem abstraction.
3. The design note covers Benders-style boundaries.
4. The design note covers column-generation-style boundaries.
5. The design note covers decomposition logs and iteration records.
6. The design note explains how decomposition may use existing LP/MIP layers without
   creating circular dependencies.
7. The design note clearly lists non-goals and out-of-scope items.
8. The design note includes candidate atomic implementation tasks without issuing or
   executing them.
9. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7A design-note
   entry.
10. No solver source code is modified.
11. No tests are modified.
12. No examples are modified.
13. No CLI behavior or JSON schemas are modified.
14. No Phase 7 implementation task is issued or executed.
15. A report is created at the expected report path.
16. `git diff --check` passes.

## Report Requirements

Create:

```text
tasks/reports/20260601-01-01_phase7-decomposition-design_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and approval:
Files changed:
Design decisions:
Candidate future tasks:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that no solver source code, tests, examples, CLI behavior,
JSON schemas, or Phase 7 implementation work were modified or created.

## Git Instructions

Git mode:

```text
local-commit
```

After successful design note creation and checks:

```bash
git add tasks/codex/20260601-01-01_phase7-decomposition-design.md notes/19_decomposition_boundary_design.md tasks/phases/phase_07_decomposition.md tasks/reports/20260601-01-01_phase7-decomposition-design_report.md
git commit -m "docs(tasks): design Phase 7 decomposition boundary"
```

Do not push unless explicitly instructed by the user.

## Final Response

When finished, report only:

- whether the Phase 7 decomposition design note was created;
- whether the Phase 7 phase record was updated;
- whether no implementation was started;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
