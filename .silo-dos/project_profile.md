# SILO Project Profile

## Current Snapshot — 2026-10-19

本文件是当前项目状态的单一摘要入口。任务规则以
[tasks/README.md](../tasks/README.md)、本轮合同和用户指令为准；阶段范围以
[ROADMAP.md](../ROADMAP.md) 和 [阶段记录](../tasks/phases/) 为依据。
历史报告中的“下一步”属于当时建议；当前建议只在本页汇总。

| 项目 | 当前状态 / 依据 |
|---|---|
| 项目身份 | SILO，Python 教学与保守参考求解器 |
| 代码版本 | 0.1.0，开发中，尚未正式发布；开发基线用 Git commit 定位 |
| 流程版本 | SILO-DOS v0.4，与代码版本分别管理 |
| Phase 0–8 | 各自已批准的保守范围完成，具体边界见阶段记录 |
| Phase 9 | open / parked；native implementation deferred and unapproved |
| Phase 10 | not started |
| 最近求解器核验基线 | bb6bafff1cea78943eb8ae9d4b1a1b7d2a4dc52b；[LP 报告](../tasks/reports/20261018-01-02_lp-dual-optimality_report.md) |
| 学习系列基线 | bdddf5851b72397c641c3dd872a306f66a12b296；[系列报告](../tasks/reports/20261018-02-01_learning-series_report.md) |
| 最近管理记录 | [研究资产纳管与同步收尾](../tasks/reports/20261018-04-02_research-assets_report.md) |
| 本轮授权范围 | 第 1 步 revised Phase-I 来源行清理修正；[执行合同](../tasks/codex/20261019-01-01_revised-phase1-cleanup.md)，已签发，签发时尚未实施 |
| 执行归属 | silo-solver开发；silo-solver-1010 负责思路与结果审查，按下文职责划分 |
| Git 同步 | 当前任务 local-commit，不 push；已知签发提交的 local-ahead 属本轮继续执行授权，实际状态实时核对 |

这里列的是已记录的核验基线，不能据此声称在新的检出上重新运行过测试。
本轮只授权第 1 步，开发对话完成后停止并等待审查；第 2–7 步仍需另行交付。
此处的“已签发”只表明合同已准备，不代表实现、测试或审查通过。

## Completed Maintenance / Evidence

| 工作 | 实现或记录 | 核验依据 |
|---|---|---|
| 开发恢复、预处理与 MIP 状态纠错 | 6bd9543、a2490ec、a4814f4 | [重启记录](../docs/development_restart.md) |
| 独立小实例正确性基准 | 5cc88cb | [基准报告](../tasks/reports/20261010-04-01_correctness-oracles_report.md) |
| LP 原始行对偶与最优性核验 | bb6baff，合同 RR=02；RR=01 保留 | [LP 对偶参考](../docs/lp_duality.md)、[报告](../tasks/reports/20261018-01-02_lp-dual-optimality_report.md) |
| 开发伴学系列 | bdddf58，L0001 已核对 | [学习目录](../learning/CATALOG.md)、[报告](../tasks/reports/20261018-02-01_learning-series_report.md) |
| 管理入口与任务追溯 | cd83009 | [整理报告](../tasks/reports/20261018-03-01_project-navigation_report.md) |
| Pricing 研究资产 | 五篇笔记、五份原始探针、16 文件来源清单 | [资产入口](../scripts/research/pricing/README.md)、[纳管报告](../tasks/reports/20261018-04-02_research-assets_report.md) |

Phase 6–8 的完成指接口、toy 驱动与有限变换边界；完整割算法、生产级
Benders / column generation / branch-and-price 和一般不确定性求解仍待后续立项。
现有 LP 支持域、MIP 支持域和数值限制分别查阅当前 API 文档。

## Recommendations / Asset Disposition

日常管理入口、任务索引及研究资产已建立稳定维护源。五篇笔记仅调整来源路径，
五份探针保持原始字节；35 个原始文件已完成独立本地备份与哈希核对。
历史原件和新运行结果保持各自身份，备份位置与复现范围见纳管报告。

旧 lp-dual-evidence worktree 已核对干净且 bb6baff 已合入；它属于另一个对话，
应用的归属检查拒绝本对话接管，因此保留在原所有者下。原对话可在不再使用时归档。
resfs 原件继续保留且受 Git 忽略；独立备份已核对，OneDrive 云端上传未单独验证。

第 1 步 revised Phase-I 冗余行清理的 source-row provenance 已形成
[详细合同](../tasks/codex/20261019-01-01_revised-phase1-cleanup.md)，交由 silo-solver开发。
执行中复核已记录构造例与可达性边界，完成来源映射修正、回归与原模型核验，
并更新 L0001。实现状态以该任务报告、提交和本对话审查为准。
后续 RMP、精确定价和列生成闭环仍为建议，未批准实施；native、Phase 9 closure
和 Phase 10 保持原有门控。

## Source / Directory Map

| 查什么 | 入口 |
|---|---|
| 当前状态、已完成与建议 | 本文件 |
| 技术边界和审阅门控 | [technical_route.md](technical_route.md)、[standing approval](standing_approval_profile.md) |
| 长期决策与被替代的历史状态 | [decision_log.md](decision_log.md) |
| 任务规则、全部合同与报告 | [规则](../tasks/README.md)、[自动生成索引](../tasks/INDEX.md) |
| 源码实际入口、目录职责、版本约定 | [development_layout.md](../docs/development_layout.md) |
| 当前用法与接口 | [docs/README.md](../docs/README.md) |
| 数学讲解、练习与核验来源 | [learning/README.md](../learning/README.md) |
| 原始设计、反例、研究演变 | [notes/README.md](../notes/README.md) |
| 同步状态解释 | [remote_sync_proof.md](remote_sync_proof.md) |
| 经验与流程改进 | [experience_map.md](experience_map.md)、[self_evolution.md](self_evolution.md) |

对话职责自 2026-10-19 起按用户指令明确划分：

- **silo-solver-1010**（`01a1254a-b349-77d0-8c66-d4b711cd511f`）：讨论思路、
  设计/交付任务、审查开发结果；不在本对话实施已交付的 solver 代码任务。
- **silo-solver开发**（`01a15208-bea9-7030-aacc-95d785e8fa58`）：执行明确批准的
  单个合同，完成实现、测试、伴学材料、报告和合同约定的 Git 操作后停止。

进入执行的决定应形成仓库合同或决策记录；任务解释不依赖聊天历史。
.silo-dos 中的旧架构、集成设计及 Research Brain 桥接文件按需阅读，
其中未执行的候选动作应先与本页和当前文件存在性核对。

## Operating Boundaries / Live Checks

- 正式源码只有 src/silo；core 保持独立。实际导入关系见目录说明。
- 外部求解器仅用于 interfaces、examples 或比较测试。
- 每轮一个原子任务；保留历史合同、报告、笔记和学习篇目身份。
- L0/L1 适用条件查 standing approval；L2/L3 需要明确授权。
- 默认 local-commit；任务允许或用户要求时才 push。同步失败保留本地提交。
- native 实现、依赖/build/packaging、dispatch、公共 CLI/schema、阶段转换保持原有门控。
- 战略信息缺失时依 local mirror → Research Brain → user decision 查询，
  Research Brain 不能替代本地执行授权。

从项目根目录执行：

~~~text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
python scripts/check_project_structure.py
~~~

以上 Git 命令中的 origin/main 是本地跟踪引用；需要确认远端即时状态时再访问远端。
文档维护检查受影响的链接、索引与实例；求解器改动按合同运行针对性及完整质量检查。
