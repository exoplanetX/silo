# Revised Phase-I 来源行清理修正 — 执行报告

## 1. 合同、起点与交付状态

- 合同：[20261019-01-01_revised-phase1-cleanup](../codex/20261019-01-01_revised-phase1-cleanup.md)。
- 类型/风险：一个 L2 正确性任务；Git mode 为 local-commit，不 push。
- 实际起点：`cfb43a828bf4b77db4172cf530ac143dc8a56a88`，main，工作区干净。
  origin/main 缓存为 `5277d1d10fb0e962c3092d783d983fe50e675b8d`，差异 `0 1`。
  唯一 ahead 提交为本合同签发；当前继续执行授权明确覆盖该状态。
- 代码起点仍为 5277d1d；没有另发任务或改动原合同。签发时同日 TT 扫描已选用 01。
- 状态：实现、针对性及全量检查、学习核对、本地提交均已完成，交付待讨论对话审查。
- 结果代码提交：`ad62e0f9dda749e5db8d6ca27749c41fc8f14045`。报告提交通过
  `git log -1 --format=%H -- tasks/reports/20261019-01-01_revised-phase1-cleanup_report.md` 定位。

## 2. 实现与数学依据

原代码把人工基所在位置直接用作原始行号，随后用同一 kept_rows 选择矩阵行与基列。
新代码分别维护：

| 身份 | 依据与用途 |
|---|---|
| 来源行 K / kept_rows | 使用已有 StandardColumn.source_constraint，切原始标准形 matrix/rhs/row_names |
| 基位置 I / kept_basis_slots | 从 basic_columns 中去掉残留人工基的位置，保留其余列的基顺序 |
| 列编号 / kept_columns、column_map | 删除全部人工列，独立重编号剩余基列与非基列 |

每个人工列先核对清单唯一性、索引、role、来源唯一命中与对应正单位列。
缺失、不存在、歧义、错配或非有限列不会退回基位置。残留人工值非零、基求解失败、
非有限状态或行依赖检查失败均返回 NUMERICAL_ISSUE。

精确算术中，按匹配顺序有 B[:,I]=E_K，Q=(B^-1)[I,:]，Q[:,K]=单位阵。
QC=Qb=0 给出 C_K=-Q[:,Kc]C_Kc、b_K=-Q[:,Kc]b_Kc，故原可行集不变。
把行按 K,Kc、基列按 I,Ic 重排后 B=[[Id,H],[0,D]]；B 可逆直接推出
D=B[Kc,Ic] 可逆。剩余问题的对偶在 K 上补零，列关系与对偶目标保持不变。

生产实现解 B^T Q^T=E_I，并在现有 DEFAULT_TOLERANCE=1e-9 下独立检查
Q[:,K]、QC、Qb 的有限残差，随后实际求解剩余基。现有换出/枢轴/迭代规则不改。
换出助手原有的 direction failure continue 没有被当作零方向的充分证据；删除必须
另外通过独立 Q 检查。故障注入回归验证了独立行不会因此被删掉。

## 3. 清理后的原模型保护与范围裁决

只通过 QC 的小绝对残差仍不足以保证原空间候选有效。独立理论复核给出
x+(1+eps)z=M、x+z=M、max z 的放大反例；eps=5e-10、M=1e10 时，
精确解满足 z=0，近似删行却可能给出 z 约等于 M，原始行误差约为 5。

因此，现有私有 _optimal_solution 在本清理实际删除行后，复用既有
check_lp_optimality(model, candidate, tolerance=DEFAULT_TOLERANCE)。失败时返回
NUMERICAL_ISSUE，primal/dual/reduced-cost 最优依据均为空。未删行路径和 tableau
保持既有行为；没有新增字段、阈值、模型域、公共结构或求解算法。

主线程把这一保护裁定为同一清理正确性目标所需的私有结果验证，属于合同允许的
清理/来源验证辅助范围。它拒绝本次明确反例，不提供一般病态输入或所有状态的数值保证。

## 4. Red / green 与原模型真值

- 在未改动生产代码的 cfb43a8 源码上，最初 red 为 17 failed / 33 passed。
  增补人工清单与放大反例后，最终 red 为 **22 failed / 33 passed，0.25s**，pytest exit 1。
  旧实现对坏 inf 人工列还出现一条算术警告；新来源检查在求解前拒绝该列。
- 旧实现三行例保留 b,c，双残留例保留 c,d，直接违反预期原始行身份。
  多余来源、人工清单、独立方向失败与放大候选等断言也能识别错误。
- 初次 green 131 passed / 1 failed：唯一失败是错误来源同时构成重复来源，实际诊断为
  ambiguous，原测试要求 incompatible。修正断言并另加“唯一但互换来源”的不相容回归；
  未改变正确性期望或减弱失败保护。
- 最终针对性命令：合同列出的 cleanup、lp_duality、revised_simplex、revised_warm_start、
  dual_oracles 五个测试文件，**133 passed in 0.62s**。维护中的四个改动 Python 文件 Ruff 通过。
- 新增 cleanup 文件含 31 项确定性参数化检查；dual_oracles 增加 4 项混合行/负 RHS/
  presolve/双后端检查；旧失败保护改为成功回归，没有保留 xfail/skip。

三行例的真值来自原始等式 x=1,z=2：保留 a,c，矩阵为二维单位阵，剩余基号(0,1)，
目标3，原始乘数(a,b,c)=(1,0,1)，约化成本零；check_lp_optimality 在原三行模型通过。
四行双残留例 I=(0,1)、K=(1,3)，保留 a,c；加常数7后目标10，原始乘数(1,0,1,0)。
测试同时覆盖原始行排列、基位置排列、幸存基顺序和交错松弛列的编号映射。

其他覆盖包括无残留人工、空问题、零变量、全部冗余、重复行、目标常数、来源异常、
非单位人工列/NaN/Inf、正人工值、奇异基、基状态非有限、剩余基求解失败。
混合 LE/GE/EQ 模型的解析解为 x=1,z=2、目标10，负 RHS GE 行乘数为 -1；
每组原始/对偶依据独立核验，不要求退化后端的乘数逐项相同。

## 5. 有界 cold-solve 可达性调查

在主线程临时观察现有换出函数的输入/输出，没有修改代码或枢轴规则。固定12例为：

- 三行 x=1,z=2,z=2 的全部6种行排列；
- 四行 x=1,x=1,z=2,z=2 的原序、逆序与一次循环移位，共3例；
- 负 RHS 重复、增加空等式、以及 x+z=3、2x+z=4、3x+2z=7 各1例。

全部以 max x+z+7 cold-solve，12组原模型核验通过，目标均为10。
换出后共观察16个残留人工变量，来源行与基位置均相同，未找到异位残留基。
代码的 Phase-I 换入规则仍允许所有非基列参与；本调查不证明异位基不可达。
结论为 **当前确定性 cold-solve 对已构造异位基的可达性未确认**；清理函数的合法
输入反例与这一有限路径调查分开报告。

## 6. 全量、环境与学习交付

- 全量 `scripts/check_quality.py` exit 0：**1399 passed in 6.97s**，Ruff 通过，
  无测试跳过或警告。SciPy 已安装，原有可选外部参照实际执行。
  结构检查通过：140 份合同、137 份报告、94 个生产模块、441 个本地链接。
  `--write-index`、普通结构检查与 `git diff --check` 均通过。
  更新当前摘要的完成链接后，收尾结构复查为同样文件数、443 个本地链接，仍通过。
  九个交付 Markdown 文件的 UTF-8、代码围栏、展示公式定界符，以及六个稳定习题编号
  和真实 verified_code 均已检查；无代码/测试在全量核验后发生变化。
  后续修改只有文档与真实基线字段，代码/测试保持该被测版本，不重复运行全量。
- 环境：现有 .venv/Scripts/python.exe，Python3.13.9、NumPy2.3.5、pytest8.4.2、
  SciPy1.16.3。silo.__file__ 位于本检出 src/silo/__init__.py；console PATH 置于
  本检出 .venv/Scripts。未安装或升级包，未创建 worktree。
- 此环境继承系统包，没有把本次核验称为锁定环境的干净重建。
- 学习交付：[L0001 正文](../../learning/lessons/L0001-lp-duality/README.md)、
  [练习](../../learning/lessons/L0001-lp-duality/exercises.md)、
  [解答](../../learning/lessons/L0001-lp-duality/solutions.md)与目录，版本0.2.0。
  第3.2节手算删除前后矩阵，第4.4节区分依赖与块三角可逆性，第5节映射三个列表，
  第8节保留修复历史和数值/可达性边界；新增稳定编号 E06，共六题。
- 学习 verified_code 为实际实现提交 `ad62e0f9dda749e5db8d6ca27749c41fc8f14045`，
  verified_on=2026-10-19，状态 checked；提交产生前曾明确保持 draft/null。
  直接从正文提取并执行唯一 Python 示例，原始/对偶目标均为13；两个后端经现有
  presolve 恢复复算 E01=16、E02=13、E03=19，原模型核验均通过；E04 的零差距坏对偶
  被拒绝；E06 的 B、基本值、Q、三个依赖关系、剩余单位基及对偶目标10均已复算。
  E05 关系保持原代数推导，没有把数值检查当作完整定价证明。

## 7. 独立服务与裁决

theory_architect 只读复核一个指定代数对象，确认块三角论证并给出绝对残差放大反例；
其初始 decision_impact=weaken 针对“局部数值检查足够”的过强主张。主线程增加
最终原模型候选保护和对应回归，按其建议缩小数值声明。它没有执行实验或写文件。

red_team_reviewer 在补丁基本形成后独立检查合同与差异，返回条件 GO、
decision_impact=strengthen，未发现致命或重大问题；条件为实际完成全量、报告、学习与
可达性边界交付。上述检查与材料现已由主线程完成。它没有检查学习正文或重跑测试，
其审查不替代主线程实验；生产与测试共用核验器的断言没有被重复计票为独立证据。
专业服务无项目写入权、无文件改动/写入尝试、未访问 RB/MRC，也不决定阶段或任务晋级。

## 8. 文件、Git 与同步

唯一生产文件为 src/silo/lp/simplex/revised.py。三个测试文件、两份当前API参考、
L0001三文件、learning/CATALOG.md、当前摘要、本报告和派生任务索引均在允许清单。
未改 tableau、standard_form/Basis 公共结构、presolve/MIP、研究资产、原合同/旧报告、
依赖、CLI/schema、native、ROADMAP 或阶段文件。

已先提交四个被测代码/测试文件，提交 ad62e0f；随后提交学习/报告收尾，二者属于
同一原子任务。最初 commit 因当前环境未配置 Git user.name/email 返回128，未产生提交；
核对最近四个提交的同一既有身份后，以单次 `git -c user.name=... -c user.email=...`
参数完成提交，没有修改仓库或全局身份配置。没有 push 授权，不尝试推送。

代码提交后 main 相对 origin/main 为 `0 2`，当时只有本任务允许的文档待提交。
文档收尾首次提交后实际核对的 Remote Sync Proof 为：

- `git status --short`：空，工作区干净。
- `git branch --show-current`：main。
- `git log --oneline -5`：本任务文档收尾、ad62e0f 修复、cfb43a8 签发、
  5277d1d 研究资产、cd83009 导航整理。
- `git rev-list --left-right --count origin/main...HEAD`：`0 3`，包含签发1个及本任务2个提交。
- `git push result`：not_attempted（local-commit）。
- `remote_sync_status`：local_ahead_origin。

上述实际查询记录随同一文档收尾提交修订保存；结果提交哈希使用第1节命令定位，
结束回执再次核对最终哈希与干净状态。origin/main 为本地缓存，未声称实时网络核验。
此前接手检查的实时 GitHub 查询连接重置；本轮没有推送或重试网络查询。

## 9. 剩余限制与下一步

当前修正不改变绝对容差策略，不保证一般近奇异、尺度放大或其他状态的数值稳健性。
异位残留基的 cold-solve 可达性未确认。第2–7步、native和阶段转换均未实施。
完成后供 silo-solver-1010 审查本报告；后续 RMP 接口只作为另行批准的任务建议。
