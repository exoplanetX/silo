# 开发目录与版本追溯

日常管理从 [当前项目状态](../.silo-dos/project_profile.md) 开始，历史检索从
[任务索引](../tasks/INDEX.md) 开始。当前接口从 [文档入口](README.md) 查询。

## 目录职责与维护源

| 目录 / 文件 | 用途与维护约定 |
|---|---|
| src/silo | 正式求解器唯一源码树；使用 Git commit 和分支管理代码演进 |
| tests/unit、regression、verification | 模块测试、CLI/文件回归、独立小实例核验 |
| tests/fixtures、examples | 小型固定输入、可运行例子；生成结果进入 outputs |
| native | 当前仅预留未来原生实现，实施保持延期 |
| docs | 当前用法、接口范围、开发基准与操作入口 |
| notes | 原始设计、反例、探索与历史决定；结论应结合日期、假设和后续证据 |
| learning | 系统讲解的唯一正文；篇目 ID 稳定，核验基线独立记录 |
| tasks/phases | 阶段目标与范围；阶段完成限于已批准边界 |
| tasks/codex | 不可变的原子任务合同；修订新建 RR |
| tasks/reports | 对应执行证据；记录实际基线、检查与遗留问题 |
| scripts/research/pricing | 已归档的合成研究探针、固定来源清单与运行入口 |
| examples/research | 使用外部求解器的隔离研究参考例 |
| .silo-dos/project_profile.md | 当前状态单一摘要，链接完成项和待议事项 |
| .silo-dos/technical_route.md、decision_log.md | 技术门控、长期决定与历史替代关系 |
| outputs、resfs、.venv、各类缓存 | 本地运行、历史原件、环境和缓存；Git 忽略 |

保留既有文件路径以维持仓库链接。需要迁移时单独确定合同、引用更新与验收；
历史合同和报告保持原样，使用对应 commit 查看当时的文件。
不要建立第二套 final/new/v2 求解器源码目录。

## 实际求解器入口

| 功能 | 实现入口 | 阅读提示 |
|---|---|---|
| CLI 和后端选择 | [main.py](../src/silo/cli/main.py)、[solvers.py](../src/silo/cli/solvers.py) | --solver 与 --lp-solver 的适用命令分别管理 |
| Tableau Phase I/II | [tableau.py](../src/silo/lp/simplex/tableau.py) 的 TableauSimplexSolver.solve | 两阶段实际流程位于本模块 |
| Revised Phase I/II | [revised.py](../src/silo/lp/simplex/revised.py) 的 RevisedSimplexSolver.solve | 来源行/基位置清理已修正；有限精度边界仍保留 |
| 最小 RMP 适配层 | [restricted_master.py](../src/silo/decomposition/restricted_master.py) | MIN目标/对偶转换，完整行冷重建、显式加列与逐次最优核验 |
| 显式RMP基复用 | [revised.py](../src/silo/lp/simplex/revised.py) 的 reoptimize、[basis_snapshot.py](../src/silo/lp/simplex/basis_snapshot.py) | 全行非人工基语义快照、原始点门控、Phase II与单次cold；RMP solve_reoptimized管理缓存 |
| 普通DAG精确定价 | [dag_pricing.py](../src/silo/decomposition/dag_pricing.py) | 全s-t路径最小约化成本，独立于LP/RMP；不含资源约束或CG控制器 |
| 整数资源DAG冷定价 | [resource_dag_pricing.py](../src/silo/decomposition/resource_dag_pricing.py) | 非负可加整数资源，完整(node,resources)状态、独立重构与状态/转移预算；目标沿浮点参考语义 |
| 资源路径参考CG | [resource_dag_column_generation.py](../src/silo/decomposition/resource_dag_column_generation.py) | 同图资源合法seed、完整资源冷定价、单conv连续主问题、可选RMP复用与有界失败历史 |
| DAG凸组合列生成 | [dag_column_generation.py](../src/silo/decomposition/dag_column_generation.py) | 合法seed、默认cold/显式可选RMP重优化及逐轮诊断、完整定价、退化增列与数值差距门控 |
| DAG可行性恢复 | [dag_feasibility.py](../src/silo/decomposition/dag_feasibility.py) | 单位人工违背量、全域零成本定价与无人工原始行复核；调用者显式进入原目标CG |
| LP 最优性核验 | [optimality.py](../src/silo/lp/optimality.py) | 原始输入坐标；有限精度与支持域见 API 文档 |
| LP 无界候选核验 | [unboundedness.py](../src/silo/lp/unboundedness.py) | 两后端终止处调用；完整原模型的点/方向逐项 Fraction 核验 |
| 预处理与恢复 | [presolver.py](../src/silo/presolve/presolver.py) | 保留变换与原坐标恢复关系 |
| 最小 MIP B&B | [branch_and_bound.py](../src/silo/mip/branch_and_bound.py) | 使用 LP 松弛和被动 cut/callback 边界 |
| 待发展骨架 | [phase_one.py](../src/silo/lp/simplex/phase_one.py)、[phase_two.py](../src/silo/lp/simplex/phase_two.py)、[scipy_backend.py](../src/silo/interfaces/scipy_backend.py) | 当前分别原样返回模型或返回 NOT_SOLVED；文件名不表示功能已接通 |

tableau 与 revised 是并存的两种后端，分别维护算法行为并做独立核验。
cuts/decomposition/uncertainty 的 conservative/toy 完成状态不表示生产级算法已经实现。
RMP已能求解当前显式列集合，普通DAG定价覆盖其图定义的完整路径域。
带凸组合等式的普通DAG自动CG已形成参考循环；独立资源冷定价已覆盖非负整数可加资源。
资源路径CG已在单conv连续参考主问题接入；真实覆盖/分割应用、时间窗/访问记忆及
原有通用ColumnGenerationSolver入口仍待后续任务。
独立DAG恢复器允许合法非空seed不满足耦合行，核验后交还保留原目标的seed问题。

## 实际导入边界

下面箭头表示“左侧导入右侧”，列出关键模块边界，省略部分共享工具依赖：

~~~text
modeling, presolve, lp, cuts, uncertainty -> core
decomposition -> lp, core
mip -> lp, cuts, core
cli -> io, lp, mip, presolve, core
interfaces -> core
~~~

AGENTS 中的长链用于表达开发递进。Phase 6 已实现的 mip → cuts 是对被动记录、
separator/callback protocols 的依赖；cuts 保持独立于 mip，避免形成回路。
core 保持独立；外部求解器调用仅限 interfaces、examples 或比较测试。
LP无界核验只读core模型与原始候选，使用标准库精确标量运算和既有支持域常量；不反向依赖求解器或上层模块。
基快照助手依赖core、Basis、标准形与numpy，不导入Revised或RMP；RMP仅调用新公开LP入口。
CG可选路径只消费公开RMP重优化结果；Revised公开类仅用于参数类型校验，不访问LP私有接口或RMP内部状态。
RMP只通过LPSolver和既有最优性核验器消费LP；下层不反向导入decomposition。
DAG定价模块本身只依赖标准库和utils常量；RMP人工桥接及完整路径枚举只在测试/教学中。
新DAG控制器消费core模型、既有RMP/定价和LP后端接口，不访问RMP私有状态；完整列枚举仍只在测试。
可行性恢复器也只消费公开RMP/定价和CG输入记录，内部保留两类列元数据，不调用旧CG优化入口。
结构检查解析显式 Python 导入；它不证明动态导入或所有运行时行为符合边界。

## 版本、任务与核验基线

| 身份 | 用法 |
|---|---|
| 代码 | 正式发布使用统一的 vX.Y.Z；开发迭代以完整 Git commit 定位 |
| 流程 | SILO-DOS v0.4 单独演进，不代表求解器版本 |
| 任务 | YYYYMMDD-TT-RR_slug；新事项用新 TT，同一任务修订用 RR |
| 学习材料 | LNNNN 身份保持稳定；讲解版本和 verified_code 分别记录 |

pyproject.toml、silo.__version__ 和 CITATION.cff 保持相同代码版本。
当前 0.1.0 为 Unreleased，引用文件不宣告发布日期。正式发布时再统一变更记录、
发布日期和 tag。普通开发提交无需为每个文档改动递增包版本。

合同写明基线；报告写明实际核验基线、改动、命令与结果。报告所在提交通过
'git log -1 --format=%H -- tasks/reports/<report-file>' 定位，避免在同一提交内填写
其尚未产生的自身哈希。工作副本状态与远端状态用 Git 实时查询。

五篇 pricing 笔记与五份原始探针已纳管，见
[研究资产入口](../scripts/research/pricing/README.md)。原始探针按字节保留并校验哈希；
实际算法不因归档而升级为正式求解器能力。应用参考例按外部求解器边界放在 examples。
16 个公开输入固定到来源 commit/hash，数据和新结果保持 Git 忽略。35 个原始文件的
独立本地备份及旧工作副本的归属处理见
[纳管报告](../tasks/reports/20261018-04-02_research-assets_report.md)。

## 日常检查

从项目根目录、项目 Python 环境执行：

~~~powershell
& .\.venv\Scripts\python.exe scripts/check_project_structure.py --write-index
& .\.venv\Scripts\python.exe scripts/check_project_structure.py
$env:PATH = (Join-Path $PWD '.venv\Scripts') + ';' + $env:PATH
& .\.venv\Scripts\python.exe scripts/check_quality.py
~~~

--write-index 只刷新 tasks/INDEX.md；普通检查只读。新增合同或报告后重新生成索引。
它展示文件是否存在，执行成败仍以报告内容为准。已知历史例外精确列于
[history_exceptions.json](../tasks/history_exceptions.json)；新增碰撞会失败。

运行前确认解释器与 silo.__file__ 属于预期环境及本次检出。隔离 worktree 使用既有
环境时显式指定该 worktree 的 src 和 console-script PATH。当前恢复环境继承全局包，
详见 [重启记录](development_restart.md)，尚未形成锁定的干净重建环境。

GitHub 保存已推送提交；OneDrive、未跟踪文件和 Git 忽略文件的状态分别核对。
任务执行完按 Git mode 提交/推送，并报告本地与远端引用及剩余工作区文件。
