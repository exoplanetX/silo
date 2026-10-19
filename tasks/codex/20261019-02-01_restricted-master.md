# 第 2 步交付：最小受限主问题（RMP）接口

## 1. 任务元信息、基线与授权

- ID：20261019-02-01_restricted-master；签发前已扫描同日合同与报告，01 已由
  revised-phase1-cleanup 使用，本任务使用新 TT=02、RR=01。
- 类型/风险：L3，现有原生 LP 上的窄范围 RMP 新适配能力，包含 L2 的求解调用与新
  Python 接口。当前用户已明确要求“把第2步需要做的任务写清楚，交付执行”，该授权
  覆盖本合同的适配层、测试、学习材料与本地提交，不需要重复询问同一授权。
- 阶段来源：tasks/phases/phase_07_decomposition.md 中 master wrapper 与未来 RMP
  能力；这是用户批准的有限扩展，旧 Phase 7 保守完成范围保持其历史含义。
  Phase 9 仍 open/parked、native deferred，Phase 10 仍未启动。
- 签发/审查：silo-solver-1010，thread 01a1254a-b349-77d0-8c66-d4b711cd511f。
- 唯一实施/写入协调：silo-solver开发，thread 01a15208-bea9-7030-aacc-95d785e8fa58。
- 工作目录：E:/OneDrive/workspace/codex/silo-solver。
- 签发前实际 HEAD：c3704bea613d04ae7a2254880490fa08611448a6；main，工作区干净。
  相对本地缓存 origin/main 为 0/3，三个提交依次为 cfb43a8（第1步签发）、
  ad62e0f（实现）、c3704be（文档报告）。没有本轮实时远端同步证明。
- 本次批准在已说明的 local-ahead 状态下继续。执行从本合同的签发提交开始；该提交
  仅增加本合同、刷新 INDEX 并更新 project_profile，solver 源码仍为上述基线。
  用户授权覆盖这三个已知本地提交及本次签发提交，不能仅因这些已知 ahead 再索要批准。
  若发现其他代码漂移、分歧或无关脏文件，保留现场并报告，不重置或覆盖。
- 签发提交定位：git log -1 --format=%H -- tasks/codex/20261019-02-01_restricted-master.md。
- Git mode：local-commit；本地提交，禁止自行 push。
- Expected report：tasks/reports/20261019-02-01_restricted-master_report.md。
- Learning delivery：新建 learning/lessons/L0002-restricted-master/ 的正文、练习、
  解答，更新 learning/CATALOG.md。签发时已扫描，当前仅 L0001，故预留 L0002。
- 模型建议：GPT-6 Sol / high。具体难点为目标/对偶/约化成本的方向转换，以及加列
  后行依赖变化。建议不等于实际切换；如配置不同据实记录，不自行升级 Astra。

## 2. 已完成的第 1 步与本任务的一句话目标

第 1 步已经讨论对话验收通过：来源行 K、基位置 I、列编号独立映射，删行后的
最优候选回到原模型核验，L0001 v0.2.0 交付通过。讨论对话在 c3704be 上独立重跑
1399 项测试、Ruff、目录与差异检查；另一个含组合冗余行的小模型枚举 840 个基排列，
其中 288 个精确 Phase-I 可行基均通过清理与原模型核验。该证据是第 1 步验收，
不代替本任务对新增代码的实际测试。

本任务的唯一目标：在现有 SILO LP 内核上实现一个可显式加列、每次完整重建并冷启动
求解、以最小化坐标返回经核验结果的 RMP 适配层，为后续定价提供可靠的行乘数接口。

本次交付是 RMP 当前列集合上的 LP 能力。精确定价、自动列生成循环和研究加速机制
属于后续独立步骤，不在本次实现范围。

## 3. 开始前必读与复用判断

先读 AGENTS.md、tasks/README.md、project_profile.md、technical_route.md、
remote_sync_proof.md，以及 learning/README.md、learning/WRITING_GUIDE.md。
然后按需读：

- src/silo/core/model.py、constraint.py、objective.py、variable.py、bounds.py。
- src/silo/lp/base.py、simplex/revised.py、simplex/tableau.py、optimality.py。
- src/silo/decomposition/master.py、column_candidate.py、column_generation.py、
  __init__.py，以及现有 decomposition boundary/record 测试。
- docs/lp_duality.md、docs/development_layout.md 与 L0001 第 7、8 节。
- 第 1 步合同与报告：20261019-01-01_revised-phase1-cleanup。

现有 MasterProblem/Result 是被动边界记录；ColumnCandidate 还要求定价来源、迭代和
已有 reduced_cost，且拒绝零向量。新接口的输入列只需名字、成本和系数，不应为复用而
伪造定价结果。复用 core Model/Variable/Constraint 与 LPSolver、现有核验器即可。
保留旧记录、toy 驱动和 ColumnGenerationSolver 的既有行为。

## 4. 数学合同：最小化、行坐标和最优性范围

原始 RMP 定义为

\[
\min_{\lambda\ge0}\quad P_S=c_0+\sum_{p\in S}c_p\lambda_p,\qquad
\sum_{p\in S}a_{ip}\lambda_p\ {\bowtie_i}\ b_i,\quad
\bowtie_i\in\{\le,\ge,=\}.
\]

支持域为连续变量、精确下界 0、上界正无穷，所有成本、系数、RHS、常数有限。
保留用户原始行名、方向、顺序与 RHS，完整行集合固定。S 为调用者显式提供的当前
列集合，RMP 本身可以具有冗余行、负 RHS、非零常数与退化最优解。

内部交给现有 LP 的模型只有目标取反：
\[
\max_{\lambda\ge0}\quad -c_0-\sum_{p\in S}c_p\lambda_p.
\]
不能调用 CLI/后端选择器，不能改变全局 LP 的 max-only 约定或增加 minimize 内核。

设内核按原始行坐标返回最大化乘数 y 与约化成本 r，则 RMP 输出须满足
\[
P_S=-P_{\max},\qquad \pi=-y,\qquad
\bar c_p=c_p-a_p^\top\pi=-r_p.
\]
整个目标值取反，目标常数只计一次。这里的 y 已撤销内核的负 RHS 标准化，适配层
不再额外翻转行。最小化的 LE 行乘数非正、GE 行乘数非负、EQ 自由，当前列的
\(\bar c_p\ge0\)，\(\lambda_p\bar c_p=0\)，并有对偶下界
\(D_S=c_0+b^\top\pi\)。讲解中推导这些关系，不能只记符号表。

OPTIMAL 的含义限定为当前 S 上的经浮点核验最优。完整主问题的最优性还要求对所有
合法未生成列成立的定价依据；本接口不拥有完整列空间，不能输出全局 CG 终止结论。
负约化成本表示旧对偶对该列不再可行，退化时加入该列可只改变对偶、不严格降低目标。

## 5. 最小 Python 接口与输入所有权

新增 src/silo/decomposition/restricted_master.py，提供以下两个小型接口：

~~~text
RestrictedMasterProblem(model: Model)
    add_column(*, name: str, cost: float,
               row_coefficients: Mapping[str, float]) -> None
    solve(solver: LPSolver | None = None) -> RestrictedMasterResult

RestrictedMasterResult
    status, objective_value, primal_values, dual_values, reduced_costs, message
~~~

默认 solver 使用现有 RevisedSimplexSolver；允许显式传入 TableauSimplexSolver
及测试用 LPSolver 替身。可以调整类型标注/私有组织，但保留上述最小使用方式与
最小化字段含义；不扩展成通用 decomposition 框架。

- 构造器接收 MINIMIZE Model，复制其列表和系数字典，随后内部拥有完整 RMP 状态。
  校验 model.validate() 及上述支持域；MAXIMIZE、整数/自由/固定/有限界变量、
  非有限数据和非法模型明确拒绝，不能静默放宽领域或改写用户输入。
- 初始列就是输入 Model 中的变量。正常流程由调用者给出可行初始 RMP；适配层
  不自动生成 seed、Big-M 列或可行性定价。原生 LP 内部既有 Phase I 可正常使用。
- add_column 创建一个连续非负无上界变量，成本为原始最小化成本；稀疏系数中
  省略的已知行取零。未知行、重复变量名、空白名字、非有限成本/系数明确拒绝。
  名称按原字符串精确匹配，不静默清理/重命名已有坐标。
- 系数全零或空映射是合法零列；不同名字的相同向量也合法，不按向量自动去重。
  本步只按变量身份拒绝重复。零列可能产生无界诊断，按第 7 节处理。
- 先完整校验再加入；失败的 add_column 不得留下半个变量或部分更新行。
  复制传入映射，调用者后来修改字典不能改变已加入列。
- 每次 solve 生成新的完整取反模型，冷调用现有 solve；本步无 presolve、基热启动、
  旧 basis/删行集合/乘数的状态复用或缓存优化。
- 结果是当前列集合的独立快照；后续加列、求解或调用者修改原输入，不能改变已返回
  快照。结果映射应只读或使用项目现有不可变数值项约定，并清楚记录访问方式。
- RestrictedMasterResult 使用原最小化语义，不把其字段装入或冒充全局最大化 Solution。
  可在 decomposition/__init__.py 中导出新接口，不改现有类型的字段和含义。
  禁止直接用 MasterProblemResult.from_solution() 原样复制 native 结果；该函数不做
  min/max 转换。新接口必须逐项转换目标、乘数和约化成本。

## 6. 加列后必须重建全部原始行：核心回归

RMP 当前列矩阵中的行依赖可以随 S 变化。旧 LP 清理删除的冗余行不得从 RMP 持久
模型中消失，也不能把旧约化问题当成下次加列的原始模型。

确定例：初始只有变量 x，成本 2，两行 a:x=1、b:x=1，常数 0。
初始最优 x=1，目标 2。加入 q，成本 0，列系数为 a:1、b:0。
新模型为 x+q=1、x=1，所以 x=1、q=0，目标仍为 2；当前两行已独立。
如果误把旧冗余行 b 永久删除，就会得到错误的 x=0、q=1、目标 0。

测试同时覆盖 q=(1,0) 和 q=(0,1)，以及行顺序变换。最小化旧对偶可能为 (2,0)，
此时第一种 q 的旧约化成本为 -2，加入后目标仍为 2。核验新乘数有效性，不要求
新旧乘数相等，也不把没有严格下降判作求解失败。此例必须进入 L0002。

## 7. 核验与状态隔离

- 任一后端返回 OPTIMAL 后，先对本次完整的取反模型和原始后端 Solution 调用
  check_lp_optimality，使用既有 DEFAULT_TOLERANCE=1e-9。每次都核验，不能只验证
  cleanup 实际删行的情况。通过后才转换并发布 RMP 的最小化最优字段。
- 原模型核验失败、缺失/非有限依据或坐标不全时，RMP 返回 NUMERICAL_ISSUE，
  objective_value 为 None，primal/dual/reduced_costs 为空，message 给出原因。
  不为配合适配层而改动 LP 核验器、阈值或求解器。
- 后端返回非 OPTIMAL 状态时，保留状态/消息作为本次 RMP 的诊断，但不发布最优
  目标或 primal/dual/reduced_costs；不沿用上一次成功结果。至少测试 INFEASIBLE、
  UNBOUNDED、ITERATION_LIMIT、NUMERICAL_ISSUE；其他状态遵守同样规则。
- 当前 RMP 不可行，只能说明当前列集合不足或该受限模型不可行，不能推断完整主问题
  不可行。需有“受限模型不可行，显式补列后可行”的小例。
- 已知数值债：x-(1+5e-10)z=1e10、x-z=1e10，max z 精确迫使 z=0，
  第 1 步审查实测旧版及当前 revised 均可能返回 UNBOUNDED。新增保护仅核验最优
  候选，其他终止状态没有独立射线/不可行性依据。本任务不修复这个既有 LP 问题，
  不把后端非最优状态升级为完整主问题的已认证结论，也不宣称一般尺度稳健性。
  本步成功算例使用小整数/有理数与已知有限最优值；数值异常走保守失败路径。

## 8. 确定性手算真值与测试要求

主要真值来自以下解析模型、原始行和最小化对偶关系；不能只比较两个内部后端。

### A. 常数、加列和约化成本方向

初始两行 a:lambda_a=1、b:lambda_b=1，成本分别 4、6，常数 7。
初始解 (1,1)，最小化目标 17、乘数 (4,6)、约化成本 (0,0)。
内部最大化目标 -17、乘数 (-4,-6)。

新列 p 的系数 (1,1)、成本 7，相对初始乘数的约化成本 -3，内部为 +3。
加入后 lambda_p=1，两个旧变量为 0，最小化目标 14；由参数 t=lambda_p，
0<=t<=1、目标 17-3t 直接给出真值。最终对偶不唯一，独立核验其符号、列关系、
互补和 D=14，不能硬编码某个后端最终乘数组合。

成本 7、10、12 的测试分别从同一个初始 RMP 开始，初始乘数 (4,6) 下的约化成本
分别 -3、0、2，对应新增后的目标分别 14、17、17。成本 10 的零约化成本仅相对
尚未加入成本 7 列的初始状态；不能先加成本 7 再要求成本 10 的列仍为零约化成本。
另行覆盖两个后端、连续加列后重新求解与重复求解确定性。不同名称相同列允许加入。比较退化见证的有效性，
不强制双后端选择相同基、解或对偶。

### B. 行依赖复活

完整实现第 6 节的模型与对称/行顺序变换。核对每次原始两行仍存在，新增列后
解和对偶满足新的完整矩阵。用手工合法旧乘数 (2,0) 验证第一种列的负约化成本，
不要求实际后端返回这组退化乘数。必须能识别“永久复用旧删行结果”的错误实现。

### C. 混合行、负 RHS 与最小化符号

\[
\min\ 7+2x-z+3w,\quad x\ge1,\quad z\le3,\quad -w=-2,\quad x+z\le5,
\quad x,z,w\ge0.
\]
解析最优为 (1,3,2)，目标 12；按列出的行顺序，乘数 (2,-1,-3,0)，
约化成本为零。分别核验 LE/GE/EQ 的符号和负 RHS 恢复，不做二次变号。

### D. 接口与失败路径

- 输入 MIN 验证、变量域、有限数据、未知行、重复名、稀疏零项、合法零列。
- 构造后外部 Model/系数字典修改、add_column 后外部映射修改、失败添加的原子性、
  历史结果快照不随新列变化。
- 初始空列且 0=1 的 RMP 不可行，补充一列系数 1、成本 3 后目标 3；
  这只演示受限不可行的范围，不引入可行性定价。
- 小型真实非最优模型/迭代限，加测试替身模拟非最优状态与错误 OPTIMAL 依据，
  证明不泄漏最优字段、不沿用旧解、核验失败不会返回 OPTIMAL。
- 用 spy LPSolver 记录两次调用，证明收到不同的新 Model 对象、完整原始行集合与
  所有当前列；不传入旧 basis，也不持久存储后端 cleanup 后的标准形。
- 现有 decomposition no-op/toy、ColumnCandidate、被动 MasterProblem 兼容，
  core/lp/mip 等下层不反向导入 decomposition，原有 LP/MIP/CLI 回归通过。
- 如增加可选 SciPy 比较，严格限于 tests，沿用可选依赖机制；解析真值覆盖必须
  无外部求解器也能运行。不新增依赖或研究规模实验。

## 9. Scope lock：唯一允许改动的文件

- 新增 src/silo/decomposition/restricted_master.py。
- src/silo/decomposition/__init__.py：仅导出新接口。
- 新增 tests/unit/test_restricted_master.py。
- 新增 tests/verification/test_restricted_master_oracles.py。
- tests/unit/test_decomposition_boundary_smoke.py：仅补充新接口相关兼容/依赖边界检查，
  无需改动时保持原样；不得削弱原 no-op 或下层边界断言。
- 新增 docs/restricted_master.md；docs/README.md 添加导航。
- docs/development_layout.md：更新实际 RMP 入口与 decomposition -> lp/core 的依赖说明，
  相关现有 cleanup 描述可准确指向第 1 步修复；不重排目录。
- 新增 learning/lessons/L0002-restricted-master/README.md、exercises.md、solutions.md；
  learning/CATALOG.md 添加开发/主题顺序及来源链接。
- .silo-dos/project_profile.md：更新本任务状态、基线、已知局限及下一步建议。
- 本任务匹配的新执行报告；脚本派生的 tasks/INDEX.md。

禁止修改：core/modeling/lp/presolve/mip/CLI/io/现有外部接口、StandardForm/Basis、
现有 decomposition/master.py、column_candidate.py、column_generation.py、
driver/toy 模块的行为，L0001 正文及历史合同/报告、research notes/探针/资产、
ROADMAP/阶段文件/其他 .silo-dos 门控、任务规则、Skill/Agent、依赖/build/native。
禁止实现定价、CG 自动循环、分支定价、缓存/状态复用/暖启动/增量矩阵更新、
自动初始列、Big-M 或可行性定价、一般变量界支持、新 CLI/JSON/Solution 字段。
若实现必须突破上述边界，保留证据并报告最小缺口，不自行扩大范围。

## 10. Learning delivery：L0002｜受限主问题与列接口

按既有十节体例独立成篇，链接 L0001 对偶基础，避免复制其完整教学正文。
至少包括：

1. 当前列集合 S、初始可行列、原模型/内核坐标与最小化乘数的含义。
2. 第 8 节 A 的手算与可执行示例；目标常数、正负约化成本的逐项核对。
3. 从弱对偶推导 pi 的行符号、rc、上下界及目标取反关系。
4. 行依赖随列集变化、第 6 节反例，以及退化负 rc 不保证严格改善。
5. API/状态/代码映射、冷重建选择、核验方法与实际复现命令。
6. 研究价值：为精确定价与后续 CG 提供参考接口；当前贡献属于基础设施。
7. 局限：只覆盖当前列集合、已知非最优状态数值债、普通非负连续域、
   没有自动可行性恢复/热启动/定价/全局终止依据，也没有性能优势主张。

至少四道稳定编号 L0002-E01... 的分层练习及完整解答，覆盖 A 的符号/常数、
混合行、行依赖复活/退化、RMP 与完整主问题最优性或可行性边界。
实际运行正文代码和可执行习题；一般结论用推导，不能把有限测试当证明。

verified_code 使用真实实现提交、verified_on 使用实际核验日期。可以先提交
实现与测试获得 A 提交，再更新 checked 元信息/学习/报告得到 B 提交；二者是同一
原子任务。代码哈希产生前保持 draft/null，不引用未来自身哈希或旧 LP 提交冒充
新增 RMP 接口的核验基线。报告区分代码验证、教学验证与只读复核的范围。

## 11. 执行流程、必需命令与验收

1. Preflight：实际 HEAD/status/branch、origin 差异、解释器和 silo.__file__，
   核对本任务授权、已知 ahead 提交及所有权。主执行对话是唯一文件写入者。
2. 从数学合同和 A/B/C 真值写确定性测试，再做最小适配实现。
   不要求为新 API 制造 import-error 式 red；记录真实失败和修复过程。
3. 可进行一个有必要的只读数学/测试证据复核，问题限定本接口；专业服务不改文件、
   不代跑实验。默认由主执行线程完成实现与实验，不另开并行写入者或模型对照试验。
4. 完成当前 API 文档与 L0002，创建匹配执行报告后刷新索引。
5. 在项目根目录用已有 .venv，不安装或升级包：

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py tests/unit/test_decomposition_boundary_smoke.py tests/unit/test_decomposition_records.py tests/unit/test_decomposition_column_candidate.py tests/unit/test_lp_duality.py tests/unit/test_lp_optimality.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

核对新文档/学习链接、UTF-8、代码围栏、公式、习题编号、真实代码基线，并运行
教学代码与有限习题。代码稳定且全量通过后，仅文档收尾无需机械重跑全套；
后续代码改变、有失败或新增实质疑点时才补跑相应检查。

验收条件：A/B/C 真值及映射通过；每个 OPTIMAL 已在完整输入上核验；失败字段
隔离；全行重建和输入/结果所有权明确；原边界及全量回归通过；L0002 有真实验证；
diff 只含允许文件；报告/索引齐全；本地提交，不推送；只完成这一个任务后停止。

## 12. 停止条件、报告与交付回执

遇到数学合同不成立、必须修改被禁模块/全局数值策略、必须引入新依赖或外部求解器、
需要真实 pricing/CG 循环才能完成本接口、来源/基线不符或无关并发写入时，报告
具体证据与最小缺口。不要改旧合同、扩大任务、重置他人文件或自动进入第 3 步。

执行报告至少写明：

- 实际起点、签发提交定位、代码/报告结果提交定位、环境与导入路径。
- 接口与数据所有权、min/max 公式、对偶符号、常数处理和全部行重建。
- A/B/C 与失败路径的实际结果，解析真值和核验器依据分别说明。
- 测试/全量/Ruff/结构/学习核验的真实命令与结果、失败及修复。
- 已有 UNBOUNDED 数值债的范围，不能写成本步已解决或全状态已认证。
- 文件清单、scope diff、偏离/未解决事项与只读服务的独立性。
- Git status/branch/log、cached origin ahead/behind、push not_attempted、
  remote_sync_status 与完整本地提交身份；不修改全局 Git 配置。
- 下一步精确定价只作为建议，不实施。

报告自身提交用 git log -1 --format=%H -- tasks/reports/20261019-02-01_restricted-master_report.md
在提交后定位，避免自引用哈希。结束回执给出功能、真实核验、学习路径、限制、
本地提交及未推送状态，并明确停在第 2 步，等待 silo-solver-1010 审查。

