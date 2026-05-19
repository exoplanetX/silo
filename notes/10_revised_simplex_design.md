# Revised Simplex Design Note

## 1. Purpose

The dense tableau simplex solver is useful because it exposes the algebra of simplex in one visible object. It is easy to inspect, easy to test on small examples, and valuable as a reference implementation. It should not become the long-term LP engine for SILO. A tableau stores every transformed coefficient explicitly and updates all rows after each pivot. That is fine for teaching and small deterministic fixtures, but it does not match the way later solver layers need to work.

The revised simplex layer should make basis-oriented LP solving explicit. Instead of carrying a full tableau, it should carry the original or standard-form matrix data, a basis, and the linear algebra needed to compute basic primal values, reduced costs, search directions, and pivots. This is the bridge from the current educational tableau solver toward warm starts, MIP node reoptimization, and future decomposition methods.

The first revised simplex implementation should still be modest. It should remain a readable Python reference implementation for small LPs. It should not claim industrial performance, sparse factorization quality, or production numerical robustness. Its purpose is to establish correct conventions and interfaces before performance-oriented techniques are considered.

## 2. Current Tableau Solver Boundary

The current tableau solver supports small continuous maximization LPs through a dense Phase I / Phase II tableau. It accepts rows with `<=`, `>=`, and `=` senses, normalizes negative right-hand sides, introduces slack, surplus, and artificial variables, detects infeasibility through Phase I, detects unbounded directions in Phase II, and returns solution diagnostics such as primal values, slacks, reduced costs, and basis status.

That solver should remain in the codebase as a reference path. It gives future tests a simple oracle for small instances, especially while revised simplex is still being built. When revised simplex and tableau differ on a small LP, the failure should force a convention audit: objective sign, row transformation, artificial variables, reduced costs, basis status, or termination status.

The tableau implementation should not be stretched into reoptimization. Its role is to keep the algebra transparent. Revised simplex should own basis state, repeated solves, and the path toward higher layers.

## 3. Mathematical Form

The first revised simplex target should be standard equality form:

```text
maximize c^T x + c0
subject to A x = b
           x >= 0
```

The current user model permits rows with `<=`, `>=`, and `=` senses. A standard-form builder should transform those rows into equality form before the revised simplex loop starts:

- `<=` row: add a nonnegative slack variable.
- `>=` row: subtract a nonnegative surplus variable and, if no natural basis is available, add an artificial variable for Phase I.
- `=` row: add an artificial variable for Phase I unless a basis column is already available.
- Negative RHS rows: multiply the row by `-1`; flip `<=` and `>=`; keep equality as equality.

Finite upper bounds and nonzero lower bounds should remain future work. They require either bound-shifting, explicit upper-bound statuses, or a row-bound representation. Adding them too early would blur the first basis conventions. Minimization can also remain unsupported unless a clean, tested conversion to maximization is added as a separate task.

The standard-form builder should record enough mapping data to reconstruct public solution fields for original variables and original constraints. It should know which columns are original variables, slacks, surplus variables, and artificial variables, and how each transformed row maps back to an original constraint.

## 4. Basis Representation

The revised simplex layer needs an explicit `Basis` abstraction. At minimum it should record:

```text
basic column indices
nonbasic column indices
variable names
basis status for variables
```

The first implementation can use only two public statuses for original variables:

```text
basic
nonbasic_lower
```

This is enough while all variables are nonnegative and finite upper bounds are unsupported. The design should leave room for later statuses:

```text
basic
nonbasic_lower
nonbasic_upper
fixed
```

The `Basis` object should not hide ordering. The order of basic columns defines the basis matrix `B`, so tests should verify deterministic basis order after construction and pivots. Nonbasic columns should also have deterministic order because entering-column rules depend on it.

The basis should be separate from the model. A model describes the LP; a basis describes a solver state for a transformed LP. Keeping those separate matters for reoptimization, where the same model or a closely related model may be solved from an existing basis.

## 5. Revised Simplex Iteration

For a chosen basis, let `B` be the basis matrix, `N` the nonbasic matrix, `c_B` the objective coefficients of basic variables, and `c_N` the objective coefficients of nonbasic variables.

At each primal revised simplex iteration:

```text
x_B = B^{-1} b
pi^T = c_B^T B^{-1}
reduced_cost_j = c_j - pi^T A_j
choose entering nonbasic column j
solve B d = A_j
perform ratio test on x_B / d
pivot by replacing the leaving basic column with j
```

For maximization with variables at lower bound zero, the optimality condition is:

```text
reduced_cost_j <= tolerance for every nonbasic j
```

An entering column is a nonbasic column with positive reduced cost above tolerance. This public convention differs in sign from the tableau objective row, where the row currently stores `-reduced_cost`. The revised simplex implementation should use the mathematical reduced cost directly, then map output to the existing public `Solution.reduced_costs` convention. Tests should make this explicit.

If the entering column direction `d = B^{-1} A_j` has no positive component above tolerance, increasing the entering variable preserves feasibility and improves the objective without bound. The solver should return `UNBOUNDED`. Otherwise the leaving row is selected by the minimum ratio among positive direction components, with deterministic row-order tie breaking unless a documented anti-cycling rule is introduced later.

The first implementation may compute `B^{-1}` effects by dense linear solves. It should not implement sparse LU, eta updates, or Forrest-Tomlin updates in the first task.

## 6. Solution Information

Revised simplex should eventually populate the same public solution fields as tableau:

```text
objective_value
primal_values
slack_values
reduced_costs
basis_status
dual_values
message
```

`primal_values` should be reconstructed from the transformed solution by selecting original variable columns. `slack_values` should be computed from original constraints, not from transformed row values, using the same convention already used by tableau:

- `<=`: `rhs - activity`
- `>=`: `activity - rhs`
- `=`: `rhs - activity`

`reduced_costs` should be reported for original variables only. The revised simplex mathematical value `c_j - pi^T A_j` can be returned directly as the public reduced cost if tests confirm the same maximization convention as the current tableau solution output. Slack, surplus, and artificial columns should not appear in public reduced costs.

`basis_status` should be reported for original variables only in the first implementation. Internal structural variables can be inspected in tests through lower-level basis objects if needed.

Dual values should be added only when the convention is fully specified and tested. The natural candidate is the row multiplier vector `pi`, but signs and mapping back through row normalization must be handled carefully. It is better for the first revised simplex task to leave `dual_values` empty than to expose a weak convention.

## 7. Reoptimization Interface

The revised simplex layer should be designed for warm starts even if the first task does not implement all warm-start behavior. A future interface may look like:

```python
solve(model, basis=None)
```

or:

```python
solve_standard_form(problem, basis=None)
```

The important point is that `basis` is an explicit optional input, not hidden global state. This matters for:

- branch-and-bound, where child nodes differ by bound changes or extra constraints;
- column generation, where the master problem gains variables;
- Benders decomposition, where the master problem gains cuts;
- repeated solves after small RHS or objective changes.

The first warm-start design can be conservative. If a supplied basis is invalid for the transformed problem, the solver should reject it with a clear status or rebuild a basis through Phase I. Silent basis repair should be avoided until the conventions are tested.

## 8. Module Layout

A reasonable future layout is:

```text
src/silo/lp/simplex/revised.py
src/silo/lp/simplex/basis.py
src/silo/lp/simplex/factorization.py
src/silo/lp/simplex/standard_form.py
```

`standard_form.py` should transform SILO models into the equality-form LP used by simplex. It should store mappings from transformed columns and rows back to original model objects.

`basis.py` should define the basis state, status labels, pivot updates, validation helpers, and public basis diagnostics. It should not solve linear systems itself.

`factorization.py` should provide the dense reference linear algebra interface. In the first implementation this can be a thin wrapper around dense solves. Later it can hide LU updates without changing revised simplex control flow.

`revised.py` should contain the primal revised simplex loop, status handling, Phase I coordination, and conversion from internal results to `Solution`.

The existing `pricing.py` and `ratio_test.py` can either be reused or mirrored with basis-oriented helpers. If reused, their sign conventions must be made explicit because tableau pricing currently sees `-reduced_cost` in the objective row.

## 9. Testing Strategy

Future revised simplex tests should be small, deterministic, and paired with tableau results whenever possible. The first test set should include:

- the same optimal LPs used by the tableau solver;
- Phase I feasibility examples with `>=` and `=` rows;
- infeasible LPs detected through Phase I;
- unbounded LPs detected through the revised simplex direction test;
- known reduced-cost examples with a nonbasic original variable;
- basis-status examples for basic and nonbasic original variables;
- degenerate smoke cases with deterministic tie behavior;
- comparison against tableau on the user-facing JSON examples;
- validation that artificial variables do not appear in public solution fields.

Tests should also cover invalid or unsupported inputs: minimization if still unsupported, finite upper bounds, nonzero lower bounds, integer variables, and binary variables. These should remain `ERROR` cases until separate tasks expand solver scope.

## 10. Implementation Phases

The revised simplex work should be split into small tasks:

```text
Phase 3A: standard-form builder and Basis dataclass
Phase 3B: primal revised simplex for already feasible bases
Phase 3C: Phase I basis construction
Phase 3D: solution diagnostics parity with tableau
Phase 3E: warm-start/reoptimization interface
```

Phase 3A should not solve LPs. It should build transformed equality-form problems and explicit basis objects with deterministic tests.

Phase 3B should solve cases where a feasible slack basis is obvious, such as nonnegative `<=` rows.

Phase 3C should introduce Phase I basis construction for `>=`, `=`, and negative RHS rows.

Phase 3D should ensure solution diagnostics match tableau conventions on small instances.

Phase 3E should expose a cautious warm-start interface and test small RHS or objective perturbations.

## 11. Out of Scope for the First Implementation

The first revised simplex implementation should not include:

- sparse LU factorization;
- eta updates or Forrest-Tomlin updates;
- dual simplex;
- presolve;
- scaling;
- finite upper bounds;
- nonzero lower bounds;
- MIP integration;
- cut generation;
- decomposition algorithms;
- external solver backends;
- performance benchmarking;
- advanced anti-cycling beyond deterministic tie breaking;
- crash basis heuristics.

Those topics are important later, but adding them before the basic basis state is correct would make the solver harder to reason about. The next task should establish the standard-form builder and `Basis` dataclass first.
