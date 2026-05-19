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
