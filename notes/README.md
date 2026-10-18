# 设计与研究笔记入口

`notes/` 保存建模/算法设计、研究假设、反例、路线判断与历史决策的演变。
现有数字前缀和原路径保留，避免破坏任务与报告引用。笔记中的阶段性结论应结合
日期、假设和后续修订阅读；进入笔记目录不自动代表已经实现或完成一般验证。

已有主题包括：

- [求解器总体路线](00_solver_roadmap.md)。
- [单纯形、基与重优化](02_simplex_basis_and_reoptimization.md)、
  [revised 设计](10_revised_simplex_design.md)、[历史对偶设计](11_dual_values_design.md)。
- [预处理设计](12_presolve_scaling_design.md)、[重复约简](13_repeated_presolve_design.md)。
- [分支定界](15_branch_and_bound_design.md)、[割与回调](18_cut_callback_boundary_design.md)。
- [分解边界](19_decomposition_boundary_design.md)、[不确定性边界](20_uncertainty_boundary_design.md)。
- [原生实现延期决策](25_native_implementation_defer_decision.md)。

增量定价研究材料已纳入版本控制；源码、输入清单、结果身份和运行方法从
[pricing 研究资产入口](../scripts/research/pricing/README.md) 查询：

| 研究记录 | 内容 |
|---|---|
| [26](26_incremental_pricing_research_start.md) | 起点、公式与反例 |
| [27](27_pricing_operation_alignment_and_structure_class.md) | 核验目录与结构类 |
| [28](28_pricing_frontier_state_and_repair_baseline.md) | 状态与参考修复 |
| [29](29_pricing_application_structure_and_cost_gate.md) | 公开实例、应用结构和成本门控 |
| [30](30_pricing_locality_conditions_and_nearest_neighbors.md) | 局部性条件与相近工作 |

这些笔记保留原有研究判断。纳管记录说明有限复现范围，不代表定价方法已进入求解器。

后续研究笔记继续按内容和现有命名规则保存，不因学习系列而重新编号。
适合教学的知识可提炼到 [learning/](../learning/README.md)，并链接原始笔记作为
来源；完整教学正文只维护一处。当前 API 查 [docs/](../docs/README.md)，执行情况查
[任务报告规则](../tasks/README.md)。
