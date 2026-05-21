# Presolve Diagnostics CLI

## Purpose

The `silo presolve` command runs the conservative presolve layer and prints diagnostics without solving the model. It is intended for inspecting presolve reductions, infeasibility or unboundedness diagnostics, and coefficient-range scaling warnings.

For the current example-by-example presolve status matrix, see [Phase 4 Regression Checklist](phase4_regression_checklist.md).

## Basic Usage

```bash
silo presolve examples/json/production.json
```

The diagnostics JSON is printed to stdout.

The same command can be run through the Python module entry point:

```bash
python -m silo.cli.main presolve examples/json/production.json
```

## Presolve Examples

The presolve examples under `examples/json/` show reductions before solving:

```bash
silo presolve examples/json/fixed_var_recovery.json
silo presolve examples/json/repeated_empty_row.json
silo presolve examples/json/presolve_infeasible_after_fixed.json
```

Use `silo solve MODEL_PATH --presolve` on the same files to solve reduced models when presolve does not prove a terminal status.

## Output File

```bash
silo presolve examples/json/production.json --output outputs/production_presolve.json
```

The short option is also supported:

```bash
silo presolve examples/json/production.json -o outputs/production_presolve.json
```

Generated files under `outputs/` are local run artifacts and should not be committed.

## Exit Codes

- `0`: diagnostics were produced, including cases where presolve reports `infeasible` or `unbounded`.
- `1`: the model file could not be read, the model was invalid, or the diagnostics file could not be written.
- `2`: command-line usage error handled by `argparse`.

This differs from `silo solve`, where non-optimal solver statuses return exit code `1`.

## JSON Output Fields

Top-level fields:

- `model_path`: input model path.
- `presolve`: presolve status, change flag, message, row and variable diagnostics, warnings, and notes.
- `reductions`: deterministic reduction records with `type`, `target`, `description`, and `data`.
- `scaling`: coefficient-range diagnostics and scaling warnings.

## Current Scope

The command reads a JSON model, runs `Presolver().run(model)`, and serializes diagnostics. It does not serialize the full presolved model.

## Important Limitations

The command does not solve the model and does not automatically scale the model. It only reports diagnostics and reductions.

`silo solve MODEL_PATH --presolve` is the separate opt-in path that applies safe presolve before solving and then returns ordinary solution JSON.
