# 资源路径凸组合参考列生成

`solve_resource_dag_column_generation`将[A资源冷定价](resource_dag_pricing.md)
接入已有MIN受限主问题。模型固定为连续lambda>=0、全局sum(lambda)=1，
其余行可为LE/GE/EQ。原理和两轮手算见
[L0010](../learning/lessons/L0010-resource-dag-cg/README.md)，
小运行例见[resource_dag_column_generation.py](../examples/resource_dag_column_generation.py)。

```text
solve_resource_dag_column_generation(
    problem: DagColumnGenerationProblem, resources: ResourceDagPricingProblem, *,
    solver=None, tolerance=1e-9, iteration_limit=100, reoptimize_rmp=False,
    pricing_state_limit=100000, pricing_transition_limit=1000000,
) -> ResourceDagColumnGenerationResult
```

`resources.graph is problem.graph`必须成立；同值另一图对象也拒绝。
构造时先创建一份DagPricingProblem，再将其同时传给两个问题记录。
两种pricing预算必须为严格正整数，reoptimize_rmp为严格bool，
True时solver只支持None或原生Revised及兼容子类。既有tolerance和轮数规则保持。
全部seed在数值列重构及任何求解前逐弧检查整数资源；非法seed抛ValueError。
seed须已使RMP可行，本入口未建设资源可行性恢复。

每次调用创建新RMP owner。默认每轮一次公开solve，True每轮一次公开
solve_reoptimized；RMP内部管理warm/单次cold回退。每轮消费最终MIN原始行对偶，
重新调用完整资源冷定价，两种pricing预算每轮重新给予。无跨轮资源状态缓存。

候选由控制器再次核对路径、原始成本/完整行/rc/分类及逐步资源。
resource_usage须为同维严格非负整数tuple，并与原始路径重构精确相同；
不允许bool/float伪装资源量。增列只使用原始重构c/a，不使用容差内漂移的返回字段。

沿用DagColumnGenerationStatus：

| 状态 | 含义 |
|---|---|
| TOLERANCE_REACHED | 完整资源最小价及消去公共常数的差距满足既有容差/一致性规则 |
| ITERATION_LIMIT | 已完成允许的求解/定价轮，不追加尚未求解的新列 |
| MASTER_FAILURE | 当前RMP非最优，不使用其对偶定价 |
| PRICING_FAILURE | 资源定价NO_PATH、数值失败或任一LIMIT，保留同轮诊断 |
| NUMERICAL_ISSUE | 主问题证据、候选、资源、差距或重复负列不一致 |

新冻结记录ResourceDagColumnGenerationIteration/Result字段和快照含义与
[普通CG](dag_column_generation.md)一致，iteration.pricing_result为ResourceDagPricingResult或None。
错误的返回记录不放入类型化历史。定价或数值失败轮的所有界、rho、gap、allowance和accepted_path
均为空；不能把LIMIT当正常终止。顶层registry与最后有效master属于同一已解轮；
后续失败的尝试registry在该轮history内。outcome保存真实公开结果，master_result is outcome.result。

设P=c0+cᵀlambda、D=c0+bᵀpi、rho为完整资源域最小rc，delta=min(0,rho)。
仅平移自由conv行对偶可得数学下界L=D+delta，依赖所有列conv系数及RHS均为1。
浮点numerical_gap保存P-L的有符号计算；objective_gap在原始贡献层消去共同c0。
固定32*ulp局部绝对贡献之和及既有拒绝规则保持，不能将该工程余量当LP误差上界。

本模型覆盖固定非负整数可加资源DAG中的路径凸组合参考闭环。
真实多路径覆盖/分割、时间窗、访问记忆、一般有环路径、整数选择和增量定价仍需独立工作。
RMP基复用不改变资源定价每轮冷重算的事实。有限正确性测试不构成加速或论文贡献结论。
