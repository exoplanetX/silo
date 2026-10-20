# RMP显式基复用与重优化

`RestrictedMasterProblem.solve_reoptimized(solver=None)` 对仅显式增列的MIN RMP提供
可选重优化。默认使用原生Revised，兼容测试子类也可；其他后端明确抛TypeError。
普通`solve()`始终cold，并清空此对象的可选缓存。DAG CG默认cold；显式
`reoptimize_rmp=True`每轮一次消费本公开入口的最终result及诊断，CG不另加cold。
见[CG用法](dag_column_generation.md#显式重优化与逐轮诊断)；定价和可行性恢复器保持原入口。

## 使用与结果

```python
first = rmp.solve_reoptimized()  # 首次cold，合格则缓存快照
rmp.add_column(name='q', cost=1, row_coefficients={'conv': 1})
second = rmp.solve_reoptimized()
print(second.result.status, second.used_warm_start, second.cold_solve_count)
```

完整可运行的A/B/C和两条独立等式例见
[L0007](../learning/lessons/L0007-rmp-reoptimization/README.md)。
新冻结类型`RestrictedMasterReoptimizationResult`由decomposition包导出，字段为：

| 字段 | 含义 |
|---|---|
| result | 既有MIN RestrictedMasterResult，字段/符号含义保持 |
| used_warm_start | 实际warm结果最终被接纳时为True |
| warm_phase_two_attempted | 是否实际进入warm Phase II，即使最终cold回退 |
| warm_iterations / cold_iterations | 各路径实际枢轴数，cold含其既有Phase I/II |
| cold_solve_count | 0或1；无快照或warm失败最多cold一次 |
| fallback_reason | 旧快照拒绝或warm失败原因，初次无快照cold时为空 |
| snapshot_available / snapshot_unavailable_reason | 本轮缓存是否合格及原因 |

新增LP入口`RevisedSimplexSolver.reoptimize(model, snapshot=None)`接收原MAX模型，
返回冻结`RevisedReoptimizationResult`。其`details`包装既有RevisedSimplexResult，
`snapshot`为新RevisedBasisSnapshot或None；其余路径/迭代字段同上（可用性由snapshot
是否None判断）。原`solve`、`solve_with_details(model,basis=None)`和旧详情字段保持。

## 资格、映射与核验

快照保存完整有序原行、旧变量类型/界/成本、原始行方向/RHS/旧系数、MAX方向和c0的
冻结内容，以及非人工列清单和基槽语义键。原变量键为`('original', name)`，结构列键
为`('slack'或'surplus', source_constraint)`。新增原变量使结构列整数位置移动，
按这些键重新映射。原名可貌似结构列；角色和来源参与核验。

首轮只有完整原模型最优核验通过、无人工列、全部原始行一行未删、基维度/分区/数值
可行性与标准形元数据均合格，才发布快照。有效最优结果若资格不足，保留OPTIMAL并
说明快照不可用；下一轮完整cold。旧行/变量重排或旧数据任何变化均拒绝复用，
仅省略零系数与显式零等价；模型名不参与数学身份。

每轮重建完整标准形。warm先去掉fresh人工列，保留每个原始行，按旧键映射基，
新增原变量非基0。重解raw基并核验标准形残差、非负性，以及完整原模型点可行性；
通过后直接运行现有primal Revised Phase II。新列负MIN约化成本是继续优化的正常
触发；退化时目标可暂时保持。最终LP OPTIMAL先完整核验，RMP再独立核验后整体
恢复MIN目标、乘数与约化成本。两层使用既有1e-9绝对容差。

## 回退、缓存与边界

warm非最优（包括已核验UNBOUNDED）、非法/不兼容快照、基或完整原点/最优性检查
失败，最多完整cold一次；cold依据失败不重试。warm无界仍走
[第7步原始点/射线门控](lp_unboundedness.md)，cold沿用相同既有出口。
iteration_limit分别用于warm和cold内部既有run，不是本轮总枢轴预算。

最终合格OPTIMAL更新缓存；非最优、最终核验失败或来源删行/资格不足清空缓存。
add_column成功只保留待核验旧快照，失败保持模型/缓存；可一次追加多列。非Revised
参数拒绝不改变对象。历史结果/快照防御性复制并只读，不复用旧primal/dual/rc数组。

本版每次仍完整重建矩阵、重解基系统，不保存LU、不修复删行关系、不接CG、不做
任意模型修改重优化。实际证据限于固定小实例与异常注入；省去Phase I的路径已验证，
运行速度提升、高维稳定性、工业性能与研究创新均需另行证据。
测试与运行记录见 [第8步报告](../tasks/reports/20261020-02-01_rmp-reoptimization_report.md)。
