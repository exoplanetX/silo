---
lesson_id: L0005
title: 列生成的可行性恢复与辅助主问题
topic: decomposition.dag-feasibility
version: 0.1.0
status: checked
created: 2026-10-19
updated: 2026-10-19
verified_code: 02aed7d5d180fbe1cbef67abec1b084777c6a369
verified_on: 2026-10-19
source_tasks:
  - 20261019-06-01_dag-feasibility
---

# L0005｜列生成的可行性恢复与辅助主问题

[目录](../../CATALOG.md) · [API](../../../docs/dag_feasibility.md) ·
[L0001](../L0001-lp-duality/README.md) · [L0002](../L0002-restricted-master/README.md) ·
[L0003](../L0003-dag-pricing/README.md) · [L0004](../L0004-column-generation/README.md)

## 1. 问题与学习目标

完整主问题可能可行，当前seed却缺少支撑耦合行的路径。旧CG在受限不可行时停止，
需要一个独立过程先恢复可行列集。本篇用单位总违背量辅助主问题和全域可行性定价完成初始化，
再以无人工变量的原始见证交还调用者。
读者应能构造三类行的人工列，证明完整辅助目标与原可行性等价，区分恢复目标与原目标，
并判断小F、正下界及浮点诊断分别支持什么结论。

## 2. 前置知识、符号与假设

前置为L0001的原始行乘数、L0002的MIN RMP、L0003的完整DAG定价和L0004的差距门控。
固定普通有限DAG全部s-t路径U，连续lambda>=0，conv等式sum(lambda)=1；
其余耦合行j属于K，固定方向LE/GE/EQ与RHS。至少一条合法seed满足路径结构规则，
但允许不满足耦合行。原成本c_p和常数c0只在后续原目标优化使用。

恢复阶段所有真实路径成本0、辅助常数0，人工变量单位成本1，辅助目标记F。
定价rho使用辅助零成本和本轮原始行乘数pi；当前列集S只随显式接受的真实路径增加。
单位罚权固定，不按行单位归一化；资源约束、整数路径选择及自动寻找第一条路径没有扩展。

## 3. 手算例子

### 3.1 恢复后再优化原目标

conv=1、r>=1/2，路径p0/p1/p2的r为0/1/2，原成本0/4/10、c0=7，seed仅p0。
图可取base_cost=1、三弧成本-1/3/9，conv基系数1。
辅助行r(lambda)+u>=1/2，目标F=u；初始lambda0=1、u=1/2，F=1/2。
辅助乘数pi_conv=0、pi_r=1，零成本rc依次0/-1/-2，因此补p2。
误用原成本会得到rc=0/3/8，漏掉需要的列。

补p2后F=0，可取lambda2=1/4、lambda0=3/4。移除u后用零目标再求完整原始行，
得到原始可行见证，交回seed(p0,p2)，原成本与c0保留。
旧CG以原目标求解先得7+10/4=9.5，再补p1到9；
解析最优lambda0=lambda1=1/2，lambda2=0，因为p1每单位r的原成本最低。

### 3.2 完整域仍有正违背量

把r下界改为3。任意真实路径凸组合的r最多2，故完整最小违背量F*=1。
seed受限F=3，定价补p2后F=1，末轮pi_conv=-2、pi_r=1，rho=0、D=L=1。
初始受限F=3不能单独给完整域结论；末轮的定价和人工约束一起支持正下界。
当前状态称POSITIVE_VIOLATION_BOUND，保留浮点证据的范围。

### 3.3 恢复也会退化

conv=1、R=1、C=0，seed坐标(0,0)，另有above=(1,1)、below=(1,-1)。
仅含seed与above时，令above权重t，0<=t<=1，总违背量|1-t|+|t|=1；below同理。
两列都出现后各1/2达到F=0。所以正确循环跨过1->1->0，目标不变仍须继续。
本检出两个后端实际先加above再加below，等价退化轨迹无需固定为同一顺序。

## 4. 原理推导与正确性依据

### 4.1 人工违背量和可行等价

LE行减非负v，GE行加非负u，EQ行加u减v，conv不加人工。固定lambda时，
最小人工量分别为max(0,A_j lambda-b_j)、max(0,b_j-A_j lambda)、|A_j lambda-b_j|。
任一合法seed取权重1满足conv，有限的行残差可由人工量补足，辅助RMP有有限可行点。
精确非负人工量保证F>=0。完整路径有限，lambda的单纯形紧，残差违背函数连续，
故最小违背量可达。F*=0时全部单位成本人工量为0，对应原可行解；原可行解配零人工量
又给F=0。这建立完整辅助LP与原可行性的双向联系。

固定列LP内部的Phase I处理当前列集；本篇外层辅助定价继续从整个U发现缺失真实列。
初始合法路径依然必要，人工列conv系数0无法替代这条路径。

### 4.2 人工列的对偶区间

原始MIN乘数符号为LE非正、GE非负、EQ自由。人工列成本1，LE列系数-1给1+pi_j>=0，
GE列系数+1给1-pi_j>=0，EQ两列共同给这两个约束。因此区间为：

| 行 | 人工系数 | pi区间 |
|---|---|---|
| LE | -1 | [-1,0] |
| GE | +1 | [0,1] |
| EQ | +1与-1 | [-1,1] |

恢复器从自有人工列系数和单位成本独立复算rc，按既有1e-9检查；不能只看返回rc字段。
例如r>=3、seed r=1，lambda1=1、u=2、F=2，注入pi_conv=-4、pi_r=2，
真实路径rc=(4,2,0)、rho=0、D=L=2、g=0，看似完整；但人工rc=1-2=-1，
违反盒约束，形式下界2甚至超过真实F*=1，必须诊断。

### 4.3 两类列的平移证明

零成本全域定价给rho=min_U(-a_p^T*pi)，D=sum_j b_j*pi_j，包含conv。
令delta=min(0,rho)，只改pi'_conv=pi_conv+delta：

\[
\bar c'_{p}=\bar c_p-\delta\ge0\quad(\text{真实路径，conv系数1}),
\qquad
\bar c'_{a}=\bar c_a\ge0\quad(\text{人工列，conv系数0}).
\]

当原始符号、人工约束和完整路径定价均满足精确条件，pi'是完整辅助对偶可行点。
conv的RHS1使目标变为L=D+delta，弱对偶给L<=F*<=F。
证明分别使用两类列的conv系数；人工约束缺失会破坏结论。
精确正L分离原不可行，当前实现的正界状态只发布浮点估计，不输出严格Farkas见证。

### 4.4 小F、原始复核与数值差距

F在[-1e-9,tolerance]内时，另建只有当前真实路径、完整原始行、零目标/常数的RMP。
该次OPTIMAL经原核验器和独立原行/权重检查后才返回成功。保留实际权重，不剪小值或归一化。
F<-1e-9诊断；复核失败也诊断，不能把小罚值当成原始可行见证。

F>tolerance时用L0004的原项有符号g和eta=32*ulp(绝对贡献和)核对。
人工成本1、真实成本0，原c0不参与；负g例外同时受eta和用户容差限制，正gap/rho阈值不加eta。
rho容差内还须g<=tolerance且L>tolerance才发布正违背下界。
32是工程局部尺度，原始行见证仍按既有1e-9核验；更小用户容差不改变全局行精度。

## 5. 算法到代码的映射

| 对象/义务 | [dag_feasibility.py](../../../src/silo/decomposition/dag_feasibility.py)中的职责 |
|---|---|
| 原输入与零成本视图 | 复用公开DagColumnGenerationProblem，replace创建独立冻结零成本图 |
| 两类列身份 | path_i映射弧元组，art_i映射(row,sign)，人工从起点固定存在 |
| 完整辅助RMP | `_build_master`保持全部行与单位人工成本，每轮冷求解 |
| 原始/人工证据 | `_check_snapshot`核对权重、行、F、坐标、rc及人工盒约束 |
| 候选重构 | `_path_data`、`_check_candidate`只从公开图汇总，入列成本强制0 |
| 小F后的见证 | 独立无人工零目标RMP，original_validation快照与辅助快照分别保存 |
| 阶段交接 | feasible_problem仅替换全部生成真实seed，旧CG由调用者显式调用 |
| 预算/失败 | 独立状态、轮号、失败阶段、辅助/复核调用数及不可变历史记录 |

辅助预算只计辅助RMP轮次；原始复核额外最多一次。最后允许轮F小可正常复核成功，
仍需新路径时ITERATION_LIMIT且不追加未求解列。目标不变继续，每轮最多接受一条真实路径。
F小不定价，全域D/rho/L/g字段为None；失败轮同样不发布新界，历史有效辅助RMP有其轮号。
每轮成本包括冷LP、完整拓扑定价、原始重构和核验，本篇没有性能优势主张。

## 6. 核验与复现

从项目根目录运行下列完整程序，双后端显式恢复后再进入原目标CG：

```python
from silo.core.enums import ConstraintSense as S
from silo.decomposition import (
    DagArc, DagPricingProblem, DagMasterRow, DagColumnGenerationProblem,
    DagFeasibilityStatus, restore_dag_feasibility, solve_dag_column_generation,
)
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

def make_problem(rhs):
    graph = DagPricingProblem(
        ['s', 't'], [DagArc(f'p{i}', 's', 't', c, {'r': i})
                     for i, c in enumerate((-1, 3, 9))],
        's', 't', ['conv', 'r'], 1, {'conv': 1},
    )
    return DagColumnGenerationProblem(
        graph, [DagMasterRow('conv', S.EQ, 1), DagMasterRow('r', S.GE, rhs)],
        'conv', [('p0',)], 7,
    )

for backend in (RevisedSimplexSolver, TableauSimplexSolver):
    problem = make_problem(.5)
    recovered = restore_dag_feasibility(problem, solver=backend())
    assert recovered.status == DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    assert [r.penalty_objective for r in recovered.iterations] == [.5, 0]
    assert recovered.auxiliary_solve_count == 2 and recovered.validation_solve_count == 1
    assert recovered.feasible_problem.graph is problem.graph
    optimized = solve_dag_column_generation(recovered.feasible_problem, solver=backend())
    assert [r.numerical_upper_bound for r in optimized.iterations] == [9.5, 9]
    positive = restore_dag_feasibility(make_problem(3), solver=backend())
    assert positive.status == DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND
    assert positive.iterations[-1].numerical_lower_bound == 1
    assert positive.feasible_problem is positive.feasibility_witness is None

    graph = DagPricingProblem(
        ['s', 't'], [DagArc('seed', 's', 't', 0),
                     DagArc('above', 's', 't', 4, {'R': 1, 'C': 1}),
                     DagArc('below', 's', 't', 2, {'R': 1, 'C': -1})],
        's', 't', ['conv', 'R', 'C'], base_coefficients={'conv': 1},
    )
    problem = DagColumnGenerationProblem(
        graph, [DagMasterRow('conv', S.EQ, 1), DagMasterRow('R', S.EQ, 1),
                DagMasterRow('C', S.EQ, 0)], 'conv', [('seed',)],
    )
    degenerate = restore_dag_feasibility(problem, solver=backend(), iteration_limit=3)
    assert degenerate.status == DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    assert [r.penalty_objective for r in degenerate.iterations] == [1, 1, 0]
    assert degenerate.auxiliary_solve_count == 3 and degenerate.validation_solve_count == 1
    print(backend.__name__, 'original optimum 9; violation 1; degenerate 1->1->0')
```

[单元测试](../../../tests/unit/test_dag_feasibility.py)覆盖三例、原始复核、失败、预算、人工约束、
局部gap、溢出和所有权。[648组解析族](../../../tests/verification/test_dag_feasibility_oracles.py)
以独立DFS重构全列LP，并用单位正方形上的Fraction违背函数核对。
每行LE/GE/EQ与RHS(-1/4,1/2,5/4)构成9设置，两行81模型，两个seed、两种排列、
两个后端共648次，结果200成功/448正违背下界，200成功均显式原目标CG交接并对照完整LP。
去掉R/C与RHS的相同基项平移后，四路径凸包为[0,1]^2：任意(x,y)可取权重
((1-x)(1-y),(1-x)y,x(1-y),xy)。两行的最小违背量因此可分别计算并相加：

\[
h_{\rm LE}(b)=\max(0,-b),\quad h_{\rm GE}(b)=\max(0,b-1),\quad
h_{\rm EQ}(b)=\max(0,-b,b-1).
\]

每行9设置中5个可行，故25个模型可行、56个有正违背量，乘每模型8组合得到200/448。
完整LP与恢复器共享底层原生求解器；Fraction辅助解析与手算原目标9提供另一类依据，
有限族通过不替代第4节一般证明。实际执行和数值例外见[报告](../../../tasks/reports/20261019-06-01_dag-feasibility_report.md)。

## 7. 研究意义与可扩展问题

可行初始化补齐后，后续重优化/增量定价才能在相同原模型和可行列集上比较，
阶段目标、人工列与原始见证分开可避免把求解对象变化误当算法收益。
本成果是成熟基础机制的可审查参考实现，尚不构成论文创新或工业规模能力。
一般可行性框架、资源定价、整数列选择、warm start与效率研究需另行定义对象和证据。

## 8. 局限、反例与失效条件

单位总违背量随行单位改变，当前不归一化或设可调罚权。合法非空seed仍是前提。
只有r=0路径却要求r>=5e-4、用户tolerance=1e-3时F虽小，原始复核仍不可行，
返回NUMERICAL_ISSUE且不交可行问题。受限正F、无改善标志也须经过完整定价/下界门控。

648族中有10个辅助末轮的返回pi使精确人工rc=-2^-52，仍通过既有1e-9浮点检查。
其中8个定价轮的形式平移目标超过解析F*达2^-54；这些乘数不满足精确对偶可行假设，
测试单列记录，未投影、裁剪或借工程eta把它们写成严格数学下界。
精确条件成立的轮次按Fraction严格核对平移下界，其余只解释为浮点数值证据。
POSITIVE_VIOLATION_BOUND不等于严格Farkas认证；现有LP/定价器的数值边界仍保留。

人工pi_r=2反例的rc=-1则远超既有核验范围，必须拒绝。F小后复核与盒约束检查各有
独立作用：前者保护原可行见证，后者保护完整辅助下界。两者不能互相代替。
失败轮界为None，原始见证只在成功时存在，读取时按状态/失败阶段与轮号核对。

## 9. 练习与解答入口

[五道练习](exercises.md)覆盖人工符号/区间、两类列平移、两阶段成本、退化/调用预算及
浮点证据边界。完成后看[完整解答](solutions.md)，题号L0005-E01至E05保持稳定。

## 10. 开发来源与修订记录

| 来源 | 路径/身份 | 作用 |
|---|---|---|
| 原子合同 | [第6步](../../../tasks/codex/20261019-06-01_dag-feasibility.md) | 辅助模型、人工对偶与原始复核义务 |
| 实际执行 | [恢复报告](../../../tasks/reports/20261019-06-01_dag-feasibility_report.md) | 648族、两类LP调用、数值边界与真实提交 |
| 代码基线 | 篇首verified_code | 真实包含独立恢复器的实现提交 |

| 日期 | 讲解版本 | 修订 |
|---|---|---|
| 2026-10-19 | 0.1.0 | 建立单位违背量、零成本定价、两类列下界、原始见证、预算与E01–E05 |
