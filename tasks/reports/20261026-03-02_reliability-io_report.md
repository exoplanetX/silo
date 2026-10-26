# 20261026-03-02｜R4跨环境回归、资源守卫与真实CI收口

**结论：本地修复和验收通过，首次push传输失败，R4 HOLD；overall_complete=false。**
当前修复尚未到达远端，实际CI尝试0，13-job/16安装/24外部读仍未取得。
按[RR02合同](../codex/20261026-03-02_reliability-io.md)§7停止网络路径，不自动重试推送。

## 1. 授权、基线与保护边界

用户在silo-solver-1010直接消息01a176fc-3f14-7db0-a4e0-7d19ad7f0d15要求仅收口R4、处理剩余问题并交付执行；
主线程实际读取核对了该消息。原[03-01报告](20261026-03-01_reliability-io_report.md)、
[原规划](../phases/reliability_io_20261026.md)和全部旧输出只读，原HOLD及费用不回写。
执行沿用silo-development-operator流程；风险L2资源/测试、L3有界CI，未切换模型。

| 身份 | 实际值 |
|---|---|
| 实际签发起点 | 6a9b5c050b054cbd6b90461a3249dbadf719aa3b |
| 分支 | codex/sparse-lp-reoptimization |
| 原生产身份/候选 | 42892035db426c4739b6c1a7ad9648852d2b1dc8 / 0.3.0a2 |
| R1冻结 | f8f00fd60728e0e9314342a3b4e037cfee50f790 |
| 修复提交 | 1473f2a6b1605cc93345073c5d261406b51f9c61 |
| 最终本地候选（教学元信息修正） | 4bff443be50a709560a04211994881e57897f883 |
| 生产LF来源SHA | d551b7e90e7a3ac5c82dafb86ad5397c55739f74b27ccb369b1e02333df902dd |
| 原R1 manifest SHA | 2fa296f567a96af88796bf0c392830c29740cfc44ea2cd290880a9d03e5a4291 |

全部128个生产模块、版本/生产依赖、输入、真值、I/O、求解容差/算法与schema保持。
没有重跑160接受组、旧sparse fixed/warm/summary、旧Goal，也没有Goal API创建/更新。
旧C HOLD、D/E未开始、native与规模/结构拓展延期；OneDrive保持退出，不操作用户进程/电源/全局环境。
测试守卫仅回收其自己创建的子进程；子进程console-script PATH和BLAS/OMP/MKL线程1保持。

## 2. CG修复与实际数学核验

原自然例在Python3.10的失败是返回path_1=.2500000000000001，测试固定期望.25000000000000006。
两实际二进制有理数相差2^-54≈5.551115123125783e-17；具体尾数产生步骤未被证明，不归因某个唯一依赖。

本次保持原自然问题、全部原始数据和Fraction(-7,4)最优真值；`_audit_round`原样保留。
测试委托真实RestrictedMasterProblem.solve，捕获它发布给CG前的不可变结果及权重副本，
核对每轮记录引用同一对象且权重未改写；对每轮直接DFS全DAG列并用实际x/pi重算：

- 原空间行活动/非负性、目标与精确dual shift，原1e-9门保持；
- fsum上下界、有符号gap、rho及32*ulp绝对贡献和；
- 终态rho>=-1e-9且objective_gap<=1e-9；仅负gap才要求-g<=eta<=1e-9及roundoff消息。

移除了特定尾数和“自然例必然负gap”的绑定，没有使用宽泛approx，也没有改生产结果或钳零。
既有`test_dag_column_generation.py`未修改并已完整实际执行，覆盖负gap inside/equal/outside/equal_budget/over_budget、
正gap阈值下/等/上、大常数冲突及零绝对尺度等确定性分支。

定向local4实际598 passed。其独立运输族432次全为tolerance_reached、646迭代，216/216两backend；
其中113个负gap记录按原门核对。自然例实际权重仍.75/.25000000000000006，
上下界−1.7500000000000002/−1.75、有符号gap−2.220446049250313e-16、eta5.684341886080802e-14。
这是一条实际本地轨迹；跨原远端矩阵尚待执行。

## 3. RSS修复与清理边界

Linux新增小型VmHWM文本解析，区分有效kB换算、无字段、文件消失、畸形/重复/错误单位及读取错误。
无字段返回None；原VmRSS不冒充峰值。缺测保留先前真实peak，继续检查同一个绝对deadline。
从未有有效样本时peak_rss_bytes=null、memory_verification_valid=false，退出时明确harness_rss_unmeasured；
缺测过程中到deadline仍终止，报告harness_timeout与独立unmeasured状态，不写成solver limit。

采样循环异常保留主错误并清理自建直接子进程。Linux保持root范围；Windows保持CTypes峰值和原root/descendants树遍历。
独立复核发现原taskkill非零返回后wait可能卡住，已修为树清理后若直接子进程仍存活，先kill再wait；
树清理异常也有直接子进程回收后备。空Windows树没有真实样本时同样不当成有效0。

新定向回归覆盖：有效/缺字段/畸形值；首次缺测后恢复；退出/文件消失保留峰值和实际退出码；
持续缺测的deadline；原RSS超限；解析/权限/意外异常时回收且保留主错误；taskkill返回0/1但子进程仍活着；
真实自建子进程异常回收和当前平台真实OS峰值。注入用例在Windows实际运行，Linux真实/proc路径待远端运行。
原normal/timeout/rss、Windows后代树和句柄回归保持并在本地通过。

| resources身份 | SHA256 |
|---|---|
| 旧工具（旧签收/driver map） | ec3b18199d66ae614643201344898a8026d1c1f0ca0c7914fe82de983708c23c |
| 本修订新工具 | c35f219c8b6aec02b1f9328ba08797d7d96154a5b1f5f39df71f0818c20abc7a |

旧manifest/driver map/收据未改；新工具不被写成旧RR08身份。旧CI缺字段的确切生命周期原因仍未证明。

## 4. 检查、失败与来源复核

新证据根outputs/reliability_io_r4_20261026，ledger.jsonl只写新账；旧runtime.run/append未调用。

| 检查 | 实际结果 |
|---|---|
| local1 初始CG/RSS/边界 | 579 passed |
| local2/3 Ruff | 各1处行长失败保留；已修正，最终完整Ruff通过 |
| local4 最终定向组 | 598 passed，含新工具边界与E09二进制差核对 |
| local5 结构与索引 | 165合同/162报告/128模块/633本地链接通过 |
| local6 prototype/evidence.py --verify | 264原始案例/24边界、native_solver_calls=0、写入0 |
| local7 reliability.freeze | 原32模型+4编辑状态重核、SILO请求0 |
| quality1 | 6770 passed/2 failed：L0016版本与不可变网页提纲不匹配 |
| quality2 | **6772 passed、exit0；pytest33.03秒，完整34.689秒，结构/Ruff通过** |
| identity1/2 | 源码/冻结/允许diff/保护文件/旧报告与旧证据均通过，四安装eligible=true |

首次完整质量的两失败由本轮更新L0016版本号引起；恢复原0.1.0并将R4作为单列增补，
不改网页提纲/代码或旧教学verified_code/on，第二次完整质量全通过。两次原始日志均保留。
独立只读r4_repair_review对CG/资源/身份/矩阵完成源码审查；提出的taskkill缺口修复后获针对ACK。
它未执行新测试/安装或写文件；其最终结论是源码block消除、远端未达仍HOLD，不能作为13-job通过。

## 5. 工件沿用、实际推送和未运行CI

identity2逐128生产文件核raw与严格CRLF/LF；原03-01报告SHA47989a6252dfb8ba16bb5dd512afdccefc8b0defcaa5fc391d707ae8da886132不变；
720个旧输出文件逐哈希保持。原四环境报告/direct_url/全部已载入模块与实际环境文件一致。
当前checker SHA61e5a2c8717b81305f818fe8bff70d09014cceacca6252ef3cae0958dbedc30d，和旧验收相同，故原四安装可沿用。
本修订没有改artifact/install/external checker，没有新构建、安装或外部读取，也没有新160组。

| 沿用工件 | SHA256 |
|---|---|
| wheel | 28873f4d557ec3b63319b84db9ee51c2aa4482c972b4d8223e3c0f26f4f3e5a9 |
| sdist | d6d233ea736ff2fb3fe0018a0b271e88bdfb334f30a7b036b4894fdc01d255f8 |

CI配置仍为4质量+8安装+1外部解析，不减平台/步骤或新增skip。
增加完整历史获取和R4身份静态收据，以便干净checkout从Git复核4289203/冻结/签发来源；不依赖本机旧outputs。
该配置尚未在新SHA上实际执行，不能把它或本地结果当作远端通过。

RR02首次且唯一实际push：git push origin HEAD:refs/heads/codex/sparse-lp-reoptimization。
本地候选4bff443be50a709560a04211994881e57897f883；推送前本地必需门均通过，远端祖先关系正确。
命令20.116秒后exit128：`Recv failure: Connection was reset`。
只读GitHub refs API确认远端仍42892035db426c4739b6c1a7ad9648852d2b1dc8；按新SHA查询Actions列表为空。
**新增CI尝试0；13/13 job、16/16安装、24/24外部读均尚未取得**，没有run URL或工件报告可签收。
原[失败run40261995554](https://github.com/exoplanetX/silo/actions/runs/40261995554)及其355 runner秒仍属03-01历史，不算本次CI。

合同§7明确推送传输失败后保留本地、不自动重试。虽然第二额度未用，它只服务获准的集中修正/同SHA基础设施CI重试，
不能绕过传输失败停止条件。本次未第二次push、未改目标、未force、未建立凭据或以API写入绕行。
网络复位的唯一底层原因未证明；只读API成功不代表Git推送传输已通畅。

## 6. 伴学、预算和完成判定

L0016新增核验说明及E09辨析：数学不变量与尾数、自然集成与确定性边界、缺测与真实超限；
原verified_code/on、网页版本和八组教学小例身份保持。新增内容实际核验身份4bff443、日期2026-10-26，
E09由本轮定向/完整测试实际核对；旧八组小例未重跑或冒充新增结果。

| 费用/次数 | 03-01已发生 | RR02新增 | 当前累计/限制 |
|---|---:|---:|---|
| 本地自动核验等秒 | 325.5752395 | 收尾检查后114.068685 | 分开账本；RR02上限1800秒，最终精确值见end_git.json |
| 定向/局部检查批 | 19 | 9 | 累计28；RR02≤12 |
| 完整quality | 2 | 2 | 累计4；RR02的2次已用满 |
| 静态身份核对 | 原账 | 3 | RR02≤3，已完成 |
| 代码/config push | 1成功 | 1传输失败 | 累计2次尝试；RR02未用第二次，传输失败即停 |
| 实际CI尝试 | 1失败 | 0 | 累计1；RR02最多2，未启动不记通过 |
| runner秒 | 355 | 0 | RR02≤420分钟 |
| 新构建/四安装/外部解析/160组 | 原报告 | 0/0/0/0 | 仅沿用已核对的原证据 |

未覆盖完成线：新修复的跨原矩阵自然CG与Linux实际状态验证、13实际成功job、16工件核验及24外部解析。
本地修复/质量/身份成立与R4远端验收分开，故原任务整体仍overall_complete=false，R1–R3维持通过。
后续最小路径是另行明确同步授权后，对当前有界修复运行原矩阵；不需要据当前证据先改生产算法或重跑160组。
本轮不签发下一任务、不继续同步。若安排后续复杂一致性核对，仍建议GPT-6 Sol/high，不据此声称已切换模型。

## 7. Remote Sync Proof与交付

- 起点6a9b5c0，git status仅两项已登记治理差异，缓存origin/main比较0/105。
- 分支codex/sparse-lp-reoptimization；本地代码/测试候选4bff443，远端任务分支仍4289203。
- git push result=failed（exit128，HTTPS连接重置），RR02实际尝试1；没有自动重试。
- main实际仍f0c5f317b8b7c2550ac574e8f27616df7b247dff，未创建PR/merge/tag/Release/PyPI或改变权限。
- 最终报告/状态提交local-only；报告提交用git log -1 --format=%H -- 本报告路径定位，不自引用SHA。
- 最终HEAD/最近5提交、缓存main与实际任务分支ahead/behind、预算和本报告SHA在end_git.json。
- remote_sync_status=dirty_worktree（仅接受的两治理差异）；同步失败事实另列push_failed，不冒充远端或main同步。
- AGENTS.md保护SHA2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638。
- 根通告保护SHA0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。

最终identity3记录旧证据/所有生产/保护哈希与允许diff；旧720文件继续不变，四安装沿用eligible=true。
收尾结构检查为165合同/162报告/128模块/635本地链接通过，工作台26项通过；已使用、未用额度和所有失败保留。
本轮以R4 HOLD的明确未达交付结束，没有自动排队的推送、CI、实验或下一任务。
