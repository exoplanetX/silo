# 第 1 步交付：Revised Phase I 冗余行来源映射修正

## 1. 任务元信息与执行授权

- ID：20261019-01-01_revised-phase1-cleanup；2026-10-19 扫描同日合同/报告后使用首个 TT。
- 类型/风险：L2，现有 revised simplex 正确性/稳健性修正；对应既有 Phase 3。
- 用户授权：2026-10-19 明确要求将七步计划的第 1 步交给“silo-solver开发”执行实施。
- 签发/审查对话：silo-solver-1010，thread `01a1254a-b349-77d0-8c66-d4b711cd511f`。
- 唯一执行/文件写入协调对话：silo-solver开发，thread `01a15208-bea9-7030-aacc-95d785e8fa58`。
- 工作目录：`E:/OneDrive/workspace/codex/silo-solver`。
- 已核查的代码起点：`5277d1d10fb0e962c3092d783d983fe50e675b8d`，main，工作区干净，
  本地 origin/main 差异 0/0。实时远端此前查询失败，不将缓存引用当成实时远端证明。
- 签发提交：用本合同的 `git log -1 --format=%H -- <本文件>` 定位，交付消息给出实际哈希。
  执行开始 HEAD 应为该签发提交：它只增加合同/索引及更新当前摘要，源码仍为上述起点。
  当前用户授权包含从这一个已知、尚未推送的签发提交继续执行；无需为其 local-ahead 重复确认。
  若发生其他代码提交、分歧或无关脏文件，先说明差异，不擅自重置或覆盖。
- Git mode：**local-commit**；完成本任务后本地提交，**不 push**。
- Expected report：`tasks/reports/20261019-01-01_revised-phase1-cleanup_report.md`。
- Learning delivery：更新 L0001 正文/习题/解答及目录，保持篇目 ID 与路径。
- 执行建议：GPT-6 Sol / high；难点为行依赖、两套索引、原始对偶恢复的一致性。
  建议不等于模型已切换；如实际配置不同，按事实记录，不自行升至 Astra。

## 2. 一句话目标及责任边界

修复 `_remove_artificial_columns` 对“原始行身份”和“基位置”的混用，使残留人工
基变量为零且无法换出时，正确删除可证明冗余的来源行，并保留可逆、原模型等价的基。

本任务承接前期 LP 对偶/核验工作，不新做 solver。完成实现、测试、伴学交付、报告和
一个实现提交后停止。七步计划的第 2–7 步均不在本次执行范围。当前讨论对话只审查交付，
不得把开发对话收到的任务自动扩展为新能力线或后续任务。

## 3. 开始前必读与已确认现状

先读 AGENTS.md、tasks/README.md、.silo-dos/project_profile.md、technical_route.md、
remote_sync_proof.md、learning/README.md、learning/WRITING_GUIDE.md。
再读以下源码与证据，不需要重审全部历史资料：

- `src/silo/lp/simplex/revised.py`：`_remove_artificial_columns`、
  `_pivot_artificial_basics_out`、`_compute_basis_state`、`_original_dual_values`。
- `src/silo/lp/simplex/standard_form.py`：`StandardColumn.source_constraint` 已存在，
  人工列按其来源约束名记录；当前无需新增公共 schema 或重造标准形。
- `src/silo/lp/simplex/basis.py`：基列顺序是基位置顺序，不保证等于原始行来源顺序。
- `tests/unit/test_lp_duality.py` 中
  `test_existing_revised_cleanup_slot_source_limit_fails_without_dual_claim`。
- `src/silo/lp/optimality.py`、`tests/verification/test_dual_oracles.py`。
- `docs/lp_duality.md` 与 `learning/lessons/L0001-lp-duality/README.md` 第 8 节。
- `tasks/reports/20261018-01-02_lp-dual-optimality_report.md`。

已知现象：一个合法、原始可行的 Phase-I 构造基在当前清理后得到奇异基，并由已有
线性求解返回 NUMERICAL_ISSUE。前期没有证明当前确定性枢轴规则能到达这个构造。
必须区分“清理函数的有效输入边界”与“实际 cold-solve 路径可达性”；不可把后者写成
已证实的用户实例故障，也不可只因未找到可达路径而忽略清理例程的行身份问题。

## 4. 数学对象、修正原则与必要证明

在当前标准形中，令 C 为全部非人工列、b 为 RHS，B 为 Phase-I 的可逆基矩阵。
清理枢轴后仍为基变量的人工列 e_k 来自原始标准化行 k，位于基位置 i。
设其基位置集合为 I、按匹配次序排列的来源行集合为 K。

当残留人工值为零且该变换行在非人工列中找不到换入列，令
Q=(B^{-1})[I,:]，则满足 Q[:,K]=单位阵、Q*C=0、Q*b=0。
这给出可删除来源行 K 的独立行依赖。删除 K 行、删除 I 位置的人工基列后，
剩余基为 B[K^c,I^c]；互补子式关系给出其非奇异性。浮点实现只能在现有容差下
检验相关条件，报告必须保留这一限制。

实现必须分别维护：

1. `kept_rows`：原始标准形行中排除来源行 K；据此切 matrix/rhs/row_names。
2. `kept_basis_slots`：基位置中排除 I；据此选择剩余 basic_columns。
3. `kept_columns`：排除全部人工列，构造独立的旧列→新列映射。
4. 剩余基列必须经列映射重编号；不能继续用 kept_rows 下标选 basic_columns。
5. 每个人工列应从已有 source_constraint 查找唯一来源行；核对来源与该人工单位列
   相容。来源缺失、不存在、不唯一或不相容时保守返回带原因的 NUMERICAL_ISSUE，
   不回退成基位置、不默认选第 0 行、不让 KeyError/ValueError 泄漏为崩溃。
6. 保留已有人工变量换出逻辑、可行性判断、枢轴规则和迭代限制。正的残留人工值
   及非奇异性无法确认的数值失败，仍须保守退出；不伪造 OPTIMAL 或对偶值。

不要求特定代码写法；要求上述身份与代数条件明确、实现可读、测试能识别两套索引。

## 5. 首个确定回归案例：三行、两个变量

原模型为 max x+z，x,z>=0，等式行依次为：

```text
a: x = 1
b: z = 2
c: z = 2
```

用现有 build_standard_form 构造后，列顺序应核对为
`x,z,artificial_a,artificial_b,artificial_c`。
提供有效基 `basic_columns=(3,0,1), nonbasic_columns=(2,4)`。
残留 artificial_b 来自原始行 b（0-based 行 1），位于基位置 0，人工基本值为 0。

当前实现误删行 a，剩余两行相同而奇异。修正后应：

- 删除原始行 b，保留 row_names=('a','c')；删除基位置 0。
- 删除全部人工列后基列为 (0,1)，剩余矩阵为二维单位阵，基有效且非奇异。
- 进入现有 Phase II 后得到 OPTIMAL，x=1、z=2、目标 3。
- 恢复原始三行的 dual/reduced costs，删除行的乘数为零；在原始模型上
  `check_lp_optimality` 通过，不能只检查 reduced problem。

把旧测试中对 NUMERICAL_ISSUE 的期望更新为正确结果，并重命名以表达修复目标。
先留下基线 red 证据，再实现 green；不要让旧“预期失败保护”长期锁住已修行为。

## 6. 其余必须覆盖的测试

至少包含以下可区分逻辑的确定性小例，允许参数化而非机械复制测试：

- **两个残留人工变量**：行 a:x=1,b:x=1,c:z=2,d:z=2；列顺序
  x,z,artificial_a,artificial_b,artificial_c,artificial_d。
  基 (3,5,0,1)，非基 (2,4)，使 I={0,1}、K={1,3}；应保留 a,c 与 x,z 基。
  同时验证基位置、来源行和列重编号，原始目标为 3。
- 至少一个行顺序或基列顺序置换，确认没有暗含“位置即来源”的假设。
- 无残留人工、全部行冗余或零行/零变量边界、重复等式；保留常数项的一例。
- 负 RHS 归一化，以及已有 LE/GE/EQ 混合模型；原始行乘数符号、目标值和互补条件
  正确。退化时比较每组见证的有效性，不强制不同后端乘数逐项相同。
- 缺失/不存在/歧义来源或不匹配人工列的输入，返回明确数值失败；已有正人工值、
  奇异基等保护路径保持保守，不产生虚假最优结果。
- 运行已有 cold-solve、presolve 恢复、暖启动和双后端原模型核验回归。
- 做有界的可达性调查（读代码或少量固定小例即可），报告是否找到当前枢轴路径到达
  source/slot 不同残留基的实例；查不到就如实写“未确认”，不开展无界搜索。

测试的主要真值来自原始等式、已知解与独立原模型核验，不能只比较两个内部后端。
可在测试中使用既有可选外部参照；原生算法内禁止调用外部求解器。

## 7. Scope lock：唯一允许写入的文件

- `src/silo/lp/simplex/revised.py`：仅本清理/来源验证与必要的小型私有辅助函数。
- `tests/unit/test_revised_phase_one_cleanup.py`（新建）、`tests/unit/test_lp_duality.py`。
- `tests/verification/test_dual_oracles.py`：仅与本修正有关的原模型核验覆盖。
- `docs/lp_duality.md`、`docs/lp_solver.md`：更新本边界的当前状态与适用说明。
- `learning/lessons/L0001-lp-duality/README.md`、`exercises.md`、`solutions.md`；
  `learning/CATALOG.md`：仅相关版本、来源和目录描述。
- `.silo-dos/project_profile.md`：完成后更新当前状态/下一步，保留对话职责划分。
- 本任务的新执行报告；由脚本重新生成的 `tasks/INDEX.md`。

如无需某项文件改动，不为了填满清单而改动。原合同保持不可变。

禁止：新求解器、RMP/定价/列生成实现、minimize/一般变量界能力、tableau 修改、
StandardForm/Basis 公共结构改造、枢轴策略/容差/迭代规则变更、presolve/MIP 重构、
新增 CLI/JSON/API 字段、依赖/build/native、阶段转换、研究资产/探针/旧合同报告改动。
禁止为新案例弱化核验、无理由 xfail/skip、宣称已完成后续研究方向。

## 8. Learning delivery：L0001 如何更新

阅读既有十节体例，在 L0001 中说明“基位置、来源行、列重编号”的区别，给出上述
三行手算矩阵与删除前后对照、冗余依据和双索引实现映射。第 8 节由“当前已知限制”
更新为“该版本已修复的历史反例”，保留证据与可达性未确认的范围。

增加一道对应练习（如 L0001-E06）与完整解答，并更新实际题数与入口描述。
研究意义限定为为对偶恢复/后续主问题求解提供稳健基础；不主张新算法或性能加速。
写清新元信息、修订原因、真实测试/代码基线。不能在一个提交内填写未来自身哈希：
可先提交被测实现与测试，得到确切代码提交，再更新 checked 讲解及报告形成同一任务
的文档收尾提交；两提交仍是一个原子任务。也可先保持新增内容 draft，由本对话审查
后完成基线收尾。不要把修改前的 5277d1d 填成修复后实现已验证的代码版本。

## 9. 执行流程、检查与验收

1. 记录 preflight：实际 HEAD/branch/status、origin/main 差异、导入路径、环境。
   用户已授权该 L2 任务，不能仅因新行为属于 L2 再索要相同授权。
2. 先写/更新能识别该错误的回归，在旧实现记录 red；原始构造基与已知最优解要检查。
3. 最小实现并运行针对性 green；必要的只读理论复核聚焦第 4 节代数义务。
   专业服务不得改文件或代跑实验；主执行对话是唯一写入者。
4. 完成学习说明和当前参考文档；先创建对应执行报告，再刷新任务索引。
5. 从项目根目录、使用已有虚拟环境执行（无需重复安装/升级依赖）：

```powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_revised_phase_one_cleanup.py tests/unit/test_lp_duality.py tests/unit/test_revised_simplex.py tests/unit/test_revised_warm_start.py tests/verification/test_dual_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
```

若使用隔离 worktree，显式令 PYTHONPATH 指向该检出的 src，PATH 使用对应 console
环境，并记录真实导入文件。代码稳定并全量通过后，无新变更/失败不重复跑全套。

验收条件：数学映射可说明；单/多残留及置换案例通过；错误来源保守失败；原始 primal/
dual 核验、现有 LP/MIP/CLI 回归和全量质量通过；L0001 实际验证/元信息诚实；
scope diff 只含允许文件；报告与索引齐全；本地提交，未推送；完成后停止。

## 10. 停止条件与执行报告

遇到证明不成立、来源元信息不足且需公共结构改动、无关文件变化、必须修改禁改模块、
需要新容差/枢轴策略或外部求解器才能成立时，保留证据、报告最小阻塞范围，交回讨论
对话裁决。不要自行扩展任务、重置工作区、修改原合同或进入第 2 步。

报告必须包含：实际起点与结果提交定位、文件清单、核心映射和证明条件、red/green、
原模型真值和检查、可达性调查范围及结论、全量结果、环境、学习交付与验证基线、
只读复核的独立性及未解决事项、Git/未推送状态、供本对话审查的结论。
报告结果提交通过 `git log -1 --format=%H -- tasks/reports/<report-file>` 定位。

结束回执使用明确事实：做了什么/为什么成立、测试与未核验范围、学习路径、实际
commit/status/ahead-behind/push 状态及下一步建议。等待审查，不自动实施第 2 步。
