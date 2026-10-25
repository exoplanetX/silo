# 稀疏LP整体目标集中恢复与续接执行报告

当前状态（2026-10-25）：RR02的R0/R1已完成，SP1 GO、SP2独立联合GO；接续原SP3，整体八项目标未完成。
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
| 2 端到端sparse cold | RR02首轮48/24/6全过，两CAP真实optimal且原空间KKT通过；完整12容量/12外部待验 |
| 3 LU/eta/数值与8机制 | 已有局部实现及非交换B/BT组件；正式8机制≥50pivot/70%待验 |
| 4 会话四修改与收益 | 已有私有会话实现，160状态×5重复和1.5/6条不回退未正式验收 |
| 5 MIP/CG真实稀疏接入 | 现有适配及小集成，固定12MIP/4CG与原全池精确P=D待验 |
| 6 旧行为与质量 | 旧验收保持；新源码全质量、288/192及保存64复核待完成 |
| 7 0.3.0a1与8安装 | helper准备保留，仍0.2.0a2实验分支，未构建/安装新候选 |
| 8 伴学、报告、独立终验 | L0015仍draft；L0012稀疏增补待核，最终八项独立GO待取得 |

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
原错误最优与资源保护保持。此源码尚待固定8机制复验，不预支SP3 GO。
