# 20261023-02-01：教学研究通用 LP/MILP 原型整体执行

## Metadata

- Task ID: `20261023-02-01_teaching-prototype`
- Type: user-authorized bounded program / solver implementation
- Risk: L3 overall, including the listed L2 algorithm and public behavior changes
- Plan: [SILO-PROTOTYPE-20261023 v0.1](../phases/phase_10_teaching_research_prototype.md)
- Starting code: `13e748f` (workbench integrated); actual issuance commit is found from this contract's Git history
- Execution: `silo-solver开发`; coordination and final review: `silo-solver-1010`
- Git mode: `local-commit`, branch `codex/teaching-research-prototype`
- Report: [matching total report](../reports/20261023-02-01_teaching-prototype_report.md)
- Model recommendation: GPT-6 Sol / high, because transformations, dual recovery, LP reoptimization, MIP bounds and GMI must agree. This recommendation is not evidence of a model switch.

## 1. Objective and direct authorization

On the existing SILO codebase, complete the five-module plan as one bounded program: a dense, small-scale, general-form LP/MILP teaching and research prototype with real native algorithms, extensible public interfaces, independently checked results and clean-install artifacts.

The user's current instruction explicitly requests a plan divided by large modules, followed by continuous goal-mode implementation with autonomous checking, validation and progress. This contract implements that request. This is one overall task with M1–M5 checkpoints, not five separately issued tasks. Individual bug fixes, tests, lessons and module transitions inside the frozen plan do not require new human approval.

The coordinator owns the single goal in its own conversation. The execution conversation executes this entire contract without creating a duplicate goal. It may use its normal continuation/recovery mechanisms and bounded implementation agents; the coordinator may send in-scope continuation or correction messages under the user's existing execution-delegation instruction.

## 2. Scope lock and exit line

Implement M1→M2→M3→M4→M5 exactly as defined in the linked plan, including its mathematical specifications, frozen manifest, local Windows Python 3.11/3.13 validation, benchmark thresholds and four-hour local verification budget.

Success requires every mandatory item in the plan's final acceptance table to PASS with actual evidence. A module's code, an interface skeleton, an increased test count or a workflow file is insufficient. M5 completes a locally validated prototype; unrun remote CI remains pending and must not become a claim of multi-platform qualification.

The original pricing research has an independent status: A/B accepted; C pre-issuance HOLD; D/E not started. This engineering program does not execute or complete those research obligations, change their topic, or erase earlier evidence.

## 3. Initialization before any solver code change

1. Read AGENTS.md, tasks/README.md, the plan and current mirror. Record actual branch/HEAD/status and known governance-file hashes.
2. Recognize this explicit user-authorized overall mode. Before source edits, add its narrow exception to tasks/README.md, current profile, technical route, standing approval and decision log. Retain ordinary single-task mode for other work. This initialization is inside this same contract.
3. Keep the original CASE governance content unchanged; do not edit or stage existing AGENTS.md changes or the untracked root CASE notice. Current known hashes are recorded in the report. Current user instruction plus this registered exception governs this program without rewriting runtime Skills or Agents.
4. Preserve native Phase 9 parked/deferred; do not manufacture native closure as a prerequisite. Add this plan's explicit program identity and progress to the current roadmap/mirror without reclassifying historical limited-scope completion.
5. Freeze the general-model KKT and transformation specifications, result/option semantics, benchmark manifest and budget accounting within the plan's bounds. Input IDs, seeds, expected statuses and oracle definitions must precede implementations intended to pass them.

## 4. Allowed changes

Only changes necessary for the linked five modules are authorized:

- `src/silo/{core,modeling,presolve,lp,mip,cuts,decomposition,interfaces,io,cli,utils}/` and the user-level package/solve entry point.
- Corresponding `tests/`, small fixtures and `examples/`; bounded verification/benchmark scripts and their manifests. Generated runs and distributions stay under ignored outputs/dist/build locations.
- `docs/`, `learning/` for the affected APIs and four module learning deliveries; stable old lesson IDs remain.
- The five-module plan's progress/evidence references, `.silo-dos/` program-specific status/rules, `ROADMAP.md`, `tasks/README.md`, this task's report and derived `tasks/INDEX.md`.
- `README.md`, `CHANGELOG.md`, `CITATION.cff`, `pyproject.toml`, necessary quality/build scripts and `.github/workflows/` for local artifacts and prospective CI. Native execution stays NumPy-based; SciPy/HiGHS is optional comparison only.
- Existing workbench catalog/source mappings may be updated to reflect the new program and evidence. No unrelated workbench UI feature expansion.

The allowed paths are boundaries, not authorization for unrelated refactors. The issued task file itself stays immutable after issuance.

## 5. Forbidden changes

- No external solver calls inside native algorithm layers; core must not depend on higher solver layers, and cuts must not depend on mip.
- No native C/C++, QP/nonlinear/conic line, parallel search, full Benders/branch-and-price, new industrial application or original C/D/E experiment.
- Do not revise old contracts, research notes/probes/data, archived evidence, CASE materials or unrelated user changes.
- Do not change the Apache-2.0 project license, install/rewrite reusable Skills/Agents, remove meaningful failing tests, relax frozen tolerances per instance, discard difficult benchmark IDs or change expected answers to match current output.
- No push, public tag/Release, PyPI/TestPyPI upload or other cloud publication under this contract. Preserve local commits and report remote state honestly.

## 6. Critical mathematical checks

- M1: use the plan's original-model KKT convention and reversible transformation ledger. Primal, dual/bound multipliers, stationarity, complementarity, objectives and infeasible/unbounded evidence must agree after combined transformations.
- M2: actual primal/dual simplex, basis identity, QR factor reuse, real scaling and general reoptimization. Nonoptimal or numerically unverified outcomes must not become optimal.
- M3: active/open/unknown-bound nodes all participate conservatively in the frontier. LP unboundedness alone proves no MILP conclusion. Unresolved unbounded relaxations cannot yield a finite stopping gap. GMI uses proved table-row conditions and local-bound-derived cuts default local.
- M4: an incomplete pricing result cannot prove the full master optimal; artificial Phase-I values must clear before feasibility is claimed. General covering/partitioning rows cannot acquire an invented global convexity row.

Independent read-only mathematical review is required for general LP transformation/dual semantics and for MIP frontier/GMI/unbounded semantics. The coordinator integrates the review; reviewer feedback is not additional run evidence.

## 7. Required verification and limits

- Use the plan's fixed 96 LP + 96 MILP independent-oracle models, 24 boundary cases, 48 LP + 24 MILP scale cases and at most 64 specified diagnostic calls.
- Follow the plan's layered run table: M1 input/transform subset, M2 LP/numerics/warm subset, M3 MILP/GMI/frontier subset, M4 research integrations; full matrix only in M5.
- Each module has at most initial integration plus two corrective integration reviews. Internal patch/test cycles do not become new contracts. Correctness regressions must be fixed within this scope; unrelated debt is reported.
- Local verification budget: M1 10 min, M2 25 min, M3 35 min, M4 10 min, M5 140 min, global reserve 20 min; 240 min total. Scale matrix worst-case 40 min/run, at most three full runs only in M5. Record consumed compute; unrun remote CI is separate.
- Run `.venv/Scripts/python.exe scripts/check_quality.py` at module checkpoints, with the venv Scripts directory added only to current process PATH for CLI tests. Use affected subsets while debugging rather than repeating whole suites without cause.
- Regenerate the task index after this contract/report is added with `scripts/check_project_structure.py --write-index`; run structure and `git diff --check`.
- M5 uses real wheel/sdist builds and source-independent clean install validation on both available Windows Python versions. CI YAML alone does not prove platform success.
- Exhausting a budget or reaching an unresolved substantive blocker means an honest incomplete handoff, not completion or an automatic extra module. Independent approved work may proceed without crossing a failed mathematical prerequisite.

## 8. Learning delivery

Read learning/README.md and WRITING_GUIDE.md. Deliver one coherent learning unit per M1–M4, updating existing material when appropriate and adding no more than four new lessons. Each includes principle, hand example, code/test mapping, research use, limitations and verified_code. M5 produces user/installation/reproduction guidance. Do not create one lesson per patch.

## 9. Report and continuation behavior

Update the single matching report with initialization and five module sections. Record actual commits, files, executed commands, results, failed attempts, independent review, consumed budget, original goal coverage, platform status and remaining obligations. Keep current progress in the profile rather than maintaining inconsistent duplicate status databases.

After a module PASS, continue directly to the next approved module. Do not end the program at the end of M1 or an individual patch. If the execution turn must return before all modules finish, leave concrete remaining work in the report and return that state to the coordinator; no new scope/approval is required for an in-scope resume.

After all modules pass, deliver the final finite checklist, actual supported domain/size, clean-install commands, artifact identity, code version and limitations, then stop. The coordinator performs the overall review before marking the single goal complete. Cross-platform release and original research C/D/E retain separate statuses.
