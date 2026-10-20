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
solve_dag_column_generation(problem, *, solver=None, tolerance=1e-9,
                            iteration_limit=100, reoptimize_rmp=False)
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

一轮包含求解当前RMP、用本轮最终经核验的最小化pi对完整DAG定价，再决定停止或加入一列。
每次只加入一条显著负约化成本的新路径；目标不变也继续。列身份为完整弧ID元组，
变量名内部按`path_0`、`path_1`编号，注册表保存其对应关系。相同成本/向量的不同路径
仍是不同身份；不靠分隔符拼接去重。重新排列输入可能改变退化轨迹，最终可行性/目标需一致。

接收候选前，从公开图数据独立重构路径、成本、全部行系数与rc。使用既有1e-9核对
返回字段，并核对改善分类。加入RMP的字段使用重构原值；rho也使用重构rc。
全部路径域包含已存在列，已有路径仍显著负rc时诊断数值问题。

| `DagColumnGenerationStatus` | 含义 |
|---|---|
| `TOLERANCE_REACHED` | rho≥-tolerance、objective_gap≤tolerance，且有符号差距通过局部一致性判据 |
| `ITERATION_LIMIT` | 本轮仍需显著改善列，预算已用尽；未追加未经下轮求解的列 |
| `MASTER_FAILURE` | 当前RMP非OPTIMAL，保留其实际状态与message；初始失败不推出完整域不可行 |
| `PRICING_FAILURE` | 定价非OPTIMAL，包括合法seed下出现矛盾的NO_PATH；不发布本轮界 |
| `NUMERICAL_ISSUE` | 字段/算术/界顺序/差距/重复改善列等不一致；失败轮界为None |

最后允许轮已满足容差时正常停止；limit不会覆盖成功条件。控制器使用独立枚举，
不发布全局Solution或完整主问题SolverStatus.OPTIMAL。后端UNBOUNDED保留为RMP诊断。

## 显式重优化与逐轮诊断

`reoptimize_rmp`严格接收bool，0/1、字符串、None等均TypeError。默认False继续每轮
公开`RMP.solve`，允许现有Revised、Tableau和兼容测试后端。True仅允许solver=None
或原生Revised/兼容测试子类；不支持的后端在RMP构造、LP或定价之前拒绝。

True每轮仅调用一次公开`RMP.solve_reoptimized`，消费其最终MIN result。旧基不合格
或warm失败时，至多一次cold已由RMP内部完成；CG不追加cold或读取基缓存。每次CG
新建一个RMP owner，所有显式增列在同一owner进行。

`DagColumnGenerationIteration`末尾追加默认None的`rmp_reoptimization`，类型为现有
冻结`RestrictedMasterReoptimizationResult`。False每轮为None；True每个已求解轮，
包括失败与外层limit，均保留同轮实际outcome，且`master_result is outcome.result`。
attempted/used_warm、cold次数、分开迭代、原因与快照资格全部沿用公开outcome。
0枢轴可以是有效复用；目标未降也可以发生真实退化枢轴。普通冷/热路径的最优对偶、
定价路径和轮数可不同，应按各自当前列集核验。用法与完整程序见
[L0008](../learning/lessons/L0008-cg-reoptimization/README.md)，基资格见
[RMP重优化](rmp_reoptimization.md)。

RMP最终失败保留尝试registry/outcome，顶层有效轮保持上一成功轮；本轮不定价。
`_master_objectives`通过、已登记有效RMP后才发生pricing/candidate/gap失败时，
顶层有效RMP可属于当前轮，但本轮全部界为空。原始主目标核验先失败时保留较早有效轮。
seed重构先失败则没有已求解轮/诊断。内部回退计入同一外层轮，最后允许轮不追加未解列。
独立恢复器仍走原入口；显式将feasible_problem交给CG(True)时，经济首轮fresh cold，
不共享辅助/原始验证基。定价、原始重构、有符号gap及32ULP规则均保持。

## 数值界与读取顺序

每轮从当前列、原始RHS和快照生成并保存有限乘积`p_i=c_i*x_i`、`d_j=b_j*pi_j`，
rho仍由完整定价并重构。令delta=min(0,rho)，用math.fsum直接汇总：

~~~text
P = fsum([c0, *p])
D = fsum([c0, *d])
L = fsum([c0, *d, delta])
g_raw = fsum([P, -L])
g = fsum([*p, *(-v for v in d), -delta])
A = fsum([*(abs(v) for v in p), *(abs(v) for v in d), abs(delta)])
eta = 32 * ulp(A)
~~~

P还与RMP发布目标按既有1e-9核对。L从原始项求和，g消去公共c0；
精确算术中L=D+delta、g=P-L，浮点发布量可能不逐位满足这些等式。
只有同轮RMP、定价、字段与界检查全部有效，迭代记录才发布：

- `numerical_upper_bound`：P；`dual_objective`：D；`rho`：重构的最小约化成本。
- `numerical_lower_bound`：L；`numerical_gap`：g_raw，保留发布量差的有符号原值。
- `pricing_result`：原始定价快照；`accepted_path`：实际接受供下一轮求解的路径，或None。
- `objective_gap`：g；`roundoff_allowance`：eta。二者追加在原有accepted_path之后，
  默认None，旧位置参数构造继续有效。

停止和界一致性使用g：g≥0通过一致性；g<0仅在eta≤tolerance且-g≤eta时通过，
其余负g诊断。eta>tolerance只禁用负差距例外，非负g仍按普通规则。
rho容差内而g>tolerance仍诊断；正向阈值不增加eta，rho改善仍严格为rho<-tolerance。
微小负g停止时message说明采用局部舍入判据。g_raw和g都不裁剪、取绝对值或互相替换。
大c0可能使g_raw=0而g仍显著为正；不能只读g_raw或`is_improving=False`。

eta不含c0，A=0采用实际ulp(0)。32是固定工程局部尺度，不能理解为LP误差严格上界；
其计算溢出或任何乘积/总和非有限均诊断。原始行、符号、权重、候选及目标核验未放松。
界是浮点核验与定价支持的数值估计。精确上下界定理需要当前原始可行、行乘数符号正确、
完整域定价及每条路径凸组合系数/RHS均为1。小负rho仍可能留下微小改善。

版本区别：初版857397e对任何L>P直接失败，且使用g_raw停止；本次数值修正改为以上
原始贡献求和与局部判据。旧合同/报告保留其历史含义，当前规则见
[第5步合同](../tasks/codex/20261019-05-01_cg-bound-consistency.md)。

结果`DagColumnGenerationResult`含status、message、failure_iteration、不可变iterations，
以及column_paths、column_set_iteration、last_valid_master、last_valid_master_iteration。
每条`DagColumnGenerationIteration`都有本轮iteration、column_paths、master_result及上述定价/界字段。

先读CG状态和失败轮号，再按轮号读取证据。结果注册表与最后有效RMP对应同一成功轮；
后续RMP失败时，失败尝试的列集在该轮迭代中，顶层保留带轮号的历史有效列集。
首次RMP失败时顶层只有该尝试的列注册表，无有效RMP。seed重构先溢出时没有已求解轮或注册表。
定价或数值检查失败时仍可保留本轮有效RMP，但该轮界/g_raw/g/eta字段全部None。
历史记录不会伪装为失败轮的新界。

## 当前边界

生产不枚举全部路径；完整列枚举只在测试。RMP默认cold，可显式选择保守基复用，路径选择使用既有拓扑DP，
控制器又独立重构候选与原始行目标。未实现增量定价、资源约束、整数路径选择、
一般CG插件或原有通用ColumnGenerationSolver入口。浮点、LP内核已有数值债和seed依赖继续保留。
本功能提供可审查参考基线；没有规模、速度或论文创新主张。
