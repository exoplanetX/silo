# Codex Task 20260521-05-01: Draft Repeated-Pass Presolve Design Note

## Task Metadata

Task file:

```text
tasks/codex/20260521-05-01_repeat-presolve-note.md
```

Execution report file:

```text
tasks/reports/20260521-05-01_repeat-presolve-note_report.md
```

Recommended local commit message:

```text
Draft repeated-pass presolve design note
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

---

## 1. Background

SILO now has a conservative presolve layer with:

- empty-row diagnostics and feasible empty-row removal;
- empty-column diagnostics and simple empty-column unboundedness detection;
- fixed-variable elimination with solution recovery;
- coefficient-range and scaling diagnostics;
- `silo presolve MODEL_PATH`;
- optional `silo solve MODEL_PATH --presolve`.

The current fixed-variable elimination intentionally does not run an iterative presolve loop. If fixed-variable substitution creates a new empty row, that row is left for a future repeated-pass presolve design.

The previous task report recommended:

```text
Phase 4H: presolve repeated-pass design for rows made empty by fixed-variable elimination.
```

This task should create the design note for that future implementation.

---

## 2. Goal

Create a technical design note for repeated-pass presolve.

The note should specify:

1. why repeated-pass presolve is needed;
2. how repeated passes interact with existing reductions;
3. how to avoid infinite loops;
4. how reduction order should be defined;
5. how diagnostics and reductions should be ordered;
6. how solution recovery should work when multiple reductions stack;
7. how repeated passes should interact with `silo solve --presolve`;
8. what the first implementation should and should not include.

This task is design-only. Do not implement repeated-pass presolve in this task.

---

## 3. Save This Task File

Create:

```text
tasks/codex/20260521-05-01_repeat-presolve-note.md
```

Save this full task prompt into that file.

Do not edit, rename, delete, or move any existing files under:

```text
tasks/codex/
```

This task may only add the new task file above.

---

## 4. Allowed Files to Modify or Add

You may add:

```text
notes/13_repeated_presolve_design.md
tasks/reports/20260521-05-01_repeat-presolve-note_report.md
```

You may update:

```text
docs/lp_solver.md
tasks/phases/phase_04_presolve_scaling.md
```

only if needed to link or align the design note.

You may update:

```text
README.md
```

only with a very short reference if appropriate. Keep README concise.

Do not modify presolve implementation files.

Do not modify CLI implementation files.

Do not modify solver implementation files.

---

## 5. Do Not Do

Do not implement repeated-pass presolve.

Do not modify `Presolver.run()` behavior.

Do not modify fixed-variable elimination behavior.

Do not modify empty-row or empty-column diagnostics behavior.

Do not modify scaling diagnostics behavior.

Do not modify `silo solve --presolve`.

Do not modify `silo presolve`.

Do not modify tableau or revised simplex.

Do not modify JSON reader or solution writer.

Do not change JSON model format.

Do not change solution JSON schema.

Do not implement MIP.

Do not add cuts, decomposition, stochastic programming, robust optimization, or native backend code.

Do not add external solver calls.

Do not add dependencies.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not force push.

Do not push unless explicitly instructed by the user.

---

## 6. Required Design Note

Create:

```text
notes/13_repeated_presolve_design.md
```

Target length: approximately 1,500–2,500 words.

Use this structure:

```markdown
# Repeated-Pass Presolve Design Note

## 1. Purpose

## 2. Current Presolve Boundary

## 3. Why a Single Pass Is Not Enough

## 4. Pass Ordering

## 5. Termination and Change Detection

## 6. Reduction Ordering and Traceability

## 7. Solution Recovery Through Multiple Reductions

## 8. Status Priority Across Passes

## 9. Interaction with CLI Solve and Presolve Diagnostics

## 10. Testing Strategy

## 11. Proposed Implementation Phases

## 12. Out of Scope for the First Implementation
```

---

## 7. Content Requirements

### 7.1 Purpose

Explain that repeated-pass presolve is needed because one safe transformation may expose another safe transformation.

Example:

```text
x fixed at 2
constraint x - 2 = 0
```

After substituting `x = 2`, the row becomes:

```text
0 = 0
```

which can then be removed as a feasible empty row.

Explain that repeated-pass presolve should preserve SILO’s conservative philosophy: deterministic, traceable, and recoverable.

### 7.2 Current Presolve Boundary

Summarize the current presolve layer:

```text
empty-row detection/removal
empty-column diagnostics/unboundedness
fixed-variable elimination
scaling diagnostics
solution recovery for fixed variables
silo presolve
silo solve --presolve
```

State that current behavior is intentionally single-pass.

### 7.3 Why a Single Pass Is Not Enough

Include examples where repeated passes matter:

1. fixed-variable substitution creates an empty row;
2. fixed-variable substitution creates an infeasible empty row;
3. removing one row may reveal an empty column;
4. fixed-variable elimination may update objective and remove variables, then empty-column diagnostics should be reconsidered;
5. multiple fixed variables may cascade.

Do not claim all these should be implemented immediately.

### 7.4 Pass Ordering

Recommend a deterministic pass order.

Suggested first repeated-pass order:

```text
1. validate model
2. scaling diagnostics on original model
3. empty-row infeasibility check
4. empty-column unboundedness check
5. feasible empty-row removal
6. fixed-variable elimination
7. repeat structural passes if the model changed
8. stop when no structural change occurs
```

Discuss whether scaling diagnostics should be recomputed on every pass or only on original model. Recommended first implementation:

```text
report scaling diagnostics on the original input model only
```

because diagnostics are user-facing and should describe the submitted model.

### 7.5 Termination and Change Detection

Define termination:

```text
repeat until no structural reduction is applied
```

A structural reduction includes:

```text
removing a feasible empty row
removing a fixed variable
```

A diagnostic-only warning should not trigger another pass.

Add a maximum pass limit as a safety guard, e.g.:

```text
max_passes = number_of_variables + number_of_constraints + 1
```

If max passes is reached, return a clear diagnostic or error status.

Discuss that proper reductions should strictly decrease row or variable count, so infinite loops should not occur.

### 7.6 Reduction Ordering and Traceability

Reduction records must be deterministic.

Specify ordering rule:

```text
pass order first, then within each pass:
  empty-row reductions in constraint order
  fixed-variable reductions in variable order
```

The complete reduction log should preserve the exact order in which transformations were applied.

This matters because solution recovery is applied in reverse reduction order when future reductions require reverse mapping.

### 7.7 Solution Recovery Through Multiple Reductions

Explain that `PresolveResult.recover_solution()` should eventually recover through all reductions in reverse order.

Current fixed-variable recovery already restores fixed variable primal values.

Future repeated-pass recovery should preserve:

```text
fixed variable values
objective value
original-space primal_values
basis_status for fixed variables
reduced_costs for fixed variables
slack_values in original constraint space
```

Explain that slack recomputation from the original model may become preferable once multiple row reductions are involved.

### 7.8 Status Priority Across Passes

Define priority:

```text
INFEASIBLE empty row > UNBOUNDED empty column > REDUCED > NO_CHANGE
```

But across passes, clarify:

- if any pass detects infeasibility, stop immediately;
- if any pass detects unboundedness, stop immediately;
- if reductions occurred and no terminal status occurs, final status is `REDUCED`;
- if no reductions occur and only warnings exist, final status is `NO_CHANGE`.

### 7.9 Interaction with CLI

Explain:

```text
silo presolve MODEL_PATH
```

should show the final repeated-pass presolve result.

Explain:

```text
silo solve MODEL_PATH --presolve
```

should solve the final presolved model and recover the original-space solution.

Default:

```text
silo solve MODEL_PATH
```

should remain unchanged.

### 7.10 Testing Strategy

Specify future tests:

1. fixed variable creates feasible empty row;
2. fixed variable creates infeasible empty row;
3. fixed variable removal followed by empty-column warning;
4. multiple fixed variables across passes;
5. reduction order across passes;
6. no repeated pass triggered by diagnostics-only warnings;
7. max-pass guard;
8. recovered solution still includes all original fixed variables;
9. recovered objective not double counted;
10. `silo solve --presolve` works on repeated-pass examples;
11. `silo presolve` shows reductions in deterministic order.

### 7.11 Proposed Implementation Phases

Break future implementation into small tasks:

```text
Phase 4H: repeated-pass presolve design note
Phase 4I: repeated-pass presolver loop with empty-row-after-fixed-variable cases
Phase 4J: original-space slack recomputation after presolve recovery
Phase 4K: repeated-pass CLI regression examples
```

Do not implement these tasks now.

### 7.12 Out of Scope

Explicitly exclude:

```text
general row redundancy detection
row aggregation
duplicate-row removal
singleton-row bound tightening
automatic scaling
MIP presolve
dual reductions
probing
basis crash
performance-focused presolve
```

---

## 8. Optional Documentation Updates

If updating:

```text
docs/lp_solver.md
```

add only a short note:

```markdown
## Repeated-Pass Presolve Plan

A repeated-pass presolve design note is available in `notes/13_repeated_presolve_design.md`. The goal is to handle cases where one conservative reduction exposes another, such as fixed-variable elimination creating feasible empty rows.
```

If updating:

```text
tasks/phases/phase_04_presolve_scaling.md
```

mention Phase 4H as the repeated-pass design step.

Do not over-expand documentation.

---

## 9. Execution Report

Create:

```text
tasks/reports/20260521-05-01_repeat-presolve-note_report.md
```

The report should include:

```markdown
# Repeated-Pass Presolve Design Note Report

## Summary

## Files Changed

## Main Design Decisions

## Proposed Implementation Phases

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend:

```text
Phase 4I: implement repeated-pass presolver loop for empty-row-after-fixed-variable cases.
```

Do not record execution results by editing the issued task file.

---

## 10. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --presolve
python -m silo.cli.main presolve examples/json/production.json
python -m silo.cli.main compare examples/json/production.json
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo solve examples/json/production.json --presolve
silo presolve examples/json/production.json
silo compare examples/json/production.json
```

Fix any failures.

---

## 11. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Draft repeated-pass presolve design note"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

---

## 12. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260521-05-01_repeat-presolve-note.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `notes/13_repeated_presolve_design.md` exists.
4. The note explains why repeated-pass presolve is needed.
5. The note defines pass ordering.
6. The note defines termination and change detection.
7. The note defines reduction ordering and traceability.
8. The note discusses solution recovery through multiple reductions.
9. The note defines status priority across passes.
10. The note discusses CLI interactions.
11. The note defines future testing strategy.
12. The note breaks implementation into small future tasks.
13. No presolve implementation code is changed.
14. No solver implementation code is changed.
15. No CLI behavior is changed.
16. No JSON model or solution schema changes are made.
17. `tasks/reports/20260521-05-01_repeat-presolve-note_report.md` exists.
18. `pytest` passes.
19. `python scripts/check_quality.py` passes.
20. CLI help/version/solve/presolve/compare commands work.
21. A local commit is created with message:

```text
Draft repeated-pass presolve design note
```

22. The task is not pushed unless the user explicitly instructs Codex to push.
