# 教学研究通用 LP/MILP 原型整体执行报告

合同：[20261023-02-01_teaching-prototype](../codex/20261023-02-01_teaching-prototype.md)。
计划：[SILO-PROTOTYPE-20261023 v0.1](../phases/phase_10_teaching_research_prototype.md)。

## 当前终态

状态：执行中。M1–M4本地模块PASS，最近完整质量6137项通过。
继续M5规模/完整诊断及发行安装门槛；整体原型未完成。

| 检查点 | 当前状态 | 实际证据 |
|---|---|---|
| 初始化：本次总授权登记与规格/manifest | PASS | 991c767、2ca6098及只读补充verify |
| M1 一般模型与统一输入/结果链 | PASS at local module checkpoint | 一般模型/IO/原始KKT/依据链及独立复核闭合 |
| M2 可重优化 LP 与数值基础 | PASS at local module checkpoint | 96小LP、四类真实warm、QR/数值回归；规模仍M5 |
| M3 MILP 搜索控制与 GMI branch-and-cut | PASS (local module) | 96小MILP及证明边界通过；完整质量6058通过；独立算法门控PASS |
| M4 公开研究接口与两个集成例 | PASS (local module) | 公开策略15项/CG57项；独立复核及完整质量6137通过 |
| M5 综合验证与本地安装交付 | in progress | 准备完成；完整矩阵/安装尚未执行 |
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

一般分支定界/割循环已实现：best-bound/DFS、整数界传播、伪成本/分数性分支、
有界舍入启发式、节点基复用、active/queued/unresolved共同参与全局界。
LP无界区分整数射线证明、可分支和未解决三态；未知或相冲突无界松弛保留无限D和空gap。
原始整数候选先舍入再核验，不以整数容差放宽行约束。

GMI使用未缩放原始binary Fraction重建实际基表行，明确整数basic/非基标签，
经split/modular公式回投原坐标；float系数按节点盒向外放松。局部割只传后代，
trace包含基身份、有效盒、坐标、精确系数及float误差；不唯一free回投拒绝。
每轮共享ProofBudget贯穿表行、推导、投影、去重、float转换和trace，4096位增长拒绝；
活动界传播最终冗余扫描亦受deadline控制，超时保留节点及有效界。

独立复核发现并已修正：2^53+1整数输入转float的静默格变化、无界公开anchor与证明anchor
不一致、JSON无限界方向丢失、有限继承界与子LP无界相冲突、精确证明/冗余扫描预算缺口。
Python/JSON/MPS三入口拒绝不可表示整数；可精确表示的2^53仍可接受。
LP Farkas从精确实际基恢复，避免对float割系数猜简单分母导致拒绝。
首次全质量6029通过/1失败：可选HiGHS整数无界返回混合状态4。适配器现仅对该状态按
剩余预算关闭presolve重试一次，持续含糊保留失败，39适配测试通过；不计为两条外部算法证据。

实际检查：MILP106、LP105，证明边界新增29；最后受影响240项通过（1.16秒pytest/
1.677秒墙钟）。完整质量 **6058 passed /22.46秒**，命令23.660秒，结构及Ruff均通过。
较早检查与失败命令均计入，M3向上累计76秒/2100秒。
协调侧额外适配/KKT/射线检查reserve累计16秒；M5准备/适配修复累计3秒。
当前验证总账：M1 96+M2 30+M3 76+M4 0+M5 3+reserve16=221秒/14400秒。
独立最终资源路径静态复核PASS，files_modified=[]/write_attempts=0，不重复计运行证据。
M3本地模块和算法门控PASS，自动进入同一合同M4。
分支割说明及L0013十节/3习题完成数学核对，verified_code待正式checkpoint登记。

### M4

本地模块PASS。公开ResearchExtensions接入真实节点选择、分支、已证明GMI割选择、原始候选启发式
和只读事件；动作、回调次数、前后deadline由执行器检查。上下文不暴露可写树/数组。
无效动作保留前沿，已有LP失败优先于后续observer失败；Python回调需协作返回。
固定MIP策略例保持冻结frozen/p/q/c输入和实际input_sha256，根整数时branch调用0据实登记；
另有已登记分数根测试实际调用替代branch/node/heuristic/separator。

一般非负列min主问题及公开增列采用LPSession；无隐含凸组合行。完整有限池CG明确
Phase I人工变量方向、聚合dual、零辅助目标后去人工变量切Phase II；启发式无列为
incomplete_pricing。最大20轮包含每次辅助和原目标LP。固定覆盖例全池原始/对偶同值2.5。
两项独立只读复核已确认数学及动作边界，修正出口：增列未重求时清除顶层旧dual；
定价RuntimeError转结构化pricing_error并保留primal/trace；observer异常保留primary LP failure。
协调额外4回归通过/0.835秒及两次受控复现0.418秒，reserve累计18秒。

CG57项定向通过，worker所有检查向上记4秒；主线程119、20、14定向检查均通过。
首次全质量6136项通过/23.78秒pytest、25.014秒命令；随后将primary failure优先语义扩展到
relaxation和terminated两个事件，最终完整检查 **6137 passed /22.85秒**，命令24.238秒，
结构及Ruff通过。L0014十节与三习题数学已核对。
M1–M3伴学verified_code登记真实8a07e4b完整提交及2026-10-24核验日期；L0014待M4提交。
一次额外未排除历史研究probe的宽Ruff得到52项历史格式债，未修改这些归档文件；正式
check_quality按既有排除列表通过，和新增代码无关。
M4全部检查向上记60秒/600秒；M5准备向上记10秒；reserve18秒。
累计96+30+76+60+10+18=290秒/14400秒。当前仍无规模或64诊断实际运行。

### M5

尚未运行完整矩阵、规模或64诊断；安装/CI/HiGHS适配器准备已完成。
冻结B13本身的small_milp4根LP为整数，不能据其报告产生GMI割。
验收须分别保留该冻结模型的答案和混合可行域，以及M3已预先登记的手算混合模型
min x+y、2x+y>=3、x整数（松弛1.5到2）的真实割轨迹，明确两个证据来源。
输入/哈希/真值保持冻结；B15可实际进入dual路径但该输入需要0 pivot，正pivot由M2独立例证明。

## Git / Remote Sync Proof

- 签发前：main，HEAD=`13e748f`，cached origin/main...HEAD=`0/33`；未查询即时远端。
- 已知用户变动：`AGENTS.md` 修改；根案例通告未跟踪，保持并排除提交。
- AGENTS.md SHA256=`2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638`。
- 根案例通告 SHA256=`0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221`。
- 总目标 Git mode=`local-commit`；采用 `codex/teaching-research-prototype`，仅定向提交本合同文件；push not_attempted。
- remote_sync_status=`dirty_worktree`；同时存在已知 local ahead，不能宣称 synchronized_with_origin。
- 本报告所在提交以 `git log -1 --format=%H -- tasks/reports/20261023-02-01_teaching-prototype_report.md` 查询，避免自引用。

最终由执行者填写当前 branch、HEAD、cached diff、实际提交及保留工作副本状态。
