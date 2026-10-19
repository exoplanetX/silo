---
lesson_id: L0003
title: DAG精确定价与完整性核验
topic: decomposition.dag-pricing
version: 0.1.0
status: checked
created: 2026-10-19
updated: 2026-10-19
verified_code: 12bfa358850b3fe55b31086c4f98741852973b31
verified_on: 2026-10-19
source_tasks:
  - 20261019-03-01_dag-pricing
---

# L0003｜DAG精确定价与完整性核验

[总目录](../../CATALOG.md) · [API参考](../../../docs/dag_pricing.md) ·
[L0001对偶](../L0001-lp-duality/README.md) · [L0002受限主问题](../L0002-restricted-master/README.md)

## 1. 问题与学习目标

RMP已返回行乘数后，定价需要回答一个范围明确的问题：在给定的全部合法列中，
最小约化成本是多少，哪一列达到它？本篇选取普通有限DAG的全部s-t路径作为列域，
以拓扑动态规划建立不截断候选的参考定价算法。

读者应能把原始最小化乘数转换为约化弧权，证明最优前缀递推，重建原始列数据，
并用独立全路径枚举核对。还要区分原成本与约化成本、基项与RMP全局常数、
算法完整性与浮点边界，以及定价结果与整个主问题结论。

## 2. 前置知识、符号与假设

前置为L0001的原始行坐标与L0002的最小化乘数pi。图G=(V,E)有限、全图有向无环，
源s与终点t不同。平行弧有不同ID；列域U恰为图中全部s-t路径，包含RMP已有路径。
图结构决定全部可行性，尚无容量、时间窗、资源预算、分支谓词或服务规则。

每弧e有成本d_e和稀疏行向量a_e，固定原始行集合为J，给定最小化乘数pi。
每条路径的基成本c_base与基向量a_base各计一次：

\[
c_p=c_{\rm base}+\sum_{e\in p}d_e,\quad
a_p=a_{\rm base}+\sum_{e\in p}a_e,\quad
\bar c_p=c_p-a_p^\top\pi.
\]

pi键集必须恰好覆盖J，稀疏向量省略的已知行取零。所有输入数值有限；J可为空，
对应空pi。RMP全局目标常数c0与c_base不同：c0只加在RMP目标一次，c_base是每个列变量
的单位成本，因此进入每条路径的定价。凸组合行系数1可用a_base表示，不沿弧重复计入。

## 3. 手算例子

节点s,a,b,t，J=(A,B,conv)，c_base=1、a_base(conv)=1，其余基系数为零。

| 弧ID | 端点 | 成本 | 非零行系数 |
|---|---|---:|---|
| sa | s→a | 2 | A:1 |
| at | a→t | 3 | B:1 |
| sb | s→b | 1 | 无 |
| bt | b→t | 1 | 无 |
| st | s→t | 7 | A:1 |

取pi=(3,4,2)，基项约化成本为1-2=-1，弧权依次为-1、-1、1、1、4。
全部三条路径可直接核对：

| 路径 | 原成本 | (A,B,conv) | 约化成本 |
|---|---:|---|---:|
| (sa,at) | 6 | (1,1,1) | -3 |
| (sb,bt) | 3 | (0,0,1) | 1 |
| (st) | 8 | (1,0,1) | 3 |

定价选择(sa,at)，原成本6，rc=-3，为改善列。原成本最便宜的(sb,bt)并非此时的
最小约化成本路径。按拓扑序，L(s)=-1、L(a)=-2、L(b)=0、L(t)=-3。

同图换pi=(2,3,1)时，三条路径rc为0、2、5，仍选(sa,at)，不改善。
换pi=(1,1,0)时rc为4、3、7，选择(sb,bt)，也不改善。
这里pi是输入参数，不宣称这三组数都来自某个RMP最优解。

## 4. 原理推导与正确性依据

### 4.1 为什么约化成本可分成弧权

把列数据代入最小化约化成本并分配内积：

\[
\bar c_p=
\underbrace{c_{\rm base}-a_{\rm base}^\top\pi}_{w_{\rm base}}
+\sum_{e\in p}\underbrace{(d_e-a_e^\top\pi)}_{w_e}.
\]

行坐标没有改变，因此不需要把pi再次翻成最大化乘数。基项只计一次，RMP全局常数
不在单列约化成本中。固定pi后，路径定价就是允许负弧权的DAG最短路问题。

### 4.2 拓扑递推与最优前缀

初始化L(s)=w_base，其余不可达。按全图拓扑序，对每条e=(u,v)松弛：

\[
L(v)=\min_{e=(u,v),\ u\ {\rm reachable}}\{L(u)+w_e\}.
\]

对任一到v的路径，最后一弧之前是到其尾点u的路径。拓扑序处理v之前，所有这些u
已经完成。归纳假设其标签是最优前缀；用更低成本前缀替换原前缀，只改变可加成本。
替换仍是一条合法路径：若前缀与后缀除连接点外再次相交，就形成有向环，与DAG假设矛盾。
故递推取到了全部候选最后弧中的最优值，L(t)最小化整个U。t不可达时U为空。
负权不破坏这个证明，因为没有尚待回头更新的环或资源状态。

### 4.3 完整路径平局

数值完全相等时，保留完整弧ID元组较小的路径，例如(a,z)优于(b,c)，不按最后一弧
比较。同终点的两条DAG前缀不能互为真前缀，否则较长者从该终点出发又返回它，产生环。
因此把同一后缀接在两个前缀后，字典序保持。每个节点保留一条最佳数值/字典序前缀足够。

精确算术下以上说明算法完整性。浮点实现可能发生消去或近等值排序误差，数值保护
支持诚实失败，不把有限数值运行升级为一般精确证明。

## 5. 算法到代码的映射

| 工作 | [dag_pricing.py](../../../src/silo/decomposition/dag_pricing.py)中的职责 |
|---|---|
| 图、行与数据所有权 | DagArc、DagPricingProblem：冻结记录、tuple与复制后的只读系数映射 |
| 全图无环验证与处理顺序 | `_topological_order`：包括不可达分量的堆式拓扑序 |
| 原始最小化弧权 | `_dot`、`_sum`：稳定行顺序与fsum汇总，拒绝非有限运算 |
| 严格标签与完整平局 | `price_dag`：每条可达弧松弛一次，比较(数值,完整弧元组) |
| 原始列重建 | 从选中arc_ids重新汇总成本/全部行系数，再重算rc并核对标签 |
| 结果状态 | DagPricingResult、DagPricingStatus：OPTIMAL、NO_PATH、NUMERICAL_ISSUE |

实现不缓存旧pi的标签、前驱或rc，不导入LP、RMP、外部solver或枚举oracle。
测试/教学可把返回cost与row_coefficients显式交给RMP.add_column，变量名由调用者指定。
旧ColumnCandidate要求非零向量与定价元信息；本模块保留合法零向量，不改变该旧约定。

标量松弛数为O(V+E)，但本参考实现还付出拓扑堆、弧排序、稀疏行点积和键排序成本。
设最大路径长度D≤V-1，完整元组复制/平局比较最坏可达每弧O(D)，标签路径存储可达O(VD)；
重构完整J坐标还需要O(|J|D)的汇总。故整体Python实现不能无条件称为线性时间。
这些明确成本用于保持参考实现可读，不构成加速主张。

## 6. 核验与复现

从项目根目录运行下例；前半核对第3节，后半只做一次显式RMP加列，并分别核对两个后端：

```python
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition import DagArc, DagPricingProblem, DagPricingStatus, price_dag
from silo.decomposition import RestrictedMasterProblem
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

problem = DagPricingProblem(
    ["s", "a", "b", "t"],
    [DagArc("sa", "s", "a", 2, {"A": 1}), DagArc("at", "a", "t", 3, {"B": 1}),
     DagArc("sb", "s", "b", 1), DagArc("bt", "b", "t", 1),
     DagArc("st", "s", "t", 7, {"A": 1})],
    "s", "t", ["A", "B", "conv"], base_cost=1, base_coefficients={"conv": 1},
)
priced = price_dag(problem, {"A": 3, "B": 4, "conv": 2})
assert priced.status == DagPricingStatus.OPTIMAL
assert priced.arc_ids == ("sa", "at")
assert priced.cost == 6 and priced.reduced_cost == -3 and priced.is_improving
assert priced.row_coefficients == {"A": 1, "B": 1, "conv": 1}

bridge = DagPricingProblem(
    ["s", "a", "b", "t"],
    [DagArc("sa", "s", "a", 1), DagArc("at", "a", "t", 3),
     DagArc("sb", "s", "b", 1), DagArc("bt", "b", "t", 1)],
    "s", "t", ["conv"], base_cost=1, base_coefficients={"conv": 1},
)
for backend in (RevisedSimplexSolver(), TableauSimplexSolver()):
    seed = Model(variables=[Variable("A")],
                 constraints=[Constraint("conv", {"A": 1}, ConstraintSense.EQ, 1)],
                 objective=Objective({"A": 5}, OptimizationSense.MINIMIZE, constant=7))
    rmp = RestrictedMasterProblem(seed)
    before = rmp.solve(backend)
    assert before.status == SolverStatus.OPTIMAL  # 先核对状态，才使用乘数。
    assert before.objective_value == 12
    column = price_dag(bridge, before.dual_values)
    assert column.status == DagPricingStatus.OPTIMAL
    assert column.arc_ids == ("sb", "bt") and column.cost == 3
    assert column.reduced_cost == -2 and column.is_improving
    rmp.add_column(name="B", cost=column.cost, row_coefficients=column.row_coefficients)
    after = rmp.solve(backend)
    assert after.status == SolverStatus.OPTIMAL
    assert after.objective_value == 10 and after.dual_values == {"conv": 3}
    final = price_dag(bridge, after.dual_values)
    assert final.status == DagPricingStatus.OPTIMAL
    assert final.arc_ids == ("sb", "bt") and final.reduced_cost == 0
    assert final.is_improving is False  # 已加入的路径仍在完整列域内。
```

RMP的全局常数7使目标为12→10；两条路径的单位成本为5与3，因此pi从5变为3，
定价rc为-2→0。把7再次加进定价就会改变列的语义。上述调用没有通用CG循环或自动列名协议。

[独立枚举测试](../../../tests/verification/test_dag_pricing_oracles.py)用自建邻接表、
完整DFS和Fraction直接汇总原始列数据，不调用生产拓扑/弧权/重构助手。
固定4节点全向前6弧的64个子图配3组正/负/零对偶，共192个问题；其中47个图有路、
17个无路，全部图共72条路径，对应216次完整路径/对偶计算。另有平行弧和人工桥接核验。

```powershell
python -m pytest tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py -q
```

完整检查、教学复算与真实代码基线记录在
[执行报告](../../../tasks/reports/20261019-03-01_dag-pricing_report.md)。

## 7. 研究意义与可扩展问题

当前能力为指定普通DAG列域提供最小约化成本路径及原始列数据，用完整枚举建立小图真值。
它为后续CG闭环和总成本研究提供参考基础，标准最短路递推本身不构成新算法贡献。

下一步若连接主问题，必须保持行坐标、列成本与列域一致，并处理重复列、失败状态和
终止条件。资源约束、增量定价、状态压缩、GPU或性能优势都需要另行定义对象和证据，
当前实现与有限核验不支持这些主张。

## 8. 局限、反例与失效条件

中间标签禁止按改善容差合并。例如到v的前缀为0与-6e-10，公共后缀为-6e-10；
真实最佳rc=-1.2e-9，默认容差下改善。若把前缀差当作1e-9内平局，可错选零前缀，
只得到-6e-10而漏报改善。容差只用于最终严格rc<-tolerance，等于负阈值时False。

最终结果从原始成本/系数重建，用既有1e-9核对与DP标签的差；用户tolerance只控制
改善分类。若两种计算的改善判别不同，即使差小于1e-9也返回NUMERICAL_ISSUE。
例如基成本-1e-8、两弧-1e-9与1e-8，当前浮点标签略小于-1e-9，fsum重构恰等于-1e-9，
本版本保守失败。基成本1e16、两弧1与-1e16时，DP标签0、重构原成本1，也保守失败。

有限输入发生乘积/路径和/列汇总溢出同样返回空字段NUMERICAL_ISSUE，不能冒充NO_PATH。
本实现检查全图弧权，包括不可达分量。NO_PATH只用于确认结构不可达且运算未失败的情况。
调用者先看status，再读is_improving；失败为None，已求出的非改善最佳路径才为False。

极端尺度、下溢和近等值路径排序仍有浮点限制。“无改善”仅指本次U、pi与容差下的分类；
False可包含小幅负rc，不能直接当作数学上全部rc非负。建立精确完整LP最优性还需要
同一完整列域、有效RMP最优见证和真正的最小rc≥0，模块不作该全局裁决。

## 9. 练习与解答入口

先完成[四道练习](exercises.md)，再看[完整解答](solutions.md)。E01为手算/对偶更新，
E02为递推/平局证明，E03为阈值与数值保护，E04为RMP人工桥接及结论边界。

## 10. 开发来源与修订记录

| 来源 | 路径/身份 | 作用 |
|---|---|---|
| 本次原子合同 | [第3步](../../../tasks/codex/20261019-03-01_dag-pricing.md) | 明确普通DAG全路径域与允许范围 |
| 实际执行报告 | [定价核验](../../../tasks/reports/20261019-03-01_dag-pricing_report.md) | 独立枚举、数值反例、人工桥接与真实提交 |
| 代码基线 | 篇首verified_code | 用`git show <verified_code>:src/silo/decomposition/dag_pricing.py`回看 |

| 日期 | 讲解版本 | 修订 |
|---|---|---|
| 2026-10-19 | 0.1.0 | 创建完整列域、拓扑证明、浮点边界、枚举及人工桥接讲解，建立E01–E04 |
