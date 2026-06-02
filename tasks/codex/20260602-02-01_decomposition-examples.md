# Codex Task: Educational Decomposition Examples

## Task Metadata

Task ID: 20260602-02-01
Task slug: decomposition-examples
Task type: documentation-example
Risk level: L0 safe
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260602-02-01_decomposition-examples_report.md

## Objective

Add checked-in educational decomposition examples that demonstrate the existing toy
Benders and toy column-generation fixture drivers without changing solver behavior.

## Context

Phase 7A recorded the decomposition boundary design in:

```text
notes/19_decomposition_boundary_design.md
```

The design note lists checked-in educational decomposition examples as the next
conservative task after the toy Benders and toy column-generation drivers exist.

Completed Phase 7 work already added:

- immutable master/subproblem records;
- decomposition iteration-log and run-summary records;
- Benders cut and column candidate records;
- a no-op decomposition driver;
- a toy fixture-only Benders-style driver;
- a toy fixture-only column-generation-style driver.

This task must remain documentation/example work. It must not introduce new solver
behavior or execute a real decomposition algorithm.

## Scope Lock

This task is atomic.

Primary objective:

- Add small executable examples for the existing toy decomposition drivers.

Allowed changes:

- `examples/decomposition/toy_benders.py`
- `examples/decomposition/toy_column_generation.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260602-02-01_decomposition-examples_report.md`

Supporting allowed change:

- `tasks/codex/20260602-02-01_decomposition-examples.md` may be committed as the issued
  task contract for this execution.

Forbidden changes:

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify LP solver behavior.
- Do not modify MIP solver behavior.
- Do not modify presolve behavior.
- Do not modify cut or callback behavior.
- Do not implement a general Benders solver.
- Do not implement a general column-generation solver.
- Do not call LP or MIP solvers from the examples.
- Do not solve restricted master problems.
- Do not implement branch-and-price.
- Do not add generated output files to git.
- Do not issue or execute another Phase 7 task.
- Do not modify existing files under `tasks/codex/`.

## Required Implementation

Create two small, deterministic Python examples:

1. `examples/decomposition/toy_benders.py`
   - constructs fixture-only `ToyBenders*` records;
   - runs `ToyBendersDriver`;
   - prints a concise deterministic summary of termination reason and iteration counts;
   - includes a module docstring explaining that the example is toy-only and does not
     validate cuts for arbitrary models.

2. `examples/decomposition/toy_column_generation.py`
   - constructs fixture-only `ToyColumnGeneration*` records;
   - runs `ToyColumnGenerationDriver`;
   - prints a concise deterministic summary of termination reason and iteration counts;
   - includes a module docstring explaining the reduced-cost convention and that the
     example is toy-only, with no restricted-master solve and no branch-and-price claim.

The examples must:

- use only existing toy decomposition records and drivers;
- avoid `Model` inputs;
- avoid LP/MIP solver calls;
- avoid writing files;
- produce deterministic stdout;
- be readable as educational examples rather than tests or production code.

Add only a brief Phase 7J note to `tasks/phases/phase_07_decomposition.md`.

## Required Checks

Run at least:

```bash
git status --short
python examples/decomposition/toy_benders.py
python examples/decomposition/toy_column_generation.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. The two decomposition examples are checked in under `examples/decomposition/`.
2. The examples run successfully and print deterministic summaries.
3. The examples use only toy fixture records and existing toy drivers.
4. The examples do not require `Model` inputs.
5. The examples do not call LP or MIP solvers.
6. No solver source code is changed.
7. No tests are changed.
8. No public CLI behavior is changed.
9. No JSON schemas are changed.
10. No generated output files are added.
11. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7J note.
12. A report is created at the expected report path.
13. Required checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260602-02-01_decomposition-examples_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and execution:
Files changed:
Implementation summary:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that no solver source code, tests, public CLI behavior,
JSON schemas, LP/MIP solver behavior, general Benders solver, general column-generation
solver, branch-and-price behavior, or generated output files were modified or created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260602-02-01_decomposition-examples.md examples/decomposition/toy_benders.py examples/decomposition/toy_column_generation.py tasks/phases/phase_07_decomposition.md tasks/reports/20260602-02-01_decomposition-examples_report.md
git commit -m "docs(decomposition): add toy driver examples"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether the educational decomposition examples were added;
- whether no solver source code or tests were modified;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
