# 单元A执行报告：整数资源DAG冷定价

## 结果与原目标覆盖

[合同](../codex/20261020-04-01_resource-dag-pricing.md)20261020-04-01，L2、
local-commit，执行自检合格，提交后停止待讨论对话独立验收。本单补原3的
非负整数可加资源冷基线，保持有限DAG和原研究主线。资源CG、时间窗/访问记忆、
原5真实应用门控、原6增量状态及原7完整计算价值均未完成。本单没有性能或创新结论。
本轮A第一次交付；未消费一次针对性修正额度，也不自行启动B。

## 起点、授权及提交身份

- 起点签发提交792b2260ca963ead196b4cca80c767d0bcbb7d94，main；cached 0/25。
- 已核验用户有界A–E协调授权及接受已登记本地状态；执行范围按本合同。
- 实现A：be03540db4f966a6c98f71e41d9025b08ddd7555，含新模块、4项导出、
  两类测试和运行例。原src/tests/examples基线f4cc36e的既有模块保持原字节。
- 学习/文档收尾提交B用以下实际路径定位，避免预填自身未来哈希：
  `git log -1 --format=%H -- tasks/reports/20261020-04-01_resource-dag-pricing_report.md`。
- 仅调用本次commit身份参数，未修改Git全局/本地配置。未push，未查询即时远端。

## 允许范围与实际变更

| 路径 | 实际作用 |
|---|---|
| src/silo/decomposition/resource_dag_pricing.py | 新冻结问题/结果、5种状态及完整资源冷DP |
| src/silo/decomposition/__init__.py | 仅新增4项公开导出 |
| tests/unit/test_resource_dag_pricing.py | 72项边界、输入、快照、预算和数值核验 |
| tests/verification/test_resource_dag_pricing_oracles.py | 1152项原始数据DFS/Fraction真值 |
| examples/resource_dag_pricing.py | 单双资源手例与预算断言 |
| docs/resource_dag_pricing.md | 新API、计数、数值语义和支持域 |
| docs/README.md | 导航 |
| docs/development_layout.md | 新入口与真实支持范围 |
| learning/lessons/L0009-resource-dag-pricing/README.md | 十节正文、充分性/递推、完整运行程序 |
| learning/lessons/L0009-resource-dag-pricing/exercises.md | 八道稳定编号练习 |
| learning/lessons/L0009-resource-dag-pricing/solutions.md | 八道解答及实际核验对应 |
| learning/CATALOG.md | 新篇与资源专题阅读顺序 |
| learning/GLOSSARY.md | 充分资源状态、冷资源定价与预算术语 |
| .silo-dos/project_profile.md | A实际状态/证据、B及原研究剩余义务 |
| 本报告 | 执行记忆 |
| tasks/INDEX.md | 仅脚本生成 |

未修改旧定价/CG/恢复/RMP/LP/core、旧测试/学习篇、研究资产、规则、ROADMAP、
native、依赖、build、CLI/schema；两项治理文件原样保留，未暂存。

## 实现、预算与数值

问题组合既有DagPricingProblem。容量/弧资源必须为严格非负整数tuple，维数可为0，
所有弧显式提供资源；键、维数及输入数值先验证，资源映射复制后只读。
每次重算弧约化权重和源状态，按稳定拓扑/资源tuple/弧ID序，仅同完整状态保留
最低(label,完整路径tuple)。汇停止展开；不做资源支配、全路径枚举或跨对偶缓存。

完成搜索后，从原始路径独立重构成本、所有声明行、rc及整数资源，核对连通/端点/
逐步容量/终态资源。失败均候选空、is_improving/resource_usage=None。
所选列数值保护与旧普通DAG一致：非有限、重构差>1e-9、跨用户改善阈值则数值失败。
检查无法发现已因舍入丢弃的其他路径，任意尺度实数最优与规范平局没有保证。

手算例成功b,c成本/rc=1、资源(1,)，4状态/4转移。状态预算3触发STATE_LIMIT：3/3；
转移预算3触发TRANSITION_LIMIT：4/3，已有汇仍清空候选。恰好4/4正常完成。
同完整状态标签替换不额外吃状态预算，资源不可行弧尝试计转移，源/汇/死路计状态。
全弧预计算失败0/0；这些计数不覆盖验证、预计算、拓扑、排序、路径复制和重构总成本。
超过2^53及2^100的整数边界实际核对，资源从未转为float。

零维、汇无出弧且充分预算的正常同域族逐字段核对普通price_dag。
汇后分支不展开，因此该部分极端数值诊断可以不同；s-t路径域保持。

## 独立真值及实际检查

固定64子图、原编号六弧、3资源配置、3 dyadic对偶及2种输入表示：
1152次定价，按一个调用一个pytest项组织。独立DFS直接从公开原始弧列出完整路径，
以独立整数求和筛资源，以Fraction精确输入浮点值重算列和rc，检查真正最优集及
完整弧tuple规范平局；不调用生产拓扑、转移、重构、数值helper。另72项unit，
因此新增1224项。不能把1152调用说成1152不同物理图或应用实例。

| 命令/核验 | 实际结果 |
|---|---|
| 启动前check_quality，补.venv/Scripts到本进程PATH | 4075 passed in 15.13s，结构/Ruff通过 |
| 初次新测试 | 1222 passed in 1.16s；当时Ruff有6处格式/zip声明错误 |
| 修正导入排序、长行及显式zip(strict=True)，补自然消减及缺对偶行用例 | 新测试1224 passed in 1.20s，Ruff通过 |
| python examples/resource_dag_pricing.py | b,c成本1、资源1、4/4及双资源(1,2)、两种LIMIT断言通过 |
| check_project_structure.py --write-index | 已生成索引；收尾新增报告后再生成 |
| 补PATH后scripts/check_quality.py | 5299 passed in 15.87s，Ruff及结构通过 |
| L0009正文Python围栏实际提取执行 | 单双资源程序通过；另核对E06等号/改善阈值 |
| L0009八道解答 | 手算/双资源/对偶切换/预算映射到原生例和unit；推导与研究辨析按声明条件核对 |
| 实现阶段git diff --check及cached --check | 通过 |

全量通过后生产/测试/例子未再改；文档收尾仅做结构、链接、UTF-8、围栏、
公式配对、verified_code与提交内容核对及diff检查，不重复全量测试。
L0009按真实实现哈希be03540核验，讲解v0.1.0/checked；没有把签发或文档提交当代码基线。
收尾结构为149 contracts/146 reports/101 modules/511 local links；受影响Markdown
相对链接、UTF-8、代码与公式围栏配对及verified_code核对通过。
讨论对话收尾前指出复杂度措辞需限定维数，已在本次教学交付内改为“q固定时按容量数值
可称伪多项式；q随输入增长时B_j=1也可能有2^q种组合”。未增加算法、实验或修正轮次。

签发方已登记不可变合同EOF多一空行的非阻断格式债。本单保留该合同原字节；
执行工作区及自身暂存变更检查通过。未掩盖/重发合同，未发生范围外修复。
本单无性能实验、无新依赖、无弱化/跳过旧测试。

## Git与Remote Sync Proof

执行开始与收尾保留同样两项治理变动：

```text
 M AGENTS.md
?? 研究主题固定_严重反面案例通告_20261020.md
```

SHA256分别：
`2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638`、
`0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221`。
实现后观察main、cached origin/main...HEAD=0/26；收尾提交后的即时proof由终端及交付
摘要给出，不将缓存引用说成已查询即时远端。branch/status/log5/cached差异均实际核对。

实现后log5：be03540、792b226、77c62bb、66378eb、21a19f2。
git push result=not_attempted；remote_sync_status=dirty_worktree，用户已批准保留。
提交后只剩上述已知治理变动，不把已知ahead或脏文件误报同步/clean。

## 停止与下一门槛

本单资源子类工程交付自检合格，执行到合同预置停止点。待silo-solver-1010独立审查；
仅其验收通过并交付B合同后，才能执行资源参考CG。本单不自动继续、不发送跨对话消息。
真实应用/完整资源状态与强基线联合证据仍缺，原5/6/7保持未完成。
原研究主题及收尾计划最多五项、C未通过即停、修正次数/预算保持，不追加第六项。
