# 教学研究通用 LP/MILP 原型整体执行报告

合同：[20261023-02-01_teaching-prototype](../codex/20261023-02-01_teaching-prototype.md)。
计划：[SILO-PROTOTYPE-20261023 v0.1](../phases/phase_10_teaching_research_prototype.md)。

## 当前终态

状态：执行中。初始化、M1和M2本地模块检查已通过，继续M3。最近完整质量5882项通过；
M2补充实际行/列缩放回归104项通过。规模/完整诊断及发行门槛统一留M5，整体原型未完成。

| 检查点 | 当前状态 | 实际证据 |
|---|---|---|
| 初始化：本次总授权登记与规格/manifest | PASS | 991c767、2ca6098及只读补充verify |
| M1 一般模型与统一输入/结果链 | PASS at local module checkpoint | 一般模型/IO/原始KKT/依据链及独立复核闭合 |
| M2 可重优化 LP 与数值基础 | PASS at local module checkpoint | 96小LP、四类真实warm、QR/数值回归；规模仍M5 |
| M3 MILP 搜索控制与 GMI branch-and-cut | pending | 尚未执行 |
| M4 公开研究接口与两个集成例 | pending | 尚未执行 |
| M5 综合验证与本地安装交付 | pending | 尚未执行 |
| 远端跨平台实测 | pending / outside local completion | 未 push、未运行远端 CI |

原研究身份：A/B 已验收；C 签发前 HOLD；D/E 未启动。本合同不计为原研究第5–7步完成。

## 规划核查与签发依据

- 主协调者核查当前 HEAD `13e748f`，保留工作台提交；对算法核心与工程/发行分别进行了只读事实核查。
- 独立规划门控给出 CONDITIONAL_GO，要求闭合五项问题：原模型 KKT/回解规格、LP 无界节点及前沿界、GMI 推导和 local 作用域、分层预算、先落授权与本地/跨平台状态分离。总计划已纳入这些条款；这不等于算法实现或实验通过。
- 用户本轮直接要求大模块计划和后续连续目标执行，总合同登记其有限范围。本次不因旧的逐原子任务模板再次逐补丁请求批准。
- 实际执行的规划检查：项目结构检查通过，151合同/148报告/102模块/524本地链接；这是添加本合同前的规划检查，签发后的数量由实际检查更新。
- 总合同签发后的结构/索引检查实际通过：152合同、149报告、102模块、527本地链接；`git diff --check` 通过。协调对话已建立本计划的唯一持续目标。
- 签发时未重跑solver测试、基准、build或干净安装；5598是历史检查身份。本次执行检查见M1–M5正文。

## 初始化与模块报告

执行者按模块逐步补充：实际代码基线、数学规格、manifest ID、文件变化、命令/结果、独立复核、计算预算、通过线覆盖和未完成义务。

### 初始化

2026-10-23，实际起点1b7deb9，分支codex/teaching-research-prototype，cached 0/34。
已只读核验讨论对话的人类原文（turn 01a16946-c96a-79b0-ac00-dec2921f3cf0），
读取总合同/计划、规则/CASE和当前mirror。未创建重复目标。按总合同先登记
tasks/README与project_profile/technical_route/standing_approval/decision_log及ROADMAP，
旧普通任务规则仍适用其他任务；本合同内M1–M5连续实施，不逐补丁签发或请示。
两治理文件哈希与签发报告一致，原字节保留且不stage。初始化期间未改solver源码。
协调方已启动只读KKT/变换复核，本执行不重复召集同一数学服务。

初始化时验证计算账为全0；当前累计见下方模块正文，总上限14400秒。
日常阅读/编辑不计验证计算；后续实际测试/build/安装命令逐次计时登记。
剩余：固定输入/KKT/变换/manifest后实施所有模块；任一模块未达线不得标PASS。

#### 编码前冻结（schema 2）

- `docs/prototype_model_contract.md`固定原始KKT、公共dual换算、变换账本、派生固定回推、
  scaling、无顶点LP的真值域、不可行/无界依据及结果语义。
- manifest=192小模型+24具体边界输入/控制参数+72规模输入，8×8诊断及两个研究例。
  `scripts/prototype/oracles.py`无生产依赖，Fraction独立小模型真值；整数域完整枚举。
- 独立审查期间schema1草稿尚未用于原生求解。发现并修正生成式的静态问题：
  一般界family目标正负不匹配构造值、运输与指派成本重复；以原矩阵内两个族覆盖派生固定
  与无顶点最优，补齐原始组合例、逐条oracle/seed/hash/操作上限和24边界具体输入。
  此为实现前防错，后续算法失败不得修改这些真值。
- 草稿SHA256=`39d96b0b15cc5506ffd57fd1b439774008d9fa345ae0d3e341f845043798b82d`；
  冻结manifest SHA256=`5b037ced206fdf349ca2524dca478a9427902ee136d0a668a449fa62af08c71e`；
  recipe SHA256=`2aa6f3609ae439a09aec4ef33b7ee865408e21c6b660d6549eb15e5df1474c70`。
- 静态检查实际0.419秒：264唯一ID/模型哈希、24边界哈希，192小模型的独立oracle域与
  预期状态一致；最大720次顶点组合（上限2000000），不含任何原生求解或规模算法运行。
  规模门槛静态满足14个100–200变量/100–400行的可解LP。此不记为模块/规模通过。
- 计入M1验证约2秒（含生成/静态/ruff）；其余模块仍0。算法实现从冻结提交之后开始。

### M1

本地模块PASS。基础代码b44e7c3，M2提交整合容差修复及补充证据；总体审查/规模线尚未到M5。

- 一般Constraint区间语义、统一solve/Options/Result、schema2 CLI optimize及python -m silo，
  JSON/free-MPS读写贯通。原始offset/T/行来源、活动界传播和逆序乘子恢复已实现。
  连续最优经原始KKT复核，不可行经精确Farkas、无界经精确原始点/射线；精确核验保持
  既有浮点数实际binary值语义，重构仅提供候选，失败不会发布确定数学结论。
- 新稠密Phase I/II revised内核及有限B&B已接通，QR/dual/warm细验归M2，GMI/前沿归M3。
  M1不以存在这些入口宣称后续模块通过。旧标准形类保留并明确拒绝区间字段，避免忽略新侧。
- 原始组合例20、派生固定行dual1/rc0、自由最优直线及12LP/12MILP基础例实际核对；
  新模型测试42项，I/O新增105项；包括直接raw输入重构KKT和API/JSON/MPS/CLI一致性。
- 实际命令：I/O首批96及102通过（0.939/0.796秒墙钟），区间优先级修正后50通过
  （0.942秒）；模型+I/O整合153通过（1.12秒pytest/1.734秒命令，新增旧入口拒绝后154）。
  首次全质量15失败/5729通过（pytest34.33秒，文件时间给命令上界36秒计账）：
  全局Model.validate提前改变旧核验错误身份。将严格有限检查放新linear_data入口后，
  受影响292项通过（pytest1.17秒/命令1.719秒），未改旧测试来接受回归。
- 修正后完整pytest **5745 passed /23.39秒**，全质量命令24.901秒；Ruff余一处行长。
  仅格式修复后全域Ruff、结构/索引及diff检查全部通过（0.699秒），无数学代码变化。
  本地日志在outputs/prototype_m1_quality*.log（忽略、不提交），没有运行72规模例。
- 独立协调侧额外3项通过（1.303秒墙钟，reserve向上记2秒），不计成模块通过。
- 伴学L0011初稿含10节、例子及3题/解答，待代码提交及复核后登记checked。
- M1验证向上累计记75秒/600秒；reserve2秒；其余模块0。包含静态生成、短调试、
  全质量失败及修复、I/O与格式检查，第一条无回收会话以保守上界记账，未漏计失败检查。
  待闭合：补充独立规模/边界依据、64显式诊断、只读verify；独立KKT/恢复代码复核。

2026-10-24闭合：`scripts/prototype/evidence.py`从原始payload独立生成48LP精确
点/dual/Farkas/ray、24MILP结构DP真值，补小LP非最优的具体依据、24边界逐项control_assertions、
64条显式诊断、输入/来源hash与只读--verify。没有生产导入或原生调用；生成器只重建输入。
真值按原始实际binary浮点值运算，冻结旧oracle/输入/答案没有修改，二者在固定集上相符。
最终证据SHA256=`e87df4f3382ba6603b9fe835ce3960b2bacf698023357223d041886b26cf4ff2`；
verify全264+24+64通过，证据测试34通过（含篡改依据、binary RHS及近抵消拒绝），Ruff通过。
worker全部失败/重复/最终检查向上计21秒，M1累计96秒/600秒。
冻结manifest的CRLF工作字节5b037ced与LF Git blob cf5736a2属于相同JSON两种运输哈希，均记录且未改。
独立代码复核未确认其他阻塞；容差根因已经独立复测闭合。补充证据协调复核继续，不能计为算法试验。

### M2

本地模块PASS。96固定小LP与4类warm的首次整合102通过/1加行路径失败（命令1.131秒）。
根因为原始新增行插在既有补界行之前，快照要求物理前缀过严；改为语义行/列键、
按身份重排旧矩阵子块，保留完整系数检查。快照version2显式改变身份版本。
修正后145项通过（96LP+warm/数值7+M1模型42，pytest0.94秒/命令1.600秒）。
RHS/改界/加行实际dual pivots>0，加列实际primal pivots>0，均warm1/cold0，与cold答案一致。
QR分解在状态/方向/对偶多次复用；奇异控制实际重分解再至多一次cold回退。

独立代码复核指出原始/对偶容差取max会放宽可行性，且MIP整数容差不一致可错误关闭节点。
已分开primal、dual、integrality与互补/目标容差；整数候选先取整再原始核验，失败时合法
分支或保留数值失败节点。新回归覆盖原始x=0.99999和x<=0.99999的整数反例，后者真值0。
协调侧实际两次复现及修复复核各约1秒，连同先前KKT单点及3测试累计reserve5秒。
后续完整质量检查 **5882 passed /21.02秒**、Ruff与结构均通过，命令22.360秒。
补充非单位行/列缩放回归后LP104项全部通过（pytest0.38秒，命令含结构/diff共1.292秒）。
不为新增单测重复整套历史回归。预处理推导使用原始binary Fraction，并对新界向外取float，
精确判断冗余侧；避免浮点向内收紧排除数学可行点。行/列缩放实际变坐标后仍核验原始KKT。
`LPSession`公开改RHS/行界/变量界/增行/增列，返回模型副本和实际诊断。
数值与输入域文档、L0012十节/3习题已交付。64固定诊断只在M5实际调用，避免重复超64额外调用；
本模块用针对性四类warm/奇异控制证明机制实际运行。72规模也仅M5执行，仍属最终必过线。
M2累计向上记30秒/1500秒；协调独立5项warm/奇异及其他检查reserve累计8秒。
当前总计M1 96+M2 30+reserve8=134秒/14400秒。

### M3

Pending.

### M4

Pending.

### M5

Pending.

## Git / Remote Sync Proof

- 签发前：main，HEAD=`13e748f`，cached origin/main...HEAD=`0/33`；未查询即时远端。
- 已知用户变动：`AGENTS.md` 修改；根案例通告未跟踪，保持并排除提交。
- AGENTS.md SHA256=`2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638`。
- 根案例通告 SHA256=`0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221`。
- 总目标 Git mode=`local-commit`；采用 `codex/teaching-research-prototype`，仅定向提交本合同文件；push not_attempted。
- remote_sync_status=`dirty_worktree`；同时存在已知 local ahead，不能宣称 synchronized_with_origin。
- 本报告所在提交以 `git log -1 --format=%H -- tasks/reports/20261023-02-01_teaching-prototype_report.md` 查询，避免自引用。

最终由执行者填写当前 branch、HEAD、cached diff、实际提交及保留工作副本状态。
