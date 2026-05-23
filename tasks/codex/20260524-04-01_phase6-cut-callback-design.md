# Codex Task: Draft Phase 6 Cut and Callback Design

## Task Metadata

Task ID: 20260524-04-01
Task slug: phase6-cut-callback-design
Task type: design-note
Related phase: Phase 6 / Cut Generation and Callbacks
Risk level: L3 strategic planning
Git mode: local-commit
Expected report path: tasks/reports/20260524-04-01_phase6-cut-callback-design_report.md

## Objective

Draft a conservative Phase 6 design note for cut generation and callback boundaries that
can later guide implementation without disrupting the pure branch-and-bound path.

This is a planning/design-note task only. Do not implement cuts, callbacks, branch-and-cut,
or any solver behavior changes.

## Context

Phase 5 is closed for the current minimal branch-and-bound scope. `ROADMAP.md` defines
Phase 6 as the next capability line:

```text
Cut Generation and Callbacks
```

The Phase 6 goal is to separate cut management from the MIP tree and define a conservative
callback boundary. Phase 6 should preserve the existing pure branch-and-bound solver as
the default reference behavior and introduce cuts only through explicit, optional,
well-tested boundaries in later implementation tasks.

Relevant files:

- `ROADMAP.md`
- `tasks/phases/phase_06_cut_callbacks.md`
- `notes/15_branch_and_bound_design.md`
- `src/silo/mip/branch_and_bound.py` for read-only context only
- `src/silo/mip/node.py` for read-only context only
- `src/silo/mip/logging.py` for read-only context only
- recent Phase 5 reports under `tasks/reports/`

## Scope Lock

This task is atomic.

Primary objective:

- Create a design note that defines the Phase 6 cut-generation and callback boundary.

Allowed changes:

- `notes/18_cut_callback_boundary_design.md`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-04-01_phase6-cut-callback-design_report.md`

Supporting allowed change:

- `tasks/codex/20260524-04-01_phase6-cut-callback-design.md` may be committed as the
  issued task contract for this execution.

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify Phase 5 files.
- Do not implement cut generation.
- Do not implement callbacks.
- Do not modify branch-and-bound search logic.
- Do not modify node ordering, pruning rules, incumbent update logic, LP solvers, or
  presolve.
- Do not issue or execute any Phase 6 implementation task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Design Content

Create `notes/18_cut_callback_boundary_design.md` with a conservative design for Phase 6.
The note must include:

1. Purpose and scope:
   - explain why Phase 6 should separate cuts/callbacks from the MIP tree;
   - state that pure branch-and-bound remains the default behavior.
2. Current dependency boundary:
   - preserve `core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty`;
   - state that native algorithms must not call external solvers.
3. Cut representation boundary:
   - define cuts as linear constraints with documented validity scope;
   - distinguish globally valid cuts from node-local cuts;
   - state what metadata each cut should carry before implementation.
4. Separator boundary:
   - define a separator interface conceptually;
   - state that separators should inspect model/solution context and return candidate cuts
     without mutating core model state directly;
   - state that the first implementation should use a simple deterministic toy separator
     or no-op separator before any real cut family.
5. Cut pool lifecycle:
   - define candidate acceptance, duplicate detection, activation, and clearing rules at a
     design level;
   - state deterministic ordering requirements.
6. Callback boundary:
   - define allowed callback hook points conceptually, such as before node solve, after LP
     relaxation, after incumbent update, and after node prune;
   - state what callbacks may observe and what they must not mutate in the first design.
7. Integration with branch-and-bound:
   - specify that cuts must be disabled by default;
   - specify that branch-and-bound without cuts must remain behaviorally unchanged;
   - define how a later implementation should pass optional cut/callback components
     without creating circular dependencies.
8. Testing strategy:
   - outline deterministic tests for cut validity checks, duplicate cuts, cut-pool
     lifecycle, callback hook ordering, and no-regression behavior when cuts are disabled.
9. Non-goals:
   - exclude branch-and-cut performance claims, broad cut families, lazy constraints,
     user-defined arbitrary mutation callbacks, commercial solver callbacks, external
     solver calls, parallel tree search, and large benchmarks.
10. Candidate atomic task sequence:
    - list a small sequence of future Phase 6 implementation tasks, but do not issue those
      tasks.

Update `tasks/phases/phase_06_cut_callbacks.md` only with a brief Phase 6A note that
points to the design note and states that no implementation is included.

## Stop Conditions

Stop and report instead of proceeding if:

- drafting the design note requires modifying solver source code;
- drafting the design note requires modifying tests or examples;
- the design cannot preserve pure branch-and-bound as the default behavior;
- the design requires changing public CLI contracts or JSON schemas;
- the design requires starting Phase 6 implementation;
- unrelated dirty repository changes make the planning scope ambiguous.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Do not run the full solver test suite unless executable files are changed unexpectedly.
Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. `notes/18_cut_callback_boundary_design.md` is created.
2. The design note defines cut representation, separator, cut-pool, callback, and
   branch-and-bound integration boundaries.
3. The design note states that pure branch-and-bound remains the default behavior.
4. The design note states that cuts are disabled by default.
5. The design note includes deterministic testing guidance.
6. The design note includes explicit non-goals.
7. The design note lists candidate future atomic Phase 6 implementation tasks without
   issuing them.
8. `tasks/phases/phase_06_cut_callbacks.md` records only a brief Phase 6A design-note
   entry.
9. No solver source code is modified.
10. No tests are modified.
11. No examples are modified.
12. No CLI behavior or JSON schemas are modified.
13. `ROADMAP.md` is not modified.
14. No Phase 6 implementation task is issued or executed.
15. A report is created at the expected report path.
16. `git diff --check` passes.

## Report Requirements

Create:

```text
tasks/reports/20260524-04-01_phase6-cut-callback-design_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Design decisions:
Future candidate tasks:
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
JSON schemas, `ROADMAP.md`, or Phase 6 implementation tasks were modified or created.

## Git Instructions

Git mode:

```text
local-commit
```

After successful design note creation and checks:

```bash
git add tasks/codex/20260524-04-01_phase6-cut-callback-design.md notes/18_cut_callback_boundary_design.md tasks/phases/phase_06_cut_callbacks.md tasks/reports/20260524-04-01_phase6-cut-callback-design_report.md
git commit -m "docs(tasks): design Phase 6 cut callbacks"
```

Do not push unless explicitly instructed by the user.

## Final Response

When finished, report only:

- whether the Phase 6 cut/callback design note was created;
- whether the Phase 6 phase record was updated;
- whether implementation was not started;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
