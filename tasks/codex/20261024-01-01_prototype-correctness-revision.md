# 20261024-01-01：五模块原型正确性修订与候选重验

## Metadata

- Task ID: `20261024-01-01_prototype-correctness-revision`
- Type: one bounded corrective-maintenance task, R1–R3 internal checkpoints
- Risk: L2 algorithm/input behavior; narrowly listed L3 local candidate rebuild/version metadata
- Starting code: `4ca4bab47f2eecb8b60d5e34e767b4dc239fd969`
- Branch: `codex/teaching-research-prototype`; issuance commit is located from this file's Git history
- Owner: `silo-solver开发`; plan/review: `silo-solver-1010`
- Plan: [SILO-PROTOTYPE-REVISION-20261024 v0.1](../phases/prototype_revision_20261024.md)
- Evidence: [independent audit and four complete repros](../../docs/prototype_audit_20261024.md)
- Git mode: `local-commit`
- Report: `tasks/reports/20261024-01-01_prototype-correctness-revision_report.md`
- Model recommendation: GPT-6 Sol / high, for numerical/dual/frontier consistency; no model switch is claimed.

## 1. Objective, source and authorization

Fix the four confirmed post-delivery correctness findings F1–F4 within the existing five-module
general-form LP/MILP teaching/research prototype; strengthen only their meaningful regression,
learning and installation coverage. Deliver one corrected local candidate, then stop.

The current human instruction is: “对这次的五大模块进行一次审查和测试，然后根据审查情况制定修订和提升计划，推送执行修订。”
This specifically authorizes the audit-driven repairs and dispatch to the existing development chat.
It covers the enumerated input/algorithm/result corrections and necessary candidate refresh here.
Do not seek another approval for these listed internal repairs or R1→R2→R3 transitions.
This is one new bounded task; the old five-module contract is fulfilled and immutable, and its
special continuous-program exception is not extended. No new goal or duplicate ongoing goal is required.

The audit is complete at the starting code: full quality6147 PASS, new192 models×2 configurations384
PASS,48 exact IP enumerations,48 format roundtrips, artifact/source hashes matched. These successes
coexist with F1–F4 confirmed counterexamples. Read the actual repros before implementation.
Fixing these defects does not introduce new capabilities or complete original research C/D/E.

## 2. Startup and scope lock

Read root AGENTS/case notices, tasks/README, current mirror, this contract, plan, audit,
learning/README and WRITING_GUIDE. Record actual HEAD/branch/status and the source identities.
Current user instruction accepts continuation from the audit's local branch and known dirty state;
do not clean/reset or push to satisfy a generic sync template.

Preserve exactly, never stage:

- `AGENTS.md`: SHA256 `2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638`.
- Root `研究主题固定_严重反面案例通告_20261020.md`: SHA256 `0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221`.

Task ID scan on2026-10-24 found no existing20261024 task/report prefix before issuance; use01-01.
Do not revise this file after issuance. Keep the old plan, old reports, frozen fixtures/expected
answers, old ledger and old0.2.0a1 artifacts unchanged.

## 3. Required corrective work

### R1: MPS conversion integrity (F3/F4)

- Centralize semantic checks for direct/derived Decimal-to-model numbers; use mathematical integer
  value, not Decimal exponent alone, to protect exact integers. Equivalent `.0`/exponent spellings
  must not silently relax coefficients, RHS or integer bounds.
- Preserve integer value for the existing input_conversion gate or explicitly reject before loss;
  a rounded model followed by optimal is forbidden. General float64 decimal semantics stays documented.
- Reject nonzero derived underflow before zero; cover L/G/E and both signs of RANGES and overflow.
  Existing ordinary finite/subnormal decimals, large exactly representable floats, MPS writer/parser
  roundtrips and JSON behavior remain compatible. No arbitrary-precision solver dependency.

### R2a: MILP pruning and supported global bounds (F1)

- Remove primal-feasibility tolerance authority from objective-bound pruning in both locations.
  Define and document when bound pruning is allowed and how requested gap stopping differs.
- Keep active/open/unresolved and any approximation-discarded bound evidence conservative through
  normal completion, heuristic incumbent changes, gap/node/time/LP limits and callback errors.
  Do not just substitute objective_tolerance and continue manufacturing zero gap at queue exhaustion.
- The F1 min example must return0.01, max negative example-0.01; constant100 adds exactly100.
  Strict objective/dual settings must be respected across primal tolerances and objective scales.
  Preserve cuts, integrality, local inheritance and old research API behavior.

### R2b: Finite CG full-pool optimality (F2)

- Distinguish enumerated pool, tolerance-screened pricing and validated full-pool dual feasibility.
  With nonnegative columns lacking common finite upper bounds, a negative reduced-cost tolerance
  alone cannot support the restricted objective as a full-pool bound.
- Add genuine improving columns even when the old scaled threshold masked the improvement, or
  derive and verify sufficient full-pool optimality evidence. A reconstructed exact candidate is
  only a proposal until checked on raw binary model data and all pool columns.
- Keep finite-pool verification/reconstruction bounded by proof/time/pivot/20-iteration limits.
  Failure must retain the feasible incumbent and honest no-proof state; no false finite full-pool
  bound or optimal status. Arbitrary pricers remain heuristic; preserve Phase I exact Farkas logic.
- F2 bounded case must actually reach-10000, not be universally rejected as unsupported.
  The second, analytically unbounded case must prove unbounded or conservatively exit without a
  finite optimal claim. Do not bypass CG by silently solving all columns via an external solver
  or replacing the loop with a black-box full-pool solve.

### R3: Regression, learning and locally installed corrected candidate

- Freeze targeted repair cases/expected answers before implementation intended to pass them;
  add meaningful regressions under existing test domains. Promote a repeatable seed20261024
  independent audit driver to version control, preserving the audit model definitions and true oracles.
- Run the plan's finite validation matrix and accounting, preserve failures, use a new ledger/output
  directory `outputs/prototype_revision_20261024/`. Do not touch the old consumed diagnostic ledger.
- Update existing L0011/L0013/L0014 relevant sections (principles, counterexample, code mapping,
  research value/limits, exercises as appropriate); record actual checked code/commands.
  Do not create a lesson per patch or falsely refresh unchanged L0012 verification.
- Version local candidate0.2.0a2 consistently in pyproject/runtime/CITATION/docs. Build wheel/sdist
  into a new dist subdirectory. Validate WindowsPython3.11/3.13×wheel/sdist in four fresh isolated
  environments outside source with`-I`, NumPy runtime only; API, JSON/MPS CLI, both public research
  examples and targeted fixes must be exercised from the installed distribution.
- Verify artifact SHA, direct_url/source provenance, no accidental src import/SciPy runtime.
  Keep earlier candidate artifacts/reports intact. Remote CI remains pending unless separately run
  under an explicit human request; this contract does not trigger publication or remote work.

## 4. Allowed changes

- `src/silo/io/mps.py`, `src/silo/mip/general.py`, `src/silo/decomposition/general_master.py`.
- Necessary supporting bounded verification in existing `src/silo/lp/verification.py`,
  `src/silo/lp/tableau_view.py`, `src/silo/utils/rational.py`; only if directly needed for F1/F2,
  state the mathematical dependency in the report, no broad LP refactor.
- Relevant `tests/unit/`, `tests/verification/`, small repair manifest/fixtures;
  `scripts/prototype/` audit/revision/install drivers. Existing frozen prototype inputs unchanged.
- Relevant `docs/`, `learning/lessons/L0011-*`, `L0013-*`, `L0014-*`, CATALOG/GLOSSARY only if needed.
  L0012 may change only with directly affected content and actual reverification.
- `pyproject.toml`, `src/silo/__init__.py`, `CITATION.cff`, README/CHANGELOG for0.2.0a2 identity
  and corrected capability/installation references. No new runtime dependencies/build backend.
- This contract's matching report, new plan status/evidence, `.silo-dos/project_profile.md`,
  `technical_route.md` and `decision_log.md` for the bounded revision status, `tasks/INDEX.md`.
- Generated audit/results/install/build outputs stay ignored. Use a single writer per file;
  workers, if used, must be explicitly assigned disjoint ownership and preserve other work.

## 5. Forbidden changes and stop conditions

No new algorithms/capability line, performance project, native/C++, unrelated API/schema/CLI
redesign, original pricing C/D/E, scientific topic change, historical contract/report edits,
old acceptance output rewrites, tolerance relaxation to hide a failure, deleted meaningful
test, external solver inside native paths, Skill/Agent creation or governance-file staging.
Do not push GitHub, tag, Release or uploadPyPI/TestPyPI.

Follow the plan's fixed limits: targeted public calls≤128, new384-call matrix≤2 rounds,
old288-case matrix≤2 new-contract rounds, fullquality≤3 runs, four installs with≤1 environmental
retry per combination; all automated validation combined≤60minutes. Record seeds, calls,
elapsed, failed attempts and source SHA in a new append-only ledger. No reset/discard/hidden run.
Old64 diagnostic outputs may be rechecked, not re-solved against their exhausted ledger.
Read-only findings/proof review do not count as a second algorithm evidence stream.

At an actual out-of-scope requirement, unavailable required environment, exhausted cap or two
root-cause correction rounds without progress on the same major blocker, stop with a consolidated
report and outstanding obligations; do not lower standards, issue another task or continue forever.

## 6. Required checks and acceptance

1. New fixed F1–F4 regression/transform matrix passes with the values/statuses stated above.
2. Independent min/max/different primal tolerances and cost scales show valid bounds/gaps;
   capped runs retain conservative states. CG tests cover smallnegativeRC amplification,
   exact full-pool dual validity, Phase I and numeric/proof/iteration budget exits.
3. Historical MPS/LP/MIP/research regressions pass. Run the planned fixed independent matrix,
   optional directHiGHS comparison and48 integer enumerations; preserve old frozen input hashes.
4. Old frozen192+24+72 correctness/scale targets pass in the new revision run; two public research
   integrations remain correct. Old saved64 diagnostics independently recheck.
5. `scripts/check_project_structure.py --write-index`, structure and full`check_quality.py` pass;
   add`.venv/Scripts` to processPATH for CLI tests. Run fullquality only after actual relevant edits.
6. Four source-independent0.2.0a2 installations and targeted installed regressions pass with
   recorded artifact/source/command identities. No binary or generated results inGit.
7. Updated lessons reflect actual math and checked commit; one matching execution report provides
   before/after evidence, calls/time, diff scope, artifacts, residual risks and original research status.
8. Local commits contain only allowed files; exact two governance hashes unchanged; no push.

Success requires all eight. Report per-contract outcome separately from original research progress.
No mandatory item may be markedPASS solely because a test count increased. On success deliver
the bounded task, update current status, and stop for the discussion chat's final review.

## 7. Report / final response

Record preflight, actual source and candidate commits, task scan, per-finding before/after,
root-cause and numerical convention, targeted and full test results, new ledger/time,
learning paths/verified_code, installSHA/source proof, failed/retried checks and unresolved limits.
Include Remote Sync Proof fields: status, branch, last5 commits, cached ahead/behind,
push not attempted, remote_sync_status. Explicitly state cached versus live remote lookup.
The report's final commit is found with`git log -1 --format=%H -- <report>`; avoid self-reference.
Finish in Chinese with outcome, material fixes, evidence, local commit/installed candidate,
remaining original research obligations and the fact this task has stopped.
