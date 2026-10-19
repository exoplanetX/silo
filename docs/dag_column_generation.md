# DAG凸组合列生成接口

[控制器](../src/silo/decomposition/dag_column_generation.py)连接现有RMP与普通DAG全路径定价。
完整推导和退化示例见[L0004](../learning/lessons/L0004-column-generation/README.md)，
依赖接口见[RMP](restricted_master.md)与[DAG定价](dag_pricing.md)。

## 固定主问题与输入

完整域是同一`DagPricingProblem`的全部s-t路径，路径权重连续非负，固定行包括
一条`sum(lambda)=1`的凸组合等式，其他行为LE/GE/EQ。目标为最小化
`objective_constant + sum(path_cost * lambda)`。路径成本与行向量沿用图的基项加弧项。

以下接口从`silo.decomposition`导入：

~~~text
DagMasterRow(name, sense, rhs)
DagColumnGenerationProblem(graph, rows, convexity_row, seed_paths, objective_constant=0)
solve_dag_column_generation(problem, *, solver=None, tolerance=1e-9, iteration_limit=100)
~~~

`sense`复用`ConstraintSense`，行名唯一且恰与图的`row_names`匹配；名称保留原拼写。
指定凸组合行必须EQ、RHS精确为1，图中该行基系数精确为1、每弧系数精确为0。
其他RHS、目标常数和图数据须有限。所有输入记录冻结并防御性复制。

`seed_paths`是非空且无重复的合法完整路径序列，每条路径用完整弧ID元组表示。
拒绝空路径、未知弧、不连贯路径及未到t的路径。初始列数据从图重构，调用者不另传成本。
初始RMP须靠seed可行；当前没有可行性定价、人工列或自动seed搜索。
非法输入抛出ValueError/TypeError。`iteration_limit`为正整数且拒绝bool，容差有限正值。
默认后端由RMP选择Revised；可显式提供现有Tableau后端。不增加任意pricer参数。

## 轮次、列身份与停止

一轮包含对当前列冷求解、用本轮经核验的最小化pi对完整DAG定价，再决定停止或加入一列。
每次只加入一条显著负约化成本的新路径；目标不变也继续。列身份为完整弧ID元组，
变量名内部按`path_0`、`path_1`编号，注册表保存其对应关系。相同成本/向量的不同路径
仍是不同身份；不靠分隔符拼接去重。重新排列输入可能改变退化轨迹，最终可行性/目标需一致。

接收候选前，从公开图数据独立重构路径、成本、全部行系数与rc。使用既有1e-9核对
返回字段，并核对改善分类。加入RMP的字段使用重构原值；rho也使用重构rc。
全部路径域包含已存在列，已有路径仍显著负rc时诊断数值问题。

| `DagColumnGenerationStatus` | 含义 |
|---|---|
| `TOLERANCE_REACHED` | rho≥-tolerance，且本轮数值差距介于0与tolerance之间 |
| `ITERATION_LIMIT` | 本轮仍需显著改善列，预算已用尽；未追加未经下轮求解的列 |
| `MASTER_FAILURE` | 当前RMP非OPTIMAL，保留其实际状态与message；初始失败不推出完整域不可行 |
| `PRICING_FAILURE` | 定价非OPTIMAL，包括合法seed下出现矛盾的NO_PATH；不发布本轮界 |
| `NUMERICAL_ISSUE` | 字段/算术/界顺序/差距/重复改善列等不一致；失败轮界为None |

最后允许轮已满足容差时正常停止；limit不会覆盖成功条件。控制器使用独立枚举，
不发布全局Solution或完整主问题SolverStatus.OPTIMAL。后端UNBOUNDED保留为RMP诊断。

## 数值界与读取顺序

每轮从当前列、原始RHS和快照重新计算
`P=c0+c^T*lambda`、`D=c0+b^T*pi`、`rho=min_U(c-a^T*pi)`，再计算
`L=D+min(0,rho)`、`gap=P-L`。P还与RMP发布目标按既有1e-9核对。
只有同轮RMP、定价、字段与界检查全部有效，迭代记录才发布：

- `numerical_upper_bound`：P；`dual_objective`：D；`rho`：重构的最小约化成本。
- `numerical_lower_bound`：L；`numerical_gap`：P-L，保留实际小正差距。
- `pricing_result`：原始定价快照；`accepted_path`：实际接受供下一轮求解的路径，或None。

L>P直接诊断，不裁剪或归零。rho已在容差内而gap过大也诊断；不能只读`is_improving=False`。
界是浮点核验与定价支持的数值估计。精确上下界定理需要当前原始可行、行乘数符号正确、
完整域定价及每条路径凸组合系数/RHS均为1。小负rho仍可能留下微小改善。

结果`DagColumnGenerationResult`含status、message、failure_iteration、不可变iterations，
以及column_paths、column_set_iteration、last_valid_master、last_valid_master_iteration。
每条`DagColumnGenerationIteration`都有本轮iteration、column_paths、master_result及上述定价/界字段。

先读CG状态和失败轮号，再按轮号读取证据。结果注册表与最后有效RMP对应同一成功轮；
后续RMP失败时，失败尝试的列集在该轮迭代中，顶层保留带轮号的历史有效列集。
首次RMP失败时顶层只有该尝试的列注册表，无有效RMP。seed重构先溢出时没有已求解轮或注册表。
定价失败时仍可保留本轮有效RMP，但该轮界字段全部None。历史记录不会伪装为失败轮的新界。

## 当前边界

生产不枚举全部路径；完整列枚举只在测试。每次RMP冷求解，路径选择使用既有拓扑DP，
控制器又独立重构候选与原始行目标。未实现warm start、增量定价、资源约束、整数路径选择、
一般CG插件或原有通用ColumnGenerationSolver入口。浮点、LP内核已有数值债和seed依赖继续保留。
本功能提供可审查参考基线；没有规模、速度或论文创新主张。
