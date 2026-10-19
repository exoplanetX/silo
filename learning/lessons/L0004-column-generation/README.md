---
lesson_id: L0004
title: 列生成闭环、退化与最优性差距
topic: decomposition.dag-column-generation
version: 0.1.0
status: checked
created: 2026-10-19
updated: 2026-10-19
verified_code: 857397e0cebdcfeb1c6c5ff325c17e0aa09c151b
verified_on: 2026-10-19
source_tasks:
  - 20261019-04-01_dag-column-generation
---

# L0004｜列生成闭环、退化与最优性差距

[总目录](../../CATALOG.md) · [API参考](../../../docs/dag_column_generation.md) ·
[L0002受限主问题](../L0002-restricted-master/README.md) · [L0003完整路径定价](../L0003-dag-pricing/README.md)

## 1. 问题与学习目标

RMP能求当前列，定价能找完整域中的最小约化成本路径。自动列生成还需要协调列身份、
逐轮乘数、退化、失败状态与停止依据。本篇用带凸组合等式的固定连续主问题把这些机制连起来。
读者应能解释一次增列为何可能不改变目标，推导完整域下界，并判断一次容差内停止支持多强的结论。

## 2. 前置知识、符号与假设

先掌握L0002的原始最小化行乘数和完整行冷重建，以及L0003的普通DAG全路径域。
固定有限DAG，U为其中全部s-t路径。路径成本c_p与完整系数a_p从同一个图的基项/弧项生成。
主问题是

\[
\min_{\lambda\ge0}\ c_0+\sum_{p\in U}c_p\lambda_p,
\qquad \sum_{p\in U}\lambda_p=1,
\qquad \sum_{p\in U}a_{jp}\lambda_p\ \{\le,=,\ge\}\ b_j.
\]

J包括唯一指定的凸组合行conv；该行每条路径系数1、RHS1、方向EQ，图中以基系数1和
全部弧系数0保证。其他行固定且有限，LE乘数非正、GE非负、EQ自由。路径权重连续。
当前列集S由合法非空seed开始，初始可行性靠实际RMP求解检查。

记P为当前原始目标，D为当前行乘数的对偶目标，rho为完整域最小约化成本，L为平移后的
对偶目标。P不是路径域U。c0只在主问题目标加一次，不进入路径约化成本。
没有资源约束、整数路径选择、自动seed或可行性定价；图完全决定路径可行性。

## 3. 手算例子

图只有s和t，四条平行弧各成一条路径；基成本0，基系数conv=1。
行R=C=1/2、conv=1均为等式，c0=-3，seed取d1、d2。

| 路径 | 成本 | R系数 | C系数 |
|---|---:|---:|---:|
| d1 | 4 | 1 | 1 |
| d2 | 6 | 0 | 0 |
| o12 | 1 | 1 | 0 |
| o21 | 2 | 0 | 1 |

初始d1=d2=1/2，P=2。只加入o21时，R行固定d1=1/2，C行迫使o21=0；
只加入o12时同样无目标下降。两列都出现后，令d1=t，可得d2=t、o12=o21=1/2-t，
0≤t≤1/2，目标P(t)=-1.5+7t。因此t=0唯一最优，o12=o21=1/2、P=-1.5。

本检出两种后端在原输入顺序得到以下实际轨迹，退化乘数和列顺序只是该次运行结果：

| 轮 | pi=(conv,R,C) | P | D | rho | L | gap | 本轮加入 |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | (6,-2,0) | 2 | 2 | -4 | -2 | 4 | o21 |
| 2 | (6,2,-4) | 2 | 2 | -7 | -5 | 7 | o12 |
| 3 | (-1,2,3) | -1.5 | -1.5 | 0 | -1.5 | 0 | 无 |

第二轮目标不变，最小rc仍显著为负，必须继续。当前L也会从-2下降到-5；
每轮有效下界可以变松，不能要求它逐轮单调。

## 4. 原理推导与正确性依据

### 4.1 为什么重复求解并保留完整行

固定S的最优解给未出现路径赋零，便成为完整主问题可行解。扩展列集保留这个解，
故精确算术下P非增，但可以相等。负rc说明当前对偶对某条完整域列失去可行性，
退化可能使新变量在下一次最优解中仍为零；目标不动不能替代定价停止检查。
每次加列后用全部原始行冷重建RMP，避免把旧列集的冗余关系永久带入新问题。

### 4.2 凸组合乘数平移下界

本轮从原始坐标计算

\[
P=c_0+\sum_{p\in S}c_p\lambda_p,\quad
D=c_0+\sum_{j\in J}b_j\pi_j,\quad
\rho=\min_{p\in U}(c_p-a_p^\top\pi).
\]

假设原始解可行、pi符号正确、rho确实来自完整U，且所有路径conv系数和RHS都为1。
令delta=min(0,rho)，只修改pi'_conv=pi_conv+delta。等式乘数自由，其他行乘数不变，
所以行符号仍合法；每条完整域列的新约化成本满足

\[
\bar c'_p=\bar c_p-\delta\ge0.
\]

因此pi'对完整主问题对偶可行，其目标L=D+delta。弱对偶与当前原始可行解共同给出

\[
L=D+\min(0,\rho)\le z^\star\le P,
\qquad P-L=(P-D)-\min(0,\rho).
\]

这里使用真实D。浮点RMP允许微小原对偶误差，直接用P代替D会漏掉差距项P-D。
缺少conv结构时，这个平移构造没有统一作用于所有列的依据；总权重为M时，相应目标修正
也应为M*delta。本控制器精确校验固定系数1、RHS1，不扩展到一般总质量模型。

### 4.3 有限轮次与数值停止

一轮用新求出的pi完整定价，只接受一条显著负rc且未出现的路径。显著负rc的既有路径
意味着当前证据冲突，诊断数值问题；不能跳过它、启发式换列或把重复当收敛。
精确算术、可行seed、正确RMP/定价和足够预算下，有限路径与不重复增列支持有限终止。
本实现有预算和浮点限制，发布更窄的数值状态。

实现只有rho≥-tolerance且0≤P-L≤tolerance时返回TOLERANCE_REACHED。
rho容差内而gap过大时诊断；L>P也诊断，不裁剪。小负rho仍可能有微小改善，
浮点界估计也没有严格舍入保证。精确最优结论需要上述精确条件及真正闭合的差距。

## 5. 算法到代码的映射

| 数学或流程对象 | [dag_column_generation.py](../../../src/silo/decomposition/dag_column_generation.py)中的职责 |
|---|---|
| 固定行、conv约定与seed | DagMasterRow、DagColumnGenerationProblem，冻结并复制输入 |
| 路径身份 | 完整弧ID元组；path_0等内部变量名与路径的只读注册表 |
| 初始列和候选真实数据 | `_path_ids`、`_reconstruct`从公开图结构重新汇总 |
| 冷求解/新pi/单列增广 | `solve_dag_column_generation`，沿用RMP与完整DAG定价 |
| 原始目标、行符号、D | `_master_objectives`用当前列及快照核对，既有绝对容差1e-9 |
| 候选字段与改善分类 | `_check_candidate`；容差内漂移字段不能写回RMP |
| 下界与停止 | L=D+min(0,rho)、真实gap检查，专用CG停止枚举 |
| 历史证据 | 独立逐轮快照、有效RMP及列集轮号，失败轮界为None |

最后预算轮若仍需新列，直接ITERATION_LIMIT，不加入没有下一轮预算求解的列。
同轮已满足停止时优先成功。若后续RMP失败，顶层注册表仍对应带轮号的最后有效RMP；
失败尝试的注册表单独在失败轮记录，当前界为None。首次失败没有有效历史RMP。
seed重构先溢出时没有已求解轮次和注册表。

成本来自多次冷RMP、每轮拓扑DP、候选重构及快照核对。路径数可能指数增长，
不把有限终止解释为多项式轮数，也不据此声称总体线性复杂度或性能优势。

## 6. 核验与复现

从项目根目录用已有环境执行下例，自动跨过退化轮次，并核对两个原生后端：

```python
from silo.core.enums import ConstraintSense as S
from silo.decomposition import (
    DagArc, DagPricingProblem, DagMasterRow, DagColumnGenerationProblem,
    DagColumnGenerationStatus, solve_dag_column_generation,
)
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

graph = DagPricingProblem(
    ['s', 't'],
    [DagArc('d1', 's', 't', 4, {'R': 1, 'C': 1}), DagArc('d2', 's', 't', 6),
     DagArc('o12', 's', 't', 1, {'R': 1}), DagArc('o21', 's', 't', 2, {'C': 1})],
    's', 't', ['conv', 'R', 'C'], base_coefficients={'conv': 1},
)
problem = DagColumnGenerationProblem(
    graph, [DagMasterRow('conv', S.EQ, 1), DagMasterRow('R', S.EQ, .5),
            DagMasterRow('C', S.EQ, .5)], 'conv', [('d1',), ('d2',)], -3,
)
for backend in (RevisedSimplexSolver(), TableauSimplexSolver()):
    result = solve_dag_column_generation(problem, solver=backend, iteration_limit=3)
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED
    assert [r.numerical_upper_bound for r in result.iterations] == [2, 2, -1.5]
    assert result.column_set_iteration == result.last_valid_master_iteration == 3
    weights = {path: result.last_valid_master.primal_values[name]
               for name, path in result.column_paths.items()}
    assert weights == {('d1',): 0, ('d2',): 0, ('o12',): .5, ('o21',): .5}
    assert result.iterations[-1].numerical_gap == 0
    print(type(backend).__name__, weights)
```

[单元测试](../../../tests/unit/test_dag_column_generation.py)核对limit、阈值、身份、快照、
失败、重构、真实gap和溢出。[完整列对照](../../../tests/verification/test_dag_column_generation_oracles.py)
独立DFS全部路径，以Fraction从原始图生成列，再直接构造完整列LP；没有复用控制器私有助手。
主例外还有8个不同模型，均为真实两弧路径，覆盖混合行、负RHS/成本、基项和不同可行seed。

九个模型各做两个后端×两组排列，另对GE模型做替代seed的四组，共40组CG/完整列LP比较。
完整LP和CG共享原生LP依赖，因此同时给出独立解析目标及主例P(t)，防止后端一致性被当作
独立数学证明。有限模型族支持参考实现的核验，不替代第4节一般推导。
本例与四题的实际核验记录见[执行报告](../../../tasks/reports/20261019-04-01_dag-column-generation_report.md)。

## 7. 研究意义与可扩展问题

当前成果是固定普通DAG凸组合主问题的可审查CG参考基础。逐轮原始行、列身份、完整定价、
退化与真实差距记录可用于后续增量方法的对照基线，先保护数学对象与失败语义，再研究效率。
普通DAG CG的正确实现本身不构成论文创新；后续特色机制须有明确新结构和独立对照证据。
资源定价、VRP、分支、整数路径选择及工业规模都需要后续单独建模和验证。

## 8. 局限、反例与失效条件

只有conv=1，路径成本1和1-5e-10，seed只含成本1。默认容差下rho约-5e-10、P=1，
L约1-5e-10，正gap约5e-10，正常TOLERANCE_REACHED。解析最优仍严格小于1；
这个状态保留容差允许的微小改善，不能改写为严格零差距。

即使rho在阈值内，P-D也可能让gap超限。例如P-D=8e-10、rho=-7e-10，gap=1.5e-9，
默认容差下必须诊断。若舍入导致L>P，保守失败；数值界没有区间算术或有向舍入保证。
原生LP既有近相关等式状态问题也继续保留，后端UNBOUNDED只是当前诊断。

seed不可行只说明当前受限列集失败：GE例r≥1/2，路径r=(0,1,2)，seed仅r=0时不可行，
完整域却可行。需要可行性定价才能自动恢复，本篇停止并保留诊断。
合法seed下定价NO_PATH是依赖契约矛盾，不能据此成功终止。

坏候选字段、非有限累计、重复显著改善路径及原始字段/改善分类冲突都保守失败；
故障注入只检验这些保护，不能声称正常后端自然出现了所有注入情形。
调用者先读CG状态与轮号，历史有效RMP只解释为其自身列集，失败轮新界为None。

## 9. 练习与解答入口

[四道练习](exercises.md)依次覆盖耦合退化、凸组合对偶平移、真实差距/小负rc、
seed失败与研究边界；完成后阅读[完整解答](solutions.md)。题号L0004-E01至E04保持稳定。

## 10. 开发来源与修订记录

| 来源 | 路径/身份 | 作用 |
|---|---|---|
| 原子合同 | [第4步](../../../tasks/codex/20261019-04-01_dag-column-generation.md) | 固定主问题、停止及允许范围 |
| 实际执行 | [CG报告](../../../tasks/reports/20261019-04-01_dag-column-generation_report.md) | 真值、故障、环境、检查及真实提交 |
| 代码基线 | 篇首verified_code | 用git show回看包含本控制器的真实实现版本 |

| 日期 | 讲解版本 | 修订 |
|---|---|---|
| 2026-10-19 | 0.1.0 | 建立自动循环、退化、平移下界、数值停止、失败与E01–E04 |
