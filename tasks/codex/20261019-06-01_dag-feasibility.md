# 第 6 步交付：CG 初始可行性恢复与可行性定价

## 1. 元信息、授权、实际基线

- ID：20261019-06-01_dag-feasibility。已扫描同日合同/报告，TT=01–05已用，
  本任务为新TT=06、RR=01，不修改旧合同/报告。
- 类型/风险：L3，现有DAG列生成支持域内新增独立可行性恢复能力，不改变项目阶段。
- 用户在第5步验收、状态汇总和下一步建议后明确要求“开始交付下一步的工作”，
  批准本合同一个原子任务的实现、测试、L0005、报告及本地提交。
- 来源：tasks/phases/phase_07_decomposition.md 后续扩展、第4/5步及第5步验收建议。
  Phase 9 open/parked、native deferred and unapproved、Phase 10 not started保持。
- 签发/验收：silo-solver-1010，thread 01a1254a-b349-77d0-8c66-d4b711cd511f。
- 唯一实施/文件写入协调：silo-solver开发，
  thread 01a15208-bea9-7030-aacc-95d785e8fa58。
- 工作目录：E:/OneDrive/workspace/codex/silo-solver。
- 实际签发前HEAD：b8864585a230604509f4e0e318222bd9bcbac214，main、工作区干净，
  cached origin/main...HEAD=0/4。四个已知本地提交依次8ee397e、15b403b、f0cc01a、
  b886458，远端上次即时核对为f0c5f31；本轮没有新push授权。
- 用户在上一轮已获知这四个本地提交未推送，随后批准本步。继续授权覆盖这四个提交
  及本次仅含合同/摘要/INDEX的签发提交；不必为已知ahead再次询问。
  其他漂移、分歧或无关脏文件须保留现场并报告，不覆盖/重置。
- 执行从本合同签发提交开始，用git log -1 --format=%H -- 本合同路径定位。
- 源码基线：CG 15b403bcd7322a0b25ebb5380539dc5c4002c4ac，
  DAG定价12bfa35、RMP48c242d、LP ad62e0f。第5步全量2331项与Ruff已验收，
  讨论对话另512次解析模型补查通过；这些不代替本步新实现验证。
- Git mode：local-commit，完成后本地提交并停止，不push。
- Expected report：tasks/reports/20261019-06-01_dag-feasibility_report.md。
- Learning delivery：新建learning/lessons/L0005-cg-feasibility/的README.md、
  exercises.md、solutions.md，更新learning/CATALOG.md；已扫描L0001–L0004。
- 模型建议：GPT-6 Sol / high，困难为辅助目标、原始行乘数、固定人工列的下界与
  移除后的可行见证之间的一致性；建议不代表实际切换配置。

## 2. 唯一目标与支持范围

新增独立恢复器：输入现有DagColumnGenerationProblem，seed至少含一条合法路径，
允许seed不满足耦合行；通过辅助主问题和全域可行性定价补列，再移除人工变量核验原行，
成功后返回保留原图/原成本/c0的feasible_problem，供调用者显式交给既有CG。

本步完成“恢复可行初始列”一个主问题。现有solve_dag_column_generation及其
不支持不可行seed的原行为保持；恢复器不自动调用原目标CG，不新增通用两阶段包装器。
测试/教学明确展示restore -> 检查状态 -> 既有CG的两次调用。

列域仍为普通固定DAG全部s-t路径、连续lambda>=0、conv等式sum(lambda)=1；
其余固定行为LE/GE/EQ。复用现有输入验证、路径元组身份和有限数据约定。
至少一条合法seed保证conv可满足；空seed、空路径域、自动找首条路径、本任务之外的
资源/分支/整数列规则均不扩展。原始行单位不同会影响总违背量，本步固定单位罚权，
不新增行缩放、归一化或用户可配置罚权。

开始前读AGENTS.md、tasks/README.md、project_profile.md、technical_route.md、
remote_sync_proof.md、learning/README.md、WRITING_GUIDE.md；再读RMP、DAG定价、
现有CG、相应API、L0001/L0002/L0003/L0004及第4/5步合同/报告。

## 3. 辅助主问题：保持conv，给耦合行添加违背量列

记K为除conv之外的全部固定行。保持原行名、方向、RHS与完整行集合：

| 原行 | 辅助行 | 新非负变量 |
|---|---|---|
| LE: A_j lambda <= b_j | A_j lambda - v_j <= b_j | v_j |
| GE: A_j lambda >= b_j | A_j lambda + u_j >= b_j | u_j |
| EQ: A_j lambda = b_j | A_j lambda + u_j - v_j = b_j | u_j、v_j |
| conv: sum(lambda)=1 | 原样保留 | 无 |

辅助目标F是全部u/v之和，每个人工列单位成本1，conv系数0，仅在其对应行系数+1或-1。
全部真实路径成本为0，辅助c0=0。所有人工列从起点固定在辅助RMP中，后续只加真实路径列。
人工列不拥有弧路径身份，变量名与真实列使用无碰撞内部命名空间，并保留人工名到行/符号
的只读映射，不能把它们混入路径注册表或最终seed。

必须给出精确算术依据：任一合法seed取权重1满足conv，各耦合行可由上述u/v补足，
所以辅助RMP可行，F>=0且存在有限目标点；完整辅助LP最优F*=0当且仅当原完整主问题可行。
LE/GE/EQ的最小人工量分别是超出量、短缺量和绝对残差。有限完整路径域和连续conv组合
保证最小值可达。原LP内部Phase I处理固定列集，当前辅助CG负责从U发现缺失列。

辅助最小化pi仍按原始行坐标，LE非正、GE非负、EQ自由。人工列对偶约束为
LE的-1<=pi_j<=0，GE的0<=pi_j<=1，EQ的-1<=pi_j<=1。
这些约束与真实路径列约束都须核对，不能只检查原行乘数符号。
按既有DEFAULT_TOLERANCE检查每个人工列1-a_art^T*pi>=-DEFAULT_TOLERANCE，
并核对其真实系数/单位成本，不能仅相信列名或返回的reduced_cost字段。

## 4. 零成本图、全域定价与辅助下界

从原图构造独立冻结视图：所有弧cost和base_cost设为0，节点/弧ID、端点、全部行系数
及base_coefficients保持。原graph及其成本不改写；原目标常数只留待最终交接。
用现有price_dag和本轮辅助RMP乘数求
\[
\rho=\min_{p\in U}(-a_p^\top\pi).
\]
使用整个U，包括当前真实列；不能用原始路径成本定价、避开已有路径或按人工列生成路径。

接收候选前从公开图数据独立核对完整路径、系数、零原始辅助成本和rc/改善标志，
沿用既有DEFAULT_TOLERANCE的一致性保护；实际加入RMP的成本强制0、系数用重构原值。
合法seed下出现NO_PATH为依赖矛盾，不构成成功或原问题不可行证明。

令D=sum_j b_j*pi_j，包含conv，delta=min(0,rho)。只平移pi_conv'=pi_conv+delta：
所有真实列conv系数1，移位rc=rc-delta>=0；人工列conv系数0，rc保持不变。
因此当原pi满足符号及人工列对偶约束时，L=D+delta是完整辅助LP下界。
本步不能直接把“所有列conv系数都是1”的旧证明套到混合人工/真实列；须分别处理两类列。

数值复算F、D、rho、L、原始差F-L，并按第5步的原项求和保存
\[
g=\mathrm{fsum}(\{c_i x_i\},\{-b_j\pi_j\},-\delta),\quad
A=\mathrm{fsum}(\{|c_i x_i|\},\{|b_j\pi_j|\},|\delta|),\quad
\eta=32\,\mathrm{ulp}(A).
\]
这里c_i包括人工成本1和真实成本0，不含原c0。负g只在eta<=tolerance且-g<=eta时接受；
非负g按正常规则；正向gap/rho门槛不加eta。全部原值保留，32仍为工程局部尺度，
不是一般LP误差界或严格不可行认证。不得为了新任务更改系数/全局容差。

生产仅使用既有公开RMP、定价/模型对象和标准库；不调用其私有目标/重建助手。
允许新模块内少量局部参考求和/重构代码，避免为共享助手改动被禁旧模块。

## 5. 状态机、原始行复核与预算

建议接口位于src/silo/decomposition/dag_feasibility.py：

~~~text
restore_dag_feasibility(problem: DagColumnGenerationProblem, *,
                       solver=None, tolerance=DEFAULT_TOLERANCE,
                       iteration_limit=100) -> DagFeasibilityResult
DagFeasibilityStatus:
    FEASIBLE_SEED_FOUND / POSITIVE_VIOLATION_BOUND / ITERATION_LIMIT /
    MASTER_FAILURE / PRICING_FAILURE / NUMERICAL_ISSUE
~~~

输入/参数规则沿用现有CG；solver默认Revised，可交叉Tableau。最多执行iteration_limit次
辅助RMP冷求解；每轮加入至多一条真实路径。最后预算轮不加入未经后续求解的新列。

1. 每轮先求解辅助RMP，核对返回值与自有完整列/人工列元数据、原始行、F、坐标、
   有限性、非负及对偶证据。非OPTIMAL为MASTER_FAILURE，保留实际status/message；
   辅助LP理论上可行且F下界0，后端INFEASIBLE/UNBOUNDED仍只是诊断。
2. 若F < -DEFAULT_TOLERANCE，数值失败；F在[-DEFAULT_TOLERANCE,tolerance]内
   （含负零/微小负值）时，进入独立原始行复核，不凭小罚值直接成功。
3. 原始行复核：移除全部人工变量，用当前全部真实路径、完整原始行、真实变量下界0、
   零目标且常数0另建RMP并冷求解。只有该次OPTIMAL经过既有最优性核验，
   且原始行/权重按既有DEFAULT_TOLERANCE独立复算通过，才FEASIBLE_SEED_FOUND。
   保留实际真实权重，不剪小值、不归一化、不删原行来制造可行。
   复核非OPTIMAL或失败为NUMERICAL_ISSUE，记录failure_stage=original_validation及
   实际RMP诊断；不输出完整主问题不可行结论，不自动尝试Phase II。
4. 复核成功：feasible_problem只替换seed_paths为全部已生成真实路径的稳定无重复元组；
   保持原graph成本/基项/行坐标、rows方向/RHS/顺序、conv名称和objective_constant。
   同时返回无人工变量的零目标原始可行见证。原目标优化由调用者显式交旧CG完成。
   本分支不需要定价即可依原始见证成功，rho/完整域下界字段应为空，不假装执行过定价。
5. 若F>tolerance，用第4节全域零成本定价并核对辅助下界/数值gap。
   rho<-tolerance的新路径则加列，目标不变仍继续；显著负rc已有路径为NUMERICAL_ISSUE。
6. rho>=-tolerance时：g超容差或局部一致性失败为NUMERICAL_ISSUE；
   只有同时L>tolerance、g<=tolerance且一致性通过，才POSITIVE_VIOLATION_BOUND。
   F>tolerance但L<=tolerance无法形成分离判据，返回NUMERICAL_ISSUE，
   不以受限正罚值或False改善标志直接宣告完整不可行。
7. POSITIVE_VIOLATION_BOUND仅表示本轮数值证据给出完整辅助LP正违背下界；
   精确算术下正下界可证明原问题不可行，当前浮点状态不发布全局SolverStatus.INFEASIBLE
   或严格Farkas见证。其他坏候选/算术、定价失败和limit按独立诊断保留。
8. 最后一轮若已经F小且原始复核通过，正常成功；若仍需新路径则ITERATION_LIMIT。
   原始行复核是额外LP调用，不消耗辅助轮预算；分别报告auxiliary_solve_count与
   validation_solve_count，后者本步最多1，真实后端调用总数可核对。
   不使用旧pi或验证阶段的零目标pi替代原目标阶段的乘数。

tolerance控制辅助目标阈值/定价/差距；原始可行见证仍用现有1e-9绝对核验，
不把自定义更小tolerance解释为新的全局行可行精度承诺。

## 6. 最小结果与证据归属

冻结记录可作少量专用dataclass，名称/私有细节可调整，至少保存：
- 状态、message、failure_iteration/failure_stage、实际两类LP调用计数。
- 逐轮辅助RMP快照、当前已求解真实列注册表、固定人工名到行/符号映射、
  实际接受路径及定价/原始行复核快照；原始元组身份与内部变量名分开。
- 当前受限罚目标F；只有全域定价及界检查通过才发布本轮D/rho/L/g_raw/g/eta，
  F小直接复核成功的轮次不伪造这些全域量。
- 最后有效辅助RMP及其列集/轮号；后续失败尝试记录自己的注册表，
  顶层可保留带轮号历史快照，但不能把它当成本轮原始可行见证。
- 仅FEASIBLE_SEED_FOUND允许非None的feasible_problem与原始feasibility_witness；
  POSITIVE/NUMERICAL/MASTER/PRICING/LIMIT状态二者一律None。
  witness和辅助master明确区分，前者只含真实路径变量、零目标、完整原始行。
- 失败轮的新全域界/差距均None，不能填0或用上轮代替。
  输入/输出/映射/历史快照防御性复制只读，后续增列或外部修改不得反写旧结果。

不返回全局Solution，不修改既有CG结果/状态体系。路径种子按元组在阶段间映射，
各阶段变量名只是内部坐标，不能靠同名假设错误接续。

## 7. 三个固定手算例及桥接

### 7.1 恢复目标与原目标明确分离

conv=1，r>=1/2，路径p0/p1/p2的r为0/1/2，原成本0/4/10，原c0=7，seed仅p0。
图base_cost=1，弧成本-1/3/9，base conv=1。辅助图的base与所有弧成本都改0。
初始人工u=1/2，F=1/2，pi=(conv:0,r:1)；零成本定价rho=-2选p2。
加p2后F=0，原始行零目标复核通过。返回seed为p0/p2，原成本与c0完整保留。
把恢复结果交既有CG：原目标先9.5，定价补p1后到9；
解析最优lambda0=lambda1=1/2，lambda2=0。

误把原成本放入恢复定价时，候选rc为0/3/8，会漏掉必需的p2；测试必须能识别。
辅助可行权重未必唯一，不固定恢复阶段必须返回某一组最优权重。

### 7.2 完整域确有正违背量

同图改r>=3，完整域最大r=2，所以最小违背F*=1。
seed辅助目标3，补p2后为1，末轮pi=(conv:-2,r:1)、rho=0、D=L=1。
必须输出POSITIVE_VIOLATION_BOUND、无feasible_problem，不因初始F=3提前停止。
数学解析量与浮点状态的结论范围分别写清。

### 7.3 恢复阶段的退化

conv=1，R=1、C=0，两条耦合行均EQ。
seed路径(0,0)，另两条真实路径为above=(1,1)、below=(1,-1)，原成本可取0/4/2。
只加入above或below之一时，辅助最小违背量仍1；两列都有后各1/2得到F=0。
自动循环应跨过F=1 -> 1 -> 0；limit=1/2只返回已求解列，limit=3完成原始行复核。
两条路径的等价加入顺序不固定。签发前已用既有公开API显式桥接，
两后端均核对了上述三例（含原目标9.5 -> 9）；新恢复器尚待实现。

## 8. 独立完整辅助LP与81模型/648次解析族

新增tests/verification/test_dag_feasibility_oracles.py，独立DFS枚举图全部路径，
从原始公开数据构造完整辅助LP及无人工的原目标LP，不用生产恢复器/CG私有助手。
完整LP比较共用原生后端，必须另有下面的Fraction解析真值，不重复计作独立证明。

同一四路径域(i,j)属于{0,1}^2，conv=1。两条坐标行各自选择：
方向LE/GE/EQ，未平移RHS为-1/4、1/2、5/4，得到每行9种设置、两行81模型。
R/C基系数1/8、-1/4，RHS也同移；首弧加i、末弧加j，conv基1/弧0。
行设置按方向(LE,GE,EQ)再RHS(-1/4,1/2,5/4)排序，
模型索引m=9*R设置索引+C设置索引，从0起。
原成本矩阵偶m取(0,4,10,7)、奇m取(3,-2,1,-4)，按00/01/10/11排列；
base_cost偶m为1、奇m为-2，c0偶m为5、奇m为-5。
图s->left_i->right_j->t：首弧成本(i+1)/2，末弧-(j+1)/4，
中弧成本c_ij-base-(i+1)/2+(j+1)/4；ID为start/end/middle加坐标。
节点序(right1,s,left0,t,right0,left1)，图行(conv,R,C)，主行(conv,R,C)。

seed仅00或仅11，各配原/反序（同时反转节点/弧/图行/主行）及两后端，共648次。
独立解析：完整conv组合可实现单位正方形内任意坐标，因此辅助最优为两行最小违背量之和：
\[
h_{\rm LE}(b)=\max(0,-b),\quad h_{\rm GE}(b)=\max(0,b-1),\quad
h_{\rm EQ}(b)=\max(0,-b,b-1).
\]
每行9设置中5个可行，故25个完整可行模型、56个完整不可行模型；
乘8组合，预期200次FEASIBLE_SEED_FOUND、448次POSITIVE_VIOLATION_BOUND。

每次验收包括：
- 原始路径/行、人工列符号与成本、完整辅助LP目标与Fraction F*一致。
- 每个正下界末轮，用Fraction对实际返回pi独立复算全部真实路径和所有固定人工列rc；
  确认人工列从起点存在且conv平移不改变它们，严格平移下界<=解析F*，数值L>tolerance。
  精确L用原始RHS/系数和返回pi的Fraction乘积重新构造，区别于直接将已舍入的浮点L转Fraction；
  浮点L与精确量另作有限精度比较。若返回pi存在舍入导致的精确约束违背，记录原因与浮点边界，
  不投影/修改pi伪造通过。
- 每个可行模型移除复核的完整行/非负权重独立核对；feasible_problem的seed恰为全部生成真实列，
  原graph弧/基成本/系数/行名、原rows和c0深层身份保持，无人工变量泄漏/重复/名称碰撞。
- 200个可行结果再显式调用既有原目标CG，并与独立完整原目标LP比较；
  第7.1节手算9为额外独立原目标依据。
- 每轮F/D/rho/L/g/eta按实际原始数据复算，区分真实权重与人工权重；
  报告两类终态数量、辅助轮数、复核LP次数、两后端/排列分布。
- 数据/容差固定；不能改罚权、扩大32、删行/路径、改原目标刷过预期数量。
  若确有底层数值债，保留证据，禁止超范围修内核。

## 9. 区分性边界和失败测试

新增tests/unit/test_dag_feasibility.py，至少覆盖：
- 三个主例自动恢复/正界/退化；原始可行seed、只有conv无耦合行、LE负RHS、
  EQ两侧偏离、混合行、平行弧、非零系数基项、原成本正负及原c0平移不污染辅助目标。
- 输入沿用现有合法性，坏problem/参数明确拒绝；人工名/行名/路径弧ID含分隔字符不混淆，
  相同向量不同路径保持身份，冻结快照与输入所有权。
- F小但移除人工后不能通过：自然例只有r=0路径却要求r>=5e-4，tolerance=1e-3，
  辅助F小于用户阈值，原始复核仍失败；不得输出feasible_problem。
- 无改善且g在容差内，但F>tolerance、L<=tolerance的边界，必须数值诊断。
  可用明确合成RMP快照隔离该分支，不能把它宣称自然后端可达。
- 小负rc、正/负g局部边界、eta>tolerance例外禁用、实质gap、有限算术/绝对和溢出；
  真正原始行/人工列约束或成本证据不合法时不得发布正下界。
  关键反例：第7.2节改seed为r=1路径，构造原始可行的辅助权重lambda1=1、u=2，F=2；
  注入pi=(conv:-4,r:2)，全部真实路径rc非负、rho=0、D=L=2且g=0，
  但GE人工列rc=1-2=-1，超过盒约束，伪下界2高于真实F*=1。
  该隔离注入必须NUMERICAL_ISSUE，即使其他下界/差距门控看似通过。
- RMP非OPTIMAL、坏OPTIMAL被RMP核验拒绝、定价NUMERICAL/矛盾NO_PATH、
  已有显著负rc路径、坏候选/原目标混入、后续轮失败/原始复核失败；
  所有非成功状态feasible_problem/witness为None，失败字段和轮号隔离。
- limit=1/2/3、最后一轮成功优先、零目标复核不占辅助预算，
  solver调用数=auxiliary+validation；不加入最后预算轮尚未求解的新列。
- 异常程序错误保持可见，不捕获所有异常冒充成功/不可行。
原有CG/RMP/DAG/LP行为必须原样回归。

## 10. 允许文件与范围锁

唯一允许：
- 新增src/silo/decomposition/dag_feasibility.py；
  src/silo/decomposition/__init__.py仅导出本步独立接口/记录。
- 新增tests/unit/test_dag_feasibility.py、
  tests/verification/test_dag_feasibility_oracles.py。
- 新增docs/dag_feasibility.md；docs/README.md加入口，
  docs/development_layout.md仅补新入口/真实支持域及依赖说明。
- 新增learning/lessons/L0005-cg-feasibility/README.md、exercises.md、solutions.md；
  更新learning/CATALOG.md。
- .silo-dos/project_profile.md本步实际状态/基线/限制/建议；
  本任务新报告、派生tasks/INDEX.md。

禁止改dag_column_generation.py、restricted_master.py、dag_pricing.py、LP/core/modeling/
presolve/mip/cuts/CLI/io/外部接口、utils、原日志/toy/通用solver、旧测试、
L0001–L0004、旧合同/报告、研究资产/notes、其他docs、ROADMAP/阶段/其他门控、
Skill/Agent、依赖/build/native或全局容差。禁止外部求解器、生产全路径枚举、
Big-M混合原目标、自动Phase-II优化、warm start、资源/分支/增量定价、性能主张。
发现超范围需求报告最小缺口，不以恢复功能为由重构旧控制器或提升原算法范围。

## 11. Learning delivery：L0005｜列生成的可行性恢复与辅助主问题

遵循十节编排，链接L0001/L0002/L0003/L0004并保持各篇主题身份。
讲清固定列LP的Phase I与全列域可行性定价；单位违背量、LE/GE/EQ列符号、
conv不加人工；零原成本定价；人工列conv0下的平移证明；F*=0与原可行等价；
小F后移除复核；正下界与浮点证据边界；退化/预算；原成本/c0交接。
研究价值说明补齐可行初始化才能公平比较后续重优化/增量定价，成熟基础机制本身不形成创新。

至少五题L0005-E01起及完整答案：辅助列与对偶区间、两类列的下界证明、
第7.1节两目标手算、退化/预算与原始见证、数值不确定和支持域辨析。
正文完整程序真实运行restore成功后原目标CG到9、正违背量1及退化1->1->0。
明确单位罚权对行单位的敏感性、非空合法seed、普通DAG/连续域、现有LP/浮点限制；
没有严格Farkas或一般数值认证、资源可行性/整数/工业性能结论。

verified_code用真正包含新模块的完整实现提交，checked/verified_on按实际核验；
允许代码/测试A后学习/报告B同一任务。A前draft/null，不能引用旧CG提交冒充新基线。

## 12. 执行、检查、报告与停止

1. 记录实际HEAD/branch/status/cached origin差异、解释器和silo.__file__，
   核对四个已知本地提交及签发提交授权，保持唯一写入协调者。
2. 先写区分性行为检查，再实现小型可读参考恢复器；不把import错误当算法red。
3. 签发阶段theory_architect独立形式化确认辅助等价与两类列平移证明，要求人工列盒约束
   及完整有符号gap门控；experiment_auditor补强人工列下界、原始见证和深层目标身份测试，
   已纳入。两服务未跑实验/改文件，意见不重复计作实测或实现通过。
   主线程负责实现、648族和原始交接实测，不重复模型对照或并行写入。
4. 完成API、L0005、报告/摘要/INDEX，用真实实现哈希收尾。
5. 使用现有环境，从项目根执行：

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_feasibility.py tests/verification/test_dag_feasibility_oracles.py tests/unit/test_dag_column_generation.py tests/verification/test_dag_column_generation_oracles.py tests/verification/test_dag_cg_bound_consistency.py tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

运行正文完整程序和有限习题，检查UTF-8/链接/围栏/公式/十节/稳定题号/真实基线。
代码稳定全量通过后纯文档收尾不重复全套；后续代码改动/失败/实质疑点才补跑。
验收：三例、648族、两类列下界及原始交接符合；误用原目标/小F/正受限罚值/失败/limit
不能产生错误成功或严格不可行主张；所有旧边界及全量质量通过；L0005真实核对；
diff只允许文件，本地提交后停止。

报告写清实际基线、辅助模型/人工列元数据、阶段目标/符号/界证明、
数值状态及原始复核、两类调用计数/失败轮归属、648具体数据与独立性、200/448分类和
200次原目标交接的实际结果；自然/注入/签发桥接/数学复核分别计数；
真实失败修复、教学与质量检查、变更范围、实现/学习提交、限制及下一步仅建议。
Git记录status、branch、log -5、cached origin差异、push not_attempted、remote_sync_status；
仅单次命令Git身份参数，不改全局配置。报告自身提交通过
git log -1 --format=%H -- tasks/reports/20261019-06-01_dag-feasibility_report.md
在提交后定位。若模型或下界不成立、必须改禁区/提升数值规则/扩大域，保留证据停止扩展。
最终回执后停在第6步，等待silo-solver-1010审查；不自动启动第7步、不向其他对话发消息。
