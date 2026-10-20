---
lesson_id: L0008
title: 列生成中的基复用与逐轮证据
topic: decomposition.cg-reoptimization
version: 0.1.0
status: checked
created: 2026-10-20
updated: 2026-10-20
verified_code: f4cc36e00628da266d12ac93b25f652c8ae2f569
verified_on: 2026-10-20
source_tasks:
  - 20261020-03-01_cg-reoptimization
---

# L0008｜列生成中的基复用与逐轮证据

## 1. 问题与学习目标

列生成反复求解逐列扩大的RMP。上一轮基有时可沿用，但本轮定价必须消费本轮最终
经核验的MIN对偶。本篇说明如何显式接入基复用，同时保留失败轮、列集、界和预算的
所属关系。该链路服务于逐步建设承载OR研究的求解器与伴学材料；有限普通DAG结果
按实际范围保留，其他原目标义务继续存在。

前置阅读：[L0004列生成与差距](../L0004-column-generation/README.md)、
[L0005独立可行性恢复](../L0005-cg-feasibility/README.md)、
[L0007基复用与单次cold回退](../L0007-rmp-reoptimization/README.md)。

## 2. 前置知识、符号与假设

完整列域U为固定普通DAG全部s-t路径；lambda连续非负、conv等式总权重精确为1。
目标min c0+sum(c_p*lambda_p)，其余行为LE/GE/EQ。seed为非空合法路径且当前RMP可行。
控制器默认cold；显式True仅使用原生Revised及兼容测试子类，严格bool校验。

| 符号 | 所属对象 |
|---|---|
| S_k | 第k轮实际已求解的不可变路径registry |
| pi_k | 该轮最终经核验的MIN RMP乘数 |
| rho_k | 对pi_k在完整U上的最小约化成本 |
| P_k、D_k、L_k | 同轮原始/对偶目标与平移后的数值下界 |
| outcome_k | 同轮公开RMP重优化结果，含最终MIN result和执行诊断 |

CG每次调用拥有新RMP，轮内仅消费一次公开opt-in结果；内部warm/cold及缓存资格由
L0007管理。逐轮结果保存outcome，顶层last_valid_master继续保留原MIN结果类型。

## 3. 手算例子

机制A：三条平行弧x/q/r，成本2/0/1，conv=1，cap系数0/1/0、cap<=0，seed仅x。
初轮乘数(2,0)，q的rc=-2、r的rc=-1，先增q。完整约束强制q=0，第二轮warm以
零步长枢轴调整基/对偶，目标仍2；当前对偶可为(2,-2)，r仍有rc=-1。增r后第三轮
warm目标1。轨迹2→2→1、cold/warm/warm，真实退化不能仅凭目标相等推断。

机制B：d1/d2/o12/o21的成本4/6/1/2，R/C向量(1,1)/(0,0)/(1,0)/(0,1)，
conv=1、R=C=1/2、c0=-3，seed为d1/d2。初始投影行依赖，cold目标2且不发快照。
加入一条off-diagonal后，原始三行恢复独立，仍cold且目标2；本轮建立资格后加入另一条，
最后warm取两条off-diagonal各1/2，目标-1.5。轨迹cold/cold/warm，不能沿用旧删行集。

恢复衔接：p0/p1/p2成本0/4/10、r=0/1/2、conv=1、r>=1/2、c0=7，seed p0。
先独立恢复得到可行seed，再显式调用经济CG。首轮9.5必须fresh cold，随后增p1可到9；
辅助零成本、验证基和经济目标各自保留来源。

## 4. 原理推导与正确性依据

仅增列时，旧非人工完整行基B与原始可行点可沿用，新增非基变量取0。原始可行性
保持不保证旧对偶对新列可行，所以仍须求解本轮RMP。任何失败warm的乘数不作为
最终依据；warm失败/cold成功时，只消费最终cold的result，外层仍是一轮。

完整定价与上下界推导保持：令rc_p=c_p-a_pᵀpi，rho=min_U rc_p，delta=min(0,rho)。
只平移自由conv乘数pi'_conv=pi_conv+delta，每条列conv系数1，故

\[
\bar c'_p=\bar c_p-\delta\ge0,\qquad
L=D+\min(0,\rho)\le z^\star\le P.
\]

该精确结论依赖原始可行性、乘数符号及完整定价；热启动方式不改变证明。有限浮点
实现保留原规则：P/D/L由原项fsum生成；g_raw=fsum(P,-L)，g在原始贡献层消去c0，
eta=32*ulp(绝对贡献之和)。负g仅在eta<=tol且-g<=eta时接受；正向阈值不加eta。
停止仍要求rho>=-tol、g<=tol并通过一致性检查。

退化最优对偶可不唯一。冷热模式可能选择不同合法对偶、路径或轮数；逐轮按各自S_k
和pi_k核对。相同目标、同一路径或一个used_warm标志都不能替代实际Phase II入口证据。

## 5. 算法到代码的映射

唯一生产接线位于[dag_column_generation.py](../../../src/silo/decomposition/dag_column_generation.py)：
末尾关键字reoptimize_rmp=False，True分支每轮调用一次公开RMP.solve_reoptimized，
将outcome.result送入原有目标核验/定价/候选/差距流程；False保留普通solve。
只读公开Revised类用于参数检查，不访问LP私有接口或RMP内部状态。

迭代末尾rmp_reoptimization默认None，四个历史分支均按关键字保存同轮outcome；
master_result is outcome.result。旧位置参数和顶层结果字段保持。路径与数值助手文本
保持，基映射/无界门控/冷回退仍由下层已有公开入口管理。

失败发布点需要分别处理：RMP非最优保留上一有效轮；原始主目标先失败也保留较早轮；
目标已通过并登记后，pricing/candidate/gap失败可保留当前有效RMP，但本轮所有界为空。
这三类不能合并成统一回退旧轮。seed重构先失败则没有已解轮与outcome记录。

## 6. 核验与复现

从项目根目录用`.venv/Scripts/python.exe`运行完整程序。全部求解走公开API。

```python
from silo.core.enums import ConstraintSense as S
from silo.decomposition import (DagArc, DagPricingProblem, DagMasterRow,
    DagColumnGenerationProblem, DagColumnGenerationStatus, solve_dag_column_generation,
    restore_dag_feasibility)

def run(label, problem, expected, cold_counts):
    result = solve_dag_column_generation(problem, reoptimize_rmp=True)
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED
    assert [r.master_result.objective_value for r in result.iterations] == expected
    assert [r.rmp_reoptimization.cold_solve_count for r in result.iterations] == cold_counts
    for record in result.iterations:
        out = record.rmp_reoptimization
        assert record.master_result is out.result
        print(label, record.iteration, record.master_result.objective_value,
              'attempt=', out.warm_phase_two_attempted, 'warm=', out.used_warm_start,
              'cold=', out.cold_solve_count, 'warm pivots=', out.warm_iterations,
              'cold pivots=', out.cold_iterations, 'snapshot=', out.snapshot_available)
    return result

graph = DagPricingProblem(['s','t'], [DagArc('x','s','t',2),
    DagArc('q','s','t',0,{'cap':1}), DagArc('r','s','t',1)],
    's','t',['conv','cap'], base_coefficients={'conv':1})
a = DagColumnGenerationProblem(graph, [DagMasterRow('conv',S.EQ,1),
    DagMasterRow('cap',S.LE,0)], 'conv', [('x',)])
ra = run('A', a, [2,2,1], [1,0,0])
assert ra.iterations[1].rmp_reoptimization.warm_iterations >= 1

graph = DagPricingProblem(['s','t'], [DagArc('d1','s','t',4,{'R':1,'C':1}),
    DagArc('d2','s','t',6), DagArc('o12','s','t',1,{'R':1}),
    DagArc('o21','s','t',2,{'C':1})], 's','t',['conv','R','C'],
    base_coefficients={'conv':1})
b = DagColumnGenerationProblem(graph, [DagMasterRow('conv',S.EQ,1),
    DagMasterRow('R',S.EQ,.5), DagMasterRow('C',S.EQ,.5)],
    'conv', [('d1',),('d2',)], -3)
rb = run('B', b, [2,2,-1.5], [1,1,0])
assert not rb.iterations[0].rmp_reoptimization.snapshot_available

graph = DagPricingProblem(['s','t'], [DagArc(f'p{i}','s','t',c,{'r':i})
    for i,c in enumerate((0,4,10))], 's','t',['conv','r'], base_coefficients={'conv':1})
p = DagColumnGenerationProblem(graph, [DagMasterRow('conv',S.EQ,1),
    DagMasterRow('r',S.GE,.5)], 'conv', [('p0',)], 7)
restored = restore_dag_feasibility(p)
assert restored.feasible_problem is not None
economic = run('economic', restored.feasible_problem, [9.5,9], [1,0])
assert not economic.iterations[0].rmp_reoptimization.warm_phase_two_attempted
```

真实入口/基身份另由[288图oracle](../../../tests/verification/test_dag_cg_reoptimization_oracles.py)
观察：原图自写DFS逐原项Fraction累计，全域端点解析与当前registry顶点枚举互相核对。
每轮检验原始MIN证据、完整价格、候选/增列、P/D/L/g_raw/g/eta与停止；不调用生产
重构、数值或基助手给真值。完整域独立owner双cold交叉检查，不影响热owner。
[大常数及门控](../../../tests/verification/test_dag_cg_reoptimization_bounds.py)与
[失败/隔离单元](../../../tests/unit/test_dag_cg_reoptimization.py)分开记录，运行数不等于测试项数。
实测288图/864次主族与60图/180次大常数CG全部通过；对应696次完整域双cold参考另计。
新406项检查、targeted1287项、全量4075项与Ruff通过。正文3次经济CG共8轮及独立恢复、
解答标量程序均实际运行；完整计数与边界见报告。

## 7. 研究意义与可扩展问题

已有能力是让经济CG可显式消费可审查的重复求解接口，并保留每轮执行/数学证据来源。
这为后续公平工作量比较提供基线：区分初始cold、资格不足cold、warm、内部回退与外层轮。
基础机制接通、有限图通过与原项目研究特色分别判断，不能由局部成熟度反推原目标完成。

后续需求应由具体OR科学问题提出，再为增量定价、资源/整数结构或其他求解机制立项。
本步没有开展性能实验、因子缓存或增量算法，也没有创新、加速或工业稳健性主张。

## 8. 局限、反例与失效条件

复用资格仍要求旧完整有序原始行一行未删、旧数据不变、仅追加列。资格不足cold属于
保守支持边界；不能为凑warm命中改数据/原行。每轮仍完整重建矩阵和解基系统。
有限路径域与凸组合约束使完整可行域有界，后端UNBOUNDED只是CG的RMP失败诊断。

大c0可能吞掉发布目标低位，P减c0无法可靠恢复数学增量目标；应按原始贡献核验，
同时保留g_raw发布语义。32ULP只描述局部工程规则，不给LP误差严格上界。冷热轨迹
不同允许，输入/逻辑RuntimeError保持可见。资源约束、整数和任意尺度仍未由这些案例验证。

## 9. 练习与解答入口

[六题](exercises.md)与[完整解答](solutions.md)覆盖可行基/对偶、退化、秩恢复、四类失败
历史、当前列集/大c0 oracle、预算与研究主张。稳定编号L0008-E01–E06。

## 10. 开发来源与修订记录

| 来源 | 用途 |
|---|---|
| [第9步合同](../../../tasks/codex/20261020-03-01_cg-reoptimization.md) | 唯一目标、15路径、864/180运行与失败交叉要求 |
| [执行报告](../../../tasks/reports/20261020-03-01_cg-reoptimization_report.md) | 当前基线、真实计数、检查/教学/提交与治理文件保护 |
| L0004/L0005/L0007 | 既有数学、独立恢复和基资格/回退依据 |

2026-10-20 v0.1.0：按篇首实际实现提交核对十节、六题、公开程序与版本化测试。
