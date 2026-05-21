# Presolve Diagnostics CLI

## Purpose

The `silo presolve` command runs the conservative presolve layer and prints diagnostics without solving the model. It is intended for inspecting presolve reductions, infeasibility or unboundedness diagnostics, and coefficient-range scaling warnings.

## Basic Usage

```bash
silo presolve examples/json/production.json
```

The diagnostics JSON is printed to stdout.

The same command can be run through the Python module entry point:

```bash
python -m silo.cli.main presolve examples/json/production.json
```

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

The command does not solve the model. It does not change `silo solve` behavior, does not automatically scale the model, and does not connect presolve to tableau or revised simplex.
