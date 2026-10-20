# 单元B执行报告：资源路径凸组合参考列生成

## 结果与完成边界

[合同20261020-05-01](../codex/20261020-05-01_resource-dag-cg.md)，L2、local-commit。
新资源CG入口、类型化结果、逐轮证据、独立真值、L0010及报告自检合格，交付后停止待
讨论对话验收。本单属于原4，在非负整数可加资源DAG、连续lambda及全局sum(lambda)=1
的参考模型内补齐闭环。真实多路径覆盖/分割、时间窗/访问记忆、资源可行性恢复、
原5联合应用证据、原6跨对偶定价维护及原7完整成本评价仍未完成。
B正确实现没有创新或加速结论；不把RMP warm等同增量定价，不把教学对偶当真实应用。

本次首次交付，未使用一次针对性修正额度，不自行签发或执行C。
既定最多五项、C未通过即停及原研究主题/完成标准保持。

## 实际起点与提交

- 合同签发52a4de025baa9e23e468c494775abc15690b8960，main、cached origin/main...HEAD=0/29。
  A验收414638a9c6ea703c883a4572ce23fa37e311b64f。
- 人类已批准A–E有界协调，继续接受已登记本地提交及两治理文件状态；不重复索要授权。
- 实现6858a736568a6d502271acf39d29f855def65b93：新模块/3项导出、unit、oracle及原生例。
- 文档/学习/报告提交用
  `git log -1 --format=%H -- tasks/reports/20261020-05-01_resource-dag-cg_report.md`
  定位，避免自指未来哈希。
- Git仅用单次commit身份参数，未改配置，未push，未查询即时远端。

## 16个允许交付路径

| 路径 | 实际作用 |
|---|---|
| src/silo/decomposition/resource_dag_column_generation.py | 新控制器及冻结iteration/result |
| src/silo/decomposition/__init__.py | 仅追加3项公开导出 |
| tests/unit/test_resource_dag_column_generation.py | 66项边界、预算、输入、历史、数值及真实接线核验 |
| tests/verification/test_resource_dag_column_generation_oracles.py | 72模型×3模式独立真值及实际轮数诊断 |
| examples/resource_dag_column_generation.py | 两轮手例三模式 |
| docs/resource_dag_column_generation.md | API及支持域 |
| docs/README.md | 导航 |
| docs/development_layout.md | 模块入口与参考主问题范围 |
| learning/lessons/L0010-resource-dag-cg/README.md | 十节正文、推导与完整程序 |
| learning/lessons/L0010-resource-dag-cg/exercises.md | 八题稳定编号 |
| learning/lessons/L0010-resource-dag-cg/solutions.md | 八题解答及核验映射 |
| learning/CATALOG.md | 新篇及阅读路线 |
| learning/GLOSSARY.md | 资源列域、凸性乘数平移 |
| .silo-dos/project_profile.md | B实际交付/证据及剩余义务，未标协调验收 |
| 本报告 | 执行记忆 |
| tasks/INDEX.md | 脚本生成 |

旧CG/A/RMP/LP及旧测试/学习篇/合同/报告/notes字节保持；只读复用原CG数学助手。
未更改规则、native、依赖/build、CLI/schema、ROADMAP阶段或增加通用/VRPTW能力线。

## 数学、参数与有限失败

接口组合已有CG问题与资源问题，严格要求同一graph对象。参数在任何求解前验证，
全部seed先逐弧整数核资源，再数值重构和建RMP。每次CG有fresh RMP owner；默认每轮
一次公开solve，True每轮一次公开solve_reoptimized并保存真实outcome，控制器不额外cold。
每轮给完整资源冷定价fresh预算，无跨轮资源状态缓存。

候选再次从原始图/资源映射核对路径、c/a/rc/改善分类、逐步容量和严格整数usage；
错误记录不写进类型化history，伪造列/资源保守数值失败，增列只用重构原始c/a。
资源定价非OPTIMAL一律PRICING_FAILURE，保留同轮资源诊断，但本轮P/D/rho/L/raw gap/
objective gap/allowance及accepted_path均空。所有LIMIT不代表无负列或收敛，也不重试预算。

凸性下界L=D+min(0,rho)依赖统一conv系数及RHS1；保留旧c0消去、signed gap及32ulp
局部规则，没有更改全局容差或宣称严格LP误差界。错误负的已有列拒绝，最后轮不追加未解列。
后续master/主目标失败保留前一有效已解registry；主目标通过后的定价/候选/界失败可保留
本轮有效master，界仍空。失败尝试registry和同轮真实outcome独立保存在history。

## 真值、数据与三模式实际观察

固定72模型：6成本组×3个alpha×行正反表示×输入原反序；每种运行3模式=216调用。
采用合同可选非零基项c_base=3/8、R_base=1/8，R RHS同步平移/翻符号，c0按成本组固定7/-3。
4条合法prefix加公共z资源可行，额外x成本-20但累计资源3>cap2，完整真值域排除它。
独立DFS/整数求和/Fraction重构全部列；所有两列bracketing alpha顶点给每轮当前registry
及同域全列LP真值，不以生产price/LP/另一次CG作为唯一真值。

逐轮检查MIN原始可行解、原始/对偶目标一致、列rc和x_j*rc_j≈0、完整资源最小价、
原始列、整数usage、所有数值界、接受路径、registry与终止；浮点核验绝对1e-9。
各模式按自身轨迹检查，不强求退化对偶/规范路径跨模式相同。

| 模式 | 固定调用 | CG轮数 | 公开cold | 公开opt-in | RMP内部cold | warm | fallback |
|---|---:|---:|---:|---:|---:|---:|---:|
| Revised冷 | 72 | 116 | 116 | 0 | 不另作opt-in计数 | 0 | 不适用 |
| Tableau冷 | 72 | 116 | 116 | 0 | 不另作opt-in计数 | 0 | 不适用 |
| Revised复用 | 72 | 116 | 0 | 116 | 72 | 44 | 0 |

以上为固定主族一次完整检查的实际观察；质量检查重复核验同一族，不新增应用轨迹/模型。
另66项unit包括三模式手例、真实cap、双资源、LE/GE正反行、fresh owner、字段不可变、
错误候选/record、首轮及后续失败、迭代上限、大正负c0与synthetic signed-gap。
手例三模式均P=4.5→2.5、rho=-4→0；seed lambda=(3/4,1/4)，增b后a=b=1/2。
opt-in手例观察到第二轮实际Phase II（非cold）、public opt-in两次，cold一次；复用solver
另开CG owner仍fresh cold。warm注入失败只由RMP内部cold一次回退；warm和cold均失败时
不再定价或额外重试，顶层保持旧2列，失败history保留尝试3列。

真实state_limit5中断计数5状态/6转移；transition_limit5中断5/5，两者已有汇仍失败空界。
这些是有限正确性/接线证据，没有运行时间收益统计。

## 检查、发现与修正记录

1. 初始模块Ruff发现一处签名行宽，修正。216主族初次通过(0.61s)，当时oracle有一处行宽。
2. 初版unit+oracle 278项通过(0.78s)，Ruff发现1处导入排序及4处长行，均修正。
3. 协调方提醒直接核对原/对偶目标及互补条件，已在原族每轮增加断言，不增模型或调用轴。
4. 初次诊断把空字符串fallback_reason按“非None”误计116次fallback；改为bool判据。
   最终实际为0；算法从未额外回退。该计数错误没有用于性能或研究结论。
5. 补4项seed数值/主目标历史/重复负列用例，并清理无效oracle record的类型化history。
   最终针对性282项通过(0.90s)，Ruff通过；其中unit66、verification216。
6. `python examples/resource_dag_column_generation.py`三模式输出及断言通过。
7. 补本进程PATH后运行`python scripts/check_project_structure.py --write-index`及
   `python scripts/check_quality.py`：5581 passed in17.29s，Ruff/结构通过。
8. 协调方随后独立复跑同一实现：5581 passed in17.92s，Ruff/结构通过，
   日志outputs/goal_B_acceptance_quality.log；这是复跑证据，尚不代表B最终验收。
9. L0010正文完整程序实际提取运行，三模式通过；手算及E01/E02 Fraction值另核对，
   E03–E07由相应unit实际数值/计数/接线/历史映射核对，E08按概念边界检查。
10. 文档收尾核对UTF-8、公式/代码围栏、十节/八题、相对链接、verified_code及
    scope/治理哈希；结构索引重新生成、diff检查。可执行文件自6858a73未再改，故不重复全套。

L0010 v0.1.0/checked，verified_code=6858a736568a6d502271acf39d29f855def65b93，
没有把签发或文档提交当作实现基线。首次格式问题及诊断计数修正均如实登记，
没有改旧测试/依赖/容差去通过检查。无范围偏离或额外研究任务。

## Git与Remote Sync Proof

起点、交付后两项治理状态保持：

```text
 M AGENTS.md
?? 研究主题固定_严重反面案例通告_20261020.md
```

SHA256：AGENTS.md为2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638；
根案例通告为0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
两者原字节保留且未暂存。main，实现后cached origin/main...HEAD=0/30；
收尾提交后状态/branch/log5/cached差异以即时终端和交付摘要记录，不将缓存说成即时远端。
实现后log5：6858a73、52a4de0、414638a、84e126c、be03540。
git push result=not_attempted，remote_sync_status=dirty_worktree；用户已接受该状态。
本单提交后只余上述治理变动，报告提交按路径git log定位。

## 下一门槛

本执行在B交付点停止，等待silo-solver-1010独立验收，不自行启动C或写C适配器。
原5真实应用、原6机制、原7完整计费均保持未完成；C readiness、GO/HOLD由讨论对话负责。
应用准备不足不等于VRPTW结构假设被否证；任何具体机制失败也不改原研究主题。
