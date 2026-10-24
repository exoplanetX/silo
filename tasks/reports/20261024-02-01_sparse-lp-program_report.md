# 稀疏 LP 与连续重优化整体执行报告

合同：[20261024-02-01](../codex/20261024-02-01_sparse-lp-program.md)。
依据：[总体规划](../phases/sparse_lp_reoptimization_program_20261024.md)、
[实施计划](../phases/sparse_lp_implementation_20261024.md)。

当前状态（2026-10-25）：**SP1 GO；SP2第7轮针对修复已获直接人类授权，完整目标未完成。**
产品a4eccb17704b04cc939d97ac39461156358fbeb7；最后96组件、172当前源公开集成及源码门通过，
smoke仍4/6，两容量LP数值失败。SP3及SP4正式验收未开始，0.3.0a1和8安装未交付。
人类现明确答复：“同意你要求的追加1次针对修复及1轮固定复验”。本次只追加第7轮，
针对可信旧owner的同基主动刷新改为完整state验证后发布，并运行一轮固定48tiny/24pressure/6smoke。
修正总上限7，原SP2共3600秒预算及输入、阈值、Bland/Devex和八项目标保持；不重置旧轮次。
第7轮通过且获独立SP2 GO后继续原SP3–SP4；若复验仍失败，保存问题包并停止新增修复/求解。

直接授权答复：“授权剩余预算内最多3轮（推荐）”，对应问题call_c43d2b03430449b49ec2dd3a8a0bc91e。
本单SP2修正上限从3扩至6；原时间预算、输入、阈值、Bland/Devex及八项目标不变。
此节更新下文提案的待授权状态，不重置旧账本或另开Goal。
原HOLD代码2b40d87、元数据2d6e337保留；整体Goal及八项目标仍未完成。


## 第7轮直接授权登记

直接人类授权时间为本次2026-10-25续接；此前第4–6轮停止有效，以下终止包作为历史证据原样保留。
本次不新增Goal、不修订不可变合同、不提高原时间预算，不改变总体完成线。
同基刷新失败可保留可信旧owner并拒绝触发entering；残差已失效的强制恢复失败仍保守退出。
推荐GPT-6 Sol/high；实现、组件、源码门及唯一固定复验的实际收据随后写入本报告。

## 第4–6轮数值包的终止快照（历史）

本节保留第6轮终止时结论；第7轮权限和当前状态以上方直接授权登记为准。
直接授权的“最多再3轮”已按第4、5、6轮完整使用，停止依据是人类次数上限，
时间余额不构成第7轮授权。集中包：outputs/sparse_lp_program_20261024/reviews/numeric_package_stop.json。

第6轮唯一smoke组a5fffafc-36a6-4a13-9ea5-c16c07ca8e37，6root/6LP均完成，
总54.9617354秒；四小Netlib optimal，两个必过容量预检未达：

| 实例 | 状态 | pivot | 实例完整耗时 | 保守OS峰值RSS |
|---|---|---:|---:|---:|
| CAP-FLOW-01 | numerical_failure | 4308 | 8.1437734秒 | 119664640字节 |
| CAP-TRANS-01 | numerical_failure | 14496 | 43.6914253秒 | 177844224字节 |

两例均未触120秒或1GiB保护，失败属于正确性门。源码GO不能替代容量通过。
FLOW候选4308次均接受并消费完整pending状态；TRANS14499次候选接受14496、丢弃3，
pending消费14496。末次成功提交后，同一B上的raw_candidate_feasibility主动刷新
才首次导致失可行：FLOW generation527→528→529，TRANS1391→1392→1393；
后一个代次是再次primal复核，仍失败。对应三份矩阵CSC SHA各自相同，未发生换基。
高置信边界是“同基重构的新generation在完整state验收前已原位发布”；
具体底层条件数或SuperLU误差来源尚未证明，不能称为唯一数值根因。
只读数学复核BLOCK/STOP见reviews/numeric_round6_terminal_cause.json及原始trace提取。
独立red_team_reviewer从原始summary/result/trace、源码和账本再次确认STOP/HOLD，
排除engine、checker、进程exit与真实求解状态的混淆；见reviews/numeric_package_stop_red_team.json。
两份审查复用同一smoke，不能重复计为容量成功证据。待授权同基提案范围合规，但没有第7轮权限。

截至原证据保护复核，SP1=368.5422803秒、SP2=505.1359841秒、SP3=0、SP4静态准备=4.4615295秒，
总878.1397939秒；SP2原3600秒约余3094.864秒。最终静态收尾实耗继续写原append-only账本。
旧984文件及完整目录清单、两治理文件哈希全部保持，来源与最后smoke相同；local-commit，无push/发布。
索引生成、项目结构复核及diff静态检查均通过，0新增solver。收尾前a4eccb1的
cached origin/main...HEAD=0/67，仅本地缓存、未查询即时远端；完整Git证明见
reviews/numeric_package_git_proof.json。最后文档收尾提交从Git history定位，避免自引用。

原八项完成线继续保留：SP1已GO；端到端cold容量门未达；8机制、160修改状态/5重复及收益、
固定12MIP/4CG、当前完整质量/旧矩阵、0.3.0a1/8安装和最终伴学/独立终验均未完成。
已做的组件与接口检查按其范围保留，不能充当未执行正式矩阵的结果。

下一项仅为待人类授权的单一提案：把“旧owner仍有完整可行状态、为继续primal选择主动发起的
同基刷新”纳入私有完整state验证后发布，失败保留可信旧owner并拒绝触发entering；
若旧残差已失效的强制恢复也失败，仍保守numerical_failure，不能回滚到不可信旧因子继续。
建议只追加1次针对修复及1轮受影响48tiny/24pressure/6smoke，沿原剩余时间、输入、阈值和总目标；
SP2通过后才按原授权继续SP3–SP4。此提案尚未执行、不新建Goal、不提高时间预算。
推荐GPT-6 Sol/high，困难集中于同基generation发布与可信旧状态的异常隔离；不声称已切模型。

## 第4–6轮实施历史

以下按当时进度保留；当前结论以上方终止快照为准。

第4轮观测仅保留末次成功pivot，失败时投影为before最差8项、after最差8项及leaving的
并集，最多17项；重构后必须重算完整state，仍失可行则保守失败，原阈值与pricing不变。
独立theory_architect代码门GO见reviews/numeric_round4_code_gate.json；不预判容量结果。
组件最终54测试通过，含before/after最差坐标变动的20维toy；7条检查含早先lint失败完整保留，
合计2.7001323秒且仅计一次。root受影响集成172测试通过，另计2.0315808秒。
SP4交付helper仅完成静态准备及9项纯逻辑测试，尚未构建/安装/运行求解器；7条收据加
1秒保守外层计时计入SP4，后续正式构建仍须SP3 GO和已提交的0.3.0a1源码。

### 第4轮实际证据（877058d）

唯一smoke组groups/7706a828-1607-49cf-9460-3f354bf94f80，6root/6LP完成，
总49.8346471秒；四Netlib optimal，FLOW3963/TRANS13830仍numerical_failure。
FLOW6.9337768秒/RSS115568640，TRANS39.8693875秒/RSS175796224，未触资源上限。
原始请求/结果与摘要均保留SHA，提取reviews/numeric_round4_trace_extract.json。

两者theta均0；预测向量在原ptol内，actual新B解与一次同基重构后均失可行。
FLOW原min−2.97146e−8/ptol2.00000e−7，fresh before−4.83789e−7/after−5.37258e−7；
TRANS预测min0/ptol4.85714e−7，fresh最差−0.125178，重构前后相同。
old/pred/fresh及方向的后向残差全部通过原门；ptol缩小与单纯eta恢复均不能解释修复。
TRANS实际pivot2.78824e−10仅略高于冻结门2.06964e−10，growth3.58649e9。
据此独立数学门推导出更小的第5轮修复：实际候选坐标rho=xb[r]/d[r]，
y[r]=rho、其他y[i]=xb[i]−rho*d[i]，不能用clamped theta0替代。
FLOW此公式给出的失败值与fresh吻合；TRANS的rho自身已违反原primal门。
在pricing.update与factor mutation之前按候选自身原ptol核验，仅O(m)，不新增LU/solve。
首次失败共享old-B一次刷新，完整重算后仍失败则拒绝整个entering并保留同基R；
全改善列被拒绝仍numerical_failure。ratio、阈值、Bland/Devex、dual和cleanup保持。
reviews/numeric_round5_design_gate.json记录独立设计GO；实现/容量结果仍待实际检查。
完整private-factor事务暂不实施，只有raw门通过仍fresh失可行时才由后续获准轮次评估。

第5轮实现kernel SHA1db2593c，66组件最终通过，检查总3.7525939秒；
原toy hook误把direction同步污染的一次失败完整保留，只修测试hook后两次全过，未因此改产品。
root受影响公开集成172项通过，1.9758299秒。独立代码门
reviews/numeric_round5_code_gate.json关闭公式/有限性/调用顺序/共享刷新/R及Bland义务。
公开SolveResult/CGResult既有递归清洗支持内部非有限诊断，审查中的序列化疑点已据代码撤回。
普通通过路径仍为原6次triangular solve/1次LU，raw门只增加O(m)向量运算。

第5轮唯一smoke groups/a927ebb8-0b97-4e77-9966-2267adfdcb22，source11bd272，
6root/6LP完成，总52.6593221秒，四Netlib通过。FLOW4308pivot/7.6409656秒失败，
raw失败25/刷新13/拒绝12；TRANS14493pivot/41.8732892秒失败，raw失败6/刷新3/拒绝3。
原失败提交被raw门拦截，沿新路径的末次候选raw门通过，actual新B仍失可行，
一次同基重构后保持失败；这关闭了“仅raw坐标门足够”的假设。
FLOW预测在原约2e−7门内而fresh min约−4.81318e−7；TRANS预测min约−5.28e−15、
fresh min约−9.63290e−7超过原约4.85714e−7门。
原始与提取reviews/numeric_round5_trace_extract.json保留，未触120秒/1GiB外guard。
第6轮是人类允许的最后修正轮：私有候选因子在实际新B验证后才发布，失败保留旧owner，
所有实际cost与峰值仍计、成功basis/eta只在接受后计，不改input/threshold/ratio/Bland/Devex。
候选状态与generation/缓存一致性经独立设计门后才实施；不能因剩余时间再开第7轮。
reviews/numeric_round6_design_gate.json保存基础设计及补充A：候选完成XB与BT对偶的
完整同代次state后检查原primal门；BT若触发重构，整组三元组作废并沿原3次state门重算。
通过后一次性pending full state替代下一外层state，绑定public/run/phase/problem、
basis、generation、RHS/cost不可变身份；不跨求解缓存状态，dual/cleanup不使用。
候选数值拒绝可以共享原old-B刷新机会；deadline/resource保持limit，没有新重试门。
SP4机械评价helper和8项纯逻辑测试已准备，0native/安装；SP1旧门来源绑定只读集成通过。

第6轮最终factor f1d42a37/kernel7cf6d061；reviews/numeric_round6_code_gate.json为独立源码GO。
14条组件检查累计7.2697574秒，最终96项通过；曾有空counter计量7KeyError的失败完整保留。
累计kernel375开始/371返回、candidate state385开始/375返回，故不能把整个历史称为全部完成；
注入失败与未返回事件保留在原收据。最后仅补post-SPLU deadline前的已生成LU单体/并存峰记账，
未改变数值轨迹；对应toy的actual单体8/并存14，仍抛time_limit且旧owner不发布。
root当前源公开集成172项通过，1.95134秒；此前峰值补丁前另一次1.9634991秒亦保留计费。
正常通过toy仍6次B/BT求解、1次初始LU。本段为运行前快照；随后正式结果见上方终止快照，禁止增加第7修正轮。

直接授权原文答复：“授权追加一次修复和复验（推荐）”，对应问题为仅追加1次
“因子重建后状态与换基提交保持同一代次”的针对修复和1轮受影响固定组复验；
保留原输入、阈值和时间预算，通过后继续原SP3–SP4。本节覆盖下文此前HOLD的待授权状态，
不删除旧失败或重置次数。唯一Goal工具最后仍blocked，API不能代用户切active；
保留其身份并执行此次已明确授权的工作，不创建第二Goal或声称状态已切换。

## 获批追加轮的实际结果与下一项决策

产品提交4fc79d466bde9a8252b6c216cfe5f1cf751a0977关闭generation一致性对象。
独立只读代码门GO；46组件首轮通过，44次direct kernel/88次LU，0public root，1.5385044秒。
root集成172测试通过，父进程118public root/315LP全部完成，另有隔离NumPy探针2root，
命令2.5609089秒。组件与代码门不预支整个SP2。

唯一获准固定轮cohort=ce5713f1-cdec-4840-b7ff-33812ca978c9，78root/77LP实际完成：

| 组 | 当前源码事实 | 完整命令耗时 |
|---|---|---:|
| tiny48 | 48/48通过，groups/7147981f-29a7-4270-8fb4-54792db4e268 | 34.2051397秒 |
| pressure24 | 原始22/24；两资源类别规范重评后24/24，原记录保留 | 17.5045307秒 |
| smoke6 | 四Netlib optimal，两个CAP numerical_failure，groups/ec300be2-e01d-4a6c-89b5-970bd3d8747e | 101.8175287秒 |

资源标签澄清由独立experiment_auditor确认：冻结metadata的sparse_nnz_limit/factor_nnz_limit
是资源种类，公开API仍为limit/resource_limit。LIMIT03有max_sparse_nnz0、输入nnz3、
未进入LP及对应message；LIMIT04有max_factor_nnz0、进入LP/standardnnz7/0次LU及factor message。
新check_exit以这些实际门据核验，不改输入/标签/数学/容差。
reviews/extra_fixed78_resource_reassessment.json只读重评既有24输出，0新solve/参考调用；
原始pass=false与原轮exit_codes=[0,1,1]保持，不能改写成原轮全绿。

容量结果：FLOW在3963pivot后Primal simplex lost feasibility，13.7941493秒，RSS115511296；
TRANS在13830pivot后同一错误，84.3660445秒，RSS172306432。均未碰120秒或1GiB外guard，
但正确性失败，不能算容量通过。FLOW补丁前后相同pivot失败；generation恢复类型仅pivot_selection，
无residual/direction_residual/pivot隐式恢复证据。因此代次缺陷是已关闭的真实风险，
本次两个CAP失败的具体数值根因仍未确定。

独立数学门继续BLOCK：已接受pivot的下一轮fresh state失去可行性；
当前后向残差门不提供基本解/方向分量符号或比率排序的前向保证。
现日志缺末次pivot的old xb/d/theta/leaving、预测new xb与fresh new-B解的对照，
不能武断归因eta累积、主元大小或Bland。TRANS最后eta链为0，尤其不能简单归因eta链。

追加授权已完整使用；原3次SP2修正到此停止，不自行执行第四次修复/诊断，不进入SP3。
截至规范重评：SP1 368.5422803秒，SP2 324.4619693秒，总693.0042496秒；
SP2原3600秒尚余约3275秒。时间余额不自动授权次数扩展。

### 建议的有界后续数值包（提案，未执行）

建议在SP2剩余时间内自主推进同一个“容量LP接受pivot后可行性保持”问题，最多再3轮
诊断—针对修复—受影响复验；每批启动前仍核完整预算，任一上限先到即停。
这会把本单SP2修正总上限从3扩至6，其余原时间/实例/阈值/正式组上限均保持。

第一步仅增加有限pivot观测并在首次lost-feasibility时，对实际current B重构/重算一次：
记录old/new ptol和min xb、enter/leave、theta、最小/次小ratio、失败行旧d/ratio、
B*d-a与B*xb-b的残差及允许bound、eta/generation/refactor reason、预测与fresh new-B值。
观测都为稀疏矩阵与有界向量，不全局dense，不调用外部优化器。

随后只按证据落入的分支修复：预测值已不可行→ratio/符号路径；
current-B重构恢复可行→数值表示恢复；重构仍不可行→先证明事务化pivot核验/候选拒绝，
再实施。持久不可行保持numerical_failure，不改阈值或跳过真实blocker宣称optimal。
不预选新算法、不修改已冻结Bland/Devex、65536及位数/操作门。

接受标准仍为当前源码fixed48/24/6全过与独立SP2 GO，然后继续原SP3–SP4八项目标。
推荐继续GPT-6 Sol/high；本提案需要人类明确扩展次数，不把原追加一次授权泛化。

## 激活与完整目标

2026-10-24，人类在本开发对话以Goal模式直接要求：
“现在silo-solver的下一阶段开发已经讨论完毕，分阶段任务已经给出，请你从
"silo-solver-1010"对话里读取最新的任务规划，完成这次的设计目标。”
唯一Goal已存在且active，所有者silo-solver开发（01a15208-bea9-7030-aacc-95d785e8fa58），
不创建第二Goal。本轮按SP1–SP4连续完成同一合同及八项总验收，正常门通过后不跨对话等待。

目标保持端到端稀疏LP、真实LU/eta、跨调用会话及四类编辑、MIP/CG接入、
12容量/12Netlib必过、160修改状态/5重复/中位收益≥1.5且6/8≥1、8安装和伴学。
任一未达仍登记未达；不改题、换例、放宽阈值或仅凭接口/测试数宣布完成。

## 启动证据

- 实际启动HEAD/发行提交：a4809855cffb028687ab0e192be68f8186937335；准备基线64700cd，产品基线f488189。
- 启动分支codex/teaching-research-prototype；创建并切换codex/sparse-lp-reoptimization，未reset/clean/push。
- 启动cached origin/main...HEAD=0/52；仅本地跟踪引用，没有即时远端查询。
- 只存在两项已接受治理差异；AGENTS.md SHA2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638，
  根案例通告SHA0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221，已核对，排除暂存。
- 已读最新讨论规划、人类准备指令/最终实施入口，合同、两计划、AGENTS/CASE、tasks规则、mirror、learning规则。
- 新报告沿用已签02-01合同身份，不新签任务；L0015当前未占用。
- 沿用silo-development-operator；本合同被当前人类直接指令激活，覆盖列明L2/L3及内部连续执行。
  推荐GPT-6 Sol/high，不声称已切模型。memory registry无SILO命中，未依赖记忆推断当前状态。

## 预算与证据根

唯一新根outputs/sparse_lp_program_20261024；账本append-only SHA链跨续接保留。
SP1/SP2/SP3/SP4/余量=30/60/180/180/30分钟，总计480分钟；不设混合总调用上限。
容量/外部≤2轮、warm≤2轮各5重复、全质量≤3轮、额外诊断≤20批各60秒；
安装每组合至多一次同SHA纯环境重试。时间不父子双计，失败/基线/比较/环境均计入。
旧prototype/revision/audit输入、工件、输出和账本只读。

## 检查点

| 阶段 | 当前状态 | 仍需证据 |
|---|---|---|
| SP1设计、输入与基线冻结 | GO；a3cff29输入、3c27324真值/基线 | 架构子门和完整证据设计门均独立GO；产品仍未改时登记 |
| SP2稀疏cold链 | HOLD，原两次加获批一次均已使用 | generation已独立GO；容量pivot后可行性保持未达 |
| SP3更新与会话 | 未开始 | 公式/缓存/机制/160状态/公平5重复收益及独立数值门 |
| SP4上层和总体交付 | 未开始 | 完整矩阵/历史/8安装/伴学/独立八项最终GO |

## 当前恢复入口

### SP1已取得的事实

- 120固定案例及8×20状态已实例化，首次输入/设计冻结提交a3cff29。
  Netlib12原件/解码/转换与独立Highs readModel/getLp逐字段/系数全等，没有运行优化器。
  108非外部案例经独立原始Fraction数学检查，容量BLOCK02真实2000变量/5000非零行/100000nnz。
- BOUND两轨迹在首次冻结及任何SILO/HiGHS优化前，发现原步长的可行性证明欠缺；
  只依据数学改为1/1024，44份旧draft及哈希归档。新40状态逐原行/界精确可行。
  最终manifest SHA51ee70574b413182e0092041e5ea96a11dda68df7ed850dcb17dc542f0f32725，
  sources SHA4d90dbbe6cdb3b668f9036fb033a2a0ae1905015d8d0200990855baa321498e2。
- 只读架构子门初评两项BLOCK（证明空间总量与缓存数值策略歧义），已按同一路线明确
  同时存活cell估计和三层身份/资源/pricing规则；窄复读GO，无新关闭项。完整SP1尚非GO。
- 已核实Windows Python3.13.9及独立3.11.15环境，NumPy2.3.5/SciPy1.16.3的正/转置LU可用。
  3.11首次依赖下载180秒harness_timeout保留；同版本、官方PyPI/系统证书传输重试9.079秒安装成功，
  没有放宽包版本、目标或数值标准。当前尚无SILO基线或HiGHS优化调用。
- 新账本初始化发现pin事件误用保留sha256字段：原字节保留，以pin-file SHA重建并验证唯一旧预像，
  明确恢复事件及以后保留字段拒绝已记录。首次preflight误套两层计时也保留双收据，
  按包含区间显式去重一次，新增父进程标记禁止嵌套计费。未重置账本、旧证据或消耗。

### 首次冻结后参考和基线

- a3cff29先于全部SILO基线与HiGHS优化调用，锁定三契约、recipes、120/160输入和来源。
  独立证据设计审核确认固定分母/容量实质/导入双路径，允许首次输入冻结；
  case candidate SHA重建核对已在首次提交内补齐。完整SP1仍需真值及基线后复核。
- 8个0.2.0a2 dense基线实际完成8次root调用，整批10.8822164秒，单线程独立进程。
  AFIRO/ADLITTLE/SC50A/SC50B/SC105/SC205/SHARE2B全部optimal；
  BLEND返回numerical_failure（Singular/near-singular basis QR），原失败完整保留。
  证据groups/422d13a0-c9db-4789-9dde-04e670d158a1，均未替换输入/预期。
- 新验证支撑6项单测通过（1.26秒pytest内部，1.71965秒完整计费），
  覆盖账本篡改/预算拒绝、OS wall/RSS和5重复配对指标，0次SILO调用。
  补充完整20状态/60秒轨迹驱动、真值绑定、进程树超时回收与旧证据只读复核入口。
  验证驱动尚待对应阶段实际使用，不以入口存在宣称机制/性能已达。
- 独立真值索引SHA8b138a13cf8a3dba039996d8b9a7ac8935a463852d0731453e18a334b4837b49。
  120案例+8初态+160修改状态全部绑定frozen payload和完整见证SHA；
  176份exact Fraction，112次单线程HiGHS（12 Netlib+100warm），0次SILO、0次重试。
  数值参考全部optimal并逐原行/界/KKT通过，最大scaled error8.852375491465501e-10，
  参考固定标准1e-8。导出69.2991402秒，后半段已测命令合计73.0969669秒，
  含小工具开销保守一次记76秒，不叠加内部68.9000196秒。
  reference/oracles_final_delivery_receipt.json含环境、逐调用和完整源/见证身份。
- evaluate SP1实际exit0，1.3865291秒；重建120/160输入、288真值绑定、8旧基线
  并复查7份最优结果对独立参考。当前产品src/pyproject与a480985完全一致。
  真值/基线第二次冻结3c27324；独立experiment_auditor复读完整证据门GO。
  与此前theory_architect架构子门GO合并，由主线程登记SP1 GO，随后才允许改产品。
  BLEND旧dense失败只保留为失败，不计入速度倍数或成功性能分母。

先核本报告、ledger链、Git/source身份及具体进程handle，再继续SP1。
输入准备由唯一写入者生成；输入/真值两提交及完整SP1独立门已完成，当前SP2 HOLD。
主线程负责CLI/账本/契约/集成；只读Devex原始依据和稠密边界核查不被计为算法实测。
所有缺口保持原范围；当前Goal未完成。原A/B已验收、C HOLD、D/E未开始，native延期。

## SP2实现与首轮证据

- 矩阵/变换/传播/原始核验/受限证明组件148测试通过，130public/134kernel完成，
  3.2221124秒。因子组件首验27通过，26kernel、45次实际LU，1.1033935秒。
  root公开接口/会话隔离/资源/旧MIP及CG集成171通过，完整命令1.9201998秒。
  这些组件结果均不代表容量或整体GO。
- 首轮tiny48/48，25.042362秒，groups/bfbe0b12-ffac-4db3-a02b-94a5b373c2ec。
- 首轮pressure21/24，12.6221512秒，groups/8bbb52d6-b632-4c71-83b6-2901dc4872a4。
  LIMIT01是harness覆盖time_limit0；NUM03/04是近相关等式被错误删除，错报optimal−1对真值0。
- 首轮smoke4/6，67.4896826秒，groups/f20168f4-f4e7-4c1b-b875-e3ba9a8e53f3。
  AFIRO/ADLITTLE/SC50A/SC50B正确optimal；CAP-FLOW-01在5592pivot后unsafe pivot，
  CAP-TRANS-01在13308pivot后失去primal feasibility。没有替换模型或调整阈值。
- 初轮Windows RSS只监控venv redirector，约7MB并非真实解释器峰值；旧值不能作为容量证据。
  已改为root及后代进程OS PeakWorkingSetSize之和（保守上界），真实40MiB子进程回归通过。
  time_limit改为min(冻结选项,外层上限)，保留零值；支撑7测试通过，2.1415432秒。
- MatOps冻结操作清单补齐、15组件通过，1.4502346秒。全池证明预留
  4*nResult+4*mResult+2*pool+32外层Fraction槽，与basis共用ProofBudget；
  58测试通过，0.7091256秒，真实1/100000007重构路径达到65536通过、65537在basis分配前拒绝。

## 两次针对修正及当前阻断

1. 第一次：删除行需原始二进制方程精确依赖证明；真正相同比值才按semantic key并列；
   factor/kernel共用安全主元谓词，并保留所有真实阻塞行。31组件通过，新增验证1.2109429秒。
   一批两模型诊断1.5189188秒，FLOW117/TRANS47pivot后均unsafe blocker数值失败。
   保存diagnostics/kernel_sp2_fix1，后代RSS约75/76MB；不计容量通过。
2. 第二次：当前B/cost/phase内拒绝不可安全换基的进入列，保留sticky Bland及visited，
   按既定顺序尝试其余列；全拒保守numerical_failure。33组件通过，新增验证1.1067804秒。
   两模型诊断36.574997秒，FLOW3963pivot后Primal simplex lost feasibility；
   TRANS5057pivot后solver自返25.0497秒time_limit，外层25.4847秒也标harness_timeout。
   原始输出完整、exit0仍按harness失败保留；RSS约102.6/132.1MB。
   保存diagnostics/kernel_sp2_fix2；没有第三次修复或额外正式组。

独立theory_architect仍判代码门BLOCK，指出同一代次不变量尚未落实：
factor.replace_column可在已选leaving后重构并重算direction，却提交旧leaving；
direction solve或Devex BTRAN隐式重构时，kernel也未统一撤销已算state/ratio。
旧d=(1,2)、xB=(1,1)选第二行，若重构后d=(2,.5)，真实blocker已是第一行，
沿用第二行会把第一基本值降至−3。该数学反例说明具体提交风险，未声称它是全部性能根因。

### 可审阅的下一项修复方案（尚未授权执行）

范围只涉及sparse_factor.py/sparse_kernel.py及对应组件tests，不改输入、容差、Bland定义或目标：

- SparseFactor增加单调generation；一次成功current-B refactor更新代次。
- state、direction、Devex BTRAN、ratio、commit携带同一代次。
  任一步重构即取消尚未提交pivot，从同一B重算xB、dual、rc、direction、true-min-ratio。
- replace_column需要重构时返回未提交retry；不以新direction提交旧leaving。
  拒绝集不授权optimal；fresh-state后有历史被拒列而改善信号消失时仍保守失败。
- 增加两项注入测试：direction solve及BTRAN分别强制重构并改变真实blocker，
  断言旧leaving从未提交；保留candidate恢复/全拒失败/小阻塞不越过测试。
- 建议仅追加一次针对修正及一次受影响正式复验（48tiny/24pressure/6smoke），
  仍遵守各例原时间/RSS、SP2剩余时间和原总预算；不重置已用额度。
  源码通过独立复读且上述组全部通过后，才可给SP2 GO并继续原SP3–SP4。
  推荐GPT-6 Sol/high，复用当前实现上下文；未声称切换实际模型。

合同第6节限定每阶段初验+两次修正；本阶段两次已使用。需要人类明确扩展本阶段次数，
才可实施上述额外修复。技术问题与次数授权分别保留，目标/完成标准不变。

## 未完成义务与证据状态

- SP2容量两个必过预检和独立数学GO未达，pressure固定整组尚未在最新修正源码重跑。
- SP3的8机制正式组、160修改状态×5重复、公平收益≥1.5及6/8≥1均未运行。
- SP4完整12容量/12Netlib、12MIP/4CG、旧288/192/64整组、全质量及8安装未运行。
- 没有0.3.0a1工件、发布或最终八项GO；pyproject/runtime仍为0.2.0a2实验分支。
- L0012保留旧dense已核基线并注明未验稀疏增补；新L0015为draft，verified_code=null。
- 暂存/提交仅本任务代码与HOLD材料，两治理文件原SHA及所有旧输出/工件/账本保持。

截至第二次诊断：SP1 368.5422803秒，SP2 157.034505秒，总525.5767853秒；
后续保存材料只进行静态检查，准确新总量从append-only ledger读取。
capacity/netlib/warm/quality正式轮次均0；diagnostic2/20；本次HOLD由阶段修正次数上限触发，
480分钟总时间并未耗尽。后续不把剩余时间自动解释为第三次修正授权。

HOLD保存检查：结构检查原先将任何SciPy导入都当作优化器调用，现按本合同
已授权的矩阵/LU边界做最小白名单适配；仅modeling矩阵adapter允许from scipy import sparse，
lp/modeling仅允许列明的sparse矩阵函数及splu。optimize、HiGHS、csgraph及core反向依赖仍拒绝。
9项纯AST策略测试通过（0次SILO），随后结构/全仓ruff/diff检查均exit0；
没有运行完整check_quality.py或新增算法试验。首次静态失败收据同样保留。

## Remote Sync Proof

branch=codex/sparse-lp-reoptimization；known governance dirty_worktree；push=not_attempted。
HOLD产品保存提交2b40d87cae0153538592abd2af492c9e6c9e7be7，前一主体提交8d72a3c；
后续MIP遗漏暂存已由独立跟进提交补齐，当前124个源码/pyproject均与已保存运行身份一致。
逐文件git blob严格只作CRLF→LF运输等价核对通过；不把实质差异归为换行。
sp2_hold_committed_identity.json保存实际源码SHA、Git/source匹配、状态、last5和cached引用。
产品保存时cached origin/main...HEAD=0/57；只读本地引用，没有fetch或即时远端核对。
该时刻last5为2b40d87、8d72a3c、8aa0946、3c27324、a3cff29。
两项已接受治理差异仍原SHA且未暂存，旧证据逐文件SHA保持。
截至保存身份复核总验证534.3422841秒（SP1 368.5422803，SP2 165.8000038）；
完整质量/容量组/Netlib组/warm/安装均未执行，无发布。
额外一次修复授权问题已在开发对话提出；提出问题不等于获准，回复前保持HOLD。
报告最后元数据提交从Git history定位；最终cached计数因本地报告提交再前进，不冒充远端状态。

后续更新：该追加授权已直接获得并执行完毕，最新算法提交4fc79d4，授权登记5893ba7。
上面的2b40d87/534秒等为前次HOLD快照，保留作历史。当前generation对象GO、SP2容量仍HOLD；
规范资源重评与最新数值包提案见报告首部。后续metadata提交从本报告Git history定位。
