# Backend Compare Command

The `silo compare` command runs the same JSON LP model through both native SILO LP backends:

```bash
silo compare examples/json/production.json
```

For the current example-by-example compare behavior matrix, see [Phase 4 Regression Checklist](phase4_regression_checklist.md).

It prints deterministic comparison JSON to stdout. To write the comparison to a file:

```bash
silo compare examples/json/production.json --output outputs/production_compare.json
```

Generated files under `outputs/` are local artifacts and should not be committed.

## Purpose

The command is intended for development, regression checks, and debugging. It compares the educational dense tableau simplex backend against the basis-oriented revised simplex backend without calling any external solver.

## Consistency

The top-level `consistent` field is `true` when:

- solver statuses match;
- if both solvers are optimal, objective values match within the default numerical tolerance;
- both solvers leave `dual_values` empty.

Primal values, slack values, reduced costs, and basis statuses are reported in `checks`, but primal equality is not required for consistency. Degenerate LPs may have multiple optimal primal solutions, so two correct backends can return different optimal variable values while agreeing on status and objective value.

## Checks

The `checks` object includes:

- `status_match`: whether solver statuses match.
- `objective_match`: whether objective values match within tolerance, or both are absent.
- `primal_max_abs_diff`: maximum absolute difference across reported primal values.
- `slack_max_abs_diff`: maximum absolute difference across reported slack values.
- `reduced_cost_max_abs_diff`: maximum absolute difference across reported reduced costs.
- `basis_status_match`: whether original-variable basis statuses match exactly.
- `dual_values_empty`: whether both backends still report empty dual values.

The `tableau` and `revised` payloads use the same solution schema as `silo solve`.

## Exit Codes

- `0`: comparison completed and `consistent` is `true`.
- `1`: comparison completed but `consistent` is `false`, or the model could not be read.
- `2`: command-line usage error handled by `argparse`.
