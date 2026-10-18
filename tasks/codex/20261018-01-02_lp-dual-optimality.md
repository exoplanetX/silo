# LP Dual Values and Original-Space Optimality Verification

## Metadata / authority
- ID: 20261018-01-02_lp-dual-optimality
- Type/risk: L2 existing LP result enhancement, explicitly approved by user 2026-10-18
- Phase reference: existing Phase 2-4 simplex/results/presolve; no phase transition
- Mode: execute this one approved atomic task; Git mode: local-commit
- Report: tasks/reports/20261018-01-02_lp-dual-optimality_report.md

## Objective and context
Populate the existing Solution.dual_values from both native LP backends and verify
original-space primal/dual optimality, preserving the current supported model domain.
This continues baseline 5cc88cb, whose local-ahead state was reported before the user's
continuation approval. No push is authorized. The primary checkout contains five
untracked notes/26..30 research files: preserve them. Implement in the clean managed
lp-dual-evidence worktree based on 5cc88cb, then integrate only this task commit into
the primary checkout if tracked HEAD has not changed. Record before/after Git state.

## Design / conventions
For max c*x+c0, x>=0 and mixed rows: y_LE>=0, y_GE<=0, y_EQ free;
rc=c-A^T*y<=0; dual objective c0+b^T*y. Preserve normalization provenance through
negative RHS and Phase I redundant row cleanup. For existing presolve-fixed variables,
rc is unrestricted and contributes rc_j*fixed_value to the dual objective. Recover
removed feasible empty rows with zero duals and reconstruct original reduced costs.
Nonoptimal results do not acquire dual optimality claims. An independent read-only
theory service checks recovery obligations; main thread owns all writes and execution.

## Allowed files / scope lock
src/silo/lp/simplex/tableau.py and revised.py (provenance/extraction only); a new
src/silo/lp/optimality.py checker; src/silo/presolve/presolver.py result recovery;
src/silo/core/solution.py documentation only; src/silo/cli/compare.py consistency
logic to accommodate nonempty/nonunique duals without changing JSON keys; focused
tests/unit and tests/verification, and existing regression tests whose old assertions
require empty optimal LP duals; README.md, docs/lp_solver.md, docs/backend_compare.md, docs/correctness_baseline.md, new docs/lp_duality.md teaching/design note;
dated outcome entries in .silo-dos/project_profile.md and technical_route.md; this
new contract/report. Supporting edits must directly serve LP dual correctness.

## Forbidden changes
No new solver or pivot/search/termination algorithm, minimization/free-variable/general
bound solving, MIP dual claims, new CLI flags or JSON keys, dependency/build/native work,
external solver calls in native algorithms, phase promotion, old task/report edits,
research-note edits, skill changes or push. Do not require dual-coordinate equality
across degenerate optima. Do not silently generalize a finite numeric check into proof.

## Checks / acceptance
Red/green tests for unique known duals, mixed senses/negative RHS, equality redundancy,
degeneracy, constants, zero/empty models, presolve-empty-row and fixed-variable recovery,
both LP backends, warm-start result extraction, and optimal/nonoptimal CLI/compare.
Independent checker validates original primal feasibility, dual signs, stationarity,
objective equality and complementarity; rejects missing/nonfinite/wrong-sign/wrong-value
evidence and unsupported model domains. Exercise previous analytical LP oracle fixtures
and optional HiGHS dual marginals where unique, allowing nonunique duals otherwise.
Existing MIP output remains free of LP-relaxation duals. Full quality script, Ruff,
diff checks pass. Document formulas, a hand-worked example, floating tolerance and limits.

## Stop conditions / report
Unexpected tracked edits, proof failure, need for forbidden capability changes or source
outside allowed modules: preserve evidence and report a bounded follow-up. Report files,
checks, independent review, environment, learning material, Git/commit/integration/push
state, unresolved limits and next recommendation. Stop after this one task.

## Revision receipt
Revision 02 supersedes 01 for the same atomic objective. Correct the allowed compare
documentation filename to the actual docs/backend_compare.md; no implementation
objective expansion. Preserve 01 unchanged. Initial red/green evidence from revision
01 is carried into the final matching 02 report. Existing Phase-I source-row/basis-slot
cleanup robustness is documented as a follow-up, without changing that algorithm.
