# 整数资源DAG冷定价接口

`price_resource_dag`在固定有限DAG的资源可行s-t路径域中执行冷状态DP。
原问题、推导、小例和练习见[L0009](../learning/lessons/L0009-resource-dag-pricing/README.md)。
普通[price_dag](dag_pricing.md)及其接口保持原样。

```python
from silo.decomposition import (
    ResourceDagPricingProblem, ResourceDagPricingResult,
    ResourceDagPricingStatus, price_resource_dag,
)
```

`ResourceDagPricingProblem(graph, resource_limits, arc_resources)`组合不可变的
`DagPricingProblem`。容量及每弧资源必须为tuple，其中每项满足`type(x) is int`
且非负；资源初始为零、逐弧相加、逐维不超过容量。`bool`、浮点、负数和维数不符
抛出异常。`arc_resources`的键必须恰好等于所有弧ID；零维也必须显式给每弧`()`。
问题防御性复制映射并只读封装。主问题行系数与资源向量分别建模。

```text
price_resource_dag(problem, dual_values, *, tolerance=1e-9,
                   state_limit=100000, transition_limit=1000000)
```

对偶键精确匹配图声明行，各值有限。tolerance有限且为正；两种预算必须为严格正整数。
非法输入在搜索前抛出`TypeError`或`ValueError`。搜索按节点ID稳定拓扑序、
同节点资源tuple序、出弧ID序运行，汇状态停止展开。相同完整`(node, resources)`
保留最低`(label, full_arc_id_tuple)`；无跨资源支配或跨调用缓存。

| 状态 | 含义 |
|---|---|
| `OPTIMAL` | 声明资源路径域的冷搜索及候选重构完成；返回最佳候选，包括非改善候选 |
| `NO_PATH` | 完整搜索无资源可行s-t路径 |
| `NUMERICAL_ISSUE` | 非有限运算、重构与label差超过既有1e-9，或改善判别不一致 |
| `STATE_LIMIT` | 一个资源可行的新状态尚未插入，已发现状态数达到上限 |
| `TRANSITION_LIMIT` | 下一条必要弧尚未检查，已检查转移数达到上限 |

成功字段：`arc_ids`、原始`cost`、含所有声明行的`row_coefficients`、
`reduced_cost=cost-pi^T a`、`resource_usage`和`is_improving=(rc < -tolerance)`。
资源从路径独立重构，并检查连通、端点和每步容量。所有非成功状态清空候选，
`cost/reduced_cost/is_improving/resource_usage=None`，弧序列与行映射为空。
结果冻结，行映射只读；后续调用不修改先前快照。

`states_discovered`统计已插入的不同状态，包括源、汇、死路，不含替换及未插入触发状态。
`transitions_checked`统计非汇状态上实际检查的每个出弧尝试，资源不可行也计数。
顺序为：检查转移预算、计一次转移、算资源、过滤不可行、检查新状态预算、插入或替换。
预算恰好等于所需工作可正常成功；存在候选而剩余工作超限仍返回LIMIT并清空候选。
预计算失败可为0/0。这些计数不包含验证、全弧权重、拓扑排序、路径复制、重构等总成本。

资源运算使用Python整数；目标沿用普通DAG的有限浮点参考语义：严格比较label，
实际相等时比较完整弧ID元组，用户tolerance只控制最终改善判别。
保护只能检查所选候选，无法找回已因舍入丢弃的其他路径；任意实数尺度下的符号最优
和全局规范平局没有保证。固定小dyadic族以独立Fraction枚举检查真最优集。
零维、充分预算、汇无出弧的正常同域实例与普通接口核对；本接口不展开汇后的分支，
因此该区域极端浮点诊断可与旧接口不同，s-t路径域相同。

运行[原生示例](../examples/resource_dag_pricing.py)：

```powershell
& ./.venv/Scripts/python.exe examples/resource_dag_pricing.py
```

支持范围是非负整数可加资源；时间窗、资源重置、访问记忆、一般有环路径、
VRPTW、资源CG接入及增量维护留待各自合同。当前实现不提供加速或创新结论。
