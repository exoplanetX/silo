# 最小受限主问题适配层 — 执行报告

## 1. 合同、基线与状态

- 合同：[20261019-02-01_restricted-master](../codex/20261019-02-01_restricted-master.md)。
- 类型/风险：一个明确批准的L3窄范围RMP能力，含L2新Python接口与LP调用；
  Git mode=local-commit，不push。没有启动新阶段或改写Phase7的历史完成范围。
- 实际起点/签发提交：`8a11eff6ed012fbe37eb36c9856066c0d0a239a0`，main，工作区干净。
  缓存origin/main为5277d1d，相对差异0/4；四个已知ahead为cfb43a8、ad62e0f、
  c3704be、8a11eff。当前授权明确覆盖此继续执行起点。
- 源码起点包含第1步修正，未把第1步验收的1399项测试或288个基算作本任务新增验证。
- 实现、针对性/全量质量、教学核对和两次本地提交已完成，待讨论对话验收。
- 本任务实现提交：`48c242d2fba886807d1230fb7a72b85c3f212b0e`。报告提交通过
  `git log -1 --format=%H -- tasks/reports/20261019-02-01_restricted-master_report.md` 定位。

## 2. 最小接口与复用边界

新增[restricted_master.py](../../src/silo/decomposition/restricted_master.py)，在decomposition
包导出RestrictedMasterProblem与RestrictedMasterResult。构造器接收连续MIN Model，
变量域精确为[0,+inf)，校验原模型、非空白名称及所有有限成本/系数/RHS/常数。

输入模型列表与所有可变系数字典均复制；Variable和Bounds是现有冻结记录，其列表
单独拥有。add_column先校验全部输入，再复制完整模型、加入变量与系数，最后一次
替换持久状态。名字精确匹配；未知行、重复名、空白名和坏数值明确拒绝。
空映射/零列合法，异名同向量合法，省略行系数为零，不自动去重或生成初始列。

结果是独立冻结类型，映射复制为MappingProxyType，可用result.dual_values['a']或
dict(result.dual_values)访问。历史结果不随输入字典、后端结果、增列或后续求解改变。
没有把最小化字段装进全局最大化Solution，也没有借用不做符号转换的
MasterProblemResult.from_solution。ColumnCandidate要求定价元信息且拒绝零向量，
本接口没有通过伪造定价结果复用它。

## 3. 数学映射与完整行重建

内部只将目标整体取反：max(-c0-c^T lambda)，原始行名、方向、顺序和RHS不变。
先在本次完整取反输入上用既有check_lp_optimality(...,1e-9)核验每个OPTIMAL，
再逐项输出P_min=-P_max、pi=-y、rc_min=-rc_max=c-A^T*pi。常数整体取反和恢复各一次。
内核已经撤销负RHS标准化，适配层不额外按RHS变号。

最小化LE乘数<=0、GE>=0、EQ自由；当前列rc>=0，互补条件成立时
c0+c^T lambda >= c0+b^T*pi，等值见证支持当前S上的最优性。
完整列域U中的其他列未经定价，本接口不能声明完整主问题或CG已终止。

每次solve都从持久MIN模型创建新的全部原始行MAX模型，另建独立reference副本，
防止测试后端修改输入后绕过核验。只调用LPSolver.solve，不经过CLI、presolve或
后端选择器，不传basis或保存后端cleanup后的标准形、删行集与乘数。
默认每次新建RevisedSimplexSolver，也可显式传TableauSimplexSolver或测试替身。

## 4. 解析真值、原坐标核验与失败路径

主要真值为合同A/B/C的手算模型，验证测试另外直接按MIN原坐标重算可行性、乘数
符号、约化成本、互补、原始目标和对偶目标，不调用生产MAX核验器来代替这些真值。

- A：初始两列成本4/6、常数7，原解(1,1)，P=17，pi=(4,6)，内核P=-17、y=(-4,-6)。
  每次从同一个初始RMP分别加入(1,1)列，成本7/10/12的旧rc=-3/0/2、
  内核改善方向rc=3/0/-2；由P(t)=17+(k-10)t、0<=t<=1给出新最优14/17/17。
  零rc或退化的最终见证只核验有效性，不强制后端选同一解或乘数。
- B：初始a:x=1、b:x=1，min2x。加入成本0的q=(1,0)或(0,1)，两种行顺序、
  两个后端均得x=1,q=0、P=2。手工合法旧pi=(2,0)对第一种q给rc=-2，
  但目标不严格下降。Spy检查两次是不同Model/列表/行字典、全部原始两行和当前所有列；
  永久复用旧删行结果会错得P=0，该回归可直接识别。
- C：min7+2x-z+3w，原解(1,3,2)，P=12，按GE/LE/负RHS EQ/松弛LE顺序，
  pi=(2,-1,-3,0)，rc=(0,0,0)，原始与对偶目标均为12；两个后端通过。
- 真实受限不可行：空列0=1返回INFEASIBLE，显式加系数1/成本3列后得3。
  真实迭代限返回ITERATION_LIMIT；负成本合法零列返回UNBOUNDED，均隔离最优字段。
- 六种非OPTIMAL状态替身均保留状态/消息，目标None、三种数值映射为空，不沿用旧解。
  十二组错误OPTIMAL依据覆盖缺失坐标、非有限值、错目标/原解/乘数/rc和多余坐标，
  全部返回空字段NUMERICAL_ISSUE。每次OPTIMAL核验的spy确认1e-9及完整行/列。
- 输入外部修改、映射后改、失败加列原子性、只读历史快照、精确名字、全零列、
  异名同向量和重复求解均覆盖。篡改输入的后端无法改变reference或持久RMP。

## 5. 实际检查与环境

先按数学合同写新增测试，再做最小实现；没有为新API制造import-error式red。
首次合同指定七文件targeted运行：**213 passed in0.55s**。
初次Ruff只发现一个未使用的dataclasses.replace导入；移除后四个改动Python文件
Ruff通过，未改数学断言、容差或失败保护。

新增测试为接口68项与解析核验16项，共84项；已有129项相关边界/记录/列候选/LP
对偶与核验器检查也在同一targeted命令中通过。不是把213项全部声称为新增测试。

完整`check_quality.py` exit0：**1483 passed in10.45s**，随后Ruff通过，无跳过或警告。
完整既有LP/MIP/CLI、no-op/toy和decomposition记录回归均保留。结构检查通过：
141份合同、138份报告、95个模块、447个本地链接（当前摘要完成链接增加前）。
--write-index、普通结构检查与git diff --check通过。代码/测试在该全量后保持不变，
后续只有文档/真实基线字段收尾，不重复全量。
当前摘要完成链接更新后的结构复查为141份合同、138份报告、95个模块、450个链接，仍通过。

提交前scope检查为13个允许路径（尚未更新当前摘要），没有合同或L0001变化。
九个交付Markdown的UTF-8、围栏、公式定界符及360个本地链接通过；L0002十节体例、
四题稳定编号通过。复核服务记录的三个实现/测试blob与全量被测文件完全一致。
最终scope为合同允许的全部14文件，其中10个Markdown的394个本地链接、UTF-8、
围栏、公式定界符、十节体例、四题编号和真实verified_code再次通过；合同/L0001未改。

使用原检出.venv/Scripts/python.exe，silo.__file__为本检出src/silo/__init__.py；
Python3.13.9、NumPy2.3.5、pytest8.4.2，console PATH指向本检出.venv/Scripts。
未安装/升级依赖、未创建worktree；环境仍继承系统包，不是锁定环境的干净重建。
本步没有新增外部求解器参照或研究规模实验，解析断言不依赖SciPy。

## 6. 教学交付与真实基线

[L0002正文](../../learning/lessons/L0002-restricted-master/README.md)、
[练习](../../learning/lessons/L0002-restricted-master/exercises.md)、
[解答](../../learning/lessons/L0002-restricted-master/solutions.md)保持十节结构，版本0.1.0，
覆盖取反关系、弱对偶符号、三种新列成本、完整行复活、退化、API所有权和结论边界。
四题稳定编号L0002-E01–E04，L0001正文及旧编号未改。

直接提取并执行正文唯一完整Python示例：初始17、旧rc=-3、加列后14，
输入与历史快照均保持。两个后端分别复算四题：E01=[14,17,17]，E02=12，
E03=2，E04=[INFEASIBLE,3,1]。一般弱对偶与完整定价义务由推导说明，有限运行
没有被当成完整列域证明。

verified_code在实际实现提交产生前保持draft/null，随后用真实实现提交
48c242d2fba886807d1230fb7a72b85c3f212b0e更新checked，verified_on=2026-10-19。
当前API说明另存于docs/restricted_master.md，目录/实际导入边界已更新。

## 7. 唯一只读复核

red_team_reviewer按本合同对一个RMP对象进行独立只读数学/测试证据复核，
返回代码方向GO、最终交付条件GO、decision_impact=strengthen。
未发现fatal/major或需要修补的代码级minor；条件为完成full quality、文档、L0002、报告与scope。
它核对实现和解析测试，没有运行实验、写文件或调用其他服务，未读本轮教学正文。
其认可不被计作第二份测试结果；解析真值、生产核验与双后端一致性分别列证据。

## 8. 范围与Git

本任务14个允许路径包括：两个实现入口、新增两个测试文件、三个API/目录文档、
L0002三文件、learning/CATALOG.md、当前摘要、新报告和派生INDEX。
test_decomposition_boundary_smoke未改，保留其下层不反向导入断言。
未改LP/core/modeling/presolve/MIP/CLI/io/外部接口、旧decomposition记录/toy/no-op、
L0001、旧合同/报告、研究资产、阶段/ROADMAP、依赖/build/native或流程规则。

代码与测试提交A为48c242d，学习/报告收尾提交B通过本报告Git历史定位，二者属于
同一原子任务。代码提交后origin差异0/5，只有本任务文档待提交。
沿用仓库既有身份的单次git -c参数，未修改仓库或全局Git身份配置，本轮没有提交失败。
Git mode为local-commit，不push，也不把缓存origin当实时远端证明。

文档收尾首次提交后实际查询的Remote Sync Proof：

- `git status --short`：空，工作区干净。
- `git branch --show-current`：main。
- `git log --oneline -5`：本任务文档收尾、48c242d实现、8a11eff签发、c3704be第1步文档、
  ad62e0f第1步实现；再前一提交为cfb43a8第1步签发。
- `git rev-list --left-right --count origin/main...HEAD`：`0 6`，已知起点4个加本任务2个提交。
- `git push result`：not_attempted。
- `remote_sync_status`：local_ahead_origin。

上述实际查询记录随同一文档收尾提交修订保存，最终哈希通过第1节命令定位并在结束
回执再次核对。origin/main是本地缓存；没有本轮实时远端查询或推送证明。

## 9. 已知数值债与下一步

既有近相关等式x-(1+5e-10)z=1e10、x-z=1e10、max z，精确要求z=0；
第1步审查已复现旧版/当前revised可能误报UNBOUNDED。本步未修内核，也没有将
非最优后端诊断升级为独立射线或完整主问题的认证结论。本轮成功真值用小整数模型。
OPTIMAL仍只覆盖当前列集合及既有绝对容差，一般尺度稳健性未保证。

完成后停止第2步，交silo-solver-1010审查。下一项仅建议小DAG精确定价基线，
需另行批准合同；建议GPT-6 Sol/high，难点为资源可行性、约化成本坐标和完整枚举核对。
本任务没有实现定价、CG循环、热启动、增量维护或后续研究机制。
