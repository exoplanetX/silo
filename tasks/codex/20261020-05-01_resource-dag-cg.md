# 单元B交付：资源路径凸组合的参考列生成闭环

## 1. 身份、原目标及授权

- ID：20261020-05-01_resource-dag-cg；新任务TT05/RR01。签发前扫描同日合同与报告，
  TT01–04分别用于LP无界、RMP复用、普通CG复用、资源冷定价；TT05空闲。
- 原归属：三阶段七步的原4，补资源路径参考闭环；L2受控算法接入。
  本单只回答“非负整数资源可行路径如何与已有单凸性RMP形成正确的连续CG闭环”。
- A已由讨论对话验收，实现be03540db4f966a6c98f71e41d9025b08ddd7555，
  文档84e126c14b4297d3493b8b183015ad235369cc9a，验收414638a9c6ea703c883a4572ce23fa37e311b64f。
  独立质量5299项、Ruff/结构及资源枚举补查通过，不冒充B验证。
- 用户在开发对话01a15208-bea9-7030-aacc-95d785e8fa58的
  turn 01a159c2-87ed-7773-a738-59d5d0bb7f28明确批准A–E有界协调启动。
  讨论对话逐单签发和验收；开发对话一次仅执行本合同后停。无需重复询问已批准范围。
- 签发前HEAD=414638a9c6ea703c883a4572ce23fa37e311b64f，main，
  cached origin/main...HEAD=0/28；即时远端未核查。继续授权覆盖已登记28个本地提交及签发提交。
- 既有治理变动原样保留，不暂存/提交/还原/挪动：
  AGENTS.md SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638；
  根研究主题固定_严重反面案例通告_20261020.md
  SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
  其他未登记变化保留并停报。实际执行基线为本合同签发提交。
- Git mode=local-commit；不push。Expected report：
  tasks/reports/20261020-05-01_resource-dag-cg_report.md。
- Learning：新L0010-resource-dag-cg；签发前已扫描L0001–L0009，无L0010。
- 来源：[有界计划](../../docs/seven_step_completion_plan_20261020.md)B、
  [全局复查](../../docs/development_route_review_20261020.md)、notes26/28、A合同及L0004/L0008/L0009。
  Phase9 open/parked、native deferred/unapproved、Phase10 not started，均保持。
- 建议GPT-6 Sol/high，原因是资源可行列域、数值界和RMP历史需一致；不声称实际切换。

## 2. 阅读与唯一完成线

先读用户目录research-lessons/CASE-20261020-01.md、根案例通告、AGENTS.md、
tasks/README.md 6.8/6.9、project_profile/technical_route/remote_sync_proof、
learning/README.md及WRITING_GUIDE.md，再读上述来源和已有CG/RMP/资源定价代码与测试。

完成线：一个新的资源路径凸组合参考CG入口，默认冷RMP、可选既有RMP基复用，
每轮完整资源冷定价；资源非法列永不进入RMP，有限成功/失败历史一致，
独立全路径/全列真值与完整质量检查通过，L0010和报告交付后停止。

本单使用已知资源可行且RMP可行的seed；不建设资源初始可行性恢复器。
支持有限DAG、A的非负整数可加资源、连续lambda>=0及全局sum(lambda)=1。
真实多路径覆盖/分割、硬时间窗、访问记忆、一般有环路径及C应用不属于本模型。

## 3. 最小接口与结构约束

新增src/silo/decomposition/resource_dag_column_generation.py，公开：

~~~text
ResourceDagColumnGenerationIteration
ResourceDagColumnGenerationResult
solve_resource_dag_column_generation(
    problem: DagColumnGenerationProblem,
    resources: ResourceDagPricingProblem, *,
    solver: LPSolver | None = None,
    tolerance=DEFAULT_TOLERANCE, iteration_limit=100,
    reoptimize_rmp=False,
    pricing_state_limit=100000, pricing_transition_limit=1000000,
) -> ResourceDagColumnGenerationResult
~~~

通过decomposition/__init__.py导出这三项。复用现有DagColumnGenerationStatus，
不新增同义状态枚举或问题记录。必须resources.graph is problem.graph；
值相等的另一图对象也拒绝，避免资源和主问题引用不同图源。文档说明构造方式。

两个新冻结记录的字段、默认值、registry只读复制和成功/失败含义与既有CG记录相同；
区别为iteration.pricing_result类型是ResourceDagPricingResult | None。
不得把资源结果塞入旧普通CG记录或改变旧公开签名。

允许从旧CG只读复用_path_ids、_reconstruct、_check_candidate、_master_objectives及数值/registry
私有辅助函数；允许新控制器采用清晰参考实现。旧CG、A、RMP、LP等模块字节保持不变。
不为消除少量重复而重构通用pricing callback框架或改变所有控制器。

开始任何RMP/定价调用前验证：
- 两问题类型/同一图对象、严格bool的reoptimize_rmp、既有正有限tolerance/正integer轮数语义；
- 两pricing预算均为type is int的正整数，拒绝bool；每轮重新给予该预算；
- True仅支持None或原生RevisedSimplexSolver，与现有入口相同；
- 对全部seed独立逐弧累加整数资源，任何超容量seed以ValueError拒绝。
  先检查全部seed，再进行数值列重构和建RMP；不让非法seed触发任何求解。
空资源维可用；所有弧仍按A要求显式有资源向量。

每次solve拥有fresh RMP owner；默认每轮一次公开solve，
opt-in每轮一次公开solve_reoptimized，保存该真实冻结outcome；
控制器不额外cold、不访问基缓存、不复用其他CG调用的owner。

## 4. 数学约定、候选核验及有限失败

资源域P_B是图中全部满足资源约束的完整s-t路径。列为原图基项加弧项：
c_p=c_base+sum c_e，a_p=a_base+sum a_e。
完整主问题min c0+sum c_p lambda_p，A lambda [<=,=,>=] b，
lambda>=0，且有指定conv行sum lambda=1。路径资源不由主问题行代替。

每轮RMP在当前registry上解最优后，使用其原始MIN行对偶完整调用
price_resource_dag(resources, duals, tolerance=..., state_limit=..., transition_limit=...)。
本单每轮重新冷定价，没有跨轮资源状态维护。

控制器必须再次独立从原图/资源映射核验候选：
- 路径连续、完整、合法；c/a/rc及改善分类遵循旧_check_candidate核验；
- 逐弧累加资源并逐步检查容量，返回usage为正确维数的严格整数tuple，且与重构完全一致。
  返回bool或float伪装的资源量须拒绝；不采用浮点容差判断资源可行。
- 错误记录、伪造路径/资源/列/分类和数值重构不一致保守NUMERICAL_ISSUE；
  不增列，不用返回的近似字段替代原始重构c/a。

定价非OPTIMAL，包括NO_PATH、NUMERICAL_ISSUE、STATE_LIMIT、TRANSITION_LIMIT：
CG返回PRICING_FAILURE，保留同轮资源定价诊断，不能当成没有负列或正常收敛；
本轮upper/dual/rho/lower/raw gap/objective gap/allowance全部None，
accepted_path=None，不增加预算重试。可行seed存在时NO_PATH虽与数据矛盾，仍不能宣称收敛。

成功轮复用原凸性数值规则：
P=c0+c^T lambda；D=c0+b^T pi；rho=min_{p in P_B}(c_p-a_p^T pi)；
delta=min(0,rho)；L=D+delta；numerical_gap=P-L。
理由：仅将conv行对偶加delta，使所有完整资源列满足对偶约束；conv RHS=1，
因此可构造该下界。不得向无全局凸性的覆盖模型外推本公式。
objective_gap使用消去共同c0后的原始求和；固定32*ulp(绝对局部项和)及既有tolerance拒绝规则保持，
同时保留raw signed gap；不调整全局数值容差，不宣称严格LP误差上界。
重复负列拒绝、最后一轮不附加尚未求解的新列、MASTER_FAILURE、
last_valid_master/column_set_iteration/failure_iteration与旧CG同义。
完整失败轮保留其尝试registry；最终公开registry和last_valid_master属于最后有效已解轮。

## 5. 手算验收例与独立真值

### 5.1 资源真正绑定的两轮例

s->u有四条prefix：(ID,c,R,resource)
a=(a,4,0,0)，b=(b,1,1,1)，c=(c,6,2,0)，d=(d,-10,1/2,2)。
公共z:u->t为(c=0,R=0,resource=1)。资源cap=2；conv基系数1，其余conv弧系数0。
主问题conv=1，R EQ1/2，c0=0，seed=(a,z),(c,z)。

完整合法列为a/z、b/z、c/z；d/z累计3非法。
初轮lambda_a=3/4,lambda_c=1/4，P=9/2；
pi_conv=4,pi_R=1，资源最小b/z，rho=-4。
加b后lambda_a=lambda_b=1/2，P=5/2；
pi_conv=4,pi_R=-3，rho=0，正常停止。
用Revised冷、Tableau冷、Revised opt-in分别运行；各最终值和资源可行性相同，
不要求一般退化例的对偶/轨迹一致。记录opt-in实际public入口及Phase II调用，
不靠计时或仅布尔字段证明复用接线。

### 5.2 有限独立oracle族

固定72模型，每个三模式，共216次完整CG调用：
- s->u四条合法prefix i=0..3，R=i，resource=i mod2；另x：R=3/2,c=-20,resource=2；
  公共z:u->t，成本/行特征0、resource=1；cap2。seed i=0与3。
- 六组合法prefix成本：
  (4,1,3,6)，(0,2,1,0)，(-2,1,-1,3)，(0,0,0,0)，
  (7/4,-1/2,5/4,9/4)，(6,4,2,0)。
- alpha=1/2、3/2、5/2；R EQ alpha，行特征/RHS同时正反表示；
  原/反节点、弧、行、seed输入表示。6*3*2*2=72。
- 可固定非零base cost=3/8、base R=1/8，并把R RHS相应加1/8后再翻符号；
  c0按成本组索引偶/奇固定7/-3。若采用这些基项，所有期望按同一原始模型重构。

独立代码从raw数据DFS完整路径，独立资源累计过滤，用Fraction独立构造c/a；
不调用生产定价/资源转移/候选重构来生成oracle真值。
全列及每轮当前registry的LP真值由所有两列bracketing alpha顶点解析枚举：
i<j且i<=alpha<=j，lambda_i=(j-alpha)/(j-i)，lambda_j=(alpha-i)/(j-i)。
取全部可行顶点最小值再加基项/c0；不以生产LP、另一次冷CG或生产price作唯一真值。
逐轮核对原始MIN原始/对偶/rc、资源最小价、所有数值界、增加路径、注册集与终止；
最终与同一资源列域和主问题的全列真值一致。
浮点对偶按声明容差核验；不强求不同模式的浮点tie路径或退化轨迹一致。
这216调用仅作有限正确性核验，无性能统计或应用主张。

### 5.3 针对性异常检查

- 零维在普通相同支持域与旧CG对照；至少一组双资源真正绑定例。
- 非资源可行seed/图身份不一致/预算与backend非法：求解前拒绝且无RMP或pricing调用。
- 实际state/transition上限：即使已有sink候选仍PRICING_FAILURE，诊断和失败空字段符合合同。
- 首轮/后续MASTER_FAILURE、price NO_PATH/numerical、错误结果/非法usage/不一致列，
  last-valid registry与同轮outcome一致；迭代上限不追加未解列。
- 大c0消去与有符号gap规则至少有针对性回归，不建立新的benchmark笛卡尔积。
- 默认/opt-in入口次数、真实warm/允许的RMP内部coldfallback、fresh owner及不可变历史。
- 至少用小型LE/GE及行正反表示检查原始MIN符号，不只检查EQ。
不要为每一异常构造全交叉矩阵；已有辅助测试可只读参考，不修改旧测试来迁就新行为。

## 6. 允许文件与禁止项

仅可新增/修改以下16个交付路径：
1. src/silo/decomposition/resource_dag_column_generation.py
2. src/silo/decomposition/__init__.py（仅追加新公开导入/导出）
3. tests/unit/test_resource_dag_column_generation.py
4. tests/verification/test_resource_dag_column_generation_oracles.py
5. examples/resource_dag_column_generation.py
6. docs/resource_dag_column_generation.md
7. docs/README.md（必要入口）
8. docs/development_layout.md（必要模块/模型范围）
9. learning/lessons/L0010-resource-dag-cg/README.md
10. learning/lessons/L0010-resource-dag-cg/exercises.md
11. learning/lessons/L0010-resource-dag-cg/solutions.md
12. learning/CATALOG.md
13. learning/GLOSSARY.md（仅必要术语/链接）
14. .silo-dos/project_profile.md（实际B交付状态/证据，不写协调方验收通过）
15. tasks/reports/20261020-05-01_resource-dag-cg_report.md
16. tasks/INDEX.md（结构脚本重建）

既有普通CG/A/RMP/LP/其他算法模块、旧测试、旧合同、历史报告和notes字节保持不变；
不改根AGENTS/案例通告、不加依赖/build/native/CLI/schema、不转换ROADMAP阶段、
不创建通用CG/VRPTW模型、feasibility恢复、资源支配、跨轮定价缓存或性能优化。
出现超范围问题登记后停，不附带修复、不追加工作单。

## 7. 伴学、质量与报告

L0010十节按WRITING_GUIDE；至少六个稳定编号习题及可核对解答。
讲清资源可行路径域与主问题行的区别、凸性对偶下界推导、手算两轮、
冷定价与RMP复用的不同、cap为什么不能证明无负列、代码映射、研究价值及模型/浮点局限。
提供完整可执行公开API程序；实际运行例子和解答计算，verified_code填真实实现完整提交。
禁止把B的玩具对偶当C的应用证据、把RMP warm当增量定价或把正确实现称新贡献。

按已有环境指引先给当前进程PATH添加.venv/Scripts，再运行：
~~~text
python -m pytest tests/unit/test_resource_dag_column_generation.py tests/verification/test_resource_dag_column_generation_oracles.py -q
python examples/resource_dag_column_generation.py
python scripts/check_project_structure.py --write-index
python scripts/check_quality.py
git diff --check
~~~
python必须使用项目.venv解释器；正文完整程序和解答按实际提取核对。
不重装环境、不加依赖。质量失败在允许范围修复后重跑；首次失败也如实写报告。

报告写：唯一目标/原4覆盖范围、实际数据和216调用、独立真值来源与浮点判据、
unit/verification/全量数量、手例三模式与实际RMP诊断、所有失败/cap含义、
文件清单、伴学核验基线、范围差异、未覆盖义务、Git前后/缓存ahead/未push/治理哈希。
实现与文档可分本地提交，文档核验锁定实际实现哈希；用路径git log定位报告提交，
不编造自指hash。不要把源码提交等同协调方验收。

## 8. 预算与结束

本单最多首次交付和一次针对同一目标的修正复核；遇阻保留证据并停止。
216主族和针对性小例仅做正确性检查，不启动耗时矩阵、应用轨迹或新算法比较。
完成代码/质量/文档/伴学/报告/本地提交后停，等待讨论对话验收；不得自行签发或执行C。
A–E最多五项及C未通过即停保持，不增加“第六项继续完善”。
