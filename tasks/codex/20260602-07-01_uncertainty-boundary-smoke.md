# Codex Task: Uncertainty Boundary Smoke Tests

## Task Metadata

Task ID: 20260602-07-01
Task slug: uncertainty-boundary-smoke
Task type: regression-test-addition
Risk level: L0 safe
Related phase: Phase 8 / Stochastic and Robust Optimization Extensions
Git mode: push-on-success
Expected report path: tasks/reports/20260602-07-01_uncertainty-boundary-smoke_report.md

## Objective

Add uncertainty package boundary smoke tests that verify finite-scenario exports and
dependency isolation without adding new uncertainty implementation behavior.

## Context

Phase 8A created the uncertainty boundary design note:

```text
notes/20_uncertainty_boundary_design.md
```

Phase 8B added immutable finite-scenario records and validation tests. The latest report
recommends a narrow follow-up for uncertainty package dependency smoke tests and minimal
exports coverage before proceeding to stochastic wrapper records.

## Scope Lock

This task is atomic.

Primary objective:

- Add boundary smoke tests only.

Allowed changes:

- `tests/unit/test_uncertainty_boundary_smoke.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/reports/20260602-07-01_uncertainty-boundary-smoke_report.md`

Supporting allowed change:

- `tasks/codex/20260602-07-01_uncertainty-boundary-smoke.md` may be committed as the
  issued task contract for this execution.

Forbidden changes:

- Do not modify solver source code under `src/`.
- Do not modify existing tests.
- Do not modify examples.
- Do not modify docs.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not implement stochastic model wrappers.
- Do not implement robust model wrappers.
- Do not implement uncertainty sets.
- Do not implement deterministic equivalents.
- Do not issue or execute another Phase 8 task.
- Do not start Phase 9.

## Required Tests

Add deterministic smoke tests covering:

- `silo.uncertainty` public exports expose finite-scenario records and do not expose
  stochastic/robust/deterministic-equivalent transformation placeholders;
- public `Solution` schemas remain free of uncertainty/decomposition-style run fields;
- lower layers still do not import uncertainty;
- uncertainty modules do not import LP, MIP, presolve, cuts, decomposition, interfaces,
  or solver classes;
- no public CLI uncertainty command is exposed.

Update `tasks/phases/phase_08_stochastic_robust.md` with only a brief Phase 8C note.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_uncertainty_boundary_smoke.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. Boundary smoke tests are added.
2. Tests verify finite-scenario exports remain minimal.
3. Tests verify lower-layer dependency direction remains clean.
4. Tests verify uncertainty modules do not import solver layers.
5. Tests verify public CLI and `Solution` schemas are unchanged by uncertainty work.
6. No solver source code is changed.
7. No existing tests are modified.
8. No wrappers, uncertainty sets, deterministic equivalents, examples, CLI behavior, or
   JSON schemas are implemented or modified.
9. A report is created at the expected report path.
10. Required checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260602-07-01_uncertainty-boundary-smoke_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and execution:
Files changed:
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

The report must explicitly state that no wrappers, uncertainty sets,
deterministic-equivalent behavior, examples, CLI behavior, JSON schemas, or solver source
code were modified.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful tests and checks:

```bash
git add tests/unit/test_uncertainty_boundary_smoke.py tasks/phases/phase_08_stochastic_robust.md tasks/codex/20260602-07-01_uncertainty-boundary-smoke.md tasks/reports/20260602-07-01_uncertainty-boundary-smoke_report.md
git commit -m "test(uncertainty): add boundary smoke tests"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether uncertainty boundary smoke tests were added;
- whether no implementation behavior was changed;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
