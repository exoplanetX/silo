# Uncertainty Boundary Design

## 1. Purpose and Conservative Phase 8 Scope

Phase 8 introduces stochastic and robust optimization support as modeling
transformations. The primary design rule is that uncertainty constructs should produce
ordinary SILO `Model` objects that can be inspected, canonicalized, and solved by existing
LP or MIP layers. Phase 8 should not introduce a separate stochastic solver or make
existing solvers aware of uncertainty modules.

The first successful Phase 8 outcome should be a small, deterministic boundary for:

- finite scenarios;
- stochastic model wrappers;
- simple robust model wrappers;
- uncertainty-set records;
- deterministic-equivalent builders;
- transformation diagnostics for small educational examples.

Early Phase 8 work should be conservative. It should prioritize validation, naming
conventions, deterministic dimensions, and transformation transparency over broad
mathematical coverage.

## 2. Dependency Direction and Package Boundary

The project dependency direction remains:

```text
core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty
```

The uncertainty layer may depend on stable core model objects, expressions, variables,
constraints, objectives, statuses, and canonicalization behavior. It must not require
`core`, `modeling`, `presolve`, `lp`, `mip`, `cuts`, or `decomposition` to import
uncertainty modules.

The package boundary should eventually live under:

```text
src/silo/uncertainty/
```

but this design note does not create implementation files. Future implementation tasks
should keep public APIs small and should avoid public CLI or JSON schema changes until a
separate task explicitly approves those contracts.

Native uncertainty transformations must not call external solvers. If external solvers
are used later, they should appear only in interfaces, examples, or comparison tests.

## 3. Finite-Scenario Data Model

Finite scenarios should be explicit records rather than implicit dictionaries passed
through solver internals. A future scenario record should include:

- a deterministic scenario id;
- an optional display name or message;
- a probability weight;
- scenario-specific parameter overrides or coefficient data;
- metadata that remains scalar and deterministic.

Scenario ids should be nonempty strings. Scenario ordering should be deterministic, either
by user-supplied sequence order or by a documented sorted order when a mapping is used.

Probability validation should be explicit. The first implementation should require
finite nonnegative probabilities and a positive total probability mass. The default policy
should be strict validation that probabilities sum to one within a documented tolerance.
An optional normalization helper can be considered later, but the deterministic-equivalent
builder should not silently rescale probabilities unless a task explicitly requests that
behavior and tests it.

Scenario-specific data should begin as simple structured overrides. Suitable early forms
include:

- objective coefficient overrides keyed by base variable name;
- RHS overrides keyed by base constraint name;
- constraint coefficient overrides keyed by base constraint and variable name;
- scalar parameter values used by a future builder.

The first implementation should avoid arbitrary callbacks or executable functions inside
scenario records. Scenario data should be serializable in principle, even if public JSON
schemas are not changed in early Phase 8.

## 4. Stochastic Model Wrapper Boundary

A stochastic model wrapper should represent the relation between a deterministic base
model and finite scenario data. It should not solve the model. It should hold:

- a base `Model`;
- a finite scenario collection;
- a declaration of first-stage variables;
- a declaration of scenario-dependent variables or constraints when needed;
- metadata describing the transformation convention.

First-stage variables are shared before uncertainty is realized. Scenario-dependent
variables are replicated per scenario. In the early boundary, first-stage declarations
should use existing variable names and should validate that those names appear in the base
model. Scenario-dependent declarations should be explicit rather than inferred from all
variables by default.

Nonanticipativity should be represented as ordinary equality constraints in the
deterministic equivalent when variables are replicated. A simple convention is:

```text
na::{base_variable}::{scenario_id}
```

for constraints tying a scenario copy to a reference or shared first-stage variable.
Alternative compact representations can be considered later, but early implementation
should favor readability and inspectability.

Variable and constraint naming should be deterministic. A recommended convention is:

```text
scenario variable: {base_name}__s::{scenario_id}
scenario constraint: {base_name}__s::{scenario_id}
nonanticipativity constraint: na::{base_name}::{scenario_id}
```

The exact delimiter should be documented in the implementation task and tested. The
builder should reject base names or scenario ids that would make generated names
ambiguous if the chosen delimiter is already present.

Metadata that crosses into deterministic equivalents should be limited to scalar values
such as source labels, scenario counts, probability tolerance, and naming convention
labels. Mutable references to scenario internals should not be passed into lower layers.

## 5. Deterministic Equivalent Boundary

The deterministic-equivalent builder should construct a new ordinary SILO `Model`. It
should not mutate the caller's base model or scenario records.

For finite scenarios, the builder should:

- replicate scenario-dependent variables with deterministic names;
- replicate scenario-dependent constraints with deterministic names;
- aggregate objective terms using scenario probabilities;
- add nonanticipativity constraints when first-stage variables are replicated;
- preserve variable bounds and types where the transformation supports them;
- produce a small diagnostic record describing generated dimensions.

Objective aggregation should be documented before implementation. For expected-value
finite-scenario models, the default convention should be:

```text
objective = first_stage_terms + sum_s probability_s * scenario_objective_terms_s
```

If a variable or term is not scenario-dependent, the builder should avoid duplicating its
objective coefficient unless the stochastic wrapper explicitly asks for replication.

Scenario constraint replication should keep each scenario's constraints separate and
traceable. Generated constraints should carry names that identify the base constraint and
scenario id. Constraint senses should remain SILO's existing senses. RHS and coefficient
overrides should be applied only through documented scenario data.

The builder should return both the transformed `Model` and deterministic diagnostics.
Useful diagnostics include:

- number of scenarios;
- number of generated variables;
- number of generated constraints;
- number of nonanticipativity constraints;
- objective aggregation convention;
- probability total and tolerance;
- sorted scenario ids;
- generated-name convention.

Diagnostics should be separate from public `Solution` schemas.

## 6. Robust Model and Uncertainty-Set Boundary

Robust optimization support should begin with simple uncertainty-set records and very
small robust counterpart transformations. The first boundary should not claim broad robust
optimization coverage.

Supported early uncertainty-set shapes can include:

- box uncertainty for independent coefficient or RHS perturbations;
- interval uncertainty with lower and upper bounds;
- budgeted uncertainty placeholders if the mathematical counterpart is specified in a
  later design or implementation task.

Each uncertainty set should state:

- affected parameter or coefficient names;
- finite lower and upper bounds or radius values;
- whether the set applies to objective, RHS, or constraint coefficients;
- assumptions required for the robust counterpart.

Simple robust counterparts should be implemented only when the constraint structure and
uncertainty set make the transformation transparent. For example, an interval RHS
uncertainty transformation may be acceptable when it conservatively tightens or relaxes a
constraint according to a documented worst-case convention. Coefficient uncertainty should
wait for a specific mathematical specification before implementation.

Out of scope for early Phase 8 robust work:

- distributionally robust optimization;
- chance constraints;
- conic robust counterparts;
- automatic dualization of uncertain constraints;
- robust counterpart generation for arbitrary nonlinear uncertainty;
- claims of production-grade robust solver behavior.

## 7. Interaction with Existing Solver Layers

Uncertainty transformations may produce ordinary `Model` objects. Existing LP, MIP,
presolve, cut/callback, and decomposition layers should not know whether a model came
from an uncertainty transformation.

Phase 8 must not change:

- core model conventions;
- LP solver defaults;
- MIP branch-and-bound behavior;
- presolve behavior;
- cut or callback behavior;
- decomposition behavior;
- public CLI behavior;
- JSON model or solution schemas.

If a future task exposes uncertainty through CLI or JSON, that task should be a separate
review-gated contract with regression tests and explicit schema documentation.

## 8. Testing Strategy

Phase 8 tests should be deterministic and tiny. The first implementation tests should
focus on records and transformations, not solver performance.

Scenario validation tests should cover:

- nonempty scenario ids;
- duplicate scenario ids;
- finite nonnegative probabilities;
- zero total probability mass rejection;
- probability sum tolerance;
- deterministic scenario ordering.

Stochastic wrapper tests should cover:

- base model validation;
- first-stage variable declarations;
- scenario-dependent variable declarations;
- rejection of unknown variable or constraint names;
- no mutation of the base model.

Deterministic-equivalent tests should cover:

- generated variable counts;
- generated constraint counts;
- objective aggregation coefficients;
- scenario constraint naming;
- nonanticipativity constraint naming and counts;
- deterministic diagnostics;
- canonical form inspection for tiny fixtures.

Robust counterpart smoke tests should cover:

- uncertainty-set validation;
- simple interval or box uncertainty records;
- documented conservative counterpart dimensions;
- rejection of unsupported uncertainty shapes.

Dependency tests should verify that lower layers do not import uncertainty modules.

## 9. Non-Goals

Phase 8 planning and early implementation should not include:

- a separate stochastic solver;
- chance constraints;
- distributionally robust optimization;
- sampling or sample-average approximation engines;
- external solver calls inside native code;
- large datasets or benchmark suites;
- performance claims;
- public CLI changes;
- JSON schema changes;
- automatic reformulation discovery;
- advanced robust dualization;
- stochastic or robust branch-and-bound integration;
- Phase 9 native implementation work.

## 10. Candidate Atomic Task Sequence

The following tasks are candidates for future Phase 8 work. They are not issued by this
design note.

1. Add immutable finite-scenario records with validation tests for ids, probabilities,
   metadata, and deterministic ordering.
2. Add uncertainty package exports and lower-layer dependency smoke tests without adding
   transformations.
3. Add stochastic model wrapper records for base model, scenario collection, first-stage
   declarations, and scenario-dependent declarations.
4. Add deterministic naming-convention helpers and tests for scenario variables,
   scenario constraints, and nonanticipativity constraints.
5. Add a deterministic-equivalent result/diagnostic record without building models.
6. Add a tiny deterministic-equivalent builder for objective and RHS overrides on
   continuous LP fixtures.
7. Add nonanticipativity constraint generation for replicated first-stage variables.
8. Add checked-in stochastic transformation examples after the deterministic-equivalent
   builder is stable.
9. Add simple uncertainty-set records for interval and box uncertainty.
10. Add one conservative robust counterpart toy transformation for a documented fixture.
11. Add checked-in robust transformation examples after the robust toy transformation is
    stable.
12. Add a Phase 8 completion audit after the planned conservative uncertainty boundary
    tasks are complete.
