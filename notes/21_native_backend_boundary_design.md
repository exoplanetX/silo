# Native Backend Boundary Design

## 1. Purpose and Conservative Phase 9 Scope

Phase 9 prepares SILO for a future optional native backend while preserving the Python
reference implementation as the source of truth. The goal is not to make SILO faster in
this phase. The goal is to define a boundary where selected kernels can later be compared
against Python behavior without changing default solver semantics.

The first successful Phase 9 outcome should be a small, deterministic boundary for:

- backend capability records;
- explicit backend selection policy;
- Python-reference conformance fixtures;
- parity diagnostics;
- failure-mode reporting when a backend is unavailable or unsupported;
- build/dependency rules that keep native code optional.

Early Phase 9 work should be conservative. It should prioritize reproducible behavior,
test isolation, and reversible backend selection over performance or broad native
coverage.

## 2. Dependency Direction and Package Boundary

The project dependency direction remains:

```text
core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty
```

Native backend planning must not invert this direction. Core model objects, canonical
forms, LP solvers, MIP solvers, presolve, cuts, decomposition, and uncertainty modules
must not import optional native implementation modules as a required dependency.

Future backend interface code should live under an explicit interface boundary, such as:

```text
src/silo/interfaces/
```

A future optional native implementation can live outside the default Python solver path,
for example under:

```text
native/
```

or another explicitly documented optional package boundary. This design note does not
create either implementation boundary.

Native algorithms must not call external solvers. External solvers may appear only in
comparison interfaces, examples, or tests that are explicitly scoped for comparison.

## 3. Python Reference Source-of-Truth Policy

Python behavior is the reference for Phase 9. A native backend may be accepted only when
it matches already-tested Python behavior on deterministic fixtures.

Reference behavior includes:

- model validation conventions;
- canonical form conventions;
- LP and MIP statuses;
- objective values;
- primal values;
- infeasible or unbounded diagnostics;
- tolerance policy where already documented;
- deterministic message and failure-mode expectations where tests assert them.

Native work must not silently change mathematical conventions. If a future native kernel
requires a different numerical tolerance, ordering policy, or status convention, that task
must document the difference and stop at a review gate before changing behavior.

## 4. Optional Backend Interface Boundary

Backend selection should be explicit, optional, and reversible. The default solver path
should remain the Python implementation.

A future backend interface can expose records such as:

- backend id;
- backend kind, such as `python_reference` or `native_experimental`;
- supported problem families;
- supported variable types;
- supported constraint senses;
- supported diagnostics;
- availability status;
- reason for unavailability or unsupported input.

Backend selection should not be global hidden state. A caller should request a backend
explicitly or use a documented default. If a requested backend is unavailable, the result
should report that fact clearly instead of silently switching to another backend unless a
task explicitly approves fallback behavior.

## 5. Candidate Native Kernel Selection Criteria

Candidate kernels should be selected only after the Python behavior is stable and covered
by deterministic tests. Good early candidates have these properties:

- small input/output boundary;
- deterministic behavior independent of thread scheduling;
- no direct dependency on external solvers;
- clear parity expectations;
- limited numerical tolerance surface;
- no public CLI or JSON schema contract required;
- failure modes that can be represented without changing public solution schemas.

Poor early candidates include broad branch-and-bound search control, presolve reductions,
cut separation, callback mutation, decomposition loops, and uncertainty transformations.
Those areas have policy-heavy behavior and should not be native-backed until the Python
reference is much more stable.

## 6. Parity and Conformance Testing Strategy

Parity tests should compare native results with Python reference results on small
deterministic fixtures. The first conformance records should not require a native backend
to be installed.

Future parity tests should cover:

- status;
- objective value;
- primal values;
- infeasible or unbounded status handling;
- unsupported-input diagnostics;
- backend availability diagnostics;
- tolerance metadata when relevant.

If native code is unavailable, conformance tests should still verify that the Python
reference backend remains available and that unavailable native backends report a stable
diagnostic. Native-specific tests can be skipped only through an explicit availability
marker or optional test group.

## 7. Failure-Mode and Diagnostics Expectations

Phase 9 diagnostics should be explicit and inspectable. Useful diagnostics include:

- backend id;
- selected backend kind;
- availability status;
- unsupported feature label;
- fallback policy, if any;
- parity fixture id;
- tolerance label;
- message.

Diagnostics should remain separate from public `Solution` schemas unless a later
review-gated task explicitly approves schema changes.

Future backend errors should distinguish:

- backend unavailable;
- backend installed but incompatible;
- unsupported model feature;
- parity mismatch;
- native execution failure;
- unsupported diagnostic request.

## 8. Dependency and Build Policy

Native dependencies must remain optional. Normal package installation should not require
a compiler, native build toolchain, or native runtime.

Future tasks that add native build files, optional dependencies, wheels, or extension
modules require explicit review. They should state:

- supported platforms;
- how native code is enabled;
- how native code is disabled;
- how tests behave when native code is unavailable;
- how generated build artifacts are excluded from git.

No Phase 9 task should add large binary files, generated build outputs, or platform-local
artifacts to git.

## 9. Public CLI and JSON Schema Non-Goals

Early Phase 9 should not expose native backend selection through public CLI commands or
JSON schemas. Public contract changes should be separate review-gated tasks with
regression tests.

Early Phase 9 should not add:

- new CLI options;
- new JSON model fields;
- new JSON solution fields;
- automatic backend selection from environment variables;
- hidden fallback behavior.

## 10. Non-Goals

Phase 9 planning and early implementation should not include:

- production-grade native optimization kernels;
- broad LP or MIP solver rewrites;
- branch-and-bound search-control changes;
- presolve behavior changes;
- cut/callback behavior changes;
- decomposition or uncertainty integration;
- public CLI changes;
- JSON schema changes;
- required native dependencies;
- external solver calls inside native algorithms;
- large benchmarks or performance claims;
- Phase 10 work.

## 11. Candidate Atomic Task Sequence

The following tasks are candidates for future Phase 9 work. They are not issued by this
design note.

1. Add backend boundary smoke tests proving default Python solver paths do not import
   optional native modules.
2. Add immutable backend capability and availability records with validation tests.
3. Add a Python-reference backend adapter record without changing solver behavior.
4. Add backend conformance fixture records for small LP fixtures without native code.
5. Add unavailable-native-backend diagnostics tests without adding native dependencies.
6. Add a no-op backend selector boundary that always selects Python reference by default.
7. Add parity result records for comparing Python reference results with future backends.
8. Add a Phase 9 implementation readiness audit before any native kernel is implemented.

## 12. Review Gates and Risk Levels

Suggested risk classification:

- L0: documentation, reports, audits, boundary smoke tests, and conformance fixtures that
  do not modify solver behavior.
- L1: passive dataclasses, capability records, availability records, and no-op selector
  boundaries that preserve default Python behavior.
- L2: backend selector behavior, public backend interface behavior, parity comparison
  execution paths, or any change that can alter solver dispatch.
- L3: adding native dependencies, starting native kernel implementation, public CLI or
  JSON schema exposure, phase closure, or starting any later phase.

No native implementation task should proceed without explicit user approval.
