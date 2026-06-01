# Decomposition Boundary Design

## 1. Purpose and Phase 7 Scope

Phase 7 introduces an educational decomposition layer above the existing modeling, LP,
MIP, and cut/callback boundaries. The goal is to make master-subproblem methods explicit
and inspectable, not to provide an industrial decomposition framework.

The first successful Phase 7 outcome should be a stable boundary for representing
decomposition roles, iteration records, generated cuts or columns, and deterministic
small-fixture workflows. Implementation should start with dataclasses and no-op or toy
drivers before adding any algorithmic loop that solves subproblems.

Phase 7 should cover:

- master problem wrappers;
- subproblem wrappers;
- Benders-style iteration structure;
- column-generation-style iteration structure;
- deterministic decomposition logs;
- small examples that expose decomposition logic.

Phase 7 must not change existing LP, MIP, presolve, cut, callback, CLI, or JSON schema
contracts.

## 2. Dependency Boundary and Allowed Direction

The dependency direction remains:

```text
core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty
```

This means:

- `core`, `modeling`, `presolve`, `lp`, and `mip` must not import decomposition modules.
- decomposition modules may import stable model, solution, LP, and MIP interfaces.
- decomposition modules must not force reverse imports into lower layers.
- native decomposition algorithms must not call external solvers.
- external solvers may appear only in interfaces, examples, or tests for comparison.

The decomposition package should eventually live under `src/silo/decomposition/`. It
should be an optional layer. Existing model construction, LP solving, MIP solving,
presolve, cut-pool behavior, callbacks, CLI commands, and JSON schemas must behave the
same when decomposition is not used.

If decomposition needs cut-like objects, the first design should prefer local
decomposition records such as Benders cut candidates or column candidates. Reusing Phase 6
cut objects can be considered later only if it does not couple cuts and decomposition in
both directions.

## 3. Master-Subproblem Abstraction

The master-subproblem boundary should represent roles before algorithms.

The master problem role is to hold the current restricted or relaxed problem that drives
the outer iteration. In a Benders-style method, the master may hold first-stage variables
and accumulated cuts. In a column-generation-style method, the restricted master problem
may hold only a subset of columns.

The subproblem role is to evaluate or improve a candidate master solution. In a
Benders-style method, a subproblem may test feasibility or compute information needed for
a feasibility or optimality cut. In a column-generation-style method, a pricing
subproblem may search for a column with improving reduced cost.

The first abstraction should avoid mutating user-authored models in place. It should pass
model-like objects and solution-like records across the boundary and return immutable or
append-only candidate records.

Information that may cross the boundary includes:

- model identifiers or labels;
- master solution values relevant to the subproblem;
- solver status;
- objective values or bounds;
- dual values or reduced costs when already exposed by the called solver;
- generated cut or column candidates;
- deterministic diagnostic messages.

Information that should not cross the boundary includes:

- mutable references to solver internals;
- callbacks that can alter node ordering, branching, pruning, or incumbent comparison;
- hidden edits to original model variables or constraints;
- public CLI or JSON schema changes.

Status handling should use existing `Solution.status` values where possible and add
decomposition-level termination reasons separately. A decomposition run may finish because
no improving cut or column is found, a subproblem is infeasible or unbounded, an iteration
limit is reached, or a toy fixture reaches a documented stopping condition.

## 4. Benders-Style Boundary

Benders-style support should begin as an educational boundary, not a general algorithm.

A conservative iteration structure is:

1. solve the current master model through an existing LP or MIP interface;
2. extract the master values needed by the subproblem;
3. build or evaluate a subproblem using a documented toy fixture rule;
4. return zero or more cut candidates;
5. append accepted cuts to the master-side record;
6. record an iteration summary;
7. stop when no cut is generated, a limit is reached, or a documented status occurs.

The master solve boundary may use `LPSolver.solve(model)` or a MIP solve interface when a
future task explicitly permits it. The Benders boundary must not change the LP or MIP
solver behavior, and must not require LP/MIP solvers to know decomposition exists.

The subproblem solve boundary should be a separate component that receives a read-only
subproblem context and returns a result record. The first implementation can use no-op or
toy subproblems rather than a full mathematical Benders subproblem.

Cut-candidate representation should be explicit. A future Benders cut candidate may store:

- deterministic cut id;
- cut type such as feasibility or optimality;
- coefficients in master variable names;
- sense and RHS;
- source subproblem name;
- iteration id;
- tolerance;
- message explaining the fixture-level validity assumption.

Feasibility and optimality cuts should begin as placeholders with documented assumptions.
The first Benders tasks should not claim valid cuts for arbitrary models. If dual values
are needed, the design must state which solver supplies them and what convention is used.

Stopping rules should be deterministic and small:

- stop when a subproblem returns no cut candidates;
- stop when a repeated cut is detected by canonical key;
- stop when an iteration limit is reached;
- stop on unsupported master or subproblem status with a clear diagnostic.

No Phase 7 Benders task should claim industrial Benders performance, broad model support,
or automatic decomposition detection.

## 5. Column-Generation-Style Boundary

Column-generation support should also begin as a boundary and toy workflow.

The restricted master problem role is to solve a model with a current subset of columns.
The pricing subproblem role is to inspect master information, typically dual values, and
return candidate columns.

A future column candidate may store:

- deterministic column id;
- variable name or generated column key;
- objective coefficient;
- coefficients in restricted-master rows;
- reduced cost;
- source pricing subproblem name;
- iteration id;
- tolerance;
- message explaining the fixture-level validity assumption.

Reduced-cost sign conventions must be documented before implementation. A simple policy is
to define the convention relative to the restricted master objective sense:

- for minimization pricing, an improving column has reduced cost below `-tolerance`;
- for maximization pricing, an improving column has reduced cost above `tolerance`.

If the early SILO restricted master only supports one objective sense, the implementation
task must state that restriction explicitly instead of silently converting signs.

Status handling should separate restricted-master status from pricing status. A pricing
subproblem may return no improving column, one improving column, an unsupported status, or
an error diagnostic. The driver should record the status without changing LP solver
schemas.

Stopping rules should be deterministic:

- stop when pricing returns no improving columns;
- stop when a duplicate column is returned;
- stop when an iteration limit is reached;
- stop when the restricted master or pricing subproblem returns an unsupported status.

No Phase 7 column-generation task should claim branch-and-price behavior, production
stabilization, large-instance performance, or automatic column discovery for arbitrary
models.

## 6. Decomposition Logs and Iteration Records

Decomposition diagnostics should be represented by immutable or append-only records. They
should not change public `Solution` schemas.

A future iteration record should include:

- deterministic iteration id;
- method label such as `benders` or `column_generation`;
- master status;
- master objective or bound when available;
- subproblem or pricing status;
- generated cut count;
- generated column count;
- accepted cut or column count;
- duplicate count when relevant;
- termination reason if the run stops at this iteration;
- diagnostic message.

The run-level result can wrap the final master solution and the iteration log. This result
should be separate from `Solution` so existing LP and MIP clients remain unchanged.

Logs should be deterministic across runs on the same fixture. Candidate ids, iteration ids,
and row or column ordering should be stable.

## 7. LP/MIP Integration Boundary

Decomposition may call existing LP and MIP layers through their public or stable internal
interfaces. For LP solves, the cleanest boundary is the `LPSolver.solve(model)` interface,
which returns a `Solution`. For MIP solves, a future task may use `BranchAndBoundSolver`
or `solve_with_details()` when the decomposition design explicitly needs MIP diagnostics.

Decomposition must not:

- modify `core`, `modeling`, `presolve`, `lp`, or `mip` modules to know about
  decomposition;
- change LP or MIP solver defaults;
- change branch-and-bound node ordering, branching, pruning, incumbent comparison, or cut
  callback behavior;
- change presolve behavior;
- change public CLI commands;
- change JSON model or solution schemas.

The decomposition layer may construct new model objects for master and subproblem solves.
It may use existing solution fields such as objective values, primal values, slack values,
dual values, reduced costs, basis status, and messages when those fields are already
available. It should not assume that every LP backend exposes every diagnostic unless a
task states that requirement and tests it.

External solvers remain out of native algorithm scope. A comparison interface or example
may use an external solver later, but native decomposition algorithms must use SILO's own
interfaces.

## 8. Testing Strategy

Phase 7 tests should be deterministic and tiny.

Master-subproblem abstraction tests should verify:

- immutable context/result records;
- validation of labels, iteration ids, statuses, and numeric values;
- no mutation of input models or solution dictionaries;
- stable ordering of generated records.

Toy Benders smoke tests should verify:

- one or two deterministic iterations on a documented fixture;
- generated feasibility or optimality cut placeholders with stable ids;
- duplicate detection or no-cut stopping;
- iteration-log contents and termination reason;
- no changes to existing LP/MIP behavior.

Toy column-generation smoke tests should verify:

- restricted-master and pricing result records;
- reduced-cost sign convention handling;
- no-improving-column stopping;
- deterministic column ids and iteration logs;
- no public schema changes.

Dependency and no-regression checks should verify:

- lower layers do not import decomposition;
- existing LP and MIP unit tests still pass when decomposition is unused;
- decomposition examples do not rely on external solvers.

## 9. Non-Goals and Out-of-Scope Items

Phase 7 planning and early implementation should not include:

- production-grade decomposition framework;
- large benchmarks or performance claims;
- branch-and-price;
- branch-and-cut-and-price;
- advanced stabilization;
- cut strengthening;
- automatic reformulation;
- automatic decomposition detection;
- callback mutation paths;
- public CLI changes;
- JSON schema changes;
- external solver calls inside native algorithms;
- changes to existing LP/MIP solver behavior;
- changes to presolve behavior;
- changes to Phase 6 cut/callback behavior;
- Phase 7 implementation inside the design-note task.

## 10. Candidate Atomic Task Sequence

The following tasks are candidates for future Phase 7 work. They are not issued by this
design note.

1. Upgrade the existing decomposition placeholder modules into immutable
   master/subproblem context/result records with validation tests.
2. Add deterministic decomposition iteration log dataclasses and termination-reason tests.
3. Add Benders cut candidate records and canonical-key tests without implementing a
   Benders solve loop.
4. Add column candidate records and reduced-cost convention tests without implementing a
   column-generation solve loop.
5. Add a no-op decomposition driver boundary that records one deterministic iteration and
   does not call LP or MIP solvers.
6. Add one toy Benders-style driver for a documented fixture, with explicit validity
   assumptions and no performance claims.
7. Add one toy column-generation-style driver for a documented fixture, with explicit
   reduced-cost conventions and no branch-and-price claims.
8. Add checked-in educational decomposition examples after the toy drivers exist.
9. Add a Phase 7 completion audit after the planned conservative decomposition boundary
   tasks are complete.
