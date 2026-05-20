# CLI Solve Usage

The `silo solve` command connects the JSON model reader, the native tableau simplex solver, and deterministic solution JSON output.

## Basic Command

```bash
silo solve examples/json/production.json
```

The solution JSON is printed to stdout.

## Write Output To File

```bash
silo solve examples/json/production.json --output outputs/production_solution.json
```

The short option is also supported:

```bash
silo solve examples/json/production.json -o outputs/production_solution.json
```

Generated files under `outputs/` are local run artifacts and should not be committed.

## Python Module Invocation

```bash
python -m silo.cli.main solve examples/json/production.json
```

## Exit Codes

- `0`: the solve command completed and the solver returned `optimal`.
- `1`: the solve command ran but the model was invalid, unsupported, infeasible, unbounded, or otherwise non-optimal.
- `2`: command-line usage error handled by `argparse`.

## Solution JSON Fields

- `status`: solver status such as `optimal`, `infeasible`, `unbounded`, or `error`.
- `objective_value`: objective value for optimal solutions, otherwise `null`.
- `primal_values`: values of original decision variables.
- `slack_values`: public slack or residual values for original constraints.
- `dual_values`: currently empty for native LP solvers.
- `reduced_costs`: reduced costs for original decision variables under the public maximization convention `c_j - pi^T A_j`.
- `basis_status`: `"basic"` or `"nonbasic_lower"` for original decision variables.
- `message`: short solver message.

## Short Example Output

```json
{
  "basis_status": {
    "x1": "basic",
    "x2": "basic"
  },
  "dual_values": {},
  "message": "Tableau simplex solved the LP.",
  "objective_value": 21.0,
  "primal_values": {
    "x1": 2.0,
    "x2": 3.0
  },
  "reduced_costs": {
    "x1": 0.0,
    "x2": 0.0
  },
  "slack_values": {
    "labor": 0.0,
    "material": 0.0
  },
  "status": "optimal"
}
```

Small floating-point roundoff may appear in numeric output for some models.
