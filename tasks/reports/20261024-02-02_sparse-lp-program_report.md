# 稀疏LP整体目标集中恢复与续接执行报告

当前状态（2026-10-25）：SP1/SP2及旧源SP3已GO；SP4修复后的当前源固定LP组、MIP/CG及历史组通过。
当前源码warm第三轮75/80，五次BOUND02 cold触60秒保护；RR04工具门、最后完整质量与原工件8环境复验通过，第4轮warm待启动，整体八项未完成。
当前合同：[20261024-02-02](../codex/20261024-02-02_sparse-lp-program.md)，签发78cc75de0197c58b95bd80b4d313c3306ab39f94。
原目标：[总体规划](../phases/sparse_lp_reoptimization_program_20261024.md)第11节八项，
[原实施计划](../phases/sparse_lp_implementation_20261024.md)、
[集中恢复计划](../phases/sparse_lp_recovery_20261025.md)及[审查](../../docs/sparse_execution_review_20261025.md)。
七轮历史见[01报告](20261024-02-01_sparse-lp-program_report.md)，原报告与失败证据保留。

## 1. 启动与直接授权

人类在silo-solver-1010直接要求：“审查这次开发实施过程的情况，找出其中问题原因并制定下一步推进计划，然后交付‘silo-solver开发’去执行修复和继续完成目标任务。”
已从源对话实际userMessage核实，turn01a1704a-56a6-7811-8bf6-b95fe87ab18e，
userMessage01a1704d-0554-7643-8b13-08780b9c5a83；转交消息要求立即按RR02执行。
RR02合同SHA256为2e11bc6f1dfe08214693fd64bbfc17ba7ff7164207944042e59189ad3cdfefac。

沿用thread01a15208-bea9-7030-aacc-95d785e8fa58及原完整Goal；get_goal启动实核状态仍blocked。
Goal工具不提供active设置，本次明确授权允许执行本包；不创建替代Goal、不重设目标或预算。
先前7/7停止保持历史事实，本次RR02是新的窄续接授权；后续阻断审计从本次重新计算。

启动HEAD78cc75d、分支codex/sparse-lp-reoptimization；生产源仍fc33014575b72b7d85a6751c975dd25ee841e449。
cached origin/main...HEAD=0/73，未查即时远端，无push/发布；仅两项已知治理差异，原哈希保护并排除暂存。
原manifest/sources/oracles/dense_baseline、旧984证据及账本保持；启动实账另存原ledger追加事件。
推荐GPT-6 Sol/high，不声称已切换模型；本报告为当前唯一总报告，01保留历史。

## 2. 恢复包与预算

一套集中SP2恢复包，最多3新增诊断、每批60秒且包含在原20批；最多2完整48/24/6联合验收，
初包及至多一次有新证据修订。内部补丁与组件修复不另算验收轮，不逐补丁再请求授权。
全部沿原SP2剩余3600秒桶和全局28800秒账本，不跨桶；整轮按1500秒及evaluate/复核余量预约。
仅证据和独立数学门支持后修订比值/有限恢复/稀疏重新平衡及必要的定价控制；无扰动、无外部优化器。
每进入列/同基最多2完整私有候选；当前B/B转置、完整state发布与强制残差失信保护保持。
原输入、真值、外部验收容差和八项目标保持；SP2联合GO后连续完成原SP3/SP4。

## 3. 原八项覆盖与当前未答义务

| 项 | 当前证据与状态 |
|---|---|
| 1 实现前冻结与设计 | SP1 GO，a3cff29输入、3c27324真值/基线，独立GO先于生产修改 |
| 2 端到端sparse cold | 当前算法a9f3213：48/48、24/24、12容量/12外部全过；两完整容量/Netlib额度已用满 |
| 3 LU/eta/数值与8机制 | 当前源8/8；既定pivot/eta机制通过，新增精确依赖SOURCE/MATH GO |
| 4 会话四修改与收益 | 当前源round3 75/80，HOLD；RR04已授权唯一round4（当前3/4），RR05新宿主窗口待执行；旧源结果不桥接 |
| 5 MIP/CG真实稀疏接入 | 固定12MIP/4CG全部通过；精确全池及真实分支/局部GMI/复用由结果门继续核对 |
| 6 旧行为与质量 | 737/737历史及6607全量测试、结构/Ruff通过；原984文件保护不变 |
| 7 0.3.0a1与8安装 | 原工件模块/元数据审计通过，RR04八个全新环境首轮全过，原SHA与检查器不变 |
| 8 伴学、报告、独立终验 | L0012/L0015按a9f3213及原样小例checked；最终报告及八项独立GO待取得 |

原研究A/B、C HOLD、D/E未启动、native延期及远端CI pending保持。本包不改变研究身份或完成线。

## 4. R0诊断、设计及后续实际收据

R0开始时尚未进行新的联合验收；审查136项和历史78例不计作RR02容量成功。

观察器提交f07835e，12纯逻辑测试/Ruff通过；9条准备检查共3.3788595秒，初次lint和统计边界
失败保留。准备期0公开求解/原生kernel/真实LU，36次toy、21次fake LU factory单列。
旧生产source SHA始终fd1309ca5aeb30dce75f288eabff5dc60060cf2e69f8cf007e9409800fb410ac。

| R0批次 | 总实际计账 | 角色及结果 |
|---|---:|---|
| rr02-r0-eta-01 | 26.3334261秒 | FLOW三份快照后主动prefix停止；TRANS诊断time_limit返回 |
| rr02-r0-no-updates-02 | 26.5895931秒 | 禁用更新的另一轨迹，同样仅作因果诊断；不计正式容量成功 |

两批均有58秒/1GiB OS进程树保护，原诊断次数2升至4/20，RR02使用2/3。
共4公开调用启动、2返回（两次TRANS time_limit），两次FLOW是有意prefix停止；
7069原生LU启动/返回，另12次同B独立稀疏LU和36次线性方程探针，全部计入批次成本一次。
无oracle点读取，无完整A/B稠密化；same-B探针不反馈选择，no-updates是不同轨迹而非同B配对。

状态保存采用“每固定案例、每模式/批次最多3份”的有界观测解释：2例×2模式×3=12份，
实际数量与完整清单已公开登记，不称12个独立实例。原文未明确跨模式累计口径；本解释由主执行者
记录并承担，数学服务不追认权限。为保持观测有界，后续不追加状态导出，保留全部原文件供终验。

eta轨迹FLOW第72步、TRANS第47步均见全部严格最小比值主元unsafe，但Harris窗口各有一个
稳定且真实坐标预测通过的候选；窗口分别0.11870105和0.12565544。对应same-B直接LU残差约1e−16，
TRANS方向与原解完全相同。禁用eta轨迹在FLOW106步/TRANS59步仍有同类缺口，分别有3/1候选。
这说明该选择器缺口真实可达，eta累积不是该缺陷类的必要条件；未证明两CAP唯一根因或新基必过。
原始状态、全部阻塞行、真实rho/选择比值/候选预测、B/BT/方向残差及所有SHA见
reviews/rr02_r0_evidence.json，SHA6ae3b2e470a7196b121a480c6ed47e5c5a76f349e6458b8c1b76211e28a01808。

[稳定性契约](../../docs/sparse_primal_stability_contract.md)已获独立theory_architect数学GO。
首包仅有保护两遍出基选择及统一两次private trial预算；保持Devex/sticky Bland，无新PhaseI/dual/缩放恢复。
预算包含B′和可选same-B，合法路径B′+B′或same-B+B′；generation重启不补额，实际开始才计一次。
direction有限且P空先走ray；所有正blocker参与窗口，+Infinity非绑定而非删行；非有限数据数值失败。
真实rho用于代数与观测，max(0,rho)仅用于进展/退化。private frame加入策略版本。
此数学GO不代替源码门或48/24/6联合SP2验收。启动实账SP2=635.2621407秒；R0闭合时692.7192160秒。

## 5. R1集中首包与组件核验

新增纯NumPy的lp/sparse_ratio.py，所有d>0进入首遍，次遍按稳定pivot及语义键排序；
完整私有trial实际构造次数统一计额，B′与same-B合计最多2、跨generation重启不补额。
same-B仅用于零预测可行候选的前选回退；B′失败优先另一离基行，不再candidate_validation自动刷新。
代数与pivot观测使用真实rho，进展/退化才max(0,rho)；新策略版本加入私有frame，dual/cleanup不改。

首次lint有一项import排序失败，保留并修正。首轮组件123通过/17失败，其中旧unsafe blocker
回归暴露全局tau窗口的实质错误最优：1e-8*x<=0及1e4*x<=1e4的精确最优为0，却返回x=1。
该旧反例保持原断言，不能视为过时策略测试；另5项选择/拒绝保护也保持。
独立数学服务再次审核后，将内部窗口收紧为
delta_i=min(原tau,max(-x_i,0)+64*eps64*(1+abs(x_i)))，用非负headroom的溢出安全公式计算。
验收容差、输入及目标未变；Gamma为固定内部工程规则，不宣称精确前向误差或全浮点最优性定理。
保存状态重算仍保留12/12稳定预测候选，0新增solver/LU/export，见reviews/rr02_r1_window_refinement.json。

行级窗口后134通过/11失败，前述6项旧数学回归全部恢复通过。余11项经独立只读核对均为
已取消的candidate-validation刷新、可选离基行数或对应成本计数假设；保留零发布、回滚、
B/BT重算、deadline/resource、拒绝历史及原空间错误最优保护，只按实际新策略修正计数。
最后144组件通过，Ruff clean；成功普通pivot仍1初始LU/6次三角求解，内部代次重启不增加trial额度。
所有失败日志和每次实际kernel/候选/LU调用分别保留在rr02_r1_*_receipt及原账本；该组件门先于联合78例。

## 6. RR02首轮SP2联合验收与独立GO

生产提交4ea42647f228d65b63aa74ee13969060e27d84a7，完整source SHA
1de3f1d307dd4f8286862bcce92d954725bebf924c32ec8768a71bd8c40018d7。
公开LP/根集成172项通过（含LP315/315、root118/118，另两NumPy隔离探针），
固定tiny48/48、pressure24/24、smoke6/6全部通过；strict SP2 evaluate exit0。
实际root78启动/78完成，LP77/77，PRESS-LIMIT-03按预期在LP前返回resource_limit。

| 固定容量例 | 原始目标 | pivot | 求解秒 | 峰值RSS字节 | 原空间核验 |
|---|---:|---:|---:|---:|---|
| CAP-FLOW-01 | -349.625=-2797/8 | 4216 | 7.429259 | 121114624 | optimal，primal/dual/KKT通过 |
| CAP-TRANS-01 | -349.625=-2797/8 | 14697 | 30.410889 | 218984448 | optimal，primal/dual/KKT通过 |

两例guard均null，低于原120秒/1GiB；全候选trial峰值均1，dense_model_allocations均0。
TRANS中间maximum_basis_residual约0.095504保留为拒绝/恢复过程峰值，不把最终KKT通过
扩张为一般浮点LP数值稳定性结论。独立原payload复算FLOW的primal/stationarity/互补残差
约1.44e-15/1.75e-15/1.92e-15、P-D约1.71e-13；TRANS约9.97e-16/3.74e-16/1.87e-16、1.14e-13。

原联合包reviews/rr02_sp2_joint_01.json保留其当时pending字段，SHA
7ae433416c4ae54bf96a1cdb576d7cd2a3b7eef5be68f7fe4209b0289c2f0ce2。
独立red_team_reviewer逐例核对78组request/result/input SHA，错绑0/78，给出SP2 GO；
回传及当前门分别保存在reviews/rr02_sp2_independent_return.txt和rr02_sp2_independent_go.json，
原账本已追加SP2 stage_gate GO。审查0新求解/测试/文件写入，无需消耗第二次联合轮。
RR02联合轮1/2、新增诊断2/3（原总4/20）；当前计账SP2=785.8677913/3600秒，
SP1=368.5422803、SP4=4.4615295，总1158.8716011/28800秒，SP3尚未启动。
原八项保持，依RR02直接授权连续进入8机制与8轨迹×五次冷/热验证，再完成SP4。

## 7. SP3初验与第一次修订

8机制首轮7/8通过，UPDATE-05在493 primal+1cleanup后返回numerical_failure，原始组
51558aa2-6ff6-4c2d-8999-e0023d73252c保留。实际终止为Phase-I cleanup lost a current optimal state，
旧last_entering_rejection人工列记录属于Phase I遗留，不能当作当前失败根因。
一次58秒/1GiB保护下的标量诊断耗1.6037797秒，1公开求解/28真实LU，无新增线性探针，
无完整矩阵或状态导出；原诊断总5/20，SP3桶承担。清理前后人工目标约0、基本值可行，
一次合法零步长换基却使该基的Phase-I reduced cost变正；原代码把这项非必要中间条件当作失败。

独立theory_architect确认数学缺口：Phase I目标-sum(a)的可行上界为0，清理只需逐步保证
当前B同代、数值有限、原primal门及正部人工量sum(max(a,0))<=原primal_tolerance。
中间基可对偶不可行；此时不能签发Farkas。保留Phase-I优化终点的原Farkas路径。
SP3第一次修订仅替换此清理不变量，并在每次换基/删依赖行后立即检查（含末次）；
不改Harris、Devex、两次候选额度或验收容差。遗留拒绝记录补上run/phase身份。

两行精确零解反例在旧源上复现失败，另外3项故障保护先通过；修订后该反例及原数学例通过。
新增正负人工量抵消及末次清理故障检查，完整因子/比值/kernel组件和Ruff通过；
原错误最优与资源保护保持，首次组件门先于8机制复验，不预支SP3 GO。

修订7891de51312bc17c79c8b117718906e7aea14b66，source SHA
3b94e2ef1272dd153cc916a576c5d3e4537737e83f544016a955b3f3c8143f3f。
8机制复验8/8，最少64pivot、最低eta比例528/530；UPDATE-05现530pivot含12cleanup、正确optimal。
150组件及独立SOURCE/MATH GO通过，核对非交换B/BT、当前B残差、缓存隔离与warm计时；
此源码意见明确不包含正式warm收益或SP3整体GO。

### 正式warm第1/2轮

固定8轨迹×cold/warm×五重复全部80child自然执行，实际699.9385155秒。
70/80成功，10失败均为WARM-BOUND-02：五次warm在第4次修改返回original_kkt_failed，
五次cold在初始成功后的第1次修改触发原60秒保护。完整分母保留，不聚合总体收益或宣称SP3通过。
其余七条各10/10，配对中位比分别3.5422、1.7448、3.4486、3.7610、1.9448、3.7067、1.8373，
仅用于定位已完成范围，不替代八条完整门。
首轮summary为warm/round1_06596c02-a89c-454f-85f5-e3cb92a94533/summary.json，SHA
abcd669cbed25cd4ec629a9b064be9af03f1dfe51fbce8aaf36947cb3ebfc66d；
归档reviews/sp3_warm_round1_failure.json。

首版driver在assert前未保存失败的公开返回，只有成功状态与失败日志；此观测缺口如实保留。
已补异常分支failed_return.json及实际started/completed计数，不改求解、truth、时序或性能门；
同时终验文档引用加入RR02当前报告，原01报告继续作为历史引用。
Ruff与8项纯证据逻辑测试通过。补充诊断只重放固定失败前缀，不能替代或回填首轮真实失败。
阶段还有第2次修订及第2次正式warm额度，原时间/诊断总上限保持。

### 第二次修订的证据与实现

标量观测器先出现一次OneDrive替换锁错误（56实际LU后、下一次pre-call marker中断），
随后两次逐行包装在已通过的initial冷解上放大开销并触58秒保护；全部保留并计账。
保存各版harness后，仅修改段启用trace、LU采用单一固定计数槽，未改变数值路径。
有效warm重放34.6716702秒，5公开调用/913真实LU全部返回，0额外线性解/重构/证明/完整状态导出。
state04的x14=-1.083257012e-7；内部global ptol约3.5e-7，原下界允许约1.0e-7。
该步0pivot、generation569/eta7/B不变；B/BT残差和其余KKT均过，唯一原空间失败是变量下界。
有效cold前缀58.6656324秒在Phase II持续Bland中触保护，从未进入Farkas/ray/proof。
初始17703pivot中17450次Bland、触发均two_degenerate；修改1到6144pivot仍有真实目标进展，无重复基。

受控诊断只取消two_degenerate触发，保留真实重复基保护及全部原门。固定cold初始+20修改
21/21正确并通过冻结oracle，880真实LU，初始722pivot、各次722–912；含导入/初始/编辑/核验
33.0049849秒。该对照不计正式性能，证明开销解释被前缀否证，支持窄修定价控制。
两个独立数学门分别批准潜在dual退出时的原空间映射分量门、仅重复基触发sticky Bland。

实现新增lp/sparse_dual.py，仅在原全局负行集合为空时补查实际原空间投影；结构变量使用
col_scale与原始有限bound，slack使用row_scale及非零q的符号公式。可映射负基本量继续原dual；
无法映射或mapped-only无安全pivot返回数值失败，不发Farkas。原全局/Farkas/完整KKT保持。
两个policy token纳入frame，旧策略cache失配；pricing仅取消two_degenerate触发，保留退化统计、
真实有序语义基重复及原资源退出。Harris出基保持，不声称经典完整Bland有限终止定理。

组件初验152/155、再验158/159的失败保留：新增pure-helper offset整数数组需强制float；
原RHS编辑fixture还需同步原空间row_upper，并固定为float以避免4.25截成4。
修复这些真实数据一致性问题后159组件/Ruff通过，旧数学反例与错误最优断言保持。
新增尺度非1的lower/upper、上下侧slack非零残差符号、free split、mapped-only无Farkas、
原空间上界被全局量遮蔽后一次实际dual pivot、跨调用真实因子复用及重复基历史保护。
第二包仍待单次运输轨迹、独立源码及最后正式warm，不提前签SP3 GO。

第二包c3fea18ca45740338bdc4d2a2add828a916e804a已冻结，source SHA
be65472620c343d0a0b0e631eaddf1a9f9480cf9bb9d290c38605aa641e52a16。
159组件及独立SOURCE/MATH GO通过，无必须源码修项。随后固定运输轨迹单次warm/cold
均完成初始+20修改、各21/21正确，实际5.2952099/33.7281149秒；warm真实跨调用复用20次、
映射dual换基2次（修改04与17），原失败位置不再零步错退。该单次不计正式性能。
第3套固定8机制（初验及两次修订）8/8，最少64pivot、全部真实eta比例1.0。
证据reviews/sp3_second_preflight.json绑定源码、组件、8机制和两个单次检查。
最后正式warm第2/2轮已启动，完整五重复及原80分母保持；源码继续冻结。

## 8. SP3正式通过与SP4续接

正式第二轮431.3803621秒，80/80子进程、1600修改状态及80初始全部正确，
strict SP3 evaluate exit0（12.8625319秒）。八轨迹修改段配对中位比分别为
RHS01 3.5303、RHS02 1.7424、BOUND01 3.3790、BOUND02 8.9605、
ROW01 3.7442、ROW02 1.9467、COL01 3.5727、COL02 1.7920；总体中位3.4546658467、8/8>=1。
包含导入及初始解的八比值分别约2.3150、1.6145、2.4021、6.2504、2.4154、1.7690、2.3689、1.6566。
主性能比定义为20次完整修改段，原60秒保护覆盖整个child。

独立red_team_reviewer直接绑定401文件、80 request/result及1680原输入，错绑0；
不导入solver/checker，独立重算1680 objective/primal/stationarity/互补，与原始checks一致。
最大child外层33.6467839秒、packet含初始33.4420122秒、保守进程树RSS111325184字节；
最大scaled primal 9.8036328767e-8，原门1e-7；该窄裕度保留，不宣称普遍数值稳定性。
最大stationarity 3.6438e-10、互补5.5404e-15，cold/warm目标最大差1.0711e-9。
实际factor跨调用复用600次，来自RHS/BOUND/COL六轨迹；ROW两轨迹每次行增维重构，
其语义warm start成立，不能称为沿用原数值factor。正式BOUND warm五重复覆盖10次mapped dual pivot。

联合门SP3 GO，无必须修项及补跑；reviews/sp3_independent_go.json登记回传事实和SHA。
独立只读计算命令约21.234秒已补记SP3，无新solver/测试/实验。原账本追加SP3 stage_gate GO。
截至此门SP1/2/3/4为368.5422803/785.8677913/1490.0927953/4.4615295秒，总2648.9643964。
L0015保存Python小例原样通过：2公开LP、2真实LU及独立2x2转置解，0.5480907秒已记SP3；
checked仅表示教学内容实际核对。原始小例SHA与更新后正文身份另存learning_checked_identity.json。
依RR02立即接续SP4；当前最终tiny/pressure及12容量/12外部、上层、历史/质量、0.3/8安装仍待验。

## 9. SP4初验与依赖证明修订

同一be654源的最终tiny48/48（27.8895517秒）、pressure24/24（13.7436475秒）、
capacity12/12（46.3194287秒）通过。完整Netlib首轮11/12（15.2864274秒），
DEGEN2在1235pivot后以Unproved near-dependent row in artificial cleanup保守失败，
976行基的旧精确B工作区预检必超65536格；无错误最优或Farkas，原失败结果保留。
其余11个外部例均optimal且通过原空间与冻结目标检查。

独立theory_architect批准一个窄稀疏依赖证明：复用已有cleanup BTRAN，行尺度恢复后用
固定分母上限1000000提出权重，流式Fraction精确核验所有非人工列（含slack）及RHS，
其他基本人工支持必须零，目标人工单位列支持权重为1。候选近似从不授权删行。
新路径只保留q长权重与n长累计量，workspace=2q+2n+32；原65536格/2m操作/4096bit/时限不变。
旧小基fallback共用剩余ProofBudget。删行后的因子与完整cleanup状态先暂存核验，
成功后才提交axis/basis/row_map；数值minor失败不登记已删行，不签Farkas。

174组件和Ruff通过；包含976行1986格证明、65536格实际可用/下一档预分配拒绝、
负RHS/非单位尺度/offset/fixed/free/reflected、slack伪相关拒绝、2^-39非零反例保持、
错误权重拒绝以及reduced-factor失败不发布行删除。最初3次lint修正记录保留，未运行失败数值组。
本修订仍待DEGEN2单次、独立源码及完整最终矩阵。新source使旧SP3全源指纹失配；
原warm2/2已满，禁止未授权第三轮或桥接旧算法结果。先完成已授权修复及可核对结果，
再就唯一必须追加的正式重验提交具体额度，整体Goal保持未完成。

## 10. SP4当前源码完整固定复验

算法提交a9f321374d4ca4758aa63d178f224c33b2a1eb0f，source SHA
56992375ac4eda6b16cf0e8b1add6f76abff683a503a19523d6632369ee0770e。
DEGEN2定向复验5.646617秒，optimal=-1435.1779999999994，1631pivot；
2次精确稀疏依赖成立并实际删2行、最终基974行，证明工作区峰值3052格、11783操作，
无dense model allocation，原始objective/KKT通过。该诊断保留在14/20全局批次中，不冒充正式整组。

theory_architect独立SOURCE/MATH GO，无必须修项；0solver/test/write，9只读命令4.1秒计入SP4。
回传记录reviews/sp4_dependency_source_math_go.json。固定分母、原始精确等式、全部slack/人工支持、
共享ProofBudget、reduced factor/full state先于发布均通过。minor的精确非奇异仍明确依赖旧B精确非奇异；
数值LU未被提升成精确秩证明。该门不等于SP4或八项GO。

| 当前固定组 | 成功分母 | 实际秒 | summary目录 |
|---|---:|---:|---|
| Netlib第2/2轮 | 12/12 | 16.4665136 | groups/1824c8d5-d4b7-4daf-85f5-99079666e859 |
| capacity第2/2轮 | 12/12 | 46.0118034 | groups/06a2e016-5543-4f0d-a634-c7f650d773fe |
| tiny | 48/48 | 27.5128873 | groups/b7a9acc2-bb9d-4dfb-8b7a-91335f1fd0dd |
| pressure | 24/24 | 13.7805478 | groups/c786e60b-e36c-4679-853b-6507864d4425 |
| 机制 | 8/8 | 6.2533391 | groups/2b11a694-a702-4cb2-bb22-24ee467bc9de |
| MIP/CG | 16/16 | 10.3672937 | 由最新mip-cg summary定位 |
| 历史兼容 | 737/737 | 35.7949653 | 由最新historical summary定位 |

全部位于原outputs/sparse_lp_program_20261024根，冻结输入/原阈值/子进程资源门保持。
Netlib首轮11/12和旧warm失败仍在原分母，未覆写或改算轮次。
历史组保存288旧固定项、192模型×2配置、64保存诊断及两个公开研究例的一条联合记录；
保存诊断0新增求解、0新外部参考，旧984文件前后哈希不变，旧账本未写入。

已向用户提交仅追加1轮原固定warm的窄请求：8轨迹×cold/warm×5重复、每条20修改，
原输入、阈值、60秒/1GiB、SP3及全局预算不变。原RR02第5节明确2轮，已用满；
新源码不能用旧正式结果桥接。等待明确答复期间继续已授权的文档/质量准备和候选交付，未启动第三轮。

候选仅将pyproject version/description、包__version__与CITATION改为0.3.0a1。
前后原始字节及严格literal-mask等价检查保存在metadata_source_bridge.json，SHA
f18e9b8e5caf1b24fe6180b78ef9ee5e71f4490e2059dee8efb84d0ce3d7525f；
新source SHA889d191b05736d36de4cd935aecf15e77900d6e7c0f2c5bb8d6bef5914439669。
这只桥接元数据，不桥接be654旧算法。L0015 v0.2.2增补线性工作区精确依赖与E11；
公开Python小例在新算法再次原样执行通过，2公开LP/2真实LU、1次独立2x2转置求解，0.5707956秒。
实际新收据reviews/learning_example_sp4_receipt.json，旧收据保留。

## 11. RR03窄授权与证据汇总修正

用户直接回复call_554103221b16444996333aabfb6b2326：
“授权追加1轮固定 warm 复验（推荐）”。[RR03](../codex/20261024-02-03_sparse-lp-program.md)
仅将本程序正式warm上限2→3；原两轮及失败成本保留，无第四轮授权。
README6.11、mirror、原账本human_warm_extension及RR03匹配小报告已登记；
RR02继续为唯一整体总报告。原输入、1600修改/80初始、五重复、配对顺序、阈值、
60秒/1GiB、SP3/全局预算及capacity/Netlib/quality/diagnostic上限全部保持。

red_team_reviewer独立核对当前5组104/104，90 optimal原objective/primal/dual/KKT独立重算，
4 Farkas及4射线用精确有理数核验，未调用项目checker或solver。最大primal残差2.8422e-13，
最大stationarity9.8363e-15、互补5.2715e-10、P-D差2.3694e-8、冻结目标误差9.3133e-10。
全部guard null，观测最大child5.2870652秒、RSS127598592字节；6耦合例pivot
1413/80/2065/80/650/2147；8机制212/196/194/80/89/64/80/80，eta比例全1.0。
104个请求均指定sparse，102个进入后给出sparse诊断且dense_model_allocations=0；
PRESS-LIMIT-01/03分别在时间限制和预LP非零门退出，没有引擎诊断，不能声称102之外也实际进入内核。
只读工具7.3599419秒已计SP4，0solver/test/write；reviews/sp4_fixed_lp_independent_go.json。
该五组子门GO不扩大为当前warm或整体GO。

首次upper/history/docs证据汇总为MIP/CG和docs通过、historical未通过：
旧probe_records实际保存192模型×2配置=384记录，汇总器错误断言原始列表192条。
实际历史driver按ID提取192个共同参考，737结果完整；旧输入/真值/384记录均未修改。
修正汇总器为核验192唯一模型、384唯一(id,config)完整笛卡尔积及每模型两个参考status/objective一致；
缺配置、重复、错ID/配置及参考冲突均拒绝。15项纯证据逻辑测试和Ruff通过，0新增solver。
初始失败reviews/sp4_upper_history_readiness.json及1.7912314秒实账保留，不重跑已通过的历史求解组。

继续核对发现同一汇总器把diagnostics recipe字典当作64条明细，第二次汇总因此TypeError；
1.8144262秒与sp4_upper_history_readiness_fixed.json继续保留。按冻结recipe的8案例×8变体
恢复64个D-案例-变体ID，仍逐一核对保存原文件SHA和0新增调用。
该schema修正后16项纯证据测试/Ruff通过，mip_cg/historical/docs_budget全部机械通过，
收据sp4_upper_history_readiness_complete.json。未修改历史driver、输入、保存结果或求解器。

完整quality第1/3次运行49.321717秒：6584 passed、1 failed；pytest完成后因失败未进入末尾Ruff。
唯一失败为旧test_native_layers_never_import_scipy_or_the_external_adapter无条件禁止SciPy导入，
与已冻结稀疏契约允许矩阵存储/LU的依赖边界冲突。未修改生产代码或数学验收断言。
架构测试改成逐文件/逐符号批准三处存储与splu导入，仍拒绝optimize、lsqr、core层扩张和外部adapter；
新增7个正/负静态例，下一次完整质量须包含全部测试及末尾lint成功。

完整quality第2/3次50.3784507秒成功：6592测试、结构检查和末尾全仓Ruff全部通过。
scope在命令前绑定全部src/tests/examples/scripts/fixtureJSON/pyproject，当前源身份一致。
实核预算总3037.1124781/28800秒，SP3 1490.0927953/10800、SP4 392.6096112/10800；
capacity2/2、Netlib2/2、warm2/3、quality2/3、diagnostic14/20。
随后在commit2f57f57a46b43adee4c104c3cf6160cac47f913f启动获批的round3，
输出warm/round3_b5c09c12-3b0d-42f9-9532-1001ad42693a；期间无生产改动或并行重型检查。

## 12. 当前源warm第三轮HOLD

整组670.6690374秒，80child自然完成，75/80；五次BOUND02 cold分别在60.58/60.83/60.55/60.56/60.56秒
由原OS保护结束。五次warm及其余70child通过。summary SHA
77b974d432734b5f385ce2ec432e21d036c809e27e8198a1a1569863898bda28，
reviews/sp3_warm_round3_failure.json保留全部失败，未聚合八条完整收益或签当前SP3/整体GO。
原be654正式80/80仍是历史事实，不能替代新源结果。

失败cold已保存的15/19/15/15/14修改前缀共78均optimal并通过原checker，
相应pivot及factorization计数逐项与旧源cold一致，单步墙钟约从1.4–1.8秒变为约3.4–4.9秒。
当前BOUND02 warm初始仍722pivot/37LU、首改574dual/28LU；依赖检查为空、删行0，
没有证据表明这些已完成状态因新增精确依赖而增加换基/分解工作。
这支持运行速度下降的事实，尚未证明超时的唯一原因，也不推出未完成状态正确。

共1663公开调用启动、1658返回完成（其中5初始由进入已检前缀推定）；完整保存75初始和1578修改结果。
剩余22修改未完整返回，五中断调用的内部LU数未完全可观测；实际墙钟全部计入原SP3桶。
一次宿主只读CPU快照见额外Python、排版及其他进程活跃；仅为本轮内瞬时观测，未证明因果或持续时间。
主线程启动前没有核对/冻结宿主负载，此观测缺口如实登记，不把环境解释当成通过依据。

当前warm3/3，capacity2/2、Netlib2/2、quality2/3、diagnostic14/20；
SP3 2160.7618327/10800秒，SP4 392.6096112/10800，总3707.7815155/28800秒。
时间余额不扩大次数；没有第四轮授权。先进行独立只读原因核对，并完成原已授权的候选/8安装，
其功能和工件结果不会恢复warm性能门或整体GO。

## 13. RR04同源码与原工件窄续接

用户直接回复call_b401b2090a634e03b64bcdcebf18fc2f：“授权该窄续接包（推荐）”。
[RR04合同](../codex/20261024-02-04_sparse-lp-program.md)仅追加同源码固定warm第4轮（3→4）
及原SHA工件的一次完整8新环境安装。启动前新20秒宿主预检，运行期间连续观测并核对末尾身份。
运行期负载如实保留为上下文，原正确性、收益及资源门保持；两份原工件禁止重建或替换。
原轮次/失败及实账均保留，其他上限不变；同一Goal，RR02继续唯一总报告。

首次工件构建44.4607308秒，126模块和元数据原字节审计通过；8环境均在direct_url archive hash处失败，0solver。
uv生成archive_info空字典，检查器正确拒绝。三个隔离小轮子探针（0.2798756/0.4541232/9.9279257秒）
验证环境内ensurepip后普通pip实际写入SHA；均0 SILO安装/0solver，不削弱原check_installed.py。
原工件summary SHA845cf2bd5521033a59d76f055b2ca4f81de8e0a99b8b4b88ac134116890c649c。
工具保护40纯组件及Ruff通过；独立只读复核、最后完整质量、新8环境及round4的实际结果随后登记。

RR04工具保护独立GO，15只读命令3.5817468秒计SP4；127生产文件与warm3逐字节相同，
13个受保护driver和原checker SHA不变。真实回传reviews/rr04_guard_review_raw.md。
此前三项工具HOLD及3.7288158秒保留：现已要求真实账本parent/一次child消费、拒绝漏reuse重建、
连续观测后重核源码/脚本/输入/环境。原复核者用量限制导致的未完成复审没有被当作GO。

当前工具提交fa0ee44；完整quality第3/3次56.2786357秒成功，6607测试及结构/全仓Ruff通过。
scope在命令前固定，质量日志runs/2026-10-25T06-28-36.007716+00-00_20f81109-9a07-4984-a922-10a00ef844ca/console.log。
原两份工件SHA未变，新八环境复验220.3045731秒，8/8首轮通过，0环境重试/0重建。
summary为delivery/7909ec92-6b7c-46f3-8d12-33e5c74d1f10/summary.json；原8溯源失败仍保留。
原checker的来源、archive SHA、依赖、会话、CLI、研究例及修复门全部通过，外部优化器调用0。
随后quality/delivery汇总0.9789662秒通过，reviews/rr04_quality_delivery_readiness.json。
下一步新宿主预检及唯一warm4；当前没有整体GO。

## 14. 宿主预检未达与RR05

两次新20秒预检分别20.4283652和20.4177340秒，均busy、0solver，正式warm4未启动。
第一窗其他排版进程合计约0.713核；第二窗其他Python约0.981核，均超过原启动线。
仅能说明各窗口负载，不能将其推广为warm3的唯一超时原因。两次对相应PID的只读身份查询
均已无匹配活进程，0.4186234/0.4473500秒同计SP4；未终止或调整其他作业。
原diagnostic20/20已用满；原上限没有被预算余额扩大。

用户直接回复call_cbfe1d7c51e94ad69b2a3b91095ade97：“授权追加宿主预检包（推荐）”。
[RR05](../codex/20261024-02-05_sparse-lp-program.md)仅追加≤3×20秒零求解窗口，单列host-preflight、
原SP4/总时间预算，源码/脚本/测试/输入和quiet阈值保持。取得有效低负载记录后，执行既获批唯一warm4。
原八项及最终独立GO仍为唯一完成线，当前整体未完成。
