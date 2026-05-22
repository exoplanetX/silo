# MIP Diagnostics Output Design

## 1. Purpose and Motivation

The current `silo mip-solve` command intentionally reuses the compact solution JSON
contract used by the LP CLI path. That keeps the first MIP command small and stable, but
branch-and-bound has useful diagnostic information that is not visible in the default
output: node counts, incumbent progress, relaxation bounds, termination reasons, and
optional node-level decisions.

This note defines a conservative diagnostics direction before any CLI or JSON behavior is
changed. The goal is to make future diagnostics useful for small deterministic examples
without turning the default solution output into a branch-and-bound trace. The design
keeps the existing public solution JSON stable by default and treats diagnostics as an
opt-in MIP-specific output mode.

## 2. Current MIP CLI Output Contract

`silo mip-solve MODEL_PATH` currently writes the same solution JSON shape used by
`silo solve`:

```json
{
  "status": "optimal",
  "objective_value": 22.0,
  "primal_values": {
    "item_1": 0.0,
    "item_2": 1.0,
    "item_3": 1.0
  },
  "slack_values": {},
  "dual_values": {},
  "reduced_costs": {},
  "basis_status": {},
  "message": "Branch-and-bound solved the MIP."
}
```

For MIP solves, `status`, `objective_value`, `primal_values`, and `message` are the
meaningful public fields. The LP-specific fields may remain empty because final MIP dual
values, reduced costs, and basis status are not defined in the same way as an LP basis
solution. An infeasible MIP returns solution JSON with status `infeasible` and exit code
`1`. A node-limit stop returns status `iteration_limit` and exit code `1`.

The compact solution object is now covered by CLI regression tests for both
`python -m silo.cli.main mip-solve` and the installed `silo mip-solve` console script.
Future diagnostics should not change this default object.

## 3. Diagnostic Information Available or Expected from Branch-and-Bound

The current Python branch-and-bound result already carries several diagnostic fields:

- `nodes_processed`: number of nodes popped from the search tree and evaluated.
- `nodes_created`: number of nodes created, including the root node.
- `nodes_pruned`: number of processed nodes pruned by infeasibility, bound dominance,
  integer feasibility, unboundedness, or error handling.
- `incumbent_value`: objective value of the best integer-feasible incumbent, or `null`.
- `best_bound`: best LP relaxation bound observed by the current implementation, or
  `null`.
- `status_message`: final branch-and-bound message.
- `log`: deterministic node-level entries with node id, depth, LP status, LP objective,
  prune reason, branching variable, incumbent value, and message.

The CLI also knows the requested `node_limit` and the selected LP relaxation backend. A
future output wrapper can therefore report `node_count`, `nodes_processed`,
`incumbent_value`, `best_bound`, `relative_gap`, `termination_reason`, and `node_limit`
without changing the solver algorithm.

## 4. Recommended Minimal Diagnostic Fields

The minimal public diagnostics contract should be a summary, not a full node trace:

```text
node_count
nodes_processed
nodes_created
nodes_pruned
incumbent_value
best_bound
relative_gap
termination_reason
node_limit
lp_solver
```

`node_count` should be a user-facing alias for `nodes_processed` in the first public
diagnostics output. Keeping both names is acceptable because `node_count` is concise for
users while `nodes_processed` matches the Python result object and makes the exact meaning
clear.

`incumbent_value` should be the best integer-feasible objective value if one exists. It
should be `null` for infeasible cases with no incumbent and for errors before any
incumbent is found.

`best_bound` should be the best available global upper-bound proxy for maximization. For
proven optimal solves, it may equal the incumbent objective in the final output. If the
implementation cannot compute a meaningful global bound for a status, it should return
`null` rather than a misleading number.

`relative_gap` should be `null` when either `incumbent_value` or `best_bound` is missing.
When both exist, use:

```text
abs(best_bound - incumbent_value) / max(1.0, abs(incumbent_value))
```

For proven optimal solves this should be `0.0`. For node-limit stops with an incumbent
and an available bound, it reports the remaining relative optimality gap.

`termination_reason` should be a stable string derived from the final MIP status and the
branch-and-bound stopping condition. Recommended first values are:

```text
optimality_proven
infeasible
unbounded
node_limit
error
numerical_issue
```

These are diagnostics strings, not new solver statuses. The public `status` field remains
the existing solution status.

## 5. Always Included or Opt-In

Diagnostics should be opt-in. The default `silo mip-solve` output should remain the
compact solution JSON exactly because users and regression tests already rely on that
contract. Adding fields to the default object would widen the public solution schema and
would make LP and MIP solution JSON diverge quietly.

The first diagnostics implementation should therefore add a separate CLI mode such as:

```bash
silo mip-solve examples/mip/binary_knapsack.json --details
```

With `--details`, the command should emit a wrapper object containing the existing
solution object plus a MIP-specific diagnostics object. Without `--details`, the command
should continue to emit only the solution object.

Detailed node logs should not be included by default, even under summary diagnostics.
Node logs can become large and expose implementation-level traversal details. They should
require an additional explicit flag in a later task, such as `--node-log`, or a more
structured detail level such as `--details nodes`. The first implementation should avoid
making node logs part of the minimal public contract.

## 6. Proposed JSON Structure

For `--details`, the recommended first wrapper is:

```json
{
  "solution": {
    "status": "optimal",
    "objective_value": 22.0,
    "primal_values": {
      "item_1": 0.0,
      "item_2": 1.0,
      "item_3": 1.0
    },
    "slack_values": {},
    "dual_values": {},
    "reduced_costs": {},
    "basis_status": {},
    "message": "Branch-and-bound solved the MIP."
  },
  "diagnostics": {
    "node_count": 5,
    "nodes_processed": 5,
    "nodes_created": 5,
    "nodes_pruned": 3,
    "incumbent_value": 22.0,
    "best_bound": 22.0,
    "relative_gap": 0.0,
    "termination_reason": "optimality_proven",
    "node_limit": 10000,
    "lp_solver": "tableau"
  }
}
```

If a future task adds node-log output, it should extend the diagnostics object only when
explicitly requested:

```json
{
  "diagnostics": {
    "node_count": 5,
    "nodes_processed": 5,
    "nodes_created": 5,
    "nodes_pruned": 3,
    "incumbent_value": 22.0,
    "best_bound": 22.0,
    "relative_gap": 0.0,
    "termination_reason": "optimality_proven",
    "node_limit": 10000,
    "lp_solver": "tableau",
    "node_log": [
      {
        "node_id": 0,
        "depth": 0,
        "lp_status": "optimal",
        "lp_objective": 23.5,
        "prune_reason": "not_pruned",
        "branching_variable": "item_1",
        "incumbent_value": null,
        "message": "Branched on first fractional integer-restricted variable."
      }
    ]
  }
}
```

The exact numbers above are illustrative. Implementation tests should assert structural
keys, deterministic statuses, and selected small-example values rather than copying this
illustrative node trace.

## 7. Backward Compatibility Considerations

Backward compatibility requires the default `silo mip-solve` command to keep returning the
existing solution JSON object. Existing fields should not be renamed, removed, or given
MIP-specific meanings that conflict with LP solve output.

The diagnostics wrapper should be a different opt-in output contract. Under `--details`,
the top-level object is no longer the raw solution object; it is a wrapper with `solution`
and `diagnostics`. That distinction should be explicit in the CLI documentation and tests.

The existing `--output` flag should keep the same meaning: it writes whatever the selected
CLI output mode would otherwise print to stdout. Thus, with no diagnostics it writes a
solution JSON object; with `--details` it writes the diagnostics wrapper.

The LP `silo solve` and `silo compare` commands should not receive MIP diagnostics fields.
Diagnostics belong first to `silo mip-solve` because the values describe branch-and-bound
search, not LP simplex state.

## 8. CLI Flag Design

Recommended first flag:

```bash
silo mip-solve MODEL_PATH --details
```

This should include only the summary diagnostics object. It should not include `node_log`
unless a later task explicitly adds a second flag. Two compatible future choices are:

```bash
silo mip-solve MODEL_PATH --details --node-log
silo mip-solve MODEL_PATH --details nodes
```

The boolean `--details --node-log` design is easier to add to the current CLI. The
level-valued `--details nodes` design may scale better if SILO later adds separate summary,
node, relaxation, or incumbent-history detail levels. The first implementation should
choose one and document it before adding tests.

No `--mip-solver` flag is needed while branch-and-bound is the only native MIP algorithm.
No `--presolve` behavior should be added through this diagnostics task.

## 9. Testing Implications

A future implementation task should add tests without weakening the current regression
matrix:

- default `silo mip-solve` output still has the current solution JSON fields only;
- `python -m silo.cli.main mip-solve MODEL_PATH --details` returns top-level `solution`
  and `diagnostics` keys;
- `silo mip-solve MODEL_PATH --details` returns the same contract through the console
  script;
- `diagnostics.node_count` equals `diagnostics.nodes_processed`;
- optimal examples report `termination_reason` as `optimality_proven`;
- infeasible examples report `termination_reason` as `infeasible` and keep exit code `1`;
- node-limit examples report `termination_reason` as `node_limit`, carry the requested
  `node_limit`, and keep status `iteration_limit`;
- `relative_gap` is `0.0` for proven optimal examples and `null` when no incumbent or bound
  exists;
- `--output` writes the wrapper when `--details` is present.

If node-log output is added later, tests should use a small deterministic fixture and
assert only stable fields: node id, depth, LP status, prune reason, branching variable,
and incumbent value. Tests should not require performance-like node counts beyond small
checked-in examples.

## 10. Out-of-Scope Items

This design task does not implement any diagnostics output. It also does not change solver
source code, CLI behavior, tests, JSON model schema, or the default solution JSON schema.

The following items remain out of scope for the first diagnostics implementation:

- cuts, heuristics, callbacks, branch-and-cut, and conflict analysis;
- MIP presolve or automatic scaling;
- external solver calls or commercial-solver comparison;
- performance benchmarking or large instances;
- alternate MIP algorithms;
- streaming logs or progress bars;
- changing `silo solve` to auto-detect and dispatch MIP models;
- exposing LP relaxation tableaux, bases, or per-node primal/dual internals;
- making `node_log` part of default output.

## Follow-Up Implementation Tasks

The next atomic task should implement only `--details` summary diagnostics for
`silo mip-solve`, using the wrapper contract in this note and leaving the default solution
JSON unchanged.

A later task may add optional node-log output after the summary contract is stable. That
task should decide whether the public flag is `--node-log` or a level-valued `--details`
option and should update tests and documentation in the same commit.
