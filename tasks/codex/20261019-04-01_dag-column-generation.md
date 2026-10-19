# 第 4 步交付：DAG 列生成闭环与停止依据

## 1. 元信息、授权与实际基线

- ID：20261019-04-01_dag-column-generation。签发前已扫描同日合同/报告，
  TT=01、02、03 已用，本任务使用新 TT=04、RR=01；既有合同保持不可变。
- 类型/风险：L3，现有 decomposition 层内的窄范围算法闭环。
- 用户在第3步验收、已完成更新推送GitHub以及第4步建议后明确回复“交付执行吧”。
  本合同据此授权下述一个原子任务，覆盖实现、测试、L0004、报告和本地提交。
- 来源：tasks/phases/phase_07_decomposition.md 的列接口后续扩展及已验收第2、3步。
  Phase 9 保持 open/parked、native deferred and unapproved；Phase 10 not started。
- 签发/验收：silo-solver-1010，thread 01a1254a-b349-77d0-8c66-d4b711cd511f。
- 唯一实施/文件写入协调：silo-solver开发，
  thread 01a15208-bea9-7030-aacc-95d785e8fa58。
- 工作目录：E:/OneDrive/workspace/codex/silo-solver。
- 签发前 HEAD：c6d0ed1bb5890facb8b36492e27c7a45a80aad4a；main，工作区干净，
  相对缓存 origin/main 为 0/0。此前推送已成功，实时远端曾核对至同一完整哈希。
- 源码基线：DAG pricing 12bfa358850b3fe55b31086c4f98741852973b31；
  RMP 48c242d2fba886807d1230fb7a72b85c3f212b0e；LP ad62e0f。
  c6d0ed1 仅登记第3步验收；本次签发也仅增加合同、更新摘要和INDEX。
- 从本合同签发提交执行；其唯一新增的已知 local-ahead 属于本次授权的交付流程，
  允许直接继续实现，无需为该签发提交再次询问。其他漂移、分歧或无关脏文件须报告。
  签发提交通过 git log -1 --format=%H -- 本合同路径定位。
- Git mode：local-commit。完成后本地提交并停止；本合同不授权推送未来实现。
- Expected report：tasks/reports/20261019-04-01_dag-column-generation_report.md。
- Learning delivery：learning/lessons/L0004-column-generation/ 的 README.md、
  exercises.md、solutions.md，以及 learning/CATALOG.md。已扫描现有L0001–L0003。
- 模型建议：GPT-6 Sol / high。困难集中在列域一致性、退化迭代及对偶下界的停止逻辑；
  建议不代表实际切换，沿用真实会话配置并据实记录。

## 2. 已验收依赖与本步唯一目标

第2步提供经过完整输入最优性核验的最小化RMP快照，每次加列后保留所有行冷重建。
第3步对普通DAG全部s-t路径求最小约化成本，输出原始成本、完整行系数和路径身份。
两步均已验收。第3步全量1742项测试、Ruff、结构检查通过；讨论对话另以5节点
全部1024个向前子图、3组对偶完成3072次独立定价核对，均通过。这些属于既有证据，
不能计作本步自动闭环已经实现或通过测试。

本步唯一目标：连接现有RMP与DAG定价，形成一个带凸组合等式、显式初始路径、
自动增列、失败传播、数值上下界及明确停止原因的可读参考循环。
使用测试中的完整列LP与解析小例核对。完成本步后停止，等待讨论对话验收。

开始前读 AGENTS.md、tasks/README.md、.silo-dos/project_profile.md、
technical_route.md、remote_sync_proof.md、learning/README.md、WRITING_GUIDE.md；
再读 restricted_master.py、dag_pricing.py、现有 column_generation.py 和 logging.py、
docs/restricted_master.md、docs/dag_pricing.md、L0002/L0003及第2、3步合同/报告。
现有通用 ColumnGenerationSolver.solve(Model) 的 NOT_SOLVED 边界保持不变。

## 3. 固定主问题与输入域

定义U为同一 DagPricingProblem 中全部s到t路径。完整主问题为
\[
\min_{\lambda\ge0}\ c_0+\sum_{p\in U}c_p\lambda_p,\qquad
\sum_{p\in U}\lambda_p=1,\qquad
\sum_{p\in U}a_{jp}\lambda_p\ \{\le,=,\ge\}\ b_j.
\]
列成本与行系数完全沿用第3步的基项加弧项定义。

- 指定唯一 convexity_row，其行方向必须EQ、RHS恰为1。
  图的该行 base coefficient 必须恰为1，每条弧的该行系数必须恰为0；
  不用容差接受结构上不满足凸组合约定的输入。
- 其他行为有限数据的固定LE/GE/EQ耦合行。实现不必人为限制行数，
  验收主例采用两条耦合行；不引入另一类主问题框架。
- 行ID唯一、非空白且精确匹配；主问题行名集合与图的 row_names 完全相同。
  行RHS、c0等数值有限，最小化乘数遵循LE非正、GE非负、EQ自由。
- seed_paths 是非空、无重复的完整合法路径序列，路径由弧ID元组定义；
  从s出发逐弧连贯且在t结束。拒绝未知弧、断路、空路径、重复路径。
  初始路径的成本与系数由同一图重构，调用者不另传一套可漂移的列数据。
- 输入记录防御性复制并不可变；外部列表/字典修改不影响问题、已发布迭代或结果。
- 初始RMP可行性由第一次真实求解检查。若当前seed不能支持耦合行，
  返回初始受限主问题失败诊断，不能推断整个U上的主问题不可行。
  本步不实现可行性定价、人工列、Big-M或自动寻找初始可行路径。
- 图固定且有限，凸组合使所有可行lambda有界。后端报UNBOUNDED时停止并保留诊断，
  不发布完整主问题无界结论。近相关等式误报状态属于已知底层数值债，本步不修LP。

只支持连续路径权重和普通DAG加性列域；资源预算、时间窗、路径服务规则、整数列选择、
分支约束、cuts、Benders、branch-and-price均不在本合同范围。

## 4. 路径身份、最小接口与结果所有权

新增 src/silo/decomposition/dag_column_generation.py，建议提供下列窄接口；
可调整私有实现和类型标注，不扩大为通用插件或求解器注册框架：

~~~text
DagMasterRow(name, sense, rhs)
DagColumnGenerationProblem(graph, rows, convexity_row, seed_paths,
                           objective_constant=0)
solve_dag_column_generation(problem, *, solver=None,
                           tolerance=DEFAULT_TOLERANCE, iteration_limit=100)
    -> DagColumnGenerationResult
~~~

DagMasterRow 是无变量系数的冻结行描述，复用现有 ConstraintSense。
solver 仅作为现有RMP的原生LP后端参数，默认沿用RMP的Revised；Tableau用于交叉核对。
tolerance有限且为正；iteration_limit为正整数，拒绝bool和非整数。
原生生产代码继续遵守外部solver边界，不依赖外部求解器。

- 权威列身份为完整 arc_ids 元组，区分平行弧及成本/向量相同的不同路径。
  RMP变量名采用确定、无碰撞的内部编号；禁止靠分隔符拼接弧ID去重。
- 维护变量名到路径元组的只读注册表，初始列与新增列使用同一协议。
  最终primal_values通过注册表可还原为路径权重。不得访问RMP._model等私有状态。
- 同一输入重复运行结果确定。行、弧或初始列重排后目标/可行性结论应一致；
  退化下不要求不同后端或排列产生相同对偶、相同新增路径顺序。
- 结果与逐轮记录采用独立、不可变快照，包含本次停止原因、当前已求解列注册表、
  最后有效RMP快照及轮号，逐轮定价状态/rho、原始目标U、对偶目标D、数值下界L、
  数值差距、定价候选及实际接受列身份。字段可按少量专用冻结记录组织。
- 结果层使用独立CG停止枚举，至少区分 TOLERANCE_REACHED、ITERATION_LIMIT、
  MASTER_FAILURE、PRICING_FAILURE、NUMERICAL_ISSUE。提供清楚message及失败轮号。
  不把CG停止包装成全局 Solution，也不直接赋 SolverStatus.OPTIMAL。
  最后RMP的OPTIMAL仅描述当前列集合。
- 只有同轮RMP与完整定价均有效时，才发布该轮数值界字段；
  失败字段用None，不用0填补。若保留历史有效快照，必须带其轮号与有效性范围，
  不得把旧定价下界伪装为失败轮的新结果。最终采用最后一个已求解的列集合。

既有 ColumnCandidate、通用日志记录、toy驱动和占位solver均保持原行为。
必要的CG专用状态放在新模块中，不改现有公共CLI/schema或core状态体系。

## 5. 自动循环、失败与迭代上限

一次迭代定义为：对当前全部列求解RMP，使用本轮经核验的原始最小化pi对全部U定价，
然后作停止或加一列的决定。最多执行iteration_limit个这样的轮次。

1. 从合法seed构建MIN模型，加入全部固定行及c0；用现有RMP冷求解。
   RMP非OPTIMAL立即MASTER_FAILURE，保留其实际status/message；
   不用空对偶继续定价，不自行把非最优状态升级为完整主问题结论。
2. price_dag使用该轮pi、同一个固定图和同一个tolerance，始终覆盖全部U。
   NUMERICAL_ISSUE等失败为PRICING_FAILURE。已有合法seed却出现NO_PATH表示输入/
   依赖契约矛盾，停止诊断；不得以空域作为成功终止依据。
3. 接收OPTIMAL候选前，独立从公开图数据检查路径合法性、原始成本、完整行系数及
   c-a^T*pi与返回字段一致，沿用既有绝对DEFAULT_TOLERANCE作数值一致性核对，
   同时要求改善分类一致。后续真正加入RMP的成本/系数必须使用重构出的原始数据，
   rho采用该重构rc；不能把容差内漂移的返回列字段写入主问题。
   坏字段、非有限累计或分类冲突须NUMERICAL_ISSUE。可用math.fsum和小型私有路径重构函数；不改定价器、不调用其私有重建助手。
4. 有限rho和U/D/L检查通过后，按第6节判定停止。
   rho<-tolerance且候选未在注册表中时，显式RMP.add_column加入恰好一列，
   下一轮重新求解；不能把同一pi继续用于另一轮。
5. 仍显著负约化成本的候选已经存在时，返回NUMERICAL_ISSUE，报告路径与rho；
   禁止把“重复候选”当作完整域收敛，禁止跳过最佳路径后启发式挑另一条。
   已有路径在最终定价中为零或容差内小负rc，则按第6节正常核对。
6. 当前目标与上轮相同不构成停止理由；退化时新列可能先以零权重进入。
   不做提前停滞规则、缓存或路径黑名单。
7. 若最后允许轮次仍需要改善列，返回ITERATION_LIMIT；
   不加入没有下一轮预算可求解的新列，避免结果注册表、primal和界属于不同列集合。
   最后一轮已满足停止条件时正常TOLERANCE_REACHED，不能被limit覆盖。

非法用户输入明确ValueError/TypeError；正常后端/定价失败走上述诊断。
不要用捕获所有异常的方式把编程错误伪装成成功、迭代上限或无改善。

## 6. 精确算术下的界、浮点发布和停止条件

本轮已求解列集为S，U是全路径域；为避免同字母歧义，下文用P表示原始目标值：
\[
P=c_0+\sum_{p\in S}c_p\lambda_p,\quad
D=c_0+\sum_{j\in J}b_j\pi_j,\quad
\rho=\min_{p\in U}(c_p-a_p^\top\pi).
\]
完整行集合J包括凸组合行。实现/日志中的数值上界字段对应P。

在精确算术下，当前原始解可行时，给未出现路径赋零得到完整主问题可行解，P是上界。
当pi满足行乘数符号，令delta=min(0,rho)，只把凸组合行乘数改为
pi_conv'=pi_conv+delta，其他行不变，则每条路径的新约化成本为
rc_p'=rc_p-delta>=0；凸组合行是等式，乘数平移不破坏行符号。
因此完整主问题的对偶可行目标为
\[
L=D+\min(0,\rho)\ \le\ z^\star\ \le P.
\]
必须说明：完整路径最小化、每条路径凸组合系数1、RHS1、当前原始可行及pi符号正确，
共同支持该推导。不能把一般RMP的负rc直接加到目标上当作通用下界。

- 使用真实D计算L，不能未经检查直接把D替换为P；RMP浮点核验允许微小原对偶误差。
  同轮数值gap=P-L=(P-D)-min(0,rho)。不遗漏c0，也不把c0加入路径rc。
- 逐轮从已知行RHS/当前列与快照计算并核对P、D及有限性；不只复制上轮缓存。
  与RMP发布目标的一致性沿用DEFAULT_TOLERANCE，异常保守NUMERICAL_ISSUE。
- 发布字段明确命名或文档标注 numerical_upper_bound、numerical_lower_bound、
  numerical_gap。它们是现有浮点核验与定价支持的数值估计；
  形式化上下界定理要求上述精确条件，本步不提供区间算术或严格舍入证明。
- 若计算得到L>P或任何非有限值，返回NUMERICAL_ISSUE；不把负gap强行归零，
  不把L裁到P，不伪造上下界顺序。该参考实现允许保守拒绝极小舍入矛盾。
- 仅当rho>=-tolerance且0<=P-L<=tolerance时，TOLERANCE_REACHED。
  必须同时核对定价和真实gap，不能只看is_improving=False。
  rho在容差内但gap过大时，返回NUMERICAL_ISSUE并解释原对偶误差；
  当前接口下没有可合法加入的显著改善列，不能空转到limit或宣称精确最优。
- 不要求每轮当前L单调；退化改变pi可能使当前L下降。本步可仅记录各轮L，
  不新增跨轮“最佳界”缓存体系。P在精确可行扩列下非增，有限精度比较按实际误差说明。
- 只在已声明图域、行约定及数值条件下解释停止；容差内小负rho意味着可能存在
  微小改善。文档、例子、报告禁止将TOLERANCE_REACHED写成一般的严格全LP最优证明。

## 7. 区分性主例：目标不动仍须继续

图仅有s、t，四条平行弧分别形成四条路径。
base_cost=0，base_coefficients={conv:1}；弧数据如下，省略系数为0：

| 路径/弧ID | cost | R系数 | C系数 |
|---|---:|---:|---:|
| d1 | 4 | 1 | 1 |
| d2 | 6 | 0 | 0 |
| o12 | 1 | 1 | 0 |
| o21 | 2 | 0 | 1 |

行conv=1、R=1/2、C=1/2，均EQ；c0=-3。seed为d1、d2。
seed解各1/2、P=2。任意只加o12或只加o21的RMP仍为P=2；
两条均加入后o12=o21=1/2，P=-3+(1+2)/2=-1.5。

独立解析：令lambda_d1=t，则lambda_d2=t，
lambda_o12=lambda_o21=1/2-t，0<=t<=1/2，目标=-1.5+7t。
所以完整主问题唯一权重解在t=0。该例同时检验分数权重、常数项、退化增列和自动重求解。

签发前仅用既有API做三次显式RMP/定价桥接，两个原生后端均得到
P=2 -> 2 -> -1.5，rho=-4 -> -7 -> 0，先o21再o12。
它验证例子与当前依赖契约；本步生产循环尚未实现。
验收要求自动循环得到正确解并跨过目标不变的一轮；
不把特定后端的退化对偶或加入顺序固定为一般数学约定。
本例当前L依次为-2、-5、-1.5，说明当前下界可暂时变松。

## 8. 测试与完整列对照

### 8.1 自动闭环与独立完整列LP

tests/verification 中独立DFS枚举小图全部s-t路径，直接从原始数据生成所有列，
构建完整MIN LP并用现有原生LP适配求解；枚举只属于测试。
不得调用新控制器的私有路径重构、去重或建模助手构造oracle。
主例再用第7节解析式独立核对，避免CG与完整LP同用底层LP造成伪独立。

- 第7节主例在Revised和Tableau均通过，最终完整行可行、路径权重和目标正确；
  每轮rho、P、D、L、gap按直接公式复算，界与解析z*比较。
- 除主例外至少8个固定小模型，覆盖真实多弧路径、不同可行seed、LE/GE/EQ耦合行、
  负/零路径成本、非零基成本/基系数、c0正负、成本相同而身份不同的路径。
  报告写清模型族和运行组合，不能只把8个输入排列当8个不同模型。
  选取可手算或独立有限枚举的模型，避免为本步引入通用精确LP顶点枚举框架。
- 同一模型对两个后端，以及至少一组图/行/seed排列核对最终目标和可行性；
  不要求退化乘数或轨迹完全一致。不宣称有限模型族证明所有CG正确。
- 凸组合单行模型也覆盖，但不能用它代替耦合主例。
  某个seed已包含全部路径时应一轮停止，最后最优路径可以已经在注册表。

### 8.2 容差、退化、身份与失败

- 两条平行弧成本1与1-5e-10，只有conv=1，seed用成本1的路径，
  c0=0，默认tolerance=1e-9。第一轮rho约-5e-10，P=1，
  L约1-5e-10，正gap约5e-10，TOLERANCE_REACHED；
  用Fraction/解析真值确认尚有小改善，不能标成严格零gap或精确最优。
  完整LP本身也有容差，不能用其近似目标替代此处的解析真值。
- rho恰在阈值边界、略内/略外，以及有RMP原对偶残差时的gap门控；
  负gap/非有限P、D、L必须诊断。必要时在测试中monkeypatch依赖返回值，
  注入记录须明确属于合成故障，不能冒充正常后端自然可达证据。
- 第7节iteration_limit=1、2时均ITERATION_LIMIT，所有返回列均已经真实求解，
  不追加未求解列；limit=3应正常停止。非法limit/tolerance拒绝。
- 已有路径仍显著负rc、坏路径/成本/系数/rc/改善字段、价格失败和异常NO_PATH；
  不增加公共任意pricer插件，可在测试模块局部monkeypatch。
- 初始RMP不支持耦合行、原生非OPTIMAL状态、后端伪造坏OPTIMAL证据被RMP拒绝；
  都要保留诊断范围。至少一个例子满足seed不可行、完整路径主问题却可行。
- 路径ID含分隔字符、平行弧、相同向量不同路径、重复seed、坏连通性；
  行集合不匹配、凸组合行/基项/弧系数/RHS错误及非有限输入拒绝。
- 历史问题、列注册表、结果及迭代记录的所有权；连续求解不同输入不串状态。
- 现有通用ColumnGenerationSolver、toy接口及跨层依赖边界保持原有检查通过。

## 9. 允许改动与范围锁

唯一允许：
- 新增 src/silo/decomposition/dag_column_generation.py；
  src/silo/decomposition/__init__.py仅导出本步窄接口。
- 新增 tests/unit/test_dag_column_generation.py、
  tests/verification/test_dag_column_generation_oracles.py。
- 新增 docs/dag_column_generation.md；docs/README.md加入口，
  docs/development_layout.md仅补充真实入口/依赖与当前有限能力。
- 新增 learning/lessons/L0004-column-generation/README.md、
  exercises.md、solutions.md；更新 learning/CATALOG.md。
- .silo-dos/project_profile.md仅更新本步实际状态、基线、限制与建议。
- 本合同匹配的新报告、派生 tasks/INDEX.md。

禁止改动LP/core/modeling/presolve/mip/cuts/CLI/io/外部接口、restricted_master.py、
dag_pricing.py、既有ColumnCandidate/日志/toy/placeholder、L0001–L0003、
旧合同/报告、notes/研究探针/资产、ROADMAP/阶段文件/其他.silo-dos门控、
任务规则、Skill/Agent、依赖/build/native。禁止生产全路径枚举、热启动、
增量定价、资源约束定价、并行定价、一般可行性阶段、性能对标与速度主张。
发现需要超范围修改，提供最小缺口与证据，停止扩展；不借闭环任务顺便修LP。

## 10. Learning delivery：L0004｜列生成闭环、退化与最优性差距

遵循已有十节编排，新建稳定篇目并链接L0002/L0003。
讲清完整主问题与RMP关系、显式seed和列身份、pi每轮更新、路径定价与自动增列、
第7节退化手算、凸组合乘数平移下界及其假设、真实原对偶差距、
容差内停止与严格最优的区别、初始不可行和失败传播、完整列对照的证据边界。

至少四道稳定题L0004-E01起及完整解答，分别涵盖：
耦合主例逐轮/解析权重；对偶平移证明与缺少conv条件的失败；
小负rc及非零P-D下的gap判断；重复列/初始不可行/资源定价的研究辨析。
正文给完整可执行自动循环例，真实运行并核对结果。

研究价值限定为可审查的CG参考基础与后续增量研究的基线。
未来特色方向需要明确新结构和对照证据；普通DAG CG实现本身不构成论文创新，
本步也没有承诺资源可行路径、VRP、工业规模或性能优势。

verified_code填写真正包含本控制器的完整实现提交；可先提交代码/测试为A，
再将该哈希写入学习材料并提交文档/报告为B，同属一个原子任务。
实现提交前保持draft/null，不引用未来自身提交或旧定价提交冒充新代码核验基线。

## 11. 执行、检查、验收与停止

1. 记录实际HEAD/status/branch/cached origin差异、解释器、silo.__file__；
   核对签发提交及本合同明确覆盖的已知ahead，保持唯一文件写入协调者。
2. 先落地有区分性的行为检查，再实现小型参考循环；
   不以缺失新模块的import错误充作算法red证据，记录真实失败/修复。
3. 需要时仅做一次边界明确的只读数学/证据复核；主线程负责实现和实际运行。
   签发阶段尝试的独立数学服务因模型容量失败，未提供审查结论；
   本合同的公式由签发主线程推导，不能在报告中把失败调用计作独立复核通过。
4. 完成API、L0004、报告与INDEX；保留不可变合同。
5. 使用现有环境，从项目根执行：

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_column_generation.py tests/verification/test_dag_column_generation_oracles.py tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

运行正文完整代码及有限习题，核对UTF-8、链接、围栏、公式、十节体例、稳定题号、
真实verified_code与实际核验记录。代码稳定全量通过后，纯文档收尾不必重跑全套；
后续代码改变、失败或新增实质疑点时补跑相应检查。

验收要求：主例自动跨过P不变的一轮并达到-1.5；双后端与独立完整列LP一致；
下界推导假设和数值字段诚实；小负rc/原对偶残差/失败/limit/身份/所有权通过；
既有边界与全量质量通过；L0004实际核对；diff仅允许文件；本地提交后停止。
若发现模型/界推导不成立、数值逻辑无法诚实表达、必须改禁区或发生无关并发写入，
保留证据、报告最小阻塞，不进入第5步或其他研究方向。

## 12. 报告与结束回执

报告记录：实际起点、输入域/API、路径身份、循环和limit计数、每种失败的结论范围；
P/D/rho/L/gap推导及浮点局限；第7节真值和真实轨迹；
完整列枚举独立性、至少8个其他固定模型及双后端/排列组合的实际数量；
故障注入与自然可达例分别记录；测试/质量/结构/教学检查及真实失败修复；
变更文件、scope偏离、只读服务实际范围与状态；实现/学习提交、剩余问题及下一步仅建议。

Git字段须含status、branch、log -5、cached origin差异、push not_attempted、
remote_sync_status。仅用单次命令Git身份参数，不改全局配置。
报告自身提交通过
git log -1 --format=%H -- tasks/reports/20261019-04-01_dag-column-generation_report.md
在提交后定位，避免自引用哈希。

最终回执给出功能、验证、L0004路径、限制、本地提交和未推送状态。
完成一个原子任务后停止，等待silo-solver-1010审查；
不自动执行第5步，不向其他对话发消息，不把下一步建议当作授权。
