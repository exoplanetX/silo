# 项目文档入口

`docs/` 维护当前使用方法、接口约定、求解范围与开发基准。原理讲解和练习从
[开发伴学系列](../learning/README.md) 进入；设计与研究演变从
[研究笔记](../notes/README.md) 进入。

| 要查什么 | 文档 |
|---|---|
| 当前开发状态、已完成与下一步建议 | [项目当前摘要](../.silo-dos/project_profile.md) |
| 全部合同、修订与执行报告 | [任务索引](../tasks/INDEX.md) |
| 目录职责、真实代码入口与版本追溯 | [开发目录说明](development_layout.md) |
| Pricing 研究笔记、探针、固定输入与复现 | [研究资产入口](../scripts/research/pricing/README.md) |
| 安装、快速开始、项目概览 | [项目 README](../README.md) |
| LP 支持范围 | [LP solver](lp_solver.md) |
| JSON 模型 | [模型格式](json_model_format.md) |
| LP 求解命令 | [solve](cli_solve.md) |
| 预处理诊断 | [presolve](presolve_cli.md) |
| LP 对偶与核验 API | [对偶接口参考](lp_duality.md) |
| 当前列集合的最小化受限主问题 | [RMP 接口](restricted_master.md) |
| 两后端比较 | [compare](backend_compare.md) |
| MIP 求解与示例 | [mip-solve](mip_solve_cli.md)、[示例](mip_examples.md) |
| 恢复开发上下文 | [开发重启记录](development_restart.md) |
| 独立小实例正确性基准 | [基准说明](correctness_baseline.md) |
| 历史 Phase 4 检查矩阵 | [回归检查表](phase4_regression_checklist.md) |

每个数学主题的系统讲解优先维护在 `learning/` 的稳定篇目中。这里保留简明的
当前行为与用法，链接教学正文；历史文档和任务链接继续可访问。
