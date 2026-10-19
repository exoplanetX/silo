# RMP显式增列基复用与重优化 — 执行报告

## 1. 合同、基线与授权

- 单个L2原子任务：[20261020-02-01_rmp-reoptimization](../codex/20261020-02-01_rmp-reoptimization.md)。
- 实际开始为f8ce202786b00ca673e124c05cca112fe1411366，main，工作区干净，
  cached origin/main...HEAD=0/13。12个已知本地提交及本合同签发均获继续授权。
  上次即时远端核对f0c5f31，本轮没有实时远端查询；local-commit，不push。
- 项目.venv/Scripts/python.exe；silo.__file__指向当前src/silo/__init__.py。
  源码基线包含已验收LP c460aa7、RMP48c242d、CG15b403b与恢复02aed7d。
- 实现、最终质量与教学核对已完成。实现A为90b377f723f047f723949aaace87f1385f42bb74；
  文档/报告B及最终Git证明见第6节。本步完成后停在第8步等待讨论审查。

## 2. 修改前cold基线与新接口

生产代码改动前，执行144条合同历史：1152次独立双后端MIN RMP cold全部通过
Fraction顶点真值与MIN原始/对偶/rc/差距核对；另576次native Revised详情均OPTIMAL、
保留全部原行、无人工列。机制例A双后端9.5→9；B/C双后端2→2→-1；
两独立EQ双后端9→8→7（22次cold，其中C为原序/q进a的代表例）。
该基线仅证明cold支持域，不作为新warm通过。本轮新增测试另覆盖C的全部四种行序/q变体。

新增[LP快照助手](../../src/silo/lp/simplex/basis_snapshot.py)保存冻结ModelIdentity：
有序变量名/类型/界/成本、全部原行名/方向/RHS/按旧变量展开的原系数、MAX方向/c0；
省略零与显式零等价，其他旧数值不按容差判同。RevisedBasisSnapshot还含完整row_names、
非人工column_keys与基槽basis_keys。原列按original/name、结构列按slack或surplus/source
标识，核对角色/来源/唯一性，不保存旧primal/dual/rc数组。

新增RevisedSimplexSolver.reoptimize(model,snapshot=None)，返回冻结
RevisedReoptimizationResult（details包装既有详情，snapshot及路径/迭代/原因字段）。
新入口捕获独立原始reference与冻结身份，执行对象另复制。映射前精确检查旧数学身份；
fresh标准形仅删人工列，完整行不删，旧基按键映射，新原变量非基0；raw解基并检查
标准形残差/非负、完整原点后直接进入既有Phase II。新对偶不要求预先可行，最终最优
则完整核验。每轮至多一个warm run、一个cold入口，分别记录预算和实际枢轴。

新增RMP.solve_reoptimized及冻结RestrictedMasterReoptimizationResult；默认/仅支持
原生Revised或兼容测试子类，其他参数先TypeError不改对象。RMP消费新公开LP入口，
继续独立完整reference核验，再整体转换MIN目标/乘数/rc。旧solve保持cold并清空缓存。
add成功保留旧快照待验证，失败不变；最终合格基更新缓存，非最优/数学失败/资格不足
清空。旧删行或坏metadata但数学依据有效时，保留合法OPTIMAL，只禁发快照。
历史结果、映射、身份均独立只读；两个RMP owner不共享可变状态。

## 3. 新真实路径、独立真值与生命周期

144条历史/576次新opt-in均OPTIMAL：实际144cold、432成功warm、0回退。
cold Phase I144次/288枢轴，cold Phase II144次/0枢轴；warm Phase I0次、
warm Phase II432次/120枢轴，其中336次warm零枢轴。第4轮未改模型全部实际进入
Phase II并零枢轴。记录来自cold入口与原runner观察，不靠flag或相同答案证明。
传入基的语义键槽序与旧快照一致，新增列实际非基，fresh人工列全部去掉且原行完整。

每轮按原始Fraction解析顶点真值核对目标、原始可行、MIN乘数符号、rc、互补和
原/对偶差距；另外1152次独立owner双后端cold重跑全部通过。比较调用不混入cold回退
预算，也不在warm owner上调用旧solve清空其缓存。无时间提升主张。

A/B/C和独立EQ的新公开路径按合同核对；B观察实际ratio=0的枢轴与结构列移位，
C首轮删行禁发快照、第二轮完整cold恢复全行基、第三轮warm。非法旧身份、语义键/
源/基/矩阵/原点、预算/非最优/伪最优与冷依据失败、引用篡改、缓存清空/重建、
实例/历史所有权均有自然或注入测试。warm真实无界先经第7步guard，然后cold再经
guard，两次实际通过记录独立；失败warm的数值和快照不作最终依据。RuntimeError可见。
自然例、故障注入、修改前cold桥接分别记录，不把签发前两项只读意见计作运行。

## 4. 实际检查与学习交付

- 新增225项：144条历史参数化测试、58项LP单元、23项RMP单元。后两者按测试用例
  区分为36项原生路径/输入/预算/所有权与45项合成metadata/数值/依据/逻辑错误注入；
  B的ratio观察仅记录，不改变算法输出，计自然机制。每个历史含4 opt-in及8独立cold，
  不能把1728次求解/复用调用写成1728个pytest测试。
- 合同第11节targeted十文件命令：**881 passed in 2.17s**，exit0。
- `scripts/check_quality.py` exit0：**3669 passed in 12.30s**，Ruff全通过，无skip/警告。
  旧cold RMP、裸basis接口、清理/无界门控、CG/恢复/定价/MIP与全部既有回归保留。
  环境Python3.13.9、pytest8.4.2，项目.venv/Scripts加入PATH；原可选oracle沿用既有方式，
  本步没有增加外部求解器调用或依赖。
- `--write-index`与普通结构检查通过：147合同、144报告、100生产模块、489本地链接
  （当前摘要收尾前）；`git diff --check`通过。最终文档核对在下文补录。
- 新三个测试文件首次218项全部通过，补充坏cold证据/空基/非有限新成本后225项通过。
  没有把import/fixture错误当作算法red；Ruff只修导入/未使用导入/行长等机械问题，
  未调整数学数据、容差、断言或旧测试来提升warm命中。
- L0007正文完整程序11次公开RMP调用：5cold、6warm，A9.5→9、B/C2→2→-1、
  EQ9→8→7；B首个warm实际1枢轴，C先不发快照、再cold建立资格、最后warm。
  解答Fraction枚举程序和六题推导均核对通过。A前draft/null，A后checked，
  verified_code为上述完整A哈希，verified_on=2026-10-20。
- 签发前theory_architect/experiment_auditor只读意见落实为全行资格、语义映射、原始点、
  实际入口观察、真实退化和独立oracle；本执行没有另启agent，意见不计作实测/独立验收。
  本轮代码/测试在全量通过后未改动；之后纯文档收尾仅做轻量检查。
- A上再次运行正文/解答程序通过；12份本任务Markdown的UTF-8、457个本地目标、
  围栏/公式定界符、十节、六个稳定题号、真实verified_code均通过。首次链接检查发现
  解答中数学方括号紧接圆括号被Markdown解析为链接，改写该句后通过，未改数学结论。
  七个代码/测试路径与`git show A:<path>`逐字一致；相对签发提交的全部变化严格为
  19个允许路径。当前摘要收尾后结构检查为147合同、144报告、100模块、491本地链接。

## 5. 范围、限制与下一步建议

本步只新增LP快照助手、Revised显式入口、RMP显式入口/缓存/新类型导出；三个新测试；
五个限定API文档、L0007三文件/CATALOG、当前摘要、此报告、INDEX，共19个允许路径。
core、标准形、Basis、Tableau、最优/无界核验器、普通单纯形/Phase-I清理、全局容差、
CG/恢复/定价与其他算法、旧测试/旧合同报告/L0001–L0006、依赖/native/门控均不改。

保持完整有序原始行且旧数据不变才可复用；本版不恢复删行/补基或支持任意模型变更。
每轮仍完整重建矩阵并解基系统，1e-9可行/最优检查与第7步精确无界门控各自保持范围。
不接CG、不做LU/稀疏缓存/增量定价，不主张速度提升、任意尺度稳定性或研究创新。
下一步仅建议：本步验收后单独设计CG显式可选消费重优化入口的原子任务，保留cold
参考与独立目标/路径/工作量证据。建议GPT-6 Sol/high处理基生命周期与等价性；
建议不构成执行授权。Phase9仍open/parked，native deferred/unapproved，Phase10未启动。

## 6. 提交与Remote Sync Proof

实现A：90b377f723f047f723949aaace87f1385f42bb74，7个代码/新测试路径。
文档/报告B含其余12个允许路径，通过
`git log -1 --format=%H -- tasks/reports/20261020-02-01_rmp-reoptimization_report.md`定位。
Git仅单次commit身份参数，不改配置；未push。B初次提交后的实际查询为：

```text
git status --short: <empty / clean>
git branch --show-current: main
git log --oneline -5:
  <本报告所属提交，按报告路径历史解析> docs: explain RMP basis reuse and cold fallback lifecycle
  90b377f feat(lp): add conservative append-only RMP reoptimization
  f8ce202 docs(tasks): hand off conservative RMP reoptimization
  a26039f docs: accept LP unboundedness validation and record audit limits
  445da97 docs: explain LP unboundedness evidence and conservative limits
git rev-list --left-right --count origin/main...HEAD: 0 15
git push result: not_attempted
remote_sync_status: local_ahead_origin
```

本节补入已实查的B后证明，然后只amend同一个未推送B，保持本步两提交/19路径。
报告自身哈希按路径历史解析，避免提交内声称未来自身哈希。最终收尾再次读取Git
状态，执行回复给出实际B哈希。第8步完成待审查，不向其他对话发消息，
不自动接CG、下个任务或阶段，不push。
