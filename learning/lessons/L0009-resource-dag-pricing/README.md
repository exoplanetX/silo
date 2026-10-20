---
lesson_id: L0009
title: 整数资源定价、充分状态与有界冷搜索
topic: decomposition.resource-dag-pricing
version: 0.1.0
status: checked
created: 2026-10-20
updated: 2026-10-20
verified_code: be03540db4f966a6c98f71e41d9025b08ddd7555
verified_on: 2026-10-20
source_tasks: [20261020-04-01_resource-dag-pricing]
---

# L0009｜整数资源定价、充分状态与有界冷搜索

## 1. 问题与学习目标

普通DAG最便宜的路径可能累计消耗过大。资源定价要在完整资源可行路径域中
寻找当前最小约化成本列。本篇学习三个对象：后续可行性需要的完整状态、当前对偶下
一个状态的最优前缀，以及有界搜索结束时能发布的结论。
本次补齐原七步计划中原3的非负整数可加资源子类；资源CG、应用门控及跨对偶维护仍待完成。

## 2. 前置知识、符号与假设

前置：[L0002](../L0002-restricted-master/README.md)的MIN列接口及
[L0003](../L0003-dag-pricing/README.md)的DAG拓扑DP。
固定有限无环图G=(V,E)，源s与汇t不同，每弧e有原始成本c_e、主问题行向量a_e、
非负整数资源d_e∈Z⁺^q（这里Z⁺含0）；容量B∈Z⁺^q，初始资源为0。
基项c₀、a₀只计一次。列成本c_p=c₀+Σc_e，行向量a_p=a₀+Σa_e，
在给定MIN原始行对偶π下，rc_p=c_p−πᵀa_p。资源与行特征独立，行特征可以为负。
支持域的全部合法性均由位置和累计资源决定，无额外访问、时间窗或先后约束。

## 3. 手算例子

三节点s,u,t，平行弧a:s→u成本0/资源2，b:s→u成本1/资源0，
c:u→t成本0/资源1，容量2，无行、基项为0。a,c总消耗3不可行；b,c成本1、消耗1可行。
单看每弧都不超2，删超容量单弧无法排除a,c。若u只留一个最低成本前缀a，
还会误删唯一可行解b,c。正确状态保留(u,2)与(u,0)。

固定顺序为：源检查a发现(u,2)，检查b发现(u,0)；u按资源序先展开0，
经c发现(t,1)；再从(u,2)检查c并因资源3拒绝。共4个状态、4次转移。
预算4/4完整成功。状态预算3在第3次转移触发，计数3/3；转移预算3在下一检查前
触发，计数4/3，此时已经有汇候选，仍只可报告搜索中断。

增加第二资源，取容量(2,2)，a=(2,0)、b=(0,2)、c=(1,0)，
仍返回b,c，资源(1,2)。第二维消耗2与成本1是不同量，不能混作约化成本行。

## 4. 原理推导与正确性依据

**充分性。** 在当前支持域中，两条合法前缀到达相同(v,r)时，后续动作及其
每步资源均由当前v、r和固定弧数据决定。沿任意候选后缀归纳，其合法性相同。
非负资源使逐步容量检查与最终总量检查一致，超限前缀不会在后面恢复可行。

**递推。** 在精确目标运算的数学模型中，令w_e=c_e−πᵀa_e，
D(s,0)=c₀−πᵀa₀；对每个可行后继，

\[
D(u,r+d_e)=\min\{D(u,r+d_e),D(v,r)+w_e\}.
\]

原图拓扑序也排列全部扩展状态。归纳假设所有前驱已正确计算，枚举每个合法入转移
便覆盖全部前缀；同状态最低前缀与任意共同后缀组合都不会更差。
汇的全部资源状态取最低值，得到数学模型最优值。精确平局下可保留字典序最小
完整弧ID元组；DAG中两个到相同节点的前缀不能互为严格前缀，因此共同后缀不颠倒该平局序。

实现对目标使用浮点标签，严格比较而不按tolerance合并。以上归纳给出数学依据，
不能把它直接当作任意尺度浮点最优性证明。独立重构检查所选列及label一致性；
小dyadic真值族才另外核对实际输出是否为精确最优路径。

状态上界为|V|∏(B_j+1)，可达部分可能很大。资源维数q固定时，按容量数值可称
伪多项式；q随输入增长时，即使各B_j=1，也可能有2^q种资源组合。
该状态计数不含Python对象、路径元组复制、排序和全图验证成本。
预算中断保留计数，清空候选。

## 5. 算法到代码的映射

| 数学/语义对象 | 实现 |
|---|---|
| 图、容量、每弧整数资源 | [ResourceDagPricingProblem](../../../src/silo/decomposition/resource_dag_pricing.py)，组合图、复制只读映射 |
| 当前(v,r)标签及拓扑递推 | 同文件price_resource_dag，按资源元组遍历，只合并完整相同状态 |
| 原始列与资源重构 | 同文件_reconstruct，从弧数据重新累加、核对每步资源/端点/rc |
| 完成、无路、数值或预算失败 | ResourceDagPricingStatus及冻结结果；非成功is_improving=None |
| 独立路径真值 | [DFS/Fraction枚举](../../../tests/verification/test_resource_dag_pricing_oracles.py)，不用生产helper |

状态计数只在插入时加一，源、汇、死路都计入；替换不计。
转移计数先检查预算再加一，资源不合法尝试也计入；汇停止展开。
输入验证及全弧权重先于源初始化，预计算失败因此可以是0/0。

## 6. 核验与复现

在仓库根目录及现有虚拟环境运行以下完整程序；代码使用实际公开API。

```python
from silo.decomposition import (
    DagArc, DagPricingProblem, ResourceDagPricingProblem,
    ResourceDagPricingStatus, price_resource_dag,
)

graph = DagPricingProblem(("s", "u", "t"), (
    DagArc("a", "s", "u", 0), DagArc("b", "s", "u", 1), DagArc("c", "u", "t", 0),
), "s", "t")
for cap, resources, usage in (
    ((2,), {"a": (2,), "b": (0,), "c": (1,)}, (1,)),
    ((2, 2), {"a": (2, 0), "b": (0, 2), "c": (1, 0)}, (1, 2)),
):
    problem = ResourceDagPricingProblem(graph, cap, resources)
    result = price_resource_dag(problem, {}, state_limit=4, transition_limit=4)
    assert result.status == ResourceDagPricingStatus.OPTIMAL
    assert result.arc_ids == ("b", "c") and result.cost == result.reduced_cost == 1
    assert result.resource_usage == usage and result.is_improving is False
    assert (result.states_discovered, result.transitions_checked) == (4, 4)
    limited = price_resource_dag(problem, {}, transition_limit=3)
    assert limited.status == ResourceDagPricingStatus.TRANSITION_LIMIT
    assert limited.arc_ids == () and limited.is_improving is None
print("L0009: core and two-resource examples verified")
```

实际核验：上述程序、[独立运行例](../../../examples/resource_dag_pricing.py)、
72项[unit测试](../../../tests/unit/test_resource_dag_pricing.py)，以及
64个固定子图×3资源配置×3对偶×2输入表示=1152次Fraction真值调用。
该1152次调用按一个调用一个pytest项组织；总计1224项新测试。
旧4075项与新增项合计5299项，2026-10-20全量通过（15.87s），Ruff/结构通过。
测试计数与时间是本机正确性记录，不是算法加速依据。输入族、对偶和弧编号固定在合同。

## 7. 研究意义与可扩展问题

现有能力提供资源约束路径列域的可核对冷基线，能支撑后续资源CG及同一列域的比较。
候选返回原始列和完整行坐标，方便核验主问题对偶与约化成本。
这是成熟DP思想在固定支持域中的参考实现，没有创新或性能结论。

对偶改变时，同一状态的最佳前缀可切换；本模块每次冷重算。
跨对偶维护仍需保存或恢复原先未选来源、完整失效依据、恢复正确性及全成本账本。
当前(V,r)充分性和有限测试不能替代这些义务。真实应用门控按收尾计划单元C独立进行。

## 8. 局限、反例与失效条件

资源必须为严格非负整数；超过2^53仍用Python整数。连续资源、负消耗/恢复、
时间窗、访问记忆、配对和一般有环路径不在当前域。DAG图本身不保证任务不重复服务，
有这种约束时需要额外状态，不能把当前(v,r)套用过去。

目标计算可能舍入。链成本10^16、1、−10^16的逐步label为0，重构fsum为1，
模块返回NUMERICAL_ISSUE；重构差超过既有1e-9或跨改善阈值都失败。
即使所选列重构通过，也不能检测已因舍入丢掉的更优列；全局精确实数最优和平局不受保证。
零维正常实例核对普通定价；本接口不展开汇后的图分支，其极端数值诊断可能不同。

状态/转移预算限制的是搜索计数，预计算、原图大小、路径复制和重构仍需时间与内存。
本任务没有硬运行时间或总内存保证。LIMIT不表示无路、无负列或已完成最优性检查。

## 9. 练习与解答入口

[八道练习](exercises.md)与[完整解答](solutions.md)使用稳定编号L0009-E01至E08，
覆盖手算、充分状态、双资源、对偶切换、预算语义、改善阈值、研究边界与浮点消减。

## 10. 开发来源与修订记录

| 类型 | 路径或版本 | 用途 |
|---|---|---|
| 原子任务 | [20261020-04-01](../../../tasks/codex/20261020-04-01_resource-dag-pricing.md) | 原3非负整数可加资源冷基线 |
| 执行报告 | [A交付记录](../../../tasks/reports/20261020-04-01_resource-dag-pricing_report.md) | 检查、计数、范围、Git证据 |
| 实现核验提交 | be03540db4f966a6c98f71e41d9025b08ddd7555 | 新模块、导出、unit/oracle及运行例 |
| 接口文档 | [资源定价API](../../../docs/resource_dag_pricing.md) | 当前调用和诊断范围 |

2026-10-20 v0.1.0：按上述真实实现核对完整程序、例子和八道解答。
原七步、SILO-DOS与讲解版本分别管理；A交付不关闭研究阶段，后续审查另记。
