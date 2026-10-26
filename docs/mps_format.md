# JSON 与 free-MPS 模型输入输出

0.3.0a2另提供[严格LP文本读写](lp_format.md)与`convert`模型转换命令。
本页JSON/MPS原域、数值保护和接口保持；LP的区间拆行规则不放宽JSON/MPS往返约定。

公共函数位于 `silo.io`：`read_json_model(path)`、`model_from_dict(payload)`、
`model_to_dict(model)`、`read_mps_model(path)`、`parse_mps(text)`、
`write_mps_model(model, path)`、`model_to_mps(model)`。读取和写入均不调用外部求解器。
文件使用 UTF-8；MPS 文件接口处理未压缩文本。非法记录抛出 `ValueError`，
MPS 解析错误带行号。格式支持与求解结果验收分别判断。

## JSON 兼容扩展

原有顶层字段 `name`、`sense`、`variables`、`objective`、`constraints` 保持。
目标方向为 `minimize` 或 `maximize`；目标对象接受 `coefficients` 和 `constant`。
变量对象接受 `name`、`lower`、`upper`、`type`，默认连续、下界 0、无上界。
`type` 可为 `continuous`、`integer`、`binary`。

变量 `lower: null` 表示负无穷，`upper: null` 表示正无穷。
行可用既有 `sense`/`rhs`，也可用 `lower`/`upper`。任一显式区间侧出现时，
行活动范围完全由 `lower`/`upper` 决定；同时提供的 `sense`/`rhs` 保留为兼容字段，
仍须通过类型、枚举及有限性校验。区间表示中，遗漏或 null 的一侧为无界，
两侧 null 表示自由行，即使兼容字段写了有限 RHS。序列化区间行时输出有效的两侧，
不再输出未参与约束的兼容字段。例如：

```json
{
  "name": "general",
  "sense": "minimize",
  "variables": [{"name": "x", "lower": null, "upper": 5}],
  "objective": {"coefficients": {"x": 2}, "constant": 3},
  "constraints": [{"name": "r", "coefficients": {"x": 1}, "lower": -2, "upper": 4}]
}
```

所有系数、目标常数、有限界和旧式 RHS 必须是有限数值，布尔值及字符串数值被拒绝。
无穷只通过 null 表达；文件中的 NaN、Infinity 等非标准 JSON 数字被拒绝。
未知字段及同一对象中的重复字段被拒绝，防止元数据或拼写错误被悄然丢弃。
`model_to_dict` 保留旧式行的 `sense`/`rhs` 表示，并以 null 输出无界侧，
因此可用 `json.dumps(model_to_dict(model), allow_nan=False)` 序列化。

## free-MPS 文本约定

按顺序支持 `NAME`、`OBJSENSE`、`ROWS`、`COLUMNS`、`RHS`、`RANGES`、
`BOUNDS`、`ENDATA`。`NAME`、`ROWS`、`COLUMNS`、`ENDATA` 必须存在；
其余节可省略，重复或逆序节被拒绝。
节头从第 1 列开始，数据记录至少缩进一个空白字符，字段以空白分隔。
推荐使用写入器采用的单空格格式：

```text
NAME example
OBJSENSE
 MIN
ROWS
 N obj
 L r
COLUMNS
 x obj 2 r 1
RHS
 rhs obj -3 r 4
RANGES
 rng r 6
BOUNDS
 MI bnd x
 UP bnd x 5
ENDATA
```

该模型的目标为 `min 3 + 2*x`，行范围为 `-2 <= x <= 4`，变量范围为 `x <= 5`。
空白行和以 `*` 开头的整行注释可用；行内注释、引号名称和名称内空白不属于本子集。
名称保留大小写，节名、行类型、bound 类型及 MIN/MAX 可不区分大小写。
数值支持十进制、小数及 E/D 指数，拒绝 NaN、无穷和无法表示的非零下溢数据。

数值转换以 Decimal 的数学值为准。数学整数若转换为 float64 会改变其值，解析器将其
保留为 Python `int`，交统一求解入口的 `input_conversion` 门控显式拒绝。例如
`9007199254740993`、`9007199254740993.0`、`9007199254740993.000`、
`9.007199254740993e15` 和 `90071992547409930e-1` 均保留同一整数；该规则覆盖
矩阵/目标系数、目标常数、RHS、连续/整数界及 RANGES 派生端点。整数性由数值决定，
尾随零、正负号和科学记法不改变保护。超过有限 float64 数值尺度的值在解析阶段拒绝。

一般非整数十进制按最近的 float64 值进入模型，包含可表示的非零 subnormal；这保持原有
浮点模型语义。例如 `0.1` 使用其二进制近似值，`5e-324` 转为最小正 subnormal。
直接或派生的非零 Decimal 若转换为 `0.0/-0.0`，均在解析阶段拒绝。精确十进制零仍合法。
该入口保护不增加任意精度求解能力，也不改变 JSON 已有数值语义。

`OBJSENSE` 接受下一行 `MIN`/`MAX`，也接受同一行 `OBJSENSE MAX`。
省略时默认 MIN。`ROWS` 首个 N 行是目标，其余 N 行作为自由约束行保留。
目标 RHS 为 `-c0`，省略目标 RHS 时 `c0=0`。自由行不接受 RHS；
自由行和目标均不接受 RANGES，避免丢弃没有模型表示的数据。

`COLUMNS`、`RHS`、`RANGES` 每条记录支持一组或两组行名/数值。
同一列的数据记录必须连续；重复矩阵元素、重复 RHS/范围元素被拒绝。
变量首次出现的列顺序、约束 ROWS 顺序保留；显式零系数规范化为稀疏缺省零。
没有非零系数的变量用一条目标零记录保留其身份。

每种向量只接受一个集合；RHS、RANGES、BOUNDS 可以使用彼此不同的集合名。
第二个 RHS、RANGE 或 BOUND 集合明确报错，禁止默认挑选第一组。

## 行范围与整数界

设 RHS 为 b、RANGES 数值为 r：

| ROWS 类型 | 恢复的下侧 | 恢复的上侧 |
|---|---|---|
| L，无 range | 负无穷 | b |
| G，无 range | b | 正无穷 |
| E，无 range | b | b |
| L，有 range | b − abs(r) | b |
| G，有 range | b | b + abs(r) |
| E，r ≥ 0 | b | b + r |
| E，r < 0 | b + r | b |

RHS/RANGES 的侧界加减在十进制文本值上进行，派生侧与直接输入共用上述转换门。
例如 `b=1e-300`、`r=0.` 后接 100 个 `9` 再接 `e-300` 的 L 行，下侧精确为
`1e-400`；其非零下溢会被拒绝。G 行及 E 行正/负范围采用同样检查，派生溢出也拒绝。
中间范围宽度可大于最大的单个浮点数，最终两侧须通过有限尺度和非零下溢检查。

写入器对整数值 float 输出其实际可表示的精确整数文本 `str(int(value))`，对其余 float
使用 `repr(value)`；保留的 Python 整数同样输出精确整数。比如 float `1e308` 的二进制
精确值是整数，最短文本 `1e308` 所表示的数学整数与该值存在差异。输出实际整数后，
读回仍是原 float，整数保护保持生效。RANGES 宽度由**与已输出端点一致的十进制值**
相减生成，因此大 float、宽于单个 float 的区间和非零 subnormal 端点均可保持往返。

整数段使用 `marker_name 'MARKER' 'INTORG'` 与匹配的
`marker_name 'MARKER' 'INTEND'`，仅接受所示单引号标记；不允许嵌套或遗漏配对。
普通列默认界为 `[0,+∞)`；INTORG 段中的整数列默认界为 `[0,1]`。
写入器为一般整数显式写出两侧，包括无限上界的 PL，避免默认界改变模型。

| Bound 类型 | 含义 | 需要数值 |
|---|---|---|
| LO / UP | 下界 / 上界 | 是 |
| FX | 两侧固定为该值 | 是 |
| FR | 两侧无界 | 否 |
| MI / PL | 下侧 / 上侧无界 | 否 |
| BV | 二元域及默认 `[0,1]` | 否 |
| LI / UI | 声明整数域并指定下界 / 上界 | 是 |

BV 必须出现在该变量其他 bound 记录之前，可再用 LO/UP/FX 收紧二元范围；
最终界必须保留在 `[0,1]` 内。其余显式下侧或上侧各只能指定一次。
单独负 UP/UI 且尚未指定下侧时，下侧设为负无穷；显式 LO/LI/MI 消除该默认歧义。
LI/UI 不对有限界取整，整数域的规范化由求解链完成。

## 明确拒绝的输入

fixed-column 的传统字段布局、空列名续行、SOS、二次段、半连续/半整数界、
多目标、多场景、未知节/类型、额外字段、未知行/列引用和 ENDATA 后的数据均报错。
传统 fixed 布局与部分对齐的 free 文本在字节上相同；本子集保留该布局作拒绝条件，
要求将这些数据重排为单空格 token 记录后输入。它不尝试猜测作者的格式意图。

MPS 不保存目标行或集合的原始名称，也不保存原文件的排版和注释。
写入器为目标和 marker 生成避免冲突的名称；变量、约束、数学数据和域保持。

范围方向和 bound 约定参考
[IBM MPS 记录说明](https://www.ibm.com/docs/en/cofz/12.9.0?topic=standard-records-in-mps-format)；
free 格式与整数 marker 默认界参考
[Gurobi MPS 格式说明](https://docs.gurobi.com/projects/optimizer/en/current/reference/fileformats/modelformats.html)。
