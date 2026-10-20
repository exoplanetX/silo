# 单元A交付：固定整数资源DAG的冷定价参考器

## 1. 元信息、目标归属与授权

- ID：20261020-04-01_resource-dag-pricing。签发前已扫描同日合同与报告：
  TT01=lp-unbounded-check、TT02=rmp-reoptimization、TT03=cg-reoptimization；TT04/RR01空闲。
  A是[原七步收尾计划](../../docs/seven_step_completion_plan_20261020.md)的单元，不改称“原第10步”。
- 原里程碑：原第3步的资源可行性缺口；任务类型L2，新增一个有界冷资源定价器。
  原目标保持：同一SILO承载OR研究并交付伴学材料；本单只回答固定资源路径域的冷定价。
  不实现B列生成接入、C应用门控、D增量状态或E性能评价。
- 人类授权已在开发对话直接核验：01a15208-bea9-7030-aacc-95d785e8fa58，
  turn 01a159c2-87ed-7773-a738-59d5d0bb7f28，用户对逐单签发、独立审查、
  保留本地未推送状态及两项治理变动的明确问题选择“授权发送启动消息（推荐）”。
  当前讨论对话负责协调、签发和验收，开发对话负责实施获签合同。
- 签发前HEAD=77c62bb0017d71d338d326e2bf968660ecb3db1f，main，
  cached origin/main...HEAD=0/24。即时远端本轮未核查。用户接受已登记24个本地提交
  及本次签发提交；不因该已知状态重复询问，不push。
- 两项已获准原样保留的治理变动：
  AGENTS.md，SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638；
  根研究主题固定_严重反面案例通告_20261020.md，SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
  不暂存、提交、覆盖、还原或挪动；其他未登记变化先保留并停报。
- 从本合同的签发提交开始执行：用git log -1 --format=%H -- 本合同路径定位。
  src/tests/examples自f4cc36e未变；按已有PATH步骤最近核验4075项、Ruff和结构通过，
  该记录不冒充本次新接口验证。
- 来源：原三阶段七步原文及上述收尾计划、note26首版非负可加资源范围、
  note28的充分状态冷基线、L0003及现有普通DAG定价。
  ROADMAP Phase9仍open/parked，native deferred/unapproved，Phase10 not started。
- Git mode=local-commit。Expected report：
  tasks/reports/20261020-04-01_resource-dag-pricing_report.md。
- Learning delivery：新L0009-resource-dag-pricing三文件、目录和必要术语。
  已扫描L0001–L0008，L0009空闲。建议GPT-6 Sol/high；不表示实际切换。

## 2. 开始阅读及唯一完成线

先读用户目录research-lessons/CASE-20261020-01.md、项目根案例通告、AGENTS.md、
tasks/README.md（尤其6.8/6.9）、当前摘要与technical_route/remote_sync_proof，
learning/README.md和WRITING_GUIDE.md，再读本合同、收尾计划A、notes26/28、
src/silo/decomposition/dag_pricing.py及其unit/verification测试。

唯一完成线：在下列固定支持域中实现资源状态DP、可追溯状态/转移上限、完整候选重构，
并通过独立资源路径枚举、旧接口不变、完整质量及L0009核验，交付后停止。
资源可行性使用整数精确运算；目标计算沿SILO现有浮点参考语义。
“精确定价”指完整声明路径域的冷搜索，不表示任意尺度符号最优或新算法贡献。

## 3. 数学对象、状态与最小接口

给定既有不可变DagPricingProblem图G，每弧有成本c_e及主问题行特征a_e；
基项保留c_0、a_0。另给非负整数容量向量B及每弧同维非负整数资源d_e。
初始资源全0，路径每一步r'=r+d_e必须逐维<=B；资源判断不使用任何浮点tolerance。
路径列c_p=c_0+sum c_e，a_p=a_0+sum a_e，最小化约化成本rc_p=c_p-pi^T a_p。
主问题行特征可正可负；资源向量与主问题行系数是不同对象，不得相互替代。

新模块src/silo/decomposition/resource_dag_pricing.py公开：

~~~text
ResourceDagPricingProblem(graph: DagPricingProblem,
                         resource_limits: tuple[int, ...],
                         arc_resources: Mapping[str, tuple[int, ...]])
ResourceDagPricingStatus:
    OPTIMAL / NO_PATH / NUMERICAL_ISSUE / STATE_LIMIT / TRANSITION_LIMIT
ResourceDagPricingResult:
    status, arc_ids, cost, row_coefficients, reduced_cost, is_improving,
    resource_usage, states_discovered, transitions_checked, message
price_resource_dag(problem, dual_values, *,
    tolerance=DEFAULT_TOLERANCE, state_limit=100000, transition_limit=1000000)
    -> ResourceDagPricingResult
~~~

允许调整私有细节，不改变这些公开含义。通过decomposition/__init__.py导出上述四项。
问题与结果使用冻结dataclass。问题通过graph字段组合现有DagPricingProblem，不继承它，
避免继承默认字段的构造顺序问题；输入Mapping允许普通dict，但须防御性复制后只读封装。
resource_limits和每个弧资源必须为tuple；
type(x) is int且x>=0，拒绝bool、浮点数、负数；维数有限可为0。
arc_resources必须为Mapping，键集合精确等于所有图弧ID，值维数一致；
0维时每个弧仍显式对应()。防御性复制并只读封装资源映射，不能由外部字典修改问题。
不增加资源重置、负资源、连续资源、时间窗、访问记忆、一般有环路径或VRP规则。

dual_values为Mapping，键精确匹配graph.row_names，各值有限；
tolerance有限且>0；state_limit/transition_limit满足type(x) is int且>0。
非法输入明确抛TypeError/ValueError；不得作为NO_PATH或预算状态发布。
已有DagPricingProblem保留全图无环、ID和数值验证。

## 4. 冷DP、数值边界和停止语义

- 每次重新计算弧约化成本及状态，无跨调用缓存。
- 输入验证 -> 与普通price_dag相同的全弧权重/基项浮点预计算 -> 初始化(s,0) -> 有界搜索
  -> 重构核验；无效输入必须在实际搜索前拒绝。
- 按原图稳定拓扑序展开，拓扑平局按node ID；出弧按arc ID；同节点资源tuple排序。
  状态为(v,r)，只在完全相同state内保留最低(label,完整arc_ID_tuple)。
  不按物理node压成一个标签，不做跨资源支配或heuristic剪枝，不枚举全部完整路径。
- 同状态标签严格比较，tolerance不影响松弛。实际label相等时按完整path tuple选取。
  汇节点不再展开；所有保留汇state按(label,path tuple)比较，不优先最小资源用量。
- 完成后独立从原始路径数据重构c_p、所有声明行a_p、rc及整数resource_usage；
  核验连通、端点、每步资源、终态资源一致。资源重构不用生产递推缓存当真值。
- 与普通price_dag的数值保护对齐：有限输入运算产生非有限值、重构rc与label差超过
  既有DEFAULT_TOLERANCE、二者在-用户tolerance两侧导致改善判别不同，保守返回NUMERICAL_ISSUE。
  不引入新全局精度、缩放或容差规则，不改旧模块。
- 明确浮点限制：重构只核验所选候选，不能发现已因舍入而丢弃的其他路径；
  任意近等价/大尺度实数最优性和全局规范平局不受本任务保证。
  小dyadic真值族单独核对真正最优集。
- 0资源维、预算充足且sink无出弧的正常同域实例，与price_dag结果核对。
  sink有出弧仍支持，但本接口在sink停止；不保证与旧接口在sink之后额外工作造成的
  极端数值诊断相同。该区别只说明诊断范围，不改变s-t路径域。

结果规则：
OPTIMAL只在完整有界搜索及重构通过后发布；即使非改善也返回最佳路径与完整列数据，
resource_usage为tuple[int,...]（0维成功是()），is_improving=(rc<-tolerance)。
NO_PATH只在完整搜索无汇state时发布。
所有非OPTIMAL结果均arc_ids=()、cost/reduced_cost/is_improving/resource_usage=None、
row_coefficients为空只读映射；不得发布中途incumbent为最优、无负列或False。
计数是本次实际工作快照，后续调用不得篡改；message清楚说明失败或限制。

## 5. 状态与转移预算的精确定义

states_discovered：已成功插入状态表的不同(v,r)数，包含源、汇和死路state，
不含标签替换、资源不可行后继、尚未插入的触发state；中断时不是全实例状态总数。
transitions_checked：已发现非汇state实际检查的(state,outgoing_arc)数，
同一原弧可在不同r上重复计数，资源不可行尝试也计入。
输入验证/全弧权重预计算不算状态扩展转移，不能把该计数说成总运行成本。

固定顺序：
1. 下一次弧检查前若transitions_checked==transition_limit，返回TRANSITION_LIMIT；
   未检查弧不计数。
2. 实际检查该弧，transitions_checked加1，算整数资源；资源不可行则跳过。
3. 后继state已存在时允许比较/替换，不增加state计数，即使state_limit已满。
4. 后继为新state且states_discovered==state_limit时返回STATE_LIMIT；
   触发弧已计入transitions，后继未插入。
5. 否则插入后继，states_discovered加1。

刚好用尽预算且无剩余必要工作，仍正常结束；不能仅以计数等于上限误报LIMIT。
已有汇候选但还有未检查工作时，LIMIT必须清空候选。
若算术预计算失败，计数反映实际已完成阶段，可为0；不能虚构已探索源状态。
默认上限是受控搜索边界，不承诺多项式复杂度、低内存或加速。

## 6. 必须手算与版本化验证

最小反例：nodes(s,u,t)，a:s->u(cost0,resource2)，b:s->u(cost1,resource0)，
c:u->t(cost0,resource1)，capacity(2)，无主问题行/基项。
普通最便宜a,c资源3不可行；本模块应返回("b","c")、cost=rc=1、usage=(1,)、
is_improving=False。完整states=4、transitions=4。
state_limit=4/transition_limit=4恰好正常；state_limit=3或transition_limit=3必须
返回相应LIMIT并清空候选（转移3时已经有汇候选也不能称完成）。

固定独立oracle轴：
- nodes=(s,a,b,t)，六条全向前弧按(sa,sb,st,ab,at,bt)固定编号j=0..5；
  全部64个子图mask，缺弧不重编号。
- cost_e=((3*j)%7-3)/4，弧行特征R=((j%3)-1)/2；
  row_names=(R,conv)，base_cost=1/4，base_coefficients={R:1/8,conv:1}。
- 三资源配置：0维cap()且弧资源()；一维cap(2,)且弧(j%3,)；
  二维cap(2,2)且弧(j%2,(j//2)%2)。
- 对偶(R,conv)=(-1/2,-1/4)、(0,0)、(3/4,1/2)。
- 原序/反序节点、弧、行及映射插入顺序两种表示。
  共64*3*3*2=1152次定价；参数化组织自定，报告区分图/表示/调用/pytest项。
- 独立DFS从原始公开图数据列全路径，再以独立整数求和筛资源、
  Fraction从输入浮点精确值重算c/a/rc；不能调用生产拓扑、资源转移、重构或数值helper。
  成功候选在独立最优集中，dyadic族按完整path tuple选规范最优；
  无资源可行路径则NO_PATH；逐字段核对整数usage、完整行向量、原始成本与改善判别。

额外unit必须覆盖：不同资源state不能按node合并；同state改进与近阈值严格标签；
多资源权衡；并行弧、0消耗和0容量；不同汇资源state同成本按path tuple平局；
不可达；sink有出弧不展开；空资源维退化；预算恰好/超一及已有汇仍LIMIT；
同state替换不额外吃state预算；不合法/缺失/额外资源、整数精度超过2^53仍不转float；
非法对偶/上限/tolerance；外部变更与多次不同pi冷求解互不污染；
全弧非有限运算与重构不一致/改善跨阈值的保守NUMERICAL_ISSUE。
数值保护故障可做限定注入，但资源路径真值不能由mock供给。

## 7. 唯一允许变更的路径

1. src/silo/decomposition/resource_dag_pricing.py（新）
2. src/silo/decomposition/__init__.py（仅四项导出）
3. tests/unit/test_resource_dag_pricing.py（新）
4. tests/verification/test_resource_dag_pricing_oracles.py（新）
5. examples/resource_dag_pricing.py（新，小型可运行原生例）
6. docs/resource_dag_pricing.md（新）
7. docs/README.md（仅导航）
8. docs/development_layout.md（仅新模块入口与真实支持域）
9. learning/lessons/L0009-resource-dag-pricing/README.md（新）
10. learning/lessons/L0009-resource-dag-pricing/exercises.md（新）
11. learning/lessons/L0009-resource-dag-pricing/solutions.md（新）
12. learning/CATALOG.md（仅新篇及阅读顺序）
13. learning/GLOSSARY.md（仅本模块新资源术语及限定约定）
14. .silo-dos/project_profile.md（A实际状态、检查、未答义务）
15. tasks/reports/20261020-04-01_resource-dag-pricing_report.md（新）
16. tasks/INDEX.md（仅生成）

本合同由协调方创建后不可改；旧测试、旧合同/报告、旧学习篇、dag_pricing、
CG/恢复器/RMP/LP/core等其他生产模块全部禁止修改。
不改研究笔记/原始探针、ROADMAP/阶段、规则/AGENTS、native、依赖/build、CLI/JSON、
公共Solution；不得加入性能、资源支配、全局框架或跨对偶缓存。
发现范围外问题记录并停报，不能顺手修复。

## 8. L0009、执行检查及验收

L0009按WRITING_GUIDE十节：原问题、(v,r)充分性、拓扑归纳、上述手例/预算、
代码与独立oracle映射、冷基线研究作用及浮点/资源爆炸/访问记忆边界；
至少六道稳定题号和完整解答，覆盖手算、节点级合并反例、双资源、对偶变化、
预算中断与改善语义、冷基线和研究贡献的辨析。
正文完整程序在双资源/核心反例上实际运行，明确真实实现提交verified_code；
禁止用合同/文档提交冒充已核验代码。不能写已实现增量定价或VRPTW。
先实现并测试提交A，再按实际实现哈希提交学习/文档/报告，正常最多两次本地提交。
不为本任务重写既有教学正文。

必跑：
~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_resource_dag_pricing.py tests/verification/test_resource_dag_pricing_oracles.py
& ./.venv/Scripts/python.exe examples/resource_dag_pricing.py
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~
另实际核对L0009程序/解答、UTF-8、公式与代码围栏、实际代码基线和受影响链接。
本单无独立性能实验；不安装新依赖，不为了绿灯弱化/跳过旧测试。
全量检查通过且代码未再改后，文档收尾只做受影响轻量检查，无需重复跑同一全量。

验收同时回答：合同内接口/资源/数值/预算/1152调用/教学是否合格；
原3覆盖了非负整数可加资源子类多少；未覆盖时间窗/访问记忆等哪些；
本单没有创新或性能结论。局部合格不等于原研究全部完成。

## 9. 停止、报告与交付

本单仅A；开发自检后交付并停止，等待讨论对话审查，不自行B/C或另开能力线。
本计划A至多一次初次交付和一次同目标针对性修正；需要修正时协调方新建RR02，
原合同不改。第二次仍有阻断则停止本轮并登记欠账，不追加任务。
签发前理论/证据服务只读审查不算执行交付次数，也不冒充实验。

报告记录：实际起点/实现/文档提交、16路径scope、1152调用与pytest项的区别、
手例/边界计数、输入/结果只读与数值实际范围、学习完整程序/解答核对、
所有失败及修正、质量命令、原3覆盖与未答、Git status/branch/log5/cached差异、
push=not_attempted、remote_sync_status=dirty_worktree及两治理哈希原样保留。
不在提交内容里预填自身未来哈希，用git log -1 --format=%H -- 报告路径定位。
若提交身份未配置，可仅在该次命令复用既有commit身份，不改Git全局配置。
完成后停止；不得自行向其他对话发消息。由协调方基于用户已授权的有界清单跟踪。

签发前theory_architect与experiment_auditor只读复核均支持本单；已采纳充分状态、
计数顺序、LIMIT空候选、dyadic独立最优集、零维及sink数值边界等意见。
本接口采用组合而非继承，不需要子类keyword-only补丁；输入dict按防御性复制处理。
服务未执行实验、未写文件，意见不计为1152次调用或新增测试。

