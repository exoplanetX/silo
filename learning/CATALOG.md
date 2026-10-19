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
| [L0004：列生成闭环、退化与最优性差距](lessons/L0004-column-generation/README.md) | 2026-10-19 | `decomposition.dag-column-generation` | checked | [DAG列生成闭环](../tasks/codex/20261019-04-01_dag-column-generation.md) |

L0001 的教学编排在 [系列整理任务](../tasks/codex/20261018-02-01_learning-series.md)
中完成；算法实现和代码基线来自上表的 LP 开发任务。总目录同时记录两种来源。
v0.2.0 由 [Phase-I 来源清理任务](../tasks/codex/20261019-01-01_revised-phase1-cleanup.md)
补充三套身份、手算与证明、数值边界和第六道练习；实际代码基线见篇首元信息与
[执行报告](../tasks/reports/20261019-01-01_revised-phase1-cleanup_report.md)。

## 按主题学习 / 未来专题编排

| 主题单元 | 建议先掌握 | 已有篇目 | 待积累的问题 |
|---|---|---|---|
| 基础：模型与可行性 | 线性代数、线性约束 | 待积累 | 变量域、原始对象、标准化与原坐标 |
| LP：单纯形与对偶 | 基、线性方程组、可行解 | [L0001](lessons/L0001-lp-duality/README.md) | Phase I、冗余行、重优化 |
| 预处理与数值 | LP 基础、浮点误差 | L0001 第 5、8 节 | 变换恢复、缩放与误差传播 |
| 整数优化 | LP 松弛、上下界 | 待积累 | 分支定界、节点状态、剪枝依据 |
| 分解与定价 | 对偶、约化成本、反复求解 | [L0002](lessons/L0002-restricted-master/README.md) → [L0003](lessons/L0003-dag-pricing/README.md) → [L0004](lessons/L0004-column-generation/README.md)，先读L0001 | 资源约束定价、增量维护与更一般主问题 |

“待积累”仅是选材位置，不代表已有章节或已批准的开发任务。主题顺序可以调整；
篇目路径保持稳定。当前第一篇需要读者已有基本 LP 与矩阵知识，前置知识见正文。

## 回看与专题整理方式

学习时按“手算 → 推导 → 代码映射 → 核验 → 练习 → 解答”阅读。
回看某次开发时，先找到篇目，再沿正文来源表进入任务报告、提交与测试。
整理专题时只选达到所需成熟度的篇目，补齐前置知识、记号与交叉引用后再编章号。

当前基准与阶段状态继续查阅 [项目文档](../docs/README.md)；本目录不以篇数衡量
求解器完成度，也不把研究候选列为已实现算法。
