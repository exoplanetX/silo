# 第8步交付：RMP显式增列后的保守基复用与重优化

## 1. 元信息、授权与实际基线

- ID：20261020-02-01_rmp-reoptimization。已扫描同日合同/报告：
  TT=01为lp-unbounded-check，TT=02/RR=01空闲；第8步是开发序号。
- 类型/风险：L2，现有RMP/原生Revised的显式可选重优化；一个原子问题。
- 用户在第7步验收及基快照/映射/增列核验/冷回退建议后批准
  “同意，执行任务后交付执行”。本合同具体化该授权；本讨论对话签发/审查，
  silo-solver开发唯一协调实现/测试/学习/报告/本地提交。
- 签发/验收thread：01a1254a-b349-77d0-8c66-d4b711cd511f（silo-solver-1010）。
- 执行thread：01a15208-bea9-7030-aacc-95d785e8fa58（silo-solver开发）。
- 工作目录：E:/OneDrive/workspace/codex/silo-solver。
- 实际签发前HEAD：a26039fa9f5f6784732f8304d663bba00215bd9a，干净main；
  cached origin/main...HEAD=0/12。已知本地提交按先后为8ee397e、15b403b、
  f0cc01a、b886458、8006344、02aed7d、70293f9、e96e3e2、26f3c48、c460aa7、
  445da97、a26039f。用户已获知12个未推送提交后批准本步，
  继续授权覆盖上述12个及本次仅含合同/摘要/INDEX的签发提交，不为已知ahead再次询问。
  其他漂移/分歧/无关脏文件保留并报告，不重置或覆盖。
- 从签发提交执行，用git log -1 --format=%H -- 本合同路径定位。
  远端上次即时核对f0c5f31；cached引用不冒充即时远端。
- 已验收源码：LP c460aa78c2abc489839a0da2411b9bd1bca95983，
  RMP48c242d、DAG定价12bfa35、CG15b403b、恢复02aed7d。第7步3444项与Ruff已验收，
  不代替本步新实现核验。
- 来源：tasks/phases/phase_03_revised_simplex.md的基复用方向，第2步RMP冷求解与
  第7步验收建议；Phase9仍open/parked，native deferred/unapproved，Phase10 not started。
- Git mode：local-commit，不push；Expected report：
  tasks/reports/20261020-02-01_rmp-reoptimization_report.md。
- Learning delivery：新learning/lessons/L0007-rmp-reoptimization/README.md、
  exercises.md、solutions.md和CATALOG；已扫描L0001–L0006。
- 推荐GPT-6 Sol/high；难点为人工列清理后的全行基、语义身份、增列索引移动和缓存一致性。
  这是建议，不代表实际切换；专业只读服务保持固定配置。

## 2. 唯一目标与支持范围

为只显式增列的MIN RMP增加可选基复用：首轮冷求解建立合格快照，
后续从新完整模型构建标准形，按语义键映射旧非人工基、以新增列非基0继续Phase II，
任何复用依据不足或warm失败最多冷回退一次，最终仍核验全部原始行的最优性。

保持现有RestrictedMasterProblem.solve(solver=None)始终cold；现有CG/可行性恢复器
不改、不自动采用新入口。本步只在固定小RMP序列证明安全复用，不接CG，不做增量定价、
因子分解缓存、稀疏更新、性能承诺或一般模型修改后的重优化。

首次保守支持：旧求解人工列已清理且完整原始行一行未删；行/旧变量/旧成本/c0都不变，
仅零个或多个新原变量追加。遇任何旧删行，不生成可复用快照，继续完整行冷求解。
这项保守限制覆盖旧行依赖随增列改变的风险，不要求恢复一般冗余行关系或补基。

开始前读AGENTS.md、tasks/README.md、project_profile.md、technical_route.md、
remote_sync_proof.md、learning/README.md、WRITING_GUIDE.md；再读RMP、Revised、
standard_form、Basis、optimality、unboundedness，L0001/L0002/L0006及第1/2/7步合同报告。
旧裸basis接口遇人工列会ERROR；不能把调用该接口当作含等式重优化已完成。

## 3. 数学对象、快照资格与不可变身份

旧非人工完整行标准形A_O*x=b，m行，基B=A_O[:,I]可逆且x_B>=0。
增列后为[A_O,A_N]*(x,z)=b，新增变量z非基0，旧B及旧可行点在精确算术下仍可用；
新列可以破坏旧对偶可行性，必须重新计算乘数/约化成本并继续Phase II。
不能沿用旧pi宣告新模型最优。warm起点只要求原始可行，不要求新对偶可行或最优；
不能因为新列rc<0而拒绝复用，完整最优性检查放在本轮求解结束。

新增冻结RevisedBasisSnapshot（建议src/silo/lp/simplex/basis_snapshot.py），至少持有：
- 按基槽顺序的basis_keys；完整有序原始row_names；
- 旧非人工列语义身份清单；
- 旧原变量顺序、类型/界/成本，全部原始行顺序/名称/方向/RHS及旧变量系数，
  MAX目标方向和常数的冻结结构身份。省略系数按原值0解释，比较持有值精确相等，
  不按容差判同，不只存可伪造的eligible布尔或一个无内容hash。
- 不保存/复用旧primal、dual、reduced-cost数组；每次从新模型重新计算。
原变量键=(original,original_name)，结构列键=(slack或surplus,source_constraint)；
角色和来源要验证，不能靠名称前缀区分。原名可以叫slack_lo、artificial_conv等。
所有语义键唯一，人工列不入快照。新增原变量插在结构列之前，整数列号会移动；
严禁把旧列号直接塞给新模型。

快照只可由本轮最终OPTIMAL、完整原Model的check_lp_optimality(...,1e-9)通过，
且details.problem/basis有效、无人工列、problem.row_names与全部原行逐项相同的
Revised结果产生。必须验证基维度/分区、类型/语义坐标和可解性，不能只比行数/集合。
原Model/字典/列表/数组后续修改不能反写快照；已返回结果也不能被后续求解修改。

资格不足只禁发快照：例如cold OPTIMAL且全部数学证据通过，但清理删行，
仍应发布已核验OPTIMAL和“快照不可用”的原因。不得为了快照资格伪改有效求解状态。

## 4. LP层专用复用入口与全行核验

新增独立的RevisedSimplexSolver.reoptimize(model, snapshot=None)（名称保持该含义），
返回新冻结RevisedReoptimizationResult，包装既有RevisedSimplexResult及本步诊断/新快照。
既有solve、solve_with_details(model,basis=None)、RevisedSimplexResult字段及其默认行为保持。
新入口在运行前保留独立原始Model/reference与冻结身份，原始核验和新快照来源不能
因执行对象/返回对象被修改而改写；不得信任可变native对象作为唯一核验源。

推荐共用快照/身份/映射纯助手放basis_snapshot.py；它不导入revised.py或RMP，
避免循环。Revised在自身模块内复用现有Phase-II、最优/无界结果构造及原始核验；
RMP仅消费新LP公开入口，不调用LP私有runner/清理函数，不另写单纯形。

对有快照的新模型：
1. 用完整新Model重建标准形；精确检查旧原变量是同序前缀、旧界/类型/成本、
   原始行有序元数据/旧系数、方向/c0未变。新变量名称唯一，只能追加。
   模型名不是数学身份；原行/变量重排、旧系数/RHS/方向/成本/c0变化本步均判不兼容，
   冷求解当前完整模型，不使用容差把旧模型当成同一个。
2. 检查快照全部旧原始行保留、旧基本键均唯一且映射成功。
   fresh人工列不在映射基中，全部是非基；在不删任何原始行的情况下去掉它们，
   建立artificial-free完整行StandardFormProblem及当前Basis。
   不调用旧“含人工列裸basis warm start”分支，也不走Phase I冒充复用。
3. 验证当前基为m×m、分区完整、B可解，raw x_B和B*x_B-b有限且按既有绝对
   DEFAULT_TOLERANCE核验，全部非人工标准变量非负；当前原变量点还要对完整原Model
   的所有行/界按同一容差独立复算。不能用_clean_zero、裁剪、归一化、删行制造通过。
   标准形可能清零小系数，标准形可行并不代替原Model可行。
4. 以映射基和新目标运行现有primal Revised Phase II，重新求pi/rc。
   其最终OPTIMAL先对完整原Model调用现有最优核验器，再发布。
   若内部给UNBOUNDED，继续使用第7步原Model点/射线门控，不旁路或放松。
5. warm非OPTIMAL（包括ITERATION_LIMIT、NUMERICAL_ISSUE、已核验UNBOUNDED）、
   无效快照/坐标、奇异/不合法基、原始点核验或最优性核验失败，
   记录复用失败后最多执行一次完整cold solve_with_details。
   公开最终数值结果以该次cold及其完整原模型核验为准；cold仍失败则直接发布诊断，
   不再循环求解、不补基、不修复候选或无界方向。
6. 无快照时只cold一次。cold OPTIMAL也须完整原模型核验才可发布/发快照；
   核验失败为NUMERICAL_ISSUE，不再次cold。cold真实UNBOUNDED沿第7步门控；
   其他非最优字段仍空/None。

原始支持域、1e-9核验、负RHS符号与第7步精确无界条件保持。
这里的可行基/最优核验仍是既有浮点语义；基复用不构成严格数值证明。

## 5. RMP显式入口、诊断和缓存生命周期

新增RestrictedMasterProblem.solve_reoptimized(solver=None)，默认且仅支持原生Revised
或其兼容测试子类；其他后端显式TypeError，调用者仍可用旧solve(Tableau等)冷解。
返回新冻结RestrictedMasterReoptimizationResult，含原MIN RestrictedMasterResult与
路径诊断；旧RestrictedMasterResult字段/意义不改。decomposition/__init__.py可仅补新类型导出。

两种新结果至少清楚区分：
- 最终结果，used_warm_start（仅实际warm被最终接纳时True）；
- warm_phase_two_attempted、实际warm迭代数（0迭代成功也是合法复用）；
- cold_solve_count为0或1，fallback/rejection reason及快照可用性/不可用原因；
- LP层返回新合格snapshot或None；RMP内部拥有缓存，不提供任意外部setter；
- 若warm尝试后cold成功，attempted=True、最终used_warm_start=False，
  不把失败warm的pi/基或状态冒充最终结果。

明确预算：warm至多一个Phase-II run，cold至多一个既有solve_with_details调用；
继承该solver的iteration_limit，各run按既有预算。分别记录warm与cold迭代，不声称
这个limit是warm+cold总枢轴预算，也不把回退成本藏起来。

RMP继续完整MIN到MAX取反：成本/c0、目标/乘数/rc逐项取反，原始行坐标不变。
继续使用独立reference副本保护原始最优核验；不信任可修改native副本或返回字段。
每个最终RMP OPTIMAL都核验完整本轮模型，非最优MIN映射为空。
两个LP/RMP核验层不能互相跳过。RMP若最终核验失败，清空缓存并NUMERICAL_ISSUE；
不能保留一个LP层合格但RMP发布失败的snapshot。

缓存规则：
- 首次opt-in cold，合格则保存新快照；否则None且有原因。
- add_column成功只保留旧快照作为待验证候选，不提前宣称新模型已求解；
  一次可追加多列。失败的原子add不改模型或缓存。
- warm成功或cold最终OPTIMAL且资格通过，以本轮最终基/完整模型更新快照。
- 最终非OPTIMAL、完整核验失败、来源删行/其他资格不足，缓存None；
  失败后下次不能用更早快照偷偷继续。fresh cold成功后可重新建立资格。
- 普通solve始终cold并清空该对象的opt-in缓存；避免交叉调用后缓存来源不明。
  非Revised参数拒绝不修改对象。并列冷参考要用独立RMP owner，不能在warm owner
  调普通solve再指望保留cache。
- 上次/本次结果及快照防御性复制、只读；两RMP实例不能共享可变缓存。

每次仍重建完整标准形和解基线性系统；本版不保存LU、不做增量矩阵或定价。
只主张符合资格时省去初始可行基搜索/Phase I，是否实际加速需以后公平实验。

## 6. 三个固定机制例

### A. 可行初始化之后的含等式重优化

conv=sumλ=1、r>=1/2，原列p0/p1/p2的r=(0,1,2)、成本(0,4,10)、c0=7。
初始只给p0/p2，cold最优9.5；显式加p1后必须实际warm并到9。
先有可行RMP，本任务不再做可行性恢复或自动选择列。

### B. 真实warm退化与结构列移位

初始min 2*x，conv:x=1、cap:0*x<=0，x>=0，c0=0。
非人工标准形含x及基本slack_cap=0，行全秩、无删行，pi_conv=2、pi_cap=0。
加q成本0、conv系数1、cap系数1，旧rc=-2，但原约束强制q=0，
一次零步长改善枢轴后目标仍2；必须warm成功并重新核验，不以目标未降拒绝。
再加r成本-1、conv系数1、cap系数0，warm最优-1。
目标2 -> 2 -> -1，后两轮必须实际warm，第一warm至少1次枢轴。
加入原变量使slack_cap的整数位置移动，实际传入Phase II的基语义键必须与旧快照一致。

### C. 旧受限投影重复，增列恢复行独立

初始仅x成本2，完整原行为a:x=1、b:x=1。cold目标2，清理删一行，无复用资格。
加q成本0、列(a:1,b:0)或(a:0,b:1)，完整模型强制x=1/q=0，目标仍2；
必须cold保留两行，绝不能沿用旧被删行集合得到错误0。
本轮完整行已满秩，可重建快照；再加r成本-1、(a:1,b:1)，下一轮必须warm到-1。
两行原/反序、两种q、双cold后端已由签发主线程实测8条历史/24次求解，均2->2->-1。
这只是既有cold桥接，不是新复用实现通过。测试说明初始投影重复，不将它写成完整列域恒等冗余。

另覆盖两条独立EQ：conv:x+y=1、balance:y=1/2，成本x0/y4、c0=7；
依次追加q(balance=1/2,cost1)与r(balance=1/2,cost0)，两列conv均1，
目标9 -> 8 -> 7，后两轮实际warm，证明多个初始人工列可被安全去除。

## 7. 固定144历史/576调用与独立解析依据

新增tests/verification/test_rmp_reoptimization_oracles.py。
列按r=1/0/2分别为seed p1、新p0、新p2；固定conv=1、lo<=mean(r)<=hi：
- (lo,hi)取(1/2,3/2)、(1/4,7/4)；
- 成本按(p1,p0,p2)取(2,0,-1)、(0,4,10)、(0,0,0)，c0按组取7/-3/0；
- 加列顺序(p0,p2)或(p2,p0)；
- 三原行(conv EQ、lo GE、hi LE)的全部6种排列；
- 原表示或全部行乘-1并翻LE/GE（EQ不变），含负RHS。
共2*3*2*6*2=144条历史。每条4轮：seed cold、加第一列warm、加第二列warm、
不改模型再warm，共576个opt-in调用，预期144次cold和432次成功复用，零cold fallback。
初始行全秩由conv和两条不等式各自的结构列保证；首次快照包含slack_hi与surplus_lo，
后续新增原列使它们索引移动，不能仅测全部基本列都是原变量的情形。

独立真值：给定当前r集合，conv组合是一维区间。
Fraction枚举单列可行点和任意两列在lo/hi处的权重（另包括退化单列），过滤原始行后
取最小原成本+c0。这是小LP顶点解析，不能从生产基快照/标准形/重优化助手取真值。
所有状态/目标/原始可行性、最小化对偶符号/rc/差距均逐轮核对。
两独立旧RMP owner分别cold Revised/Tableau同轮交叉检查；退化时不要求pi或基逐项相等。

签发前主线程已实际cold运行该144族：1152次双后端RMP均符合独立Fraction真值；
另576次native Revised详情均OPTIMAL、全部原行保留、人工列为空。
它们仅证明支持域/资格基线，不冒充新warm通过。新实现须重新运行全部历史。

测试必须观察真实入口/runner调用：
- 首轮实际cold一次，后3轮cold入口0次、Phase I 0次、Phase II恰1次；
- 传入Phase II的是当前完整非人工问题与按旧basis_keys槽序映射的基；
  新增列必须在非基集合，不调用旧bare-basis人工列拒绝路径。
- used_warm_start和记录数与实际调用一致；即使0枢轴也必须真实进入Phase II；
  不用仅比较答案或自报flag证明复用。
- 记录576最终状态、144/432路径、Phase I/II与cold入口实际次数，分清
  opt-in运行与1152次并列cold参考，不把比较调用混入回退预算。

## 8. 失效、隔离与回退测试

新增tests/unit/test_rmp_reoptimization.py和tests/unit/test_revised_reoptimization.py，至少：
- A/B/C、两独立EQ、LE/GE、负RHS、无行、小负/正成本与常数、重复向量不同变量、
  原名貌似结构列、连续一次加多列、不改模型重复求解；B的零步长枢轴真发生。
- 快照冻结/输入所有权、实例隔离、旧结果不被增列或后续求解反写；
  普通solve清空缓存、失败add不清空，参数拒绝不改变状态。
- 原行序/方向/RHS、旧变量顺序/界/类型/系数/成本/c0变化，即使仅微小差异或
  标准形清零后看似相同，都不可误认兼容；冷解当前完整模型并如实记录原因。
- 缺/重复语义键、错误角色/来源、非法基分区、旧人工键、快照声称全行但内容不符、
  矩阵奇异/非有限或raw原始点不合法，最多cold一次。
- 制造标准形点在原行上不满足的例子，必须在warm前原始核验拒绝；
  不能只在最终OPTIMAL阶段发现曾经不合法的起点。
- warm返回ITERATION_LIMIT/NUMERICAL_ISSUE/已核验UNBOUNDED等，
  或warm OPTIMAL缺失/伪造/非有限/原始最优核验失败，均cold一次；
  warm非最优状态不作为最终新最优或新快照泄漏。
- cold最终OPTIMAL核验失败，则NUMERICAL_ISSUE、cacheNone且不重试；
  cold本身非OPTIMAL保留既有数值语义/空字段，不伪造快照。
  失败后下一次fresh cold，成功可重新建立cache；后续另一次cold失败不能复用更早快照。
- warm无界分支经过第7步guard，再冷回退；最终cold仍走guard，
  两次实际检查与失败诊断分别记录，不能因复用新增未经核验UNBOUNDED出口。
- 损坏metadata但数学Solution有效时，只禁发快照，不把资格不足混同数学失败；
  合格来源本轮同样验证，构造函数的布尔或hash不能替代实际检查。
- 程序逻辑RuntimeError保持可见；不catch Exception把实现bug伪装成cold fallback。
  自然例/内部故障注入/签发cold基线分别计数。
- 原有cold RMP、裸basis warm接口、LP清理/无界门控、CG/恢复和全量回归原样通过。

## 9. 允许文件与范围锁

唯一允许：
- 新src/silo/lp/simplex/basis_snapshot.py；
  src/silo/lp/simplex/revised.py仅新增opt-in入口/结果和快照映射、Phase-II接入/核验；
  原有求解/清理/无界算法保持，复用已有内部runner，不复制算法。
- src/silo/decomposition/restricted_master.py仅opt-in入口/缓存/诊断，
  必要的内部结果发布复用；旧solve的数学行为保持cold，允许清空新缓存。
  decomposition/__init__.py仅补新RMP诊断类型导出。
- 新tests/unit/test_revised_reoptimization.py、tests/unit/test_rmp_reoptimization.py、
  tests/verification/test_rmp_reoptimization_oracles.py。
- 新docs/rmp_reoptimization.md；docs/README.md加入口、
  docs/restricted_master.md和docs/lp_solver.md仅同步新显式入口/限制、
  docs/development_layout.md仅补入口/依赖。
- 新L0007-rmp-reoptimization正文/练习/解答，learning/CATALOG.md。
- .silo-dos/project_profile.md实际状态/新限制/基线；本任务新报告；派生tasks/INDEX.md。

禁止改core/Solution/Status、modeling、presolve、standard_form.py、basis.py、
Tableau、optimality.py、unboundedness.py、普通pricing/ratio/pivot、utils/global tolerance、
其余decomposition（含CG/恢复/定价）、MIP/cuts/uncertainty/interfaces/CLI/io、
旧测试/旧合同报告/L0001–L0006、研究资产/notes、其他docs/门控/阶段/ROADMAP、
Skill/Agent、依赖/build/native。不接CG，不实现一般删行恢复、任意模型修改重优化、
增量定价或LU缓存，不改变公共Solution/CLI/JSON。
发现超范围需要时保留证据、报告最小缺口，不自行扩大。

## 10. Learning delivery：L0007｜RMP基复用、语义坐标与冷回退

十节编排，链接L0001/L0002/L0006。讲清可行基在增列下保持、新列可破坏对偶可行、
非基新增列0、语义列键/结构列索引、完整行/人工列/删行资格、
原始核验与缓存来源、退化、单次cold fallback和旧接口边界。
完整小程序实际运行A的9.5->9、B与C的2->2->-1、独立EQ的9->8->7，
输出真实warm/cold诊断，不借私有助手伪造实现通过。
至少六题L0007-E01起及完整答案，覆盖定理/对偶、映射、删行反例、
退化、失效生命周期、解析对照和研究主张边界。
研究意义连接重复求解与以后增量定价的公平基线；这次只是可审查参考基复用，
不主张已提高运行速度、工业性能或构成研究创新。仍完整重建矩阵和解基系统。
verified_code用实际包含LP入口/RMP接入的完整实现哈希，A前draft/null、
A后按真实核验标checked/日期，允许实现A和文档报告B同一任务。

## 11. 执行、验收、报告与停止

1. 记录实际HEAD/branch/status/cached差异、Python和silo.__file__，核对12已知提交
   及签发授权，保持单一文件写入协调者。Git仅单次身份参数，不改配置。
2. 先用现有cold路径重现机制例和固定族，再写区分性检查/最小实现；
   import/fixture错误不算算法red，不用删旧测试、改数据/容差刷过warm命中。
3. theory_architect已只读形式化确认全行无删行+语义基在增列下保持可行，
   要求专用人工列去除入口、完整原始点核验、可观察Phase II和缓存失效；
   experiment_auditor要求实际调用计数、真退化、受限投影秩恢复与独立oracle。
   只读意见未计为运行或实现通过，主线程负责裁决与实际测试。
4. 现有环境从项目根执行：

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_revised_reoptimization.py tests/unit/test_rmp_reoptimization.py tests/verification/test_rmp_reoptimization_oracles.py tests/unit/test_revised_simplex.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py tests/unit/test_lp_unboundedness.py tests/verification/test_lp_unboundedness_oracles.py tests/unit/test_dag_column_generation.py tests/unit/test_dag_feasibility.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

运行L0007全部完整程序/有限习题；检查十节/稳定题号/真实哈希、UTF-8/链接/围栏/公式。
完整质量通过后纯文档收尾仅轻量检查；后续代码变化/失败/实质疑点才重跑。

验收：A/B/C及独立EQ正确；144历史真实144cold/432warm且无伪装/回退，
逐轮解析真值、MIN字段和完整核验通过；失效/数值/预算失败最多单次cold，
缓存生命周期/所有权/历史证据正确；第7步guard不旁路，旧行为与全量质量通过；
L0007真实核对，diff仅允许文件，本地提交后停止。

报告记录实际基线、接口/快照字段、资格与完整行保守限制、语义映射、
人工列删除与Phase-II入口、原始核验、单次回退/缓存失效、144族逐轮真实路径/
Phase-I/II/迭代与两cold参考计数、解析真值/退化/秩恢复、自然/注入/签发桥接分开计数、
质量/教学实际结果、真实失败与修正、实现/学习提交、剩余限制及下一步仅建议。
Remote Sync Proof含status、branch、log -5、cached差异、push not_attempted、
remote_sync_status；报告自身哈希提交后用git log -1 --format=%H -- 报告路径定位。
完成第8步本地提交后停止，等待silo-solver-1010审查，不自动接CG、
推进下一任务或阶段，不push，不向其他对话发消息。
