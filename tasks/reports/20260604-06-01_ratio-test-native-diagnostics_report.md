# Task Report: 20260604-06-01 Ratio-Test Native Diagnostics

## Objective

Add passive unavailable-native diagnostic records for the selected
`tableau_leaving_row_ratio_test` native-kernel candidate.

## Risk Level And Approval Confirmation

- Risk level: L1 controlled implementation.
- The user explicitly approved executing
  `tasks/codex/20260604-06-01_ratio-test-native-diagnostics.md`.
- Approval boundaries prohibited native implementation, solver calls, solver dispatch
  changes, CLI changes, JSON schema changes, native dependencies, build or packaging
  changes, roadmap changes, and phase changes.

## Task ID Scan Result

Existing `20260604-*` task/report prefixes before this task:

- `20260604-01-01_parity-result-records`
- `20260604-02-01_phase9-readiness-audit`
- `20260604-03-01_native-kernel-selection`
- `20260604-04-01_ratio-test-parity-fixtures`
- `20260604-05-01_phase9-implementation-readiness-audit`

Selected and executed task ID:

- `20260604-06-01_ratio-test-native-diagnostics`

No collision was found.

## Files Changed

- `src/silo/interfaces/tableau_ratio_native_diagnostics.py`
- `tests/unit/test_tableau_ratio_native_diagnostics.py`
- `tasks/codex/20260604-06-01_ratio-test-native-diagnostics.md`
- `tasks/reports/20260604-06-01_ratio-test-native-diagnostics_report.md`

## Implementation Summary

Added a passive `TableauRatioNativeDiagnostic` record with deterministic normalization
for:

- diagnostic id;
- candidate id;
- backend id;
- availability status;
- reason;
- tolerance label;
- message.

The module normalizes availability status through `BackendAvailabilityStatus`, requires
reasons for unavailable and unsupported statuses, trims and validates label fields, and
does not probe native runtime availability.

## Diagnostic Coverage Summary

The deterministic candidate-specific diagnostic tuple covers:

- `ratio-test-native-unavailable`, recording that the optional native runtime for
  `tableau_leaving_row_ratio_test` is not installed;
- `ratio-test-native-unsupported`, recording that native
  `tableau_leaving_row_ratio_test` implementation is not approved.

The diagnostics are passive records only. They do not call solvers, execute ratio tests,
run parity comparisons, import native modules, or change public `Solution` schemas.

## Checks Run

- `pytest tests/unit/test_tableau_ratio_native_diagnostics.py` - passed, 24 tests.
- `pytest tests/unit/test_tableau_ratio_parity.py` - passed, 29 tests.
- `pytest tests/unit/test_backend_boundary_smoke.py` - passed, 4 tests.
- `pytest tests/unit/test_backend_capability_records.py` - passed, 12 tests.
- `pytest tests/unit/test_python_backend_adapter.py` - passed, 6 tests.
- `pytest tests/unit/test_backend_conformance.py` - passed, 15 tests.
- `pytest tests/unit/test_unavailable_native_backend_diagnostics.py` - passed, 8 tests.
- `pytest tests/unit/test_backend_selector.py` - passed, 13 tests.
- `pytest tests/unit/test_backend_parity_records.py` - passed, 21 tests.
- `pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py`
  - passed, 48 tests.
- `python scripts/check_quality.py` - passed, 975 tests.
- `git diff --check` - passed.

## Deviations From Scope

None.

## Git Status

- Before execution:

```text
?? tasks/codex/20260604-06-01_ratio-test-native-diagnostics.md
```

- After implementation and before report:

```text
?? src/silo/interfaces/tableau_ratio_native_diagnostics.py
?? tasks/codex/20260604-06-01_ratio-test-native-diagnostics.md
?? tests/unit/test_tableau_ratio_native_diagnostics.py
```

- After report and before commit: expected new interface module, new test module, issued
  task file, and this report.
- Local commit: created after this report was written; final commit hash is reported in
  the Codex final response.
- Push mode: `push-on-success`; final push result is reported in the Codex final
  response.

## Unresolved Issues

Native implementation remains blocked. Remaining prerequisites include an optional native
build/dependency policy, a platform and generated-artifact exclusion policy, and a native
implementation strategy decision packet.

## Next Recommended Atomic Task

Create a design-only Phase 9 native build/dependency and generated-artifact policy note
for the selected ratio-test candidate.

Suggested risk level: L3 strategic if it chooses or constrains a future native
implementation line. Explicit user approval is required before issuing or executing it.

## Boundary Status

- No native kernel was implemented or approved.
- No solver behavior was changed.
- No solver dispatch was changed.
- No public CLI behavior was changed.
- No JSON schemas were changed.
- No roadmap, phase, or note files were changed.
- No native dependencies were added.
- No build or packaging files were changed.
- No second task was issued or executed.
