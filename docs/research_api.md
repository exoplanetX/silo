# Public research interfaces

`silo.solve(model, options, extensions=ResearchExtensions(...))` exposes controlled
MILP strategy choices. Import extensions from `silo.mip.research`. Contexts are
immutable snapshots: mappings contain original variable names, bounds, costs and
points; open nodes expose IDs/depths/bounds; verified cut views contain read-only
original-space coefficients. Mutable tree nodes, factorization arrays and proof
internals stay executor-owned.

| Callback | Accepted action | Executor check |
|---|---|---|
| `branch_rule(context)` | One name in `context.fractional` | Genuine fractional candidate; ordinary floor/ceil children |
| `node_selector(context)` | One ID in `context.open_nodes` | Existing queued node |
| `separator(context)` | Unique indices into `context.cuts` | Only native, completely proved local GMI candidates |
| `heuristic(context)` | Complete primal mapping or `None` | Original row/bound feasibility and integrality, then actual integer rounding |
| `observer(context)` | No action | Immutable iteration snapshots |

Callbacks run in the caller's Python process. They must return promptly; the
executor checks the shared wall deadline before and after each callback and caps
their total calls (`call_limit`, default 10000). It cannot preempt a callback that
never returns. Exceptions, invalid actions, deadline or call-limit exhaustion
retain the active/open frontier and return `limit` with a separate reason and
`diagnostics.research_error`. A failed observer at an otherwise exhausted tree may
return a zero-gap limit. An existing primary solver failure retains its status
and reason; a later terminal observer exception is secondary information in
`diagnostics.research_error`. Research callbacks are currently MILP-only.

The separator extension selects or declines verified native cuts. Arbitrary
external cut expressions and user-supplied validity assertions are outside this
prototype interface. Native GMI generation still observes its own exact proof
budget. `diagnostics.research_trace` records actual callback/event/node invocations.

`silo.mip.research_example.run_example()` uses only public APIs, replaces node and
branch policies and returns a structured trace for the frozen four-binary example
(optimum -8.5). That example has an integral root; separate deterministic interface
tests exercise actual fractional branching and heuristic replacement.

`silo.decomposition.general_master` supplies a general nonnegative-column master,
public column addition and a finite-pool CG reference loop. Its rows retain their
declared intervals/equalities; no implicit convexity equation is added. Phase I
uses explicit nonnegative artificial violations for finite row sides. Full-pool
optimality requires complete finite pricing and zero auxiliary infeasibility;
heuristic pricing without an improving column returns an incomplete termination.
The installed `covering_example()` reproduces objective 2.5.

The old single-convex-combination RMP/DAG APIs retain their original domain.
These interfaces support reproducible algorithm comparisons. They establish no
new application result, incremental-pricing theorem or performance advantage.
