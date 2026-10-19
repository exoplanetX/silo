# DAG路径精确定价接口

[dag_pricing.py](../src/silo/decomposition/dag_pricing.py)对普通有限有向无环图中全部
s-t路径求最小约化成本。完整手算、正确性推导与人工RMP桥接见
[L0003](../learning/lessons/L0003-dag-pricing/README.md)。

## 对象与输入

- `DagArc(arc_id, tail, head, cost, row_coefficients={})`：稳定弧ID、端点、原成本、稀疏行系数。
- `DagPricingProblem(nodes, arcs, source, sink, row_names=(), base_cost=0, base_coefficients={})`：
  明确完整路径列域、每条路径只计一次的基成本和基系数。
- `price_dag(problem, dual_values, *, tolerance=DEFAULT_TOLERANCE)`：返回独立的`DagPricingResult`。

这些接口从`from silo.decomposition import ...`导入。节点/弧/行ID必须是唯一的非空白
字符串，保留精确名称；平行弧允许，ID须不同。源终点必须存在且不同，全图必须无环，
包括不可达分量。未知端点、未知系数行、自环或环明确拒绝。

所有输入数值有限；`dual_values`的键集必须与`row_names`完全一致，缺失行不默认为零。
稀疏系数省略的已知行取零，空行集配空乘数合法，零列向量和负弧成本合法。
结构/值错误抛出`ValueError`，类型错误抛出`TypeError`。
输入序列复制为tuple，系数映射复制为只读Mapping；后续修改原列表/字典不改变问题。

## 列与对偶坐标

路径列成本为`base_cost + sum(arc.cost)`，列向量为`base_coefficients + sum(arc.row_coefficients)`。
输入乘数是RMP最小化的原始行乘数pi，约化成本为`cost - column.T*pi`，不再变号。
凸组合行系数1可放在基系数中，仅计一次。RMP全局目标常数c0不参与定价。

列域包含图中全部s-t路径，包括已在RMP中的路径；定价层不去重，不生成RMP变量名，
不包装要求非零向量的旧ColumnCandidate。桥接调用者显式提供变量名并调用RMP.add_column。
当前没有资源预算、时间窗、容量、分支谓词或额外路径合法性规则。

## 状态与读取顺序

| status | 字段含义 |
|---|---|
| `DagPricingStatus.OPTIMAL` | 返回最佳路径，即使它不改善；arc_ids为完整弧ID元组，cost为原始列成本，row_coefficients覆盖全部声明行 |
| `NO_PATH` | 图中无s-t路径，arc_ids/映射为空，cost/reduced_cost/is_improving为None |
| `NUMERICAL_ISSUE` | 数值运算或重构检查失败，同样为空字段/None，message说明原因 |

始终先检查status；`is_improving`是三态字段，失败的None不能当作False的无改善结论。
结果为冻结快照，映射只读，可按名称索引或用`dict(...)`复制。换pi重新定价不改变旧结果。

## 数值规则与完整性范围

拓扑动态规划支持负约化弧权；中间标签严格比较，数值完全相等时按完整arc_ids元组
字典序选路。输入节点/弧排列与系数字典插入顺序不改变结果。
用户tolerance须有限正值，只用于最终`reconstructed_rc < -tolerance`，等于阈值时为False。

结果从原成本与系数重新汇总，重算rc并和DP标签比较，绝对差最多为既有1e-9；
该一致性容差与用户改善参数分别使用。即使差很小，两种计算对是否改善的分类不一致
也保守返回NUMERICAL_ISSUE。有限输入产生非有限乘积/汇总同样失败；不会伪装成无路。
实现检查所有弧的约化权，包括不可达分量，再处理可达标签。

“精确”指精确算术下完整优化指定路径域，无启发式截断。Python实现有一般极端尺度、
消去和近等值路径排序的浮点限制。False仅表示本次pi/列域/容差下未发现超过阈值的改善；
精确完整LP最优性还需要有效RMP见证、相同列域及数学上的最小rc非负等条件。
本模块不调用LP/RMP、枚举或外部solver，也不作CG全局终止裁决。

算法的标量松弛数为O(V+E)。当前实现还包括堆拓扑序、排序、稀疏点积、完整路径元组
复制/比较及列向量重构，整体Python成本不直接等于线性时间；详见L0003第5节。
