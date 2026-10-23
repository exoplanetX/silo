# 一般 LP/MILP 用户入口

`from silo import solve, SolveOptions`，调用`result = solve(model, SolveOptions())`。
Model变量/目标保持原API，Constraint新增lower_bound/upper_bound；显式侧优先于sense/rhs。
`silo optimize model.json`或`silo optimize model.mps`进入统一原生路径；旧solve/mip-solve
命令继续提供历史标准形参考接口。支持域见[原始模型规格](prototype_model_contract.md)，
MPS语法见[MPS格式](mps_format.md)。

统一结果有status、termination_reason、has_primal_solution、objective_value、primal_values、
原始row_activities/row_slacks、dual_values/reduced_costs/side_multipliers、primal_bound/dual_bound、
absolute_gap/relative_gap、iterations/nodes/elapsed_seconds、optimality、witness与diagnostics。
`to_dict()`产生schema_version=2；JSON中无穷界为null，并由dual_bound_is_infinite说明。
MILP不发布LP对偶最优声明。公共dual与reduced cost采用原始目标方向，公式见规格。

CLI退出码：optimal=0，infeasible=2，unbounded=3，limit=4，numerical_failure=5，
invalid_model=6，unsupported=7，文件写入错误=1。API数学终态与用户参数错误分开；
非法SolveOptions直接抛ValueError/TypeError，模型错误通过结构化结果返回。

参数包括time_limit（秒）、node_limit、lp_iteration_limit、relative_gap、absolute_gap，
presolve/scaling/cuts/heuristics布尔开关、best_bound/dfs节点策略和auto/primal/dual LP方法。
CLI对应`--time-limit`、`--node-limit`、`--lp-iteration-limit`、`--relative-gap`、
`--absolute-gap`、`--no-presolve`、`--no-scaling`、`--no-cuts`、`--no-heuristics`。
CLI的`--node-limit`默认10000，API默认100000。默认容差与绝对/相对残差固定于规格。
max_dense_cells限制稠密工作区估算；超限返回resource_limit，输入稀疏字典不会改变稠密内核。

`basis=result.basis`可传入后续`solve(model, options, basis=basis)`。快照存语义行/列键及
矩阵系数；RHS/界或追加行/列变化后检查身份，失效至多一次cold回退。诊断报告实际路径。
presolve或scaling改变结构时允许明确cold回退，不能把给过basis参数计为基复用。

原生路径只使用NumPy和标准库；外部对照从interfaces进入。Tableau/旧Revised类和
原DAG/资源参考CG保留其显式标准形数学域。新用户API不扩大这些低层接口的输入约定。
