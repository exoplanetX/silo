---
lesson_id: L0007
title: RMP基复用、语义坐标与冷回退
topic: decomposition.rmp-reoptimization
version: 0.1.0
status: checked
created: 2026-10-20
updated: 2026-10-20
verified_code: 90b377f723f047f723949aaace87f1385f42bb74
verified_on: 2026-10-20
source_tasks:
  - 20261020-02-01_rmp-reoptimization
---

# L0007｜RMP基复用、语义坐标与冷回退

## 1. 问题与学习目标

给受限主问题显式增加列之后，旧可行基在一定条件下仍可使用。本篇推导其依据，
说明怎样识别同一列、保留完整原始行、继续Phase II，并在证据不足时一次冷回退。
目标是形成可审查的参考复用机制；当前没有运行速度提升或工业性能主张。

先读 [L0001原始行与对偶](../L0001-lp-duality/README.md)、
[L0002最小RMP](../L0002-restricted-master/README.md)、
[L0006无界门控](../L0006-lp-unboundedness/README.md)。普通solve保留cold，
本步新入口由调用者明确选择，现有CG/可行性恢复器继续原有路径。

## 2. 前置知识、符号与假设

RMP为MIN、连续非负变量、无有限上界，原始LE/GE/EQ行、成本/RHS/常数有限。
LP内部整体取反为MAX。复用适用范围为：旧求解无人工列、完整有序原始行一行未删；
固定旧变量顺序、类型/界/成本、原始行顺序/方向/RHS/旧系数、目标方向和常数，
只追加零个或多个新原变量。省略零与显式零等价，模型名不影响数学身份。

| 记号 | 含义 |
|---|---|
| A_O、A_N | 旧非人工标准形列、新加入列 |
| B=A_O[:,I] | 旧完整行基，按基槽顺序取列 |
| x_B、z | 旧基变量与新增非基原变量 |
| basis_keys | 基槽顺序的语义列键，原变量按名、结构列按角色和来源行 |
| snapshot | 冻结的完整结构身份与基身份，不含旧primal/dual/rc数组 |

完整行身份用于阻止旧投影中的行依赖被误用。基槽、列位置、原始行身份各自独立，
新增原变量会插在结构列之前，整数列号随之变化。

## 3. 手算例子

例A：conv=sumλ=1、r>=1/2，p0/p2的r=(0,2)、成本=(0,10)、c0=7。
先用p0/p2，λp2=1/4、λp0=3/4，最优9.5。加入r=1、成本4的p1，
取λp0=λp1=1/2，得到9；旧可行点仍能用，新对偶却需要重新优化。

例B：min2x，conv:x=1、cap:0x<=0。完整非人工基为x与slack_cap，点(1,0)。
加q成本0、conv/cap系数(1,1)，旧MIN乘数为(2,0)，新rc=-2；原cap强制q=0。
进入q的比率检验在cap给零步长，发生退化枢轴而目标仍为2。新乘数可为(2,-2)，
满足MIN的LE乘数非正。再加r成本-1、系数(1,0)，可取r=1，目标降为-1。
这是实际warm中2→2→-1的机制，目标未降不能判复用失败。

例C：初始仅x，a:x=1、b:x=1、成本2。受限列投影重复，cold会删一行，快照禁发。
加q成本0、系数(a:1,b:0)，完整模型仍强制x=1、q=0，目标2；新两行矩阵
[[1,1],[1,0]]满秩。若只保留a，可错误选q=1得到0。故这轮cold保留全行；
其后加r成本-1、系数(1,1)，新合格快照才允许warm到-1。

两独立EQ例：x+y=1、y=1/2、成本(0,4)、c0=7，初始9。依次加conv系数1、
balance系数1/2的q/r，成本1/0，目标为9→8→7；新标准形两个fresh人工列均可
由旧完整行非人工基替代，直接Phase II。

## 4. 原理推导与正确性依据

旧模型的标准形为 A_O x=b，B可逆且x_B=B⁻¹b>=0，其余变量非基0。
增列后有

\[
[A_O,A_N]\begin{pmatrix}x\\z\end{pmatrix}=b,
\qquad x_B=B^{-1}b,\quad x_{N_O}=0,\quad z=0.
\]

因此旧点在增列后仍可行；旧B仍是m×m可逆矩阵，列内容未变，只需映射新位置。
新列的MIN约化成本为 c_new-a_newᵀpi_old，可为负；旧对偶对新增列的约束可能不满足。
重新计算乘数/约化成本并继续Phase II是必要步骤，不能直接发布旧最优值。

精确算术中可行域扩展使MIN最优值不增；严格下降还依赖允许正步长，例B说明负rc与
零步长可以同时发生。浮点实现按已有容差验证raw Bx=b、非负性和完整原始点；标准形
清零后的可行性不替代原始行检查。最终OPTIMAL需完整原模型最优核验。

语义键为(original,原名)或(slack/surplus,来源原行)。例B加q后，列序[x,slack_cap]
变为[x,q,slack_cap]，旧基索引(0,1)应映射为(0,2)。原变量恰名slack_cap时，
角色仍将它与结构列区分。完整原始行一行未删是本版资格；例C的被删关系不能安全
延伸到新列。本版不恢复一般行变换或补基。

## 5. 算法到代码的映射

| 对象/规则 | 实现 |
|---|---|
| 冻结旧模型完整身份、基槽键、列清单 | [basis_snapshot.py](../../../src/silo/lp/simplex/basis_snapshot.py) 的 RevisedBasisSnapshot/capture_identity |
| 只追加兼容检查、fresh人工列去除、语义映射 | 同模块 map_snapshot，保留全部行 |
| raw基点与完整原始行独立复算 | validate_basis_point，不调用clean/裁剪 |
| 实际warm Phase II与最多一次cold | [revised.py](../../../src/silo/lp/simplex/revised.py) 的 reoptimize |
| MIN恢复、第二层独立核验与缓存生命周期 | [restricted_master.py](../../../src/silo/decomposition/restricted_master.py) 的 solve_reoptimized |

LP新结果包装既有详情，RMP新结果的result包装既有MIN快照；旧公开结果字段保持。
used_warm_start只标最终接纳的warm，warm_phase_two_attempted记录真实尝试；
cold_solve_count至多1。warm失败的迭代和原因保留，最终数值来自cold结果及其完整核验。
各run继承iteration_limit；它分别适用于warm Phase II和cold内部各既有run，
总枢轴预算不等于一次limit。cold_iterations包含cold的Phase I与Phase II。

缓存仅由本轮最终合格依据更新。普通solve清空缓存；成功add保留旧快照待检查，
失败add保持模型和缓存；最终非最优、数学核验失败或资格不足都清空缓存。
有效OPTIMAL遇删行/坏元数据时保留数学结果，只禁发快照。两个对象与历史结果互相隔离。

## 6. 核验与复现

在项目根目录用`.venv/Scripts/python.exe`运行以下完整程序，所有求解均走公开入口。

```python
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S, OptimizationSense as O
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus as T
from silo.core.variable import Variable
from silo.decomposition import RestrictedMasterProblem

def make(names, costs, rows, constant=0):
    return Model('lesson', [Variable(n) for n in names], rows,
                 Objective(dict(zip(names, costs)), O.MINIMIZE, constant))

def run(label, model, additions, expected, warm_flags):
    owner = RestrictedMasterProblem(model)
    outcomes = [owner.solve_reoptimized()]
    for name, cost, coefficients in additions:
        owner.add_column(name=name, cost=cost, row_coefficients=coefficients)
        outcomes.append(owner.solve_reoptimized())
    assert [r.result.objective_value for r in outcomes] == expected
    assert [r.used_warm_start for r in outcomes] == warm_flags
    for result in outcomes:
        assert result.result.status == T.OPTIMAL
        assert result.cold_solve_count == int(not result.used_warm_start)
        print(label, result.result.objective_value, 'warm=', result.used_warm_start,
              'attempt=', result.warm_phase_two_attempted, 'cold=', result.cold_solve_count,
              'warm pivots=', result.warm_iterations, 'cold pivots=', result.cold_iterations,
              'snapshot=', result.snapshot_available)
    return outcomes

a = make(['p0', 'p2'], [0, 10], [
    Constraint('conv', {'p0': 1, 'p2': 1}, S.EQ, 1),
    Constraint('r', {'p2': 2}, S.GE, .5)], 7)
run('A', a, [('p1', 4, {'conv': 1, 'r': 1})], [9.5, 9], [False, True])
b = make(['x'], [2], [Constraint('conv', {'x': 1}, S.EQ, 1),
                      Constraint('cap', {}, S.LE, 0)])
out = run('B', b, [('q', 0, {'conv': 1, 'cap': 1}), ('r', -1, {'conv': 1})],
          [2, 2, -1], [False, True, True])
assert out[1].warm_iterations >= 1
c = make(['x'], [2], [Constraint('a', {'x': 1}, S.EQ, 1),
                      Constraint('b', {'x': 1}, S.EQ, 1)])
out = run('C', c, [('q', 0, {'a': 1}), ('r', -1, {'a': 1, 'b': 1})],
          [2, 2, -1], [False, False, True])
assert not out[0].snapshot_available and out[1].snapshot_available
eq = make(['x', 'y'], [0, 4], [Constraint('conv', {'x': 1, 'y': 1}, S.EQ, 1),
                               Constraint('balance', {'y': 1}, S.EQ, .5)], 7)
run('EQ', eq, [('q', 1, {'conv': 1, 'balance': .5}),
              ('r', 0, {'conv': 1, 'balance': .5})], [9, 8, 7], [False, True, True])
```

教学输出展示路径诊断；真实入口证据另由
[144历史oracle](../../../tests/verification/test_rmp_reoptimization_oracles.py)观察cold入口、
Phase I/II、传入基语义键和新增列非基身份。独立真值枚举概率单纯形的可行单列及两列
在lo/hi端点的组合，全部原项先转Fraction，逐轮核对MIN原始/对偶/rc/差距。
另用独立owner运行1152次双后端cold，避免清空warm owner缓存。
异常及缓存测试在 [LP单元](../../../tests/unit/test_revised_reoptimization.py) 与
[RMP单元](../../../tests/unit/test_rmp_reoptimization.py)，实际结果见第10节报告。
实际144历史/576调用全部最优，144次初始cold、432次warm、零回退；并列1152次cold
符合Fraction真值。新225项、全量3669项与Ruff通过；正文11次公开调用和解答程序通过。

## 7. 研究意义与可扩展问题

本次能力可作为重复求解与未来增量定价的对照基线：分别记录cold、真实warm、失败
回退与工作量，避免相同答案掩盖实际仍在冷求解。全行限制和语义快照使成功路径可解释。
成熟单纯形基复用的参考实现本身不构成研究创新。

后续研究需要公平比较完整重建/线性系统成本与Phase-I节省，并按成功率、迭代数、
目标一致性和时间分别报告。接入CG、资源定价、LU更新或规模性能各需独立任务与证据，
当前实现没有推进这些能力。

## 8. 局限、反例与失效条件

原始行重排、旧变量重排、旧值哪怕只差微小数值都本轮不兼容，执行当前完整模型cold。
旧删行即使最终数学最优也无复用资格；这项保守规则排除例C的秩变化风险。
基奇异/非有限、raw原点违背、warm非最优或最终依据失败均最多cold一次，cold失败
后缓存清空；后续必须fresh cold，不能拿更早快照继续。RuntimeError保持可见。

最优与可行检查仍使用既有1e-9绝对容差，不承诺任意尺度正确性。无界出口继续
L0006的完整原点/方向精确标量门控；warm已核验无界仍回退cold一次，两个出口各自
检查。该规则不统一presolve的独立终态或外部/替身后端的状态证明。
每次仍完整构造标准形、重解基系统，无LU缓存或一般模型修改热启动保证。

## 9. 练习与解答入口

[六道练习](exercises.md)与[完整解答](solutions.md)覆盖可行基、对偶、映射、删行反例、
退化、生命周期、解析oracle与研究主张。稳定题号L0007-E01–E06。

## 10. 开发来源与修订记录

| 来源 | 用途 |
|---|---|
| [第8步合同](../../../tasks/codex/20261020-02-01_rmp-reoptimization.md) | 资格、单次回退、144历史、范围与教学要求 |
| [执行报告](../../../tasks/reports/20261020-02-01_rmp-reoptimization_report.md) | 实测路径、迭代、cold对照、质量、教学与Git证明 |
| L0001/L0002/L0006 | 原始行、MIN映射与无界充分依据的已有约定 |

2026-10-20 v0.1.0：按篇首实际实现提交核对完整程序、六题/解答、代码映射与全部测试。
