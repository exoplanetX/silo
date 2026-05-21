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
- No default presolve and no automatic scaling.
- No MIP branch-and-bound.
- No cuts, decomposition, stochastic programming, or robust optimization.
- No external solver call in native algorithms.

The tableau path is intended to remain simple enough for tests and documentation to explain every mathematical convention.

## Native LP Solver Backends

SILO currently exposes two native LP backends through the CLI. The `tableau` backend is the educational reference path and is useful for inspecting full tableau algebra on small models. The `revised` backend is the basis-oriented path and is useful for future warm starts, reoptimization, and MIP relaxation work. The CLI default remains `tableau`.

## MIP Relaxation Boundary

The MIP layer now includes a deterministic LP relaxation builder for the first Phase 5 branch-and-bound scope. It converts binary and bounded nonnegative integer variables into continuous relaxation variables and represents their finite upper bounds as ordinary linear rows before calling an LP backend. This keeps the tableau and revised simplex solvers unchanged: they still receive only continuous maximization LPs with nonnegative variables and no direct finite variable upper bounds.

The relaxation builder is an internal Python API. SILO still does not expose a working branch-and-bound solver or MIP CLI path.

## Revised Simplex Layer

The LP layer includes a dense tableau reference solver and a revised simplex implementation documented in [`notes/10_revised_simplex_design.md`](../notes/10_revised_simplex_design.md). The revised path uses explicit basis objects and the shared standard-form builder as a foundation for warm starts and future reoptimization work without changing the tableau reference implementation.

## Revised Simplex Preparation

Phase 3A added a standard-form builder and explicit `Basis` dataclass. These components transform supported LP models into equality form and record deterministic basic/nonbasic column metadata used by the revised simplex implementation.

## Revised Simplex Feasible-Basis Path

SILO includes a primal revised simplex implementation for small LPs that already have a feasible slack basis. It handles continuous maximization LPs with nonnegative variables and `<=` rows directly through the standard-form slack basis.

## Revised Simplex Phase I

The revised simplex solver now supports Phase I construction for artificial-variable cases. It can solve small continuous maximization LPs with `<=`, `>=`, and `=` rows, including rows normalized from a negative RHS, while still excluding finite upper bounds, nonzero lower bounds, and integer or binary variables. Phase I maximizes the negative sum of artificial variables, removes artificial columns after feasibility is established, and then runs Phase II with the original objective.

## Revised Simplex Warm Starts

`RevisedSimplexSolver.solve_with_details()` returns a detailed result containing the final standard-form problem and basis. A compatible basis can be supplied to `solve_with_details()` to warm start another solve. This is currently a conservative interface intended for small LPs with the same standard-form structure; artificial-variable warm starts and basis mapping across model transformations remain future work.

## Public Reduced-Cost Convention

For maximization LPs, public reduced costs are reported for original variables as `c_j - pi^T A_j`. At optimality, basic original variables should have reduced costs near zero, and nonbasic variables at their lower bound should have nonpositive reduced costs within tolerance. The tableau implementation may store the opposite sign in its internal objective row, but public `Solution.reduced_costs` is normalized to the same convention used by revised simplex.

Both current native LP solvers intentionally leave `dual_values` empty. Dual-value exposure requires a separate mapping design because original rows may be `<=`, `>=`, or `=`, and negative RHS normalization can flip row signs before solving.

## Presolve and Scaling Layer

Phase 4 added conservative presolve and scaling diagnostics. The initial design is documented in [`notes/12_presolve_scaling_design.md`](../notes/12_presolve_scaling_design.md), and the completed Phase 4 scope is summarized in [`notes/14_phase4_completion_summary.md`](../notes/14_phase4_completion_summary.md). The presolve layer prioritizes traceability and solution reconstruction over aggressive reductions.

## Presolve Core

The presolve layer uses immutable result, diagnostics, scaling, and reduction record objects. `Presolver.run(model)` validates the model, applies conservative diagnostics and reductions, and returns a traceable `PresolveResult`.

## Empty-Row and Empty-Column Presolve Diagnostics

The presolver now detects feasible empty rows, infeasible empty rows, and simple empty-column unboundedness. Feasible empty rows are removed from the returned presolved model with traceable reduction records. Empty columns are diagnostic-only except when a nonconstrained variable with positive maximization objective and no finite upper bound proves unboundedness.

## Fixed-Variable Presolve

The presolver can eliminate variables with equal lower and upper bounds by substituting their fixed values into constraints and the objective. The transformation is recorded with `ReductionType.FIXED_VARIABLE`, and recovered solutions restore fixed variable values in original model space.

## Scaling Diagnostics

The presolver now computes coefficient-range diagnostics without automatically scaling the model. Diagnostics report matrix coefficient range, RHS magnitude, objective magnitude, near-zero coefficients, and large-range warnings. Automatic scaling remains future work because primal, reduced-cost, and future dual-value mappings must be handled carefully.

## Presolve Diagnostics CLI

Use `silo presolve MODEL_PATH` to inspect presolve and scaling diagnostics without solving the model. Use `silo solve MODEL_PATH --presolve` to explicitly solve a presolved model and recover the result in original model space. Default `silo solve MODEL_PATH` behavior does not run presolve.

## Repeated-Pass Presolve

The presolver now repeats conservative structural passes until no further empty-row or fixed-variable reductions are exposed. This allows fixed-variable elimination to create feasible empty rows that can be removed in a later pass. Diagnostics-only warnings do not trigger additional passes.

The repeated-pass design is documented in [`notes/13_repeated_presolve_design.md`](../notes/13_repeated_presolve_design.md).

## Original-Space Slack Recovery

When `silo solve MODEL_PATH --presolve` recovers a solver-space solution, slack values are recomputed from the original model constraints and recovered primal values. This keeps solution JSON in original model space even when presolve removed feasible empty rows.

## Phase 4 Regression Matrix

The current solve, presolve, and compare behavior for all checked-in JSON examples is documented in [`docs/phase4_regression_checklist.md`](phase4_regression_checklist.md) and enforced by `tests/regression/test_phase4_cli_regression_matrix.py`.
