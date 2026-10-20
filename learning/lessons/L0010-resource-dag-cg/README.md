---
lesson_id: L0010
title: 资源可行列域与凸组合列生成
topic: decomposition.resource-dag-column-generation
version: 0.1.0
status: checked
created: 2026-10-20
updated: 2026-10-20
verified_code: 6858a736568a6d502271acf39d29f855def65b93
verified_on: 2026-10-20
source_tasks: [20261020-05-01_resource-dag-cg]
---

# L0010｜资源可行列域与凸组合列生成

## 1. 问题与学习目标

资源定价产生一条列，列生成还需反复求解当前主问题、使用当前对偶完整定价、
核对候选并决定增列或停止。本篇连接[L0009](../L0009-resource-dag-pricing/README.md)
的资源冷基线与[L0004](../L0004-column-generation/README.md)的凸组合主问题。
任务归属原七步的原4：在声明资源子类与参考主问题内形成闭环。
真实应用门控、跨对偶机制和完整成本评价保持各自义务。

## 2. 前置知识、符号与假设

固定有限DAG，每弧有成本c_e、主问题行特征a_e、非负整数资源d_e。
资源从0累加且逐维不超B，全部资源可行完整路径构成P_B。
路径列c_p=c_base+Σc_e、a_p=a_base+Σa_e，主问题为

\[
\min c_0+\sum_{p\in P_B}c_p\lambda_p,\qquad
\sum_{p\in P_B}a_{jp}\lambda_p\ [\le,=,\ge]\ b_j,\quad
\lambda_p\ge0,\quad\sum_p\lambda_p=1.
\]

最后一行是指定conv等式，其每列系数及RHS严格为1。c_base属于每条列，
c0是只加一次的主问题常数。资源是路径内部可行性；R等耦合行限制列的组合，
两者分别建模。MIN对偶中LE乘数非正、GE非负、EQ自由。
seed非空、完整、资源可行，并已使当前RMP可行；本入口不恢复不可行seed。
两个输入记录必须引用同一图对象，以保持列数据和资源的共同来源。

## 3. 手算例子

s→u四条前缀如下，公共z:u→t成本/行特征为0、资源消耗1；容量2。
所有列conv=1，耦合行为R=1/2，c0=0。

| 前缀 | 成本 | R特征 | 前缀资源 | 完整路径资源 |
|---|---:|---:|---:|---:|
| a | 4 | 0 | 0 | 1 |
| b | 1 | 1 | 1 | 2 |
| c | 6 | 2 | 0 | 1 |
| d | -10 | 1/2 | 2 | 3，不可行 |

seed为a,z和c,z。R行给2lambda_c=1/2，故lambda_c=1/4、lambda_a=3/4，
P=4×3/4+6×1/4=9/2。当前对偶pi_conv=4、pi_R=1，
b的rc=1−4−1=−4；d虽更便宜，却超容量，不属于P_B。
加入b后lambda_a=lambda_b=1/2、lambda_c=0，P=5/2；
对偶pi_conv=4、pi_R=−3，使a/b的rc=0、c的rc=8，rho=0。

| 轮 | P | D | rho | L | 消去c0后的g | 接受列 |
|---|---:|---:|---:|---:|---:|---|
| 1 | 9/2 | 9/2 | -4 | 1/2 | 4 | b,z |
| 2 | 5/2 | 5/2 | 0 | 5/2 | 0 | 无 |

Revised冷、Tableau冷与Revised复用三模式实际都得到该两轮轨迹。
一般退化模型的对偶和轨迹可以不同，应按各自registry和对偶核对。

## 4. 原理推导与正确性依据

当前registry中的每列均在P_B内；把其他lambda设0，当前RMP原始可行解仍为全列
主问题可行解。因此其目标P给数学上界。设当前原始行对偶为pi，
rho=min_{p∈P_B}(c_p−a_pᵀpi)，delta=min(0,rho)。
只令pi'_conv=pi_conv+delta，其余不变，则所有资源列的新rc为旧rc−delta>=0。
conv乘数自由，其他行的符号仍正确；其RHS为1，故对偶目标变为D+delta。
在精确运算及完整定价等前提下，L=D+delta<=z*<=P。
详见[L0004的推导](../L0004-column-generation/README.md)；把列域替换为P_B仍需完整资源定价。
缺少统一conv结构的真实覆盖模型，不能套用这个修正公式。

实现使用浮点参考规则：P/D/L按原始项fsum，raw gap=fsum(P,−L)；
objective_gap在原始贡献中消去公共c0，保留符号。
令eta=32×ulp(局部绝对贡献之和)。g<0仅在eta<=tolerance且−g<=eta时接受；
rho>=−tolerance时还须g<=tolerance。该工程保护不提供严格LP线性代数误差界。
大c0可能使raw gap舍入为0，原始贡献层的g仍能显示4的缺口。

资源预算中断只覆盖部分搜索域，无法确认rho，故CG返回PRICING_FAILURE并清空本轮界。
每轮RMP基复用仅改变取得当前最优RMP证据的过程；资源定价仍是fresh冷DP。
先前未选前缀跨对偶恢复问题见L0009，B没有实现该机制。

## 5. 算法到代码的映射

| 对象/门槛 | 实现位置 |
|---|---|
| 新入口及资源结果记录 | [resource_dag_column_generation.py](../../../src/silo/decomposition/resource_dag_column_generation.py) |
| 全部seed逐弧核资源、候选资源二次核验 | 同文件_resource_usage、_check_resource_candidate |
| 列/主目标/差距数学助手 | 只读消费[原CG辅助函数](../../../src/silo/decomposition/dag_column_generation.py)，旧文件字节不变 |
| 当前对偶的完整资源域 | [price_resource_dag](../../../src/silo/decomposition/resource_dag_pricing.py)，每轮重新给预算 |
| 默认cold/显式opt-in | [RMP公开入口](../../../src/silo/decomposition/restricted_master.py)，owner每次CG调用新建 |
| 独立每轮/全列真值 | [原始数据DFS及Fraction顶点](../../../tests/verification/test_resource_dag_column_generation_oracles.py) |

先验证全部seed资源，再重构数值列和创建RMP。候选的c/a/rc按原始图核对，
资源按整数精确重算，返回usage须为严格整数tuple；容差内漂移字段也不直接写入RMP。
错误记录不进入类型化history。原始列、资源失败和一般数值失败均不增列。
每次公开RMP重优化的真实outcome保留到该轮，master_result is outcome.result。

## 6. 核验与复现

在仓库根目录使用`.venv/Scripts/python.exe`执行以下完整公开API程序。

```python
from silo.core.enums import ConstraintSense as S
from silo.decomposition import (
    DagArc, DagColumnGenerationProblem, DagColumnGenerationStatus,
    DagMasterRow, DagPricingProblem, ResourceDagPricingProblem,
    solve_resource_dag_column_generation,
)
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

graph = DagPricingProblem(("s", "u", "t"), (
    DagArc("a", "s", "u", 4), DagArc("b", "s", "u", 1, {"R": 1}),
    DagArc("c", "s", "u", 6, {"R": 2}), DagArc("d", "s", "u", -10, {"R": 0.5}),
    DagArc("z", "u", "t", 0)), "s", "t", ("conv", "R"), base_coefficients={"conv": 1})
problem = DagColumnGenerationProblem(graph, (DagMasterRow("conv", S.EQ, 1),
    DagMasterRow("R", S.EQ, 0.5)), "conv", (("a", "z"), ("c", "z")))
resources = ResourceDagPricingProblem(graph, (2,), {
    "a": (0,), "b": (1,), "c": (0,), "d": (2,), "z": (1,)})
for backend, reuse in ((RevisedSimplexSolver(), False), (TableauSimplexSolver(), False),
                       (RevisedSimplexSolver(), True)):
    result = solve_resource_dag_column_generation(problem, resources, solver=backend,
                                                  reoptimize_rmp=reuse)
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED
    assert [r.master_result.objective_value for r in result.iterations] == [4.5, 2.5]
    assert [r.rho for r in result.iterations] == [-4, 0]
    assert result.iterations[0].accepted_path == ("b", "z")
    assert ("d", "z") not in result.column_paths.values()
print("L0010: three modes and resource domain verified")
```

实际检查：66项[unit](../../../tests/unit/test_resource_dag_column_generation.py)，
72固定模型×3模式=216次完整CG，每个调用一个pytest项，共282项新增测试。
独立DFS从公开原始数据构建资源可行列；Fraction枚举全部两列bracketing顶点，
分别核对每轮当前registry和完整资源列域的LP真值。另核对原始MIN的原/对偶目标、
x_j×rc_j、最小资源价格、资源用量、所有数值界和registry变化；不依赖生产求解作为唯一真值。

三模式各72调用、116轮；两个cold模式各116次公开solve。
opt-in模式116次公开重优化，内部cold72、warm44、fallback0。
unit另观察真实Phase II、公开入口次数、fresh owner及warm失败后的RMP内部单次回退。
这属于接线和有限正确性证据，不由计时推断复用或加速。
全量5581项于2026-10-20通过(17.29s)，Ruff/结构通过；正文程序及解答另实际核对。

## 7. 研究意义与可扩展问题

B使原3资源冷基线与原4参考主问题形成可重复、可审查的逐轮过程。
原始MIN坐标、资源域和当前列集合共同固定，便于后续判断某轮维护的对象与成本。
基复用诊断可帮助区分RMP成本与定价成本，但本任务没有性能实验。
这些是成熟机制的参考实现，当前没有原创性主张。

原5需要真实应用主问题、完整定价状态、真实对偶与同域强基线联合证据；
本例的两轮对偶仅属于教学参考。原6的增量状态和原7的完整计费仍未完成，
是否继续由既定C门槛裁决，不能凭B通过将这些义务标成完成。

## 8. 局限、反例与失效条件

本模型有全局conv等式、连续变量及非负整数可加资源DAG。
真实多路径覆盖/分割、访问记忆、时间窗、一般有环、自动seed及资源恢复不在支持域。
资源整数判断精确；目标继承A和普通CG的浮点局限，候选通过不能证明一般符号最优。
预算按每轮重新给予，未提供总时间或内存上界。

失败历史要保留所属关系：首轮seed重构失败时无已解history；首轮master失败时保留
尝试registry但无last_valid_master；后续master或主目标核验失败，顶层保留前一有效已解轮。
若主目标已通过后才遇到pricing/candidate/gap失败，则当前RMP可作为last_valid_master，
但本轮界全部为空。失败尝试的新registry仍在本轮history，不能将其重新配给旧master。
最后允许轮发现负列也不追加未求解列；显著负的已有列说明证据冲突，返回数值失败。

## 9. 练习与解答入口

[八道练习](exercises.md)及[解答](solutions.md)：L0010-E01至E08，
覆盖两轮手算、凸性下界、资源cap、双资源、公共常数、基复用证据、失败历史与研究边界。

## 10. 开发来源与修订记录

| 类型 | 真实路径/版本 | 用途 |
|---|---|---|
| 原子合同 | [20261020-05-01](../../../tasks/codex/20261020-05-01_resource-dag-cg.md) | 原4资源参考CG |
| 执行报告 | [B交付](../../../tasks/reports/20261020-05-01_resource-dag-cg_report.md) | 范围、检查和Git记录 |
| 核验代码 | 6858a736568a6d502271acf39d29f855def65b93 | 新入口/记录、unit、独立真值及原生例 |
| API | [资源CG文档](../../../docs/resource_dag_column_generation.md) | 当前调用与失败语义 |

2026-10-20 v0.1.0：按实际实现提交核对正文程序、三模式手例与八题。
源码、讲解、合同与协调验收分别定位，本篇checked不等于研究晋级。
