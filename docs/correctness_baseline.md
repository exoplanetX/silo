# Independent Small-Instance Correctness Baseline

Established by task `20261010-04-01_correctness-oracles` on 2026-10-10.

## Evidence design

`tests/verification/oracles.py` stores original-input fixtures and implements exact
finite integer enumeration using Python `Fraction`. Neither enumeration nor primal
validation calls SILO standard-form, presolve, relaxation, branching or feasibility
helpers. `make_model` only constructs the model being tested.

`tests/verification/test_correctness_oracles.py` exercises:

- 17 LP fixtures with hand-derived statuses/objectives: an intersection optimum,
  equality, negative RHS, Phase I, redundant rows, a degenerate optimum, objective
  constants, zero objective, rowless models, inconsistent rows, an impossible empty
  row, an improving coupled ray, feasible/infeasible improving empty columns,
  terminating decimal coefficients and a fractional negative RHS.
  Tableau and revised simplex each run with presolve enabled and disabled.
- 10 bounded pure-integer fixtures with hand answers checked against exhaustive
  enumeration; 36 additional cases from a deterministic Cartesian grid of row senses,
  RHS values and objectives. Both LP backends drive the native B&B implementation.
  The grid has two variables in `{0,1,2}`; the largest explicit domain has 16 points.
- Optional SciPy HiGHS comparisons for the same 17 LP inputs and four SILO execution
  configurations. The converter independently constructs rows from the fixture:
  negate GE rows, retain EQ rows, negate the maximization objective, restore its
  constant, and explicitly use nonnegative unbounded-above continuous variables.
  HiGHS presolve is disabled to request definitive infeasible/unbounded statuses.
  Unexpected oracle termination is a test failure, not an accepted answer.
- Negative controls showing that primal validation rejects a wrong objective, a
  violated original row, a missing coordinate, and a nonfinite coordinate.

For every optimal answer, validate complete finite original coordinates, lower/upper
bounds, integrality where applicable, original row residuals, the independently
expected objective, and objective reconstruction. Alternative optimal coordinates
are accepted. Absolute tolerance is `1e-7`, with zero relative tolerance on objective
comparisons; the exact enumerator uses no floating-point feasibility tolerance.

## Reproduce

From the repository root in the installed development environment:

```powershell
$env:PATH = (Join-Path $PWD '.venv\Scripts') + ';' + $env:PATH
& .\.venv\Scripts\python.exe -m pytest tests/verification -q
& .\.venv\Scripts\python.exe scripts/check_quality.py
```

SciPy is already declared under `optional-backends` in `pyproject.toml`. With SciPy
available the baseline has 232 passing checks. Without SciPy, only its 68
comparison cases skip; analytical and integer-enumeration checks still execute.
No runtime solver calls SciPy and no new dependency is introduced.

## Interpretation and next evidence gap

This is reproducible finite evidence for the current small, well-scaled supported
domain. The HiGHS runs repeat the analytical inputs; they provide a second method of
verification, not 68 additional mathematical instances. Backend/presolve combinations
also share the same underlying fixtures. Test count must not be treated as a count of
independent problems or a correctness proof.

The baseline covers maximization with zero lower bounds. LP finite upper bounds,
free variables and minimization remain outside the current solver scope. Enumeration
covers finite pure-integer problems; mixed continuous/integer unboundedness retains
its dedicated regression tests and bounded-integer proof assumptions. This suite does
not establish numerical robustness, general MIP correctness, dual/KKT correctness,
warm-start correctness, performance, or correctness of decomposition/cut algorithms.

Next recommended atomic task: add an independently checked LP optimality-evidence
baseline (dual feasibility and objective equality where evidence is available), or
first formalize the missing dual-result contract if that evidence is unavailable.
Capability expansion should be separately scoped and authorized.
