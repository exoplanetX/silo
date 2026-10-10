# Independent Correctness Baseline — Execution Report

## Objective / result

Completed the user-approved independent small-instance baseline without changing
solver source. Seventeen analytical LP inputs and 46 finite pure-integer inputs
(10 explicit plus 36 grid cases) produce 232 new checks across configurations,
external comparisons and four negative controls. All pass. This is evidence for
63 mathematical inputs, not 232 independent problems or a general correctness proof.

## Files changed

- `tests/verification/oracles.py`: raw specifications, exact rational enumeration,
  original-input primal/status/objective checks, analytical LP and integer fixtures.
- `tests/verification/test_correctness_oracles.py`: backend/presolve combinations,
  finite grid, optional independent HiGHS conversion, validator negative controls.
- `docs/correctness_baseline.md`: reproduce commands, coverage, conventions and limits.
- `docs/development_restart.md`, `.silo-dos/project_profile.md`,
  `.silo-dos/technical_route.md`: dated synchronization/authorization/evidence entries.
- Matching immutable task contract and this report.

No source, dependencies, public schemas, phase files or old task/report files changed.

## Checks / environment

- Initial targeted design: 216 passed in 0.74s; targeted Ruff passed.
- Initial full quality script: 1229 passed in 7.28s; Ruff passed.
- Added two decimal-coefficient/negative-RHS LP inputs after independent review.
- Final targeted `python -m pytest tests/verification -q`: 232 passed in 0.73s.
- Final `python scripts/check_quality.py`: **1245 passed in 7.20s**, Ruff all passed,
  exit 0. This is the original 1013 tests plus 232 new checks.
- `git diff --check`: no whitespace errors; Git emitted only CRLF normalization notices.
- Python 3.13.9, NumPy 2.3.5, pytest 8.4.2, SciPy 1.16.3; existing `.venv` and editable
  installation, with `.venv/Scripts` first on PATH. The environment inherits host
  packages; no clean-room reproducibility claim is made.

SciPy was installed and all 68 external-comparison configurations executed. Missing
SciPy is handled by per-test importorskip: 164 analytical/enumeration/negative-control
checks remain executable. Absence of SciPy was not separately simulated in this run.

## Independence / review

Enumeration uses Fraction over original bounded integer domains, without SILO's
relaxation, branching or feasibility routines. HiGHS rows are converted directly
from raw fixtures; no SILO standard-form matrix is reused. Optimal primal answers
are checked in original coordinates, including objective reconstruction. The
test acceptance threshold is absolute 1e-7; integer enumeration is exact.

Read-only `experiment_auditor` reviewed the concrete test design and returned
`decision_impact: strengthen`. It confirmed independence and finite coverage,
recommended decimal LP inputs and explicit limitations for mixed MIP/numerical
robustness, and independently reran the initial 216 targeted checks. It modified
no files. Main thread added the decimal inputs and documented all limitations.
Its review of the initial tests is not represented as a separate review of the
subsequently added fixtures or the final full suite.

## Git / synchronization

Before implementation:

- `git status --short`: empty; branch `main`, HEAD `a4814f4`.
- User-requested initial `git push origin main`: succeeded,
  `847bc59..a4814f4 main -> main` at https://github.com/exoplanetX/silo.
- Recovery commits pushed: `6bd9543`, `a2490ec`, `a4814f4`.
- `git rev-list --left-right --count origin/main...HEAD`: `0 0` after push.
- `remote_sync_status`: synchronized at the start of this new task.

This task's Git mode is local-commit. Commit reference: the commit containing this
report, subject `test: add independent small-instance correctness oracles`, parent
`a4814f4`. Resolve its exact hash using `git log -1 --format=%H --` followed by this
report path; a report cannot contain its own future commit hash. The final response
records the actual hash after commit. Expected post-commit state: clean main, ahead
one (`0 1`), `remote_sync_status: local_ahead_not_pushed`. The earlier push succeeded;
the new baseline commit's push is deliberately skipped under local-commit mode.

## Scope deviations / unresolved

No implementation scope expansion and no newly failing mathematical case found.
The evidence covers finite, well-scaled fixtures. General mixed MIP, numerical stress,
dual/KKT conditions, warm starts, performance and decomposition remain unverified by
this baseline. Existing mixed-MIP unbounded-status regression tests remain in the
full suite. Native remains deferred; Phase 9 open/parked; Phase 10 not started.

## Next recommended atomic task

Define original-space LP dual sign/objective conventions and recovery obligations
before implementing dual output and primal/dual optimality checks. `Solution` already
has `dual_values` but native LP results currently leave it empty. Separate design,
implementation and capability-expansion scopes as needed. Recommend GPT-6 Sol / high
for sign consistency through GE/EQ rows, Phase I and presolve recovery; routine fixture
maintenance can use Sol / medium. This report issues no new task or phase approval.
