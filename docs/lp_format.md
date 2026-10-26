# SILO-LP-1：严格线性文本约定

本语法于生产实现前冻结，来源为[20261026-03-01](../tasks/codex/20261026-03-01_reliability-io.md)。
这是明确的 LP 线性子集；兼容性以实际声明和独立读取结果为限。

UTF-8；反斜线 `\` 起至行尾为注释。节标题独占一行、不区分大小写；顺序固定：

| 节 | 接受的全部别名 |
|---|---|
| 目标 | Minimize, Minimum, Min, Maximize, Maximum, Max |
| 行 | Subject To, Such That, ST, S.T., S.T |
| 界 | Bounds, Bound |
| 一般整数 | Generals, General, Gen, Integers, Integer |
| 二元 | Binaries, Binary, Bin |
| 终止 | End |

目标、Subject To 和 End 必须存在；其他节可省略，每节最多一次。
Subject To 可为空。End 后只可有空白和注释。节重排、未知节、截断明确拒绝。
名称为 `[A-Za-z_][A-Za-z0-9_.]*`，排除上述节标题中的单词以及
`free, inf, infinity, nan, sos, semi, semicontinuous, semiinteger`（不区分大小写）。
变量名和行名各自唯一；输出不会静默改名。目标标签可省略；行标签可省略，
未命名行按 `row_1`、`row_2`……并在与全部显式行名冲突时递增编号。

目标和行左侧是线性项的和，可跨行；项间必须有 `+` 或 `-`，首项符号可省略。
项是十进制/E指数数值、裸变量或数值后接变量；不接受乘号、括号、乘积或平方。
目标常数保留，行左侧常数精确移至右侧。关系为 `<=`、`>=`、`=`，
右侧为一个有符号有限数值。双侧一行、变量右侧、非线性、SOS、多目标/多场景均拒绝。
表达式中同变量的多项在精确十进制有理域合并，再一次转换；
零项或抵消后的变量仍保留身份。数字转换为 binary64，非有限和非零下溢拒绝；
整数转换不精确时拒绝。该保护不表示任意精度求解。

Bounds 每行一条，可为 `l <= x <= u`、`x <= u`、`x >= l`、`l <= x`、
`u >= x`、`x = v`、`x free`。界位置接受有符号 inf/infinity；
下界只能为负无穷，上界只能为正无穷。连续和一般整数默认 `[0,+inf)`；
单独上界保留默认下界，free 显式指定两侧。允许在不同记录分别给两侧；
重复指定同一侧拒绝。矛盾界拒绝。Generals/Binaries 每个变量只能声明一次，
冲突或重复域声明拒绝。二元域与 `[0,1]` 取交集，交集为空拒绝。

导出时所有变量显式列界，并在目标以 `0 name` 保留零列。
等式/单侧行保留原名；真正的有限区间 `l < u` 拆为两行。
映射依原行顺序，先下后上，基名分别为 `原名__lower`、`原名__upper`；
候选若与任一原变量名、原行名或先前生成名冲突，添加 `_1`、`_2`……至未占用。
这项映射是确定的，不用行顺序或求解容差猜测对应。
完全自由行与零变量模型的 LP 导出明确报未支持；JSON/MPS原域保持。
输出目标标签从 `obj` 开始，避开所有变量/导出行名，必要时追加数字后缀。
数字采用能恢复相同 binary64 的文本表示，整数不先转换为不精确浮点。

LP 往返核对方向、目标常数/系数、变量身份/界/整数格及每个有名有限行侧。
预期直接从原始 payload 构造；实际从公开解析数据构造。
有限数值按 `Fraction(value)` 的实际二进制有理值精确比较，正负零等同；
无穷只比较方向。LP 允许上述拆行，JSON/MPS仍要求原有行对象约定和稳定重写。
`2**-39` 系数或界差异必须被拒绝。求解点沿既有原空间分量容差独立核验，
不要求浮点等式成为精确有理等式。

公开入口：`read_lp_model(path)`、`parse_lp(text)`、`write_lp_model(model,path)`、
`model_to_lp(model)`；CLI `optimize` 识别 `.lp`/`--format lp`。
`silo convert INPUT --output OUTPUT` 按 `.json/.mps/.lp` 转换，不求解；
auto 转换拒绝未知输入后缀，显式 --format 可指定未知输入后缀。
未知输出后缀与输入输出同一路径拒绝。先完成序列化再写出。
`optimize --output` 保持解 JSON schema2，原其他命令不变。

冻结与复现入口（仓库根目录）：

```text
python -m scripts.reliability.freeze
python -m scripts.reliability.accept --formats
python -m scripts.reliability.accept --solve --output OUTPUT
python -m scripts.reliability.external --output OUTPUT
python -m scripts.reliability.artifacts --output OUTPUT
```

这些运行有合同次数上限；实际本地执行通过 `scripts.reliability.runtime` 分类记账。
固定接受集不会注册为 pytest 参数；开发单测使用独立手写微例。
