# MIP Solve CLI

## Purpose

The `silo mip-solve` command solves supported MIP JSON models with SILO's native branch-and-bound solver. It is separate from `silo solve`, which remains the continuous LP solve command.

Branch-and-bound solves LP relaxations internally. The LP relaxation backend can be selected with `--lp-solver`, but tableau and revised simplex are still LP backends, not MIP algorithms.

## Basic Usage

```bash
silo mip-solve examples/mip/binary_knapsack.json
```

The solution JSON is printed to stdout.

## LP Relaxation Backend

The default LP relaxation backend is `tableau`:

```bash
silo mip-solve examples/mip/binary_knapsack.json --lp-solver tableau
```

The revised simplex backend can also be selected:

```bash
silo mip-solve examples/mip/binary_knapsack.json --lp-solver revised
```

Use `--lp-solver` for MIP solves. The `--solver` flag belongs to the LP `silo solve` command.

## Node Limit

```bash
silo mip-solve examples/mip/binary_knapsack.json --node-limit 1000
```

The value must be a nonnegative integer. If the search reaches the node limit before proving optimality, the command returns solution status `iteration_limit` and exit code `1`.

## Summary Diagnostics

The default output remains the compact solution JSON. Use `--details` to emit a wrapper
with the compact solution plus branch-and-bound summary diagnostics:

```bash
silo mip-solve examples/mip/binary_knapsack.json --details
```

The wrapper has top-level `solution` and `diagnostics` objects. The `solution` object uses
the same fields as default output. The `diagnostics` object includes:

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

Detailed node logs are not emitted by `--details`.

Add `--node-log` to include one entry per processed branch-and-bound node:

```bash
silo mip-solve examples/mip/binary_knapsack.json --details --node-log
```

`--node-log` requires `--details`. Each entry includes node id, depth, LP relaxation
status and objective, prune reason, branching variable, incumbent value, and message. It
does not include LP tableaux, bases, full relaxation models, or primal/dual vectors.

## Output File

```bash
silo mip-solve examples/mip/binary_knapsack.json --output outputs/knapsack_solution.json
```

The short form is also supported:

```bash
silo mip-solve examples/mip/binary_knapsack.json -o outputs/knapsack_solution.json
```

When `--details` is present, `--output` writes the wrapper JSON instead of the compact
solution JSON.

When both `--details` and `--node-log` are present, `--output` writes the wrapper JSON with
`diagnostics.node_log`.

Generated files under `outputs/` are local run artifacts and should not be committed.

## Exit Codes

- `0`: the MIP solve command completed and returned `optimal`.
- `1`: the command ran but returned a non-optimal status, or a read/write error occurred.
- `2`: command-line usage error handled by `argparse`.

## Examples

```bash
silo mip-solve examples/mip/binary_knapsack.json
silo mip-solve examples/mip/binary_choice.json
silo mip-solve examples/mip/integer_allocation.json --lp-solver revised
silo mip-solve examples/mip/mixed_binary_integer.json
silo mip-solve examples/mip/mixed_continuous_integer.json
silo mip-solve examples/mip/infeasible_binary.json
```

The infeasible example emits solution JSON with status `infeasible` and exits with code `1`.

Regression coverage exercises both `python -m silo.cli.main mip-solve` and the installed
`silo mip-solve` console script on the checked-in MIP examples.

## Current Limitations

- Maximization only.
- Binary and bounded nonnegative integer variables.
- Optional compatible continuous variables with lower bound `0` and no finite upper bound.
- No cuts.
- No heuristics.
- No callbacks.
- No branch-and-cut.
- No MIP presolve.
- No LP tableau, basis, or full relaxation dumps in node-log JSON.
