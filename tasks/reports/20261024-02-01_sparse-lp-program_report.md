# 稀疏 LP 与连续重优化整体执行报告

合同：[20261024-02-01](../codex/20261024-02-01_sparse-lp-program.md)。
依据：[总体规划](../phases/sparse_lp_reoptimization_program_20261024.md)、
[实施计划](../phases/sparse_lp_implementation_20261024.md)。

当前状态（2026-10-25）：**SP1 GO，SP2 HOLD；两次针对修正已用完，整体Goal未完成。**
停止新增求解器验证；当前只保存可复查代码、证据和下一项修复方案。

## 激活与完整目标

2026-10-24，人类在本开发对话以Goal模式直接要求：
“现在silo-solver的下一阶段开发已经讨论完毕，分阶段任务已经给出，请你从
"silo-solver-1010"对话里读取最新的任务规划，完成这次的设计目标。”
唯一Goal已存在且active，所有者silo-solver开发（01a15208-bea9-7030-aacc-95d785e8fa58），
不创建第二Goal。本轮按SP1–SP4连续完成同一合同及八项总验收，正常门通过后不跨对话等待。

目标保持端到端稀疏LP、真实LU/eta、跨调用会话及四类编辑、MIP/CG接入、
12容量/12Netlib必过、160修改状态/5重复/中位收益≥1.5且6/8≥1、8安装和伴学。
任一未达仍登记未达；不改题、换例、放宽阈值或仅凭接口/测试数宣布完成。

## 启动证据

- 实际启动HEAD/发行提交：a4809855cffb028687ab0e192be68f8186937335；准备基线64700cd，产品基线f488189。
- 启动分支codex/teaching-research-prototype；创建并切换codex/sparse-lp-reoptimization，未reset/clean/push。
- 启动cached origin/main...HEAD=0/52；仅本地跟踪引用，没有即时远端查询。
- 只存在两项已接受治理差异；AGENTS.md SHA2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638，
  根案例通告SHA0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221，已核对，排除暂存。
- 已读最新讨论规划、人类准备指令/最终实施入口，合同、两计划、AGENTS/CASE、tasks规则、mirror、learning规则。
- 新报告沿用已签02-01合同身份，不新签任务；L0015当前未占用。
- 沿用silo-development-operator；本合同被当前人类直接指令激活，覆盖列明L2/L3及内部连续执行。
  推荐GPT-6 Sol/high，不声称已切模型。memory registry无SILO命中，未依赖记忆推断当前状态。

## 预算与证据根

唯一新根outputs/sparse_lp_program_20261024；账本append-only SHA链跨续接保留。
SP1/SP2/SP3/SP4/余量=30/60/180/180/30分钟，总计480分钟；不设混合总调用上限。
容量/外部≤2轮、warm≤2轮各5重复、全质量≤3轮、额外诊断≤20批各60秒；
安装每组合至多一次同SHA纯环境重试。时间不父子双计，失败/基线/比较/环境均计入。
旧prototype/revision/audit输入、工件、输出和账本只读。

## 检查点

| 阶段 | 当前状态 | 仍需证据 |
|---|---|---|
| SP1设计、输入与基线冻结 | GO；a3cff29输入、3c27324真值/基线 | 架构子门和完整证据设计门均独立GO；产品仍未改时登记 |
| SP2稀疏cold链 | HOLD，两次修正后容量预检仍未达 | 重构/比率/提交代次一致性及固定组复验；尚无SP2 GO |
| SP3更新与会话 | 未开始 | 公式/缓存/机制/160状态/公平5重复收益及独立数值门 |
| SP4上层和总体交付 | 未开始 | 完整矩阵/历史/8安装/伴学/独立八项最终GO |

## 当前恢复入口

### SP1已取得的事实

- 120固定案例及8×20状态已实例化，首次输入/设计冻结提交a3cff29。
  Netlib12原件/解码/转换与独立Highs readModel/getLp逐字段/系数全等，没有运行优化器。
  108非外部案例经独立原始Fraction数学检查，容量BLOCK02真实2000变量/5000非零行/100000nnz。
- BOUND两轨迹在首次冻结及任何SILO/HiGHS优化前，发现原步长的可行性证明欠缺；
  只依据数学改为1/1024，44份旧draft及哈希归档。新40状态逐原行/界精确可行。
  最终manifest SHA51ee70574b413182e0092041e5ea96a11dda68df7ed850dcb17dc542f0f32725，
  sources SHA4d90dbbe6cdb3b668f9036fb033a2a0ae1905015d8d0200990855baa321498e2。
- 只读架构子门初评两项BLOCK（证明空间总量与缓存数值策略歧义），已按同一路线明确
  同时存活cell估计和三层身份/资源/pricing规则；窄复读GO，无新关闭项。完整SP1尚非GO。
- 已核实Windows Python3.13.9及独立3.11.15环境，NumPy2.3.5/SciPy1.16.3的正/转置LU可用。
  3.11首次依赖下载180秒harness_timeout保留；同版本、官方PyPI/系统证书传输重试9.079秒安装成功，
  没有放宽包版本、目标或数值标准。当前尚无SILO基线或HiGHS优化调用。
- 新账本初始化发现pin事件误用保留sha256字段：原字节保留，以pin-file SHA重建并验证唯一旧预像，
  明确恢复事件及以后保留字段拒绝已记录。首次preflight误套两层计时也保留双收据，
  按包含区间显式去重一次，新增父进程标记禁止嵌套计费。未重置账本、旧证据或消耗。

### 首次冻结后参考和基线

- a3cff29先于全部SILO基线与HiGHS优化调用，锁定三契约、recipes、120/160输入和来源。
  独立证据设计审核确认固定分母/容量实质/导入双路径，允许首次输入冻结；
  case candidate SHA重建核对已在首次提交内补齐。完整SP1仍需真值及基线后复核。
- 8个0.2.0a2 dense基线实际完成8次root调用，整批10.8822164秒，单线程独立进程。
  AFIRO/ADLITTLE/SC50A/SC50B/SC105/SC205/SHARE2B全部optimal；
  BLEND返回numerical_failure（Singular/near-singular basis QR），原失败完整保留。
  证据groups/422d13a0-c9db-4789-9dde-04e670d158a1，均未替换输入/预期。
- 新验证支撑6项单测通过（1.26秒pytest内部，1.71965秒完整计费），
  覆盖账本篡改/预算拒绝、OS wall/RSS和5重复配对指标，0次SILO调用。
  补充完整20状态/60秒轨迹驱动、真值绑定、进程树超时回收与旧证据只读复核入口。
  验证驱动尚待对应阶段实际使用，不以入口存在宣称机制/性能已达。
- 独立真值索引SHA8b138a13cf8a3dba039996d8b9a7ac8935a463852d0731453e18a334b4837b49。
  120案例+8初态+160修改状态全部绑定frozen payload和完整见证SHA；
  176份exact Fraction，112次单线程HiGHS（12 Netlib+100warm），0次SILO、0次重试。
  数值参考全部optimal并逐原行/界/KKT通过，最大scaled error8.852375491465501e-10，
  参考固定标准1e-8。导出69.2991402秒，后半段已测命令合计73.0969669秒，
  含小工具开销保守一次记76秒，不叠加内部68.9000196秒。
  reference/oracles_final_delivery_receipt.json含环境、逐调用和完整源/见证身份。
- evaluate SP1实际exit0，1.3865291秒；重建120/160输入、288真值绑定、8旧基线
  并复查7份最优结果对独立参考。当前产品src/pyproject与a480985完全一致。
  真值/基线第二次冻结3c27324；独立experiment_auditor复读完整证据门GO。
  与此前theory_architect架构子门GO合并，由主线程登记SP1 GO，随后才允许改产品。
  BLEND旧dense失败只保留为失败，不计入速度倍数或成功性能分母。

先核本报告、ledger链、Git/source身份及具体进程handle，再继续SP1。
输入准备由唯一写入者生成；输入/真值两提交及完整SP1独立门已完成，当前SP2 HOLD。
主线程负责CLI/账本/契约/集成；只读Devex原始依据和稠密边界核查不被计为算法实测。
所有缺口保持原范围；当前Goal未完成。原A/B已验收、C HOLD、D/E未开始，native延期。

## SP2实现与首轮证据

- 矩阵/变换/传播/原始核验/受限证明组件148测试通过，130public/134kernel完成，
  3.2221124秒。因子组件首验27通过，26kernel、45次实际LU，1.1033935秒。
  root公开接口/会话隔离/资源/旧MIP及CG集成171通过，完整命令1.9201998秒。
  这些组件结果均不代表容量或整体GO。
- 首轮tiny48/48，25.042362秒，groups/bfbe0b12-ffac-4db3-a02b-94a5b373c2ec。
- 首轮pressure21/24，12.6221512秒，groups/8bbb52d6-b632-4c71-83b6-2901dc4872a4。
  LIMIT01是harness覆盖time_limit0；NUM03/04是近相关等式被错误删除，错报optimal−1对真值0。
- 首轮smoke4/6，67.4896826秒，groups/f20168f4-f4e7-4c1b-b875-e3ba9a8e53f3。
  AFIRO/ADLITTLE/SC50A/SC50B正确optimal；CAP-FLOW-01在5592pivot后unsafe pivot，
  CAP-TRANS-01在13308pivot后失去primal feasibility。没有替换模型或调整阈值。
- 初轮Windows RSS只监控venv redirector，约7MB并非真实解释器峰值；旧值不能作为容量证据。
  已改为root及后代进程OS PeakWorkingSetSize之和（保守上界），真实40MiB子进程回归通过。
  time_limit改为min(冻结选项,外层上限)，保留零值；支撑7测试通过，2.1415432秒。
- MatOps冻结操作清单补齐、15组件通过，1.4502346秒。全池证明预留
  4*nResult+4*mResult+2*pool+32外层Fraction槽，与basis共用ProofBudget；
  58测试通过，0.7091256秒，真实1/100000007重构路径达到65536通过、65537在basis分配前拒绝。

## 两次针对修正及当前阻断

1. 第一次：删除行需原始二进制方程精确依赖证明；真正相同比值才按semantic key并列；
   factor/kernel共用安全主元谓词，并保留所有真实阻塞行。31组件通过，新增验证1.2109429秒。
   一批两模型诊断1.5189188秒，FLOW117/TRANS47pivot后均unsafe blocker数值失败。
   保存diagnostics/kernel_sp2_fix1，后代RSS约75/76MB；不计容量通过。
2. 第二次：当前B/cost/phase内拒绝不可安全换基的进入列，保留sticky Bland及visited，
   按既定顺序尝试其余列；全拒保守numerical_failure。33组件通过，新增验证1.1067804秒。
   两模型诊断36.574997秒，FLOW3963pivot后Primal simplex lost feasibility；
   TRANS5057pivot后solver自返25.0497秒time_limit，外层25.4847秒也标harness_timeout。
   原始输出完整、exit0仍按harness失败保留；RSS约102.6/132.1MB。
   保存diagnostics/kernel_sp2_fix2；没有第三次修复或额外正式组。

独立theory_architect仍判代码门BLOCK，指出同一代次不变量尚未落实：
factor.replace_column可在已选leaving后重构并重算direction，却提交旧leaving；
direction solve或Devex BTRAN隐式重构时，kernel也未统一撤销已算state/ratio。
旧d=(1,2)、xB=(1,1)选第二行，若重构后d=(2,.5)，真实blocker已是第一行，
沿用第二行会把第一基本值降至−3。该数学反例说明具体提交风险，未声称它是全部性能根因。

### 可审阅的下一项修复方案（尚未授权执行）

范围只涉及sparse_factor.py/sparse_kernel.py及对应组件tests，不改输入、容差、Bland定义或目标：

- SparseFactor增加单调generation；一次成功current-B refactor更新代次。
- state、direction、Devex BTRAN、ratio、commit携带同一代次。
  任一步重构即取消尚未提交pivot，从同一B重算xB、dual、rc、direction、true-min-ratio。
- replace_column需要重构时返回未提交retry；不以新direction提交旧leaving。
  拒绝集不授权optimal；fresh-state后有历史被拒列而改善信号消失时仍保守失败。
- 增加两项注入测试：direction solve及BTRAN分别强制重构并改变真实blocker，
  断言旧leaving从未提交；保留candidate恢复/全拒失败/小阻塞不越过测试。
- 建议仅追加一次针对修正及一次受影响正式复验（48tiny/24pressure/6smoke），
  仍遵守各例原时间/RSS、SP2剩余时间和原总预算；不重置已用额度。
  源码通过独立复读且上述组全部通过后，才可给SP2 GO并继续原SP3–SP4。
  推荐GPT-6 Sol/high，复用当前实现上下文；未声称切换实际模型。

合同第6节限定每阶段初验+两次修正；本阶段两次已使用。需要人类明确扩展本阶段次数，
才可实施上述额外修复。技术问题与次数授权分别保留，目标/完成标准不变。

## 未完成义务与证据状态

- SP2容量两个必过预检和独立数学GO未达，pressure固定整组尚未在最新修正源码重跑。
- SP3的8机制正式组、160修改状态×5重复、公平收益≥1.5及6/8≥1均未运行。
- SP4完整12容量/12Netlib、12MIP/4CG、旧288/192/64整组、全质量及8安装未运行。
- 没有0.3.0a1工件、发布或最终八项GO；pyproject/runtime仍为0.2.0a2实验分支。
- L0012保留旧dense已核基线并注明未验稀疏增补；新L0015为draft，verified_code=null。
- 暂存/提交仅本任务代码与HOLD材料，两治理文件原SHA及所有旧输出/工件/账本保持。

截至第二次诊断：SP1 368.5422803秒，SP2 157.034505秒，总525.5767853秒；
后续保存材料只进行静态检查，准确新总量从append-only ledger读取。
capacity/netlib/warm/quality正式轮次均0；diagnostic2/20；本次HOLD由阶段修正次数上限触发，
480分钟总时间并未耗尽。后续不把剩余时间自动解释为第三次修正授权。

HOLD保存检查：结构检查原先将任何SciPy导入都当作优化器调用，现按本合同
已授权的矩阵/LU边界做最小白名单适配；仅modeling矩阵adapter允许from scipy import sparse，
lp/modeling仅允许列明的sparse矩阵函数及splu。optimize、HiGHS、csgraph及core反向依赖仍拒绝。
9项纯AST策略测试通过（0次SILO），随后结构/全仓ruff/diff检查均exit0；
没有运行完整check_quality.py或新增算法试验。首次静态失败收据同样保留。

## Remote Sync Proof

branch=codex/sparse-lp-reoptimization；known governance dirty_worktree；push=not_attempted。
HOLD产品保存提交2b40d87cae0153538592abd2af492c9e6c9e7be7，前一主体提交8d72a3c；
后续MIP遗漏暂存已由独立跟进提交补齐，当前124个源码/pyproject均与已保存运行身份一致。
逐文件git blob严格只作CRLF→LF运输等价核对通过；不把实质差异归为换行。
sp2_hold_committed_identity.json保存实际源码SHA、Git/source匹配、状态、last5和cached引用。
产品保存时cached origin/main...HEAD=0/57；只读本地引用，没有fetch或即时远端核对。
该时刻last5为2b40d87、8d72a3c、8aa0946、3c27324、a3cff29。
两项已接受治理差异仍原SHA且未暂存，旧证据逐文件SHA保持。
截至保存身份复核总验证534.3422841秒（SP1 368.5422803，SP2 165.8000038）；
完整质量/容量组/Netlib组/warm/安装均未执行，无发布。
额外一次修复授权问题已在开发对话提出；提出问题不等于获准，回复前保持HOLD。
报告最后元数据提交从Git history定位；最终cached计数因本地报告提交再前进，不冒充远端状态。
