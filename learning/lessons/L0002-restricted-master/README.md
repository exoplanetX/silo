---
lesson_id: L0002
title: 受限主问题与列接口
topic: decomposition.restricted-master
version: 0.1.0
status: checked
created: 2026-10-19
updated: 2026-10-19
verified_code: 48c242d2fba886807d1230fb7a72b85c3f212b0e
verified_on: 2026-10-19
source_tasks:
  - 20261019-02-01_restricted-master
---

# L0002｜受限主问题与列接口

[系列入口](../../README.md) · [总目录](../../CATALOG.md) ·
[API参考](../../../docs/restricted_master.md) · [L0001对偶基础](../L0001-lp-duality/README.md)

## 1. 问题与学习目标

受限主问题（restricted master problem，RMP）优化的是调用者当前已提供的列集合。
当我们从少量列开始，再显式加入一列时，需要确保目标方向、行乘数和约化成本均在
同一数学坐标中解释，还要保留可能重新变得独立的约束行。

本篇建立一个透明的参考接口：使用既有最大化LP内核求解最小化RMP，每次完整重建、
冷启动并核验最优候选。读者应能手算取反关系，判断新列的符号，识别行依赖复活，
并区分当前列集合最优与完整主问题最优。

## 2. 前置知识、符号与假设

先掌握[L0001](../L0001-lp-duality/README.md)的对偶、约化成本、原模型核验与
有限精度边界。设固定原始行集合为J，当前列集合为S，模型为

\[
P_S=\min_{\lambda\ge0}\ c_0+\sum_{p\in S}c_p\lambda_p,
\qquad \sum_{p\in S}a_{ip}\lambda_p\ \bowtie_i\ b_i,\quad i\in J.
\]

\(\bowtie_i\) 可为LE/GE/EQ，行名、顺序、方向和RHS固定；列通过名字区分。
变量连续、下界精确为0、上界正无穷，所有输入数值有限。\(\pi_i\) 是最小化原始行乘数，
\(\bar c_p=c_p-a_p^\top\pi\) 是最小化约化成本，\(D_S=c_0+b^\top\pi\) 是当前RMP的
对偶下界。输入列应由调用者显式给出；接口也允许先观察受限不可行，再手动补列。

原生LP自己的Phase I用于解当前模型，不提供面向完整列空间的初始列生成或可行性定价。
本篇没有自动定价、CG循环、暖启动或增量状态复用。

## 3. 手算例子

### 3.1 非零常数与三种新列成本

初始RMP为

\[
\min\ 7+4\lambda_a+6\lambda_b,\qquad
a:\lambda_a=1,\quad b:\lambda_b=1.
\]

原解为\((1,1)\)，目标17。取\(\pi=(4,6)\)，两个约化成本为零，对偶目标
\(7+4+6=17\)。交给内核的最大化目标为\(-7-4\lambda_a-6\lambda_b\)，
最优值-17，原始行乘数\(y=(-4,-6)\)。常数在两个目标中各出现一次。

新列p的系数为\((1,1)\)、成本为k。相对同一个初始对偶，
\(\bar c_p=k-10\)，取反模型中的约化成本为\(10-k\)。
令\(t=\lambda_p\)，由两行可得\(\lambda_a=\lambda_b=1-t\)、\(0\le t\le1\)，故

\[
P(t)=17+(k-10)t.
\]

| 从同一个初始RMP加入 | 旧最小化约化成本 | 旧最大化约化成本 | 新最优值 |
|---|---|---|---|
| k=7 | -3 | 3 | 14，t=1 |
| k=10 | 0 | 0 | 17，任意可行t均最优 |
| k=12 | 2 | -2 | 17，t=0 |

k=7后的最优对偶可不唯一，只需满足当前三列的对偶关系并达到14。
这三行表格是三个独立实验；先加入成本7列后，成本10列相对新对偶的约化成本需要重新计算。

### 3.2 加列会使冗余行复活

初始仅有x，成本2，行a:x=1、b:x=1。两行对当前列重复，最优x=1、目标2。
现在显式加成本0的q，系数\((1,0)\)，完整模型成为

\[
a:x+q=1,\qquad b:x=1.
\]

新解仍为x=1、q=0、目标2，两行已经独立。如果永久删除旧冗余行b，错误模型会取
x=0、q=1、目标0。q系数\((0,1)\)时同理，因此每次求解都要从完整原始行重建。

旧对偶可以取\((2,0)\)。对q=(1,0)，旧约化成本为-2，但新增后目标仍为2。
原因是旧对偶不再满足q的列约束，新的合法最优对偶可取\((0,2)\)；当前原始解也退化。
负约化成本给出旧对偶失效的信息，不保证退化问题每次增列都有严格目标改善。

## 4. 原理推导与正确性依据

### 4.1 最小化弱对偶与行符号

对LE行，为使\(\pi_i a_i^\top\lambda\ge\pi_i b_i\)，应取\(\pi_i\le0\)；
对GE行应取\(\pi_i\ge0\)，EQ行自由。若所有当前列满足\(\bar c=c-A^\top\pi\ge0\)，则

\[
c_0+c^\top\lambda
=c_0+\pi^\top A\lambda+\bar c^\top\lambda
\ge c_0+b^\top\pi=D_S.
\]

这给出当前列集合的下界。原始可行点与对偶可行乘数达到相同目标时，该RMP最优。
相应互补关系为\(\lambda_p\bar c_p=0\)、\(\pi_i(b_i-a_i^\top\lambda)=0\)。
使用这些关系前仍须检查可行性、行符号和约化成本一致性。

### 4.2 整个目标取反，行坐标保持原样

内部模型最大化\(-c_0-c^\top\lambda\)。若内核已在原始行坐标给出y、r，则

\[
P_S=-P_{\max},\qquad \pi=-y,\qquad
\bar c=c-A^\top\pi=-(-c-A^\top y)=-r.
\]

内核已撤销负RHS归一化，适配层无需再翻转相应行。唯一额外转换来自目标方向。
在不改变行、变量的条件下，这些等式把原生最大化的可行最优见证映射为最小化见证。
全局`Solution`的约定保持最大化，RMP使用独立结果类型承载最小化语义。

### 4.3 当前列集合与完整列集合

设完整合法列集合为U，S为其子集。RMP可行解令其他列为0，就得到完整问题的可行解，
所以最小化时\(P_U\le P_S\)。当前RMP的最优值提供完整问题的一个可达到上界；
当前乘数只检查S的列约束，未必对U提供合法下界。

若能证明所有未生成合法列也满足\(c_p-a_p^\top\pi\ge0\)，则同一乘数对完整问题
对偶可行，与当前原解共同给出完整LP最优性。这是后续完整定价应承担的证明义务。
受限不可行时，补列可能扩大可行集，故不能由当前状态直接推断完整问题不可行。

## 5. 算法到代码的映射

| 数学/状态工作 | 代码职责 |
|---|---|
| 拥有完整最小化RMP | [restricted_master.py](../../../src/silo/decomposition/restricted_master.py)：构造器、`_copy_model` |
| 显式原子加列 | `add_column`：先校验名称/成本/行，再构造候选模型并替换 |
| 全部行冷重建与整体取反 | `solve`：为后端和核验分别创建完整模型，不复用旧基或删行集 |
| 原生最优依据核验 | [optimality.py](../../../src/silo/lp/optimality.py)：`check_lp_optimality`，既有容差1e-9 |
| 最小化字段转换与快照 | `RestrictedMasterResult`：独立冻结记录、复制后的只读映射 |

持久模型保留原始行，既有LP可以在本次求解内部删除冗余行；它的标准形和basis不被RMP
保存。当前矩阵的行依赖在加列后可能失效，这是本次选择完整冷重建的正确性理由。

构造器复制Model的变量/行列表、行系数字典和目标字典；变量与Bounds是已有冻结对象。
增列时复制映射，失败不会留下半个变量。结果映射支持`result.dual_values["a"]`，
需要普通字典可用`dict(result.dual_values)`；修改映射会抛出`TypeError`。
同名变量拒绝，零列和异名同向量合法；非空白名字保持原字符串，不静默改名。

## 6. 核验与复现

从项目根目录、现有环境运行下例：

```python
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition import RestrictedMasterProblem

model = Model(
    variables=[Variable("la"), Variable("lb")],
    constraints=[Constraint("a", {"la": 1}, ConstraintSense.EQ, 1),
                 Constraint("b", {"lb": 1}, ConstraintSense.EQ, 1)],
    objective=Objective({"la": 4, "lb": 6}, OptimizationSense.MINIMIZE, constant=7),
)
rmp = RestrictedMasterProblem(model)
before = rmp.solve()
assert before.status == SolverStatus.OPTIMAL
assert before.objective_value == 17
assert before.dual_values == {"a": 4, "b": 6}
assert 7 - before.dual_values["a"] - before.dual_values["b"] == -3
rmp.add_column(name="p", cost=7, row_coefficients={"a": 1, "b": 1})
after = rmp.solve()
assert after.status == SolverStatus.OPTIMAL
assert after.primal_values == {"la": 0, "lb": 0, "p": 1}
assert after.objective_value == 14
assert 7 + sum(after.dual_values.values()) == 14
assert all(rc >= -1e-9 for rc in after.reduced_costs.values())
assert before.primal_values == {"la": 1, "lb": 1}  # 历史快照保留原坐标。
assert model.variable_names() == ["la", "lb"]  # 输入未被加列改变。
```

可显式调用`rmp.solve(TableauSimplexSolver())`核对另一后端。每个最优候选都先在
完整取反模型上核验，成功才发布最小化字段；非最优结果目标为None、映射为空。
只读结果不承担后端求解日志或标准形缓存的角色。

[接口测试](../../../tests/unit/test_restricted_master.py)检查所有权、原子性、快照、
符号转换与失败注入；[解析核验](../../../tests/verification/test_restricted_master_oracles.py)
直接在原始最小化模型上核对行符号、约化成本、互补、原始/对偶目标，并用A/B/C手算真值。
两套后端之间的相同结果只作补充，不能代替解析真值。

```powershell
python -m pytest tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py -q
```

实际运行范围、完整质量检查、教学核对与代码提交见
[执行报告](../../../tasks/reports/20261019-02-01_restricted-master_report.md)。元信息的
`verified_code`应定位真实包含本接口的实现提交。

## 7. 研究意义与可扩展问题

已有能力是求解当前列集合、提取最小化行乘数、显式增列并重新核验。它为后续精确定价
与CG循环提供参考接口，属于基础设施；本次没有提出新算法或证明性能优势。

后续精确定价必须接收同一行坐标的乘数、覆盖规定列域，并用完整枚举等独立真值核对。
只有形成正确的定价与终止依据后，才能讨论整个CG闭环。是否值得热启动、增量维护
或机器学习辅助，还需要单独的正确性和总成本证据。

## 8. 局限、反例与失效条件

支持普通非负连续变量；一般上下界、自由/固定/整数变量明确拒绝。没有自动初始列、
可行性定价、presolve、暖启动、旧基或乘数缓存，也不拥有完整列集合或自动终止判断。

非最优状态保留为原生后端诊断，不附独立不可行性或无界射线。已知既有数值债为
\(x-(1+5\times10^{-10})z=10^{10}\)、\(x-z=10^{10}\)，目标max z。
精确等式迫使z=0，但第1步审查在旧版及当前revised均观察过UNBOUNDED。
本接口若将目标改为min(-z)，仍可能转发相应诊断；最优候选核验不验证非最优状态。
这项已复现边界来自第1步审查及[本合同](../../../tasks/codex/20261019-02-01_restricted-master.md)，
本步未修复或声称重建了LP数值策略。

绝对容差核验只提供有限精度依据。原生内核通过核验的OPTIMAL只解释为当前S上的
浮点最优，完整主问题仍需定价证据。输入/结果快照解决数据所有权，不意味着多个线程
可以并发修改同一个RMP对象；本实现按顺序调用。

## 9. 练习与解答入口

完成[四道分层练习](exercises.md)，再查看[完整解答](solutions.md)。题目依次对应
符号/常数、混合行、行依赖复活与退化、受限问题的最优性及可行性边界。

## 10. 开发来源与修订记录

| 来源 | 路径/身份 | 作用 |
|---|---|---|
| 本次原子合同 | [第2步](../../../tasks/codex/20261019-02-01_restricted-master.md) | 新适配层、真值与允许范围 |
| 实际执行报告 | [实现/教学核验](../../../tasks/reports/20261019-02-01_restricted-master_report.md) | 命令、结果、提交与剩余限制 |
| 对偶基础 | [L0001](../L0001-lp-duality/README.md) | 原始坐标、最大化见证和有限精度边界 |
| 代码基线 | 篇首verified_code | 使用`git show <verified_code>:src/silo/decomposition/restricted_master.py`回看 |

| 日期 | 讲解版本 | 修订 |
|---|---|---|
| 2026-10-19 | 0.1.0 | 创建最小RMP讲解、原始行复活反例、API映射和E01–E04 |
