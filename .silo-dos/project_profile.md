# SILO Project Profile

## Current Revision — 2026-10-24

正确性修订候选0.2.0a2已完成，代码f488189bd5835d9b1b4c7d0319b847a1671da1d1。
[合同20261024-01-01](../tasks/codex/20261024-01-01_prototype-correctness-revision.md)的
R1输入、R2最优性与界、R3四安装均有通过证据；
[执行报告](../tasks/reports/20261024-01-01_prototype-correctness-revision_report.md)是实际收据入口。

旧候选基线4ca4bab的[审查](../docs/prototype_audit_20261024.md)确认四反例：
MILP误用可行性容差剪枝、CG漏小负rc并错报全池最优、MPS等值整数丢精度、派生侧非零下溢。
修订已修复这些机制；有限CG以原始二进制数据全池精确可行对P=D门控，失败保留无证明状态。
6327测试、新384调用/192直接HiGHS/48整数穷举、旧288集及两公开例、保存64诊断复核均通过。
Windows3.11.15/3.13.9×wheel/sdist四个新隔离安装通过，工件120模块匹配代码提交。
原研究A/B已验收、C HOLD、D/E未启动；native Phase9仍parked/deferred；远端CI pending。

本单八项执行验收已PASS，交讨论对话独立审查后停止执行。首次check_quality.py因尾部格式lint
退出1的记录保留；用户明确批准调用上限从128提高至144后，完整复验exit0，6327测试、结构和Ruff通过。
严格调用144/144，完整质量2/3次，自动验证保守226/3600秒；新旧矩阵均1轮，四安装均首轮成功。
追加复验未改产品源码或工件，不增加算法、实例或研究任务，不自动进入下一单。

当前分支codex/teaching-research-prototype，追加收尾前cecb26c时cached origin/main...HEAD=0/48，
没有即时远端查询。两项治理变动按原哈希保留并排除提交；local-commit，未push。
[修订计划](../tasks/phases/prototype_revision_20261024.md)保持单合同三个内部检查点；
推荐GPT-6 Sol/high，不声称已切模型。本单收据已闭合，最终提交见执行报告Git history。

## Completed Program — 2026-10-23

SILO-PROTOTYPE-20261023 is explicitly authorized under the
[single total contract](../tasks/codex/20261023-02-01_teaching-prototype.md).
The execution chat implements M1→M2→M3→M4→M5 continuously; the discussion chat owns
the sole goal and overall review. The [total report](../tasks/reports/20261023-02-01_teaching-prototype_report.md)
is the execution checkpoint. Initialization: authority registered before source edits;
KKT/transform and fixed-input freeze committed 2ca6098. M1/M2 local module checkpoints PASS:
general input/restore, original witnesses,96 LPs,4 genuine warm paths,QR and separate tolerances.
M3 local module/independent algorithm gate PASS; general frontier/unbounded states,
exact GMI/local cuts and resource guards validated. Full quality6058 passes;
supplemental raw evidence264+24+64 statically verifies. M4 public research interfaces,
finite-pool CG/Phase I and frozen integrations PASS, full quality6137 passes.
M5 local acceptance PASS: frozen192 small+24 boundary+72 scale all PASS; strengthened
saved-output recheck288 PASS with0 new solves; exactly64 diagnostics PASS;192 optional
HiGHS comparisons PASS; both public integrations and recorded mechanism replay PASS.
Windows3.11/3.13 wheel/sdist all four isolated installs PASS (one NumPy network retry
retained). Final full quality6147 PASS, source/learning/artifact identities sealed in
outputs/prototype/final_acceptance.json; overall discussion-chat technical gate GO.
Remote Windows/Linux CI remains pending. Local candidate0.2.0a1, no publication.
Branch codex/teaching-research-prototype, issuance 1b7deb9; current code via total report.
Known governance changes are retained byte-for-byte and excluded from commits;
local-commit, no push, remote_sync_status=dirty_worktree. Verification accounted: M1 96s,
M2 30s,M3 76s,M4 60s,M5 480s (350s install stream incl network failure),reserve22s;
total764s/14400s (conservative rounded account). Scale runs1/3, diagnostic calls64/64.
Implementation/acceptance commit f78b412398fe70e2fe7f645b16aeebabe4967a4a;
artifact source d4c852f7112c6abfc2d799c42c924a6aa4cef188. Final status-only commit
is located by the total report's Git history. Cached origin/main...f78b412 is0/43;
no live remote lookup. Execution complete; no automatic next task.
Native Phase 9 remains parked; the original research A/B accepted, C HOLD, D/E not started.
This program's new general LP/MILP and packaging scope does not complete that research.

## Historical Snapshot — 2026-10-20

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
| 最近求解器核验基线 | B资源参考CG实现6858a736568a6d502271acf39d29f855def65b93；5581项(17.29s)、Ruff/结构通过，新增282项含216次三模式独立全列调用；A及旧CG/RMP/LP不变，见[B报告](../tasks/reports/20261020-05-01_resource-dag-cg_report.md) |
| 学习系列基线 | L0001 v0.2.0按ad62e0f、L0002 v0.1.0按48c242d、L0003 v0.1.0按12bfa35、L0004 v0.2.0按15b403b、L0005 v0.1.0按02aed7d、L0006 v0.1.0按c460aa7、L0007 v0.1.0按90b377f、L0008 v0.1.0按f4cc36e、L0009 v0.1.0按be03540、L0010 v0.1.0按6858a73核对；初建系列bdddf58，见[系列报告](../tasks/reports/20261018-02-01_learning-series_report.md) |
| 最近管理记录 | [本轮验收与停止记录](../docs/bounded_goal_outcome_20261020.md)；[固定计划](../docs/seven_step_completion_plan_20261020.md)和[全局复查](../docs/development_route_review_20261020.md)保留 |
| 本轮授权范围 | A/B已由讨论对话验收；C签发前就绪性HOLD，本轮到达预设停止点；C实验及D/E未签发，不自动新增前置平台任务，两治理变动原样保留，不push |
| 执行归属 | silo-solver开发；silo-solver-1010 负责思路与结果审查，按下文职责划分 |
| Git 同步 | B文档a9a9f67交付后main、cached 0/31；讨论验收与C停止记录另作本地提交，最终差异以终端实查为准。两治理文件哈希不变且排除提交，未push、未查询即时远端，remote_sync_status=dirty_worktree |

这里列的是已记录的核验基线，不能据此声称在新的检出上重新运行过测试。
开发序号1–9均已由讨论对话按合同验收；原七步的完成范围见下节，不据此计为原研究计划完成。
远端上次即时核对已同步至第4步审查摘要f0c5f31。
第5步签发、实现、学习和验收摘要四个已知本地提交为8ee397e、15b403b、f0cc01a、
b886458。用户获知该状态后批准下一步，继续授权覆盖这四个提交及本次第6步
合同/摘要/INDEX签发提交。第6步可行性恢复已完成并通过本轮讨论审查；
2026-10-20用户在获知8个未推送提交后批准第7步，继续授权覆盖这8个及本次签发提交。
第7步仅修正两个LP后端无界终止依据，现已验收；实现c460aa7、文档445da97及验收a26039f均为本地提交。
用户在获知12个未推送提交后批准第8步，继续授权覆盖上述提交及本次合同/摘要/INDEX签发提交。
第8步已通过讨论验收；用户获知16个未推送提交及两项治理文件变动后批准第9步，
继续授权覆盖上述提交及本次合同/摘要/INDEX签发，已知治理文件按合同哈希原样保留。
开发对话仅执行本次CG显式接入任务，完成后停止待审；本轮及本合同均不推送。
实现、测试和审查分别记录；第6步实现02aed7d及文档70293f9同样保留本地提交身份。

## Original Plan / Global Review — 2026-10-20

本次全局回查确认：原计划为七个研究/开发里程碑，后来开发序号1–9含新增纠错与工程增强，
二者不能逐号对应。完整证据、原对话定位及对应表见
[开发路线全局复查](../docs/development_route_review_20261020.md)。

- 原1/2完成；原3在A验收后覆盖普通DAG及非负整数可加资源冷定价；
  时间窗/访问记忆等更一般资源状态未覆盖，原4的B资源路径单conv连续参考闭环已验收。
- 实际开发5/7是正确性修复，6是可行性恢复扩展，8/9是RMP基复用及CG接入；这些交付通过
  各自合同验收，不等于原5/6/7的研究适用性、增量定价机制和完整计算价值已完成。
- notes26已将固定资源约束路径中对偶更新下的精确状态维护登记为当前研究主线；
  notes29/30仍缺定价瓶颈、小完整接口与完整维护成本优势的联合应用正例。
  历史理论/外置应用探针属于已有部分证据，不能忽略，也不能冒充原生算法实现或正面收益。
- 当前实质阶段：普通DAG参考闭环、A整数资源冷定价及B资源参考CG已建立，
  现停在C签发前就绪性HOLD；原5应用联合证据、原6增量机制及原7完整价值评价保持未完成。
- 撤回将冷热RMP/CG耗时实验自动作为下一优先任务的建议。A/B已按有界清单验收；
  C尚缺可核验的应用精确定价及真实轨迹基础，强冷/直接动态对照也未落实，D/E不启动。
  未来恢复前先明确有限平台核验方案并获相应授权，不自动追加能力线或成本比较任务。
  原研究问题保持，具体机制的失败不构成替换主题或缩减完成标准的许可。

此前总体复查没有启动新开发任务；用户后续授权下的A/B执行和C停止见下节，ROADMAP阶段未转换。
下一项联合核查建议GPT-6 Sol/high；推荐不代表已切换模型。

## Standing Instruction / Fixed Goals and Exit Boundaries — 2026-10-20

用户明确要求：前期按目标方向制定的分阶段任务必须坚持原目标，并有明确结束界限，
禁止无限追加任务。执行依据已写入[tasks/README.md第6.9节](../tasks/README.md#69-fixed-goals-phase-exit-and-bounded-work)。

- 每次签发先引用原阶段/里程碑，列明唯一问题、验收依据、成功停止点和失败/超限停止点。
- 阶段计划列有限交付清单及原子任务数量上限；有界研究/实验列具体执行预算。
- 新增修复或增强须说明对原计划及结束界限的影响，按原权限批准；合同数量不充当研究进度。
- 达标后交付并停止；超限未达标则交付证据、保留未答义务，不通过扩项或降低标准宣称完成。
- 本对话继续负责目标和结束界限的审查，开发对话按单合同执行后停止。

本次为用户直接要求的规则落地，仅维护任务规则和当前摘要；未签发开发10、算法任务或阶段转换。
行政规则维护无新增算法学习主题；原学习系列保持。

## Remaining Plan / Stopped at C Pre-issuance HOLD — 2026-10-20

此前目标模式准备阶段只要求检查与列计划；后续启动授权及A/B合同见本节末。总计划详见
[原七步有界收尾计划](../docs/seven_step_completion_plan_20261020.md)。
剩余清单最多五项：A资源冷定价（原3）、B资源路径凸组合参考CG（原4）、
C单一真实应用适用性裁决（原5）、条件D一个增量定价机制（原6）、条件E完整成本评价（原7）。
C的真实覆盖/分割模型不得强加全局convexity；B的参考闭环不充当真实应用证据。
C为HOLD或任一预算/范围阻断即停止本轮，D/E不启动；不自动追加第六项或转新应用。
E完整评价可以得出无收益并结束评价交付；超限中断只能登记部分完成，长期研究目标保持。

按文档补当前进程PATH后的全量检查通过，未发现验收后代码破坏。第一次未补PATH有13项
console入口找不到的失败，第二次4075通过；没有为通过测试修改代码或依赖。
理论、证据及独立红队只读复核支持该有条件计划，未重复运行实验。
实例ID、真实应用适配、强基线及D具体机制须按条件在未来合同中冻结，不将草案当执行授权。
讨论对话负责逐单签发和审查，开发对话逐合同完成后停止；计划整理时尚未启动目标，后续授权见下段。
用户随后要求把目标模式计划集中列出，已在同一计划第7节补齐目标说明、职责、
结束条件及可采用的启动文本；本次整理不构成执行、对外消息或push授权。

用户随后在“silo-solver开发”的turn 01a159c2-87ed-7773-a738-59d5d0bb7f28直接选择
“授权发送启动消息（推荐）”。问题明示本讨论对话逐单签发/独立审查、开发对话执行合同，
并接受本地未推送状态、保留两治理变动、遵守预算及C未过即停；已只读核验原始人类回复。
该直接授权覆盖有界协调消息和清单内逐单推进，不因同一已知状态再次询问。
执行者的持续目标已在其对话启动，本对话不重复创建第二个目标。

本轮首份已签发合同：[A资源冷定价](../tasks/codex/20261020-04-01_resource-dag-pricing.md)；B见后节。
签发前main=77c62bb、cached 0/24；继续授权覆盖24已知本地提交及签发提交，
两治理文件哈希与前述记录一致，未提交。TT04与L0009经扫描可用。
A固定有限DAG、非负整数资源及上限、(v,r)冷状态，公开状态/转移预算和1152调用独立oracle，
交付L0009；不接CG/增量/应用。理论与证据服务只读核对签发条件，未执行实验或改文件。
A实施、质量、伴学和报告完成即停；本讨论对话已按下节证据验收A，可在有界授权内签发B。

## Bounded Unit A / Accepted — 2026-10-20

[A合同](../tasks/codex/20261020-04-01_resource-dag-pricing.md)实现提交
be03540db4f966a6c98f71e41d9025b08ddd7555：组合现有图，按完整(node,整数资源tuple)
冷DP，不做跨资源支配或缓存。状态/转移预算分别诊断，非成功清空候选；原始列、
路径及资源独立重构。资源整数精确，目标保持既有浮点参考保护和局限。

新增72项unit及1152项独立DFS/Fraction核验，共1224项；全量5299通过(15.87s)，
Ruff和结构通过；[L0009](../learning/lessons/L0009-resource-dag-pricing/README.md)
按实现哈希核对单双资源完整程序和八道练习解答。详见[A报告](../tasks/reports/20261020-04-01_resource-dag-pricing_report.md)。

讨论对话在文档提交84e126c14b4297d3493b8b183015ad235369cc9a上独立运行完整质量检查：
5299 passed in15.54s，Ruff/结构通过；16个交付路径符合合同，模块SHA256保持
B2E31D04EA2716F67AB094D6FFAA74225697E2E54E13295B704CF55B6AC3C91C。
L0009十节、八道稳定编号练习及完整正文程序已核对；伪多项式结论明确要求资源维数固定。
另以5层双平行弧的32路径、8资源上限、4对偶、3表示作96次独立Fraction补查，
72最优/24无路，1032状态/1776转移；独立前缀状态计数和全路径最优值一致。
该补查保存在忽略目录outputs/goal_A_parallel_review.py，不混入1224项新增测试。
理论和证据服务只读复核均无必须先修项，没有运行实验或写文件；主线程据实际证据裁决。
两治理文件哈希保持，未push；不可变A合同既有EOF空行记为格式债，不改历史合同。

A在声明的非负整数可加子类通过本轮首次验收，无需修订合同。B资源CG已按下节签发，
C应用门槛、条件D机制及E完整成本仍未完成；没有加速或创新结论。最多五项的整体预算及
C未通过即停规则保持；不把一次工程交付替代原研究义务。两治理文件哈希不变，不push。

## Bounded Unit B / Accepted — 2026-10-20

[B合同](../tasks/codex/20261020-05-01_resource-dag-cg.md)仅补原4的单凸性连续资源路径参考CG。
签发前main=414638a、cached 0/28；授权覆盖已知本地状态及签发提交，不push。
TT05/RR01、L0010已扫描可用；既有普通CG/A/RMP/LP源码保持不变。
新入口组合已有CG问题与同一graph对象的资源问题；全部seed求解前核资源，
每轮fresh资源冷定价；预算/无路/数值定价失败不能发布界或冒充正常终止。
固定72模型三模式共216次独立原图DFS/Fraction当前列集及全域顶点核验，
另加有限故障/预算/warm接线例，交付L0010。理论与证据服务只读预审无方向性阻断，
未运行实验或写文件；其参数前验、失败空字段和独立资源重构要求已在合同固定。
实现6858a736568a6d502271acf39d29f855def65b93；66项unit及216项独立DFS/Fraction
顶点核验均通过，新增282项，全量5581项(17.29s)、Ruff/结构通过。
三模式各72调用/116轮；opt-in公开入口116次、内部cold72/warm44/fallback0。
真实Phase II及允许的内部回退另有有限接线核验；不构成性能结论。
[L0010](../learning/lessons/L0010-resource-dag-cg/README.md)按真实实现核对公开API程序与八题，
[报告](../tasks/reports/20261020-05-01_resource-dag-cg_report.md)记录范围、失败及Git证据。
文档/教学/报告提交a9a9f672cbc0d77c3e9f799dca8b4ff51e7789cd。
讨论对话独立运行check_quality：5581 passed in17.92s，Ruff/结构通过；
16交付路径符合合同，旧CG/A/RMP/LP不变，模块哈希7452ABB0803688FD884BCAD7A52C21C0E8AA996A51C58FBB7C0EEBC64711FA22。
L0010十节/八题核对，完整正文程序原样运行通过；正文哈希及三模式结果见本轮停止记录。
理论与证据服务只读复核均无必须先修项，未运行或改文件；B首次交付验收通过，无需RR02。

## C Readiness / Pre-issuance HOLD — 2026-10-20

最终裁决：C_READINESS_HOLD — pre-issuance evidence infrastructure not ready。
C实验合同未签发，核心CG/定价运行0；D/E未签发。本轮已到固定计划的预设停止点。
三实例R101-25/R102-25/R103-25按SINTEF标准前25客户定义完成来源预检，
原始/派生哈希已版本化记录于[本轮验收与停止记录](../docs/bounded_goal_outcome_20261020.md)。
输入身份不等于完整实验合同冻结；模型/数值/初始化/列管理/基线仍缺明确可执行合同。
应用冷精确定价/真实root-CG轨迹未就绪，阻断C可靠运行；强冷/同域直接动态对照未就绪，
阻断GO及E公平比较。外部有限适配器是否可用仍未决，未复现构建或适配，不能据本地缺失推断外部不存在。
红队只读复核支持本轮停线并要求上述限定；未运行实验或写文件，不作应用否证。
25客户派生范围、未取整时间的完整状态/数值问题及fleet<=25的冗余性均如实保留。
原5未通过、原6/7未启动；VRPTW局部性假设和原研究主题保持开放。
未来前置能力/平台核验如需新增工作，先修订有限清单并获相应授权；当前不自动签发或转其他应用。

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
| CG数值界一致性 | 15b403b；保留有符号发布差，追加消去c0的objective_gap与固定32ULP局部判据 | [修正报告](../tasks/reports/20261019-05-01_cg-bound-consistency_report.md)、L0004 v0.2.0；已通过讨论对话审查 |
| DAG初始可行性恢复 | 02aed7d；单位人工违背量、全域零成本定价和无人工原始行复核 | [恢复报告](../tasks/reports/20261019-06-01_dag-feasibility_report.md)、[L0005](../learning/lessons/L0005-cg-feasibility/README.md)；已通过讨论对话审查 |
| LP无界终止核验 | c460aa7；完整原始点/方向逐项Fraction核验，Phase-I伪无界转数值矛盾 | [第7步报告](../tasks/reports/20261020-01-01_lp-unbounded-check_report.md)、[L0006](../learning/lessons/L0006-lp-unboundedness/README.md)；已通过讨论对话审查 |
| RMP显式基复用 | 90b377f；全行非人工语义快照、原始点门控、Phase II与单次cold回退 | [第8步报告](../tasks/reports/20261020-02-01_rmp-reoptimization_report.md)、[L0007](../learning/lessons/L0007-rmp-reoptimization/README.md)；已通过讨论对话独立审查 |
| CG显式消费重优化 | f4cc36e；严格bool开关、一次公开RMP调用、同轮最终MIN result与冻结诊断 | [第9步报告](../tasks/reports/20261020-03-01_cg-reoptimization_report.md)、[L0008](../learning/lessons/L0008-cg-reoptimization/README.md)；已通过讨论对话独立审查 |
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
第2步签发时曾记录近相关等式误报UNBOUNDED的既有数值债，范围和反例保留在
[第2步合同](../tasks/codex/20261019-02-01_restricted-master.md)；第7步现已为直接LP无界出口加入原始候选保护，结果见下文。

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

第4步已验收并推送，其旧判据下的保守诊断和历史证据保留。
第5步已按[数值界一致性合同](../tasks/codex/20261019-05-01_cg-bound-consistency.md)完成修正：
保留P/D/rho/L和有符号numerical_gap，从原始乘积消去c0计算objective_gap，
以固定32ULP的roundoff_allowance处理微小负g；正向差距/rho阈值与原始核验未放松。
实际先重现旧版391/41及自然反例，再运行新版432族全部正常停止，646轮逐轮独立
Fraction解析/原始数据/精确平移下界核对通过。113个末轮保留微小负g并符合局部判据。
另有20次真实常数平移、局部边界和实质正负冲突保护，原40组完整列LP对照保留通过。
472项新增检查、932项针对性与全量2331项测试、Ruff通过；L0004 v0.2.0的两个完整程序、
六题和真实修正基线15b403b核对完成，见[修正报告](../tasks/reports/20261019-05-01_cg-bound-consistency_report.md)。
签发experiment_auditor的只读证据设计建议已落实，未计作本轮实测或严格误差证明。
2026-10-19，silo-solver-1010在f0cc01a上验收第5步：独立重跑全量2331项测试
（9.05s）、Ruff、目录及差异检查，均通过；12个交付文件符合合同，禁区无改动。
L0004 v0.2.0两个完整程序重跑通过，十节、六题/解答及真实15b403b基线核对通过。
额外用不同参数的共享DAG族检查：alpha/beta各取1/8、3/8、5/8、7/8，成本矩阵为
(-2,5,1,-3)、(7/4,-9/4,7/2,-1/2)、(6,2,-4,1)、(-7,-7,-1,-1)，R/C基项为3/8、-5/8，
基成本-3/4，矩阵索引从0起，c0偶数索引为-7、奇数索引为5；首弧成本(i+1)/4、末弧(1-j)/8。
64模型各配两个端点seed、原/反序和两个后端，共512次，全部TOLERANCE_REACHED。
736轮独立Fraction端点真值、原始行可行性及返回乘数平移下界核对通过；
89轮保留微小负objective_gap且满足局部预算，末轮精确原始目标最大误差约1.50e-15。
上述512为本轮补查，未混入2331个版本化测试条目或开发报告的432族计数。
独立experiment_auditor只读确认合同证据覆盖和独立性，无必须修正项；服务未跑实验、
未写文件，也未把此前证据设计意见计作数学证明。

第6步已按[合同](../tasks/codex/20261019-06-01_dag-feasibility.md)实现独立DAG可行性恢复，
从非空合法路径seed出发允许耦合行不可行，以单位总违背量和全域零成本定价补真实列。
F小后移除人工变量，另建零目标完整原始行RMP核验；成功保留原图/原成本/c0交回seed问题。
恢复与原目标CG通过调用者两次显式调用连接，旧CG依然要求可行seed；支持域保持连续conv=1普通DAG。
648组解析回归得到200成功/448数值正违背下界，辅助LP1144次、原始复核200次；
200次成功均显式交旧CG并对照完整原目标LP。三例双后端核对恢复后原目标9、正违背1及退化1->1->0。
715项新增检查、1647项针对性及全量3046项测试与Ruff通过，L0005 v0.1.0完整程序/五题/真实代码基线核对。
数值边界单列保留：10个辅助末轮的人工rc精确越界2^-52，其中8个形式平移目标超解析值2^-54。
精确对偶条件成立的定价轮严格Fraction下界通过，其余按既有1e-9核验的浮点证据解释，未投影乘数。
人工pi_r=2/rc=-1伪下界和小F却原始行不可行等反例均被拒绝，详见[恢复报告](../tasks/reports/20261019-06-01_dag-feasibility_report.md)。
签发前公开API桥接及两项只读复核未计作新恢复器实测；成熟度限教学与研究基线，不发布严格Farkas结论。
2026-10-19，silo-solver-1010在70293f9验收第6步：独立重跑3046项测试（10.75s）、
Ruff、目录及差异检查通过；14个交付文件均在合同范围，旧CG/RMP/定价/LP与旧测试无改动。
L0005完整程序双后端重跑，十节、五题/解答和真实02aed7d实现基线核对通过。
另构造非矩形三角形路径域(0,0)/(2,0)/(0,2)，R/C方向各取LE/GE/EQ，
RHS对依次(1/2,1/2)、(3/2,3/2)、(5/2,1/2)、(-1/2,3/2)，共36模型。
按方向对与RHS对的乘积顺序编号m从0起，奇m增加Q=R-C行，方向按m模3选LE/GE/EQ，
RHS为m模4等于1时1/2、否则-1/2。R/C/Q基项为3/8、-1/8、1/4，RHS同移。
偶m成本(-3/2,5/4,-1/4)、c0=-7，奇m成本(2,-1,3)、c0=11；图基成本3/4。
三条路径各两弧，首弧成本i/8、末弧补足，行增量各分一半到两弧；三个单路径seed、
原/反节点弧行序、双后端，共432次。Fraction枚举lambda单纯形与残差零超平面的
分区顶点，独立最小化总违背与原目标；204次恢复成功且原目标交接通过，228次数值正界，
零诊断失败，两个后端各102/114。676个定价轮独立复算完整域约化成本、平移目标与真实/人工对偶条件；
精确条件成立时严格下界通过，36轮精确对偶条件存在浮点越界，形式界最多超精确值
1.11e-16，单列保留；204个原目标末值与Fraction真值误差均为0。
该432次是本轮补查，不混入3046个版本化测试或开发报告648族。复现脚本仅留在被忽略的
outputs/step6_triangle_review.py，本摘要保留模型定义，未将临时产物纳入Git。
theory_architect与experiment_auditor分别只读复核实现数学一致性和证据独立性，均无必须先修项；
服务未执行实验或修改文件，意见不重复计作实测。以上为第6步验收记录；第7步本轮另行签发。

总体成熟度为可学习、可核验的小规模方法原型；连续普通DAG列生成已有从合法seed恢复到
原目标优化的参考闭环。ROADMAP的Phase 0–8完成仅对应各自保守范围，阶段数量不代表
通用求解能力完成比例。当前能力与主要剩余工作如下：

| 组件 | 已验证能力 | 主要剩余工作 |
|---|---|---|
| 建模、LP与核验 | 简单线性模型、Tableau/Revised、原始行最优性核验、无界候选点/方向精确标量核验、保守预处理 | 一般变量界、对偶单纯形、其余数值状态可靠性与稀疏线性代数待完善 |
| DAG列生成 | MIN RMP及CG显式基复用、全域普通DAG定价、退化控制、浮点差距门控、独立初始恢复 | 资源约束定价基线、增量定价、原研究适用性与完整成本证据、整数与分支定价 |
| MIP | 支持域内小型MAX分支定界与LP松弛 | 实际割加入、启发式、强分支与规模验证 |
| 割与其他分解 | 被动接口、记录及toy Benders/CG | 通用Benders与通用ColumnGenerationSolver仍为NOT_SOLVED入口，未形成通用框架 |
| 随机/鲁棒 | 有限场景记录和小型目标/RHS变换、区间RHS最坏情况变换 | 场景变量复制、非前瞻约束、更一般不确定性及求解集成 |
| 运行与学习 | 小实例回归、任务追溯、L0001–L0008 | 锁定干净重建环境、成体系规模基准；native保持延期 |

第7步已实现并完成开发验证：两个原生LP的Phase-II无界出口使用完整原Model的实际
有限候选点/方向Fraction核验；未通过返回NUMERICAL_ISSUE。原反例
x-(1+5e-10)z=1e10、x-z=1e10、maxz现在双后端均数值诊断；其精确解仍为z=0，
诊断不计作已求得最优。Phase-I内部伪无界转数值矛盾，正常枢轴与全局容差保持原样。
240核心族从96最优/144无界改为96最优/48真无界/96数值诊断；32对照为4最优/
12真无界/4不可行/12数值诊断。共272次保留100旧最优和60真无界，108误报全部拒绝。
每个公开无界结果的实际候选均由独立原项Fraction oracle核对。核心大epsilon保留80最优，
小epsilon保留16最优；行/变量排列和双后端均覆盖。新增398项检查，全量3444项与Ruff通过；
L0006十节、六题/解答、16次双后端完整程序与标量核对通过，代码基线c460aa7。
2026-10-20，silo-solver-1010在445da97验收第7步：独立重跑3444项测试（28.28s）、
Ruff与目录检查通过；16个交付文件严格符合合同，其他生产模块/旧测试/旧合同报告无改动。
L0006完整程序16次双后端及解答标量程序重跑通过，十节、六题/答案、真实c460aa7基线、
UTF-8/围栏/公式核对通过；实现提交之后代码/测试没有变化。
独立theory_architect只读复核点/方向充分条件、候选坐标与全出口门控；
experiment_auditor只读复核272族、旧正常路径保留、实际候选及独立oracle，均无必须先修项。
两服务未运行实验或修改文件，意见不重复计作实测；签发前意见也没有冒充验收。

本轮额外构造三变量混合行族：B取1/4、3/2，C取1/2、2，q取1/8、8；
行依次为-2q*x+q*z=-2qB、4y-z=4C、x-2z<=B、y+z>=C、-4q*x+2q*z=-4qB，
目标max z+c0，B=1/4时c0=-7，否则11。四种情形分别保持原域、加2^-36*z<=1、
加2^-16*z<=1、加z<=-1。每例原/反行序、x/y/z或z/y/x变量序、两个后端，
共256次。解析真值：原域点(B,C,0)与方向(1/2,1/4,1)给真无界；正cap给精确
最优c0+1/epsilon；负cap与z>=0矛盾。实际为64最优、64不可行、64有限数值诊断，
64个真无界中56次UNBOUNDED、8次NUMERICAL_ISSUE（均Revised）。
56个实际发布方向由独立Fraction原项核验通过；72个拒绝候选均独立验证确有原始违背。
例如B=1/4、C=1/2、q=1/8、原序时Revised实际点为(.25,.5,0)，方向约
(.3999999999999999,.2,.8)，第一原等式的精确方向残差为2^-55，因此保守拒绝。
初次补查把全部真无界期待为UNBOUNDED，在第2次运行发现该已声明边界；随后保持
所有数据/容差不变，按充分条件记录识别率，并独立检查成功和拒绝的实际候选。
上述256为完整补查，另有初次2次和代表例1次，不混入3444个版本化测试或272合同族。
临时复现脚本仅保留在被忽略的outputs/step7_affine_ray_review.py，未纳入Git。
第7步可验收；保守拒绝说明仍需区分结论可信度、候选构造质量和求解成功率。

数值边界仍明确：真实无界3*x=1、maxz的浮点点无法精确满足原行，会保守数值拒绝。
本检查仅覆盖两个原生LP的直接无界出口；presolve独立终态、其他后端、MIP整数可行性
和一般数值状态各保留其边界。没有通用精确求解、任意尺度或工业性能保证。
第8步实现、开发验证与L0007经silo-solver-1010独立审查通过，代码90b377f。新增显式LP reoptimize
及RMP solve_reoptimized，普通solve仍完整cold并清空新缓存。全行非人工最终最优基
经原始核验/元数据核验发快照；按语义键映射移位列，fresh人工列去除但不删原行，
raw点核验后实际进入Phase II。旧删行来源无资格；失败最多cold一次，最终资格决定缓存。
本轮改动前另跑1152双后端cold及576全行详情，仅作支持域基线。新144历史/576调用
实测144cold/432warm/0回退，均最优；cold Phase I144次/288枢轴、Phase II144次/0枢轴，
warm Phase I0次、Phase II432次/120枢轴，其中336次零枢轴warm仍实际调用Phase II。
传入基/新增列非基身份由runner观察核对；原项Fraction真值及1152独立双后端cold对照通过。
A/B/C与两独立EQ的公开路径、真实零步长退化、增列恢复行独立和故障/缓存生命周期通过。
新增225项检查（144历史、58 LP单元、23 RMP单元），targeted881项，全量3669项与Ruff通过。
L0007十节、六题/解答、11次公开调用完整程序与解析程序按真实90b377f基线核对。
本轮独立复跑check_quality：3669 passed in16.76s，Ruff与结构检查通过；重新观察144族，
上述cold/warm/Phase-I/II/枢轴及336次零枢轴计数均一致。原Revised的27个既有函数/方法
AST不变；7个代码/测试路径与90b377f逐字一致，19个实现/文档路径均属合同范围，旧合同未改。
正文11次公开调用及解答Fraction程序原样运行通过。E06的25/4由p0=1/4、p2=3/4达到；
结合mean<=3/2给成本下界-3/4，核对了该最优值，未因把可行值27/4误作最优而修改正确教材。
另作独立二维资源补查：conv与两个均值区间共5行，资源点(u,v)取{0,1,2}²，seed=(1,1)，
再逐个加入其余8列。区间取[1/2,3/2]或[1/4,7/4]；成本2u-3v+uv、常数7，或
(3u-2v) mod5-2、常数-3；4加列序×3行序×全行正反表示，共96历史，每历史10轮。
960次opt-in实测96初始cold、864warm、0回退，warm共300枢轴；1920次双后端独立cold
对照及Fraction至多3正列顶点真值、原始MIN证据全部通过。该补查与225项/144合同族分开，
不作一般模型或规模保证。实际临时脚本保留于被忽略的outputs/step8_two_resource_review.py。
理论与证据服务仅只读复核，不执行实验、不改文件，其意见不重复计为运行证据；最终判断由讨论对话负责。
第8–9步均已验收；第9步CG接入及L0008通过本轮讨论对话独立审查，本轮不推送。
每轮仍全矩阵重建与解基，无LU缓存，当前没有加速/工业性能主张。
第9步代码f4cc36e：末尾严格bool reoptimize_rmp=False，True仅消费一次公开RMP结果，
迭代末尾保存实际冻结outcome，四个成功/失败分支同轮接线；CG不加cold、不访问基缓存。
新288图/864次主族、60图/180次大常数CG全部正常停止，696次完整域双cold参考另计。
True主族443轮=323cold/120warm，大常数100轮=90cold/10warm，均零回退；观察实际
公开入口、native cold、Phase I/II与传入基，独立当前registry顶点/全域端点和数值字段核对。
A/B三模式6次CG通过；A首个warm实际零步长，B为cold/cold/warm。恢复后经济CG首轮fresh cold。
接受warm与warm失败/cold成功分别交叉后续pricing/candidate/gap失败；双失败、发布位置、
预算、输入拒绝、异常后owner隔离与只读历史通过。新增406项，targeted1287项、全量4075项及Ruff通过。
L0008十节/六题/完整程序按真实f4cc36e基线核对；有限DAG链路保持原目标中的限定位，不声明创新/加速。
本轮独立复跑check_quality：4075 passed in15.71s，Ruff及结构通过；正文3次经济CG/8轮
与解答标量程序原样运行通过。原CG的11个辅助函数AST不变，4个代码/测试路径与f4cc36e
逐字相同，15路径符合合同，旧合同未改；用户治理文件哈希保持。
另作5原行/9条共享三弧路径的3×3二维资源网格补查：conv=1、两个均值区间，seed=(1,1)。
区间[1/2,3/2]或[1/4,7/4]；成本2u-3v+uv/c0=7或(3u-2v) mod5-2/c0=-3；
4弧序×3行序×非conv正反表示，共96图表示，各三模式288次CG、每模式336轮。
True实测96cold/240warm/0回退、warm共240枢轴；逐轮独立原图DFS/Fraction当前列集及
完整域顶点、MIN原始/对偶/rc/互补、全域price、P/D/L/g/eta、registry和真实Phase II通过。
该补查不混入406项或864/180版本化运行，也不外推一般规模稳健性；实际临时脚本保留在
被忽略的outputs/step9_cg_expanded_review.py。理论及证据服务只读复核未发现必须先修项，
没有运行或改文件，其意见不重复计为实验。开发对话继续停在第9步，后续待另行批准。
签发前临时桥接已跑288图/864次三模式CG，区间72图的True桥接120轮为72cold/48warm，
方形216图的True桥接323轮为251cold/72warm，均零回退且最终解析目标一致。
另60个大常数变体/180次CG及两机制例各三模式通过；仅证明既有接口支持域，
当时没有正式开关或逐轮字段，桥接不计为新实现通过；上述新验证来自本轮正式入口与版本化测试。
第9步验收时曾建议先做冷热CG工作量/耗时对照；2026-10-20全局复查撤回其自动优先级，
改按本页Original Plan / Global Review记录回到原研究适用性门槛。冷热测量可作辅助证据，
不能代替资源约束定价的瓶颈、结构与完整维护成本判断；后续任务仍未签发或执行。
候选方向舍入的识别率问题单独保留，不把本步数值诊断算作求得最优或完整无界识别。
具体应用与实现任务应对照既定增量精确定价主线及未答义务，每项另行原子合同。
建议GPT-6 Sol/high用于跨层失败历史与等价性检查；推荐不代表实际切换，Phase门控保持。
资源约束、增量研究和性能主张仍待后续任务；native、Phase 9 closure及
Phase 10保持原有门控。第5步明确修订第4步的严格负gap判据，旧合同与历史证据保留；
旧CG数值规则仍为15b403b，独立恢复器基线02aed7d；32ULP保留工程局部尺度限制，没有LP误差严格上界。

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
