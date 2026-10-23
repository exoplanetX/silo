# SILO Technical Route

## Authorized continuous prototype program — 2026-10-23

The user directly approved SILO-PROTOTYPE-20261023's five-module implementation.
[Contract](../tasks/codex/20261023-02-01_teaching-prototype.md) and
[plan](../tasks/phases/phase_10_teaching_research_prototype.md) authorize general
LP/MILP, the listed API/CLI/schema and packaging/CI changes, and program-specific
rule registration. Continue at module PASS without issuing another task or asking
again. The total report governs recovery; the coordinator owns final acceptance.
The execution checkpoint now delivers all five local modules; further activity
is limited to the coordinator's in-scope final review, with no sixth module.
The following native corridor and ordinary-task gates remain valid outside this
program. Native implementation stays deferred; original research C/D/E stays unchanged.

## Role / Current State

本文件维护技术边界与决策门控；当前完成项、核验基线和下一步建议统一查
[project_profile.md](project_profile.md)。执行历史查
[任务索引](../tasks/INDEX.md) 和 [decision_log.md](decision_log.md)。
本文件不重复追加每轮执行流水，也不自动形成待执行队列。

当前阶段 corridor 保持：

~~~text
phase9_parked_on_design_bookkeeping_after_native_defer
~~~

Phase 0–8 按其保守范围完成；Phase 9 open / parked，native implementation
deferred and unapproved；Phase 10 not started。依据为
[阶段路线](../ROADMAP.md)、[native 延期决定](../notes/25_native_implementation_defer_decision.md)
及 [里程碑报告](../tasks/reports/20260604-12-01_project-milestone-audit_report.md)。

## Existing Scope / Maintenance

- 当前 Python LP、presolve 和最小 branch-and-bound 可通过单独批准的任务维护。
  2026-10 的状态纠错、正确性基准与 LP 对偶工作已完成，证据由当前摘要链接。
- 窄范围文档、报告、导航与状态维护按 L0 或具体流程风险分类执行。
- 对现有 .silo-dos 文件先检查内容与存在性；旧设计中的 create-file 建议是历史候选。
- 模型、算法、数学约定、数值或正确性任务按
  [tasks/README.md 6.8](../tasks/README.md#68-development-companion-learning)
  声明学习交付；行政整理说明不适用即可。
- 推荐项先形成一个 scope-locked 合同。执行完当前任务后停止。

## Risk / Approval Gates

| 风险 | 范围 | 执行条件 |
|---|---|---|
| L0 | 文档、报告、审查、有限 bookkeeping | 范围明确、同步条件满足且无高风险改动 |
| L1 | 有设计依据的被动记录、protocol、no-op 边界、验证支撑 | 适用 standing approval 或具体授权；有验收条件 |
| L2 | LP/MIP/presolve/后端、求解行为、公共 API/CLI/JSON schema | 用户明确批准具体任务 |
| L3 | 阶段转换、架构重设、native、依赖/build/packaging、新能力线、流程规则 | 用户明确批准对应范围 |

完整细则查 [standing_approval_profile.md](standing_approval_profile.md)、
[AGENTS.md](../AGENTS.md)、[任务规则](../tasks/README.md) 与本轮合同。
当前指令和批准范围不能由旧模板或历史执行记录代替。

## Native Candidate / Implementation Gate

候选仍为 tableau_leaving_row_ratio_test。用户可单独要求保持延期、修订或拒绝候选，
也可批准一个明确的实现任务；已有候选选择和审批模板均不表示实现获批。

实现前必须明确：候选及实现形式、允许文件、依赖/build/platform 政策、生成物排除、
availability-gated 测试、Python 默认 dispatch 边界，以及 CLI/schema 的独立授权。
实现按 L3 管理；dispatch 或公共接口变化按相应 L2/L3 范围审阅。

## Phase 9 Closure / Phase 10 Planning

Phase 9 closure 需要用户明确批准；closure-readiness 审查和正式 closure bookkeeping
分别分类为 L0 与 L3。未来审查应说明：native 延期是否可作为本阶段终点、是否存在
阻塞、允许修改的 bookkeeping 文件，以及继续延期的记录。关闭 Phase 9 不自动启动
Phase 10。可能的 future classification 为
phase9_complete_for_deferred_native_boundary_scope，当前仍保持 open / parked。

Phase 10 planning 需要明确的 planning 授权，合同应说明目的、范围、非目标、依赖方向、
门控和候选原子序列。若 Phase 9 仍开放，需明确接受并行规划。
planning 批准不包含实施授权。

## Source / Git Boundaries

- core 独立；原生算法不调用外部求解器。实际源码入口见
  [development_layout.md](../docs/development_layout.md)。
- 修改 src、tests、examples、notes、ROADMAP 或阶段文件均须属于本轮合同的允许范围。
- 旧 tasks/codex 合同保持不可变；历史建议先与当前摘要核对。
- 不自动新增 native/build/packaging、公共 CLI/schema、阶段转换或下一项任务。
- 默认 local-commit；push 权限按任务 Git mode 和用户指令。
- 同步状态实时查询；脏工作区或 ahead/behind 不明时，依据
  [remote_sync_proof.md](remote_sync_proof.md) 和本轮明确的恢复授权处理。
- 已知无关文件可以在批准范围内保留并使用干净隔离 worktree；集成前复核主检出基线、
  原文件哈希和允许范围。干净 worktree 不能用来声称主工作区干净。

历史执行结论保留在原合同、报告及 Git 历史。本次整理的来源和替代关系见
[20261018-03-01 报告](../tasks/reports/20261018-03-01_project-navigation_report.md)。
