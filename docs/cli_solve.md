# CLI Solve Usage

The `silo solve` command connects the JSON model reader, the native tableau simplex solver, and deterministic solution JSON output.

For backend-to-backend diagnostics, use `silo compare MODEL_PATH`; see [Backend Compare Command](backend_compare.md).

For presolve and scaling diagnostics without solving the model, use `silo presolve MODEL_PATH`; see [Presolve Diagnostics CLI](presolve_cli.md).

## Basic Command

```bash
silo solve examples/json/production.json
```

The solution JSON is printed to stdout.

## Selecting a Solver Backend

The default backend is still the educational dense tableau simplex solver:

```bash
silo solve examples/json/production.json --solver tableau
```

The basis-oriented revised simplex solver can be selected explicitly:

```bash
silo solve examples/json/production.json --solver revised
```

Both backends are native SILO implementations. No external solver is called. The `tableau` backend remains the default for now, while `revised` is available for comparison and future basis-oriented workflows.

## Optional Presolve Before Solving

Presolve is opt-in for the solve command:

```bash
silo solve examples/json/production.json --presolve
silo solve examples/json/production.json --solver revised --presolve
```

When `--presolve` is used, SILO runs conservative presolve before the selected solver. If presolve proves infeasibility or unboundedness, `silo solve` returns the corresponding solution status without calling a simplex backend. Otherwise, the selected backend solves the presolved model and the solution is recovered in original model space, including slack values recomputed from the original constraints.

Default solve behavior does not run presolve. Presolve diagnostics are not included in solution JSON; use `silo presolve MODEL_PATH` to inspect diagnostics, reductions, and scaling warnings.

### Presolve Recovery Examples

```bash
silo solve examples/json/fixed_var_recovery.json --presolve
silo solve examples/json/repeated_empty_row.json --presolve
silo solve examples/json/presolve_infeasible_after_fixed.json --presolve
```

These examples show fixed-variable recovery, repeated-pass empty-row removal, original-space slack recovery, and presolve-detected infeasibility.

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
python -m silo.cli.main solve examples/json/production.json --solver revised
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
