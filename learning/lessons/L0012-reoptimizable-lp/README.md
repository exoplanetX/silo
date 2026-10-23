---
lesson_id: L0012
title: 基分解、缩放与原始对偶重优化
topic: lp.reoptimization-numerics
version: 0.1.0
status: checked
created: 2026-10-24
updated: 2026-10-24
verified_code: 8a07e4b211795c60bf77bfabda1b90a0b2f3f04c
verified_on: 2026-10-24
source_tasks: [20261023-02-01_teaching-prototype]
---

# L0012｜基分解、缩放与原始对偶重优化

## 1. 问题与学习目标

连续修改模型时，解过的基往往比重新Phase I更有用。本篇区分原始可行与对偶可行，
理解四类修改为何选择不同重优化方式，并把真实基复用与仅传递basis参数区分开。

## 2. 前置知识、符号与假设

MAX c'z，Az=b，z>=0；B为非奇异基本列矩阵，zB=B^-1 b，lambda=B^-T cB，
rc=c−A'lambda。原始可行是zB>=0，对偶可行是所有非基rc<=0。旧标准形数学域见L0001，
一般模型的正反映射见L0011。这里是稠密有限精度参考算法。

## 3. 手算例子

min 3−x−2y，x+y<=2，0<=x<=2，0<=y<=1.5，最优x=.5,y=1.5，值−.5。
把首行RHS改1，旧基算出x=−.5,y=1.5，破坏原始可行；成本未变，对偶仍可行。
dual pivot使x离开、相应slack进入，得到x=0,y=1，目标1。
若追加z∈[0,1]，首行系数1、成本−3，旧点可行，但新列改善成本，primal pivot增大z。
得到z=1,y=1,x=0，目标−2。四类修改的完整测试见下文。

## 4. 原理推导与正确性依据

原始单纯形选rc_j>0进入，d=B^-1 Aj，保持zB−theta*d>=0的最小比率离开；
若d无正分量，非负方向与可行点构成无界候选，仍须原始精确核验。
对偶单纯形选负基本值离开，表行aBar=e_i'B^-1 A，在aBar_j<0的列中选
rc_j/aBar_j最小比率，维持rc<=0。不存在这种列时，B^-T e_i给Farkas候选。

QR写B=QR，解Rz=Q'b及R'w=cB、lambda=Qw，避免显式逆；同一基的分解可多次使用。
出现残差或奇异异常，重建同一实际基一次并记录真实尝试。失效warm再至多一次cold。
缩放A_s=RAC、b_s=Rb、c_s=Cc；原变量z=Czs，对偶lambda=Rlambda_s，rc=rc_s/C。
所有最终判据回原始模型，缩放后的“小残差”不能替代这一关。

## 5. 算法到代码的映射

`lp/kernel.py:QRFactor`与`solve_canonical`维护基/Phase I/II及两种枢轴；
`BasisSnapshot`保存version2、语义行/列与完整旧矩阵。新增行可能插在补界行之前，
因此按身份找旧子块，不用物理前缀。`lp/session.py:LPSession`拥有模型副本与basis；
`lp/general.py`负责回解与核验。诊断报告cold/warm、primal/dual pivots、分解/复用/重分解。

## 6. 核验与复现

运行`.venv/Scripts/python.exe -m pytest tests/unit/test_prototype_lp.py -q`。
96固定小LP逐个比较独立有理真值，四类warm分别与cold比答案及原始KKT。
前三类实际dual_pivots>0，加列primal_pivots>0；奇异基实际重分解后仅一次cold。
独立容差反例检验严格primal不会被宽dual放松，整数候选拒绝也不能关闭未证节点。
最终代码基线及实际完整核验在元信息/总报告登记，draft不代表规模门槛通过。

## 7. 研究意义与可扩展问题

可重优化LP使增列、加割及节点界变化共用一个可观测内核。基身份和事件轨迹可比较研究策略。
复用次数不直接证明加速；稀疏LU、更新分解和定价策略属于后续可替换边界。

## 8. 局限、反例与失效条件

近奇异、极端系数比例和人为极严容差可能返回数值失败。数据转换前检查稠密工作区门槛，
不承诺精确峰值内存。浮点输入按实际binary值核验严格证明对象，有理重构只能给候选。
primal、dual、integrality、pivot、互补、目标容差各管自己的判据；整数近似须取整并复核原始行。

## 9. 练习与解答入口

见[练习](exercises.md)与[解答](solutions.md)，L0012-E01至E03。

## 10. 开发来源与修订记录

来源[总合同](../../../tasks/codex/20261023-02-01_teaching-prototype.md)、
[总报告](../../../tasks/reports/20261023-02-01_teaching-prototype_report.md)、
[数值说明](../../../docs/numeric_engine.md)。2026-10-24初稿。
