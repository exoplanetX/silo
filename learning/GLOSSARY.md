# 术语与约定索引

术语按数学功能使用。各篇仍须声明自身模型；本表帮助保持表述一致，不将当前
最大化约定推广到所有研究模型。

| 中文 | English | 本系列中的含义 / 约定 |
|---|---|---|
| 原始问题、原始解 | primal problem / solution | 输入优化问题及其决策变量解 |
| 对偶值、行乘数 | dual value / row multiplier | 约束对应的乘数；LP 最大化中 LE 非负、GE 非正、EQ 自由 |
| 约化成本 | reduced cost | 当前最大化 LP 使用 \(r=c-A^\top y\)；最小化定价须显式转换方向 |
| 基、基矩阵 | basis / basis matrix | 独立列的索引及对应矩阵；基位置和原始行身份分别记录 |
| 原始坐标 | original coordinates | 用户输入的变量与约束，不等同于标准化后的扩展表示 |
| 互补松弛 | complementary slackness | 行乘数与行余量、普通变量与约化成本的互补条件 |
| 最优性核验 | optimality verification | 检查候选解及其依据满足指定模型条件；浮点通过不等于精确证明 |
| 证明 | proof | 支持一般数学结论的论证，须写清假设与适用范围 |
| 见证 | witness | 可核查的构造对象，如一组原始/对偶解或一条合法列 |
| 核验依据 | certificate / verification evidence | 按用途译名；避免把 correctness claim、构造对象、核验过程混为一词 |
| 受限主问题 | restricted master problem, RMP | 当前已生成列上的主问题，最优性范围受列集合限制 |
| 定价 | pricing | 检查未生成列的约化成本、寻找改善列或形成相应终止依据 |
| 资源充分状态 | resource-sufficient state | L0009中(node,累计非负整数资源)决定全部合法后续；不自动涵盖访问记忆/时间窗 |
| 冷资源定价 | cold resource-constrained pricing | L0009每次对偶查询重新构建资源状态标签，无跨对偶缓存 |
| 状态/转移预算 | state / transition limit | L0009分别计已插入状态和实际出弧尝试；耗尽表示不完整搜索，候选为空 |
| 回归案例 | regression case | 固定输入与预期行为，防止已知问题重新出现 |

当前已成篇的说明见 [L0001](lessons/L0001-lp-duality/README.md)。新增术语时写明
适用模型或篇目，避免仅给英文词的固定直译。
