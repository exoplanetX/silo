# 五模块原型正确性修订执行报告

合同：[20261024-01-01](../codex/20261024-01-01_prototype-correctness-revision.md)。
计划：[有界修订](../phases/prototype_revision_20261024.md)。本轮一项维护任务，R1–R3内部检查点。

## 当前状态

R1/R2已实现并通过固定回归，R3四个隔离安装已通过。验收5的完整质量聚合命令收据待预算裁决，
其余必要结果已具体交付。发行提交0a5512018db1f320789e489deec5cc9c3d18abdc，
实际源码基线4ca4bab47f2eecb8b60d5e34e767b4dc239fd969，分支codex/teaching-research-prototype。
用户在讨论对话直接授权四项修订及候选重验；按单合同连续完成，不沿用旧总目标自动授权。
推荐GPT-6 Sol/high，未声称切换。内存检索无SILO命中，未使用记忆推断项目事实。

## 启动与冻结

已读AGENTS、tasks/README、mirror、合同/计划/审查、案例与learning规则。
修订输入配方在scripts/prototype/revision_cases.py；targeted manifest在算法改动前冻结。
原outputs/audit_20261024、outputs/prototype及旧64消耗保持只读。
新计算账本/结果限定outputs/prototype_revision_20261024，计算上限3600秒。
调用上限：targeted128，384矩阵2轮，旧288矩阵2轮，完整质量3次，四安装各最多1次环境重试。

## R1 / R2 / R3

- R1：数学整数值统一保留精度；直接/派生非零下溢显式拒绝。139新增与62历史MPS测试通过，
  仅1次公开solve。写入器保留可表示大float、subnormal及整数端点一致往返。
- R2a：两处目标剪枝严格比较node.bound>=incumbent，不引用primal或objective容差。
  18个最优变形与四类限额通过；原active/open/unresolved、cut和研究回调语义保留。
- R2b：有限池任一实际binary负rc增列；全池最优须精确原始可行对P=D、所有侧符号/列rc成立。
  候选来源为raw、有限分母与现有basis精确方程，不调用外部solver。已入列负rc触发更严LP dual工作，
  presolve证明失败可在同一20轮内无presolve重求。证明/时间/枢轴共享预算；失败保留incumbent且无有限全池界。
  不可表示有理目标的P/D分别向外包络。-10000例、解析无界例、1/3原始精确可行对及篡改拒绝通过。
- R3固定新矩阵：seed20261024，输入字节SHA4df0fbec29dc7afd7df66872d395bd5c52e7f31155c6c28e642050483383ddad，
  192模型×2配置384调用、192直接HiGHS、48纯IP穷举通过；一轮4.424秒。
  旧192小例+24边界+72规模通过，两公开例正确，计289记录/296原生调用、31.292秒。
  64旧诊断只复核保存输出，新求解0次，3.290秒。旧输入、旧输出和旧账本不变。
- 全量pytest6327项通过（22.28秒）。首次check_quality.py尾部Ruff发现本轮新冻结配方六处行长问题；
  仅格式修正，已与冻结提交逐AST、生成合同及manifest核对完全一致。
  首次格式化仍留一处长SHA文字，拆分相邻字面量后同范围全仓Ruff通过。失败日志全部保留。
  本轮全量测试已通过，格式修订未改变任何AST或生成输入；质量收尾仅重验失败的Ruff步骤。
  不将首次脚本exit1改写为exit0，不重复6327项或隐藏额外调用。
- 初轮针对性34调用30通过/4失败，原因是精确分数字符串发布误用float；修正Fraction解析后仅重跑四例通过。
  精确证明扩展后74/75通过，唯一失败是模拟clock与ProofBudget真实clock不一致；贯通同一clock后该测试通过。
  scoped lint发现的未用import/行长及probe准备E741均修正并保留原记录；未放宽数值容差或预期答案。
- L0011/L0013/L0014相关原理、反例、代码映射与练习已修订，v0.2.0按
  f488189bd5835d9b1b4c7d0319b847a1671da1d1登记checked；全量检查对应源码未变。
  L0012教学内容和原核验元信息保留。新增LP helper只重建原始basis的Bx=b、B^T*pi=cB候选；
  ProofLimitError仅区分证明超限与坏输入，保持既有ValueError捕获兼容，不扩张LP算法。

## 安装候选与来源

源码提交f488189bd5835d9b1b4c7d0319b847a1671da1d1，版本0.2.0a2，构建后未改变任何生产模块。
冻结输入先行提交ffc534a45df0752a02d5401300bc88a0356b40c2；该配方后续仅格式化，
全部AST、生成input_contract与manifest完全相同，实际旧/新SHA在新账本逐事件保留。

| 新工件 | SHA256 |
|---|---|
| dist/prototype/revision-a2-20261024-01/silo_solver-0.2.0a2-py3-none-any.whl | bf87d1799b7a660c5f8480669579a2e1de4f23d69015e1334580d5d99c970cc0 |
| dist/prototype/revision-a2-20261024-01/silo_solver-0.2.0a2.tar.gz | c63f3e6bea5d26a463e6d1bf41ede53c7f46f2e29f4dbd415ce50632430ab4c4 |

工件来自git archive的干净提交快照；各120个Python模块原始字节匹配Git blob。
工作区7模块为CRLF、归档为LF，逐文件双SHA及严格LF相等保留；没有其他差异。
首次构建前严格raw门因这项运输差异停止，未创建环境/运行修复调用，1.4522784秒及失败输出保留。
判据改为工件raw匹配提交、工作区仅接受这7项纯EOL运输映射后继续，未改源码。
外部checker的canonical SHA=89fbf31aee6576614457104b019c7687cb5f4296e68a3de5236d8d643d3d9f26；
worktree CRLF SHA=04c53697010e3454c2ee5b86bab728508965804f9494505cb25df614ef92e2ef，LF相同。

| 环境/工件 | Python | NumPy | API/CLI/研究例/修复调用/F4拒绝 | 状态 |
|---|---|---|---|---|
| py311-wheel | 3.11.15 | 2.4.6 | 3/4/2/5/6 | PASS |
| py311-sdist | 3.11.15 | 2.4.6 | 3/4/2/5/6 | PASS |
| py313-wheel | 3.13.9 | 2.5.4 | 3/4/2/5/6 | PASS |
| py313-sdist | 3.13.9 | 2.5.4 | 3/4/2/5/6 | PASS |

均在源码树外全新venv以-I执行，直接archive SHA与direct_url一致，全部silo模块来自site-packages，
SciPy未安装、未导入。各组合首轮成功，环境重试0；四个checker实际20修复调用、24次F4解析拒绝。
每组F1返回±.01；F2有界例返回-10000，精确P=D且公共dual=-10000.000000000002安全包络。
解析无界例实际返回numerical_failure/original_kkt_failed，保留-10000000可行incumbent、dual=None；
这是合同允许的保守退出，没有发布有限最优或声称已识别无界。

完整收据在outputs/prototype_revision_20261024/installation/final-summary.json及attempt-02/commands.json。
实际wrapper合计107.042756秒，含首次失败1.4522784和成功105.5904776；连准备/来源核验保守计110秒，
首次失败只计一次。所有环境和失败日志保留，旧0.2.0a1工件SHA不变。

## 逐项验收与剩余动作

| 合同项 | 当前证据 | 执行判断 |
|---|---|---|
| 1 F1–F4固定反例及变形 | 139 MPS新测试、34冻结求解案例及7项精确门回归均在6327全量通过 | PASS |
| 2 界/差距、全池精确与预算 | min/max/常数/尺度、限额、原历史回调/Phase I、精确P=D及1/3包络通过 | PASS |
| 3 历史回归与新独立矩阵 | 6327测试、384原生、192直接HiGHS、48整数穷举通过 | PASS |
| 4 旧288、公开集成、保存64诊断 | 一轮288+两例通过，64输出只读复核通过 | PASS |
| 5 索引、结构、完整质量命令 | --write-index已执行；结构/6327 pytest及末次同范围Ruff分别通过；首次聚合exit1尚无整条exit0 | HOLD |
| 6 四个独立安装与工件来源 | 四组合首轮通过、120模块Git raw身份及运输映射记录 | PASS |
| 7 伴学与匹配报告 | 三篇v0.2.0实际checked，L0012未虚刷；本报告记录全部失败与限制 | PASS |
| 8 允许范围、两治理哈希与不push | 源码f488189仅允许文件，两治理原hash保持，未push | PASS |

目前不声明合同八项全部成功。验收5需完整check_quality.py exit0；同范围Ruff恢复通过及AST/输入等价性
不被写成第二次全量测试或聚合命令成功。当前严格重复计数108/128，再整套增加36将达144；
已向用户请求本单仅提高调用上限至144，60分钟总时间及其他上限保持，等待明确答复。

## 调用、时间与独立复核

| 预算项 | 本轮实际/严格重复计数 | 原上限 |
|---|---|---|
| F1/F2冻结回归首轮 | 34，含4次序列化失败 | 计入128 |
| 只重跑失败F2 | 4 | 计入128 |
| R1 MPS gate | 1 | 计入128 |
| R2 F2/limit复验 | 12 | 计入128 |
| 新增1/3 basis例定向核验 | 1 | 计入128 |
| 完整质量中的新修复调用 | 36 | 计入128 |
| 四安装新修复调用 | 20 | 计入128 |
| 严格合计 | 108 | 128 |
| 新384矩阵 | 1轮 | 2轮 |
| 旧288矩阵 | 1轮 | 2轮 |
| 完整质量 | 1次，聚合exit1；后续Ruff单步恢复通过 | 3次 |
| 四安装环境重试 | 各0 | 每组合1 |
| 全部自动验证 | 保守195秒，含失败/准备/安装/5秒收尾余量 | 3600秒 |

账本outputs/prototype_revision_20261024/ledger.jsonl是新的append-only SHA链。
针对性计数按本轮新修复root solve/column_generation调用计，包含全量和安装中的重复；
历史单元测试、两个固定矩阵与公开集成另记其次数，不把128写成所有历史求解调用总数。
旧outputs/prototype/run_ledger.json仍为64诊断已消耗，SHA
50289becc8d3072eef8dae758c800e7008506fccafd2828989fe4f99c2d15f6b未变。
旧freeze_manifest/oracles/manifest/model_contract及0.2.0a1两工件均通过原SHA核对。

理论服务只读核对F1下界职责、全池弱对偶、basis方向/翻转/常数及presolve候选的原始核验。
窄复核提出有理primal界向上包络和有限proposal重复打分的预算旁路，两处均已修正并在6327测试中验证。
该服务未运行实验，不算另一条算法证据。证据服务只读确认当前组成步骤不等于整条命令exit0；
其审阅时旧报告尚未登记索引与安装，但实际--write-index收据和四安装现已单列。
验收5保持HOLD，不由开发者或服务自行改成PASS。

## Git 与权限

- 启动cached origin/main...HEAD=0/45；未实时查询远端。
- local-commit；push not_attempted，remote_sync_status=dirty_worktree。
- 代码提交f488189，收尾前cached origin/main...HEAD=0/47；无live lookup。
  收尾后实际status/branch/last5/ahead-behind保存outputs/prototype_revision_20261024/final_git_receipt.json。
- 收尾前last5依次f488189bd5835d9b1b4c7d0319b847a1671da1d1、
  ffc534a45df0752a02d5401300bc88a0356b40c2、0a5512018db1f320789e489deec5cc9c3d18abdc、
  4ca4bab47f2eecb8b60d5e34e767b4dc239fd969、f78b412（完整历史见final_git_receipt）。
- 原有AGENTS.md修改和根案例通告未跟踪原样保留、排除暂存。
- 原AGENTS SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638。
- 根案例通告SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
- 报告最后提交按git log -1 --format=%H -- 本报告路径定位，避免自引用。
- 原研究A/B已验收、C HOLD、D/E未开始；native延期及远端CI pending保持。

## 当前交付线

修复与可安装候选已交付；本单7项有通过依据，验收5仍HOLD，未宣称合同成功或最终GO。
等待用户对额外16次调用上限的明确答复；未获得前不运行完整质量第二次，也不启动其他开发任务。
若授权，只补同一单的完整质量命令与其实际收据，保留所有旧失败和原研究状态。
