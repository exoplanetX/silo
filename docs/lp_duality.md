# LP 对偶约定与最优性核验 / LP Duality and Optimality

本功能延续 SILO 的现有两个单纯形后端。学习目标是理解：最优原始解给出
一个可达到的目标值，对偶可行解给出一个上界，两者相等时构成最优性依据。

## 1. 原模型与符号

当前求解范围保持为连续最大化问题：

\[
P(x)=c_0+c^\top x,\qquad x_j\ge0,
\]

约束行允许 \(a_i^\top x\le b_i\)、\(a_i^\top x\ge b_i\)、等式。
普通变量没有有限上界；现有 presolve 还可以消去精确固定变量 \(x_j=v_j\)。
本任务增加结果与核验能力，不增加最小化、自由变量或一般上下界求解能力。

`Solution.dual_values` 的键是**输入原模型的约束名**，符号为：

| 原始行方向 | 对偶值 \(y_i\) | 作用 |
|---|---|---|
| `<=` | \(y_i\ge0\) | 保证 \(y_i a_i^\top x\le y_i b_i\) |
| `>=` | \(y_i\le0\) | 负乘数反转不等号，得到同一上界方向 |
| `=` | 无符号限制 | 两侧相等 |

原始约化成本（reduced cost）定义为

\[
r=c-A^\top y.
\]

对普通非负变量要求 \(r_j\le0\)。因此任意原始可行点均满足

\[
c_0+c^\top x=c_0+y^\top Ax+r^\top x\le c_0+b^\top y=D(y).
\]

**原始可行性、对偶可行性和目标相等共同给出最优性依据。**
互补松弛（complementary slackness）进一步核对每行的乘数与余量乘积为零，
以及每个普通变量的 \(x_jr_j=0\)。只检查两个目标数相等，无法排除错误符号。

## 2. 手算例子

\[
\max\ 2x+7,\qquad x\le3,\quad x\ge0.
\]

原始最优解是 \(x=3\)，目标值为 13。取行对偶值 \(y=2\)，则
\(r=2-1\cdot2=0\)，对偶目标为 \(7+3\cdot2=13\)。原始与对偶都可行，
且上下界相等，故核验通过。这里常数 7 必须计入两侧，不能遗漏或重复相加。

若约束写成 \(-x\ge-3\)，原始行对偶值应为 \(-2\)。输入形式改变后，
内部标准化问题可以相同，返回的原始行乘数符号仍必须正确恢复。
在同一最优基保持可行的局部 RHS 变化范围内，乘数也给出最优目标的变化率；
退化、换基等情形需要另行分析，不能直接承诺全局敏感性结论。

## 3. 两个后端怎样得到对偶值

- Tableau 记录当前每行相对于原始输入行的线性组合矩阵 \(T\)。负 RHS
  变号写入初始化；每次枢轴同步更新；Phase I 删除冗余变换行时同步删除对应
  映射。Phase II 用原始变量的基成本计算 \(y^\top=c_B^\top T\)。
  结构列成本为零。该透明实现增加一个稠密行映射，具有 \(O(m^2)\) 存储成本。
- Revised 已在计算约化成本时求解 \(B^\top y'=c_B\)。保留该乘数，按仍然
  存在的标准化原始行名映射，撤销 RHS 变号；被删除的冗余等式行取零乘数。
  暖启动使用最终基的 Phase II 乘数，不使用 Phase I 的辅助目标乘数。

退化问题的最优对偶值可以不唯一。核验要求每组乘数各自满足原模型条件；
两个后端返回逐坐标相等的乘数并非验收条件。
恢复行对偶值时保留其原始数值，不按绝对阈值清零：很小的 \(y_i\) 乘以
很大的 \(b_i\) 仍可能是实质性的对偶目标贡献。固定变量的恢复约化成本
同样保留原值，避免丢失 \(r_jv_j\) 项。

## 4. 预处理恢复与固定变量

现有 presolve 仅执行固定变量代入和可行空行删除。可行空行恢复为零乘数；
保留行的方向和名字不变。完整最优对偶结果恢复后，重新按原始 \(A,c,y\)
计算所有约化成本。固定变量沿用 `basis_status="fixed"`，其约化成本恢复为
\(c_j-a_{\cdot j}^\top y\)，替代旧实现统一填写的零占位值。

固定变量的约化成本没有符号限制。设固定坐标集合为 \(F\)，则对偶上界为

\[
D(y,r)=c_0+b^\top y+\sum_{j\in F}r_jv_j.
\]

例如 \(\max 5f+2x+7\)，\(f+x\le3\)，\(f=2\)，\(x\ge0\)：
取 \(x=1,y=2\)，得到 \(r_f=3,r_x=0\)，原始目标为 19；对偶目标为
\(7+3\cdot2+3\cdot2=19\)。遗漏固定界的贡献会错误得到 13。
精确固定的有限负值也适用同一代数公式。

手工构造的历史 `Solution` 若缺少保留行对偶值，presolve 保持旧恢复行为，
不会为其虚构完整对偶依据；核验器会拒绝不完整的结果。

## 5. 使用与判定

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
assert check.primal_objective == check.dual_objective == 13
```

对预处理结果应传入**原模型和恢复后的解**。核验器不求解模型，也不读取
单纯形的基或内部可行性函数。它检查：

1. 状态为 `OPTIMAL`，模型在已支持的连续域，变量/行键完整且数值有限。
2. 原始行与变量界的可行性，以及原始行对偶符号。
3. 报告约化成本与独立计算的 \(c-A^\top y\) 相符；普通变量满足非正符号。
4. 报告目标、原始目标与包含固定界贡献的对偶目标两两相符。
5. 行与普通变量的互补松弛。

返回 `LPOptimalityCheck`，包括 `passed`、五类最大残差、两个重构目标与消息。
默认使用绝对容差 `1e-7`；不合适的容差参数抛出 `ValueError`。这是浮点
核验，不是精确有理数证明，也不代表大尺度、病态或近相关模型的数值保证。
非最优结果、MIP、一般变量界等不适用证据会明确失败。

`solve` 提供对偶值，调用者可以显式核验；本任务没有在每个单纯形返回路径中
自动调用核验器。`silo compare` 在最优状态下自动核验两个后端各自的原模型
依据并比较目标值，使用现有 `DEFAULT_TOLERANCE=1e-9`。JSON 键保持不变，
历史 `dual_values_empty` 字段作为描述性诊断保留，不再要求它为真。
MIP 结果仍不暴露节点 LP 的对偶值；非最优 LP 不提供最优对偶依据。

## 6. 已知边界与学习顺序

独立数学复核确认：revised 的既有 Phase I 清理按人工变量的基位置删除
原始行。当人工变量的来源行与基位置不同，某些手工构造的基会导致清理后
基奇异。当前基求解将其归为 `NUMERICAL_ISSUE`；没有证据表明下文测试基
一定可由当前枢轴路径到达。成功产生非奇异基时，删除行集具有冗余性，
保留行乘数加删除行零乘数的恢复成立。对来源行的更稳健清理留给单独任务。

对应的代数义务：若残留人工列来自行集合 \(K\)，位于基位置集合 \(I\)，
则 \(Q=(B^{-1})_{I,:}\) 满足 \(Q_{:,K}=I\)、\(QC=0\)、\(Qb=0\)。
按来源行 \(K\) 删除可保证剩余基非奇异；按位置 \(I\) 删除时，成功条件为
\(Q_{:,I}\) 非奇异。这项既存稳健性限制不被本次对偶输出掩盖。

建议学习顺序：先手算第 2 节，再读 `optimality.py` 中的原模型核验，随后
对照 tableau 的行映射和 revised 的基转置方程，最后推导第 4 节的固定界项。
研究接口下一步需要最小化/变量界约定与可重优化的主问题；本任务不实现这些扩展。
