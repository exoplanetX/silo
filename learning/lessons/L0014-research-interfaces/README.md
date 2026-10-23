---
lesson_id: L0014
title: 受控研究策略、一般主问题与有限列生成
topic: research.general-column-generation
version: 0.1.0
status: checked
created: 2026-10-24
updated: 2026-10-24
verified_code: 35bb032dacfb6afa21833d4159e795367a72170e
verified_on: 2026-10-24
source_tasks: [20261023-02-01_teaching-prototype]
---

# L0014｜受控研究策略、一般主问题与有限列生成

## 1. 问题与学习目标

研究策略需要进入真实搜索过程，同时保留求解器对可行性、有效界和终止的责任。
本篇解释怎样限定策略动作，以及一般主问题的列生成何时能给出完整最优结论。

## 2. 前置知识、符号与假设

先读L0001、L0005、L0012、L0013。列变量lambda>=0，目标min c^T lambda，
行界l<=A lambda<=u。有限池P预先给定，RMP仅含子集S。公开signed dual为pi，
约化成本r_j=c_j-a_j^T pi。完整定价取P内所有未入列的最小约化成本。
本篇的完整性量词限定于声明的有限池；未声明的路径、业务列域不在证明中。

## 3. 手算例子

两行覆盖需求均为1；四列分别为a0=(1,0),c0=3；a1=(0,1),c1=2；
a2=(1,1),c2=4；a3=(2,0),c3=1。初始S={0,1}，解lambda0=lambda1=1，
值5，对偶pi=(3,2)。未入列约化成本r2=-1、r3=-5，因此可添加第3列。
之后lambda3=1/2、lambda1=1，值2.5；pi=(1/2,2)，四列约化成本均非负。
原始可行与对偶可行同值给出完整四列最优2.5。此处lambda和为1.5，说明额外
添加sum(lambda)=1会改变模型。第2列的最终约化成本为1.5。

## 4. 原理推导与正确性依据

覆盖问题的对偶为max 1^T pi，A^T pi<=c，pi>=0。RMP最优对偶只保证已入列
不等式；若完整池定价证明min_j r_j>=0，这个对偶就对完整池可行。
RMP原始解补零后仍对完整池可行，原始/对偶同值，故完整池最优。
浮点实现按冻结残差与目标准则核验，数值近零终止的结论限于该容差。

空初始列可能不可行。Phase I对下侧加入正人工变量、对上侧加入负人工变量；
等式需同时允许两个方向，目标最小化全部人工变量之和，原列在此阶段成本为0。
完整池辅助最优值为0才允许去除人工变量、恢复原目标；辅助值严格为正且完整定价
已闭合，说明原完整池不可行。启发式未找到列不能证明这两个结论中的任何一个。

策略替换同样依赖证明保留：分支只选真正分数变量，再由执行器建立floor/ceil两支；
节点选择只改变已有节点的处理顺序；割选择只挑选已经证明有效的候选；启发式候选
仍需原始空间核验。这样策略可改变轨迹，树的覆盖关系和界的方向由执行器维持。

## 5. 算法到代码的映射

- `silo.mip.research.ResearchExtensions/ResearchContext`：只读输入、受控动作和回调预算。
- `silo.mip.general.solve_milp`：执行动作验证，保留active/open/unresolved前沿。
- `silo.decomposition.general_master.GeneralRestrictedMaster`：公开RMP与增列。
- `FiniteColumnPricer/column_generation`：完整有限池定价与Phase I/II闭环。
- `silo.lp.session.LPSession`：增列基复用；目标/人工列域切换后重新建立有效基。

## 6. 核验与复现

使用`python -m pytest tests/unit/test_research_extensions.py tests/unit/test_general_master.py -q`。
核对只读快照、实际分支/节点/启发式/割选择、错误动作保留界、覆盖/分割/混合行、
辅助可行性恢复、完整定价与启发式终止。两个公开安装例分别为
`silo.mip.research_example.run_example()`和`general_master.covering_example()`。
M4实际检查57项CG与15项公开策略通过，完整质量6137通过；核验基线见篇首完整提交。

## 7. 研究意义与可扩展问题

已有接口可比较策略轨迹、列选择与基复用，同时记录目标/界、时间与失败。
可迁移的研究问题包括定价不完整性与停止依据、动作范围与证明责任，以及策略质量
对树规模的影响。接口可用与方法具有外部贡献应分别判断；此工程不完成原C/D/E研究。

## 8. 局限、反例与失效条件

有限池CG不能宣称对未知无限列域最优；非完整定价也不能用“未找到列”代替证明。
错误的全局凸组合方程会排除上述lambda和1.5的最优解。外部任意割尚无有效性协议，
当前separator仅选择原生已证明割。Python回调须及时返回；执行器检查调用前后时间，
无法抢占无限循环回调。LP数值失败、非零人工变量和迭代限额都必须保留各自终止状态。

## 9. 练习与解答入口

见[练习](exercises.md)及[解答](solutions.md)：计算对偶与约化成本、构造不完整定价反例、
说明非法策略动作怎样影响证明义务。

## 10. 开发来源与修订记录

来源为[原型总合同](../../../tasks/codex/20261023-02-01_teaching-prototype.md)M4及
[总报告](../../../tasks/reports/20261023-02-01_teaching-prototype_report.md)。2026-10-24初稿，
与原十篇及M1–M3共同保持稳定ID；实际代码核验待M4 checkpoint。
