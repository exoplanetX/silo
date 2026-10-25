# SILO 稀疏 LP 与连续重优化：详细实施计划

计划身份：`SILO-SPARSE-LP-20261024 / implementation-v1.2`，2026-10-25。
总目标及数字门槛以[总体规划](sparse_lp_reoptimization_program_20261024.md)为准；
本文件将其展开为一个总任务内的实施顺序、责任、接口、输入和交付门。
准备阶段只生成计划与合同。2026-10-24用户已在“silo-solver开发”以Goal模式明确启动；
SP1输入a3cff29、真值/基线3c27324已冻结，架构/完整证据独立GO先于产品。
当前SP2容量阻断已修复，完整固定LP/机制/上层/历史及8安装均有通过证据；原第4项候选
为当前源warm4完整80/80。后续同源超时、观察器缺口与RR07辅助门HOLD如实保留。
现在按[最终收口计划](sparse_lp_closure_20261025.md)及RR08核验原八项；整体未预先完成。
本文件保留原SP1–SP4工作包与完成标准，禁止据旧阶段描述重复启动已经通过的算法工作。

## 0. 唯一执行入口与读取顺序

当前入口合同：[20261024-02-08_sparse-lp-program](../codex/20261024-02-08_sparse-lp-program.md)。
原[01合同](../codex/20261024-02-01_sparse-lp-program.md)保留为启动/原目标依据。
该合同是一个整体任务，SP1–SP4是内部工作包，不另签四个或更多原子任务。

恢复时按顺序读取：根AGENTS及案例通告 → tasks/README → 当前及原入口合同 → 总体规划 →
本实施计划/集中恢复计划 → 当前mirror/历史报告。冲突按当前直接用户指令、合同、总体目标处理，
不得用旧已完成目标的授权代替本次启动授权。

用户明确以目标模式启动后：

- **开发对话拥有本轮唯一Goal**，自行完成SP1→SP4、必要的只读独立复核、修复和本地交付。
  当前讨论对话负责事前规划及用户请求后的独立项目审查，不作为常规阶段切换的等待条件。
- 每个阶段PASS后继续同一合同，保存阶段提交/报告与检查收据；无需逐补丁或逐门再问用户。
- 仅对超范围、目标/门槛变更、权限扩张或真实无法继续的问题集中报告；预算不能通过新Goal重置。
- 全部八项总验收通过并取得独立最终技术GO后，Goal可完成并停止。未达不标complete。
  阻断状态遵守Goal工具自身规则；不得为满足状态工具而继续运行已耗尽的计算预算。

当前准备基线：`64700cdb0d258d303fa1ac06e0f06a8a8bddd2b8`；产品源码`f488189`。
待启动合同的发行提交用Git history定位。实施从包含该提交的检出开始，新分支建议
`codex/sparse-lp-reoptimization`；不新建solver副本或自动创建另一个工作树。

## 1. 已定效果与全程不变量

必须交付：端到端稀疏LP、LU+真实eta更新、跨调用因子复用、四类修改、现有MIP/CG接入、
固定验证、8个隔离安装和伴学。原数学方向、KKT、整数格、Farkas/射线及有限CG精确门保持。

必须达到：12容量/12外部LP全部正确；指定最大2000变量/5000行/100000非零；每例120秒/
1GiB；160个修改状态全部正确最优；5重复后8条轨迹cold/warm比值中位数≥1.5且6条≥1。
任一必过例超时或数值失败均为未达，不转组、不删例。原C HOLD、D/E未开始及native延期保持。

### 1.1 固定依赖与公开行为

- 基础安装仍NumPy，默认`lp_engine="dense"`。新增`sparse` extra支持Python3.11+，
  首轮验收锁定SciPy1.16.3；其本地包元信息为Python>=3.11、NumPy>=1.25.2且<2.6。
  SP1核对两版本环境可安装性并存锁定收据；依赖不可用即报告，不自行改大版本。
- 建议metadata：`scipy==1.16.3; python_version >= '3.11'`置于`sparse` extra；
  base的Python>=3.10声明不因本轮降低。未验Python版本的sparse能力不作通过声明。
- `SolveOptions`末尾兼容增加`lp_engine`，合法值dense/sparse；统一CLI `optimize`增加
  `--lp-engine`。旧`solve`/`mip-solve`命令的既有范围不扩张。
- sparse依赖缺失时返回`unsupported/sparse_dependency_missing`，不偷偷densify或调用外部优化器。
- 增加稀疏资源选项：`max_sparse_nnz=1000000`、`max_factor_nnz=5000000`、
  `max_factor_updates=20`；前两项为非负整数，更新链上限合法范围0..20，0表示禁用eta。
  稀疏/因子资源零值在确需该资源时触发明确资源出口；额外依赖必须在sparse选中时惰性导入。
  `max_dense_cells`继续约束dense，不得先拒绝sparse模型再分派引擎。
- solver层只可调用SciPy sparse/linalg数值运算；外部优化器仍限interfaces/测试/比较工具。
  原生路径的`linprog/milp/HiGHS`调用须有静态及运行时阻断测试。
- 候选版本0.3.0a1；只本地构建、安装、提交，不push、tag、Release或上传包。

### 1.2 推荐文件责任

这些是允许范围内的明确责任；类名可在SP1契约中一次冻结，不能以命名为由重设计整个项目。

| 责任组 | 新建/修改路径 | 交付与唯一写入边界 |
|---|---|---|
| 数据/规范化 | `modeling/matrix_ops.py`、`modeling/general.py`，必要时`modeling/sparse_general.py` | dense/CSR/CSC操作、稀疏变换/缩放；不改搜索算法 |
| 预处理/核验 | `presolve/activity.py`、`lp/verification.py`、`lp/tableau_view.py` | 非零遍历、来源恢复、受限证明抽取 |
| 数值因子/内核 | 新`lp/factorization.py`、`lp/sparse_kernel.py`，必要公共helper及`lp/kernel.py`适配 | B/B^T、eta、稀疏Phase I/II/Devex；保留dense参考 |
| 会话/集成 | `lp/session.py`、`lp/general.py`、`solver.py`、`mip/general.py`、`decomposition/general_master.py` | 缓存/失效、统一分派、节点与增列；由集成负责人唯一写入 |
| 被动选项/CLI | `core/solve_types.py`、`cli/main.py`，必要的包导出 | 兼容新增选项；core不导入SciPy/LP/MIP；现有core/matrix.py占位类不当作可信缓存身份 |
| 验证/交付 | `scripts/sparse_program.py`、`scripts/sparse_program/`、`tests/unit/test_sparse_*`、`tests/verification/test_sparse_*`、小manifest、docs/learning | 新runner及预算/来源核验，旧manifest/结果保持只读 |

若使用写入代理，仅并行“数据/变换/核验”和“因子/内核”，明确互斥文件；
`SolveOptions`、`lp/general.py`、session及上层集成由执行主线程唯一合并。
每个写入者必须知道其他人在同库工作，不回退他人修改。最多3个并行代理，独立评审默认只读。

## 2. SP1：先冻结设计和证据，再改产品

### SP1.1 设计契约

在产品src/pyproject改动前提交：

1. `docs/sparse_matrix_contract.md`：矩阵操作、规范化映射、资源门、标准形身份及原空间恢复。
2. `docs/sparse_basis_session_contract.md`：第5节公式、factor接口、数值参数、快照兼容、缓存失效表。
3. `docs/sparse_validation_contract.md`：输入/真值、计时/内存、driver子命令、阶段与预算核算。

三份是同一任务的设计交付，不是新增合同。Devex至少冻结进入评分、权重维护/重置、
确定性并列规则和Bland回退触发；核对可定位的公开原始论文或官方实现，记录所读版本。
不能只给分数排序换名Devex，不能把未读全文写成已核验公式。

### SP1.2 验证工具及输入冻结

实现验证入口`scripts/sparse_program.py`，辅助模块置于同名目录，
显式处理manifest、ledger、来源、子进程deadline/RSS、参考oracle、报告。该阶段可改验证工具、
docs及小fixtures，不改solver产品代码。准备三类文件：

- `tests/fixtures/sparse_program_manifest.json`：固定ID、配方、参数、预期及预算的唯一入口。
- `tests/fixtures/sparse_program_sources.json`：外部URL/版本/来源、原始/解码/转换SHA与数学检查。
- `tests/fixtures/sparse_program_oracles.json`：独立真值、精度、原始模型校验及参考来源。

固定seed20261024，按稳定组/ID排序和独立子seed生成；顺序规则和序列化在manifest声明。
先提交输入配方、全部ID、数据SHA及门槛，再运行任何SILO基线；随后提交真值/比较器与基线。
SP1全部提交和设计门GO须早于任何针对性产品实现。
不能在SP1提交导入尚不存在生产模块的普通pytest，导致历史测试收集失败；先提交被动案例与数学契约。

### SP1.3 数据与基线

- 取得总体规划列明的12个Netlib输入；每文件首次+一次下载重试。可用官方数据分发镜像，
  记录具体URL/版本并核对数学输入，不能替换ID。解码/标准MPS转换限验证导入层。
- 数值导入独立核对目标方向/常数、行侧、变量域和稀疏系数；行数对照时说明目标行计数。
  参考求解器与SILO不得只共用一个未经核查的转换。
- 48小例用独立有理顶点/解析oracle；容量例提供独立原始可行/对偶对或结构性最优性依据；
  HiGHS是补充比较器。外部历史截断最优值只作交叉参考，不能当精确小数真值。
- 在8个重叠外部例（AFIRO、ADLITTLE、BLEND、SC50A、SC50B、SC105、SC205、SHARE2B）
  保存0.2.0a2 dense基线；即使原基线失败也保留输入。原生产树身份与实际运行提交同时记录。
- 记录CPU/内存/OS/Python/NumPy/SciPy、BLAS线程、源码树/脚本hash、随机seed及比较器版本。
  原报告不冒充新profiling结果。设计与数据不具备时集中报告SP1未达。

**SP1审核门**：独立架构检查+证据设计检查，一遍签收契约和manifest；
不把性能目标视为已有结果。验证预算30分钟，数据/依赖问题不通过修改目标绕过。

## 3. 固定输入实例化规则

### 3.1 48小例与24压力例

- `TINY-NET-01..12`、`TINY-TRANS-01..12`、`TINY-BLOCK-01..12`、`TINY-GENERAL-01..12`。
  每例≤4变量/8行，覆盖min/max、目标常数、区间/等式、自由/固定/上界反射、负界、零行/列。
  对稀疏配方逐一用解析或独立Fraction顶点枚举求真值，不调用SILO辅助函数生成oracle。
- `PRESS-OPT-01..08`：4退化/冗余、4等价尺度变化，尺度取1e-6至1e6，必须正确最优。
- `PRESS-INF-01..04`、`PRESS-UNB-01..04`：原始数据上独立已知Farkas或锚点/射线，必须正确终态。
- `PRESS-NUM-01..04`：2精确依赖/冗余必须最优，2近奇异可验证最优或事先声明的保守数值失败。
  合法终态集合在冻结前写明；不能事后把错误状态改名为允许失败。
- `PRESS-LIMIT-01..04`：time0、pivot0、稀疏nnz门、factor填充门；预期limit及对应reason。
  外部watchdog杀进程属于harness失败，不能伪造为solver主动limit。

### 3.2 12容量例

容量目标以原始未规范化的非固定变量和有效约束计数；不能用未使用变量、全零列或重复行凑数。
行数大于网络本体时应来自明确的侧约束/多期或资源结构，配方解释业务/数学作用。

| 固定ID | 原始变量/行目标 | nnz上限 | 角色 |
|---|---:|---:|---|
| CAP-FLOW-01 | 256 / 512 | 4096 | 网络含侧约束；SP2预检 |
| CAP-FLOW-02 | 1000 / 1500 | 20000 | 同类扩展 |
| CAP-TRANS-01 | 400 / 600 | 6000 | 运输含侧约束；SP2预检 |
| CAP-TRANS-02 | 1500 / 2000 | 30000 | 同类扩展 |
| CAP-ASSIGN-01 | 625 / 500 | 6000 | 连续指派含侧约束 |
| CAP-ASSIGN-02 | 1600 / 1000 | 30000 | 同类扩展 |
| CAP-BLOCK-01 | 800 / 800 | 16000 | 块角耦合 |
| CAP-BLOCK-02 | 2000 / 5000 | 100000 | 总容量上界必过例 |
| CAP-INVENT-01 | 600 / 700 | 8000 | 生产/库存多期 |
| CAP-INVENT-02 | 1200 / 1500 | 25000 | 同类扩展 |
| CAP-GENERAL-01 | 1000 / 1100 | 25000 | 一般稀疏约束 |
| CAP-GENERAL-02 | 1800 / 2200 | 60000 | 同类扩展 |

全部必须正确最优，单例120秒/1GiB；新规模组统一`lp_iteration_limit=100000`，
容差仍为原约定。至少6个大组ID在manifest标定presolve=False，
必须保留实质耦合且有≥20有效pivot；用诊断证明没有只走separable捷径。
这6个ID在基线前选定，生成/机制若不满足，应在SP1报告设计问题，不在求解后筛选成功例。

### 3.3 外部、机制、轨迹、上层

- `NETLIB-{12个固定名称}`：名称与总体规划完全一致，全部正确最优；每例120秒。
  SP2只先验AFIRO/ADLITTLE/SC50A/SC50B，完整12例的最终性能门在SP4。
- `UPDATE-01..08`：从固定结构输入的预先声明诊断版本取得；每例≥50有效换基，
  稳定组≥70%可更新pivot真实走eta，基签名/完整分解调用和当前B残差可核对。
  分母为稳定组实际成功的同维基列替换次数；周期/安全重分解不能把该次pivot移出分母。
  结构扩维、初始建基另计；不得用实现自己标记的eligible位任意缩小分母。
  另行单测坏主元/残差/第21次更新/结构失效，不把故意恢复例混入稳定效率分母。
- `WARM-{RHS,BOUND,ROW,COL}-{01,02}`：每条20次修改全部预期可行最优，
  大轨迹至少RHS-02、COL-02达到≥1000变量/500行。每个状态有冻结修改操作与独立真值。
  正式8条×2模式×5重复×20修改=1600次状态求解；另计80次初始状态。
  每轨迹/模式/重复共60秒，包含导入/初始求解和20次修改，初始成本单列但不移出预算。
- `MIP-{KNAP,MULTIKNAP,COVER,FACILITY,ASSIGN,FIXEDCOST}-{01,02}`：12例，每例60秒，
  规模保持现有原型支持域，按既有枚举/DP/外部及原始核验判据，不追加新MIP算法。
  至少4例出现真实分支，至少2例实际生成/使用有效局部GMI并再优化。
- `CG-COVER`、`CG-GENERAL`、`CG-TINYRC`、`CG-UNBOUNDED-GUARD`：4例，各60秒/20轮。
  GENERAL必须有真实Phase I入列及Phase II跨调用复用；TINYRC正确-10000；最后一例
  保持合同允许的证明无界或保守退出，无有限伪最优；另有旧1/3与预算出口单测保留。

内部生成/转换配方只能在上述结构范围实例化一次，输入/预期提交后不得更换、改seed、
加更容易模型或放宽阈值。外部对照只算一个HiGHS算法流；不把重复计时当作新独立实例。

## 4. SP2：端到端稀疏cold

### SP2.1 矩阵、变换与资源门

- 在`solver.solve`/session入口先选engine，再验证资源和构造数据，保留旧input_conversion保护。
- 实现MatOps的行/列非零、matvec、transpose、absolute-product、取基、追加/选择行列及稳定身份。
  CSR服务按行操作、CSC服务取列/基，双视图的存储成本据实计数。
- 用`offset`、原变量索引/方向、列缩放和来源表实现x=o+Tz、ray、multipliers，
  T仅作为数学映射，不在sparse路径分配n×k实体。
- 标准形slack/artificial单元稀疏追加，语义行/列ID与原始坐标恢复一致；区间拆分和整数格不变。

### SP2.2 传播、核验与证明预算

- Activity传播按非零支撑，保持Fraction计算、方向安全的界和逆序乘子来源恢复。
  可复用行活动量；不能因缓存错过变化界而错误删行。
- 原始KKT使用稀疏乘加，精确Farkas/射线逐原非零项累加；残差尺度与0.2.0a2相同。
- `tableau_view`在创建Fraction标准形、坐标向量之前检查预计单元、nnz、位数与deadline；
  basis_limit80不能代替大n保护。精确基只按需抽B，GMI只抽相关行/坐标，
  禁止为每个native列分配长度n的全量坐标。超限跳割或保守退出并记录原因。
- 同一模型在dense/sparse应符合相同原空间数学契约；保留`result._lp`消费者的显式适配。

### SP2.3 cold内核与公开入口

- 用稀疏标准形实现Phase I、人工变量清理、Phase II、原始/对偶单纯形和终止。
  先支持每次换基重做SparseLU，保证算法/恢复正确；SP3再加更新，不以此状态交付最终Goal。
- Factor接口固定`solve_B(rhs)`、`solve_BT(rhs)`、`replace_column(...)`、`refactor(...)`、
  `identity`和统计；SuperLU内部行列置换由适配器封装，对外始终原语义顺序。
- sparse快照version3保存语义键与O(nnz)不可变稀疏数据身份，不保存全矩阵tuple或可变LU对象。
  version2合法输入可按语义映射后新分解；无法映射时一次记录cold，不按旧列号直接使用。
- 兼容增加选项、extra、统一CLI；dense旧行为/字段保持，缺依赖和资源门用小测试确认。

**SP2验证**：先lint/组件，再48真值、24压力、4小外部和CAP-FLOW/TRANS-01；
检查无隐藏dense分配及B/B^T残差。最终容量/外部性能不在此先验。
独立读者核对变换、恢复及基方程后门GO。预算60分钟。

## 5. SP3：基更新和会话的数学/数值契约

### SP3.1 LU+eta公式与执行顺序

以基位置r的进入列a替换当前B的一列，`d=B^-1*a`、`p=d[r]`，
`E=I+(d-e_r)e_r^T`，`B_new=B*E`。链`B_k=B_0*E_1*...*E_k`。

单eta逆作用：`y[r]=v[r]/p`，`y[i]=v[i]-d[i]*v[r]/p`（i≠r）。
单eta转置逆：`y[i]=v[i]`（i≠r），`y[r]=(v[r]-sum(d[i]*v[i],i≠r))/p`。

- 解`B_k*x=b`：先base LU解`B_0^-1*b`，再按**时间正序**应用`E_1^-1...E_k^-1`。
- 解`B_k^T*y=q`：先按**时间逆序**应用`E_k^-T...E_1^-T`，最后base LU解`B_0^-T`。

强制次序反例：`B0=I, E1=[[1,0],[1,1]], E2=[[1,1],[0,1]]`，
当前B=`[[1,1],[1,2]]`；q=(1,0)时正确转置解(2,-1)，错误正序会给(1,-1)。
单eta测试不能替代这个非交换双更新测试。

每次方向和结果都对**当前实际B或B^T**检查：
`||r||inf <= 1e-10*(1+||rhs||inf+||abs(B)*abs(solution)||inf)`。
检查`B_old*d=a`后才提交eta。主元保护使用既有pivot_tolerance及当前方向尺度，
链长最多20；第21次追加前以当前B重新建立base并清链。
不截断小系数来伪造eta稀疏性。

残差失败最多2次迭代细化，再对当前B重分解一次并重解；仍失败给numerical_failure。
主元/增长（固定指标`max(norm_inf(d),1/abs(p))>1e8`）、填充、链长或结构门触发真实重分解，
这些是数值策略，不是定理常数；在SP1记录，不能按基准成绩逐例放宽。

Devex首先用于primal进入列评分，dual保留有证明的确定性出基/比值规则。
SP1须给所采用Devex工作定义与复位依据；退化/循环检查触发Bland并记录，不加入新竞争策略。

### SP3.2 缓存身份、失效与隔离

会话私有factor与公开basis分开。缓存命中要求当前基的维度、行/基列语义顺序、缩放后
数值系数、坐标结构和数值策略身份相符；不可变版本或稳定digest必须绑定实际系数，
不能依赖可变dict的frozen外壳。结果/witness永远绑定本次模型/对偶/选项。

| 修改 | 因子处理 | 仍须重做的计算 |
|---|---|---|
| RHS改变且基签名不变 | 保留base+eta | 基本值、可行性、模式选择、对偶/终态/KKT |
| 界/offset改变，但列方向、补行、缩放和B不变 | 可保留factor | 新RHS/恢复账本/原始核验，不复用旧primal |
| 目标或dual容差改变且B不变 | 可保留factor | 对偶、reduced costs、停机与证明全部重核 |
| 追加非基列且旧行缩放和B不变 | 保留factor，必要pivot后追加eta | 新列定价及完整性检查 |
| 追加行/维度变化 | 严格失效，扩基后新分解 | 扩维可行性/模式/全部核验；本轮不做bordering更新 |
| fixed/free模式、侧别/行集合、预处理或缩放改变 | 失效，语义映射后新分解或一次cold | 当前变换与全部计算 |
| 坏/过期basis、改系数、行列重排身份不一致、engine变化 | 不得命中旧数值缓存 | 记录原因并安全恢复 |

整模型SHA变化不自动等于factor必须失效，模型SHA不变也不替代实际基身份检查。
公共model副本与用户可变输入不得修改内部缓存；branch节点不共享可变LU/eta状态。
SuperLU对象不做通用deepcopy/序列化；跨进程/导入的被动basis需要新建数值分解。

### SP3.3 机制与正式计时

先完成非交换eta、随机合法短链、转置、残差/主元恢复、第21次重分解、坏签名的组件测试；
再跑8机制例与8×20轨迹。计数至少分为：`base_factorizations`、`eta_updates`、
`refactorizations_by_reason`、`within_solve_reuses`、`cross_solve_reuses`、`cold_fallbacks`。
这些字段必须对应实际调用，可用spy独立核对，不能沿用一个factor_reuses混称所有复用。

每条轨迹先单列初始求解；正式状态成本包含编辑、复制/模型校验、规范化、数值求解、
恢复及最优性检查。cold从同一冻结状态独立重建，参数/engine/资源相同；顺序交替。
5重复全部保留，`R_ij=T_cold_ij/T_warm_ij`（20次修改完整成本），
`R_i=median_j(R_ij)`，总体`R=median_i(R_i)`；至少6个R_i≥1且R≥1.5。
同时公布包含初始求解的链总成本和摊销比值；重优化段1.5不能被写成所有工作负载都快1.5。
每次60秒保护覆盖初始及修改全过程；SP3预算中的160分钟已包含所有这些初始求解。
禁止将失败/超时删掉后计算比值，也不把只快的三角求解段当总收益。

**SP3审核门**：独立核对公式顺序、当前B残差、缓存隔离和公平计时，数学/机制/性能分别PASS。
两轮正式计时最大160分钟，8机制例8分钟，其余检查12分钟，合计180分钟。

## 6. SP4：上层真实接入、总体评估和候选

### SP4.1 上层

- MIP统一选sparse LP；`np.vstack`局部割追加改经矩阵边界，父子节点basis身份保持。
  12例必须核验原始整数点/目标与保守全局界；分支、局部GMI、割后重优化日志能定位。
- RMP/CG的Phase I人工侧行、Phase II、增列均经sparse session；strict负rc与原始全池
  精确P=D门不变。证明无法形成时保守，无通过全列黑箱替代CG的捷径。
- 对上层source、native engine与factor/cache身份做收据，不能仅凭选项名判定稀疏生效。

### SP4.2 最终评估

用最终相关代码完成48小例、24压力、完整12容量/12外部、8机制、8轨迹、12 MIP/4 CG；
先前收据只有源路径及依赖未变化时可复用，否则重核受影响组。
保留原全部单测、288固定例、192审查模型和保存64诊断只读复核；不重开旧ledger。

报告数学成功率、合法保守退出率、错误结论数、总时及分段时间、峰值RSS、nnz(A/standard/L/U)、
fill、更新/重分解/回退、原始残差及冷/热比值。单一加权总分不替代八维评价。
容量/外部必过24例成功率必须100%，压力组允许失败条目不混入其分母。

### SP4.3 工件、伴学及结束

- 最终代码提交后用干净Git快照构建wheel/sdist，逐生产模块匹配工件与源码；EOL运输差异
  单列映射，不能据此接受其他字节漂移。metadata/runtime/CITATION均为0.3.0a1。
- Windows Python3.11/3.13×wheel/sdist×NumPy-only dense / SciPy sparse，共8个新环境。
  源码树外`-I`验证API、JSON/MPS CLI、两公开研究例和关键修复；dense配置无SciPy，
  sparse配置锁SciPy1.16.3且优化器调用被阻断。环境SciPy存在不算外部优化器被调用。
- 8个环境各首轮一次；网络/锁文件故障允许同SHA一次重试，不能覆盖旧失败。
  Linux/其他Python或远端CI未实际运行时pending；不触发GitHub push/公开发布。
- 更新L0012，新增L0015（当前最大14，启动时复核未被他人占用）讲解稀疏基及eta；
  若15已用则选下一未用ID而不覆盖既有篇。目录ID稳定，原理/手算/练习/代码/价值/局限/
  verified_code与真实核验同行交付。必要交叉更新L0011/13/14，不新增无关教学主题。
- 更新当前README/安装/工作台来源映射，移除旧候选误作当前入口的歧义，不重写历史报告。

**SP4审核门**：执行主线程完成自检后，由未承担实现的独立终验者按总体规划八项逐条核验。
技术总GO后更新当前状态，完成唯一Goal并停止。讨论对话后续项目审查不自动启动新任务。

## 7. 验证入口、收据与恢复

以下是SP1必须实现并验证的目标命令，**当前尚未存在/执行，不代表已有测试通过**。
driver先运行独立preflight、manifest/源码检查，再执行指定分组，每次新run UUID目录。

```text
python scripts/sparse_program.py preflight
python scripts/sparse_program.py freeze-inputs
python scripts/sparse_program.py check-inputs
python scripts/sparse_program.py baseline --engine dense --cohort overlap
python scripts/sparse_program.py run --group tiny --engine sparse
python scripts/sparse_program.py run --group pressure --engine sparse
python scripts/sparse_program.py run --group sp2-smoke --engine sparse
python scripts/sparse_program.py evaluate --stage SP2
python scripts/sparse_program.py run --group mechanism --engine sparse
python scripts/sparse_program.py warm --round 1 --repetitions 5
python scripts/sparse_program.py evaluate --stage SP3
python scripts/sparse_program.py run --group capacity --engine sparse
python scripts/sparse_program.py run --group netlib --engine sparse
python scripts/sparse_program.py run --group mip-cg --engine sparse
python scripts/sparse_program.py run --group historical
python scripts/sparse_program.py install-checks --candidate 0.3.0a1
python scripts/sparse_program.py summary --final
```

实际命令、参数和返回语义在SP1文档冻结；新driver将既有结构/lint/pytest/build/install命令
包装进预算与日志，不另做第二套同义测试。新增测试文件名和命令在各阶段报告记录。
全质量使用原`scripts/check_quality.py`，先做ruff/组件再整条运行，process PATH含`.venv/Scripts`。

新账本唯一根：`outputs/sparse_lp_program_20261024/`；规划准备输出另放其他目录。
ledger逐事件含program/contract、source tree/script/input SHA、group/IDs/engine/options、
start/end/elapsed、started/completed calls、退出码、失败/重试、预算桶和append-only hash链。
实际求解总次数据实记录，按固定分组与轮次控制，不再设混合128类上限。

- 单测内调用、外部对照、CG内部LP与MIP节点分开记；计时包装不要父子命令双重累计。
- 子进程超时/OOM/退出异常保留输入及尾部输出，作为失败而非丢失的“未运行”。
- 原`outputs/prototype/`、`prototype_revision_20261024/`、`audit_20261024/`和a1/a2工件只读。
- 恢复先读总报告最后checkpoint、ledger链和Git/source身份；已完成未变输入不重复跑，
  正在运行的步骤按收据恢复，不能因会话重启清零预算或重建Goal。
- 完整容量/外部组最多2轮；正式warm最多2轮各5重复；全质量最多3轮；每阶段初验+2次
  针对修正；额外诊断20批各60秒。全部验证分桶30/60/180/180+余量30=480分钟。
- SP3已单独核算160+8+12=180分钟。开始批次前检查剩余桶/总额度；不足不能开新整轮。
  预算耗尽、同一重大问题两轮无进展或必要数据/依赖不可用时交集中未达包，不增加阶段/任务。

## 8. 总报告与阶段记录模板

当前唯一总报告：`tasks/reports/20261024-02-02_sparse-lp-program_report.md`，RR02实际执行时创建；
`tasks/reports/20261024-02-01_sparse-lp-program_report.md`保留七轮恢复前历史。
启动登记人类实际启动指令、Goal owner、分支/HEAD/dirty例外、依赖、读取记录、阶段预算。
每阶段记录：目标 → 对应内部工作包 → 变更/提交 → 实际命令/案例/来源 → 失败及根因 →
只读审核结论 → 门判定 → 剩余义务/预算 → 自动进入的下一个既定阶段。

最终表必须逐项记录总体规划八项、原研究覆盖与未覆盖、工件/平台状态、性能完整分母、
额外诊断、目标停止点和remote sync proof。报告result commit从Git history定位，不自引用。
成功不能只写“全部测试通过”；未达时明确哪一门、哪个ID、哪项指标不足。

## 9. 实施准备核查与权限边界

本轮只读数学服务已独立推导eta公式和非交换转置反例，代码服务核对8组耦合；
未执行新solver实验、下载实例或改产品。数学推导不充当数值性能证据。
计划与待启动合同准备完成后，用户在开发对话明确启动才使其列明的实施授权生效。
不得在当前讨论对话提前创建Goal、发消息让开发开始或修改solver。

独立执行准备门已一遍核查总体/实施/合同草案及README6.11，结论GO，无额外关闭项。
其核对激活边界、唯一Goal、数学/缓存、计数和预算一致性，不是算法或性能运行通过。
合同最终创建保持该审查版本；随后完成索引/结构与Git范围核对，本轮只交付准备文件。
