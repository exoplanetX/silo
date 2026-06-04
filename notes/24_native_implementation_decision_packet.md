# Native Implementation Decision Packet

## Task And Candidate Summary

This packet reviews whether SILO should proceed toward native implementation for the
selected Phase 9 candidate:

```text
tableau_leaving_row_ratio_test
```

The candidate corresponds to the Python reference behavior of
`silo.lp.simplex.ratio_test.choose_leaving_row`. The candidate boundary is intentionally
small: normalized tableau rows, an entering-column index, a tolerance, and a leaving-row
index or `None`.

This packet is design-only and decision-review only. It does not implement native code,
approve native implementation, change solver dispatch, add native dependencies, modify
build or packaging files, expose CLI or JSON schema controls, close Phase 9, start Phase
10, or issue a follow-on task.

## Current Readiness Evidence

The repository now has the following Phase 9 evidence:

- `notes/21_native_backend_boundary_design.md` defines the conservative backend
  boundary, Python reference source-of-truth policy, optional backend interface boundary,
  parity strategy, diagnostics, dependency/build policy, and review gates.
- `notes/22_native_kernel_candidate_selection.md` selects
  `tableau_leaving_row_ratio_test` as the first candidate and rejects broader
  search-control, presolve, cut/callback, decomposition, and uncertainty candidates for
  first native work.
- `src/silo/interfaces/tableau_ratio_parity.py` provides passive candidate-specific
  parity fixtures.
- `src/silo/interfaces/tableau_ratio_native_diagnostics.py` provides passive
  candidate-specific unavailable-native diagnostics.
- `notes/23_native_build_dependency_policy.md` defines build, dependency, generated
  artifact, platform, test/CI, and solver-behavior policy.
- `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md` classifies the
  project as:

```text
ready_for_user_native_kernel_implementation_decision_review
```

This classification means the repository is ready for a user decision about the native
implementation path. It does not mean the repository is ready to implement native code
without a separate explicit approval.

## Risk Level

The implementation decision is L3 strategic.

It is L3 because approving native implementation would create a new solver capability
line and would eventually require decisions about native source boundaries, optional
runtime behavior, platform support, build products, generated-artifact exclusion,
availability-gated tests, and solver dispatch boundaries.

## Candidate Implementation Options

### Option A: Defer Implementation

Defer native implementation and keep Phase 9 focused on passive boundaries, diagnostics,
policy, and implementation-readiness review.

This option preserves normal Python installation, avoids build-system commitments, and
keeps default solver behavior unchanged. It is also consistent with the current native
build/dependency policy.

### Option B: Approve A Narrow Optional Python Extension Path Later

Approve, in a later task, a narrowly scoped optional Python extension path for only
`tableau_leaving_row_ratio_test`.

This is the preferred technical path if the user later decides to approve
implementation. It matches the small in-process boundary of the selected candidate better
than a standalone executable or broad native backend. It must remain optional, disabled by
default, and unreachable from default solver paths until a separate integration review.

### Option C: Reject Native Implementation For This Candidate

Reject native implementation for `tableau_leaving_row_ratio_test` and keep it permanently
Python-only.

This option is defensible if the expected educational value or performance benefit does
not justify native packaging complexity.

### Option D: Revise Candidate Or Prerequisites

Revise the candidate, implementation strategy, or prerequisites before any implementation
approval.

This option is appropriate if the user wants a different first native candidate, a
different native technology choice, more policy detail, or more passive tests before
implementation review.

## Recommended Option

Recommended option:

```text
defer implementation
```

Reason:

The repository has the necessary decision-review artifacts, but the current policy
recommendation is still to defer native implementation. The selected candidate is small
and deterministic, yet implementation would still move SILO from Python-reference
boundary preparation into native packaging and runtime support. Deferral keeps the next
step deliberate and avoids creating build, platform, and artifact obligations before the
user explicitly chooses to cross that gate.

## Exact Decision Language

Recommended defer sentence:

```text
I explicitly decide to defer native implementation for the
tableau_leaving_row_ratio_test candidate for now; continue Phase 9 only with design,
audit, or bookkeeping tasks unless I later explicitly approve a native implementation
task.
```

Alternative revise sentence:

```text
I explicitly request revising the Phase 9 native implementation decision packet before
any native implementation; do not implement native code, add dependencies, change build
or packaging files, change CLI or JSON schemas, or change solver dispatch.
```

Alternative reject sentence:

```text
I explicitly reject native implementation for the tableau_leaving_row_ratio_test
candidate; keep the candidate Python-reference only and do not issue native
implementation work for it.
```

Future approval sentence if the user later chooses to implement:

```text
I explicitly approve issuing and executing exactly one L3 native implementation scaffold
task for tableau_leaving_row_ratio_test, limited to an optional Python extension path
that remains disabled by default, with no default solver dispatch, no CLI changes, no
JSON schema changes, no external solver calls, no generated artifacts committed, no
Phase 9 closure, and no Phase 10 work; create the required report, run the required
checks, commit locally after checks pass, push if possible, and stop after one atomic
task.
```

This future sentence is only a template. It is not approval by this packet.

## Likely Future Files If Implementation Is Approved

A future implementation task may need to touch files like the following, but this packet
does not create or modify them:

- `native/README.md`, only if the native implementation boundary needs documentation;
- `native/<approved_kernel_path>/...`, only after native source layout approval;
- `src/silo/interfaces/<approved_native_boundary>.py`, only for an optional passive or
  explicitly requested native interface boundary;
- `tests/unit/<approved_native_parity_tests>.py`, only for availability-gated parity
  checks;
- `pyproject.toml`, only if a separate L3 task explicitly approves build or dependency
  changes;
- `.gitignore`, only if a separate task approves generated-artifact exclusion rules.

Any actual file set must be specified in a separate issued task.

## Invariants That Must Remain Unchanged

Any future native task must preserve:

- default Python solver path;
- `TableauSimplexSolver` behavior;
- `RevisedSimplexSolver` behavior;
- MIP branch-and-bound behavior;
- public CLI behavior;
- JSON model and solution schemas;
- backend selector behavior unless separately approved;
- absence of hidden fallback;
- absence of environment-variable dispatch;
- Python reference behavior as the source of truth;
- ratio-test tolerance convention: pivot coefficients less than or equal to tolerance are
  ignored;
- row-order tie-breaking convention for equal ratios;
- no external solver calls inside native algorithms;
- no generated native artifacts committed to git.

## Required Future Checks

Any future implementation task must include, at minimum:

- `pytest tests/unit/test_backend_boundary_smoke.py`;
- `pytest tests/unit/test_tableau_ratio_native_diagnostics.py`;
- `pytest tests/unit/test_tableau_ratio_parity.py`;
- candidate-specific native parity tests, availability-gated if native runtime support is
  unavailable by default;
- public CLI no-regression tests;
- public JSON schema no-regression checks if any schema-adjacent file is touched;
- source-boundary checks proving default solver imports do not load native modules;
- `git diff --check`.

Build commands and native tooling must be run only inside a task that explicitly approves
them.

## Possible Failure Modes

Future native implementation can fail through:

- packaging or compiler failures;
- platform-specific import failures;
- missing optional native runtime diagnostics;
- tolerance mismatch with Python reference behavior;
- row-order tie-breaking mismatch;
- hidden fallback to Python;
- default solver-path native imports;
- public CLI or JSON contract creep;
- generated artifacts entering git;
- non-deterministic native behavior;
- native implementation calling external solvers;
- source dependency direction violations.

These failure modes are why implementation remains a separate L3 review gate.

## Decision Boundary

This packet recommends deferring implementation for now. It also records a future
approval template if the user later decides to proceed.

The packet does not approve or implement native code. It does not create a native
implementation task. It does not change source code, tests, dependencies, build files,
packaging files, solver dispatch, CLI behavior, JSON schemas, roadmap files, phase files,
or future phase status.

## Next Recommended Atomic Task

Recommended next atomic task:

```text
Create a Phase 9 decision-response bookkeeping task after the user chooses defer, revise,
reject, or approve a future implementation path.
```

Suggested risk level:

```text
L0 if limited to task/report files or L3 if it changes Phase 9 strategic status.
```

Approval required:

```text
Yes, if the task records or acts on a strategic implementation decision.
```
