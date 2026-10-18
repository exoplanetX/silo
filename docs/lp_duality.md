# LP 对偶值与最优性核验：接口参考

系统讲解、手算推导、代码映射和习题集中维护在
[L0001：LP 对偶约定与最优性核验](../learning/lessons/L0001-lp-duality/README.md)。
本文件保留原有路径，供使用者查阅当前 API 约定。

## 支持范围与符号

当前为连续最大化 LP：普通变量非负且无有限上界；现有 presolve 可恢复精确固定
变量。`Solution.dual_values` 使用输入原模型的约束名，行符号为 LE 非负、GE 非正、
EQ 无限制。`reduced_costs` 使用 \(r=c-A^\top y\)。

普通坐标满足 \(r_j\le0\)。固定坐标 \(x_j=v_j\) 的约化成本无符号限制，对偶目标为

\[
D=c_0+b^\top y+\sum_{j\in F}r_jv_j.
\]

恢复原始对偶值和固定约化成本时保留其数值，避免小乘数与大 RHS/固定值的乘积丢失。
一般变量界、自由变量、最小化直接求解和 MIP 对偶最优性不在本功能范围内。

## API 与调用方式

[check_lp_optimality](../src/silo/lp/optimality.py) 接收原模型、恢复后的 `Solution`
和可选正绝对容差，返回 `LPOptimalityCheck`。默认容差为 `1e-7`。
预处理后应将 `reduction.recover_solution(...)` 的结果与原模型一起传入。
完整可运行代码见 [L0001 第 6 节](../learning/lessons/L0001-lp-duality/README.md)。

返回字段为 `passed`、`primal_violation`、`dual_violation`、`stationarity_violation`、
`objective_gap`、`complementarity_violation`、`primal_objective`、`dual_objective`、
`message`。核验读取原模型，重新计算可行性、符号、约化成本、三个目标的一致性与
互补松弛；不信任报告的余量或基状态。

缺失坐标、非有限数值、非最优状态或不支持的模型域返回失败；非法容差抛出
`ValueError`。这提供浮点残差核验，不等于精确证明或一般数值稳健性保证。

## 输出与兼容性

两个现有后端在最优 LP 结果中提供对偶值；调用者按需显式调用核验器。
`silo compare` 自动核验每个后端的原模型依据，使用已有 `1e-9` 绝对容差。
退化时允许不同的合法最优对偶向量；不要求逐坐标相等。
比较 JSON 键保持不变，历史 `dual_values_empty` 仅描述最优结果是否为空。
非最优 LP 和最终 MIP 结果不提供最优 LP 对偶依据。

当前 revised Phase I 存在已记录的人工列来源行/基位置清理边界，特定构造基会返回
`NUMERICAL_ISSUE`。范围与代数说明见 L0001 第 8 节；本次目录整理不改算法。
