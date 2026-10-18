# SILO Technical Route

## Role Of This Route

This file is the repository-local SILO-DOS v0.4 technical route. It records the current
decision corridor from the project state, not a backlog of work to execute
automatically.

The current route is based on:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`
- `tasks/reports/20260604-11-01_phase9-post-defer-audit_report.md`
- `notes/25_native_implementation_defer_decision.md`

This route does not replace `ROADMAP.md`, `tasks/phases/`, issued task files, or user
approval.

## Current Route State

Current milestone:

```text
python_reference_solver_milestone_complete_for_current_educational_scope
```

Current phase corridor:

```text
phase9_parked_on_design_bookkeeping_after_native_defer
```

Interpretation:

- Phase 0 through Phase 8 are complete for their scoped educational/conservative
  milestones.
- Phase 9 is open.
- Phase 9 is parked on design, audit, policy, readiness, and bookkeeping.
- Native implementation is deferred and unapproved.
- Phase 10 has not started.
- No immediate implementation task is required.

## Route Principles

The route is governed by these principles:

- One atomic task at a time.
- No implicit phase transition.
- No implicit native implementation.
- No second task after completing the current task.
- Reports may recommend next actions, but recommendations are not execution permission.
- L2/L3 gates require explicit user approval.
- If route state is ambiguous, stop and produce a Decision Packet.

## Current Allowed Actions

The following actions are allowed only when explicitly requested or approved by the user.

### Remain Parked

SILO may remain parked at the current milestone with no new task.

This is the default strategic posture after the milestone audit and native defer
decision.

### Process Or Documentation Refinement

Allowed as L0 tasks when scoped narrowly:

- create `.silo-dos/decision_log.md`;
- create `.silo-dos/experience_map.md`;
- create `.silo-dos/remote_sync_proof.md`;
- create `.silo-dos/standing_approval_profile.md`;
- create `.silo-dos/self_evolution.md`;
- add `.silo-dos/templates/` files in separate atomic tasks;
- audit whether `tasks/README.md` should reference `.silo-dos/` after enough files
  exist.

These tasks must not change solver behavior or phase status.

### Revise Or Reject The Native Candidate

The user may explicitly request a design-only task to revise or reject the selected
`tableau_leaving_row_ratio_test` native candidate.

Expected risk:

- L3 strategic design if the task changes candidate direction or native implementation
  posture.

Required boundary:

- no native implementation;
- no build or dependency change;
- no solver dispatch change;
- no public CLI or JSON schema change;
- no Phase 9 closure unless separately approved.

### Approve A Specific Native Implementation Path

The user may later explicitly approve a native implementation path. This is not approved
now.

Expected risk:

- L3 strategic for native implementation scaffold or build/dependency path;
- L2/L3 if solver dispatch or backend behavior is touched.

Required before execution:

- exact implementation candidate;
- exact files allowed;
- exact build/dependency policy;
- generated-artifact exclusion policy;
- availability-gated tests;
- no-dispatch boundary unless dispatch is separately approved;
- explicit user approval sentence.

### Prepare Phase 9 Closure

The user may explicitly approve a Phase 9 closure-readiness audit or closure bookkeeping
task.

Expected risk:

- L0 for closure-readiness audit;
- L3 for closure bookkeeping.

Closure must not start Phase 10.

### Start Phase 10 Planning

The user may explicitly approve Phase 10 planning.

Expected risk:

- L3 strategic phase start/planning.

Planning approval does not approve Phase 10 implementation.

## Current Forbidden Actions

Do not do any of the following by default:

- implement native backend code;
- add native dependencies;
- modify build or packaging files;
- change solver dispatch or backend selection behavior;
- add public native CLI controls;
- add native JSON schema controls;
- close Phase 9;
- start Phase 10;
- issue Phase 10 planning without explicit user approval;
- issue Phase 10 implementation work;
- modify solver source code outside an issued task;
- modify tests outside an issued task;
- modify examples outside an issued task;
- modify `ROADMAP.md` or `tasks/phases/` outside a scoped phase task;
- modify existing notes or task files outside a scoped maintenance task.

## Decision Gates

### L0 Gate

L0 process, documentation, audit, and bookkeeping tasks may be auto-executed in Mode A
when the scope is explicit and no forbidden changes are required.

Examples:

- `.silo-dos/` process documentation;
- audit reports;
- task-system cleanup.

### L1 Gate

L1 controlled implementation may be auto-executed only when:

- backed by a design note;
- explicitly scoped;
- acceptance criteria are clear;
- no L2/L3 behavior is touched.

Current parked Phase 9 route does not require any immediate L1 task.

### L2 Gate

Stop before L2 tasks unless the user explicitly approves the specific task.

L2 includes:

- solver behavior changes;
- backend behavior changes;
- public CLI contract changes;
- JSON schema changes;
- presolve, LP, MIP, or dispatch behavior changes.

### L3 Gate

Stop before L3 tasks unless the user explicitly approves the specific task.

L3 includes:

- phase start;
- phase closure;
- architecture redesign;
- native implementation;
- dependency/build/packaging decisions;
- new solver capability lines.

## Phase 9 Closure Conditions

Phase 9 closure is not approved now.

A future Phase 9 closure path should satisfy:

1. User explicitly approves closure-readiness review or closure bookkeeping.
2. A closure-readiness audit confirms no active blockers.
3. The audit states whether deferred native implementation is acceptable as the Phase 9
   endpoint for the current roadmap.
4. The closure task is limited to allowed bookkeeping files.
5. The closure task does not start Phase 10.
6. The closure report records that native implementation remains deferred unless the user
   separately changes that decision.

Possible closure classification:

```text
phase9_complete_for_deferred_native_boundary_scope
```

This classification is only a possible future state. It is not current state.

## Phase 10 Planning Conditions

Phase 10 has not started.

Before Phase 10 planning:

1. The user must explicitly approve starting Phase 10 planning.
2. The task must be planning/design-only unless implementation is separately approved.
3. The task must not modify solver source code or tests unless explicitly scoped.
4. The task must define the Phase 10 purpose, scope, non-goals, dependency direction,
   review gates, and candidate atomic task sequence.
5. Starting Phase 10 planning must not imply Phase 10 implementation.

If Phase 9 remains open, Phase 10 planning requires explicit acceptance that planning is
allowed before Phase 9 closure, or a prior Phase 9 closure task.

## Native Implementation Gate

Native implementation remains deferred and unapproved.

Before any native implementation task:

1. The user must explicitly approve the exact task.
2. The implementation candidate must be named.
3. The implementation form must be named.
4. Build, dependency, platform, and generated-artifact policy must be explicit.
5. Tests must be availability-gated when native runtime support is absent by default.
6. Default solver dispatch must remain Python-only unless a separate dispatch task is
   approved.
7. Public CLI and JSON schema changes must remain out of scope unless separately
   approved.
8. The task must stop after one atomic implementation step.

## Current Authorized Maintenance — 2026-10-10

The user explicitly approved baseline organization followed by the presolve and MIP status-correctness repairs discovered in the restart audit. These are maintenance of the existing solver scope; native remains deferred, Phase 9 stays open/parked, and Phase 10 has not started.

Execute the three authorized tasks sequentially with separate contracts, reports and local commits. No push was requested. Local-ahead state produced by this approved sequence does not require repeated approval. Preserve unrelated work and do not expand into new capabilities or phase changes.

See `docs/development_restart.md` and matching `tasks/reports/20261010-*` for current evidence. Older create-file suggestions for existing local mirror files are superseded. After completing the authorized repairs, report next-step recommendations and stop.

### Recovery outcome

The baseline and both authorized status repairs are complete in separate local commits. The project environment is `.venv`; historical `resfs/` originals are preserved and locally ignored. Presolve now requires feasible-point evidence for a terminal empty-column unbounded status. MIP now resolves integer feasibility before promoting LP unboundedness, with strict integer coordinates on this proof path. Consult the matching reports for tests and final commit references.

Recommended next scope: establish independent small-instance correctness oracles and adversarial status regressions before expanding LP/MIP capabilities or reconsidering native acceleration. This recommendation does not issue another task or approve a phase transition. Native remains deferred, Phase 9 open/parked, Phase 10 not started.

### Subsequent authorized baseline — 2026-10-10

The user subsequently requested a push followed by the recommended baseline task.
Recovery commits 6bd9543, a2490ec and a4814f4 were pushed successfully to origin/main;
the new task started clean with ahead/behind `0 0` at a4814f4. This later authorization
supersedes the earlier sequence's no-push instruction for those completed commits.
Task `20261010-04-01_correctness-oracles` adds independent analytical LP checks, exact
finite integer enumeration and optional test-only HiGHS comparison. See
`docs/correctness_baseline.md` and its execution report for coverage and limitations.
The baseline task uses local-commit mode. Phase/native decisions remain unchanged.
Next recommended scope is a separately approved LP dual-result convention and
optimality-evidence task; no follow-on task is issued automatically.

### Authorized LP dual evidence — 2026-10-18

The user explicitly approved LP dual conventions, output and optimality verification
in the existing solver. Task `20261018-01-02_lp-dual-optimality` (revision 01 preserved)
adds original-row multipliers to both backends, fixed-aware presolve recovery, an
independent Python checker and compare-time validation, without adding JSON keys.
See `docs/lp_duality.md` for formulas, worked examples and limits, and the matching
report for tests and local commit/integration evidence. This continues the approved
baseline at 5cc88cb in a clean managed worktree, preserving primary-checkout research
notes. Git mode is local-commit; no push is included. Phase 9 remains open/parked,
native deferred and Phase 10 not started. A known revised Phase-I source-row cleanup
robustness obligation is documented for a separate atomic task, without altering the
current pivot/search algorithm or implying another task's execution approval.

### Development companion series — 2026-10-18

The user approved a dedicated, systematically arranged learning series that grows
with solver development and can later support thematic material or a textbook.
`learning/README.md` and `learning/CATALOG.md` are its entry points; stable lesson
IDs are independent of future chapter order. L0001 curates the completed LP dual
work with principles, code provenance, research connections, limits and exercises.
`docs/` keeps current reference material, `notes/` keeps original research history,
and tasks keep their existing roles. See tasks/README.md section 6.8 for prospective
learning deliveries; no historical contracts are rewritten. No solver/native/phase
change or push is included. Next solver recommendation remains the separately scoped
revised Phase-I cleanup-provenance task, with an L0001 update when that work occurs.
