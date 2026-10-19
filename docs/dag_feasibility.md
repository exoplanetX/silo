# DAG初始可行性恢复接口

[restore_dag_feasibility](../src/silo/decomposition/dag_feasibility.py)从非空合法路径seed出发，
用单位人工违背量和全域零成本定价恢复耦合行可行性。原理、手算和完整程序见
[L0005](../learning/lessons/L0005-cg-feasibility/README.md)。

~~~python
from silo.decomposition import DagFeasibilityStatus, restore_dag_feasibility
from silo.decomposition import solve_dag_column_generation

restored = restore_dag_feasibility(problem, solver=None, tolerance=1e-9, iteration_limit=100)
if restored.status == DagFeasibilityStatus.FEASIBLE_SEED_FOUND:
    optimized = solve_dag_column_generation(restored.feasible_problem)
~~~

## 输入域和辅助模型

problem为既有DagColumnGenerationProblem；图、行名/方向/RHS、conv=1、原成本/c0与
合法非空seed规则沿用[CG接口](dag_column_generation.md)。seed可不满足耦合行。
空seed、自动搜索首条路径、资源/分支/整数路径规则没有扩展。
solver默认由RMP使用Revised，亦可指定现有Tableau。iteration_limit为正整数且拒绝bool，
tolerance有限正值；非法输入抛出TypeError/ValueError。

保持conv不加人工变量；其他行按LE减v、GE加u、EQ加u减v，u/v非负。
人工列单位成本1、conv系数0，真实路径成本全部0，辅助常数0。
artificial_columns保存内部人工变量名到(row_name, sign)的只读映射；真实列column_paths
保存独立path_i到完整弧ID元组的注册表，两者不混合，行/弧ID分隔字符不参与名字拼接。
单位罚权对行单位敏感；当前没有行缩放或可调罚权。

构造独立零成本图视图，保留所有系数与图结构；原graph及原成本/c0保持。
每轮全行冷RMP后，独立核对原始行、权重、F、坐标、符号、人工列真实系数/单位成本及
1-a_art*pi≥-1e-9，再按需要调用完整DAG定价。候选从公开零成本图独立重构，
实际入RMP的成本为0、系数为重构原值。

## 状态和原始见证

| DagFeasibilityStatus | 含义 |
|---|---|
| FEASIBLE_SEED_FOUND | F小后，无人工、零目标、完整原始行的独立RMP复核成功 |
| POSITIVE_VIOLATION_BOUND | 完整零成本定价与人工列约束/数值差距均通过，得到L>tolerance |
| ITERATION_LIMIT | 辅助轮预算用尽，未追加未经下轮求解的路径 |
| MASTER_FAILURE | 辅助RMP非OPTIMAL，保留实际后端诊断 |
| PRICING_FAILURE | 零成本定价失败或与合法seed矛盾的NO_PATH |
| NUMERICAL_ISSUE | 证据/算术/字段/人工约束/差距/原始复核不一致 |

F<-1e-9诊断；F位于[-1e-9,tolerance]内进入原始行复核，小F本身不产生成功。
原始复核非OPTIMAL或独立行核对失败均为NUMERICAL_ISSUE，failure_stage=original_validation。
原始见证仍按既有绝对1e-9核验，自定义tolerance不改变全局行精度。

只有成功结果的feasible_problem和feasibility_witness非None。前者仅替换seed为全部已生成
真实路径，保留原graph、rows、conv与c0；后者只含真实路径变量的零目标RMP快照。
真实权重保留，不剪小值、归一化或删行。调用者显式进入原目标CG；恢复器不自动优化原目标。

## 界、记录和调用计数

F>tolerance时以本轮pi对全部零成本路径定价rho=min(-a*pi)。令delta=min(0,rho)，
D=sum(b*pi)、L=fsum(全部b*pi,delta)。平移conv乘数只改变真实列rc，人工列conv=0使其rc不变；
人工对偶约束是建立平移下界的必要条件。当前列F是受限罚值，不能单独判断整个域。

字段numerical_gap=fsum(F,-L)，objective_gap从原始c_i*x_i和-b*pi及-delta求和，
roundoff_allowance=32*ulp(绝对贡献和)。沿用[第5步规则](dag_column_generation.md)：
负gap例外同时受局部eta和用户tolerance限制；正gap与rho阈值不加eta。
rho容差内但gap超限，或F>tolerance且L≤tolerance，均诊断。
显著负rc已有路径也诊断；目标不变继续，最后预算轮不追加未求解路径。

DagFeasibilityIteration保存iteration、当前column_paths/artificial_columns、master_result、
penalty_objective、pricing_result、original_validation、D/rho/L/两种gap/eta及accepted_path。
F小直接复核时没有定价，全域界/差距字段为None；失败轮也不发布新界。
DagFeasibilityResult保存上述迭代、状态/message、failure_iteration/failure_stage、
最后有效辅助RMP和其列集轮号、两类注册表，以及仅成功时的原始见证/可行问题。
后续失败尝试自己的列集在失败轮中，顶层历史有效列集不能冒充失败轮的新证据。

auxiliary_solve_count计辅助冷求解，validation_solve_count计额外原始复核（最多1次）。
后端调用总数为两者之和，原始复核不消耗辅助预算；最后允许轮F小仍可正常复核成功。
输入、映射、结果和历史快照独立只读。初始化列汇总即溢出时没有已求解轮或有效注册表。

## 证据范围

精确算术下F*=0等价于原完整域可行；严格正对偶下界可分离不可行。
当前POSITIVE_VIOLATION_BOUND提供浮点数值证据，不发布全局INFEASIBLE或严格Farkas见证。
648组解析回归中，10个末轮返回pi存在2^-52的精确人工约束越界，仍在既有1e-9核验内；
其中8个定价轮的形式平移目标超过解析F*达2^-54。测试单列这些情形，未投影乘数或声称
它们满足精确对偶条件，详情见[执行报告](../tasks/reports/20261019-06-01_dag-feasibility_report.md)。
32ULP仍是工程局部尺度；既有LP与DAG浮点边界、单位罚权和有限小模型适用范围保留。
