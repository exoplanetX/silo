---
lesson_id: L0011
title: 一般模型、可逆变换与原始空间核验
topic: modeling.general-lp
version: 0.1.0
status: draft
created: 2026-10-23
updated: 2026-10-24
verified_code: null
verified_on: null
source_tasks: [20261023-02-01_teaching-prototype]
---

# L0011｜一般模型、可逆变换与原始空间核验

## 1. 问题与学习目标

模型支持min/max与一般界，内核仍可只处理非负变量。关键是给每一次变换留下
可逆关系，使最后的可行点、目标、对偶和依据都在用户输入坐标中核验。
本篇学习这种分层关系，以及预处理派生界为何必须有对偶来源。

## 2. 前置知识、符号与假设

原模型为min/max c0+c'x，行区间l_r<=Ax<=u_r，变量区间L<=x<=U。
所有系数有限，缺少的界用无穷；整数变量界按整点解释。s=min:+1/max:-1。
四类非负乘子为行Yl/Yu、变量Zl/Zu。约定
s*c−A'Yl+A'Yu−Zl+Zu=0，公共signed dual为d=s*(Yl−Yu)，rc=c−A'd。
这些约定只决定符号，退化时不强求乘子唯一。

## 3. 手算例子

min x+2y+5z+7，1<=x+y<=3，−2<=x<=4，y自由，z=3。
对固定x选y=1−x，目标24−x，故x=4,y=−3,z=3，目标20。
Yl=2，Yu=0，Zx上=1，Zz下=5，其余为0；stationarity三个分量均0，
每个正乘子对应紧侧。对偶目标7+2−4+15=20。
公共d=2，rc=(−1,0,5)。将目标全取负并改max，得到−20，s归一后KKT相同。

## 4. 原理推导与正确性依据

用x=o+Tz，z>=0：有限下界x=L+z；仅上界x=U−z；自由变量x=z+−z−；
原始固定变量只保留offset。canonical目标MAX −s*f，c0由offset恢复，
区间行拆侧、有限上界补行，并逐行保存来源与方向。整数位移必须用整数锚点。

对上侧a'x<=b，若其他变量最小活动有限，则a_j>0时
x_j<=(b−Σk≠j a_k*chosen_bound_k)/a_j。该新界的不等式是原行及其他界的
正线性组合。其对偶乘子应逆序按同一组合系数分配回原始行和旧界。
传播后的固定不能冒充原始固定：min x，0<=x<=2，行x=1，最优行dual=1，
原始界乘子为0；把派生固定乘子留在原始下界会违反互补。

恢复后检查原始可行、符号、stationarity、互补及原始目标=对偶目标，
因此标准形得到“最优”只是候选。不可行用原始Farkas正矛盾；无界用原始可行点和
严格改善射线，整数无界另需整数兼容性。无顶点的最优直线不能靠空顶点集判不可行。

## 5. 算法到代码的映射

- `core/constraint.py:row_bounds`与`core/model.py:validate`定义输入对象。
- `modeling/general.py:normalize`记录offset/T、row origins、整数坐标与缩放关系。
- `presolve/activity.py:propagate/recover_multipliers`记录并逆推派生界。
- `lp/general.py:solve_lp_data`统一变换、内核、恢复和原始核验。
- `lp/verification.py`做KKT、精确Farkas及点/射线核验。
- `solver.py:solve`与`cli/main.py`提供用户入口，I/O不调用算法。

## 6. 核验与复现

仓库根运行`.venv/Scripts/python.exe -m pytest tests/unit/test_prototype_models.py -q`。
组合例预期20，派生固定例预期行dual1、rc0；测试从原始输入直接重构互补与stationarity。
JSON/MPS/API/CLI保持相同目标。独立Fraction oracle不导入生产规范化；验收矩阵身份
固定在`tests/fixtures/prototype_manifest.json`，补充证据与运行结果见总报告。
本篇核验提交与日期在实际检查后登记，draft不构成完成声明。

## 7. 研究意义与可扩展问题

一般建模可使后续LP/MIP/列生成共用同一数学约定；来源账本也可服务敏感性分析和解释。
这是可复核基础设施，尚不构成新算法贡献。原DAG与资源研究义务保持各自范围。

## 8. 局限、反例与失效条件

稠密参考内核受工作区和数值预算限制。整数取整的不可行依据不能当作连续LP的Farkas。
近奇异或重构失败会返回numerical_failure。有限测试不证明任意规模/条件数都可稳定求解。
旧tableau/Revised标准形入口仍保留其输入域，完整一般用户入口为silo.solve。

## 9. 练习与解答入口

见[练习](exercises.md)和[解答](solutions.md)，ID固定L0011-E01至E03。

## 10. 开发来源与修订记录

来源为[总合同](../../../tasks/codex/20261023-02-01_teaching-prototype.md)、
[总报告](../../../tasks/reports/20261023-02-01_teaching-prototype_report.md)与
[原始规格](../../../docs/prototype_model_contract.md)。2026-10-24初稿，模块M1实际代码核验后登记基线。
