# Phase 7 Decomposition Boundary Design Report

Task ID: 20260601-01-01

Objective:
Draft a Phase 7 decomposition-layer design note that defines conservative
master-subproblem abstractions, Benders-style and column-generation-style boundaries,
deterministic decomposition logs, dependency boundaries, non-goals, and candidate atomic
implementation tasks.

Risk and approval:

- Risk level: L3 strategic planning.
- Reason: this starts Phase 7 planning and defines a new solver capability line, but it is
  design-only and includes no implementation.
- Approval: the user explicitly approved starting Phase 7 planning and explicitly did not
  approve Phase 7 implementation.

Files changed:

- `tasks/codex/20260601-01-01_phase7-decomposition-design.md`
- `notes/19_decomposition_boundary_design.md`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-01-01_phase7-decomposition-design_report.md`

Design decisions:

- Created `notes/19_decomposition_boundary_design.md` as the Phase 7A design note.
- Defined Phase 7 as an educational decomposition boundary rather than a production-grade
  decomposition framework.
- Preserved the dependency direction:
  `core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty`.
- Stated that lower layers must not import decomposition modules.
- Defined master and subproblem roles around model/solution exchange, status boundaries,
  and deterministic diagnostics.
- Defined a conservative Benders-style boundary with master solve, subproblem solve, cut
  candidate placeholders, feasibility/optimality cut placeholders, status handling, and
  deterministic stopping rules.
- Defined a conservative column-generation-style boundary with restricted master problem,
  pricing subproblem, column candidate records, reduced-cost sign conventions, status
  handling, and deterministic stopping rules.
- Defined decomposition logs and iteration records as immutable or append-only diagnostics
  that do not change public `Solution` schemas.
- Stated that decomposition may call existing LP and MIP layers through stable interfaces
  while avoiding circular dependencies and avoiding behavior changes in lower layers.
- Added deterministic testing guidance for context/result records, toy Benders smoke
  tests, toy column-generation smoke tests, iteration logs, dependency boundaries, and
  no-regression checks.
- Added a brief Phase 7A note to `tasks/phases/phase_07_decomposition.md`.

Candidate future tasks:

- Upgrade the existing decomposition placeholder modules into immutable
  master/subproblem context/result records with validation tests.
- Add deterministic decomposition iteration log dataclasses and termination-reason tests.
- Add Benders cut candidate records and canonical-key tests without implementing a
  Benders solve loop.
- Add column candidate records and reduced-cost convention tests without implementing a
  column-generation solve loop.
- Add a no-op decomposition driver boundary that records one deterministic iteration and
  does not call LP or MIP solvers.
- Add one toy Benders-style driver for a documented fixture, with explicit validity
  assumptions and no performance claims.
- Add one toy column-generation-style driver for a documented fixture, with explicit
  reduced-cost conventions and no branch-and-price claims.
- Add checked-in educational decomposition examples after the toy drivers exist.
- Add a Phase 7 completion audit after the planned conservative decomposition boundary
  tasks are complete.

Checks run:

- `git status --short`
- `git diff --check`

Results:

- The Phase 7 decomposition boundary design note was created.
- The Phase 7 phase record was updated with only a brief Phase 7A design-note entry.
- No solver source code was modified.
- No tests were modified.
- No examples were modified.
- No CLI behavior was modified.
- No JSON model or solution schemas were modified.
- No `src/silo/decomposition/` implementation files were created.
- Existing tracked placeholder files under `src/silo/decomposition/` were inspected only
  to avoid incorrect planning assumptions; they were not modified.
- No decomposition tests were created.
- No Benders decomposition was implemented.
- No column generation was implemented.
- No Phase 7 implementation task was issued or executed.
- `git diff --check` passed.

Git status before:

```text
## main...origin/main
?? tasks/codex/20260524-12-01.md
?? tasks/codex/20260601-01-01_phase7-decomposition-design.md
```

Git status after:

```text
 M tasks/phases/phase_07_decomposition.md
?? notes/19_decomposition_boundary_design.md
?? tasks/codex/20260524-12-01.md
?? tasks/codex/20260601-01-01_phase7-decomposition-design.md
?? tasks/reports/20260601-01-01_phase7-decomposition-design_report.md
```

Local commit hash:

```text
Created after this report is staged; the final response records the final commit hash.
```

Push attempted:

```text
Pending final push attempt because the user explicitly requested push if possible; the
final response records whether push completed or failed.
```

Issues or conflicts:

- The user-supplied temporary task input `tasks/codex/20260524-12-01.md` remains
  untracked. It was not edited, deleted, renamed, staged, or committed.
- No unrelated tracked dirty changes were present before execution.

Next recommended atomic task:

After explicit user approval for Phase 7 implementation, issue exactly one L1 task to add
decomposition package scaffolding and immutable master/subproblem context/result records
with validation tests.
