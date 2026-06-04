# Native Build And Dependency Policy

## Purpose

This note records the Phase 9 native build, dependency, platform, and generated-artifact
policy for the selected first native-kernel candidate:

```text
tableau_leaving_row_ratio_test
```

The candidate corresponds to the Python reference behavior of
`silo.lp.simplex.ratio_test.choose_leaving_row`, but this note does not implement native
code, approve native implementation, change solver dispatch, add dependencies, modify
build or packaging files, expose CLI or JSON schema controls, close Phase 9, or start
Phase 10.

## Current Repository State

SILO remains a Python reference implementation. The current repository state has these
native-backend properties:

- no native implementation files beyond the reserved `native/README.md`;
- no required native runtime dependency;
- no native extension module;
- no compiler toolchain requirement for normal installation;
- no native build-system integration;
- no public CLI or JSON schema surface for native backend selection;
- passive Phase 9 records for backend capability, Python-reference backend records,
  conformance fixtures, selector behavior, parity results, ratio-test parity fixtures,
  and candidate-specific unavailable-native diagnostics.

The normal installation dependency set remains Python-oriented. In `pyproject.toml`,
runtime dependencies are limited to `numpy>=1.24`. The existing `optional-backends`
dependency group is for external comparison-oriented backend work and is not a native
kernel policy.

## Non-Goals

This policy note does not include:

- native ratio-test implementation;
- C, C++, Rust, Cython, pybind11, cffi, or other extension scaffolding;
- build-system or packaging edits;
- dependency additions;
- generated native artifacts;
- solver dispatch;
- fallback behavior;
- public CLI flags;
- JSON model or solution schema fields;
- performance benchmarks;
- Phase 9 closure;
- Phase 10 planning or implementation.

## Future Native Implementation Forms

Future review may compare three implementation forms.

### Python Extension Module

A Python extension module would expose the selected kernel through a Python-callable
native function. This has the smallest dispatch boundary for a small primitive such as
`tableau_leaving_row_ratio_test`, but it also introduces packaging, compiler, wheel, and
platform support questions. It should not be added until a separate L3 task approves the
build backend and optional dependency policy.

### Standalone Native Executable Or Library

A standalone executable or shared library behind an explicit optional interface keeps the
Python package independent of extension builds, but it is too heavy for the current
ratio-test candidate. It would introduce process, ABI, path, platform, and artifact
management concerns that are disproportionate for a single deterministic pivot helper.

### Deferred Native Implementation

Deferring implementation keeps Phase 9 focused on reference behavior, diagnostics,
fixtures, and review gates. It preserves normal installation and default solver behavior
while the project decides whether a native kernel is worth the packaging cost.

## Recommended Near-Term Policy

The recommended near-term Phase 9 policy is:

```text
defer native implementation
```

This is the most conservative choice. The project has a selected candidate, passive
fixtures, and unavailable-native diagnostics, but it has not yet approved a build backend,
platform support matrix, optional dependency mechanism, artifact exclusion rule set, or
native CI behavior. Deferring implementation avoids turning a small algorithmic
candidate into a packaging commitment before the package boundary is stable.

If the user later approves implementation after review, the preferred first technical
form should be a narrowly scoped optional Python extension module for only
`tableau_leaving_row_ratio_test`, not a standalone native executable or broad native
backend. That later choice still requires a separate L3 task and must not be inferred
from this note.

## Dependency Policy

Normal installation must not require:

- a compiler;
- a native build toolchain;
- a native runtime;
- platform-specific shared libraries;
- native package managers;
- optional external solvers.

Native dependencies must remain optional and separately approved. A future native task
must state the exact optional dependency mechanism before changing `pyproject.toml` or any
packaging file.

Native algorithms must not call external solvers. External solvers may remain only in
comparison interfaces, examples, or tests that are explicitly scoped for comparison.
Native code must implement only the approved kernel behavior and must match Python
reference fixtures.

## Build Policy

This task makes no build backend or packaging changes.

Any future build change requires a separate L3 task with explicit user approval. That task
must state:

- the selected native implementation form;
- the build backend or extension mechanism;
- how native code is enabled;
- how native code is disabled;
- how normal Python installation avoids native requirements;
- how tests behave when native runtime support is absent;
- how generated artifacts are excluded from git;
- how platform support is declared.

The default Python solver path must remain importable and testable without native build
products. Native build failure must not break ordinary Python reference use.

## Generated-Artifact Policy

Future native tasks must not commit generated or platform-local artifacts. Excluded
artifact classes include:

- compiled object files;
- shared libraries and dynamic libraries;
- static libraries;
- executable binaries;
- generated extension modules;
- wheels and built distributions;
- local build directories;
- CMake, Meson, maturin, setuptools, or compiler cache directories;
- generated headers or source files unless explicitly approved as source artifacts;
- benchmark dumps;
- profiling outputs;
- large logs;
- platform-specific temporary outputs;
- local toolchain metadata;
- downloaded third-party native source trees;
- vendored native dependencies.

If future native work needs repository ignore rules, that must be handled in a separate
task before build products are generated.

## Platform Policy

Future native work must state a platform policy before implementation. At minimum it must
define:

- supported operating systems;
- supported Python versions;
- CPU architecture assumptions;
- whether native acceleration is unavailable by default;
- how unavailable-native diagnostics are produced;
- whether fallback is prohibited or explicitly allowed;
- how tests behave when native runtime support is missing.

Until this policy is approved in an implementation task, tests must pass without native
runtime installed.

## Test And CI Policy

Default CI should keep Python reference tests required. Native-specific tests should be
optional, availability-gated, or skipped with explicit diagnostics until native runtime
support is approved and documented.

For the selected ratio-test candidate, any future native implementation must add parity
tests against the passive `tableau_leaving_row_ratio_test` fixtures. Those tests should
cover:

- unavailable-native diagnostics when native runtime support is absent;
- deterministic row-index results when native runtime support is present;
- tolerance-boundary behavior;
- tie-breaking by row order;
- no default solver dispatch to native code;
- no public CLI or JSON schema changes.

The first native implementation task should not require external solvers or large test
fixtures.

## Solver-Behavior Policy

The default solver path remains Python-only. Future native work must preserve:

- no default dispatch to native code;
- no hidden fallback;
- no automatic environment-variable selection;
- no public CLI exposure without separate review;
- no JSON schema exposure without separate review;
- no mutation of existing LP, MIP, presolve, cuts, decomposition, or uncertainty
  behavior;
- no change to `TableauSimplexSolver`, `RevisedSimplexSolver`, or MIP branch-and-bound
  behavior unless a separate higher-risk task explicitly approves it.

Native parity diagnostics must remain separate from public `Solution` schemas unless a
later review-gated schema task approves public exposure.

## Decision Packet

Task:

```text
Phase 9 native build/dependency and generated-artifact policy for
tableau_leaving_row_ratio_test
```

Risk level:

```text
L3 strategic
```

Recommendation:

```text
defer native implementation for now
```

Reason:

The selected candidate is small and deterministic, but implementation would still commit
the project to a native packaging path. The current repository has the right passive
boundary artifacts but no approved build backend, platform policy, artifact exclusion
policy, or native CI policy. Deferring implementation preserves Python reference
stability and keeps the next approval gate focused.

Preferred future path if implementation is later approved:

```text
optional Python extension module for only tableau_leaving_row_ratio_test
```

This is preferable to a standalone executable or broad native backend because the
candidate has a small in-process input/output boundary. It should still remain optional,
disabled by default, and unreachable from the default solver path.

Required approvals before implementation:

- approve the native implementation form;
- approve any build backend or packaging changes;
- approve optional native dependencies, if any;
- approve platform and CI behavior;
- approve generated-artifact exclusion rules;
- approve parity execution tests;
- approve the exact no-dispatch integration boundary;
- approve a separate first native implementation task.

This decision packet does not approve implementation.

## Candidate Atomic Tasks After This Policy

The following are candidate future tasks only. They are not issued by this note.

1. Create a Phase 9 implementation-readiness audit after the build/dependency policy
   note.
2. If the audit recommends review, create a decision packet for whether to approve,
   revise, or reject the first native implementation path.
3. If explicitly approved later, add the narrow optional native implementation scaffold
   for `tableau_leaving_row_ratio_test` without default solver dispatch.
4. In a separate later task, add native parity execution tests that are availability-gated
   and keep default Python behavior unchanged.

## Boundary Statement

This note does not implement native code, approve native implementation, add native
dependencies, change build or packaging files, change solver dispatch, expose CLI or JSON
schema controls, close Phase 9, start Phase 10, or issue any follow-on task.
