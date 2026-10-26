# 20261026-03-02｜仅收口R4：跨环境回归、资源采样与真实CI

## 1. 任务身份、来源与直接授权

- 项目：silo-solver；执行对话：**silo-solver开发**，`01a15208-bea9-7030-aacc-95d785e8fa58`。
- 原任务：SILO-RELIABILITY-IO-20261026；本单是同一任务块的RR02必要修复，唯一主问题是完成尚未通过的R4。
- 用户直接指令：“那就针对只收口R4吧，按照你的建议把剩下的问题处理了，制定任务交付执行吧”。这授权下列修复、验证和交付，不启动新算法阶段。
- 原合同：[03-01](20261026-03-01_reliability-io.md)；原规划：[R4与原完成线](../phases/reliability_io_20261026.md)；历史结果：[03-01报告](../reports/20261026-03-01_reliability-io_report.md)。三者只读。
- 起点HEAD：`08c35a4ceaef512a1da1cd5047beaa2784f23f02`；已推送产品：`42892035db426c4739b6c1a7ad9648852d2b1dc8`；R1冻结：`f8f00fd60728e0e9314342a3b4e037cfee50f790`。
- 分支沿用`codex/sparse-lp-reoptimization`。当前候选保持`0.3.0a2`；全部生产`src/`、版本与生产依赖只读。
- 任务类型：一个R4交付收尾合同，内部依次修复、验证、CI、报告；不另拆任务。
- 风险：L2测试/资源守卫语义，L3有限CI与工件交付；直接授权仅限本文。
- 推荐模型：**GPT-6 Sol / high**；难点是保留CG数值检验的严格性、处理Linux进程时序并关联真实安装身份。建议不等于已切换模型。
- Git mode：**push-on-success**，按第7节窄范围许可。执行者是实现的唯一写入者；共享工作区中不得回退其他人的内容。
- 不调用Goal创建/更新，不重开旧Goal，不创建定时任务；旧C HOLD、D/E未开始、native延期与规模/模型结构延期保持。

本修订只接续原R4。R1–R3继续依据其原源码/冻结输入/真值/原始结果验收；不重跑160请求组、不新造接受集、不修改原报告以覆盖失败。
本单成功时，由新报告把原R1–R3与新R4结果合并判定原任务完成；旧报告中的当时HOLD继续保留。
本文明确取代03-01在本次R4续接中对所列历史测试/资源脚本的禁改、已结束的续跑权限与一次push上限；其他禁止项保持。

## 2. 已观察失败与本次成功标准

旧CI：<https://github.com/exoplanetX/silo/actions/runs/40261995554>，绑定产品4289203，attempt1，结论failure。

| 失败 | 实际观察 | 修复完成应达到 |
|---|---|---|
| Ubuntu/Windows Python3.10 | `test_dag_cg_bound_consistency.py:177`期望`.25000000000000006`，实际`.2500000000000001` | 按实际返回数据独立核对数学条件，全部后续CG检查实际完成，保留确定性的负gap边界覆盖 |
| Ubuntu Python3.12 | `resources.py:39`缺VmHWM导致StopIteration，poll仍None | 字段缺失、退出竞态与不可测状态显式处理；峰值、deadline和子进程回收保持正确 |
| 下游未运行 | 安装matrix和external-format因quality失败skipped | 原定13个job全部实际成功，16次安装核验和24次外部读取有原始结果 |

日志未保存完整进程生命周期，唯一尾数来源与VmHWM缺失原因仍未证明。不得直接归因OneDrive、内存不足或GitHub服务。

## 3. 唯一写入范围

### 允许修改

- `tests/verification/test_dag_cg_bound_consistency.py`：限自然舍入回归及其必要小助手/诊断；保留原模型、独立Fraction/DFS与`_audit_round`的数学义务。
- `scripts/sparse_program/resources.py`：限Linux峰值读取、缺测状态、守卫异常清理；当前旧SHA为`ec3b18199d66ae614643201344898a8026d1c1f0ca0c7914fe82de983708c23c`。
- `tests/unit/test_sparse_program_support.py`：上述资源守卫回归；可新增`tests/unit/test_linux_rss_guard.py`，采用小型确定性文本/时序故障注入。
- `.github/workflows/quality.yml`：保持13-job拓扑，补本修订身份核对和必要日志/失败收据；不得减少平台、矩阵、断言或required步骤。
- 新增`scripts/reliability/r4_closure.py`：薄的RR02范围/身份核对与收据入口；不创建通用编排器，不调用旧runtime.run/append写旧账本。
- `scripts/reliability/artifacts.py`、`check_installed.py`、`external.py`、`parse_external.py`：只有新到达的R4路径产生可定位错误时，允许一次集中平台/路径/失败收据修正；不得改已通过的模型、期望、请求分母、精确比较规则或优化语义。
- `tests/unit/test_reliability_tools.py`：仅相应R4工具边界回归，使用另行手写微例。
- `README.md`、`docs/installation.md`、`docs/research_baseline.md`：当前CI/安装身份与限制；`scripts/workbench/catalog.json`及`tests/unit/test_workbench.py`仅对应状态/来源字段，不改UI或旧研究状态。
- `.silo-dos/project_profile.md`、`technical_route.md`、`decision_log.md`、`standing_approval_profile.md`：仅本修订授权、真实状态和来源。
- `learning/lessons/L0016-reliable-solver/README.md`及必要的`exercises.md`、`solutions.md`、`learning/CATALOG.md`：第8节伴学交付。
- 本次报告`tasks/reports/20261026-03-02_reliability-io_report.md`、派生`tasks/INDEX.md`。
- 本次本地证据根`outputs/reliability_io_r4_20261026/`；CI可沿用各次干净checkout中的`outputs/reliability-ci/`。生成证据/工件/环境不进Git。

### 保持只读

- **全部`src/**`、`pyproject.toml`、`CITATION.cff`**，包括LP/MIP/CG实现、I/O、dispatch、容差、返回schema、版本和生产依赖。
- `tests/fixtures/reliability_20261026/**`、`docs/lp_format.md`、`scripts/reliability/oracle.py`、`exact.py`、`freeze.py`、`accept.py`、`check_result.py`、`worker.py`、`runtime.py`、`static.py`及其他未列文件。
- `tests/unit/test_dag_column_generation.py`及已有负gap/阈值单测保持；可运行，不得削弱。
- 除明确放行的`resources.py`外，旧prototype/sparse_program全部脚本、冻结清单、输入、工件、账本和已封存收据；全部现有合同和03-01报告。
- 两治理差异保护并排除暂存：`AGENTS.md` SHA`2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638`；根`研究主题固定_严重反面案例通告_20261020.md` SHA`0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221`。

当前已知分支领先main及这两项差异属于获准续接状态，不reset/clean、不先main归零。OneDrive保持退出，不控制用户进程/电源/全局环境；只回收本任务自己启动的测试子进程。

## 4. CG回归：保留数学强度，解除特定尾数绑定

1. 先核对旧失败日志与自然问题的所有后续断言，保留问题数据、真实原生求解入口及`Fraction(-7,4)`最优真值。
2. 对实际返回权重独立重算原空间行活动、非负性、目标、完整DAG列成本/约束、精确dual shift、rho与上下界。
   继续使用原`_audit_round`的`1e-9`数学门；`fsum/ulp`等关系按实际数据精确重算。禁止宽泛`approx`吞掉后续检查。
3. 把固定权重尾数/固定目标尾数改为上述数学不变量。自然端到端例允许合法的零、正微量或负微量gap；负gap仍须满足原`-g <= eta <= tolerance`，保持返回权重和有符号gap，不钳零、不改原生结果。
4. 复用`test_dag_column_generation.py`中的确定性故障注入：负gap inside/equal/outside/equal_budget/over_budget、正gap阈值及大常数冲突。
   必须实际执行这些单测；证明“自然回归跨环境正确”和“负gap分支/拒绝阈值仍有覆盖”分别有证据。无需再造整套注入框架。
5. 不因平台或依赖版本skip/xfail，不删Python3.10，不修改生产容差、算法或依赖以规避原失败。

## 5. Linux RSS：显式缺测、保留守卫、保证回收

1. 对`/proc/<pid>/status`解析作小型可测处理，区分有效VmHWM、无字段、文件消失、畸形值和读取失败。
2. 缺测时保留先前真实峰值，继续检查退出与墙钟deadline；有限重试/等待受原child deadline约束，不以无限retry等待字段出现。
3. 持续不可测必须明确失败并记录原因；不把无字段当有效0、不把VmRSS冒充峰值、不把采样失败改成solver limit或正常成功。
   进程已退出且已有有效峰值时保留结果与真实退出码；没有有效样本应明确未测，不能签发有效内存核验。
4. 用覆盖采样循环的异常清理保证自建直接子进程终止/回收，保留主错误。Linux原范围仍是root；Windows原后代树采样与清理范围保持。
5. 新定向用例至少覆盖：有效字段换算；首次缺失后恢复；已退出/文件消失保留峰值；畸形/持续不可测的可见失败；采样异常回收；缺测过程中deadline继续生效。
   故障注入用例在Windows也运行，纯Linux真实`/proc`核验在Ubuntu执行。原normal/timeout/rss和Windows后代/ctypes回归继续通过。

**历史身份处理：**旧RR08的driver map与`_drivers_unchanged`锁定旧resources SHA。本次新工具记录旧/新SHA、修复提交和新验证；旧运行只在旧工具身份下解释。
不修改旧manifest/收据，不重跑旧fixed/warm/summary去使新工具冒充旧签收，不向旧账本登记本次成本。旧固定范围的验收结论保持。

## 6. 验证顺序、工件和CI

### 本地修复与核对

执行前记录真实HEAD、Git差异、远端任务分支、保护哈希和原报告/原证据身份；把本单登记到新报告与新证据根。
先定向CG/资源单测，随后完整quality、Ruff/结构、原`prototype/evidence.py --verify`及`python -m scripts.reliability.freeze`（零SILO求解）。
继续用选定虚拟环境的console-script PATH和子进程线程1，不重复原PATH失败，不修改全局PATH。

新增薄入口`python -m scripts.reliability.r4_closure --verify --output OUTPUT`核对：

- 所有生产`src/`文件列表/内容与4289203一致（记录raw与严格LF语义），版本/生产依赖身份不变；CI获取所需Git提交，不依赖忽略outputs。
- R1 manifest及五个冻结对象未变；R1先冻结后生产的既有历史成立；两治理哈希保持。
- 允许diff与resources旧/新SHA清楚；原03-01报告/原始结果只读。CI可用Git跟踪身份复核历史报告，不要求本机旧outputs存在。

原四个本地安装通过证据可以沿用，但须核实原工件SHA、生产来源和当前checker均相符并标明沿用。
本单若改安装/外部checker，则对应结果不自动沿用：在push前用当前工具定向重核。本地必要新构建/四环境最多两轮，见第7节；保留旧工件不覆盖。
远端始终从当次提交构建一套共享当前候选wheel/sdist，记录新SHA；候选仍0.3.0a2，不把新打包字节冒充旧工件。

### 实际CI固定完成线

维持原13-job拓扑与检查强度：

- 4源码质量：Windows/Ubuntu × Python3.10/3.12；上述CG和RSS回归必须实际进入运行。
- 8安装：Windows/Ubuntu × Python3.11/3.13 × dense/sparse；每job两个不同新环境核同一共享wheel/sdist，共**16次工件核验**。
- 1外部格式：Ubuntu/Python3.13，highspy1.15.1只做**24次readModel/getLp**，优化调用0。

安装仍为源码树外普通安装、`python -I`、运行/元数据版本、实际解释器/平台/site-packages、工件SHA/direct_url、全部loaded modules来源核对。
安装依赖NumPy2.3.5，sparse额外SciPy1.16.3；dense无SciPy；独立外部解析环境不污染安装矩阵。
每安装环境仍为原24公开请求；不扩充、不把其嵌套LP称独立实例，不运行整套160接受组。
required步骤不得skip/xfail/continue-on-error。平台固有的既有条件skip原样保留，不能新增skip规避本单失败。
日志应保存实际依赖、失败阶段、原始退出码及工件报告。拿不到报告只说明未完成，不能靠上传空占位文件记PASS。

## 7. 有界修复、推送与停止

本修订是用户新批准的有限R4续接额度。原03-01已发生的质量2次、CI失败1次、push1次及全部本地成本保持；新收据同时列旧/新增/累计，不重置旧账本或借用旧余量。

- 本次本地自动核验/构建/安装累计≤**30分钟**；定向开发检查≤**12批**，完整quality≤**2次**，静态身份核对≤**3次**。
- 如确需重建/重装：构建≤**2次**、本地四环境≤**2轮**；外部checker变动后的定向24读≤**2轮**，全部计入30分钟。第二轮仅用于真实修正，不覆盖前次失败。
- 全质量后发生有行为影响的允许修改，应在剩余质量额度内复验；不得用只跑通过子集替代最终完整quality。
- 新CI最多**2次完整尝试**，最多**2次非强制代码/config push**。第二次仅用于首次CI暴露的、仍在本合同允许范围内的一次集中修正；或同SHA纯基础设施rerun。二者共享第二次额度，不另加第三次。
- 这是仅对RR02的§6.4一次push规则窄例外。每次push前所需本地检查均通过；首次成功即停止，不为用满额度再推送。
- 固定refspec：`git push origin HEAD:refs/heads/codex/sparse-lp-reoptimization`。核对现有public仓库exoplanetX/silo与非分叉远端；push传输失败即保留本地并报告，不自动重试网络推送、不force/改目标。
- 每quality job≤20分钟、安装job≤15分钟、外部格式job≤10分钟；每次最多210 runner分钟，本修订≤420新增runner分钟；等待和实际费用分开记。
- 两次CI均保留SHA/attempt/jobs/日志/工件；第二次CI只接受与本次修复相关的更改。CI仅排队或服务不可用时如实未完成，不以本地结果替代。
- 最终收尾报告可本地提交，明确其相对最后实际CI提交的差异；不因报告自引用追加第三次push。源代码/工件检查工具若又变则不得关联成已过CI身份。

发现需要任何生产算法/I/O/预处理/搜索/容差改动、原R1–R3真值改动、矩阵缩减或额外额度时，保存最小失败包和未达项后结束本轮；不自行扩大。
必要独立只读复核应核对CG数学门、资源状态/清理和真实CI矩阵；其审查不执行新的求解/安装或改文件。

## 8. 报告、伴学与最终验收

新报告固定为`tasks/reports/20261026-03-02_reliability-io_report.md`。不修改03-01报告。
报告逐项记录：授权/起点、两类修复原因与未证归因、允许diff、production/冻结/工具/工件SHA、所有成功与失败、真实分母、预算旧/新增/累计、CI URL与每job结果、Remote Sync Proof、学习材料及未达项。
Remote Sync Proof同时核缓存origin/main和实际任务分支、push次数与结果；当前任务分支同步不冒充main同步。

**Learning delivery：更新L0016的R08/核验说明及一个必要辨析练习。**解释数学不变量与浮点尾数、自然集成例与确定性故障注入、缺测与真实资源超限的区别；给出5.55e-17小例、代码映射、研究价值与局限。
保持既有正文与原verified_code/on；增补段落在修订记录单列实际核验提交、日期和用例，不把旧8组教学小例冒充新运行，也不为本次补丁新建篇目。

下列全部成立即可签收原任务并停止：

1. 原R1–R3输入/真值/代码身份与原通过证据保持，所有`src/`仍为4289203；无新增原生算法变化。
2. 自然CG例的完整数学核验跨原矩阵通过，确定性负gap/阈值覆盖保持且实际执行。
3. RSS缺测/退出/错误/清理定向回归通过；原Linux normal/timeout/rss与Windows相应回归通过；缺测未记成有效0或solver limit。
4. 当前最终允许变更完整quality、结构/Ruff、两个冻结静态核对通过，原本地四安装沿用或必要重核的理由/身份明确。
5. 最终实际CI **13/13 job成功、16/16安装核验、24/24外部读**，共享候选身份、模块来源与全部required步骤有原始证据。
6. 新报告、L0016增补、索引/镜像和保护文件核对完成；明确旧失败保留、候选仍0.3.0a2、旧Goal继续complete。

任一项未满足则`overall_complete=false`并写清尚缺什么。达到以上完成线或本单停止条件后交付，禁止自动进入扩容、结构拓展、native、研究C/D/E或下一任务。
