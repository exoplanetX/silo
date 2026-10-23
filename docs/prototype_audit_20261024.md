# 五模块独立复查与修订依据（2026-10-24）

结论：五模块主体已落地，当前候选需要一次有界正确性修订。确认4项缺陷，归为3个修订包；
M2未发现新的确认错误。当前修订目标保持教学研究通用LP/MILP原型，不新增第六模块。

审查基线：`4ca4bab47f2eecb8b60d5e34e767b4dc239fd969`，分支
`codex/teaching-research-prototype`，版本`0.2.0a1`。
历史总合同和原验收记录保持原状，本文件登记后来发现的不足。
原研究A/B已验收、C HOLD、D/E未开始；native延期状态不变。

## 1. 本次实际测试及其含义

| 检查 | 实际结果 | 能说明什么 |
|---|---|---|
| 完整质量检查 | 6147 passed / 22.94s，Ruff及结构检查通过 | 历史回归保持，无法排除覆盖之外的缺陷 |
| 新种子一般模型 | 96 LP + 96 MILP，每例默认/关闭presolve、scaling、cuts、heuristics并用DFS，共384次原生调用，0差异 | 小型双边界、等式、负系数及混合整数模型的新增对照证据 |
| 外部及独立真值 | 192个模型直接调用SciPy/HiGHS比较；其中48个纯整数另做完整有限域穷举 | 外部算法只算一条证据流；48个穷举不依赖求解器 |
| JSON/MPS往返 | 上述模型选24个，两格式共48次，原始数学数组完全相同 | 常规输入往返保持，未覆盖所有十进制转换边界 |
| M2独立检查 | 18个一般LP，行尺度1e-4至1e4，与HiGHS目标一致 | 本次未确认LP内核新错，不表示任意条件数稳定 |
| 发行记录复核 | 9个封存证据哈希、2个工件哈希一致；wheel中120个Python模块与当前源码一致 | 前次安装记录/工件未被替换；本次未重新安装 |
| 定向反例 | 协调方独立复现下列4项；6次直接solve加1次CG（另含2次内部LP） | 直接反驳相应输入或结果判定，而非从测试数推测 |

新增随机矩阵生成先固定seed `20261024`、规模4变量6行、每类96例与两组参数，再运行。
纯整数48例每变量最多6个取值，混合整数48例含2个整数和2个连续变量。
每16例设置一个明确不可行模型；其余由整数可行点构造。
直接使用SciPy的`linprog`/`milp`，不调用SILO外部适配层，且不使用SILO自己的可行性检查辅助函数。
独立检查原数组可行性、整数性、目标和最优界。384次原生调用连同对照及穷举耗时3.500s。
Python3.13.9、NumPy2.3.5、SciPy1.16.3。

本次证据在忽略目录`outputs/audit_20261024/`：

- `quality.log`：完整质量输出。
- `independent_probe.py`、`probe_models.json`、`probe_records.json`、`probe_summary.json`：新增矩阵及全部结果。
- `io_delivery_probe.py`、`io_delivery_summary.json`：往返与封存证据/工件复核。
- `confirmed_repros.py`、`confirmed_repros.json`：协调方逐项复现。

矩阵驱动SHA256：`e90479eb7ee71b7494270f4719c569fbab0f96aa4e0988533892a9728ac59bc3`。
192个模型JSON SHA256：`4df0fbec29dc7afd7df66872d395bd5c52e7f31155c6c28e642050483383ddad`。
生成运行文件不入Git；修订执行须将有意义的回归及可重复驱动纳入版本管理。
本次未重开/重置旧`outputs/prototype/run_ledger.json`，未重跑其已用满的64诊断额度。
三条只读复核分别负责M1/M2、M3、M4/M5；代理建议由协调方复现后采用，不重复计为独立算法证据。

## 2. F1（P1）：MILP目标剪枝越用了原始可行性容差

位置：`src/silo/mip/general.py`的节点弹出剪枝（原369行）、LP后剪枝（478行）、
`global_bound()`（185行）及结束输出（638–653行）。

```python
from silo import SolveOptions, solve
from silo.io import model_from_dict

p = {
    "name": "prune", "sense": "minimize",
    "variables": [{"name": "x", "lower": 0, "upper": 1, "type": "binary"},
                  {"name": "y", "lower": 0, "upper": 1, "type": "binary"}],
    "constraints": [{"name": "cover", "coefficients": {"x": 2, "y": 3}, "lower": 3}],
    "objective": {"coefficients": {"x": 0.006, "y": 0.01}},
}
r = solve(model_from_dict(p), SolveOptions(
    presolve=False, cuts=False, primal_tolerance=0.01,
    dual_tolerance=1e-12, objective_tolerance=1e-12,
    absolute_gap=0, relative_gap=0,
))
print(r.status, r.objective_value, r.dual_bound, r.absolute_gap)
```

实际`optimal, 0.016, 0.016, 0`；解析最优`x=0,y=1`、目标`0.01`。
两点均严格可行，因此差异不能归因于约束可行性放宽。启发式先产生`x=y=1`，
`node.bound >= best-primal_tolerance`随后丢弃仍能改进的节点；空前沿把incumbent变成了下界。
严格primal容差下答案正确。最大化负目标和加常数100可复现相同缺陷。
默认primal容差下，目标改成`6e-8*x+1e-7*y`并保持严格dual/objective容差也会触发。

修订必须同时处理目标比较的容差职责和被近似关闭子树的界；只替换容差变量不足以保证gap真实。
正gap参数才授权提前gap停止；原始可行性容差不授权近似目标剪枝。

## 3. F2（P1）：有限列生成的负约化成本被容差忽略后误发全池最优

位置：`src/silo/decomposition/general_master.py`的`PricingContext._score`（184行）、
`_finite_price`（255行）、结束分支（636–643行）与`ColumnGenerationResult.dual_bound`（451行）。

```python
from silo.core.model import Model
from silo.core.constraint import Constraint
from silo.decomposition.general_master import (
    GeneralRestrictedMaster, MasterColumn, FiniteColumnPricer, column_generation,
)
m = Model(name="cg_cap")
m.add_constraint(Constraint("cap", {}, rhs=1e12))
r = column_generation(GeneralRestrictedMaster(m),
    FiniteColumnPricer([MasterColumn("x", -1e-8, {"cap": 1})]))
print(r.status, r.objective_value, r.dual_bound)
```

实际`optimal, 0, 0`；完整问题`min -1e-8*x, 0<=x<=1e12`，解析最优`-10000`。
同一全列模型直接走原生`solve`实际得到`-10000`。
完整池中`rc(x)=-1e-8`已被检查，却因阈值而忽略；变量可取很大值，单列残差容差不能控制目标误差。

另一个解析无界反例：

```text
min -10000000*b - c
a+b-c=1, a+2b-c=2; a,b,c>=0
初始列a,b；完整池a,b,c；presolve=False
```

可行族`b=1,a=c=t>=0`使目标趋向负无穷。现CG却给约`-1e7`的有限最优，
其记录的`rc(c)=-1`仍被相对阈值忽略。该例由独立复核实跑，协调方独立复现了前一个有限例。

修订须分开“已遍历所有列”“没有阈值以上的改善列”“全池对偶可行与有效目标界”。
有限例必须实际求到`-10000`；无界例须取得有效无界依据或保守退出，不能发布有限最优。
允许有界的精确二进制/有理候选核验，不能在原生路径调用外部solver，也不能以全池黑箱替代列生成。

## 4. F3（P1）：MPS等值大整数的不同文本写法改变整数界

位置：`src/silo/io/mps.py::_decimal_number`（505–509行）。

```text
NAME lattice
ROWS
 N obj
COLUMNS
 x obj 1
BOUNDS
 LI bnd x 9007199254740993.0
 PL bnd x
ENDATA
```

执行`solve(parse_mps(text))`，现返回`optimal, x=9007199254740992`。
该点不满足原文本整数下界。词法指数为0的同值token `9007199254740993`
和`9.007199254740993e15`会正确保留整数并返回`numerical_failure/input_conversion`。
尾随`.0`改变Decimal指数，绕过了已有整数保护。
应按数学数值而非词法小数位判定整数，并覆盖系数、RHS、界、派生端点及写读往返。
契约不要求增加任意精度求解器；要求在精度丢失前明确拒绝或保留整数供既有门控拒绝。

## 5. F4（P2）：MPS RANGES派生非零端点下溢为零

位置：同一转换函数及`_row_bounds`（416–429行）。

```python
from silo.io import parse_mps
width = "0." + "9"*100 + "e-300"
text = "\n".join([
    "NAME underflow_range", "ROWS", " N obj", " L row", "COLUMNS",
    " x obj 1 row 1e-300", "RHS", " rhs row 1e-300", "RANGES",
    f" rng row {width}", "BOUNDS", " BV bnd x", "ENDATA", "",
])
model = parse_mps(text)
print(model.constraints[0].row_bounds)
```

实际为`(0,1e-300)`，进一步求解得`optimal,x=0`。原十进制模型下侧为`1e-400`，
即`1e-400<=1e-300*x<=1e-300`且x二元，只有x=1可行。
直接token的非零下溢已有拒绝，派生端点漏过了检查；应在解析阶段明确拒绝。
极端尺度使该问题优先级低于常规数值下的F1/F2，仍属于现有输入承诺的必要修复。

## 6. 五模块判定与修订方向

| 模块 | 当前判断 | 本轮处理 |
|---|---|---|
| M1 模型与输入 | 主通路成立，MPS转换完整性有缺口 | 修F3/F4，统一直接与派生转换门 |
| M2 LP与重优化 | 已有交付通过，本轮无确认新错 | 保持回归，检查被M1/M3/M4调用的原空间核验 |
| M3 MILP与割 | 搜索/割已建立，目标剪枝与界发布有错 | 修F1；补目标尺度、方向、平移和限额回归 |
| M4 研究接口 | 接口可用，CG全池最优证明不足 | 修F2；保持Phase I、迭代上限及真实列生成 |
| M5 安装验证 | 原记录及工件真实，针对性覆盖不足 | 加反例/变形回归，更新候选工件及干净安装 |

下一步只有一项：执行[修订计划](../tasks/phases/prototype_revision_20261024.md)及
[不可变修订合同](../tasks/codex/20261024-01-01_prototype-correctness-revision.md)。
修复、回归、伴学、工件与报告全部达到退出线后停止，不转入性能研究、C/D/E或新算法能力。

## 7. 派发前独立复核

`audit_revision_gate`以只读红队角色核对审查、计划、合同及必要源码，一次复核结论GO：
F1–F4均已覆盖，有限CG例不能靠保守拒绝绕过；旧账本和旧授权未被复用，八项退出条件足够。
本次门控没有重跑实验，没有计作新增实验流，也不代表修订已完成。
派发前按现有内容本地提交，精确排除两项治理文件，再将合同路径及提交身份交开发对话。
