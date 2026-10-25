---
lesson_id: L0012
title: 基分解、缩放与原始对偶重优化
topic: lp.reoptimization-numerics
version: 0.2.0
status: checked
created: 2026-10-24
updated: 2026-10-25
verified_code: a9f321374d4ca4758aa63d178f224c33b2a1eb0f
verified_on: 2026-10-25
source_tasks: [20261023-02-01_teaching-prototype, 20261024-02-01_sparse-lp-program, 20261024-02-02_sparse-lp-program]
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
从原模型RHS=2重新开始，若追加z∈[0,1]，首行系数1、成本−3，旧点可行，但新列改善成本，primal pivot增大z。
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

2026-10-25稀疏增补：显式sparse路径增加LU/eta和会话独占数值缓存，
详见[L0015](../L0015-sparse-basis-updates/README.md)。本页元信息已更新到实际复验提交；
原dense正文和以下稀疏增补分别按各自源码、组件和正式轨迹核对。

私有数值因子的身份包含实际B系数、基本列顺序、行侧、坐标方向、尺度及数值策略。
被动basis只提供可核对的语义身份，不携带可共享的SuperLU或eta。每次公开求解仍重新形成
当前模型的基本值、对偶、约化成本和原始空间KKT；旧目标或旧模型的最优状态不可缓存复用。

| 修改 | 可保留的数值对象 | 本次必须重算 |
|---|---|---|
| RHS，B及行方向不变 | LU及eta | 基本值；失原始可行且仍对偶可行时采用dual |
| 界或offset，坐标/补界侧不变 | 可保留B因子 | 新RHS与原变量恢复；结构改变时失效 |
| 追加非基本列，尺度及B不变 | LU及eta | 新列定价；需要时进行真实primal换基 |
| 追加行或行维数改变 | 映射后的被动basis | 新维度B的数值分解和全部状态 |

同一B下的三角求解复用、一次eta更新和跨调用收益是三个不同主张。
因子重构时须撤销旧代次的未提交方向/离基选择；候选新基与主动同基刷新都需完整state
通过原门才发布。旧因子残差已经失信时，恢复失败只能安全退出，不能恢复使用该旧状态。
这些规则及反例详见L0015，本页不复制第二份完整推导。

RR02的4ea4264在固定48/24/6及两容量例通过原空间KKT后获独立SP2 GO；
7891de5另通过150组件与8机制，包含Phase-I清理合法零步换基的正确性修订。
第二包c3fea18另通过159组件及正式8轨迹×冷/热×五重复，1600修改/80初始全部正确，
实际跨调用复用、原空间核验和3.4547/8条收益门通过。L0015保存小例原样运行，覆盖上界修改
后一次实际mapped dual pivot及真实cross reuse；原理、手算和E01–E03对应原组件/正式轨迹核对。
以上为第二包阶段记录。当前a9f3213的12容量/12Netlib和原工件8安装已通过；
RR08重新核warm4完整80项/1680解、原资源与五重复收益门，并明确保留warm3/5超时和辅助观察HOLD。
这支持该轮固定门，不推导跨运行稳定性；本页checked仍仅表示实际教学核对，verified_code保持原身份。
完整收据见[RR02报告](../../../tasks/reports/20261024-02-02_sparse-lp-program_report.md)。
