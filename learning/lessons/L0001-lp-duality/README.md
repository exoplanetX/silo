---
lesson_id: L0001
title: LP 对偶约定与最优性核验
topic: lp.duality
version: 0.2.0
status: checked
created: 2026-10-18
updated: 2026-10-19
verified_code: ad62e0f9dda749e5db8d6ca27749c41fc8f14045
verified_on: 2026-10-19
source_tasks:
  - 20261018-01-02_lp-dual-optimality
  - 20261018-02-01_learning-series
  - 20261019-01-01_revised-phase1-cleanup
---

# L0001｜LP 对偶约定与最优性核验

[系列入口](../../README.md) · [总目录](../../CATALOG.md) ·
[当前接口参考](../../../docs/lp_duality.md)

## 1. 问题与学习目标

单纯形返回一个目标值后，我们还需要判断：这个值是否来自可行点？是否存在
更好的解？原始可行解给出可达到的目标值，对偶可行解给出上界；两者相等时，
形成最优性依据。这是本篇从求解结果走向独立核验的主线。

读完本篇，应能手算一个简单 LP 的对偶值，解释负 RHS 变号的影响，推导固定
变量的对偶目标修正，并定位 SILO 中的提取与核验代码。算法代码来自已有
tableau/revised 后端；这一篇把开发成果整理为可重复学习的材料。

## 2. 前置知识、符号与假设

需要已掌握：线性约束与可行解、矩阵乘法、独立列与基矩阵、线性方程组。
本篇自带对偶推导；尚不熟悉单纯形枢轴的读者可先完成手算和核验，再读代码。

当前原模型是连续最大化问题：

\[
P(x)=c_0+c^\top x,\qquad x_j\ge0,
\]

约束行可为 \(a_i^\top x\le b_i\)、\(a_i^\top x\ge b_i\) 或等式。
普通变量没有有限上界；已有 presolve 还支持代入精确固定坐标 \(x_j=v_j\)。

| 记号 | 含义 |
|---|---|
| \(A,b,c,c_0\) | 输入原模型的约束矩阵、RHS、目标系数和目标常数 |
| \(y\) | 原始约束行的对偶值（dual value / row multiplier） |
| \(r=c-A^\top y\) | 原始变量的约化成本（reduced cost） |
| \(B,c_B\) | 当前基矩阵与基变量的 Phase II 成本 |
| \(T\) | tableau 当前行相对于输入原始行的线性组合 |
| \(F\) | 精确固定变量集合；这些坐标的 \(r_j\) 无符号限制 |

当前 API 不直接求解最小化、自由变量或一般有限上下界 LP。本篇第 7 节的
最小化关系只用于数学方向转换，不表示已经新增求解能力。

## 3. 手算例子

### 3.1 一个约束的最优性依据

\[
\max\ 2x+7,\qquad x\le3,\quad x\ge0.
\]

最优原始解是 \(x=3\)，目标值 \(2\cdot3+7=13\)。取行乘数 \(y=2\)，
得到 \(r=2-1\cdot2=0\)，对偶目标 \(7+3\cdot2=13\)。
任何可行 \(x\) 都有 \(2x+7\le13\)，而 \(x=3\) 达到它，故最优性成立。

同一约束写为 \(-x\ge-3\) 时，原始行乘数应为 \(-2\)。内部变号可以把
两种形式转换成同一个计算问题，返回结果仍须对应用户输入的原行方向。
常数 7 在两侧各计入一次，不参与 \(B^\top y=c_B\) 的计算。

在最优基保持可行的局部 RHS 变化范围内，乘数还给出目标变化率。换基和退化
会影响这一解释的适用范围，不能仅凭一个乘数承诺全局敏感性结论。

### 3.2 人工变量来自哪一行，当前位于哪个基位置

考虑 \(\max x+z\)，原始等式依次为 \(a:x=1\)、\(b:z=2\)、\(c:z=2\)，
变量非负。标准列依次为 \((x,z,u_a,u_b,u_c)\)，人工列 \(u_b=e_b\)。
提供基列 \((u_b,x,z)\)，即旧列号 `(3,0,1)`。按原始行顺序写出：

\[
C=\begin{bmatrix}1&0\\0&1\\0&1\end{bmatrix},\quad
b=\begin{bmatrix}1\\2\\2\end{bmatrix},\quad
B=\begin{bmatrix}0&1&0\\1&0&1\\0&0&1\end{bmatrix},\quad
B^{-1}b=\begin{bmatrix}0\\1\\2\end{bmatrix}.
\]

这是可逆、原始可行的 Phase-I 基，人工基本值为零。其基位置 `0` 对应 \(u_b\)，
而 \(u_b\) 的来源为原始行 `b`（原始行号 `1`）。这两个下标各有自己的坐标。
变换行 \(q^\top=(0,1,-1)\) 给出 \(q^\top C=0\)、\(q^\top b=0\)，
即行 \(b\) 可由行 \(c\) 恢复。

正确操作是删除原始行 `b`、删除基位置 `0`，并删除全部人工列。于是

\[
C_{\{a,c\},:}=\begin{bmatrix}1&0\\0&1\end{bmatrix},\qquad
b_{\{a,c\}}=\begin{bmatrix}1\\2\end{bmatrix}.
\]

剩余基列的旧号 `(0,1)` 映射为新号 `(0,1)`，得 \(x=1,z=2\)、目标 3。
原始三行乘数可取 \((y_a,y_b,y_c)=(1,0,1)\)，约化成本为零，
\(b^\top y=1+0+2=3\)。加目标常数 7 时，两个目标都变为 10。
若误删原始行 `a`，剩余矩阵为 \(\left[\begin{smallmatrix}0&1\\0&1\end{smallmatrix}\right]\)，
基即奇异。这个构造核对的是清理函数的有效输入；当前 cold-solve 是否能到达该基
仍是独立问题，见第 8 节。

## 4. 原理推导与正确性依据

### 4.1 对偶符号与上界

为了让逐行相乘后都满足 \(y_i a_i^\top x\le y_i b_i\)，需要：

| 原始行 | 乘数条件 |
|---|---|
| `<=` | \(y_i\ge0\) |
| `>=` | \(y_i\le0\) |
| `=` | 无符号限制 |

对普通非负变量，另要求 \(r=c-A^\top y\le0\)。于是

\[
c_0+c^\top x
=c_0+y^\top Ax+r^\top x
\le c_0+b^\top y=D(y).
\]

这是当前模型的弱对偶推导。若原始与对偶都可行，且 \(P(x)=D(y)\)，这个
可达到值同时等于所有可行目标的上界，故两个解最优。该结论不依赖某个后端
是否给它标记了 `OPTIMAL`。

### 4.2 互补松弛

最优时还核对 \(y_i(b_i-a_i^\top x)=0\) 和普通坐标的 \(x_jr_j=0\)。
行方向只影响余量符号，乘积是否为零不受它影响；等式行由原始可行性使残差为零。
实现使用乘积的绝对值。目标相等和互补条件都应建立在可行性与符号检查之上。

### 4.3 固定变量为什么需要补一项

若 \(j\in F\) 满足 \(x_j=v_j\)，则 \(r_jx_j=r_jv_j\) 是一个已知项，
不需要 \(r_j\le0\)。相应上界为

\[
D(y,r)=c_0+b^\top y+\sum_{j\in F}r_jv_j.
\]

这也可由 presolve 代入直接得到：

\[
c_0+c_F^\top v+(b-A_Fv)^\top y
=c_0+b^\top y+(c_F-A_F^\top y)^\top v.
\]

例：\(\max 5f+2x+7\)，\(f+x\le3\)，\(f=2\)，\(x\ge0\)。
取 \(x=1,y=2\)，则 \(r_f=3,r_x=0\)，原始目标为 19；对偶目标为
\(7+3\cdot2+3\cdot2=19\)。遗漏固定界项会错误得到 13。
精确固定的有限负值同样满足这个代数关系。

### 4.4 来源行删除为什么同时保持行依赖与可逆基

令 \(C\) 包含全部非人工标准形列（含松弛/剩余列），\(B\) 是清理换出后仍
可逆的基。按同一匹配次序，\(I=(i_1,\ldots,i_s)\) 为残留人工基的位置，
\(K=(k_1,\ldots,k_s)\) 为对应人工单位列的来源行，且 \(B_{:,i_t}=e_{k_t}\)。
这些来源应互异。定义 \(Q=(B^{-1})_{I,:}\)，则 \(Q_{:,K}=\mathrm{Id}_s\)。
残留人工值为零给出 \(Qb=0\)；无法用非人工列换出给出 \(QC=0\)。
非人工基本列在 \(B^{-1}B\) 中对应其他位置，因此也满足这个零条件。

写 \(R=K^c\)，有

\[
C_K=-Q_{:,R}C_R,\qquad b_K=-Q_{:,R}b_R.
\]

故任一满足保留等式 \(C_Rw=b_R\) 的非人工变量向量，也满足被删等式。
反向蕴含显然成立，变量域不变，因此精确可行集相同。

可逆性来自另一项结构：把行按 \((K,R)\)、基列按 \((I,I^c)\) 重排后，

\[
B\sim\begin{bmatrix}\mathrm{Id}_s&H\\0&D\end{bmatrix},\qquad D=B_{K^c,I^c}.
\]

\(B\) 可逆直接推出 \(D\) 可逆。这里删除的是行集合 \(K\) 和基位置集合 \(I\)，
两者无需相等。保留问题的最优对偶在 \(K\) 上补零，不改变各列的对偶关系或
对偶目标；原始负 RHS 行的符号恢复也不改变零乘数。

以上是精确算术结论。实现解 \(B^\top Q^\top=E_I\) 而不显式构造逆矩阵，
用既有 `1e-9` 绝对容差核对三个关系并实际求解剩余基。局部小残差可能被较大
变量值放大，故发生删行时，最终候选还须通过第 6 节的原模型最优性核验。

## 5. 算法到代码的映射

| 数学工作 | 代码与职责 |
|---|---|
| Tableau 的行变换与 \(c_B^\top T\) | [tableau.py](../../../src/silo/lp/simplex/tableau.py)：`row_origins`、`pivot`、`_original_dual_values` |
| Revised 的 \(B^{-\top}c_B\) | [revised.py](../../../src/silo/lp/simplex/revised.py)：`_compute_basis_state`、`_original_dual_values` |
| 人工列来源、行依赖与三套索引 | `revised.py`：`_artificial_source_rows`、`_check_cleanup_dependence`、`_remove_artificial_columns` |
| 原模型结果恢复 | [presolver.py](../../../src/silo/presolve/presolver.py)：`PresolveResult.recover_solution` |
| 独立原模型核验 | [optimality.py](../../../src/silo/lp/optimality.py)：`check_lp_optimality` |
| 双后端比较 | [compare.py](../../../src/silo/cli/compare.py)：分别核验每一组候选解 |

Tableau 初始化 \(T\) 时记入负 RHS 变号；每次枢轴同步更新行与 \(T\)，
Phase I 删除冗余变换行时也删除对应映射行。最终用 Phase II 成本计算乘数，
结构列的成本为零。这个透明实现额外使用 \(O(m^2)\) 的稠密行映射存储。

Revised 已在计算约化成本时求解 \(B^\top y'=c_B\)。保留最终乘数，按剩余
标准化原始行的名字映射，撤销 RHS 变号；删除的冗余等式行取零乘数。
暖启动读取最终基的 Phase II 乘数，避免混入辅助问题的目标。

清理中的 `kept_rows` 选择原始标准化行，`kept_basis_slots` 选择剩余基位置，
`kept_columns` 及 `column_map` 删除人工列并重新编号。人工来源复用
[StandardColumn.source_constraint](../../../src/silo/lp/simplex/standard_form.py)，
不根据人工列名猜来源。来源缺失、歧义、非单位列、局部依赖检查失败或剩余基求解
失败时返回 `NUMERICAL_ISSUE`。`_optimal_solution` 在实际删行后用原模型核验最终候选，
失败时返回同一保守状态，并清空候选最优解和对偶字段。

Presolve 对可行空行补零乘数，对保留行沿用其名字与方向，再根据原始 \(A,c,y\)
重算约化成本。固定坐标保留 `basis_status="fixed"`；恢复的 \(r_j\) 可以非零。
很小的 \(y_i\) 或固定 \(r_j\) 也不按显示阈值清零，因为 \(y_i b_i\) 或
\(r_jv_j\) 可能仍有显著贡献。

## 6. 核验与复现

在项目根目录、已安装 SILO 的 Python 环境中运行：

```python
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.presolve import Presolver

model = Model(
    variables=[Variable("x")],
    constraints=[Constraint("capacity", {"x": 1}, ConstraintSense.LE, 3)],
    objective=Objective({"x": 2}, OptimizationSense.MAXIMIZE, constant=7),
)
reduction = Presolver().run(model)
solution = reduction.recover_solution(TableauSimplexSolver().solve(reduction.model))
check = check_lp_optimality(model, solution)
assert check.passed, check
assert solution.dual_values == {"capacity": 2.0}
assert check.primal_objective == check.dual_objective == 13
```

把求解器换成 `RevisedSimplexSolver` 可核对第二个后端。对预处理结果，必须
用原模型和恢复后的解进行核验。核验器不求解模型，不复用单纯形内部的可行性函数，
也不信任报告中的余量或基状态；它重新计算行活动、约化成本和目标。

默认绝对容差为 `1e-7`。五类残差分别描述原始可行性、对偶可行性、约化成本
一致性、报告/原始/对偶目标两两差异，以及互补松弛。缺少坐标、非有限数值、
非最优状态或不支持的模型域会明确失败。返回字段与当前行为见
[接口参考](../../../docs/lp_duality.md)。

对应测试为 [符号与恢复](../../../tests/unit/test_lp_duality.py)、
[Phase-I 清理](../../../tests/unit/test_revised_phase_one_cleanup.py)、
[核验器错误控制](../../../tests/unit/test_lp_optimality.py) 和
[独立解析/外部参照](../../../tests/verification/test_dual_oracles.py)。
可执行以下针对性检查：

```powershell
python -m pytest tests/unit/test_revised_phase_one_cleanup.py tests/unit/test_lp_duality.py tests/unit/test_lp_optimality.py tests/verification/test_dual_oracles.py -q
```

可选外部参照依赖 SciPy；缺失时跳过对应测试，解析与内部核验继续执行。

本篇 v0.1.0 的教学核对与 v0.2.0 的清理修复分别有执行报告，见第 10 节。
新版本的示例、习题、代码提交与实际检查以该修复报告和顶部元信息为准。

## 7. 研究意义与可扩展问题

当前能力让候选结果可以在原模型中核查，也为反复求解主问题提供行乘数。
这是基础设施价值；标准对偶关系的实现本身不构成新算法贡献。
来源清理修正使给定合法 Phase-I 基能够保留可逆的剩余基，为对偶恢复及未来反复
求解主问题提供更稳健的基础；本修复不主张新算法或性能加速。

列生成常采用最小化主问题，定价关注 \(\bar c_p=c_p-a_p^\top\pi\)。若把
同一模型的目标取反形成最大化问题，且保留同一约束行坐标，则
\(y=-\pi\)，从而

\[
r_p^{\max}=-c_p-a_p^\top y=-(c_p-a_p^\top\pi)=-\bar c_p.
\]

最小化中的负约化成本列，对应取反模型中正约化成本的改善方向。若同时变换行
或变量，还必须合并其映射。受限主问题上的核验只覆盖当前列集合；对完整主问题
作终止判断，还需要完整定价给出的相应依据。

连续对偶更新、定价状态复用和重优化可在这个接口上提出进一步问题。
它们仍需自己的状态充分性、正确性与总成本证据；本篇没有实现或验证这些机制。

## 8. 局限、反例与失效条件

- 默认绝对容差只给浮点核验结果，不能代替精确证明或一般数值稳健性保证。
- 不同最优基可给出不同最优对偶向量，应各自核验，不能强制逐坐标相等。
- 仅有“报告状态最优”或“原始/对偶目标相等”仍不充分；见练习 E04 的零差距反例。
- 当前域不包含一般有限界、自由变量、最小化直接求解或 MIP 对偶最优性。
- `solve` 返回对偶值，调用者按需调用核验器；`silo compare` 自动核验，使用现有
  `1e-9` 绝对容差。比较 JSON 的历史 `dual_values_empty` 字段仅描述是否为空。

第 3.2 节是 v0.2.0 修复的历史反例：旧清理把基位置当成原始行号，误删行后出现
奇异基。新实现分别处理来源行、基位置和列编号；原始三行模型中的解与对偶通过核验。
有界调查检查了 12 个固定 cold-solve 小例，观察到 16 个残留人工变量，来源行与
基位置均相同。该调查未确认当前枢轴路径可到达上述异位构造，也没有证明不可达。

绝对容差还有尺度边界。例如 \(x+(1+\varepsilon)z=M\)、\(x+z=M\)，
\(\max z\)，取 \(\varepsilon=5\times10^{-10}\)、\(M=10^{10}\)。
精确等式迫使 \(z=0\)。局部依赖残差虽小于 `1e-9`，删行后的候选却可能给出
约 \(z=M\)，原始行违反量约为 \(\varepsilon M=5\)。新实现的最终原模型核验
会拒绝该错误最优候选并返回 `NUMERICAL_ISSUE`；它不重新求解或承诺处理所有病态输入。
全局数值缩放、精确算术、一般界及其他状态的数值保障均需单独讨论。

## 9. 练习与解答入口

先完成 [六道分层练习](exercises.md)，再查看 [解答与核对依据](solutions.md)。
练习覆盖计算、符号变换、固定界、反例、研究接口辨析和人工来源清理。

## 10. 开发来源与修订记录

| 来源 | 记录 | 作用 |
|---|---|---|
| 算法开发任务 | [LP 对偶与核验](../../../tasks/codex/20261018-01-02_lp-dual-optimality.md) | 对偶提取和核验器的实现范围 |
| 算法执行报告 | [实现与测试依据](../../../tasks/reports/20261018-01-02_lp-dual-optimality_report.md) | 红/绿测试、独立复核及已知限制 |
| 教学整理任务 | [系列编排](../../../tasks/codex/20261018-02-01_learning-series.md) | 稳定篇号、体例与习题整理 |
| 教学整理报告 | [本次实际检查](../../../tasks/reports/20261018-02-01_learning-series_report.md) | 本篇代码例和习题核对范围 |
| 清理修复任务 | [Phase-I 来源行修正](../../../tasks/codex/20261019-01-01_revised-phase1-cleanup.md) | 三套索引、数值保护和 E06 |
| 清理修复报告 | [修复与实际核验](../../../tasks/reports/20261019-01-01_revised-phase1-cleanup_report.md) | 红/绿测试、原模型检查、有界可达性与代码基线 |

核验代码基线为顶部 `verified_code` 中的实际修复提交。链接指向当前源码；可用
`git show <verified_code>:src/silo/lp/simplex/revised.py` 查看相应版本。当前接口参考由 `docs/` 维护，后续实现
变化需显式更新本篇或注明其历史适用版本。

| 日期 | 讲解版本 | 修订 |
|---|---|---|
| 2026-10-18 | 0.1.0 | 从原对偶文档整理为首篇；增加学习目标、代码映射、研究连接及练习 |
| 2026-10-19 | 0.2.0 | 修复来源行/基位置混用；补充手算矩阵、块三角证明、数值放大边界与 E06 |
