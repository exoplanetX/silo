# JSON Model Format

SILO can read small optimization models from JSON. The model format is broader than the current tableau LP solver: the model layer can represent integer and binary variables, but the current native tableau solver solves only continuous maximization LPs with nonnegative variables and no finite upper bounds.

## Top-Level Fields

```json
{
  "name": "production",
  "sense": "maximize",
  "variables": [],
  "objective": {},
  "constraints": []
}
```

- `name`: optional model name.
- `sense`: currently use `"maximize"` for tableau solves.
- `variables`: list of variable declarations.
- `objective`: objective coefficients and optional constant.
- `constraints`: list of linear rows.

## Variables

```json
{
  "name": "x1",
  "lower": 0.0,
  "upper": null,
  "type": "continuous"
}
```

Current tableau solve support:

- `type`: `"continuous"`
- `lower`: `0.0`
- `upper`: `null`

The model layer also recognizes integer and binary variable types. LP CLI commands still use LP backends, while MIP examples are currently solved through the Python `BranchAndBoundSolver` API.

Binary variables use bounds within `[0, 1]`:

```json
{"name": "x", "lower": 0.0, "upper": 1.0, "type": "binary"}
```

Bounded nonnegative integer variables use finite integer-valued upper bounds:

```json
{"name": "x", "lower": 0.0, "upper": 3.0, "type": "integer"}
```

Fixed variables can be represented with equal lower and upper bounds:

```json
{"name": "x", "lower": 2.0, "upper": 2.0, "type": "continuous"}
```

Native simplex solvers still reject finite bounds directly. Use `silo solve MODEL_PATH --presolve` when a checked-in example relies on fixed-variable presolve recovery.

## Objective

```json
"objective": {
  "coefficients": {"x1": 3.0, "x2": 5.0},
  "constant": 0.0
}
```

The current tableau solver supports maximization models. The objective constant is optional and defaults to `0.0`.

## Constraints

Supported row senses for the tableau LP solver are:

- `<=`
- `>=`
- `=`

Example row:

```json
{
  "name": "labor",
  "coefficients": {"x1": 1.0, "x2": 2.0},
  "sense": "<=",
  "rhs": 8.0
}
```

Rows may have negative right-hand sides; the tableau solver normalizes them internally.

## Complete Example

```json
{
  "name": "production",
  "sense": "maximize",
  "variables": [
    {"name": "x1", "lower": 0.0, "upper": null, "type": "continuous"},
    {"name": "x2", "lower": 0.0, "upper": null, "type": "continuous"}
  ],
  "objective": {
    "coefficients": {"x1": 3.0, "x2": 5.0}
  },
  "constraints": [
    {"name": "labor", "coefficients": {"x1": 1.0, "x2": 2.0}, "sense": "<=", "rhs": 8.0},
    {"name": "material", "coefficients": {"x1": 3.0, "x2": 2.0}, "sense": "<=", "rhs": 12.0}
  ]
}
```

Run it with:

```bash
silo solve examples/json/production.json
```

## Solver Support Warning

The JSON model format may represent more than the LP CLI can solve. For example, binary and integer variables can be represented in JSON, but `silo solve` currently reports an unsupported-model error for them because it uses LP backends. Use the Python `BranchAndBoundSolver` API for the MIP examples under `examples/mip/`.
