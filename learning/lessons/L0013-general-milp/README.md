---
lesson_id: L0013
title: 一般整数搜索、全局界与可核验GMI
topic: mip.branch-and-cut
version: 0.1.0
status: checked
created: 2026-10-24
updated: 2026-10-24
verified_code: 8a07e4b211795c60bf77bfabda1b90a0b2f3f04c
verified_on: 2026-10-24
source_tasks: [20261023-02-01_teaching-prototype]
---

# L0013｜一般整数搜索、全局界与可核验GMI

## 1. 问题与学习目标

通用MILP需要在分支、割、启发式和预算之间保持同一个有效前沿。本篇学习有效下界怎样
继承、局部割为何随祖先保留，以及如何从整数basic的split得到可核验GMI。

## 2. 前置知识、符号与假设

先读L0011/12。用F=s*f最小化，节点有效下界beta，incumbent值U；开放包括queued、active、
unresolved。GMI表行为xB=b−Σa_j*z_j，其中basic明确整数，所有非基z非负并有整数标签与原坐标图。
浮点输入按实际binary值给严格证明对象，LP最优KKT按固定残差准则。

## 3. 手算例子

min x+y，2x+y>=3，x∈{0,1,2,3}，0<=y<=4。LP点x=3/2,y=0，目标1.5。
用surplus t=2x+y−3，表行x=3/2−y/2+t/2。两非基列连续，f0=1/2，
GMI为y/2+t/2>=1/2，回代得到x+y>=2。它切除LP点，保留整数切片的所有连续可行点。
加割重优化界从1.5升2，与整数最优2相同。

纯整数表行xB=12/5−z1/5−3z2/5给alpha=(1/5,4/15)、RHS2/5，即3z1+4z2>=6。
混合表行xB=3/2−zI/4+zC/2给zI/4+zC/2>=1/2；连续负系数使用负方向分式，不取fraction。

## 4. 原理推导与正确性依据

对整数非基zI任选整数m_j，令q=xB+Σm_j*z_j仍整数，aBar_j=a_j−m_j；连续列aBar=a。
于是q=b−ΣaBar*z，q<=floor(b)或q>=ceil(b)。第一支推出ΣaBar*z>=f0；第二支推出
Σ[−f0/(1−f0)*aBar]*z>=f0。因z>=0，取alpha=max(aBar,−f0*aBar/(1−f0))即可同时支配两支。
整数列在floor(a)/ceil(a)中选较小系数，得到f_j<=f0时f_j，否则f0*(1−f_j)/(1−f0)；
连续列不能用整数平移，保留a或−f0*a/(1−f0)。因此GMI有效；枚举是实例补充而非一般证明。

若x=o+sigma*z，坐标图z=(x−o)/sigma；slack是明确原始行侧/上界的剩余量。
非单位缩放先撤销，整数锚点须整数，slack的整数性须逐式证明。无法唯一投影的自由拆分拒绝。
转float后用delta系数误差在节点箱上的最小值向外调RHS，保证数值候选弱于exact割。
箱或来源含局部加强，割默认local，只有本节点及后代可用。

搜索保持B=min(U,所有开放有效beta)。父节点的两个floor/ceil分支覆盖其全部整数点，children继承
父界；新LP dual bound取max加强。P=sU,D=sB，gap只在有incumbent且B有限时公布。
LP无界须进一步证明整数anchor/ray；分数anchor继续分支，缺证明保留unresolved，不丢前沿。

## 5. 算法到代码的映射

`mip/general.py`管理NodeCut、祖先继承、有效界、pseudocost、启发式、割循环和所有出口。
`lp/tableau_view.py`从原始方程重建精确未缩放basis行；`cuts/gmi.py`只消费被动表行，
推导与外向浮点化，独立于MIP。`utils/rational.py`给共享deadline/操作预算及系数门。
`lp/verification.py`核验原始点/Farkas/射线，公共无界点从同一witness派生。

## 6. 核验与复现

运行`.venv/Scripts/python.exe -m pytest tests/unit/test_prototype_mip.py tests/unit/test_prototype_proof_boundaries.py -q`。
包含96独立整数枚举/连续顶点真值、mixed松弛从1.5到2、有限域逐点GMI、局部祖先/兄弟、
四类限额、三态无界、移位/反射/缩放/slack标签、箱误差和证明预算。
注入有限继承界与无界冲突时，保留incumbent10、dual无穷及gap=None；这是状态机控制测试。
具体运行记录和代码提交核验后填元信息，规模仍由M5统一检验。

## 7. 研究意义与可扩展问题

同一框架可比较分支、节点策略、割选择和启发式，轨迹显示实际调用与失败原因。
基础B&B/GMI的正确实现为研究平台提供能力，不直接证明策略更快或构成新贡献。

## 8. 局限、反例与失效条件

整数LP无界不意味着MILP无界：x=1/2且x整数、y无界即反例。拒绝near-integer候选也不意味着节点不可行。
不可表示的原始大整数先拒绝转换，不能先转float再称保格。无损float公开不了的有理anchor只保留witness。
GMI限80行精确basis、固定深度/轮数/系数和工作预算；跳过割不影响搜索正确性，可能影响性能。

## 9. 练习与解答入口

见[练习](exercises.md)与[解答](solutions.md)，L0013-E01至E03。

## 10. 开发来源与修订记录

来源[总合同](../../../tasks/codex/20261023-02-01_teaching-prototype.md)、
[总报告](../../../tasks/reports/20261023-02-01_teaching-prototype_report.md)、
[算法说明](../../../docs/branch_and_cut.md)。2026-10-24初稿。
