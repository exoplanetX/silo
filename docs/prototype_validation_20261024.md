# 0.2.0a1 本地原型核验

本页保存固定输入上的实际结果；总任务状态与预算见
[总报告](../tasks/reports/20261023-02-01_teaching-prototype_report.md)。原研究A/B已验收、C HOLD、
D/E未启动；native Phase 9 parked。这里的工程结果分别保留自己的范围。

## 输入、环境与原始依据

输入在`2ca6098`冻结，原始数学/JSON manifest及脚本的SHA见
`scripts/prototype/evidence.py`；补充oracle从原始binary Fraction、枚举/顶点及独立DP重建。
首轮实际代码为`cc11a929189ea7cf6e8edde952640edc0f7f0090`，后续`d4c852f`只更新文档及
研究例严格JSON输出，原生算法保持相同。每个运行目录的environment记录所有src文件hash、
runner/checker hash、Python、NumPy、CPU及线程。

实际机器：Windows 11 build26300，Intel64 Family6 Model151 Stepping2，20逻辑CPU；
Python3.13.9、NumPy2.3.5；OPENBLAS/OMP/MKL线程环境均为1。固定seed20261023。
每个规模例均在独立子进程运行，LP硬墙钟20秒、MILP60秒/100000节点。

## 实际矩阵

| 分组 | 结果 | 最大变量/行 | 最慢单例墙钟 |
|---|---|---|---|
| 小LP | 96/96 | 3/3 | 0.0033秒 |
| 小MILP | 96/96 | 4/3 | 0.0302秒 |
| 固定边界 | 24/24状态与输出通过 | 以冻结输入为准 | 含两次真实CLI拒绝 |
| 规模LP | 48/48 | 196/256 | 1.354秒 |
| 规模MILP | 24/24 | 48/30 | 2.620秒 |
| 固定诊断 | 64/64，恰64次 | 8个声明模型 | 实际开关/基路径计数 |
| SciPy/HiGHS补充对照 | 192/192 | 相同小模型 | 一条外部算法证据 |

有14个最优规模LP同时达到100–200变量/100–400行。最大变量数和最大行数可来自不同实例。
规模MILP最多24个整数变量，有12个实例落在20–30整数变量区间。
首轮288项总验证30.720秒（命令30.996秒），无删除、替换、超时或答案改动。
这些构造型固定例衡量声明范围内的正确性与运行表现，不表示工业实例竞争力。

原始点、行活动值、整数性、目标、LP侧乘子/驻点/互补、Farkas、射线和MILP最终界均由
独立原始输入检查器复核。加强flag/gap代数检查后，再读全部288份输出核验通过，
没有新增求解或规模轮次。无incumbent时两种gap均为空；未知无限界保留方向。

两研究例分别复现完整四列CG值2.5及策略MILP值-8.5。CG有原始解
lambda=(0,1,0,1/2)与对偶(1/2,2)同值依据；20轮上限包含辅助LP。
固定策略例根整数，branch_rule调用0；分数根回归另行证明真实替换分支路径。

## 验证设计的明确注释

冻结B13自身根LP为整数；机器记录`fractional_point_removed=False`、`mechanism_triggered=False`。
其原输入/答案通过，GMI混合切片机制由预先登记的M3手算例单列覆盖：min x+y，
2x+y>=3、x整数，实际松弛1.5→2、排除原分数点并保留各整数切片的连续端点。
没有把手算例伪填为B13的执行轨迹。

B15实际进入dual路径且pivot=0；M2已有双变量改RHS例提供正dual pivot轨迹。
B19冻结重复basis在QR前拒绝；不同的线性相关列QR恢复见已有M2回归。
这些证据互相补齐机制类别，各自输入身份保持独立。

诊断首次在第33次结果写入时遇到无限值JSON记录错误；前33份输出保留，恢复时只补余31次。
持久ledger保留scale1与diagnostic64的身份/hash链。旧计数从真实summary/environment/output
明确导入为legacy_import，原来未记录的run UUID/issue时间保留unknown；没有伪造历史字段。
新消耗逐项记录UUID、代码/runner/checker/hash、输出目录及累积核对。

首次研究例记录同样遇到无限界序列化问题；随后严格JSON修复。机制回放又暴露记录器把
float LP值与1.5做精确相等比较的问题，改用预先冻结的目标残差准则；精确GMI推导未改。
失败目录和额外验证时间均保留，总报告计账。

## 本地证据与重现

生成物保持Git忽略，位于`outputs/prototype/validation/`：
`core`、`strict_recheck`、`diagnostics`、`external`、`integrations_v2`及`mechanisms`。
`integrations_v2`保留其中机制记录器失败；两正式集成例本身通过，最终机制通过见独立目录。
持久账本为`outputs/prototype/run_ledger.json`。wheel/sdist及四个独立环境的路径/hash见
[安装文档](installation.md)；远端Windows/Linux×3.10/3.12 CI未运行，状态pending。

新克隆上首次重现：

```text
python scripts/prototype/evidence.py --verify
python scripts/prototype/validate.py --group core --output outputs/prototype/validation/core
python scripts/prototype/validate.py --group diagnostics --output outputs/prototype/validation/diagnostics
python scripts/prototype/validate.py --group integrations --output outputs/prototype/validation/integrations
python scripts/prototype/validate.py --group external --output outputs/prototype/validation/external
```

现有运行目录和账本禁止为取得新配额而重置。`--resume`只恢复诊断已保存输出；
`--group recheck --source ...`只重新核验输出，原生调用为0。完整规模最多3轮，当前消耗1轮。
