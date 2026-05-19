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

- No revised simplex yet.
- No dual simplex.
- No sparse factorization.
- No presolve or scaling.
- No MIP branch-and-bound.
- No cuts, decomposition, stochastic programming, or robust optimization.
- No external solver call in native algorithms.

The tableau path is intended to remain simple enough for tests and documentation to explain every mathematical convention.

## Planned Revised Simplex Layer

The current implementation uses a dense tableau solver. The next LP-layer goal is a revised simplex design documented in [`notes/10_revised_simplex_design.md`](../notes/10_revised_simplex_design.md). That layer should introduce explicit basis objects, standard-form builders, and a path toward warm starts and reoptimization without changing the current tableau reference implementation.

## Revised Simplex Preparation

Phase 3A adds a standard-form builder and explicit `Basis` dataclass. These components transform supported LP models into equality form and record deterministic basic/nonbasic column metadata before a future revised simplex iteration loop is implemented.

## Revised Simplex Feasible-Basis Path

SILO now includes an initial primal revised simplex implementation for small LPs that already have a feasible slack basis. This path is intentionally narrower than the tableau solver: it currently supports only continuous maximization LPs with nonnegative variables and `<=` rows that produce no artificial variables. Phase I support for the revised simplex layer is planned later.
