# 总目录与阅读路线

本目录同时保存开发顺序与主题顺序。`checked` 表示已按记录的代码基线核对示例、
链接及对应依据；它不等于出版审定、创新认可或一般正确性证明。
`draft` 表示仍待核对，`superseded` 表示保留供历史阅读并应链接替代篇。

## 按开发顺序回看

| 篇目 | 建篇日期 | 主题 | 状态 | 对应开发任务 |
|---|---|---|---|---|
| [L0001：LP 对偶约定与最优性核验](lessons/L0001-lp-duality/README.md) | 2026-10-18 | `lp.duality` | checked | [LP 对偶开发](../tasks/codex/20261018-01-02_lp-dual-optimality.md) |
| [L0002：受限主问题与列接口](lessons/L0002-restricted-master/README.md) | 2026-10-19 | `decomposition.restricted-master` | checked | [最小RMP适配层](../tasks/codex/20261019-02-01_restricted-master.md) |
| [L0003：DAG精确定价与完整性核验](lessons/L0003-dag-pricing/README.md) | 2026-10-19 | `decomposition.dag-pricing` | checked | [普通DAG定价](../tasks/codex/20261019-03-01_dag-pricing.md) |
| [L0004：列生成闭环、退化与最优性差距](lessons/L0004-column-generation/README.md) | 2026-10-19 | `decomposition.dag-column-generation` | checked v0.2.0 | [DAG列生成闭环](../tasks/codex/20261019-04-01_dag-column-generation.md)、[数值一致性](../tasks/codex/20261019-05-01_cg-bound-consistency.md) |
| [L0005：列生成的可行性恢复与辅助主问题](lessons/L0005-cg-feasibility/README.md) | 2026-10-19 | `decomposition.dag-feasibility` | checked | [可行性恢复](../tasks/codex/20261019-06-01_dag-feasibility.md) |
| [L0006：LP无界判定：可行点、改善方向与数值核验](lessons/L0006-lp-unboundedness/README.md) | 2026-10-20 | `lp.unboundedness` | checked | [LP无界终止核验](../tasks/codex/20261020-01-01_lp-unbounded-check.md) |
| [L0007：RMP基复用、语义坐标与冷回退](lessons/L0007-rmp-reoptimization/README.md) | 2026-10-20 | `decomposition.rmp-reoptimization` | checked | [RMP显式重优化](../tasks/codex/20261020-02-01_rmp-reoptimization.md) |
| [L0008：列生成中的基复用与逐轮证据](lessons/L0008-cg-reoptimization/README.md) | 2026-10-20 | `decomposition.cg-reoptimization` | checked | [CG显式接入](../tasks/codex/20261020-03-01_cg-reoptimization.md) |
| [L0009：整数资源定价、充分状态与有界冷搜索](lessons/L0009-resource-dag-pricing/README.md) | 2026-10-20 | `decomposition.resource-dag-pricing` | checked | [资源DAG冷定价](../tasks/codex/20261020-04-01_resource-dag-pricing.md) |
| [L0010：资源可行列域与凸组合列生成](lessons/L0010-resource-dag-cg/README.md) | 2026-10-20 | `decomposition.resource-dag-column-generation` | checked | [资源参考CG](../tasks/codex/20261020-05-01_resource-dag-cg.md) |
| [L0011：一般模型、可逆变换与原始空间核验](lessons/L0011-general-model/README.md) | 2026-10-24 | `modeling.general-lp` | checked v0.2.0 | [教学研究原型M1](../tasks/codex/20261023-02-01_teaching-prototype.md)、[正确性修订](../tasks/codex/20261024-01-01_prototype-correctness-revision.md) |
| [L0012：基分解、缩放与原始对偶重优化](lessons/L0012-reoptimizable-lp/README.md) | 2026-10-24 | `lp.reoptimization-numerics` | checked v0.2.0 | [教学研究原型M2](../tasks/codex/20261023-02-01_teaching-prototype.md)、[稀疏续接](../tasks/codex/20261024-02-02_sparse-lp-program.md) |
| [L0013：一般整数搜索、全局界与可核验GMI](lessons/L0013-general-milp/README.md) | 2026-10-24 | `mip.branch-and-cut` | checked v0.2.0 | [教学研究原型M3](../tasks/codex/20261023-02-01_teaching-prototype.md)、[正确性修订](../tasks/codex/20261024-01-01_prototype-correctness-revision.md) |
| [L0014：受控研究策略、一般主问题与有限列生成](lessons/L0014-research-interfaces/README.md) | 2026-10-24 | `research.general-column-generation` | checked v0.2.0 | [教学研究原型M4](../tasks/codex/20261023-02-01_teaching-prototype.md)、[正确性修订](../tasks/codex/20261024-01-01_prototype-correctness-revision.md) |
| [L0015：稀疏基、eta更新与重构后的状态一致性](lessons/L0015-sparse-basis-updates/README.md) | 2026-10-25 | `lp.sparse-basis-updates` | checked v0.2.2 | [稀疏整体执行](../tasks/codex/20261024-02-01_sparse-lp-program.md)、[RR02续接](../tasks/codex/20261024-02-02_sparse-lp-program.md) |

L0001 的教学编排在 [系列整理任务](../tasks/codex/20261018-02-01_learning-series.md)
中完成；算法实现和代码基线来自上表的 LP 开发任务。总目录同时记录两种来源。
v0.2.0 由 [Phase-I 来源清理任务](../tasks/codex/20261019-01-01_revised-phase1-cleanup.md)
补充三套身份、手算与证明、数值边界和第六道练习；实际代码基线见篇首元信息与
[执行报告](../tasks/reports/20261019-01-01_revised-phase1-cleanup_report.md)。

L0012稀疏增补与L0015已按实际提交、保存小例和独立数学门核对。
L0015新增流式精确删行与174组件依据；旧正式五重复和当前源码的最终重验身份分别登记。
RR07仅更新L0015验收状态：两条固定cold正确，但频率配对门未达，完整受控性能继续HOLD；教学版本和示例核验身份保持。
RR08重核指定warm4的原固定门并显式披露历次失败；L0012/L0015仅更新验收角色和范围，verified_code与小例执行身份保持。
完整容量、外部组和候选安装的任务完成状态仍查当前执行报告；checked不替代总体门。

## 按主题学习 / 未来专题编排

| 主题单元 | 建议先掌握 | 已有篇目 | 待积累的问题 |
|---|---|---|---|
| 基础：模型与可行性 | 线性代数、线性约束 | 待积累 | 变量域、原始对象、标准化与原坐标 |
| LP：单纯形与对偶 | 基、线性方程组、可行解 | [L0001](lessons/L0001-lp-duality/README.md) → [L0006](lessons/L0006-lp-unboundedness/README.md) | Phase I、冗余行、重优化 |
| 预处理与数值 | LP 基础、浮点误差 | L0001 第 5、8 节 | 变换恢复、缩放与误差传播 |
| 整数优化 | LP 松弛、上下界 | 待积累 | 分支定界、节点状态、剪枝依据 |
| 分解与定价 | 对偶、约化成本、反复求解 | [L0002](lessons/L0002-restricted-master/README.md) → [L0003](lessons/L0003-dag-pricing/README.md) → [L0004](lessons/L0004-column-generation/README.md) → [L0005](lessons/L0005-cg-feasibility/README.md) → [L0007](lessons/L0007-rmp-reoptimization/README.md) → [L0008](lessons/L0008-cg-reoptimization/README.md)；资源专题[L0009](lessons/L0009-resource-dag-pricing/README.md) → [L0010](lessons/L0010-resource-dag-cg/README.md)，先读L0001 | 真实覆盖CG、时间窗/访问记忆、增量维护与更一般主问题 |

资源专题从L0003进入[L0009](lessons/L0009-resource-dag-pricing/README.md)，
再衔接L0004的主问题语义及[L0010资源参考CG](lessons/L0010-resource-dag-cg/README.md)；
时间窗/访问记忆、真实覆盖应用与增量维护仍待各自任务。

“待积累”仅是选材位置，不代表已有章节或已批准的开发任务。主题顺序可以调整；
篇目路径保持稳定。当前第一篇需要读者已有基本 LP 与矩阵知识，前置知识见正文。

## 回看与专题整理方式

学习时按“手算 → 推导 → 代码映射 → 核验 → 练习 → 解答”阅读。
回看某次开发时，先找到篇目，再沿正文来源表进入任务报告、提交与测试。
整理专题时只选达到所需成熟度的篇目，补齐前置知识、记号与交叉引用后再编章号。

当前基准与阶段状态继续查阅 [项目文档](../docs/README.md)；本目录不以篇数衡量
求解器完成度，也不把研究候选列为已实现算法。
