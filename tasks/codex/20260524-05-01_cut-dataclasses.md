# Codex Task: Add Cut Candidate Dataclasses

## Task Metadata

Task ID: 20260524-05-01
Task slug: cut-dataclasses
Task type: implementation
Related phase: Phase 6 / Cut Generation and Callbacks
Risk level: L1 controlled implementation
Git mode: push-on-success
Expected report path: tasks/reports/20260524-05-01_cut-dataclasses_report.md

## Objective

Add immutable cut candidate and cut metadata dataclasses with validation and stable
canonical-key behavior, backed by deterministic unit tests.

This is the first approved Phase 6 implementation task. Do not implement cut pools,
separators, callbacks, branch-and-bound integration, CLI behavior, or JSON schemas.

## Context

`notes/18_cut_callback_boundary_design.md` defines the Phase 6 cut/callback boundary. Its
first candidate implementation task is:

```text
Add immutable cut candidate and cut metadata dataclasses under `src/silo/cuts/`, with
validation and canonical-key tests.
```

The user explicitly approved this first Phase 6 implementation task under SILO-DOS Mode A.
This approval applies only to this atomic task.

Relevant files:

- `notes/18_cut_callback_boundary_design.md`
- `tasks/phases/phase_06_cut_callbacks.md`
- `src/silo/cuts/__init__.py`
- `src/silo/cuts/cut_pool.py` for read-only context only
- `src/silo/cuts/separator.py` for read-only context only

## Scope Lock

This task is atomic.

Primary objective:

- Add immutable dataclasses for cut metadata and cut candidates, plus validation and
  canonical-key tests.

Allowed changes:

- `src/silo/cuts/candidate.py`
- `src/silo/cuts/__init__.py`
- `tests/unit/test_cut_candidate.py`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-05-01_cut-dataclasses_report.md`

Supporting allowed change:

- `tasks/codex/20260524-05-01_cut-dataclasses.md` may be committed as the issued task
  contract for this execution.

Forbidden changes:

- Do not modify solver source code outside `src/silo/cuts/candidate.py` and
  `src/silo/cuts/__init__.py`.
- Do not modify `src/silo/cuts/cut_pool.py`.
- Do not modify `src/silo/cuts/separator.py`.
- Do not implement cut pool behavior.
- Do not implement separators.
- Do not implement callbacks.
- Do not integrate cuts into branch-and-bound.
- Do not modify branch-and-bound behavior.
- Do not modify node ordering, branching, pruning, incumbent update logic, LP solvers, or
  presolve.
- Do not modify CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not issue or execute any additional Phase 6 task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Implementation Content

Add a new `src/silo/cuts/candidate.py` module with immutable dataclasses and enums that
cover:

- cut validity scope, including global and node-local scope;
- cut activity state, including candidate, accepted, active, duplicate, rejected, and
  expired;
- cut metadata with source separator name, validity scope, optional deterministic cut id,
  optional node id, tolerance, message, and activity state;
- cut candidate with coefficients, sense, RHS, and metadata;
- validation for nonempty variable names, finite coefficients, nonzero coefficient vector,
  valid `ConstraintSense`, finite RHS, valid validity scope, valid activity state,
  nonempty source separator name, nonnegative node id when supplied, and positive finite
  tolerance;
- immutable normalized coefficient storage;
- a stable `canonical_key()` method that returns a deterministic tuple for duplicate
  detection, ordered by an optional caller-provided variable order and otherwise by
  variable name.

Export the new public cut dataclasses/enums from `src/silo/cuts/__init__.py`.

Update `tasks/phases/phase_06_cut_callbacks.md` with a brief Phase 6B note that records
the dataclass implementation. Do not change Phase 6 scope or acceptance criteria.

## Required Tests

Add `tests/unit/test_cut_candidate.py` with deterministic tests for:

- valid global cut candidate construction;
- valid node-local metadata construction;
- immutability of metadata and cut candidate objects;
- normalized coefficient copy that cannot be mutated through the caller's original dict;
- rejection of empty coefficient maps;
- rejection of empty variable names;
- rejection of nonfinite coefficients;
- rejection of all-zero coefficient vectors;
- rejection of nonfinite RHS;
- rejection of empty source separator name;
- rejection of nonpositive or nonfinite tolerance;
- rejection of negative node id;
- stable canonical key independent of input coefficient dict insertion order;
- canonical key respecting an explicit variable order;
- public exports from `silo.cuts`.

## Stop Conditions

Stop and report instead of proceeding if:

- implementing the dataclasses requires cut-pool behavior;
- implementing the dataclasses requires separator behavior;
- implementing the dataclasses requires branch-and-bound integration;
- implementing the dataclasses requires modifying branch-and-bound, LP solvers, presolve,
  CLI behavior, JSON schemas, examples, or `ROADMAP.md`;
- unrelated dirty repository changes make the implementation scope ambiguous.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_cut_candidate.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. Immutable cut metadata and cut candidate dataclasses are implemented.
2. Cut validity scope and cut activity state enums are implemented.
3. Validation covers all required invalid cases.
4. Coefficients are normalized into immutable internal storage.
5. `canonical_key()` is deterministic and covered by tests.
6. New cut dataclasses/enums are exported from `silo.cuts`.
7. `tests/unit/test_cut_candidate.py` passes.
8. `python scripts/check_quality.py` passes.
9. `git diff --check` passes.
10. No cut pool behavior is implemented.
11. No separators are implemented.
12. No callbacks are implemented.
13. No branch-and-bound behavior is changed.
14. No CLI behavior or JSON schemas are changed.
15. No additional Phase 6 task is issued or executed.
16. A report is created at the expected report path.

## Report Requirements

Create:

```text
tasks/reports/20260524-05-01_cut-dataclasses_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Implementation summary:
Validation behavior:
Tests added:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that no cut pool, separator, callback, branch-and-bound
integration, CLI behavior, JSON schema, example, or additional Phase 6 task was created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260524-05-01_cut-dataclasses.md src/silo/cuts/candidate.py src/silo/cuts/__init__.py tests/unit/test_cut_candidate.py tasks/phases/phase_06_cut_callbacks.md tasks/reports/20260524-05-01_cut-dataclasses_report.md
git commit -m "feat(cuts): add cut candidate dataclasses"
git push origin main
```

If push fails, preserve the local commit, record the failure in the report, and report the
failure clearly in the final response.

## Final Response

When finished, report only:

- whether cut candidate dataclasses were implemented;
- whether canonical-key validation tests were added;
- whether forbidden Phase 6 work was avoided;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
