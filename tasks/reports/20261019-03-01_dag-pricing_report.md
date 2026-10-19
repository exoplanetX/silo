# 第3步执行报告：普通DAG精确定价

## 1. 授权、起点与结果定位

执行[合同20261019-03-01](../codex/20261019-03-01_dag-pricing.md)，风险L3，
唯一实施协调为silo-solver开发；思路、签发与交付审查归silo-solver-1010。
本步只交付普通DAG全部s-t路径列域的拓扑定价、核验、L0003和本地提交。
完成后停止第3步，等待讨论对话审查；第4步CG闭环仍需独立交付。

实际起点为453699e25fea87ac6a653e91361a321c1f22d94b，main、工作区干净，
本地缓存origin/main...HEAD为0/7。已知ahead依次为cfb43a8、ad62e0f、c3704be、
8a11eff、48c242d、939fb59及本步签发453699e，均在本合同继续执行授权内。
代码起点为RMP实现48c242d，LP内核ad62e0f；本轮没有无关源码漂移。
实际执行前已读合同指定的本地规则、技术/同步镜像、现有RMP、数值常量和学习规范。

推荐配置沿用合同GPT-6 Sol/high：困难在原始行乘数、完整路径最优性与浮点分类。
这是配置建议，本报告没有通过工具切换模型，也没有开展模型对照实验。
实现/测试提交A为12bfa358850b3fe55b31086c4f98741852973b31；学习/报告提交B
通过下方命令定位。两者属于同一原子任务。
本报告自身提交在收尾后用以下命令定位，避免填写未来自身哈希：

~~~text
git log -1 --format=%H -- tasks/reports/20261019-03-01_dag-pricing_report.md
~~~

## 2. 交付接口与固定列域

新增[dag_pricing.py](../../src/silo/decomposition/dag_pricing.py)，由decomposition入口导出
DagArc、DagPricingProblem、DagPricingStatus、DagPricingResult和price_dag。
生产模块只依赖标准库和既有utils.DEFAULT_TOLERANCE；AST边界测试核对这一限制。
没有生产枚举、LP/RMP调用、CG循环或ColumnCandidate行为改动。

列域为给定有限DAG中全部s-t路径，s与t不同，允许独立ID的平行弧；全图都须无环，
包括不可达分量。节点/弧/行ID唯一非空白，端点/行引用必须存在。
路径允许已在RMP中出现，图结构决定可行性；资源、时间窗、容量和分支限制未建模。

每条路径的原成本c=base_cost+sum(d_e)，完整行向量a=base_coefficients+sum(a_e)，
约化成本为c-a^T*pi，pi采用最小化原始行坐标。基项只计一次；RMP全局常数c0不进入rc。
输入pi的键集合须恰等于row_names，稀疏弧/基系数的省略已知坐标取零，空行集合法。
构造记录复制序列和映射，冻结数据并提供只读结果快照；更换pi重新计算。

OPTIMAL保留达到最小值的连贯路径、原成本、全部声明行系数、重构rc与严格改善标志，
包括最佳路径非改善的情况。NO_PATH及NUMERICAL_ISSUE均无候选路径/映射，
cost、reduced_cost、is_improving均为None。非法输入在求解前明确ValueError/TypeError。

## 3. 算法、证明与数值约定

令w_base=c_base-a_base^T*pi、w_e=d_e-a_e^T*pi，以L(s)=w_base按全图拓扑序松弛。
路径加性给出rc=w_base+sum(w_e)。处理顶点v时全部入邻点已求最优；任意到v的路径
可用最优前缀替换。若替换前缀与同一后缀产生重复顶点，原图将存在有向环，故DAG中
替换合法。由拓扑归纳，精确算术下L(t)达到全部s-t路径的最小rc；负权无需额外处理。

中间标签按原数值严格比较，完全相等才比较完整arc_id元组。到同一顶点的两条不同
路径不可能互为严格前缀，否则出现回到该顶点的环；因此拼接相同后缀保持字典序，
保留一个字典序最小的同值前缀充分。拓扑堆、出弧排序及行点积键排序固定输入排列行为。

改善容差只用于最终重构rc<-tolerance，等于负阈值为False。路径选出后独立汇总原成本
与完整行向量，重算rc并与DP标签比较：绝对差须不超过既有1e-9，且两者改善分类相同。
一致性阈值不随用户改善容差改变。有限输入运算溢出/非有限或上述核对失败时返回
空字段NUMERICAL_ISSUE；全图弧权都检查，包括不可达弧。

两项具体数值结果：base=1e16、弧成本1与-1e16时，DP标签0、重构原成本1，保守失败；
base=-1e-8、弧成本-1e-9与1e-8时，DP略低于-1e-9而重构恰在边界，两者改善分类
不同，即使差小于1e-9仍保守失败。两者都未发布错误候选或False结论。
近阈值前缀0与-6e-10配公共后缀-6e-10，实际选择后者得到-1.2e-9、True；
禁止以最终改善容差合并中间标签。

标量松弛数量O(|V|+|E|)。本Python实现还包含堆/排序、稀疏点积键排序、完整路径元组
复制/比较，最长路径D带来的路径处理可达O(|E|D)、标签路径存储O(|V|D)，
完整列重构为O(|J|D)。未把整个实现宣称为无条件线性时间或性能优势。
极端尺度、下溢及近等值路径排序仍受浮点限制，完整性证明与有限数值结果分别表述。

## 4. 独立完整路径真值与RMP桥接

[unit测试](../../tests/unit/test_dag_pricing.py)共62项，覆盖手算/pi更新、严格阈值、
完整元组平局、平行弧、死分支/孤立节点、输入排列/点积顺序、所有权、非法图与行、
有限输入运算溢出、重构不一致及导入边界。
[verification测试](../../tests/verification/test_dag_pricing_oracles.py)共197项。

独立oracle以DFS枚举完整路径，直接从原始弧成本和行向量按Fraction求和并计算c-a^T*pi，
没有调用生产拓扑、弧权、标签、重构或求和助手。比较状态、最小值、全路径字典序、
连贯性、原成本、全部列坐标和严格改善标志。

固定族为4节点全向前6弧的全部64子图，6弧成本(-1,2,3,0,-2,1)，
r系数i%2、q系数i%3-1，base_cost=1、base_conv=1。对偶为(r,q,conv)的
(2,-1,3)、(-1,2,-2)、(0,0,0)，共192个图/对偶比较。
64图中47个有路、17个无路，合计72条完整路径；3组对偶对应216次路径值评估。
另有3项平行弧/基项/空行集核验，各自交换节点/弧输入顺序，以及2项实际RMP桥接。
这些是有限图族的穷尽路径真值，不是一般定理的实验替代。

两个原生后端revised与tableau分别运行显式桥接：两路径原成本A=5、B=3，
base_cost=1、base_conv=1，RMP全局常数7、conv=1。
初始仅A时目标12、pi=5；定价B的原成本3、列系数1、rc=-2。
显式add_column后重新求解目标10、pi=3，再定价返回已存在B、rc=0、False。
每次先检查RMP状态，再用其经核验乘数。未增加自动驱动或路径去重。

## 5. 实际检查、失败与环境

先写合同约定的区分性测试，再完成参考实现；没有为新API制造import-error式red。
首次合同targeted命令通过：386 passed in0.70s，其中新增259项、原有相关回归127项。
四个改动Python文件的Ruff检查通过，首轮没有需要修复的失败，也未放松数学断言。

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py tests/unit/test_decomposition_boundary_smoke.py tests/unit/test_decomposition_column_candidate.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

完整check_quality.py exit0：1742 passed in12.08s，随后Ruff All checks passed，
无跳过或警告。--write-index、普通结构检查均通过：142份合同、139份报告、
96模块、455个本地链接（当前摘要完成链接增加前）。git diff --check通过。
代码/测试在该次全量后保持不变；后续收尾只更新文档与真实基线字段。
提交A前scope为13个允许路径（当前摘要未更新），9个交付Markdown的严格UTF-8、
围栏、公式定界符及364个本地链接通过，L0003十节与四题稳定编号通过，
三个只读复核blob与全量受测文件一致。当前摘要更新后的结构复查为142份合同、
139份报告、96模块、458个本地链接；最终scope为全部14个允许文件，10份交付
Markdown的严格UTF-8、围栏、公式及402个本地链接通过，十节/四题/真实verified_code
通过。代码和测试与全量检查及只读复核blob仍一致。
收尾校验的首次工具包装因JavaScript模板字符串中的反引号未能解析，仓库命令未执行；
修正包装后上述校验通过。此工具输入错误未引起源码或测试改动。
正文代码块及习题有限计算已单独实际运行，具体见下一节。
使用本检出.venv/Scripts/python.exe，Python3.13.9、pytest8.4.2；
silo.__file__为E:/OneDrive/workspace/codex/silo-solver/src/silo/__init__.py。
console PATH在检查时前置本检出.venv/Scripts；未安装/升级依赖、未新建worktree。
沿用已有继承系统包的环境，本步没有验证从锁定环境干净重建。
生产和新增oracle均未调用外部求解器，没有运行性能或研究规模实验。

## 6. L0003交付与实际教学核对

[L0003正文](../../learning/lessons/L0003-dag-pricing/README.md)、
[练习](../../learning/lessons/L0003-dag-pricing/exercises.md)、
[解答](../../learning/lessons/L0003-dag-pricing/solutions.md)版本0.1.0，保持十节体例。
给出列域、基项、原始乘数、前缀替换/字典序证明、数值反例和完整可执行例；
L0001/L0002只引用其稳定入口，没有改写正文或历史身份。

从正文提取唯一完整Python代码块并直接exec编译执行，手算图rc=-3，
revised/tableau两后端均通过目标12->10、rc=-2->0的显式桥接断言。
四道稳定编号的核对分别为：

- L0003-E01：直接从全部三条原始路径重算，三组pi的rc分别为[-3,1,3]、[0,2,5]、
  [4,3,7]，并核对选路及改善标志。
- L0003-E02：按第3节拓扑归纳与无严格前缀条件核对证明；现有平局测试提供有限例，
  没有将测试通过写成一般证明。
- L0003-E03：运行严格前缀反例得到-1.2e-9、True；大数消去及改善分类分歧均返回
  空字段NUMERICAL_ISSUE。
- L0003-E04：正文代码对两个后端实际桥接，conv=1的精确全路径下界7+3=10，
  并说明一般完整LP结论还需要有效RMP见证与真正非负的全部约化成本。

实现提交产生前元信息保持draft/null；实际提交A产生后更新checked、
verified_code=12bfa358850b3fe55b31086c4f98741852973b31、verified_on=2026-10-19。
API参考另存[dag_pricing.md](../../docs/dag_pricing.md)，目录与依赖说明同步更新。

## 7. 唯一独立只读复核

按合同使用一次red_team_reviewer，问题限本定价对象的数学、实现及测试证据。
它返回代码与数学方向GO、最终交付条件GO，decision_impact=strengthen，
没有fatal/major/minor代码修正项；条件是主线程完成全量质量、教学/文档与范围核对。
它未运行实验、写文件或调用其他服务，教学正文不在其阅读范围。
一般证明、独立枚举和双后端桥接各自提供证据，复核结论未重复计为测试结果。

其读取的三个blob如下，提交前核对与实际受测文件一致：

~~~text
src/silo/decomposition/dag_pricing.py eeff9ca4b8733520f77840e3c9e8c76f64f2cc6b
tests/unit/test_dag_pricing.py 7dae323ad7850bfa4fe20b8f3830df2adc40ce70
tests/verification/test_dag_pricing_oracles.py 0248d31ba3c1bf50d8064e14cbc21b741587ef19
~~~

## 8. 范围、本地Git与停止位置

允许范围为新定价模块、decomposition导出、新增两个测试、三个API/目录文档、
L0003三文件、学习目录、当前摘要、本报告及派生INDEX，共14个文件。
未修改LP/core/modeling/presolve/MIP/CLI/io/外部接口、restricted_master.py、
既有ColumnCandidate/toy/CG驱动、L0001/L0002、旧合同/报告、研究资产、
ROADMAP/阶段文件/其他门控、依赖/build/native或Skill/Agent定义。
实现/测试提交A只含四个Python文件，提交后cached origin差异0/8，只有本任务文档
待收尾。沿用既有仓库身份的单次命令Git参数，不改全局/仓库身份配置，无提交失败。
最终Git范围为合同全部14个允许文件；代码/测试提交A和文档收尾提交B保持同一任务身份。
Git mode=local-commit，push not_attempted；origin/main是本地缓存，本步不作实时远端断言。

文档收尾首次提交后实际查询的Remote Sync Proof：

- `git status --short`：空，工作区干净。
- `git branch --show-current`：main。
- `git log --oneline -5`：本任务文档收尾、12bfa35实现、453699e签发、939fb59第2步文档、
  48c242d第2步实现。
- `git rev-list --left-right --count origin/main...HEAD`：`0 9`，已知起点7个加本任务2个提交。
- `git push result`：not_attempted。
- `remote_sync_status`：local_ahead_origin。

实际查询记录随同一文档收尾提交修订保存，最终提交由第1节Git历史命令定位，
结束回执再次核对工作区、分支及cached origin差异。本步没有实时远端查询或推送证明。

完成后停在第3步。第4步仅建议连接RMP与完整定价的窄范围控制器，须另行批准合同，
建议GPT-6 Sol/high，困难在列身份、行坐标一致、失败传播与终止条件。
当前定价无资源可行性、增量维护或性能优势主张；浮点False可包含小幅负rc，
模块不宣告完整主问题最优。既有近相关等式误报UNBOUNDED数值债保留原记录，
本步没有修复底层LP或提升非最优诊断的证据强度。
