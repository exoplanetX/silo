# Native Kernel Candidate Selection

## Purpose

This note selects a first Phase 9 native-kernel candidate for later user review. It is a
design boundary only. It does not implement native code, approve native implementation,
change solver dispatch, add dependencies, expose CLI or JSON schema controls, or close
Phase 9.

## Readiness Basis

The Phase 9 readiness audit in
`tasks/reports/20260604-02-01_phase9-readiness-audit_report.md` classified the project
as `ready_for_user_native_kernel_design_review`, not ready for direct native-kernel
implementation. The audit found that the conservative backend boundary is in place:

- backend boundary smoke tests;
- immutable backend capability and availability records;
- passive Python-reference backend records;
- passive conformance fixture records;
- unavailable-native diagnostics tests;
- a no-op backend selector boundary;
- passive parity result records.

The audit also keeps native implementation blocked until a specific candidate, input and
output boundary, parity fixture set, build policy, and no-regression plan are approved.

## Selection Criteria

The first candidate should satisfy the criteria in
`notes/21_native_backend_boundary_design.md`:

- small input/output boundary;
- deterministic behavior independent of thread scheduling;
- no external solver calls;
- no default solver-path import of native modules;
- clear parity expectations against Python reference behavior;
- limited numerical tolerance surface;
- no public CLI or JSON schema contract;
- failure modes representable without changing public `Solution` schemas;
- no dependency on native build tools for normal installation.

The first candidate should also avoid solver policy. It should not choose node order,
perform presolve reductions, separate cuts, mutate callbacks, run decomposition loops, or
transform uncertainty models.

## Candidate Screen

### Tableau Or Revised-Simplex Pivot And Ratio-Test Primitives

This area is the best early candidate class. The Python functions are small and already
deterministic. The safest member is the tableau leaving-row ratio-test primitive:
`silo.lp.simplex.ratio_test.choose_leaving_row`.

It has a narrow boundary:

- input: tableau rows, an entering-column index, and a tolerance;
- output: a leaving-row index or `None`;
- convention: ignore pivot coefficients less than or equal to tolerance;
- convention: choose the minimum nonnegative ratio implied by the current normalized
  tableau row data;
- convention: break equal ratios by row order.

This primitive has no public CLI or JSON surface and no dependency on model objects,
branch-and-bound, presolve, cuts, decomposition, uncertainty, or external solvers.

### Small Canonical Or Vector Arithmetic Helpers

Small arithmetic helpers are also plausible, but the current candidate boundary is less
clear. Canonical-form construction and standard-form building are still tied to model
validation, column naming, row normalization, artificial-variable conventions, and
Python dataclasses. Moving any of that first would risk mixing native arithmetic with
model-convention policy. Pure vector helpers can be reconsidered after the ratio-test
fixture pattern exists.

### Branch-And-Bound Search-Control Primitives

Branch-and-bound primitives are rejected for the first native candidate. Node ordering,
branching-variable choice, pruning, incumbent comparison, and node-log order are solver
policy. Any change could alter default MIP behavior and would require a higher-risk
review gate.

### Presolve Reductions

Presolve reductions are rejected for the first native candidate. Even conservative
reductions change model shape, recovery requirements, diagnostics, and feasibility
interpretation. They are not an appropriate first native kernel.

### Cut Separation Or Callback Mutation

Cut separation and callback mutation are rejected. They can change LP relaxations, MIP
tree behavior, callback order, or future lazy-constraint semantics. Phase 6 intentionally
kept these boundaries conservative.

### Decomposition Loops

Decomposition loops are rejected. Benders and column-generation behavior includes master
and subproblem iteration policy, generated cuts or columns, convergence conventions, and
logs. These are too broad for the first native kernel.

### Uncertainty Transformations

Uncertainty transformations are rejected. Deterministic equivalents, robust
counterparts, uncertainty sets, and nonanticipativity conventions change model structure
and naming. They should remain Python reference behavior until much later.

## Recommended First Candidate

The recommended first native-kernel candidate is:

```text
tableau_leaving_row_ratio_test
```

This candidate corresponds to the Python reference behavior of
`silo.lp.simplex.ratio_test.choose_leaving_row`.

The candidate should not be wired into tableau simplex by default. A future
implementation task, if separately approved, should add only an optional native
implementation boundary and passive parity checks first. Solver dispatch and default LP
behavior must remain Python-only until a later explicit review gate.

## Candidate Boundary

The candidate boundary is:

- `rows`: normalized tableau rows represented as finite numeric row sequences, with the
  right-hand side in the final column;
- `entering_column`: a zero-based column index into each tableau row, excluding the
  right-hand-side position;
- `tolerance`: the tolerance used to decide whether a pivot coefficient is positive;
- output: the zero-based leaving-row index, or `None` when no row has a pivot coefficient
  greater than tolerance.

The semantic contract is:

- rows are treated as read-only;
- rows are already in the Python reference tableau convention;
- rows are expected to be rectangular and finite for parity fixtures;
- pivot coefficients less than or equal to tolerance are ignored;
- candidate ratios use the row right-hand side divided by the pivot coefficient;
- the minimum ratio wins;
- exact ratio ties use the smaller row index;
- no model object, basis object, solver object, status object, or file path enters this
  boundary.

## Default Behavior Preservation

This candidate does not alter default Python solver behavior because candidate selection
does not implement or connect native code. Any future implementation must remain
optional and unreachable from the default solver path until a separate task explicitly
approves dispatch behavior.

The default `TableauSimplexSolver`, `RevisedSimplexSolver`, MIP branch-and-bound, CLI
commands, JSON schemas, and public solution records must remain unchanged.

## Parity Fixture Requirements

Before native implementation, a separate task should add passive parity fixtures for the
selected candidate. The fixtures should cover:

- a single eligible leaving row;
- multiple eligible rows with a unique minimum ratio;
- equal ratios that break by smaller row index;
- pivot coefficients equal to tolerance, which must be ignored;
- pivot coefficients below tolerance, zero, or negative, which must be ignored;
- no eligible row, returning `None`;
- a small production-style tableau row set derived from existing Python fixture
  conventions without reading fixture files at runtime.

The first parity fixture set should use values far from numerical ambiguity except for
the explicit tolerance-boundary case. It should compare only the selected row index or
`None`, plus passive metadata such as fixture id and tolerance label.

## Conventions To Fix Before Implementation

The following conventions must be fixed before any native code is written:

- tolerance value and label, initially `DEFAULT_TOLERANCE = 1e-9`;
- whether tolerance is interpreted as strict `pivot > tolerance`;
- ratio tie-breaking by row index;
- finite numeric input requirement for parity fixtures;
- no mutation of input rows;
- no automatic fallback from native to Python inside the kernel;
- unavailable-native diagnostics when the optional native runtime is absent;
- parity mismatch diagnostics that remain outside public `Solution` schemas.

## Non-Goals

This candidate does not include:

- a full tableau simplex implementation;
- a revised simplex implementation;
- basis updates;
- entering-column selection;
- pivot-row normalization;
- model canonicalization;
- presolve;
- branch-and-bound;
- cut separation;
- callbacks;
- decomposition;
- uncertainty transformations;
- public CLI flags;
- JSON schema fields;
- native build-system or packaging changes;
- performance benchmarks or speedup claims.

## Implementation Prerequisites

Before native implementation can be considered, the project should have:

- passive candidate-specific parity fixtures;
- an unavailable-native diagnostic path for the candidate;
- a documented optional build and dependency policy;
- a platform and artifact exclusion policy;
- a decision packet for whether native code will be Python-extension based, standalone,
  or deferred;
- explicit user approval for the first implementation task.

## Review Gates Before Implementation

The next review gates are:

1. Approve a passive fixture task for `tableau_leaving_row_ratio_test`.
2. Review fixture coverage and diagnostics.
3. Approve or reject an optional native build/dependency plan.
4. Approve or reject the first native implementation task.
5. Keep solver dispatch disabled until a separate L2/L3 review approves integration.

No native implementation is approved by this note.

## Recommended Next Atomic Task

Recommended next task:

```text
Add passive parity fixture records for the tableau leaving-row ratio-test candidate.
```

Suggested risk: L1 controlled implementation if limited to passive fixture records and
tests, with no native implementation, no solver dispatch, no CLI or JSON schema changes,
no build or packaging changes, and no default solver behavior changes.

Explicit approval is required before execution because it continues Phase 9 native-kernel
preparation.
