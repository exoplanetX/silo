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
| 最近求解器核验基线 | 857397e0cebdcfeb1c6c5ff325c17e0aa09c151b；[DAG列生成报告](../tasks/reports/20261019-04-01_dag-column-generation_report.md)，1859项测试与Ruff通过；定价保持12bfa35、RMP保持48c242d、LP内核保持ad62e0f |
| 学习系列基线 | L0001 v0.2.0按ad62e0f、L0002 v0.1.0按48c242d、L0003 v0.1.0按12bfa35、L0004 v0.1.0按857397e核对；初建系列bdddf58，见[系列报告](../tasks/reports/20261018-02-01_learning-series_report.md) |
| 最近管理记录 | [研究资产纳管与同步收尾](../tasks/reports/20261018-04-02_research-assets_report.md) |
| 本轮授权范围 | 第1–4步已验收并推送；用户已批准第5步[数值界一致性合同](../tasks/codex/20261019-05-01_cg-bound-consistency.md)，交开发对话实施，结果待验收 |
| 执行归属 | silo-solver开发；silo-solver-1010 负责思路与结果审查，按下文职责划分 |
| Git 同步 | 第4步及审查摘要f0c5f31已推送并核对即时远端；第5步签发/实施采用local-commit，实际差异用Git实时核对 |

这里列的是已记录的核验基线，不能据此声称在新的检出上重新运行过测试。
第 1–4 步均已由讨论对话验收，更新及审查摘要已成功推送至f0c5f31。
用户随后批准CG数值界一致性任务，本轮签发第5步单个合同；唯一新增签发提交
属于已知local-ahead，合同明确允许开发对话直接继续。第5步实现/测试待交付审查，
第6–7步尚未交付。本轮批准不含未来实现推送。
实现、测试和审查分别记录；本轮检查通过不代替讨论对话的交付审查。

## Completed Maintenance / Evidence

| 工作 | 实现或记录 | 核验依据 |
|---|---|---|
| 开发恢复、预处理与 MIP 状态纠错 | 6bd9543、a2490ec、a4814f4 | [重启记录](../docs/development_restart.md) |
| 独立小实例正确性基准 | 5cc88cb | [基准报告](../tasks/reports/20261010-04-01_correctness-oracles_report.md) |
| LP 原始行对偶与最优性核验 | bb6baff，合同 RR=02；RR=01 保留 | [LP 对偶参考](../docs/lp_duality.md)、[报告](../tasks/reports/20261018-01-02_lp-dual-optimality_report.md) |
| Revised Phase-I 来源行清理 | ad62e0f；区分来源行、基位置与列编号，删行后核验原模型 | [修正报告](../tasks/reports/20261019-01-01_revised-phase1-cleanup_report.md)、[L0001](../learning/lessons/L0001-lp-duality/README.md) |
| 最小RMP适配层 | 48c242d；最小化字段、原子显式增列、完整行冷重建与逐次最优核验 | [RMP报告](../tasks/reports/20261019-02-01_restricted-master_report.md)、[L0002](../learning/lessons/L0002-restricted-master/README.md) |
| 普通DAG精确定价 | 12bfa35；拓扑全路径最小化、严格标签与完整元组平局、原始列重构及保守数值失败 | [DAG定价报告](../tasks/reports/20261019-03-01_dag-pricing_report.md)、[L0003](../learning/lessons/L0003-dag-pricing/README.md)；已通过讨论对话审查 |
| DAG凸组合列生成 | 857397e；显式seed、冷RMP与完整定价、退化增列、数值界/差距及失败轮次 | [CG报告](../tasks/reports/20261019-04-01_dag-column-generation_report.md)、[L0004](../learning/lessons/L0004-column-generation/README.md)；已按保守浮点范围验收，舍入诊断限制见下文 |
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

第 1 步 revised Phase-I 冗余行清理已完成来源映射修正与数值保护，单/多残留构造基、
置换、原模型核验和全量检查通过，L0001 v0.2.0 已按实际实现提交更新。
12 个固定 cold-solve 小例均通过核验，尚未确认异位残留基在当前枢轴路径中的可达性。
2026-10-19，silo-solver-1010 已验收第 1 步，独立重跑 1399 项测试、Ruff 与结构检查，
并用一个组合冗余行模型的 288 个精确可行基核对清理，L0001 v0.2.0 通过审查。
近相关等式仍可能误报 UNBOUNDED，属于已复现的既有数值债；范围和反例记录在
[第 2 步合同](../tasks/codex/20261019-02-01_restricted-master.md)，本轮不修复底层状态判定。

第2步最小RMP已实现：沿用原生LP，显式转换最小化目标、乘数与约化成本，原子加列后
从完整行集合冷重建；每个最优候选先在完整输入上核验，再发布只读最小化快照。
84项新增检查及全量1483项测试通过；L0002 v0.1.0和四道习题已实际核对。
2026-10-19，silo-solver-1010已验收[第2步报告](../tasks/reports/20261019-02-01_restricted-master_report.md)，
独立重跑1483项测试、Ruff与结构检查，并用2x2指派模型核对96种行序/加列顺序/后端组合、
288次RMP求解，目标均为7 -> 7 -> 0；L0002代码例、习题及真实基线通过核对。
RMP仅覆盖当前列集合，非最优状态保留为后端诊断。

第3步普通DAG精确定价已实现：以拓扑DP最小化全部s-t路径的约化成本，严格比较中间标签，
精确平局按完整弧ID元组，独立重构原始列数据并检查数值一致性。
259项新增检查覆盖64子图×3组对偶的完整路径真值，386项相关检查与全量1742项测试、
Ruff通过；两个LP后端人工RMP桥接均得目标12 -> 10、rc=-2 -> 0。
L0003 v0.1.0的代码例和四题已按真实实现提交12bfa35核对。
具体域、浮点边界和证据见[DAG定价报告](../tasks/reports/20261019-03-01_dag-pricing_report.md)。
2026-10-19，silo-solver-1010在8efabeeb3a1e232ec0ca4b216a48661062f3b270上验收第3步：
独立重跑1742项测试、Ruff、结构及差异检查；另以5节点全向前10弧的全部1024个子图、
三组对偶完成3072次定价核对，独立Fraction枚举5184个路径值，含549个空域输入，全部通过。
新图族的节点/弧顺序与拓扑编号不同，成本、行系数和基项含正负值；未复用生产私有助手。
L0003正文代码及双后端人工桥接重新运行，十节、四题和真实代码基线通过核对。
独立只读数学复核未发现必须先修项；未把它重复计作实验结果。第3步可验收，无需修补实现。

第4步已按[执行合同](../tasks/codex/20261019-04-01_dag-column-generation.md)完成普通DAG
凸组合连续主问题自动CG：显式合法seed、路径元组身份、冷RMP与完整定价、每轮一列，
处理退化、失败和预算，计算P/D/rho/L及实际gap并按容差停止。
自动主例两后端均跨过P不变的一轮，得到2 -> 2 -> -1.5；另8个不同小模型及替代seed
共40组双后端/排列完整列LP对照通过。117项新增检查、460项针对性及全量1859项测试、
Ruff通过；L0004 v0.1.0代码例、四题和真实实现基线857397e已核对。
本轮一次独立只读复核因模型容量失败，没有形成审查结论，见[CG报告](../tasks/reports/20261019-04-01_dag-column-generation_report.md)。
2026-10-19，silo-solver-1010在85cdda3上验收第4步：独立重跑全量1859项测试
（7.81s）、Ruff、结构及差异检查，14个变更文件均在合同允许范围，禁区保持原样。
L0004正文完整代码双后端重跑，十节、四题及解答、真实实现哈希通过核对。
另构造54个解析模型：含三段弧的共享DAG有00/01/10/11四条路径，两条边际等式，
alpha、beta各取1/4、1/2、3/4；成本矩阵依次为(4,1,2,6)、(-3,2,1,-4)、
(0,0,0,0)、(-4,-4,3,3)、(9/4,-3/2,1/2,13/4)、(1,-5,-2,0)。
令lambda_11=t，则lambda_00=1-alpha-beta+t、lambda_01=beta-t、lambda_10=alpha-t，
t位于[max(0,alpha+beta-1),min(alpha,beta)]，线性目标的端点给出独立精确最优。
每模型采用两个端点的正权重路径作seed，再配原/反序及两个后端，共432次运行。
图的R/C基系数为1/8、-1/4，行RHS相应平移；基成本按矩阵序号为1/-2，c0为2/-3。
391次TOLERANCE_REACHED，目标符合解析值；41次按合同的严格L>P规则返回
NUMERICAL_ISSUE，其中Tableau为24次、Revised为17次；偏差仅2.22e-16至8.88e-16，
这41次末轮原始目标距解析最优也不超过8.88e-16。605个已发布界记录复算通过，
包括失败前历史轮；全部轮次另用Fraction对返回乘数核对精确平移下界，均合法。
这属于自然运行的保守拒绝，未声称432次均收敛，也未更改合同/代码掩盖诊断。
最小复现可用四条平行路径p00/p01/p10/p11，成本(-4,-4,3,3)，
R=(1/8,1/8,9/8,9/8)、C=(-1/4,3/4,-1/4,3/4)，conv=1、R=7/8、C=1/2，c0=-3；
按C/R/conv行序、p11/p00 seed序，Revised给权重0.75和0.25000000000000006，
P=-1.7500000000000002、D=L=-1.75、rho=0，触发差2.22e-16的数值诊断。
图可取base_cost=-2、base_coefficients={conv:1,R:1/8,C:-1/4}，弧增加对应0/1指标。
独立只读experiment_auditor确认合同证据覆盖与40组计数相符，无必须修正项；
该服务未跑实验、未改文件，其意见未重复计作实测或独立LP真值。
本轮数学服务因模型容量失败，未形成独立数学复核；主线程承担数学与实测检查。

第4步已按合同验收并推送，当前可用性受上述保守浮点诊断限制。
用户已明确批准第5步[数值界一致性任务](../tasks/codex/20261019-05-01_cg-bound-consistency.md)：
保留P/D/rho/L及原始有符号numerical_gap，追加消去公共c0的objective_gap与局部
roundoff_allowance，以固定32ULP工程约定容纳微小负差距，正向差距/rho阈值不扩大。
要求432族、最小自然反例、局部例外边界、大c0与实质矛盾保护，更新L0004至v0.2.0。
签发前在旧源码上重现391/41计数，并仅对末轮快照作新判据前瞻分类，432次均满足；
这不代替新实现回归。独立experiment_auditor只读审查补强三项证据边界，未跑实验/改文件。
推荐GPT-6 Sol/high。开发对话完成本地提交后停止，等待本对话验收；实现尚待开展。
资源定价、热启动与增量研究保持后续候选，本轮不扩大算法域。
资源约束、热启动、增量研究和性能主张仍待后续任务；native、Phase 9 closure及
Phase 10保持原有门控。第5步明确修订第4步的严格负gap判据，旧合同与历史证据保留；
在新实现交付前，当前源码行为仍以857397e为准。

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
