# 受限主问题（RMP）接口参考

[RestrictedMasterProblem](../src/silo/decomposition/restricted_master.py) 在原生最大化
LP 上提供当前列集合的最小化适配。完整手算、符号推导与可执行示例见
[L0002](../learning/lessons/L0002-restricted-master/README.md)。

## 输入与使用

输入为 `Model`，目标方向 `OptimizationSense.MINIMIZE`，变量连续、下界精确为0、
上界为正无穷；成本、矩阵系数、RHS和目标常数均须有限。LE/GE/EQ、负RHS、冗余行和
空列集合允许存在；非法或不支持的模型抛出 `ValueError`，输入类型错误抛出 `TypeError`。
变量名/行名须为非空白字符串，保留其精确拼写、方向与顺序。

给定符合支持域的 `model`：

```python
from silo.decomposition import RestrictedMasterProblem
from silo.lp.simplex.tableau import TableauSimplexSolver

rmp = RestrictedMasterProblem(model)
initial = rmp.solve()  # 默认 RevisedSimplexSolver，每次冷启动。
rmp.add_column(name="p", cost=7, row_coefficients={"a": 1, "b": 1})
result = rmp.solve(TableauSimplexSolver())
```

`solve(solver: LPSolver | None = None) -> RestrictedMasterResult` 只调用传入的原生
LP接口，不经过CLI或后端选择器。输入模型和增列系数字典均由适配层复制；后续调用者
修改原列表/字典不会改变RMP。变量与Bounds为已有冻结记录，持久状态拥有自己的列表。

## 显式加列

`add_column(*, name, cost, row_coefficients)` 加入一个连续非负无上界变量。
未知行、重复变量名、空白名、非有限成本/系数会明确拒绝；失败时保持RMP状态完整。
所有数据先验证，再构造新模型并一次替换持久状态。

省略的已知行系数取零，空映射或全零列合法。不同名称的相同向量也合法，按变量名
区分身份，不做向量去重。名字精确匹配，例如 `"a"` 和 `" a "` 是不同坐标。
调用者显式提供初始列和后续列；接口不生成seed、Big-M列或可行性定价。

每次求解从全部持久原始行和当前全部列构造新的取反模型。另保留独立核验副本，防止
后端修改传入对象后改变核验问题。普通solve无presolve或基复用，并清空可选复用缓存。
旧列矩阵中的冗余关系可能在增列后失效，原生LP本次删掉的行始终保留在RMP持久模型中。

显式`solve_reoptimized(solver=None)`仅支持原生Revised及兼容测试子类，返回新冻结
`RestrictedMasterReoptimizationResult`（`result`包装既有MIN结果及路径诊断）。首次
cold生成合格全行非人工基快照，后续仅增列时按语义键映射，直接Phase II；失败最多
cold一次。旧删行/其他资格不足时保留合法最优结果但清空缓存。普通solve仍可传Tableau。
两种入口都完整重建本轮模型并核验MIN证据；详见[重优化约定](rmp_reoptimization.md)。

## 返回字段与最小化坐标

`RestrictedMasterResult` 为独立的冻结结果类型，字段为 `status`、`objective_value`、
`primal_values`、`dual_values`、`reduced_costs`、`message`，不属于全局最大化 `Solution`。
三种数值映射为复制后的只读 `Mapping`，按名称索引；需要普通字典时调用 `dict(...)`。
后续增列、求解或修改后端结果字典不会改变历史快照。

内部整体取负目标，包含常数；核验成功后返回
`P_min=-P_max`、`pi=-y_max`、`rc_min=-rc_max=c-A.T*pi`。
最小化LE行乘数非正、GE非负、EQ自由，当前列的约化成本非负。内核已恢复负RHS行的
原始坐标，适配层只做上述一次符号转换。

每个原生 `OPTIMAL` 都先在完整取反输入上调用现有 `check_lp_optimality`，使用
`DEFAULT_TOLERANCE=1e-9`。依据缺失、非有限、坐标不全或残差不合格时，返回
`NUMERICAL_ISSUE`。其他状态保留后端状态与消息。所有非最优返回的目标为 `None`，
三种数值映射为空；不会复用上次最优结果。

## 结论范围与数值限制

`OPTIMAL` 只涵盖当前列集合。完整主问题的最优性需要完整定价依据；受限不可行也
不能推出完整主问题不可行。负约化成本说明旧对偶对新增列不再可行，退化时目标可保持不变。

非最优状态属于后端诊断。两个原生LP的直接无界出口已核验完整原始点/射线，
见[无界门控及保守拒绝边界](lp_unboundedness.md)。RMP不新增严格不可行性证明或
一般尺度保证。旧接口来源与当时边界见L0002第8节及
[第2步报告](../tasks/reports/20261019-02-01_restricted-master_report.md)；新复用范围见L0007。
