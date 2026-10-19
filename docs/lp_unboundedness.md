# LP 无界终止核验

Tableau 和 Revised 的直接 Phase-II `UNBOUNDED` 出口先核验完整原始 `Model`
上的候选点与改善方向。当前支持连续 MAX、既有近零下界/无有限上界域、LE/GE/EQ。
公开求解参数、`Solution` 字段和 `RevisedSimplexResult` 结构保持原有约定。

## 发布条件

候选必须有完整原变量坐标、有限数值。点满足实际原始下界和全部原行；方向非负，
对 LE 行满足 Ad<=0、GE 行满足 Ad>=0、EQ 行满足 Ad=0；还必须有 c·d>0。
于是 x0+t·d 对任意 t>=0 可行，目标随 t 无上界。目标常数不参与改善率。

内部“没有离基行”提供候选信号。进入列必须有效且非基，基坐标须一致；结构列按
实际位置/角色与原变量名称投影。Tableau 读取当前基的原始 RHS 和进入列；Revised
仅在无界候选处额外解当前基，保留未清零的点与方向。检查读取完整原模型，包括
Phase-I 后已删除的行、负 RHS 原方向和原始微小系数。

[内部核验模块](../src/silo/lp/unboundedness.py) 逐项先转换成 `Fraction`，再乘积、求和
和判号。float 表示实际二进制值，int 保留原整数。检查不使用残差容差，不做十进制
重解释、有理重建或候选修复，也不调用求解器。正常枢轴与全局容差保持原有行为。

## 状态与诊断

条件全部成立才发布 `UNBOUNDED`，消息附 `verified exactly`。坐标缺失/非法、
非有限数值、点或方向违背原行/界、无严格改善或终止基求解失败，都返回
`NUMERICAL_ISSUE`；消息区分 point、direction、improvement、coordinates、nonfinite。
非最优结果的目标为 `None`，primal/slack/dual/reduced-cost/basis 映射为空。
候选保留在内部，不作为最优解字段发布。

Phase I 最大化负人工量和，目标向上有界于零。其内部若报告无界，两个后端均发布
`NUMERICAL_ISSUE` 并指出 Phase-I 矛盾。

## 数值限制与复现

`x-(1+5e-10)z=1e10, x-z=1e10, max z` 的精确输入解为 z=0。
现有容差可能删掉一行并产生候选方向；完整原行检查拒绝它，返回数值诊断。
同样，微小正系数 `epsilon*z<=b` 给有限上界，微小负系数允许的真实改善方向则
可以通过。详见 [L0006 的完整双后端程序](../learning/lessons/L0006-lp-unboundedness/README.md)。

该策略只核验已有有限候选。对真实无界的 `3*x=1, max z`，浮点 x≈1/3 无法精确
满足原等式，可保守返回 `NUMERICAL_ISSUE`。它不保证识别所有真实无界模型、所有
终态或任意尺度问题。presolve 独立终态、外部/替身后端和 MIP 整数可行性判定保持
各自边界。RMP/CG/恢复器沿用原有数值失败传播；没有修改上层算法。

固定 240 核心族和 32 对照及实际候选的独立原项核对见
[解析测试](../tests/verification/test_lp_unboundedness_oracles.py)，异常、数值表示与上层
传播见 [单元测试](../tests/unit/test_lp_unboundedness.py)。执行记录见
[第7步报告](../tasks/reports/20261020-01-01_lp-unbounded-check_report.md)。
