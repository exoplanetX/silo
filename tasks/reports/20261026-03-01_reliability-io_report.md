# 20261026-03-01｜可靠研究基线与LP文件互操作执行报告

**结论：R1–R3及本地交付通过，R4真实CI失败，overall_complete=false；已按合同停止。**
候选0.3.0a2的LP读写、转换、独立同域接受和四个本地安装环境已完成。
跨平台持续集成尚未达到完成线，不能把本地通过写成整体通过。

## 1. 授权、身份和范围

依据[唯一合同](../codex/20261026-03-01_reliability-io.md)与[全文计划](../phases/reliability_io_20261026.md)。
讨论对话silo-solver-1010的直接用户消息：01a175ca-3256-7e41-b346-a16da428d7c3批准三项巩固，
01a175e9-3d8e-7362-a177-911cb166af7d要求其他已讨论事项交付执行并延期规模/结构拓展，
01a17602-d1ce-72b3-a29a-75ae5af7b57e要求继续完成。主线程实际读取核对了这些消息。
L2/L3许可限本合同，沿用当前分支与两项已登记治理差异；silo-development-operator流程已应用。

- 实际起点/签发提交：315fecbbd8f601edf7283949a7ea1d444700c987。
- 分支：codex/sparse-lp-reoptimization；起点相对缓存origin/main为0/101。
- 冻结提交：f8f00fd60728e0e9314342a3b4e037cfee50f790；起点至冻结提交的src差异为空。
- 产品/CI提交：42892035db426c4739b6c1a7ad9648852d2b1dc8；原算法锚点a9f3213。
- 原始源码与LF规范化来源分别保存source_lock.json；后者整体SHA为d551b7e90e7a3ac5c82dafb86ad5397c55739f74b27ccb369b1e02333df902dd。
- 当前任务未调用Goal API、未重开旧Goal。旧Goal complete、原C HOLD/D/E未开始、native延期保持。
- OneDrive保持退出；未关闭其他用户进程、改变电源或全局环境。子进程线程均设1。

## 2. 四检查点实际结果

| 检查点 | 结果 | 实际依据 |
|---|---|---|
| R1 基线与冻结 | PASS | 32基础模型+4编辑状态；独立有理oracle、语法、比较规则先提交；保护哈希不变 |
| R2 文件互操作 | PASS | 四个LP公开函数、LP optimize与convert；96格式往返、16手写正例、25拒绝例、2微扰；外部24只读解析 |
| R3 独立接受 | PASS | 首轮160实际公开入口全部通过；152隔离执行单元；零失败/超时；未用第二轮 |
| R4 工件/CI | HOLD | 本地四环境通过；实际CI质量1/4成功，远端16安装及24外部读未运行 |

全部新运行证据位于outputs/reliability_io_20261026，不纳入Git；ledger.jsonl为本单追加账本。
本单未写入旧工件/原始运行证据/账本；Git跟踪的旧程序、旧输入/真值/合同/封存报告差异为空。

## 3. R1：冻结与独立数学依据

冻结夹具53480字节，低于512KiB。24LP为16 optimal、4 infeasible、4 unbounded；
8MILP为6 optimal、2 infeasible；四个指定MILP的松弛点有分数且界严格优于整数最优。
RHS、变量界、增行、增列四个新状态也先获真值。
oracle不导入SILO/NumPy/外部优化器，按原数据Fraction(value)枚举顶点与有限整数格；
最优性附原始对偶依据，不可行附正矛盾组合，无界附实际可行锚点和改善方向。
实测每例最大120候选基、
1084计量有理运算、
0.001655秒，均低于20000/2000000/30秒上限。
接受集未注册为pytest参数；开发只用另一组手写微例。这是操作性保留集，同一执行者能读取，不称真正盲测。

| 冻结对象 | SHA256 |
|---|---|
| `tests/fixtures/reliability_20261026/inputs.json` | `87940f04363d344b8399759ccdd1a78a00e69ac22b06f1bbf5f3b8acd405ec89` |
| `tests/fixtures/reliability_20261026/truth.json` | `62208f41363b9cb3c1a9ff8e5321ba48f40280240bec61020fd37727749f89ee` |
| `docs/lp_format.md` | `ebf93dd79ad700e5f1b9f2ffd3f8df42011b6a50b5379ba5fe5a1532e988d2e3` |
| `scripts/reliability/oracle.py` | `1a7446eba8d90582ef22a035275edaf52b9bff274658502a87725be9dbcecfec` |
| `scripts/reliability/exact.py` | `b59c23b10a1f8f6c1d48e3fe7cc373549255fda7fd34f1cfec23d9a3f24fae4f` |
| manifest.json | `2fa296f567a96af88796bf0c392830c29740cfc44ea2cd290880a9d03e5a4291` |

开始资源快照耗时0.214秒：Windows11、Python3.13.9、20逻辑处理器、32GiB RAM，
可用约17.1GiB；NumPy2.3.5/SciPy1.16.3。它只说明开始时资源，不建立宿主稳定性或频率门。

## 4. R2：实现、格式与开发修正

新增silo.io.read_lp_model/parse_lp/write_lp_model/model_to_lp及小型数值codec；
CLI optimize增加LP，convert按json/mps/lp读写且不求解、拒绝同一路径，保持旧schema2/退出码/JSON回退。
core/modeling/presolve/lp/mip/cuts/decomposition/uncertainty、solver dispatch、旧JSON/MPS解析器未修改。
LP区间拆行名称按冻结映射防冲突；零列身份、目标常数、界和整数域保留。

实际开发检查：首批303项I/O及旧回归通过，后续304项通过；针对修正的90项通过。
Ruff开发失败均为已保存的导入排序/行长/style问题，实际修正后通过。
独立只读源码复核/root/reliability_implementation_review指出并核对了两项修正：
区间原名obj消失后目标label稳定选择；外部无穷映射按侧拒绝NaN/错误方向。
复核还促成worker记录实际模块来源与入口jsonl，分开发出请求数和真实入口数。
另在数值token转换前检查Decimal有限/下溢，避免超大指数分配巨大有理数。
这些在正式接受前完成；没有正式接受失败或接受后生产修补。

精确格式门逐模型逐格式32×3=96，稳定重写通过；手写LP6/MPS6/JSON4，25非法LP，
系数/界各一次2^-39扰动均明确拒绝。期望直接从原始payload构造，实际读公开解析数据；
格式门不使用solver容差。JSON/MPS保留原有更强行对象语义。

外部highspy1.15.1在独立全新环境执行12模型×MPS/LP=24次readModel/getLp，
逐名精确比较全部目标、界、整数格和约束侧，全部通过；优化调用0。
高层runner、实际原始矩阵与独立返回保存parse1/requests.json、raw.json、summary.json。

## 5. R3与本地完整质量

首轮正式160请求于49.471秒完成（整轮≤900秒，LP每入口≤10秒、MILP≤30秒），全部通过。
真实入口jsonl与各worker原始结果、原始/解析payload、来源哈希和独立检查收据全部保存acceptance1/。

| 组 | dense+sparse实际请求 |
|---|---:|
| 32基础模型直接求解 | 64 |
| 8LP+4MILP的JSON/MPS/LP后复求 | 72 |
| 四轨迹各初始+单编辑session | 16 |
| 四修改后cold | 8 |
| 合计 | 160 |

LP最优结果独立重算原空间可行性、侧乘子符号、站立式、互补和目标/对偶差；
不可行/无界按精确原始Farkas/point-ray核对。MILP按完整整数枚举真值、原始可行性/整数性、界与gap核对。
M01–M04在dense/sparse各有2次实际branch；其余MILP按冻结状态通过。
四编辑均使用warm入口。稀疏RHS/界/增行各cross_solve_reuses=1；增列因basis_or_coordinate_identity重建，
保留真实诊断，不强加同一基序列或提速条件。冷热结果分别匹配冻结目标。

首次完整quality：6726 passed、13 failed，均为console-script调用silo时PATH缺虚拟环境目录。
日志quality1/console.log保留；只给测试子进程前置选定解释器目录，未改全局PATH或旧测试。
第二次完整quality实际exit0：**6743 passed，30.56秒pytest，完整命令32.536秒**，结构与Ruff通过。
本地完整quality2/2额度已用满，未安装全suite调用profile，pytest与正式160分别记账。

## 6. 新工件与真实远端CI

新候选只构建1次；不是重建或重用旧0.3.0a1工件。工件身份如下：

| 本地工件 | SHA256 |
|---|---|
| `silo_solver-0.3.0a2-py3-none-any.whl` | `28873f4d557ec3b63319b84db9ee51c2aa4482c972b4d8223e3c0f26f4f3e5a9` |
| `silo_solver-0.3.0a2.tar.gz` | `d6d233ea736ff2fb3fe0018a0b271e88bdfb334f30a7b036b4894fdc01d255f8` |

本地Windows3.13.9×dense/sparse×wheel/sdist四个全新环境首轮均通过，每环境24固定公开请求、总96。
普通安装后在源码树外python -I执行，核runtime/metadata、direct_url工件SHA、NumPy2.3.5，
sparse额外SciPy1.16.3、dense无SciPy，以及全部已加载SILO模块与构建source manifest一致。
smoke覆盖LP/MILP、三格式、3次不求解CLI转换、三格式optimize、四编辑初始/warm/cold及有限池CG。
内部嵌套LP不算独立实例。原始环境路径、报告、模块哈希和日志保存installed1/及install1/。
sdist安装的临时wheel是pip正常构建产物，原始direct_url继续绑定同一sdist SHA。

唯一非强制push成功同步产品提交至public仓库exoplanetX/silo的任务分支；不更新main，未创建PR/merge/tag/Release/PyPI。
实际[CI运行40261995554](https://github.com/exoplanetX/silo/actions/runs/40261995554)为push触发、attempt1，
绑定42892035db426c4739b6c1a7ad9648852d2b1dc8，最终conclusion=failure。

| 实际源码质量job | 结果 | 证据 |
|---|---|---|
| Ubuntu3.10，121376156936 | 6740 passed/1 failed/2 skipped | [job](https://github.com/exoplanetX/silo/actions/runs/40261995554/job/121376156936) |
| Ubuntu3.12，121376157102 | 6740 passed/1 failed/2 skipped | [job](https://github.com/exoplanetX/silo/actions/runs/40261995554/job/121376157102) |
| Windows3.12，121376157182 | 6743 passed；质量及两冻结核对成功 | [job](https://github.com/exoplanetX/silo/actions/runs/40261995554/job/121376157182) |
| Windows3.10，121376157204 | 6742 passed/1 failed | [job](https://github.com/exoplanetX/silo/actions/runs/40261995554/job/121376157204) |

配置的逻辑拓扑13job=4源码+8安装+1外部格式。实际API列出4执行job及installed/external-format两个skipped占位；
上游失败使安装matrix尚未展开。远端工件构建未运行、工件报告0，16安装核验与24外部解析均未运行；skipped不算通过。
实际四个执行job墙钟合计355秒（5分55秒），低于首轮210 runner分钟；未消费第二轮。

两个3.10的失败为旧DAG CG回归tests/verification/test_dag_cg_bound_consistency.py:177：
path_1实际0.2500000000000001，精确期望0.25000000000000006。后续恢复/负gap断言因早期失败未全部执行，
不能由尾数很小就把整项记PASS。观察到NumPy2.2.6/SciPy1.15.3；具体数值差异的唯一来源未证明。
Ubuntu3.12为旧scripts/sparse_program/resources.py:39读取/proc状态未找到VmHWM后抛StopIteration，
对应normal子进程测试；日志显示poll仍None，具体进程生命周期状态未保存，时序原因仍属推断。
该环境NumPy2.5.4/SciPy1.18.1；本地与CI依赖/平台不同，不能只凭差异归因。

只读独立复核认定没有checkout/依赖获取/服务取消等纯基础设施故障证据；
采样代码需处理的状态和精确回归断言均属于代码路径。因此不rerun，不再次push，不修本单禁改文件。
完整run/jobs/原始日志/无工件事实保存ci_final.json与ci_job_*_raw.log；最小失败包failure_packet.json。

## 7. 伴学、预算与未达项

L0017交付原理、手算例、代码映射、局限及4练习/独立解答；其文本小例实际执行通过，公开求解0次。
verified_code为产品完整提交，verified_on为2026-10-26；小例SHA和来源收据在prepush_check.json。
L0016仅增补交叉引用，保留其原verified_code/on。CATALOG、GLOSSARY和当前文档/工作台只更新本单状态。

本单独立ledger：截至报告汇编，本地自动核验及只读CI/Git取证已登记300.550秒；最终收尾后约5.5分钟，
精确总数以最终ledger/end_git.json为准，低于3600秒。推理、编辑及等待CI不混入计算实验时间。
开发与收尾检查共19/20批；结构最终164合同/161报告/128模块/627链接通过，工作台26项回归通过。
full quality2/2、正式组1/2、外部1/2、构建1/2、本地四环境1/2。
未用额度不构成停止后续跑许可；旧Goal预算/轮次完全未动。

必需未达：R4源码质量3个job失败，远端16工件及24外部读未运行。整体完成条件未满足。
后续最小建议为另行授权旧CG回归的完整数值语义与Linux RSS读取的兼容修订，再跑同一有限矩阵；
建议GPT-6 Sol/high，保留独立只读复核。当前不签发或执行下一合同、不扩大算法/模型域。
原已验收稀疏程序的固定范围结论保持，不因此撤销旧签收或声称新增工业稳定性。

## 8. Remote Sync Proof与保护文件

- 起点git status仅两项已登记治理差异；整个任务未暂存或回退它们。
- AGENTS.md SHA2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638。
- 根通告SHA0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
- 代码、脚本与测试保持产品提交4289203身份；最终追加仅报告/文档/工作台来源元数据。
- git push result=succeeded，恰好1次，固定HEAD:refs/heads/codex/sparse-lp-reoptimization，未force。
- 实际远端任务分支4289203；main保持f0c5f317b8b7c2550ac574e8f27616df7b247dff。
- 最终文档提交local-only，不为收尾自引用再次push；该报告提交用git log -1 --format=%H -- 本报告路径定位。
- 最终HEAD/最近5提交、缓存origin/main与实际任务分支ahead/behind、全部保护哈希和预算在end_git.json。
- 收尾首次git ls-remote只读核对遇Connection reset（未push）；失败日志local18保留，随后改用已认证的只读GitHub refs API确认。
- remote_sync_status=dirty_worktree，仅保留已接受的两治理差异；任务分支代码同步不冒充main同步。

本轮以有明确未达项的本地交付结束。所有计算/构建/安装/远端续跑权限停止，没有下一任务自动执行。
