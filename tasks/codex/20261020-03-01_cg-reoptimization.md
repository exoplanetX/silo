# 第9步交付：DAG列生成显式接入RMP重优化

## 1. 元信息、授权与当前基线

- ID：20261020-03-01_cg-reoptimization。已扫描同日合同/报告：
  TT01=lp-unbounded-check，TT02=rmp-reoptimization，TT03/RR01空闲；第9步是开发序号。
- 任务类型/风险：L2，现有普通DAG CG消费既有RMP可选入口，一个原子问题。
- 用户在第8步验收、获知16个未推送提交及两项治理文件变动后要求
  “执行详细任务，交付执行”。授权为本合同具体化的CG集成、测试、学习、报告及本地提交。
  原目标保持：逐步建设承载用户OR研究的求解器并形成开发伴学材料。
  本步只补重复求解链路，不把有限DAG范围当作项目完成或研究特色已经形成。
- 设计/签发/验收：silo-solver-1010，01a1254a-b349-77d0-8c66-d4b711cd511f；
  执行：silo-solver开发，01a15208-bea9-7030-aacc-95d785e8fa58。
- cwd：E:/OneDrive/workspace/codex/silo-solver；签发前HEAD：
  09fb205f246b1fa0db558ae569216b2401197212，main，cached origin/main...HEAD=0/16。
  已知本地提交依次为8ee397e、15b403b、f0cc01a、b886458、8006344、02aed7d、
  70293f9、e96e3e2、26f3c48、c460aa7、445da97、a26039f、f8ce202、90b377f、
  be0dd57、09fb205。继续授权覆盖上述16个及本次合同/摘要/INDEX签发提交。
  远端上次即时核对f0c5f31；本轮cached引用不冒充即时远端。
- 工作区两项已告知的用户治理改动获准原样保留，在当前检出执行本步：
  AGENTS.md已修改，SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638；
  根目录研究主题固定_严重反面案例通告_20261020.md未跟踪，
  SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
  不提交、覆盖、还原、暂存或挪动这两文件；不为已知ahead/这两项重复询问。
  其他漂移、分歧或不明脏文件保留并停报，不能重置来制造干净状态。
- 实际执行从签发提交开始，用git log -1 --format=%H -- 本合同路径定位。
  已验收源码：RMP/LP90b377f723f047f723949aaace87f1385f42bb74、CG15b403b、
  恢复02aed7d、定价12bfa35；第8步3669项/Ruff及L0007已由讨论对话独立审查。
- 来源：tasks/phases/phase_03_revised_simplex.md的重复求解方向、
  tasks/phases/phase_07_decomposition.md的分解接口边界和第8步验收建议。
  Phase9仍open/parked、native deferred/unapproved；Phase10 not started。
- Git mode：local-commit，不push。Expected report：
  tasks/reports/20261020-03-01_cg-reoptimization_report.md。
- Learning delivery：新learning/lessons/L0008-cg-reoptimization/README.md、
  exercises.md、solutions.md及learning/CATALOG.md；L0001–L0007已占用。
- 推荐GPT-6 Sol/high。难点是跨层失败历史、退化对偶及缓存来源一致性；
  建议不代表已切换，专业只读服务保持固定配置。

## 2. 唯一目标和开始前阅读

为现有solve_dag_column_generation提供明确的可选RMP重优化开关，
保持默认cold，公开保存每轮实际重优化诊断；后续定价/候选/界/停止继续消费
本轮最终经核验的MIN RestrictedMasterResult。CG不拥有基快照或额外回退。

先读用户目录research-lessons/CASE-20261020-01.md、项目根案例通告、AGENTS.md、
tasks/README.md、project_profile、technical_route、remote_sync_proof、
learning/README.md和WRITING_GUIDE.md。再读当前CG/RMP/Revised公开接口，
第4/5/8步合同报告、L0004/L0005/L0007及其回归；按需查恢复器。
当前任务不改既定主题，不引入案例项目模型，不改已废弃稿件或其他项目。

## 3. 锁定API和最小接入

函数末尾追加keyword：
solve_dag_column_generation(problem, *, solver=None, tolerance=1e-9,
iteration_limit=100, reoptimize_rmp: bool=False)。

- type(reoptimize_rmp) is bool，拒绝0/1、字符串、None及其他truthy值。
- False：仍每轮master.solve(solver)，后端支持和现有默认行为保持；
  不能预先调用新入口或偷偷准备新缓存。
- True：solver=None或原生RevisedSimplexSolver/兼容测试子类；
  非Revised在RMP构造/任何LP或定价调用前明确TypeError。False仍允许现有Tableau/测试后端。
- 每次CG调用创建且只拥有一个新的RMP owner，所有增列继续现有add_column；
  True每轮恰调用一次公开master.solve_reoptimized(solver)，将outcome.result交给原CG流程。
  不用outcome.used_warm_start判断“还要不要cold”；内部回退已经在第8步入口完成。
- 不读取master._model、_basis_snapshot或任何LP私有runner/映射/清理函数。
  生产中只为类型校验导入公开Revised类；实际求解仍由公开RMP负责。
- 不重建RMP owner来逃避缓存/资格问题，不在同一个owner调用普通solve作参考，
  不复用失败warm的pi/rc，不在CG缓存旧对偶。独立cold对照使用独立owner。

在DagColumnGenerationIteration现有roundoff_allowance之后追加：
rmp_reoptimization: RestrictedMasterReoptimizationResult | None = None。
直接消费RMP已有冻结公开结果，不新增协议/后端架构，不修改RMP结果类型。

- False模式每条记录新字段为None，旧位置参数、replace和冻结行为保持。
- True凡本轮已调用RMP，成功、master失败、pricing失败、数值失败及外层limit/正常停止
  记录都包含该轮实际outcome；record.master_result is outcome.result。
- rmp_reoptimization.result是最终MIN结果；attempted、used_warm、cold次数、分开迭代、
  回退原因和快照资格均由已有outcome原样提供，不由CG猜测或重新计数。
- 顶层last_valid_master仍为既有RestrictedMasterResult，类型/轮号/注册表含义保持。
  seed重构先失败且尚未创建RMP时，保持现有无已解轮/无诊断记录语义。
- 新字段按关键字传递到全部四个history.append分支，不只覆盖成功分支。
  无需decomposition/__init__.py新增导出，既有函数/记录已导出。

## 4. 原数学与失败语义保持

开关只替换每轮RMP公开入口。以下规则/助手保持原实现：
_path_ids、_reconstruct、_check_candidate、_master_objectives及数值/命名助手；
完整DAG定价、严格rho<-tolerance、原始候选重构、tuple路径身份、退化增列、
P/D/L、g_raw、有符号且消去c0的objective_gap、固定32*ulp(A)及所有阈值不改。
不裁剪负gap，不放宽1e-9，不用热启动标志代替最优核验或完整定价。
不要求cold/warm同基、同对偶、同选列或同轮数；按各自当前列集和对偶核验。

失败历史按当前代码的发布位置区分：
1. RMP最终非OPTIMAL：MASTER_FAILURE，本轮attempted registry和outcome保留，
   pricing/全部界/g/eta/accepted_path为空，顶层last_valid_*保留上一成功轮；首轮则无历史。
2. 有效RMP已通过_master_objectives且被登记为last_valid后，pricing/候选/gap失败：
   本轮界/g/eta/accepted_path为空，outcome和当前有效RMP可保留；
   顶层last_valid_*对应当前已核验RMP，不能退回旧轮或把旧界冒作新界。
3. _master_objectives尚未通过而失败：维持其原有历史有效轮，记录本轮尝试和outcome。
4. warm失败/内部cold成功：同一外层轮使用cold最终解、只定价一次，可正常加列；
   CG不再调用cold。warm失败/内部cold失败：按第1条停止，不能用旧成功标志推进定价。
5. 外层iteration_limit按RMP/定价轮计数，内部warm/cold不是额外CG轮；
   最后允许轮不追加未求解列，成功条件优先于limit，保持原规则。

所有True/False异常都保持现有输入错误与逻辑RuntimeError可见。
第8步负责完整行资格、单次cold、最终最优/无界门控及缓存失效，本步不重写或削弱它。
普通有限路径凸组合可行域有界，后端UNBOUNDED在CG仍只是RMP失败诊断。

## 5. 两个必须真实发生的机制例

A：conv=sumλ=1、cap:λ_q<=0；路径x/q/r的成本2/0/1、cap系数0/1/0，
seed仅x，c0=0。普通DAG可用三条平行弧。
初轮pi=(2,0)，q的rc=-2，r的rc=-1，所以先加入q。
q受cap限制只能取0，第一warm必须实际零步长枢轴、目标仍2；
下一轮加入r并warm到1。三轮目标2->2->1，cold/warm/warm；
观察实际leaving-row ratio=0，不只检查目标未降或迭代标志。

B：旧coupled图d1/d2/o12/o21的成本4/6/1/2、R/C向量(1,1)/(0,0)/(1,0)/(0,1)，
conv=1、R=C=1/2、c0=-3，seed d1/d2。
三轮目标2->2->-1.5，cold/cold/warm：首轮投影行依赖，清理删行且snapshot_available=False；
首个off-diagonal增列恢复完整行基，仍cold并建立资格；最后才warm。
检查完整原始R/C/conv行，不把旧删行关系延续到新列。
固定原输入用于精确机制断言；其他排列只要求各自机制/真值，不强求相同候选名。

另做恢复阶段衔接：图p0/p1/p2成本0/4/10、r=0/1/2、conv=1、r>=1/2、c0=7，
初始seed p0不可行。先调用原restore_dag_feasibility，再显式对其feasible_problem
调用CG(True)。不改恢复器、零成本辅助目标或验证预算，不共享任何辅助/验证基；
经济CG首轮必须fresh cold、原成本/c0正确。用公开返回值和真实owner/调用记录核验。

## 6. 固定主族：288图、864次CG与独立逐轮依据

新增tests/verification/test_dag_cg_reoptimization_oracles.py，独立构建两族：

I. 72个区间图：
- 三条真实双弧branch路径p1/p0/p2，总r=1/0/2，seed仅p1；
  s->v_i弧成本(i+1)/2，v_i->t补足总成本；图基成本按成本组偶/奇取1/-2。
- conv保持base=1、弧系数0、EQ/RHS1。lo/hi均表示同一r；
  区间(1/2,3/2)或(1/4,7/4)；原始三行的全部6种排列。
- 成本(p1,p0,p2)=(2,0,-1)、(0,4,10)、(0,0,0)，c0依组7/-3/0。
- 两种表示：lo GE/hi LE为正，或两非conv行同时乘-1并翻方向/RHS；
  conv绝不能翻负。非conv图基系数为sign/8，末弧补足sign*r。
  负表示同时反弧输入顺序；节点序(v2,s,v0,t,v1)，图row_names跟随原始行序。
共2*3*6*2=72图；允许部分seed已最优、全程只有一轮cold。

II. 216个运输方形图：
- 路径(i,j)取i,j∈{0,1}，s->left_i->right_j->t，全部4条；
  start成本(i+1)/2、R弧系数i；end成本-(j+1)/4、C系数j；
  middle成本补足路径总成本，图base成本按k偶/奇为1/-2，R/C基系数1/8、-1/4。
- 六个按(00,01,10,11)排列的总成本矩阵：
  (4,1,2,6)、(-3,2,1,-4)、(0,0,0,0)、(-4,-4,3,3)、
  (9/4,-3/2,1/2,13/4)、(1,-5,-2,0)。
- alpha,beta各取1/4、1/2、3/4；conv=1，R=alpha+1/8，C=beta-1/4，全EQ；
  c0按k偶/奇为2/-3。
- t∈[max(0,alpha+beta-1),min(alpha,beta)]，
  λ=(1-alpha-beta+t,beta-t,alpha-t,t)。
  分别以两个端点的严格正权重路径为seed；原表示及节点/弧/行/seed序全部反序。
  原节点序(right1,s,left0,t,right0,left1)，图row_names=(C,conv,R)；
  原行序(conv,R,C)，原seed按00/01/10/11筛正；反序不翻conv符号。
共6*3*3*2*2=216图。

每图三模式：默认cold-Revised、显式cold-Tableau、True-Revised；
主族共288图/864次完整CG调用，外层limit=100、内层limit=10000、tolerance=1e-9。
另用代表例比较显式False与省略开关，旧调用全保留。
864是运行数，不是864个独立数学模型、内部LP数或pytest项。

独立依据必须从原始图数据出发：
- 自写DFS枚举全路径，Fraction逐原项累加成本/系数。
  不调用生产重构/主目标/快照助手或旧verification测试来算真值。
- 当前列集只取该轮immutable registry，不能拿最终列集反推前轮。
  独立枚举非负权重顶点：取正变量支持，选conv与足够活跃非conv行，
  Fraction解非奇异小系统，过滤全部原始EQ/LE/GE，再最小化原目标。
  冗余EQ允许秩不足，不能假定三个原行始终独立。
  完整域目标另由区间端点或方形t两个端点解析取得；两者互相核对。
- 每个模式每轮独立重算原始可行、MIN乘数符号、rc、互补性和原/对偶差距；
  全路径最小rc、实际定价路径及其候选字段、改善分类、接受路径/注册表增量、
  P/D/L/rho/g_raw/g/eta/停止或limit与轮号均核对。
  对原始浮点结果按现有绝对1e-9核验，原项先转Fraction，不靠生产核验器自证。
- 完整列集的独立owner双cold LP作交叉对照，分别统计；不得清空热路径owner。
  同一图不同模式可有不同有效轨迹，逐轮oracle分别作用于其当前列集。

实际路径另观察公开RMP入口、native solve_with_details和Phase I/II runner：
默认/False不调用solve_reoptimized；True每轮仅一次公开opt-in调用且不调用普通RMP.solve。
accepted warm实际只入Phase II，传入问题全原行/无人工列、新增列非基，cold入口0；
内部回退如实记录一次cold，不能用CG结果flag代替trace。
核对诊断引用、solver/owner调用数、Phase次数、枢轴、零枢轴和缓存资格。

签发前临时桥接已实际完成上述864次：三模式均TOLERANCE_REACHED且最终解析目标一致；
区间True桥接72次CG/120轮=72cold+48warm；方形216次CG/323轮=251cold+72warm，
均零回退。桥接仅在内存用测试类把旧CG的solve转向现有公开solve_reoptimized，
没有新增开关/迭代字段，不是本步实现通过。新入口须重跑本族并记录真实计数。
不要把某些seed不合格导致cold当作错误，也不为凑warm数修改原行或数据。

## 7. 大常数、失败、隔离与兼容性

新增tests/verification/test_dag_cg_reoptimization_bounds.py：
- 上述六方形成本，alpha=beta=1/2、下端点seed、原/反序，
  c0取0、±2^40、±2^60，共60图，各三模式180次CG。
- 逐轮原始贡献、c0消去的g与解析增量目标独立检查，保留g_raw的发布语义；
  不能要求浮点P减c0恢复低位，也不能要求发布值逐位等于解析实数最优值。
  P/D/L/g_raw按原项浮点fsum重构，数学目标比较用c0-free原项与既有1e-9。
- 显著负g、eta<=tol的负g例外/越界、正g恰阈值和略超阈值、rho严格阈值、
  c0掩盖的实质gap、非有限乘积/总和、已有显著负路径等代表边界在True下仍生效。
  能用真实数据时真实运行，必要的内部故障注入另列，不借注入声称自然失败概率。

新增tests/unit/test_dag_cg_reoptimization.py，至少：
- 机制A/B、恢复后显式经济CG、无改善首轮停止、多次调用/不同solver实例隔离；
  同一个solver也不跨CG owner或辅助/经济阶段复用快照。
- 严格bool校验；True拒绝Tableau/任意其他backend且RMP/LP/pricer均0调用；
  False保持旧Tableau与测试backend；默认路径未调用任何新入口。
- 所有五类终态及初始seed重构先失败的新字段/历史语义；
  旧位置构造新字段None，结果/输入/历史字典只读防御性复制。
- 在后续真实warm轮注入一次kernel非最优，内部cold成功：
  同轮只一次opt-in、至多一次cold、只一次定价，消费cold最终pi/数值，
  其后正确加列/停止且诊断attempted=True、used_warm=False。
- warm失败并cold失败：当前registry/outcome保留、界为空、上一有效轮不改；
  不多做一轮cold/定价，不把失败路径加到顶层历史有效列集。
- 有效RMP之后分别注入pricing失败、候选失败和gap失败：
  当前outcome与有效RMP可保留，所有本轮界为空，顶层按第4节发布位置保存。
  若主目标原始验证先失败，则保持更早有效轮；不能把这些情况合成一个错误规则。
- 外层limit1/2/恰成功轮与内部Revised预算/回退各自计数，
  最后一轮不追加未解列；跨运行/异常后不复用旧CG owner。
- 第8步本已完成的非法快照/原始行/无界门控用原回归保护，
  本步不重复实现或制造真实凸组合无界例；控制器非最优状态分支注入须标作合成。
- RuntimeError保持可见，禁止catch Exception兜底或吞错后继续。
  测试私有hook只用于观察/故障注入，不参与构造解析真值。

签发桥接另完成60图/180次大常数CG，True共100轮=90cold+10warm、零回退；
机制A/B各三模式共6次CG，True6轮=3cold+3warm。它们仅为桥接范围证据。
最初探查把-3.5000000000000004与-3.5逐位比较失败；修正检查器为既有1e-9/
原始贡献判据后最终完整运行通过。生产算法、数据及容差未改，失败探查不混入最终计数。

## 8. 允许文件与禁止范围

唯一允许：
- src/silo/decomposition/dag_column_generation.py：新keyword/校验、
  一个公开RMP入口分支及迭代末尾诊断字段/全部分支接线，必要模块说明；
  原数值助手/候选/路径/停止判据不改。
- 新tests/unit/test_dag_cg_reoptimization.py；
  新tests/verification/test_dag_cg_reoptimization_oracles.py；
  新tests/verification/test_dag_cg_reoptimization_bounds.py。
- docs/dag_column_generation.md：签名/逐轮字段/用法/冷默认/失败/数值边界；
  docs/rmp_reoptimization.md仅更新新CG消费者与默认边界；
  docs/development_layout.md仅更新现有CG入口/依赖，docs/README.md仅必要导航。
- 新L0008-cg-reoptimization三文件与learning/CATALOG.md。
- .silo-dos/project_profile.md实际进度/基线/限制；
  本合同指定新报告及派生tasks/INDEX.md。

禁止改LP/RMP/基快照/标准形/Basis/最优与无界核验、定价器、可行性恢复器、
decomposition其余模块或__init__导出、core/Solution/Status、MIP/割/不确定性/
interfaces/CLI/JSON、旧测试/合同/报告/旧学习篇、notes/研究资产、其他docs、
ROADMAP/阶段/门控/规则/Skill/Agent/依赖/build/native。
不做增量定价、LU/矩阵缓存、对偶稳定化、一般CG插件、资源或整数扩展、性能优化。
必要超范围缺口记录并停报，不自行跨层修改；已知用户治理文件保持原字节。

## 9. Learning delivery：L0008｜列生成中的基复用与逐轮证据

按WRITING_GUIDE十节，前置链接L0004/L0005/L0007。
说明同一经济模型增列保持原始可行基、当前最终MIN对偶驱动定价、
为什么旧/失败warm对偶不能沿用、完整定价与原上下界推导不因热启动改变；
退化为何可改变最优对偶/列轨迹，为什么目标不降或0枢轴仍可能是有效机制。

完整公开API程序实际运行A/B，打印各轮rmp_reoptimization诊断和目标；
再展示恢复器返回feasible_problem后显式调用CG(True)，核验经济首轮fresh cold。
至少六题L0008-E01起及完整推导/答案，覆盖基与对偶义务、真实退化、删行秩恢复、
四种失败历史、独立当前列集oracle/大c0及预算/研究主张辨析。
研究意义：为后续研究中的重复求解与公平工作量比较形成可核查基础；
特色方向由实际OR问题提出需求，本步不改原目标、不宣称创新/加速/工业稳健性。
仍完整矩阵重建和解基系统、全域普通DAG定价；后续各自另行立项。

verified_code必须是实际包含新CG入口与测试的完整实现哈希A；
A前draft/null，A后真实核验再checked/日期，允许实现A与文档报告B同一原子任务。
旧篇目不改写为新版本；新API文档链接本篇，不复制完整教学正文。

## 10. 检查、报告与停止

1. 实查HEAD/branch/status/cached差异、Python、silo.__file__及两治理文件哈希；
   只提交本任务允许路径，禁止git add -A，Git只用单次身份参数、不改配置。
2. 先在现有源码复现A/B与冷族，再写区分性检查/最小实现；
   不把import/fixture错误算算法red，不删旧测试、改数据/容差或特意重排来刷warm命中。
3. theory_architect只读确认一次公开调用/严格bool/同轮诊断/失败发布点；
   experiment_auditor要求独立当前列集oracle及warm-fail/cold-success/fail和后续定价/gap失败交叉。
   两服务未运行或写文件；其意见不计作运行或新实现验收。
4. 项目根命令：

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_cg_reoptimization.py tests/verification/test_dag_cg_reoptimization_oracles.py tests/verification/test_dag_cg_reoptimization_bounds.py tests/unit/test_dag_column_generation.py tests/verification/test_dag_column_generation_oracles.py tests/verification/test_dag_cg_bound_consistency.py tests/unit/test_rmp_reoptimization.py tests/unit/test_revised_reoptimization.py tests/verification/test_rmp_reoptimization_oracles.py tests/unit/test_dag_feasibility.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

逐一运行L0008完整程序/有限解答；检查十节、稳定题号、真实哈希、
UTF-8、链接、围栏和公式定界符。全量通过后仅文档收尾做轻量检查；
代码变化、失败或实质疑点才再跑相关/全量，不无理由反复运行。

验收：默认cold及旧字段兼容；True实际可选消费、每轮诊断准确；288图/864主族、
60图/180常数族及A/B独立真值与真实入口通过；回退/失败历史/预算/隔离正确，
原pricing/数值助手与规则保持、全量质量通过；L0008实际核对，diff仅允许范围。
报告必须区分模型族、CG运行、外层轮、公开RMP调用、warm尝试/接纳、cold/回退、
Phase I/II、枢轴/零枢轴、完整域cold参考、pytest项；自然/故障注入/签发桥接分开。
记录基线、实际签发提交、API/字段、每轮验证/失败/所有权、真实失败与修正、
质量与教学、范围偏差、实现/学习提交、未覆盖研究义务及下一步仅建议。
Remote Sync Proof含status（本来就有两项用户变动，不称干净）、branch、log -5、
cached差异、push not_attempted、remote_sync_status；复核治理哈希未变。
报告自身提交用git log -1 --format=%H -- 报告路径定位，避免自指哈希。

完成这一合同的实现/检查/学习/报告/本地提交后停止，等待silo-solver-1010审查。
不push、不自动开展性能实验/增量定价/下一任务或阶段，不向其他对话发消息。
