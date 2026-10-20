# DAG CG显式接入RMP重优化 — 执行报告

## 1. 合同、原目标与执行基线

执行唯一L2合同[20261020-03-01_cg-reoptimization](../codex/20261020-03-01_cg-reoptimization.md)。
原目标是逐步建设承载用户OR研究的求解器及伴学材料，本单仅接通显式重复求解链路；
有限普通DAG案例、数学有效性和研究贡献分别判断，未覆盖的原项目义务继续保留。
已实际读取用户目录CASE-20261020-01与项目根通告，不迁入案例模型、不修改封存稿件。

实际签发/开始HEAD：160550bbafc5a9b4af63fba09d67a4ffe2a7182d，main，cached
origin/main...HEAD=0/17。16个已知提交及签发均获继续授权；上次即时远端f0c5f31，
本轮未查实时远端。解释器项目.venv/Scripts/python.exe，silo.__file__为当前src/silo/__init__.py。
工作区开始即有两项用户治理变动，授权原字节保留，不称干净：

- AGENTS.md已修改，SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638。
- 根研究主题固定_严重反面案例通告_20261020.md未跟踪，
  SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
- 全局案例实际hash为3f0c6eda126eb6a42d4107d277acabaee65ce7606b1a23f9eb8be896c7c44112。

两项治理文件不暂存/提交/覆盖/还原；local-commit，不push。实现A为
f4cc36e00628da266d12ac93b25f652c8ae2f569，质量与教学完成，文档B/最终Git证明见第6节。
第8步LP/RMP90b377f、CG15b403b数值规则、恢复02aed7d与定价12bfa35为基线。

## 2. 修改前实跑与最小接入

生产修改前按原公开cold路径运行主族288图×双后端=576次CG，全部正常停止并通过
原图DFS/Fraction当前列集顶点与完整域端点真值：区间每后端72次CG/120轮，方形
每后端216次CG/323轮；另完整域独立owner双cold为576次LP。60大常数图两后端
120次CG、各100轮通过，另120次完整域LP对照。A/B各双后端共4次CG，目标分别
2→2→1与2→2→-1.5。上述是本轮旧源码基线，不计为新开关/逐轮诊断通过。
签发前临时桥接只作支持域证据，也未混入本轮实现计数。

生产仅[dag_column_generation.py](../../src/silo/decomposition/dag_column_generation.py)：
末尾追加严格bool reoptimize_rmp=False，True仅None/原生Revised及兼容子类；
不支持参数在RMP/LP/定价前拒绝。False沿用每轮公开solve；True每轮一次公开
solve_reoptimized，将最终MIN outcome.result交回原流程，不在CG额外cold。
迭代末尾追加默认None的rmp_reoptimization；全部四处history.append保留同轮outcome，
master_result is outcome.result。每次CG一个新RMP owner，CG不触碰基缓存或LP私有接口。

主目标/候选/路径/数值助手及阈值保持；warm失败/cold成功只定价一次。RMP最终失败
保留上一有效轮，原始主目标先失败也保留较早有效轮；有效RMP已登记后发生
pricing/candidate/gap失败，当前有效RMP可保留，本轮界/g/eta/accepted_path为空。
seed重构先失败保持无已求解轮/无outcome记录。外层预算仍按轮，最后轮不追加未解列。

## 3. 主族、大常数与真实调用证据

新288图/864次三模式CG全部TOLERANCE_REACHED，逐轮独立MIN/价格/注册表/界检查通过；
完整域双cold独立owner576次。以下调用/Phase来自公开RMP、native cold和runner实际观察：

| 族/模式 | CG/轮数 | RMP ordinary/opt-in | cold/warm/回退 | cold I/II次数 | cold I/II枢轴 | warm II次数/枢轴 |
|---|---|---|---|---|---|---|
| 区间 cold-Revised | 72/120 | 120/0 | 120/0/0 | 120/120 | 240/72 | 0/0 |
| 区间 cold-Tableau | 72/120 | 120/0 | 120/0/0 | 120/120 | 240/72 | 0/0 |
| 区间 True-Revised | 72/120 | 0/120 | 72/48/0 | 72/72 | 144/0 | 48/48 |
| 方形 cold-Revised | 216/323 | 323/0 | 323/0/0 | 323/323 | 906/72 | 0/0 |
| 方形 cold-Tableau | 216/323 | 323/0 | 323/0/0 | 323/323 | 906/72 | 0/0 |
| 方形 True-Revised | 216/323 | 0/323 | 251/72/0 | 251/251 | 690/0 | 72/72 |

主族True共443个opt-in外层轮=323cold+120warm，零回退、零warm零枢轴轮；
warm实际只入Phase II，完整原行/无人工列、传入基槽键和新增列非基身份均核对。
资格不足的cold不算回退错误。主族True出现63个自然负g轮，均在原32ULP允许范围。
冷热轨迹即使本族相符，也不外推为必须相同。表中Phase枢轴只记runner内实际pivot，
不冒充线性系统/资格核验次数或性能成本。

大常数60图/180次CG全部通过，另完整域双cold120次。每个cold模式60CG/100轮，
ordinary100、cold100、Phase I/II各100次，枢轴230/10；True60CG/100轮为90cold+10warm，
opt-in100、零回退/零warm零枢轴；cold I/II90/90次、200/0枢轴，warm II10次/10枢轴。
P/D/L/g_raw按原始浮点项fsum重构，g/数学目标在c0-free原贡献层核对，不要求P减c0恢复低位。

每个原始图自写DFS/Fraction累加；每轮仅取其immutable registry，枚举支持与独立
活跃行、Fraction解小系统、过滤全部原始EQ/LE/GE，允许冗余EQ秩不足。完整域另用
区间/方形端点解析互核。未调用生产重构/主目标/基助手或旧verification求真值。
所有模式每轮核对当前最优、原始可行/乘数符号/rc/互补/差距、全路径价格及候选字段、
严格改善、接受列、P/D/L/rho/g_raw/g/eta、轮号与停止。完整域LP参考另列，不清空热owner。

## 4. 机制、异常、质量与学习

A真实cold/warm/warm、首个warm实际ratio=0且至少一次枢轴；B真实cold/cold/warm，
首轮旧删行禁发快照，第二轮全行cold恢复资格。恢复阶段原入口保持，显式经济CG新owner
首轮fresh cold，原成本/c0为9.5→9；即便同一solver也不复用辅助/验证快照。
内部warm失败/一次cold成功后，分别交叉定价失败、候选失败与gap失败；最终cold pi被
实际消费，诊断attempted=True/used_warm=False，CG不再cold。双失败不再定价/重试，
尝试registry保留而顶层有效轮保持前轮。接受warm后的对应失败分支亦覆盖。
严格bool/类型零工作拒绝、五终态、原始主目标先失败、seed溢出、内外预算、异常后新owner、
旧位置字段None与只读历史/字典、RuntimeError可见均有检查，合成与自然机制分开。

- 新增406个pytest项：288主族参数项（864 CG）、60大常数参数项（180 CG）、
  14代表数值检查及44单元。14代表检查为4个真实数据/10个故障注入；44单元为
  24个原生路径/输入/预算/隔离观察、20个合成故障交叉。自然/注入/签发桥接分别计数，
  内部RMP、外层CG、LP对照和pytest项不混同。
- 合同十文件targeted命令：**1287 passed in 5.44s**，exit0。
- `scripts/check_quality.py` exit0：**4075 passed in 14.91s**，Ruff全通过，无skip/警告；
  旧LP/RMP/基快照/无界/定价/恢复/MIP与既有CG回归全部保留。Python3.13.9、pytest8.4.2，
  项目.venv/Scripts加入PATH，未新增外部求解器依赖/调用。
- `--write-index`与普通结构检查通过：148合同、145报告、100模块、495本地链接
  （当前摘要收尾前）；`git diff --check`通过。
- 首次大常数文件为74通过/1失败，失败是合成gap夹具把|1|+|-1|的尺度2按1算ULP，
  因而误把33*ulp(1)视为越界。按实际尺度检查32/33*ulp(2)边界后通过；生产规则、
  族数据与容差未改。Ruff仅修导入/未用导入/行长/lambda写法，未删旧测试或刷warm命中。
- L0008完整程序实际3次经济CG/8轮：A2→2→1、B2→2→-1.5、恢复后9.5→9；
  经济部分4cold/4warm，辅助/验证求解另计。恢复后首轮无warm尝试。解答贡献/尺度
  标量程序与六题推导核对；A前draft/null，A后checked、verified_on=2026-10-20、真实完整A哈希。
- 与签发源码逐函数比较确认原CG所有数值/路径/候选助手文本不变；本轮无新agent，
  签发前theory_architect/experiment_auditor意见不计为运行或独立验收。
  全量后代码/测试未改，文档收尾只做轻量核对。
- A上再次运行正文与解答程序通过；独立恢复实际辅助2次/验证1次，和经济3次CG/8轮
  分开记录。11份本任务Markdown的UTF-8、457个本地目标、围栏/公式定界符、十节与
  E01–E06题号、真实verified_code核对通过；四个代码/测试路径与git show A逐字一致。
  任务变化严格15路径，另两治理变动哈希不变、未提交；当前摘要收尾后的结构复查
  为148合同、145报告、100模块、497本地链接，差异检查通过。

## 5. 范围、原目标未覆盖部分与下一步仅建议

本步15允许路径：一个生产CG、三个新测试、四个限定API文档、L0008三文件/CATALOG、
当前摘要、此报告、INDEX。LP/RMP/基快照/定价/恢复器、其他算法、旧测试/合同/报告/学习篇、
研究资产/规则/Skill/Agent/依赖/native均不改；两治理文件原字节保留在提交之外。

本步只接通有限普通DAG凸组合参考循环的可选复用。仍完整矩阵重建和解基、完整DAG定价；
没有增量定价、LU/矩阵缓存、一般CG插件、资源/整数扩展或性能优化。既有浮点1e-9与
32ULP只是工程支持边界，任意尺度/高维/工业性能、加速、研究特色与原项目完成均未由本步证明。
后续仅建议根据具体OR问题确定需求，再单独签发相应验证/算法任务；建议GPT-6 Sol/high
处理跨层证据与等价性，常规文档medium。不得以有限图结果接管原求解器建设目标。
Phase9仍open/parked、native deferred/unapproved，Phase10未启动。完成后停待讨论审查。

## 6. 提交与Remote Sync Proof

实现A：f4cc36e00628da266d12ac93b25f652c8ae2f569，4个代码/新测试路径。
文档B含其余11个允许路径；L0008按实际核验填写checked。
文档/报告B通过git log -1 --format=%H -- 本报告路径定位。Git仅单次身份参数，不改配置。
B初次提交后实际查询为：

```text
git -c core.quotepath=false status --short:
 M AGENTS.md
?? 研究主题固定_严重反面案例通告_20261020.md
git branch --show-current: main
git log --oneline -5:
  <本报告所属提交，按路径历史解析> docs: explain CG reoptimization evidence and failure histories
  f4cc36e feat(decomposition): opt DAG column generation into RMP reuse
  160550b docs(tasks): hand off CG reoptimization integration
  09fb205 docs: accept RMP reoptimization and record independent audit
  be0dd57 docs: explain RMP basis reuse and cold fallback lifecycle
git rev-list --left-right --count origin/main...HEAD: 0 19
git push result: not_attempted
remote_sync_status: dirty_worktree
```

仅余两项既有用户治理变动，已按第1节哈希复核不变。补入本节后只amend同一个未推送B，
本步仍两提交/15允许路径；治理文件从未进入暂存或本步提交。报告自身哈希用路径历史
定位，避免未来自指；最终再次实查status/cached/治理哈希并在执行回复给出实际B哈希。
本单完成后停止待审查，不push、不向其他对话发消息、不自动执行后续任务。
