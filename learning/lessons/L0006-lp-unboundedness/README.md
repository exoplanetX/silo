---
lesson_id: L0006
title: LP无界判定：可行点、改善方向与数值核验
topic: lp.unboundedness
version: 0.1.0
status: checked
created: 2026-10-20
updated: 2026-10-20
verified_code: c460aa78c2abc489839a0da2411b9bd1bca95983
verified_on: 2026-10-20
source_tasks:
  - 20261020-01-01_lp-unbounded-check
---

# L0006｜LP无界判定：可行点、改善方向与数值核验

## 1. 问题与学习目标

LP 返回无界意味着原始可行域中存在目标任意好的可行解。单纯形中“有改善进入列、
无可选离基行”给出内部候选；发布结论前还需要原模型可行点与改善方向。
本篇说明两部分依据怎样构成充分条件，以及微小残差为何足以破坏无界判断。

开发背景是两个后端都把近相关等式下的有限模型误报无界。第7步仅加强终止候选
核验，正常迭代仍按原有浮点规则运行。先读
[L0001](../L0001-lp-duality/README.md) 的原始行与负 RHS 约定；上层接口见
[L0002](../L0002-restricted-master/README.md)、
[L0004](../L0004-column-generation/README.md)、
[L0005](../L0005-cg-feasibility/README.md)。

## 2. 前置知识、符号与假设

模型为 max c0+cᵀx，行方向属于 LE/GE/EQ，变量连续、无有限上界，既有支持域的
下界为零或既有容差内近零值。候选核验仍逐项使用实际原始下界 l。

| 符号 | 含义 |
|---|---|
| x0 | 完整原变量坐标中的有限候选点 |
| d | 同一原坐标中的候选方向（ray direction） |
| t | 任意非负实数，无上界 |
| B | 终止轮当前基矩阵，与原始行身份分别管理 |
| aᵢ、bᵢ | 原始输入的第 i 行与 RHS，包含已删行 |

原始数据按实际数值解释：Python int 保留原整数，float 表示实际二进制有理值。
例如 float 0.1 与精确十进制 1/10 有差别。`Fraction(value)` 在乘法前转换；
`Fraction(str(value))`、先算浮点点积、分母截断都改变待核验对象。

## 3. 手算例子

先看 x-z=2、x,z>=0、max z+5。取 x0=(2,0)、d=(1,1)，得到
x(t)=(2+t,t)，等式保持、变量非负，目标 5+t 趋向正无穷。

主反例为 x-(1+δ)z=10¹⁰、x-z=10¹⁰、max z，其中实际 δ=float(1+5e-10)-1>0。
两行相减给 δz=0，故 z=0、x=10¹⁰，最优值零。原序运行时两个后端 Phase I 后
保留第一行，终止候选为 x0=(10¹⁰,0)、d=(1+δ,1)。第一行方向残差为零，
被删的第二行方向残差为 δ=281475/562949953421312。它虽然小于 1e-9，
但 x(t) 在第二行的残差为 tδ，对任意 t 的可行性已经失败。
手设 d=(1,1) 则违反第一行；核验必须观察后端实际候选。

小系数对照：epsilon*z<=b、epsilon>0、b>=0 给 z<=b/epsilon；
-epsilon*z<=b 允许 z=t 的改善方向。系数大小相同，符号决定不同几何结构。

## 4. 原理推导与正确性依据

候选充分条件为

\[
x^0\ge l,\quad A_{LE}x^0\le b_{LE},\quad
A_{GE}x^0\ge b_{GE},\quad A_{EQ}x^0=b_{EQ},
\]

\[
d\ge0,\quad A_{LE}d\le0,\quad A_{GE}d\ge0,\quad
A_{EQ}d=0,\quad c^\top d>0.
\]

证明：对 LE 行，aᵢᵀ(x0+td)=aᵢᵀx0+t·aᵢᵀd<=bᵢ；GE 行用相反方向，EQ
行用零斜率。变量界由 x0>=l 与 d>=0 保持。目标为
c0+cᵀx0+t·cᵀd，严格正斜率保证任意大的目标值。常数只平移目标。

可行点与方向承担不同证明义务。x=1、x=2、max z 有方向 d=(0,1)，可行域却为空；
方向不能补足点的缺失。对于所有 t>=0 的断言，固定绝对残差阈值不足：任何非零
等式方向残差乘以 t 都会放大。二进制幂缩放在本篇有限范围内可保留精确数值关系，
随意浮点缩放可能再次舍入，不能直接推定候选仍精确可行。

当前标准形候选令 d_enter=1、d_basic=-B⁻¹A_enter，其余非基为零；点令非基为零，
基坐标为 B⁻¹b。Tableau 已存储这些变换行，直接取当前 RHS 和进入列；Revised
在终止处重解当前基得到未清零结果。进入列必须有效且非基，结构列与原变量分别投影。
这些浮点构造只产生候选，仍需上面完整原行的独立条件。

Phase I 最大化 -sum(人工变量)，其值向上不超过零。Phase-I 内部无界与此界矛盾，
只能形成数值诊断；原目标的无界结论必须来自 Phase II。

## 5. 算法到代码的映射

| 数学对象/步骤 | 代码位置 |
|---|---|
| 原模型 x0、d 与逐项精确判号 | [unboundedness.py](../../../src/silo/lp/unboundedness.py) 的 check_lp_unboundedness |
| 原始 Tableau RHS、进入列与原变量前缀投影 | [tableau.py](../../../src/silo/lp/simplex/tableau.py) 的 _unbounded_solution |
| 当前基原始重解、original role/name 投影 | [revised.py](../../../src/silo/lp/simplex/revised.py) 的 _unbounded_solution |
| 保留实际进入列 | 两模块内部 run 记录的 entering_column 默认字段 |
| 原始证据失败 | NUMERICAL_ISSUE，公开非最优字段为空 |

源文件链接从篇目目录向上三级进入项目根目录。
检查前不调用 `_clean_zero`，不夹成非负，不修复方向，也不增加一次可行性 LP。
Revised 的公开详情结构保持原有字段，compatible warm-start 入口使用同一个终止门控。

## 6. 核验与复现

在项目根目录，用 `.venv/Scripts/python.exe` 运行以下完整程序。它只调用公开后端。

```python
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S, OptimizationSense as O
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus as T
from silo.core.variable import Variable
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

def make(name, rows):
    return Model(name, [Variable('x'), Variable('z')], rows,
                 Objective({'z': 1}, O.MAXIMIZE, 5))

cases = [
    (make('literal', [
        Constraint('a', {'x': 1, 'z': -(1+5e-10)}, S.EQ, 1e10),
        Constraint('b', {'x': 1, 'z': -1}, S.EQ, 1e10)]), T.NUMERICAL_ISSUE),
    (make('coupled', [Constraint('lo', {'x': -1, 'z': 1}, S.LE, -1)]), T.UNBOUNDED),
    (make('empty', []), T.UNBOUNDED),
    (make('tiny-positive', [Constraint('b', {'z': 2**-32}, S.LE, 1)]), T.NUMERICAL_ISSUE),
    (make('tiny-negative', [Constraint('b', {'z': -2**-32}, S.LE, 1)]), T.UNBOUNDED),
    (make('large-positive', [Constraint('b', {'z': 2**-24}, S.LE, 1)]), T.OPTIMAL),
    (make('third', [Constraint('fixed', {'x': 3}, S.EQ, 1)]), T.NUMERICAL_ISSUE),
    (make('near-contradiction', [Constraint('a', {'x': 1}, S.EQ, 1),
        Constraint('b', {'x': 1}, S.EQ, 1+2**-40)]), T.NUMERICAL_ISSUE),
]
for backend in (TableauSimplexSolver, RevisedSimplexSolver):
    for problem, expected in cases:
        result = backend().solve(problem)
        assert result.status == expected, (backend.__name__, problem.name, result)
        if expected == T.OPTIMAL:
            assert result.objective_value == 5 + 2**24
            assert check_lp_optimality(problem, result, tolerance=1e-9).passed
        else:
            assert result.objective_value is None
            assert not any((result.primal_values, result.slack_values,
                result.dual_values, result.reduced_costs, result.basis_status))
        print(backend.__name__, problem.name, result.status.value)
```

对应 [固定族原项 oracle](../../../tests/verification/test_lp_unboundedness_oracles.py)
与 [单元/注入测试](../../../tests/unit/test_lp_unboundedness.py) 分开管理。
原项 oracle 根据原始等式解析分类，并观察实际送给 guard 的 Model/x0/d；
对公开无界结果逐项先转 Fraction 后检查，不调用生产核验器给出真值。
240 核心族与32对照共272次实测：100最优、60真无界、108数值诊断、4不可行。
原100个正常最优路径全部保留，原108个误无界改为数值诊断。新增测试398项，
全量3444项与Ruff通过；正文16次双后端教学运行和解答标量程序通过，详见报告。

## 7. 研究意义与可扩展问题

已有能力是给两个原生 LP 的无界出口增加可核对的充分依据。它提高 RMP、CG、
可行性恢复与 MIP 消费底层状态时的可信度，为后续效率比较固定正确基线。
成熟基础核验机制的正确实现本身不自动构成论文贡献。

后续研究可明确候选构造的成功率、额外检查成本与不同数值尺度的关系；实际求解
改进仍需要模型族、失败分类和独立真值。热启动、稀疏基维护、精确求解与高维性能
各自需要单独任务和证据，本篇没有验证这些能力。

## 8. 局限、反例与失效条件

3*x=1、max z 的精确可行域非空且无界；有限二进制浮点数无法等于 1/3。
因此当前点即使很接近可行，也可能被精确条件拒绝。返回 NUMERICAL_ISSUE 表示
当前候选依据不足，不能据此改判有界或不可行。这是充分条件的保守成功范围。

本实现只做有限数值候选的精确标量核验，不做有理逆、精确枢轴、十进制意图恢复
或方向修复。正常枢轴/清零/冗余处理仍使用既有规则，原始核验负责拒绝其不合法
终止候选。它没有认证全部最优/不可行终态，也未统一 presolve 的独立终态、外部/
替身后端或 MIP 的整数可行性依据；上层边界仍需各自检查。

## 9. 练习与解答入口

[六道练习](exercises.md) 覆盖充分条件、微小残差、内部坐标、数值表示、空可行域
与上层传播。[完整解答](solutions.md) 给出推导、判据与可运行标量核对。
稳定编号 L0006-E01–E06；核验记录见下一节与任务报告。

## 10. 开发来源与修订记录

| 来源 | 作用 |
|---|---|
| [第7步合同](../../../tasks/codex/20261020-01-01_lp-unbounded-check.md) | 单个正确性目标、范围、272族、保守边界与教学要求 |
| [执行报告](../../../tasks/reports/20261020-01-01_lp-unbounded-check_report.md) | 实际旧/新状态、代码提交、命令结果和Git证明 |
| L0001、L0002、L0004、L0005 | 原始行约定、最小化适配与上层数值诊断的已有边界 |

2026-10-20 v0.1.0：按篇首实际实现提交核对；十节、六题/解答、完整程序及链接检查通过。
