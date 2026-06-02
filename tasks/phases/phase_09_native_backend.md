# Phase 9: Native Backend

Phase 9A records the native backend boundary design in `notes/21_native_backend_boundary_design.md`; it is planning-only and includes no implementation.

## Goal

Prepare selected solver kernels for a future native backend while preserving Python reference behavior as the source of truth.

## Scope

This phase covers native-backend planning, interface conformance, optional acceleration targets, and parity tests against the Python implementation.

## Expected Files

- `native/README.md`
- `src/silo/interfaces/`
- `tests/unit/test_backend_conformance.py`

## Algorithmic Requirements

Native code must follow already-tested Python conventions. Backend selection should be explicit, optional, and reversible. Native algorithms must not call external solvers.

## Testing Requirements

Add Python/native parity tests for any implemented native kernel. Tests should verify status, objective value, primal values, and failure-mode messages on small deterministic fixtures.

## Do Not Do

Do not begin native implementation before the Python model, LP, and MIP layers are stable. Do not make native dependencies required for normal package installation.

## Acceptance Criteria

Native backend work remains optional, tested against Python reference behavior, and isolated from the default educational solver path.
