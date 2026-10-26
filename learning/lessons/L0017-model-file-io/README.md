---
lesson_id: L0017
title: 模型文件怎样保持数学语义
topic: modeling.file-io
version: 0.1.0
status: checked
created: 2026-10-26
updated: 2026-10-26
verified_code: 42892035db426c4739b6c1a7ad9648852d2b1dc8
verified_on: 2026-10-26
source_tasks: [20261026-03-01_reliability-io]
---

# L0017｜模型文件怎样保持数学语义

## 1. 问题与学习目标

模型文件读写的核心义务，是让读回的模型表达同一个目标和可行域。
目标常数丢失可能不改变最优点，却改变目标值和gap；自由变量被默认非负，
则直接改变可行域。读写函数都来自同一实现时，相同错误还可能在往返中抵消。
本篇学习怎样声明有限格式、分离语义与求解核验，并引入另一种解析实现。

## 2. 前置知识、符号与假设

考虑 `min/max cᵀx+c₀`，行区间 `lᵢ≤aᵢᵀx≤uᵢ`，变量区间
`Lⱼ≤xⱼ≤Uⱼ`，部分变量取整数。无穷表示某侧不存在，不能当成有限大数。
本篇适用线性、单目标模型；LP文本遵循
[SILO-LP-1](../../../docs/lp_format.md)，JSON/MPS保持各自已有约定。
名称是交换时的身份线索，顺序变化不应改变数学比较。

## 3. 手算例子

取 `min 2x+y+3`，`1≤x+y≤4`，`x≥0`，`y=1`。
代入固定变量可得 `0≤x≤3`，目标为 `2x+4`，最优值4在x=0取得。
LP文本用两行表达原区间：

```text
Minimize
 obj: 2 x + y + 3
Subject To
 band__lower: x + y >= 1
 band__upper: x + y <= 4
Bounds
 0 <= x <= +inf
 y = 1
End
```

两个单侧约束的交集恰好是原区间；常数3必须保留。
如果输入已经含名为band__lower的行或变量，输出按预定规则选择band__lower_1等未占用名，
不能覆盖已有身份。零目标/零列变量仍在目标与Bounds中显式出现。

## 4. 原理推导与正确性依据

数学等价要求方向、c、c₀、变量域以及每个有限行侧一致。
`l≤aᵀx≤u`等价于两条不等式；`aᵀx+k≤b`等价于`aᵀx≤b−k`。
它们是代数恒等变换，与求解器能否找到最优解无关。
整数变量还必须保持整数格，二元变量的有效域是显式界与[0,1]的交集。

十进制文本`.1x+.2x−.3x`先在精确文本有理域合并，可得0x，仍保留x。
解析后有限标量进入binary64模型表示；非零下溢、非有限和不能精确表示的整数明确拒绝。
此输入保护并不把数值求解器变成任意精度算法。

文件核对比较`Fraction(value)`表示的实际二进制有理值。
目标系数1变为`1+2**-39`，即使差异小于求解容差，也已经改变文件语义，应被拒绝。
求解点则有另一义务：使用原始数据回算残差，按已声明分量容差判断。
把这两类阈值混在一起，会允许文件错误被数值容差遮蔽，或错误地要求浮点点精确满足等式。

## 5. 算法到代码的映射

| 对象 | 实现位置 | 作用 |
|---|---|---|
| 有限语法/拒绝规则 | [lp.py](../../../src/silo/io/lp.py) | 词法、节顺序、线性和、显式界/整数域 |
| 文本数值转换 | [number_codec.py](../../../src/silo/io/number_codec.py) | 精确累加后统一转换，保护整数和下溢 |
| 名称/区间输出 | `model_to_lp` | 确定拆行、防冲突、保留零列 |
| 不求解的转换 | [CLI](../../../src/silo/cli/main.py) | convert完成序列化后写出，optimize保留解输出职责 |
| 独立格式签名 | [exact.py](../../../scripts/reliability/exact.py) | 直接从原始payload构造预期，精确核对公开解析数据 |
| 独立真值 | [oracle.py](../../../scripts/reliability/oracle.py) | 有理顶点/对偶、矛盾或射线、有限整数枚举 |

core/modeling及求解算法保持独立于文件语法；解析器输出既有Model对象。
原生算法不导入或调用外部优化器。

## 6. 核验与复现

下面的小例只读写文本，不求解。在已安装当前候选的仓库根目录执行：

```python
from silo.io import parse_lp, model_to_lp

text = "Min\n 2 x + y + 3\nST\n lo: x+y >= 1\n hi: x+y <= 4\nBounds\n y = 1\nEnd"
model = parse_lp(text)
assert model.objective.constant == 3
assert model.variables[1].bounds.lower == model.variables[1].bounds.upper == 1
assert model_to_lp(parse_lp(model_to_lp(model))) == model_to_lp(model)
```

开发回归使用独立手写微例，位置为`test_lp_io.py`、`test_model_conversion_cli.py`、
`test_reliability_tools.py`。正式32模型保留集另由`accept.py`读取，不注册为pytest参数。
精确格式往返、手写输入和highspy1.15.1的24次readModel/getLp属于不同核对路径；
外部进程只解析，不执行优化。真实运行分母和失败记录以
[本单报告](../../../tasks/reports/20261026-03-01_reliability-io_report.md)为准。
2026-10-26实际执行本篇Python小例，文本读写与稳定重写断言通过，公开求解调用0次。
小例代码SHA为010140173005da670d243444e1d413272f179c378e6eb7a1148fbb7d7861bc8c；
原始核对收据为outputs/reliability_io_20261026/prepush_check.json。

## 7. 研究意义与可扩展问题

模型交换能帮助复现论文算例、保存失败输入、比较不同建模工具的导出结果。
先保证读写语义，才能把求解差异归到算法或数值机制。外部读取提供实现独立性，
但有限输入上通过不能证明所有合法文件都兼容。更广方言和更大模型需另行明确目标。

## 8. 局限、反例与失效条件

SILO-LP-1不覆盖二次/非线性、SOS、半连续、多目标/多场景或任意厂商方言。
完全自由行及零变量模型的LP导出明确未支持；JSON/MPS原支持域不缩减。
非法/保留名称拒绝，不能静默改名。一个writer/parser对的自洽不够证明交换正确。
新接受集是操作性保留集，同一执行者能读，不称真正盲测；二次运行也保留首次暴露记录。
小数据有限核验不推出工业成熟度，不改变原研究C/D/E或native状态。

## 9. 练习与解答入口

见[练习](exercises.md)及[解答](solutions.md)：包含常数移项、区间/名称、
精确格式与浮点容差、同源往返的反例。

## 10. 开发来源与修订记录

任务为[20261026-03-01](../../../tasks/codex/20261026-03-01_reliability-io.md)，
冻结先行提交f8f00fd60728e0e9314342a3b4e037cfee50f790。
2026-10-26初建v0.1.0并核对小例，产品身份42892035db426c4739b6c1a7ad9648852d2b1dc8。
前置综合篇为[L0016](../L0016-reliable-solver/README.md)，本篇不改其历史核验身份。
格式和独立读取参考[HiGHS官方Python示例](https://ergo-code.github.io/HiGHS/dev/interfaces/python/example-py/)
及[模型文件格式说明](https://docs.gurobi.com/projects/optimizer/en/current/reference/fileformats/modelformats.html)。
