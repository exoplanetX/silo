# 第6步执行报告：DAG可行性恢复

## 1. 合同、授权和基线

本轮执行[20261019-06-01合同](../codex/20261019-06-01_dag-feasibility.md)，L3，
唯一目标为独立可行性恢复及原始行见证交接。开发对话是唯一写入/运行协调者，
silo-solver-1010负责签发与验收。完成本原子任务后停止，不自动进入第7步或原目标优化。

实际起点8006344a5a2275e1198cd1e2759627385855cdae，main、工作区干净，cached
origin/main...HEAD=0/5；已知8ee397e、15b403b、f0cc01a、b886458及本次签发8006344
都在用户继续授权内。Git mode=local-commit，本轮不push或访问即时远端。
源码依赖CG15b403b、定价12bfa35、RMP48c242d、LP ad62e0f保持。
已读合同指定规则、当前摘要/技术/同步镜像、学习规范、依赖与前序合同/报告。
推荐GPT-6 Sol/high，难点为两类列的对偶与原始见证；本轮没有声称切换模型。

代码/测试A为02aed7d5d180fbe1cbef67abec1b084777c6a369，学习/报告B通过下方Git历史定位，
两个提交属于同一原子任务。
本报告自身提交通过下列命令在提交后定位，避免未来自身哈希：

~~~text
git log -1 --format=%H -- tasks/reports/20261019-06-01_dag-feasibility_report.md
~~~

## 2. 接口、两类列与范围

新增[dag_feasibility.py](../../src/silo/decomposition/dag_feasibility.py)，只导出
restore_dag_feasibility、DagFeasibilityStatus、DagFeasibilityIteration、DagFeasibilityResult。
输入为既有DagColumnGenerationProblem，复用合法非空seed/固定普通DAG/conv=1验证。
不改旧CG不可行seed时的失败行为；恢复成功后由调用者显式调用旧CG。

辅助模型保持全部原始行与方向/RHS；LE减v、GE加u、EQ加u减v，人工非负且单位成本1、
conv系数0。真实列成本0、conv系数1，辅助c0=0。人工从起点固定存在，后续只加真实路径。
path_i到完整弧元组和art_i到(row,sign)分别冻结保存，命名不拼接用户行/弧ID。
独立冻结零成本图保留原始系数/结构；原graph、成本、基项、rows与c0保持。
只使用公开RMP/定价/模型对象，没有旧模块私有助手、外部solver或生产全路径枚举。

任一合法seed可取权重1，人工量补足各行，辅助问题有有限可行点且F>=0。
完整lambda单纯形紧，最小违背函数连续，因此F*可达且F*=0等价原完整域可行。
人工列对偶必须分别满足1-a_art*pi>=0，联合原行符号给LE[-1,0]、GE[0,1]、EQ[-1,1]。
实现从真实人工系数/单位成本按既有1e-9独立核对，不相信伪造的返回rc。

完整零成本定价rho=min_U(-a*pi)，delta=min(0,rho)。conv乘数平移delta后，
真实路径rc减delta、人工rc不变；人工约束成立时L=D+delta是完整辅助LP下界。
这是两类列分别论证的结果，保留精确条件与浮点估计的区别。
F/D/rho/L、发布差F-L、原项g与32ULP局部eta均沿用既有数值规则，不扩大用户阈值。

## 3. 状态、原始复核与证据归属

每轮辅助RMP冷求解并核对原始行/权重/F/坐标/符号/人工约束/rc及有限性。
F<-1e-9诊断；F在[-1e-9,tolerance]内进入独立原始复核：移除全部人工，
用当前全部真实路径、完整原始行、零目标/常数另建冷RMP，先经既有最优性核验，
再独立复算完整行/非负/目标与坐标，才返回FEASIBLE_SEED_FOUND。
成功保留实际权重，不剪小值、归一化或删行；更小用户容差不改变原始行的1e-9精度。

feasible_problem只替换seed为全部已生成真实路径，保留原图/原目标；feasibility_witness
是无人工零目标原始见证。其他五种状态一律无这两个成功字段。
F小分支不定价，全域D/rho/L/g/eta为None；失败轮也不发布新界。
最后有效辅助RMP及其列集带轮号，后续失败尝试自己的注册表在失败轮中，不能冒充历史见证。

F>tolerance时完整定价，新显著负rc路径每轮最多接受一条；退化继续，重复显著改善路径诊断。
无改善时必须g在阈值内、负g局部规则通过且L>tolerance，才POSITIVE_VIOLATION_BOUND。
F>tolerance但L未分离仍诊断。辅助RMP非OPTIMAL为MASTER_FAILURE，定价失败/异常NO_PATH
为PRICING_FAILURE，原始复核失败为NUMERICAL_ISSUE及failure_stage=original_validation。
不发布全局INFEASIBLE或严格Farkas见证，程序异常保持可见。

辅助轮预算和原始复核分开计数，validation最多1次。最后轮F小可复核成功，
仍需新路径则ITERATION_LIMIT，不追加未经后续求解的列。

## 4. 三个手算例的实际结果

Revised/Tableau均实际运行以下流程，完整代码另外在L0005提取执行：

- r>=1/2、conv=1，路径r=(0,1,2)，原成本(0,4,10)、c0=7，seed=p0。
  辅助F=.5->0，初轮pi=(0,1)、rho=-2，接受p2。辅助2次、无人工复核1次，
  全域界只在初轮发布（D=.5、L=-1.5、g=2）。显式旧CG原目标9.5->9。
  独立原始下界c_p>=4*r_p给目标>=7+4*.5=9，lambda0=lambda1=.5达到。
- r>=3，同图最小违背量1。辅助F=3->1，初轮L=1仍继续定价补p2，末轮rho=0、D=L=1，
  输出POSITIVE_VIOLATION_BOUND，无原始复核和成功问题。
- seed=(0,0)、above=(1,1)、below=(1,-1)，conv=1/R=1/C=0。
  自动F=1->1->0，两后端当前轨迹先above再below；辅助3次、原始复核1次。
  limit=1/2只返回1/2条已求解路径；limit=3正常成功，后端调用分别1、2、4。

签发前公开API桥接与两项只读设计复核作为合同来源保留，未计作上述新恢复器实测。

## 5. 648模型族、完整LP与200次原目标交接

[verification](../../tests/verification/test_dag_feasibility_oracles.py)独立DFS枚举四条三弧路径，
Fraction汇总原始成本/系数，自建完整辅助LP（真实成本0/单位人工）和完整原目标LP。
没有使用恢复器/旧CG的私有重构/建模助手。完整LP共享原生后端，另以独立解析违背量核对。

两行各按LE/GE/EQ再RHS(-1/4,1/2,5/4)排序为9设置，m=9*R索引+C索引，形成81模型。
图s->left_i->right_j->t有四条路径，R/C基系数1/8、-1/4，首弧增i、末弧增j，
RHS同移，conv基1/弧0。偶m原成本(0,4,10,7)、base_cost1、c0=5；
奇m原成本(3,-2,1,-4)、base_cost-2、c0=-5。
首弧成本(i+1)/2、末弧-(j+1)/4，中弧使总成本等于对应矩阵值。
节点/ID/图行/主行顺序沿用合同，seed00或11，原/反序同时反转图/行，两后端共648组。

原始四列凸包为单位正方形，两行最小违背独立相加：
h_LE(b)=max(0,-b)，h_GE(b)=max(0,b-1)，h_EQ(b)=max(0,-b,b-1)。
每行5个可行设置，25模型可行、56正违背，乘8组合预期200/448。

实际648次为200 FEASIBLE_SEED_FOUND、448 POSITIVE_VIOLATION_BOUND；
两后端各100/224，两种排列各100/224。
辅助LP总1144次（1轮200组、2轮400组、3轮48组），原始复核200次，
恢复器后端总调用1344，逐组与计数器核对；944轮实际定价，200个小F终轮不伪造定价量。
所有人工列从起点保留、native MAX成本-1，真实列成本0，conv人工系数0。
200个可行结果逐一显式进入旧CG，并对照独立完整原目标LP，均通过。
原graph/rows/c0深层数据和全部真实seed身份核对，原始见证没有人工变量泄漏。

## 6. 精确Fraction检查与实际浮点边界

每轮原始行/非负/F与人工rc独立复算；944个定价轮的D/rho/L/发布差/g/eta按原始项核对。
Fraction用返回pi的原始二进制值重算全部真实/人工rc，conv平移后的真实rc精确非负。
936个定价轮满足精确人工/行符号条件，严格核对精确平移下界<=解析F*。

另10个辅助末轮的人工rc精确为-2^-52（Revised8、Tableau2），符号约束无精确越界；
它们仍在既有1e-9核验内，保留原pi。其中8个有定价记录的形式平移目标超解析F*为2^-54，
最大5.551115123125783e-17。对这些不把形式目标称为有效的精确对偶下界，
仅核对浮点估计及小量偏差并单列记录；没有投影/裁剪pi或扩容差刷预期计数。
两个F小终轮的相应约束边界不用于发布全域下界，原始可行见证另行核验。
此观察限制当前浮点正界的认证强度，不改变辅助模型精确条件下的定理。

## 7. 失败、注入与测试修正

[unit](../../tests/unit/test_dag_feasibility.py)明确注入seed r=1、u=2/F=2、pi_conv=-4/pi_r=2，
真实rho=0、D=L=2/g=0，但人工rc=-1；恢复器独立人工检查拒绝伪下界。
另有人工成本被改2、原始复核伪OPTIMAL、后续辅助失败、坏候选/原成本混入/容差内字段漂移、
非有限/绝对和/系数汇总溢出、已有显著负rc、局部gap边界及程序异常等保护。
注入用于隔离防护，不宣称正常后端自然出现所有合成错误。

自然例只有r=0却要求r>=5e-4、用户tau=1e-3，辅助F小但原始复核失败，
NUMERICAL_ISSUE、failure_stage=original_validation，无可行问题/见证。
合成微小负F保留原值再做原始复核；多个分量各在非负容差内但总F<-1e-9时仍拒绝。
补充小负rho阈值、正负g/eta预算、L未分离、内部名字/分隔符、冻结所有权等检查。

先写区分性行为再实现，未用新模块import错误作red。首轮unit51 passed in0.26s。
扩至unit64与648族时首轮106 failed/606 passed in2.95s；逐项诊断确认目标逐位相等
断言不适合浮点最优值，且精确人工约束假设实际有上节10个舍入例外。
改为按既有1e-9比较浮点目标，保留适用条件成立时的严格Fraction下界检查，
并显式记录约束不精确时的形式目标，未修改任何生产数值判据来消除这些差异。
随后712 passed in2.00s。最初Ruff17项为3导入块、5循环闭包绑定提醒、9长行；
限定新文件/exports整理导入，改用显式冻结记录replace，手动换行后Ruff通过。
再补负F和容差内重构保护3项，最终新增unit67+verification648=715项。
合同九文件targeted为1647 passed in3.66s，已有932项同轮回归通过。

## 8. 实际质量、教学和环境

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_feasibility.py tests/verification/test_dag_feasibility_oracles.py tests/unit/test_dag_column_generation.py tests/verification/test_dag_column_generation_oracles.py tests/verification/test_dag_cg_bound_consistency.py tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

完整check_quality.py exit0：3046 passed in10.65s，随后Ruff All checks passed，无跳过或警告。
--write-index、普通结构与git diff --check通过；摘要更新前为145份合同、142份报告、
98模块、475个本地链接。提交A前scope为13个允许文件（摘要尚未更新），
9份Markdown的严格UTF-8、围栏、公式及384个本地链接通过，十节/五题/draft/null通过。
全量后代码/测试保持不变，后续真实基线与文档收尾只做轻量检查，不重复全套。
摘要更新后结构复查为145份合同、142份报告、98模块、479个本地链接。
最终scope为全部14个允许文件，10份Markdown的严格UTF-8、围栏、公式及433个本地链接，
十节/五题/真实verified_code通过；代码与测试仍和受测提交A一致。
使用本检出.venv/Scripts/python.exe，Python3.13.9、pytest8.4.2，silo指向本检出src/silo。
沿用已有继承系统包环境，无新依赖、外部solver、worktree、性能实验或干净环境重建。

[L0005正文](../../learning/lessons/L0005-cg-feasibility/README.md)、
[练习](../../learning/lessons/L0005-cg-feasibility/exercises.md)、
[解答](../../learning/lessons/L0005-cg-feasibility/solutions.md)按十节、五道稳定题号建立v0.1.0。
唯一完整Python程序直接compile/exec，双后端均完成恢复->原目标9、正违背1、退化1->1->0。
E01独立算真实rc(4,2,0)/人工rc-1；E02一般证明人工审核，Fraction正方形计数200/448；
E03独立原成本下界9与受限9.5；E04实际三种预算LP计数1/2/4；
E05实际小F原始复核失败及既有局部gap/精确人工例外记录，全部完成有限核对。
实现提交前保持draft/null，实际提交A产生后更新checked、
verified_code=02aed7d5d180fbe1cbef67abec1b084777c6a369、verified_on=2026-10-19。

## 9. 服务、Git与结束位置

签发合同记录theory_architect独立形式化与experiment_auditor证据设计，两服务未跑实验/写文件；
其意见不计为新实现通过。本轮主线程执行全部实现/648族/交接和教学，未新增并行写入。
实际浮点约束例外按合同指定方式保留/报告，未向其他对话发消息或扩大底层修复范围。

允许14文件：新模块/exports、新unit/verification、3个API/导航、L0005三文件、CATALOG、
当前摘要、新报告及派生INDEX。旧CG/RMP/定价/LP/旧测试/L0001–L0004、其他禁区保持。
实现/测试A仅含4个Python文件，提交后cached origin差异0/6；
最终scope为14个允许文件，身份仅用单次命令参数，不改全局/仓库配置。

文档收尾首次提交后实际查询的Remote Sync Proof：

- `git status --short`：空，工作区干净。
- `git branch --show-current`：main。
- `git log --oneline -5`：本任务文档收尾、02aed7d实现、8006344签发、b886458第5步验收、
  f0cc01a第5步文档。
- `git rev-list --left-right --count origin/main...HEAD`：`0 7`，已知起点5个加本任务2个提交。
- `git push result`：not_attempted。
- `remote_sync_status`：local_ahead_origin。

实际查询记录随同一文档收尾提交修订保存，最终哈希通过第1节命令定位，
结束回执再次核对状态、分支及cached origin差异。本轮没有即时远端查询或提交失败。

完成后停在第6步，等待silo-solver-1010审查，第7步未授权实施。
下一步仅建议先审查恢复器及数值证据，再单独定义后续合同，推荐GPT-6 Sol/high。
单位罚权、非空合法seed、连续普通DAG与既有LP/浮点核验边界保留，未发布严格Farkas、
一般数值认证、资源/整数/增量/工业规模或性能结论。
