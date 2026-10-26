# 20261026-03-01｜可靠研究原型基线与LP文件互操作

## 1. 元信息与直接授权

- 项目：silo-solver；工作区沿用当前检出。
- 执行对话：**silo-solver开发**，`01a15208-bea9-7030-aacc-95d785e8fa58`。
- 任务类型：一个整体工程维护/互操作任务，内部R1–R4检查点。
- 唯一主问题：把现有求解能力交付为可复现、可交换、可独立核验的研究原型基线。
- 用户先批准“固定研究基线、独立验证集、实际CI”三项，随后指令：“扩展更大的模型和扩展更广泛的模型结构这个稍等在深入讨论，现在先把其他讨论过的事情先做成任务交付执行。”又要求“继续完成任务”。
- 其他已讨论事项：补LP文件读写、巩固既有MPS/JSON、轻量资源准备；不扩规模、结构或算法。
- 来源与验收设计：[完整实施计划](../phases/reliability_io_20261026.md)。必须全文读取，不能只按本页摘要执行。
- 签发前提交：`50d3599aa4854ba74a44b599f6218a3d1c4c4e5c`；原算法锚点`a9f3213`，当前候选`0.3.0a1`。
- 分支：`codex/sparse-lp-reoptimization`。签发提交仅含计划/规则镜像/索引；执行时记录实际起点。
- 风险：L2文件/API/CLI，L3当前候选与CI交付，限本合同已批准范围；核心算法只读。
- 推荐模型：GPT-6 Sol / high；跨格式数值语义、独立真值与安装来源需要一致性核对。建议不等于已切换模型。
- Git mode：**push-on-success**，只允许第7节的一次任务分支同步；不merge/tag/release。
- 不调用create_goal/update_goal，不重开旧Goal，不创建重复Goal或定时自动任务。

## 2. 当前状态与边界

稀疏LP工程原八项目标已经结束。旧预算、warm3/5失败、warm4有限结论、RR04–07 HOLD和所有封存证据保持。
原研究A/B已验收、C HOLD、D/E未开始，native延期保持。
当前工作区两项治理差异明确保留并排除暂存：

- `AGENTS.md` SHA256 `2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638`
- 根通告 `研究主题固定_严重反面案例通告_20261020.md` SHA256 `0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221`

本次直接指令在当前已知分支、本地领先历史和上述受保护差异下执行本合同，不以通用旧模板要求先reset/clean或把它们提交。
发现其他来源不明的源码改动时先确认归属，不回退他人内容。
OneDrive保持退出，不自动启动或操作；不关闭其他用户进程，不更改电源、安全或全局环境。

## 3. 文件所有权与允许修改

“silo-solver开发”是本合同实现文件的唯一写入者；只读专业复核不写代码。共享工作区保留他人修改。

### 生产与接口

- 新增 `src/silo/io/lp.py`，必要的 `src/silo/io/formats.py`、`src/silo/io/number_codec.py`；后两者仅为当前文件任务的小助手。
- `src/silo/io/__init__.py`：只导出所列LP接口。
- `src/silo/cli/main.py`：增加LP读取和convert，保持旧命令与结果schema。
- `src/silo/__init__.py`、`pyproject.toml`、`CITATION.cff`：仅一致更新候选`0.3.0a2`；不改变生产依赖范围/许可证/发行政策，不添发布日期。

### 独立验证与CI

- `scripts/reliability/`：有限职责的冻结、oracle、接受、格式解析、跨平台安装检查器及必要入口；不建通用调度/宿主观察/profile系统。
- `tests/fixtures/reliability_20261026/`：本合同新冻结输入/真值/profile/比较规则；总计≤512KiB，冻结后只读。
- 新增 `tests/unit/test_lp_io.py`、`test_model_conversion_cli.py`、`test_reliability_tools.py`及必要同目录小fixture。
- `tests/unit/test_mps_io.py`、`test_general_json_io.py`、`test_revision_mps.py`：仅补当前I/O回归，不删除/放宽旧断言。
- `tests/unit/test_workbench.py`：仅同步当前候选显示断言，不改历史版本、性能范围或原研究状态断言。
- `.github/workflows/quality.yml`、必要的`.github/workflows/reliability.yml`；CI依赖constraints可放`scripts/reliability/`，不是生产依赖。
- `.gitignore`：仅在确有必要时增加本合同outputs/temp/cache忽略项，不取消已有保护。

### 文档、伴学与报告

- `README.md`、`CHANGELOG.md`、`docs/README.md`、`docs/general_solver.md`、`docs/development_layout.md`、`docs/installation.md`、`docs/mps_format.md`、新`docs/lp_format.md`、`docs/research_baseline.md`。
- `.silo-dos/project_profile.md`、`technical_route.md`、`decision_log.md`、`standing_approval_profile.md`：仅本任务状态和来源；保留旧记录。
- `scripts/workbench/catalog.json`：仅当前候选/格式/实际CI来源映射；不得改UI或旧研究状态来迁就本任务。
- `learning/lessons/L0017-model-file-io/`、`learning/lessons/L0016-reliable-solver/README.md`及其必要小练习增补、`learning/CATALOG.md`、`learning/GLOSSARY.md`。
- 本报告 `tasks/reports/20261026-03-01_reliability-io_report.md`、`tasks/INDEX.md`。
- 新运行证据只写`outputs/reliability_io_20261026/`，不纳入Git。

### 禁止修改

`src/silo/core/**`、`modeling/**`、`presolve/**`、`lp/**`、`mip/**`、`cuts/**`、`decomposition/**`、`uncertainty/**`及solver dispatch算法；既有`io/mps.py`、`io/json_reader.py`行为与字节；旧prototype/sparse_program脚本及fixtures/outputs/工件；旧不可变合同/封存报告；两治理文件。
不得扩充全局后端、改变数值容差/模型语义/解JSONschema、native、性能验收或原研究状态。
禁止修改既有任务合同，包括本合同。发现需要核心算法修复，按第6节交付失败证据，不进入数值修补循环。

## 4. 必须按顺序执行的检查点

### R1 基线、profile与新输入冻结

按实施计划建立当前基线、LP语法与独立精确比较规则。
先形成32模型、四编辑轨迹、独立oracle与输入/truth/profile/比较器哈希的冻结提交，**再修改任何生产src文件**。
接受集只由独立runner读取，不让pytest提前消费。开发用另一组手写例。
记录一次≤10秒资源快照，在测试子进程固定BLAS/OMP/MKL线程为1；不加频率/安静度硬门。

### R2 LP/MPS/JSON互操作

公开四接口：`read_lp_model`、`parse_lp`、`write_lp_model`、`model_to_lp`。
实现`optimize --format lp`/`.lp`和`convert INPUT --output OUTPUT`；旧输出职责、退出码与非MPS后缀JSON回退保持。
LP区间行按预定映射拆成两个有限侧，数字、默认界、域、名称和拒绝规则以计划第4节为准。
全部32模型做精确格式语义往返；6手写LP/6MPS/4JSON及20个LP拒绝例分别核对。
独立比较器禁止使用solver容差；加入小于solver容差的2^-39系数/界扰动拒绝例。
外部highspy1.15.1仅在验证进程对12模型×MPS/LP共24文件做readModel/getLp，不优化，不进入生产依赖。

### R3 有限独立接受

32模型为24LP（16最优/4不可行/4无界）+8MILP（6最优/2不可行），不新增结构。
四个预先冻结的有松弛间隙MIP可使用既有cuts=False/heuristics=False验证实际分支。
一轮160公开入口请求：64原模型、72格式后复求、16session、8修改后cold。最多两轮，具体分母与检查见计划第5节。
exact oracle提供真值；浮点返回点按既有原空间分量容差核验，不强加精确浮点点要求。
语义往返以精确数据相等为门，不能借求解容差吸收格式错误。

### R4 当前候选、隔离安装和实际CI

新候选0.3.0a2；旧候选和旧检查器保留。新增薄的跨平台checker，源码树外普通安装、`python -I`、模块来源、工件SHA、平台/依赖身份全部核对。
本地Windows3.13×dense/sparse×wheel/sdist四环境先通过。
远端拓扑固定：4源码质量job；8安装job（OS×3.11/3.13×dense/sparse，每job顺序核wheel/sdist）；1 Ubuntu3.13外部格式job，共13job。
每个安装环境≤24固定公开请求。CI静态重核冻结身份和安装smoke，不再跑完整160接受组。
当前远端代码同步后须获取绑定SHA的实际run/jobs/工件结果；只存在配置或queued/skip不算通过。
最终基线、学习材料和报告链接实际结果并保持其范围；不发起下一任务。

## 5. 检查及预算

全部预算是本任务新账，不复用/重置旧Goal费用。

- 本地自动验证、构建和安装合计≤60分钟；局部开发检查≤20批，全项目quality≤2次。
- oracle每例≤20000组合/2000000有理运算/30秒；病例规模不要求达到最大上限。
- 正式160组≤2轮，每轮≤15分钟；LP请求≤10秒、MILP≤30秒；输出保留原始退出/超时。
- 外部24文件解析≤2轮；候选构建≤2次，本地四环境安装≤2轮，只为一次真实I/O/工具修正保留重试。
- 远端≤2轮同SHA（初次+纯基础设施失败rerun）；quality job≤20分钟，安装≤15分钟，外部格式≤10分钟。单轮最多210 runner分钟，两轮≤420。
- 禁止在循环里以改名/新输出目录规避次数；嵌套求解、回归、安装请求分别记分母，不用全局profile捏造独立实例数。
- 超额或必需核心修改时，保留本地成果、失败和未完成项，停止本轮；不用剩余时间追加任务。

必须执行：独立freeze检查、新格式及CLI回归、原JSON/MPS回归、新接受组、结构、Ruff和适当完整quality、本地四环境、实际CI。
命令入口由新薄工具提供并在R1文档锁定；不得调用已结束的`sparse_program.py run/quality/install/summary`来登记本任务。

## 6. 验收、修正与停止

下列全部成立才写overall_complete=true：

1. R1冻结提交先于生产代码，输入/truth/oracle/profile/比较规则哈希未变。
2. LP公开读写与CLI在声明profile内完整、正例/拒绝例正确，JSON/MPS旧行为不退化。
3. 三格式独立精确语义核对、外部24文件解析和反扰动检查通过。
4. R3原生状态、目标、原始核验、MIP界及四编辑与冻结真值一致；无未解决必需项。
5. 本地quality及四环境通过，远端13个required job与16次工件核对实际通过。
6. 基线、L0017/L0016来源、报告和索引完成；最终diff全部在允许范围，两治理哈希未变。

首次接受组失败最多一次针对允许文件的集中修正。核心算法失败、禁改文件需求或耗尽额度则结束对应路径，不把它写成PASS；可以交付已完成模块。
CI若源代码/配置失败，只有一次push权限，保留失败和本地交付并停止远端路径；同SHA纯基础设施故障才可rerun一次。
不将“CI待运行/不可用”降格为通过，不因新的验证失败撤销旧程序原范围验收。
达到完成线或明确停止条件后交付停止，不启动扩容、结构拓展或新的合同。

## 7. Git、远端和公开边界

执行前核对origin确为现有`exoplanetX/silo`，只记录脱敏host/owner/repo，不输出凭据。
所有本地必需检查通过后，允许**一次**非强制push：

```text
git push origin HEAD:refs/heads/codex/sparse-lp-reoptimization
```

该仓库是public，任务分支源码同步后公开可见。该同步仅用于已批准的真实CI和版本保存；不更新main，不创建PR/合并/tag/Release/PyPI发布，不改访问权限。
若ref已分叉或push失败，保留本地提交并记录；不force、不改推送目标、不反复尝试或建立凭据。
GitHub连接器若只返回PR触发的run，不能据其空列表判断push CI未发生；改用现有`gh run list`/只读Actions API定位同SHA的push run，无需创建PR。
收尾报告允许一个本地文档提交：以源码哈希关联已过CI提交，明确报告提交尚未push；不为自引用再同步。
Remote Sync Proof同时报告缓存`origin/main`及实际任务分支；当前branch同步不冒充main同步。报告SHA用其文件Git历史定位。

## 8. 交付报告与伴学

报告路径固定为`tasks/reports/20261026-03-01_reliability-io_report.md`。
写明用户授权、实际起点/版本、四检查点状态、冻结/产品/工件身份、每组真实分母、预算、失败与修正、CI URL/SHA/jobs、允许diff及保护哈希、Git与未达项。
本项目采用该报告与`docs/research_baseline.md`承载本任务结果摘要，不新增另一套results状态树。
L0017按learning规范交付原理、区间/常数小例、代码映射、研究意义和局限、练习/解答；verified_code/on只填实际核对身份。
L0016只增加已实施方法的必要说明和交叉引用，旧教学核验身份不冒充新执行结果。

交付后停止。主协调会读取本对话结果；不另行向其他对话发消息。
