# Cut and Callback Boundary Design

## 1. Purpose and Scope

Phase 6 introduces a conservative cut-generation and callback boundary above the current
pure branch-and-bound solver. The goal is not to turn SILO into a full branch-and-cut
solver in one step. The goal is to define where cuts can be represented, validated,
deduplicated, activated, and observed without making the existing MIP tree harder to
reason about.

Pure branch-and-bound remains the default behavior. A model solved without explicit cut or
callback components must follow the same node selection, branching, pruning, incumbent
update, diagnostics, and CLI output contracts established in Phase 5. Cuts must be
optional, disabled by default, and introduced only through tested extension points.

Phase 6 should first make boundaries explicit. Implementation should start with a no-op
separator or deterministic toy separator before adding any real cut family. This keeps the
first cut path focused on lifecycle correctness rather than algorithmic performance.

## 2. Current Dependency Boundary

The dependency direction must remain:

```text
core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty
```

The `core` package must not depend on MIP, cuts, decomposition, or uncertainty modules.
The LP solvers must remain LP solvers. The MIP layer may call LP relaxations, and a future
cut layer may provide optional cut components to MIP, but cuts must not cause reverse
imports into `core`, `modeling`, `presolve`, or `lp`.

Native algorithms must not call external solvers. External solvers may appear only in
interfaces, examples, or tests for comparison. Phase 6 cut and callback design must assume
the existing native tableau and revised simplex backends are the LP relaxation engines.

## 3. Cut Representation Boundary

A cut is a linear constraint with documented validity scope. It should be representable
using the same mathematical convention as ordinary SILO linear rows, but it should carry
metadata that distinguishes it from user-authored model constraints and node-local
branching constraints.

The design should distinguish at least two validity scopes:

- Globally valid cuts are valid for every feasible solution of the original MIP model.
- Node-local cuts are valid only under the local branching constraints of one search-tree
  node or its descendants, depending on the separator contract.

Before implementation, each candidate cut should be able to carry:

- deterministic cut id or deterministic source key;
- linear coefficients in existing variable names;
- constraint sense and RHS;
- validity scope;
- source separator name;
- optional node id for node-local cuts;
- tolerance used for violation checking;
- human-readable reason or message;
- activity state such as candidate, accepted, active, duplicate, rejected, or expired.

Cut metadata should make diagnostics possible without changing the public `Solution`
schema. A cut should not mutate the original model object directly. The branch-and-bound
integration can later choose to materialize accepted cuts into LP relaxation rows for a
specific solve step.

## 4. Separator Boundary

A separator is a component that inspects model and solution context and returns candidate
cuts. Conceptually, a separator should receive read-only context such as:

- original model;
- current node;
- current LP relaxation solution;
- current incumbent value, if any;
- existing cut-pool state needed for duplicate checks;
- configured tolerances.

A separator should return candidate cuts without mutating core model state, MIP tree
state, incumbent state, or the LP solver. This functional boundary makes deterministic
tests easier and avoids hidden algorithmic changes.

The first implementation should use either:

- a no-op separator that always returns no cuts; or
- a deterministic toy separator whose generated cut is deliberately simple, documented,
  and valid for a tiny checked fixture.

The first separator task should not introduce a broad cut family. It should test the
separator API and lifecycle boundary, not cut performance.

## 5. Cut Pool Lifecycle

The cut pool owns candidate acceptance, duplicate detection, activation, and clearing.
It should be separate from branch-and-bound node storage and separate from the LP
relaxation builder.

At a design level, the lifecycle should be:

1. A separator returns candidate cuts in deterministic order.
2. The pool validates basic structure: known variable names, finite coefficients, supported
   sense, finite RHS, and supported validity scope.
3. The pool computes a canonical key for duplicate detection.
4. Duplicate candidates are marked duplicate or ignored without changing active cuts.
5. Accepted cuts are stored in insertion order or deterministic key order.
6. Active cuts are selected deterministically for a node relaxation.
7. Node-local cuts are cleared when their scope expires.
8. Global cuts remain available until the solve ends unless a later policy explicitly
   supports aging.

Duplicate detection should canonicalize coefficient order by model variable order and use
documented tolerances. The first implementation should avoid aggressive cut purging,
aging, efficacy filtering, or dominance logic.

## 6. Callback Boundary

Callbacks should begin as observation and controlled extension hooks, not arbitrary
mutation points. The first design should define hook points without giving callbacks the
ability to silently alter solver conventions.

Candidate hook points are:

- before node solve;
- after LP relaxation solve;
- after candidate cut separation;
- after cut-pool update;
- after incumbent update;
- after node prune;
- after child creation;
- at solve completion.

In the first callback design, callbacks may observe:

- node id and depth;
- parent id;
- LP relaxation status and objective;
- prune reason;
- branching variable;
- incumbent value;
- cut counts and cut ids;
- solver status and diagnostics.

Callbacks must not mutate:

- the original model;
- core variables or constraints;
- LP solver internals;
- node ordering;
- branching rules;
- pruning rules;
- incumbent comparison;
- public CLI or JSON schemas.

Any future callback that can add cuts should do so by returning candidate cuts through the
same separator/cut-pool boundary, not by editing the tree or model directly.

## 7. Integration with Branch-and-Bound

Cuts must be disabled by default. A default `BranchAndBoundSolver()` invocation should
produce the same behavior as the Phase 5 solver. No-cut behavior should be covered by
explicit no-regression tests before and after cut integration.

A later implementation should pass optional cut and callback components into the MIP
solver through constructor arguments or a small configuration object. The default value
should be `None` or an explicit no-op component. This avoids changing existing call sites.

The branch-and-bound solve loop should treat cut integration as an optional step after LP
relaxation solve and before branching or pruning decisions, but the exact placement needs
careful implementation review. A conservative first integration can run with a no-op
separator and verify that the control flow does not change when cuts are disabled.

Cut modules should live under `src/silo/cuts/`. They may depend on core/modeling concepts
needed to describe linear constraints and on public MIP context records when needed, but
they should not introduce circular dependencies that force MIP dataclasses to depend on
cut implementation details. If MIP needs to expose cut context, prefer small protocol-like
records or simple immutable dataclasses.

## 8. Testing Strategy

Phase 6 tests should be deterministic and small.

Cut representation tests should verify:

- valid candidate construction;
- rejection of unknown variables;
- rejection of invalid coefficients, unsupported senses, invalid RHS, or missing scope;
- stable canonical keys.

Cut-pool tests should verify:

- duplicate detection;
- deterministic insertion or key ordering;
- global and node-local scope handling;
- activation for a node;
- clearing of expired node-local cuts;
- no hidden mutation of original model objects.

Callback tests should verify:

- hook ordering on a tiny deterministic solve;
- read-only callback observations;
- rejection or absence of arbitrary mutation paths;
- stable event records for no-op callbacks.

Branch-and-bound integration tests should verify:

- cuts disabled by default;
- no-regression behavior for existing MIP fixtures when cuts are disabled;
- no-op separator produces the same solution and node diagnostics as the no-cut path;
- a simple deterministic toy separator, if added, changes only the explicitly tested
  optional cut-enabled path.

## 9. Non-Goals

Phase 6 should not begin with:

- branch-and-cut performance claims;
- a broad family of cuts;
- lazy constraints;
- user-defined arbitrary mutation callbacks;
- commercial solver callback emulation;
- external solver calls;
- parallel tree search;
- large benchmarks;
- automatic MIP presolve;
- changes to public CLI contracts;
- changes to JSON model or solution schemas;
- hidden changes to branch-and-bound defaults.

The first successful Phase 6 outcome is a stable boundary with deterministic tests, not a
faster MIP solver.

## 10. Candidate Atomic Task Sequence

The following are candidate future Phase 6 tasks. They are not issued by this design note.

1. Add immutable cut candidate and cut metadata dataclasses under `src/silo/cuts/`, with
   validation and canonical-key tests.
2. Add a deterministic cut pool with duplicate detection, activation, and scope-clearing
   tests.
3. Add no-op separator and separator protocol tests, without changing branch-and-bound
   behavior.
4. Add read-only callback event records and hook-order tests using no-op callbacks.
5. Integrate optional no-op cut/callback components into branch-and-bound while proving
   no-regression behavior when cuts are disabled.
6. Add one deterministic toy separator for a tiny fixture, with explicit validity
   documentation and no performance claims.
