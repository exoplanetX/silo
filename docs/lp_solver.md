# LP Solver

SILO currently includes an educational dense tableau simplex solver for small continuous LPs. It is a readable reference implementation and a solver-building laboratory, not a performance-oriented replacement for industrial LP solvers.

## Accepted Mathematical Class

```text
maximize c^T x + c0
subject to rows with <=, >=, or =
           x >= 0
           x continuous
           no finite variable upper bounds
```

The solver rejects minimization models, finite upper bounds, nonzero lower bounds, integer variables, and binary variables.

## Tableau Features

- Dense tableau implementation.
- Deterministic entering-column rule.
- Deterministic minimum-ratio leaving-row rule.
- Phase I / Phase II flow.
- Slack variables for `<=` rows.
- Surplus and artificial variables for `>=` rows.
- Artificial variables for equality rows.
- Negative RHS normalization.
- Infeasible LP detection through the Phase I artificial objective.
- Unbounded LP detection in Phase II.
- Solution diagnostics for primal values, slacks, reduced costs, and basis status.

## Current Non-Goals

- No sparse or industrial-grade revised simplex implementation.
- No dual simplex.
- No sparse factorization.
- No presolve or scaling.
- No MIP branch-and-bound.
- No cuts, decomposition, stochastic programming, or robust optimization.
- No external solver call in native algorithms.

The tableau path is intended to remain simple enough for tests and documentation to explain every mathematical convention.

## Native LP Solver Backends

SILO currently exposes two native LP backends through the CLI. The `tableau` backend is the educational reference path and is useful for inspecting full tableau algebra on small models. The `revised` backend is the basis-oriented path and is useful for future warm starts, reoptimization, and MIP relaxation work. The CLI default remains `tableau`.

## Planned Revised Simplex Layer

The LP layer includes a dense tableau reference solver and an initial revised simplex implementation documented in [`notes/10_revised_simplex_design.md`](../notes/10_revised_simplex_design.md). The revised path uses explicit basis objects and the shared standard-form builder as a foundation for later warm starts and reoptimization without changing the tableau reference implementation.

## Revised Simplex Preparation

Phase 3A adds a standard-form builder and explicit `Basis` dataclass. These components transform supported LP models into equality form and record deterministic basic/nonbasic column metadata before a future revised simplex iteration loop is implemented.

## Revised Simplex Feasible-Basis Path

SILO includes a primal revised simplex implementation for small LPs that already have a feasible slack basis. It handles continuous maximization LPs with nonnegative variables and `<=` rows directly through the standard-form slack basis.

## Revised Simplex Phase I

The revised simplex solver now supports Phase I construction for artificial-variable cases. It can solve small continuous maximization LPs with `<=`, `>=`, and `=` rows, including rows normalized from a negative RHS, while still excluding finite upper bounds, nonzero lower bounds, and integer or binary variables. Phase I maximizes the negative sum of artificial variables, removes artificial columns after feasibility is established, and then runs Phase II with the original objective.

## Revised Simplex Warm Starts

`RevisedSimplexSolver.solve_with_details()` returns a detailed result containing the final standard-form problem and basis. A compatible basis can be supplied to `solve_with_details()` to warm start another solve. This is currently a conservative interface intended for small LPs with the same standard-form structure; artificial-variable warm starts and basis mapping across model transformations remain future work.

## Public Reduced-Cost Convention

For maximization LPs, public reduced costs are reported for original variables as `c_j - pi^T A_j`. At optimality, basic original variables should have reduced costs near zero, and nonbasic variables at their lower bound should have nonpositive reduced costs within tolerance. The tableau implementation may store the opposite sign in its internal objective row, but public `Solution.reduced_costs` is normalized to the same convention used by revised simplex.

Both current native LP solvers intentionally leave `dual_values` empty. Dual-value exposure requires a separate mapping design because original rows may be `<=`, `>=`, or `=`, and negative RHS normalization can flip row signs before solving.

## Planned Presolve and Scaling Layer

Phase 4 will introduce conservative presolve and scaling diagnostics. The initial design is documented in [`notes/12_presolve_scaling_design.md`](../notes/12_presolve_scaling_design.md). Early presolve will prioritize traceability and solution reconstruction over aggressive reductions.

## Presolve Core

Phase 4 begins with immutable presolve result and diagnostics objects. The initial `Presolver` is intentionally a no-op that validates the model and returns a traceable `PresolveResult`; actual reductions are added in later tasks.

## Empty-Row and Empty-Column Presolve Diagnostics

The presolver now detects feasible empty rows, infeasible empty rows, and simple empty-column unboundedness. Feasible empty rows are removed from the returned presolved model with traceable reduction records. Empty columns are diagnostic-only except when a nonconstrained variable with positive maximization objective and no finite upper bound proves unboundedness.

## Fixed-Variable Presolve

The presolver can eliminate variables with equal lower and upper bounds by substituting their fixed values into constraints and the objective. The transformation is recorded with `ReductionType.FIXED_VARIABLE`, and recovered solutions restore fixed variable values in original model space.

## Scaling Diagnostics

The presolver now computes coefficient-range diagnostics without automatically scaling the model. Diagnostics report matrix coefficient range, RHS magnitude, objective magnitude, near-zero coefficients, and large-range warnings. Automatic scaling remains future work because primal, reduced-cost, and future dual-value mappings must be handled carefully.

## Presolve Diagnostics CLI

Use `silo presolve MODEL_PATH` to inspect presolve and scaling diagnostics without solving the model. This command does not change the default `silo solve` workflow.

## Repeated-Pass Presolve Plan

A repeated-pass presolve design note is available in [`notes/13_repeated_presolve_design.md`](../notes/13_repeated_presolve_design.md). The goal is to handle cases where one conservative reduction exposes another, such as fixed-variable elimination creating feasible empty rows.
