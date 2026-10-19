# LP无界终止核验 — 执行报告

## 1. 合同、基线与状态

- 合同：[20261020-01-01_lp-unbounded-check](../codex/20261020-01-01_lp-unbounded-check.md)。
- 唯一L2正确性任务，local-commit，不push；完成后停在第7步待讨论对话审查。
- 实际开始HEAD为26f3c48c6d913c1d42414d940ae0ea1edd7ac9ba，main，工作区干净；
  cached origin/main...HEAD=0/9。八个已知本地提交及本合同签发均在授权继续范围。
- 解释器为项目.venv/Scripts/python.exe，silo.__file__定位到当前src/silo/__init__.py。
  使用同一工作副本核对，无当前实时远端查询，不把缓存引用当成即时远端。
- 实现、针对性/全量与教学检查已完成；实现A为
  c460aa78c2abc489839a0da2411b9bd1bca95983。文档/报告本地提交与最终Git证明见第6节。

## 2. 改动前实际基线与原因

在生产代码改动前，以合同参数顺序实际运行240核心族与32对照共272次。
核心逐项身份固定在新oracle的product顺序，96个旧OPTIMAL的case ID逐一保存；
其余144例旧状态均UNBOUNDED。旧32对照按生成顺序：前12例UNBOUNDED，
接着4例INFEASIBLE；tiny16依次为UUUUUUUUUUOOUUOO（O最优、U无界）。

| 集合 | 解析有限/真无界/不可行 | 旧OPTIMAL | 旧UNBOUNDED | 旧INFEASIBLE | 旧误无界 |
|---|---|---|---|---|---|
| 核心240 | 192/48/0 | 96 | 144 | 0 | 96 |
| 对照32 | 16/12/4 | 4 | 24 | 4 | 12 |
| 总计272 | 208/60/4 | 100 | 168 | 4 | 108 |

按epsilon顺序(-2^-24,-2^-32,0,+2^-32,+2^-24)，旧核心分别为40O/8误U、
8O/40误U、48真U、8O/40误U、40O/8误U。两个后端各占一半；q与行序
会影响阈值，大epsilon也有误报，不能把大epsilon组当成全最优。

实际字面反例追踪：Tableau Phase-I终止基为[0,3]，第二变换行含z系数
5.000000413701855e-10、RHS0；其残留人工变量无超过阈值的非人工换入列，
清理删除第二行，Phase II保留第一行。Revised初始矩阵保留1与-1.0000000005等
原系数，得到相同Phase-I基(0,3)；清理的局部依赖检查按既有容差通过，保留r1。
两个后端随后因无离基行报告无界。

原序实际候选x0=(1e10,0)、d=(1.0000000005,1)，r1方向残差零，
被删r2的方向残差delta=281475/562949953421312>0。手设(1,1)会违反r1，
本次观察区分了手设方向与实际候选。tiny正系数2^-32在规范化时清零，
有限上界丢失，旧路径同样误报无界；负号对照仍有合法射线。
本步未修改这些清理/规范化或普通枢轴规则，只保护公开无界终止。

## 3. 新核验与候选来源

共享内部[unboundedness.py](../../src/silo/lp/unboundedness.py)只读完整原始Model、x0、d。
点满足实际原始界和每一原行；方向非负，LE/GE/EQ分别要求Ad<=0/>=0/=0，且c*d>0。
所有原项和候选项在乘积/求和前转Fraction；float是实际二进制值，int保留原整数。
无残差容差、十进制重解释、分母投影、候选修复、精确枢轴或额外可行性LP。

两个内部run记录仅追加默认entering_column。进入列须有效且非基，基/原坐标一致。
Tableau取当前基的未清零RHS和负进入列，按原变量前缀位置投影；Revised仅在
终止处重解当前B*x=b与B*w=Aenter，取dB=-w，按original role/original_name投影。
原始变量可拥有貌似结构列的名称；检查完整原行，不把删除后的矩阵代替原Model。
非有限/非法候选、终止基求解失败或原始条件不满足，返回NUMERICAL_ISSUE及分类消息。
所有非最优Solution字段保持为空/None，公开详情结构和LP包导出保持原有接口。

Phase-I目标为负人工量和，上界0，内部伪无界均转数值矛盾；Tableau补齐保护，
Revised保留已有语义。Phase-II直接solve、无行、Phase-I后与Revised详情/兼容热启动
都经过相同门控。程序逻辑RuntimeError不吞作普通数值失败。

## 4. 新结果与检查

| 集合 | 新OPTIMAL | 新UNBOUNDED | 新NUMERICAL_ISSUE | 新INFEASIBLE |
|---|---|---|---|---|
| 核心240 | 96 | 48 | 96 | 0 |
| 对照32 | 4 | 12 | 12 | 4 |
| 总计272 | 100 | 60 | 108 | 4 |

核心按epsilon顺序为40O/8N、8O/40N、48真U、8O/40N、40O/8N。
四种(原/反行序,原/反变量序)各60例，每组24O/24N/12U；两个后端在总272中
各为50O/54N/30U/2I。完整保留96个逐项旧核心最优和4个大正系数对照最优，
每个最优通过原始check_lp_optimality(...,1e-9)并核对解析目标。
大epsilon保留80O，小epsilon保留16O；有限例零假无界/假不可行。
108个诊断分别为原r1方向违背52、r2方向违背52、tiny正bound方向违背4。
对照字面8例全部数值诊断；负RHS真无界4例/矛盾不可行4例保持；
tiny负号8例真无界、大正号4例最优、小正号4例数值诊断。

观察包装记录两个后端实际传入的完整原Model/x0/d，168次门控中60次通过、108次拒绝，
每后端30次通过/54次拒绝；全部60个公开UNBOUNDED逐项用独立Fraction原项oracle
核对点、方向和严格改善。未用手设见证代替实际候选，也未用生产checker给真值。

- 新oracle测试273项：272固定端到端与1个清单/旧基线核对；核心旧最优case ID
  固化于测试，case产品顺序给出完整参数身份。
- 新单元测试125项：72直接原项核验、18自然公开后端路径、29内部异常/数值/程序错误
  注入、1个详情及兼容热启动测试（两次实际LP）、2个自然MIN RMP反例、3个上层
  替身传播测试。注入与自然可达例分开陈述；共有398项新增版本化检查。
- 真无界3*x=1的两个后端均NUMERICAL_ISSUE，消息为Point违背原行；近矛盾
  x=1与x=1+2^-40双后端同样拒绝。大整数、实际二进制0.1、原项近消去、
  二进制幂缩放、实际近零下界、未清零微小负分量与非有限候选均有区分性回归。
- 上层自然MIN RMP反例返回空字段NUMERICAL_ISSUE；替身测试核对CG/辅助恢复
  MASTER_FAILURE、原始复核NUMERICAL_ISSUE、MIP首次数值失败无伪incumbent。
  上层生产代码无改动；既有MIP真无界与整数探针、RMP零列无界、CG与648恢复族
  均包含在通过的回归中。
- 新测试初次370项运行中11项fixture赋值失败：Objective/Constraint为冻结记录，
  改用dataclasses.replace构造坏值后370项通过；没有将这些fixture错误算作算法red。
  第一次Ruff的6个导入/行长/类型写法问题在全量前修正。真正旧错证据来自改动前272实跑。
- 合同第10节targeted十一文件命令最终 **1575 passed in 6.12s**，exit0。
  较早尚未增补最后12项时为1563通过；中间一次复跑的session输出未完整留存，
  最终完整重跑取得上述1575与exit0，不把未留存输出当作通过证明。
- `scripts/check_quality.py` exit0：**3444 passed in 19.70s**，Ruff全通过，
  无skip/警告。执行时项目.venv/Scripts加入PATH，Python3.13.9、pytest8.4.2。
  原有可选外部oracle继续按既有方式运行，新guard/测试未增加外部求解器依赖。
- `--write-index`和普通结构检查均通过：146合同、143报告、99生产模块、
  483本地链接（当前摘要收尾前）；`git diff --check`通过。最终文档检查见下文。
- L0006正文8例×双后端共16次、解答标量程序实际通过；六题手算/证明与代码对应
  核对。A前draft/null；A后checked、verified_on=2026-10-20与真实完整A哈希。
  文档后续仅做轻量核对，代码/测试在全量之后未改动。
- 当前摘要与学习基线收尾后，普通结构复查通过：146合同、143报告、99模块、
  484本地链接；11个本任务Markdown的UTF-8、443个本地目标、围栏/公式定界符、
  十节与E01–E06题号通过。正文及解答程序在A上再次运行通过，三份生产文件与
  `git show A:<path>`逐字一致；`git diff --check`通过。

签发前theory_architect、experiment_auditor的只读意见已落实于原始点+方向、非基
进入列、Phase-I矛盾、字面反例和独立证据设计。本次执行未另启动agent；其意见
不计为运行次数、实现通过或独立验收。

## 5. 交付范围与限制

实现只改两后端并新增LP内部核验器；两个新测试文件；当前接口文档入口；
新L0006正文/练习/解答与目录；当前摘要、此报告和派生INDEX，总16个允许路径。
core、标准形、最优性核验、普通枢轴/清理、全局容差、decomposition/MIP生产模块、
旧测试、旧合同/报告、L0001–L0005、native与依赖均保持原样。

真实无界3*x=1、maxz的浮点候选点不精确满足原行，会保守NUMERICAL_ISSUE；
此诊断没有改判有限/不可行。微小方向残差同样不能容差判零后支撑所有t>=0。
仅核验已有候选，不保证识别所有真实无界、所有终态、任意尺度或工业性能。
presolve独立终态、外部/替身后端和MIP整数可行性证明仍保留各自边界。
没有启动第8步、RMP重优化、阶段迁移或任何Skill/Agent写入。

## 6. 提交与Remote Sync Proof

实现提交A：c460aa78c2abc489839a0da2411b9bd1bca95983，含5个代码/测试文件。
文档/报告提交B含其余11个允许路径，通过
`git log -1 --format=%H -- tasks/reports/20261020-01-01_lp-unbounded-check_report.md`定位。
Git身份仅用于单次commit参数，不改配置。B初次提交后实际查询：

```text
git status --short: <empty / clean>
git branch --show-current: main
git log --oneline -5:
  <本报告所属提交，按报告路径历史解析> docs: explain LP unboundedness evidence and conservative limits
  c460aa7 fix(lp): verify original point and ray before unbounded status
  26f3c48 docs(tasks): hand off LP unboundedness validation
  e96e3e2 docs: accept DAG feasibility and assess solver maturity
  70293f9 docs: explain DAG feasibility recovery and numerical limits
git rev-list --left-right --count origin/main...HEAD: 0 11
git push result: not_attempted
remote_sync_status: local_ahead_origin
```

本节记录已实查的B初次提交后证明；补入证明后仅amend同一个未推送B，保持本步
两提交和16路径。报告自身哈希用路径历史定位，避免在提交内声称未来自身哈希。
最终收尾再次读取Git状态并在执行回复给出实际B哈希，不访问或修改实时远端。
第7步完成待审查；不向另一对话发消息、不自动执行第8步或其他开发任务。
