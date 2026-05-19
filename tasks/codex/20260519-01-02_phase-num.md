可以，下面这段直接给 Codex，用来做一个**小修订任务**：统一 Phase 编号、修正 placeholder message、确认本地测试通过，然后推送。

~~~markdown
# Codex Task: Clean Up SILO Phase Numbering and Verify Scaffold Quality

## Goal

Clean up the current SILO repository scaffold by making the roadmap, task files, README references, and placeholder messages use a consistent phase numbering convention. Then run local quality checks and push the cleanup commit to GitHub.

Repository:

https://github.com/exoplanetX/silo

## Phase Convention to Use

Use the following phase numbering consistently across README, ROADMAP, tasks, notes, and placeholder messages:

```text
Phase 0: Project Scaffold
Phase 1: Model Core and Canonicalization
Phase 2: Tableau Simplex
Phase 3: Revised Simplex and Basis Reoptimization
Phase 4: Presolve, Scaling, and Numerical Diagnostics
Phase 5: MIP Branch-and-Bound
Phase 6: Cut Generation and Callbacks
Phase 7: Decomposition Layer
Phase 8: Stochastic and Robust Optimization Extensions
Phase 9: Native Backend
~~~

## Required Changes

### 1. Rename task files if needed

Make sure the task files use exactly these names:

```text
phase_00_project_scaffold.md
phase_01_model_core.md
phase_02_tableau_simplex.md
phase_03_revised_simplex.md
phase_04_presolve_scaling.md
phase_05_branch_and_bound.md
phase_06_cut_callbacks.md
phase_07_decomposition.md
phase_08_stochastic_robust_extensions.md
phase_09_native_backend.md
```

Make sure file contents match the new phase numbers.

### 2. Update README.md

Make sure the roadmap section uses the same phase numbering:

```text
Phase 0: Project scaffold
Phase 1: Model core and canonicalization
Phase 2: Tableau simplex
Phase 3: Revised simplex and basis reoptimization
Phase 4: Presolve, scaling, and numerical diagnostics
Phase 5: MIP branch-and-bound
Phase 6: Cut generation and callbacks
Phase 7: Decomposition layer
Phase 8: Stochastic and robust optimization extensions
Phase 9: Native backend
```

Do not expand README into a long document. Keep it concise.

### 3. Update ROADMAP.md

Ensure ROADMAP.md uses exactly the same phase order and names.

### 4. Update simplex placeholder message

In:

```text
src/silo/lp/simplex/tableau.py
```

Make sure the placeholder message says:

```text
This placeholder will be completed in Phase 2.
```

### 5. Check references in notes/

Search all files under `notes/` for phase references. Fix any inconsistent numbering.

### 6. Check references in tasks/

Search all task files for inconsistent phase numbers or outdated filenames.

## Do Not Do

Do not implement simplex yet.

Do not change the solver architecture.

Do not introduce new dependencies.

Do not modify the Apache-2.0 LICENSE.

Do not force push.

Do not add generated files, cache files, virtual environments, or outputs.

## Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
```

If the console script is available, also run:

```bash
silo --help
silo --version
```

Fix any errors caused by renaming or imports.

## Git Commit

After all checks pass:

```bash
git status --short
git add .
git commit -m "Align SILO phase numbering"
git pull --rebase origin main
git push origin main
git status
```

## Acceptance Criteria

The cleanup is complete only if:

1. Phase numbering is consistent across README, ROADMAP, tasks, notes, and code messages.
2. The task filenames follow the Phase 0–9 convention.
3. `pytest` passes.
4. `python scripts/check_quality.py` passes.
5. CLI version/help commands work.
6. No generated files or cache directories are committed.
7. The commit is pushed to `main`.
8. `git status` is clean after push.

```
这个任务完成后，SILO 的 scaffold 就可以视为稳定版 Phase 0。下一步再正式进入 **Phase 1: Model Core and Canonicalization**，重点补 `Model.validate()`、JSON reader tests、solution writer tests、变量上下界、变量类型、目标常数和 row-bound 表达。
```
