# 五模块原型正确性修订执行报告

合同：[20261024-01-01](../codex/20261024-01-01_prototype-correctness-revision.md)。
计划：[有界修订](../phases/prototype_revision_20261024.md)。本轮一项维护任务，R1–R3内部检查点。

## 当前状态

R1/R2已实现并通过固定回归，R3等待四个新隔离安装。发行提交0a5512018db1f320789e489deec5cc9c3d18abdc，
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
- L0011/L0013/L0014相关原理、反例、代码映射与练习已修订；待正式代码提交后登记核验基线。
  L0012教学内容和原核验元信息保留。新增LP helper只重建原始basis的Bx=b、B^T*pi=cB候选；
  ProofLimitError仅区分证明超限与坏输入，保持既有ValueError捕获兼容，不扩张LP算法。

## Git 与权限

- 启动cached origin/main...HEAD=0/45；未实时查询远端。
- local-commit；push not_attempted，remote_sync_status=dirty_worktree。
- 原有AGENTS.md修改和根案例通告未跟踪原样保留、排除暂存。
- 原AGENTS SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638。
- 根案例通告SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
- 报告最后提交按git log -1 --format=%H -- 本报告路径定位，避免自引用。
- 原研究A/B已验收、C HOLD、D/E未开始；native延期及远端CI pending保持。
