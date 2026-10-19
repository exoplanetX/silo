# 第4步执行报告：DAG凸组合列生成闭环

## 1. 合同、授权与实际起点

本轮执行[20261019-04-01合同](../codex/20261019-04-01_dag-column-generation.md)，
风险L3，唯一目标为固定普通DAG路径域、连续凸组合主问题的参考CG循环。
用户“交付执行吧”的授权覆盖实现、测试、L0004、报告与local-commit。
实现协调归silo-solver开发，silo-solver-1010负责签发和验收。本轮完成后停在第4步。

实际起点83aeb9ce4a2c58829443d449ebfb458988dce6b7，main、工作区干净，
cached origin/main...HEAD=0/1，唯一ahead为本合同签发，明确在继续执行授权内。
前序验收记录为c6d0ed1；本轮没有重新查询即时远端。
依赖源码为RMP 48c242d、DAG定价12bfa35、LP ad62e0f，没有并发无关漂移。
已按合同读任务规则、状态/技术/同步镜像、学习规范、依赖源码及第2/3步材料。

配置建议GPT-6 Sol/high沿用合同，难点为退化、对偶平移及失败证据所属列集。
本报告不声称切换模型。主线程负责全部实现与运行，独立服务只读。
代码/测试A为857397e0cebdcfeb1c6c5ff325c17e0aa09c151b；学习/报告B通过下方命令定位，
两个提交属于同一个原子任务。
本报告提交通过以下命令在提交后定位，避免未来自身哈希：

~~~text
git log -1 --format=%H -- tasks/reports/20261019-04-01_dag-column-generation_report.md
~~~

## 2. 新接口、主问题与所有权

新增[dag_column_generation.py](../../src/silo/decomposition/dag_column_generation.py)，
导出DagMasterRow、DagColumnGenerationProblem、DagColumnGenerationIteration、
DagColumnGenerationResult、DagColumnGenerationStatus和solve_dag_column_generation。
仅消费公开core模型、RMP/定价、LP接口及既有数值常量，没有访问RMP._model。
生产不枚举完整路径，不增加任意pricer插件或改通用ColumnGenerationSolver。

完整U为同一图中全部s-t路径。权重非负连续，固定行包含指定conv等式，RHS精确1，
图中conv基系数精确1、每弧系数精确0；其他行为有限LE/GE/EQ，行名恰与图一致。
目标c0加路径成本，原始最小化pi沿用RMP；c0不进入rc。
seed是非空、无重复、逐弧连贯到t的完整弧ID元组，列数据由同一公开图重构。
初始可行性由第一次真实求解检查，未实现人工列、Big-M或可行性定价。

路径元组是权威身份，平行弧/同成本同向量的不同路径保持独立；内部变量名path_0等
仅作无碰撞编号，注册表保存映射。行/图/seed重排允许改变退化轨迹，目标/可行性核对一致。
输入、列注册表、结果与迭代记录均冻结/复制为独立快照，历史不随新迭代或外部列表变化。

顶层column_paths与last_valid_master属于同一成功轮，分别带column_set_iteration和
last_valid_master_iteration。失败尝试的列集在其独立迭代记录中，失败轮界全部None。
首次RMP失败只有尝试注册表，没有有效RMP；seed重构先溢出时没有已求解轮或注册表。
这些规则防止用历史乘数或旧界冒充失败轮的新证据。

## 3. 循环、界与停止

每轮先全行冷RMP，用本轮经核验最小化pi做完整图定价，独立从原图重构候选路径、
原成本、完整向量与rc；按既有1e-9核对返回字段及改善分类。加入RMP的成本/系数和rho
都使用重构原值，不能把容差内漂移字段写回主问题。
未出现的显著负rc路径每轮最多接受一条，下一轮重新求解。目标不变仍继续。

从当前列和快照重算P=c0+c^T*lambda，并核对后端目标/有限性/原始行；
D=c0+b^T*pi从完整RHS与本轮乘数重算，行符号按既有绝对容差检查。
rho由完整定价和原始列重构得到。设delta=min(0,rho)，精确算术下只平移自由等式
pi_conv'=pi_conv+delta，每条路径系数1使新rc=rc-delta>=0；RHS1使目标变为
L=D+delta。原始可行解在完整域补零给出上界P，故L<=z*<=P。
证明依赖完整U、合法conv结构、当前原始可行和pi符号正确，不能推广到任意主问题。

实际字段标为numerical_upper_bound=P、dual_objective=D、rho、
numerical_lower_bound=L、numerical_gap=P-L=(P-D)-min(0,rho)。
这是浮点核验支持的估计，不含区间或严格舍入证明；没有将D替换为P。
只有rho>=-tolerance且0<=gap<=tolerance时TOLERANCE_REACHED。
小负rho和小正gap保留，rho容差内但gap过大或L>P都NUMERICAL_ISSUE，不裁剪。

预算计数为真实RMP/定价轮数。最后轮仍需新列则ITERATION_LIMIT，不追加未经求解的列；
最后轮满足容差则正常停止。已有路径仍显著负rc为NUMERICAL_ISSUE，不黑名单换列。
RMP非OPTIMAL为MASTER_FAILURE；定价失败/异常NO_PATH为PRICING_FAILURE；
坏字段、分类冲突、非有限累计等为NUMERICAL_ISSUE，不捕获编程异常冒充正常结果。
初始受限不可行及后端UNBOUNDED保留诊断范围，不发布完整主问题状态或全局Solution。

## 4. 主例实际轨迹与独立完整列对照

主例四条平行路径成本(4,6,1,2)，(R,C)为(1,1)、(0,0)、(1,0)、(0,1)，
R=C=1/2、conv=1、c0=-3，seed为前两列。
解析令d1=t，则d2=t、o12=o21=1/2-t，P=-1.5+7t、0<=t<=1/2，唯一最优t=0。
两个后端原顺序实际自动轨迹相同：

| 轮 | pi=(conv,R,C) | P | D | rho | L | gap | 接受路径 |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | (6,-2,0) | 2 | 2 | -4 | -2 | 4 | o21 |
| 2 | (6,2,-4) | 2 | 2 | -7 | -5 | 7 | o12 |
| 3 | (-1,2,3) | -1.5 | -1.5 | 0 | -1.5 | 0 | 无 |

o12=o21=1/2，d1=d2=0。目标不动的一轮确实跨过；当前L可下降。
limit=1、2返回已求解列数2、3和ITERATION_LIMIT，limit=3返回4列及TOLERANCE_REACHED。
反序图/行/seed也核对最终解析权重，但不把特定退化乘数或增列次序固定为通用规则。

[verification](../../tests/verification/test_dag_column_generation_oracles.py)用独立DFS穷尽小图
全部路径，Fraction直接汇总原始数据，独立建立完整MIN列模型经既有RMP适配求解。
不调用控制器/定价器私有重构、身份或建模助手。完整LP与CG共享原生LP依赖，
因此同时用解析目标核对，未把双后端一致性重复计为独立证明。

另8个不同模型均为3或4条真实两弧路径，各自有中间顶点；完整数据和预期值如下。
q/r均为最终路径系数，成本已含基项，列表顺序对应测试分支编号：

| 模型 | 成本 | 耦合行 | c0 | 基成本/非conv基系数 | 解析最优 |
|---|---|---|---:|---|---:|
| conv | (3,1,0) | 无 | 0 | 0/无 | 0 |
| ge | (0,4,1) | r=(0,1,2)>=1/2 | 0 | 0/无 | 1/4 |
| le | (3,0,1) | r=(0,2,1)<=1/2 | 0 | 0/无 | 2 |
| eq | (3,-1,-7) | r=(0,1,2)=1/2 | 2 | 1/r=1/4 | 5/2 |
| negative_rhs | (2,2,0) | r=(-2,0,-1)=-1 | -2 | 0/无 | -2 |
| mixed | (2,1,0) | r=(0,1,2)>=1/2，q=(2,1,0)<=3/2 | 3 | -1/q=1/4 | 3 |
| equal_identity | (0,0,-1) | 无 | 0 | -2/无 | -1 |
| asymmetric | (0,2,-2,0) | r=(1,0,1,0)=1/4，q=(1,0,0,1)=3/4 | -1 | 1/r=1/8 | -3/2 |

解析依据：conv和equal_identity取最低成本；ge的单位r最低成本为1/2，
以分支0/2权重3/4、1/4达到1/4；le每单位r最大降成本2，以分支0/2各1/2达到2。
eq消去x1=.5-2x2得不含c0目标1-2x2，在x2=.25取.5，加c0得2.5。
negative_rhs取第三条路径成本0，加c0得-2；mixed第三条成本0同时满足两行，加c0得3。
asymmetric令第一条权重t得第二条t、第三条.25-t、第四条.75-t，目标-1.5+4t，
0<=t<=.25，最优-1.5。这些独立解析量与完整列LP目标共同核对。

九模型×两后端×原序/反序=36组，另ge换可行seed(0,2)的四组，共40组CG/完整列LP比较，
逐轮复算原始行可行性、pi符号、P/D/rho/L/gap及与解析最优的界关系。
另一个完整列LP确认ge只seed分支0时受限不可行、完整模型最优仍为1/4。
没有把8个输入排列算作8个不同模型，也没有据有限族声称所有CG实例一般正确。

## 5. 数值、身份与失败证据

自然小模型：平行路径成本1与1-5e-10，seed为1，默认容差一轮停止，P=1、rho约-5e-10，
保留小正gap。Fraction由原始浮点值直接确认完整最优严格小于1，未用近似LP目标认证零差距。
默认负阈值恰等/内/外、初始受限不可行、不同后端及合法分隔字符身份均真实运行。
两个序列('a|b','c')与('a','b|c')保持不同身份；成本/向量相同不合并。

[unit测试](../../tests/unit/test_dag_column_generation.py)的明确合成故障包括：
RMP五类非OPTIMAL、后续轮失败、坏OPTIMAL被真实RMP核验拒绝、定价NUMERICAL_ISSUE/NO_PATH、
坏路径/行坐标/成本/rc/改善字段、已有显著负rc路径、非有限结果、有限P/D/L运算溢出。
P-D=8e-10且rho=-7e-10得到gap=1.5e-9，按NUMERICAL_ISSUE停止；
另用容差内原始可行残差制造L>P，验证未裁剪。注入记录只证明保护生效，不声称自然可达。
容差内成本及conv系数字段漂移后，实际入RMP仍为重构原值，最终目标/权重按原列核对。
有限seed成本和先溢出时诊断，没有已求解注册表。RuntimeError程序错误保持可见。

## 6. 实际检查、修复与环境

按区分性行为先写测试，再实现控制器；未以新模块import错误伪造算法red。
首次新增检查105 passed in0.35s。补充12项数值/输入/边界检查后，新增共117项，
其中unit74、verification43。合同六文件targeted为460 passed in0.64s，
既有343项与本轮117项分别计数。
首次Ruff发现8项：2个导入块、4个长行及2处zip未显式strict。
导入限定在两个新文件自动整理，长行手动修正、zip设strict=True；随后四文件Ruff通过，
targeted再次460 passed in0.64s。数学断言、容差及失败保护没有放松。

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_column_generation.py tests/verification/test_dag_column_generation_oracles.py tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

完整check_quality.py exit0：1859 passed in10.96s，随后Ruff All checks passed，
没有跳过或警告。--write-index、普通结构检查和git diff --check通过；
当前摘要更新前结构为143份合同、140份报告、97模块、462个本地链接。
实现提交前scope为13个允许文件，9份交付Markdown的严格UTF-8、围栏、公式定界符、
371个本地链接通过；L0004十节、四题及draft/null通过。代码全量后保持不变，
最终摘要/真实基线字段和Git证明收尾只做文档检查，不重复全套。
摘要更新后的结构为143份合同、140份报告、97模块、466个本地链接，仍通过。
最终scope为全部14个允许文件，10份Markdown的严格UTF-8、围栏、公式及413个本地链接
通过，十节/四题/真实verified_code通过，代码与测试与全量受测提交A完全一致。
使用现有.venv/Scripts/python.exe，Python3.13.9、pytest8.4.2，silo.__file__为
E:/OneDrive/workspace/codex/silo-solver/src/silo/__init__.py。
沿用继承系统包的环境，没有安装/升级依赖、新建worktree或验证干净环境重建。
没有外部求解器、性能对标或研究规模实验。

## 7. L0004实际教学核验

新建[L0004正文](../../learning/lessons/L0004-column-generation/README.md)、
[练习](../../learning/lessons/L0004-column-generation/exercises.md)、
[解答](../../learning/lessons/L0004-column-generation/solutions.md)，v0.1.0，十节与四个稳定题号。
正文完整Python块直接提取、compile/exec，在Revised/Tableau均实际复现P=2->2->-1.5、
最后o12/o21各1/2，注册表和有效RMP轮号均3，最后gap0。

E01用原始四列独立算三组rc=(0,0,-3,-4)、(0,0,-7,0)、(0,7,0,0)，
核对P/D/rho/L/gap；Fraction端点核对解析式最优-3/2。
E02按第3节独立检查平移/弱对偶的一般推导和无总权重反例，不把有限代码运行称为证明。
E03用Fraction确认实际二进制成本仍有正改善，精确复算残差gap=1.5e-9与边界1e-9。
E04实际运行seed不可行而完整主问题目标1/4，历史轮/注册表/失败None由单元测试核对；
资源扩展部分按对象缺口解释，没有执行资源定价。
实现提交产生前保持draft/null；实际提交A后绑定checked、
verified_code=857397e0cebdcfeb1c6c5ff325c17e0aa09c151b、verified_on=2026-10-19。

## 8. 只读复核状态

签发阶段独立数学服务因容量失败，没有审查结论，未计作通过。
本轮代码形成后，按合同仅尝试一次red_team_reviewer，对界、退化、limit、原始字段及
失败轮证据归属进行只读锁定复核。服务返回“Selected model is at capacity”，未提供评审。
没有独立GO或decision_impact结论可引用，也没有服务写入或代跑实验。
主线程继续承担推导、实现、解析/枚举及实际检查；缺少独立复核结论作为本轮交付限制记录。
未改固定专业Agent配置、未换模型重试，也未因此扩展范围。

## 9. 允许范围、Git与停止位置

范围锁为新控制器/导出、新unit/verification、三个API/导航文件、L0004三文件、
学习目录、当前摘要、新报告和派生INDEX，共14个允许文件。
RMP、DAG定价、LP/core/modeling/presolve/MIP/cuts/CLI/io/外部接口、通用CG/日志/toy、
L0001–L0003、旧合同/报告、研究笔记/探针/资产、ROADMAP/阶段/其他门控、
依赖/build/native及Skill/Agent定义均保持原状。实现提交A只含4个Python文件，
cached origin差异0/2；当前摘要更新后的scope为14个允许文件。
Git mode=local-commit，不push；单次命令身份参数沿用仓库既有身份，不改全局配置。

文档收尾首次提交后实际查询的Remote Sync Proof：

- `git status --short`：空，工作区干净。
- `git branch --show-current`：main。
- `git log --oneline -5`：本任务文档收尾、857397e实现、83aeb9c签发、c6d0ed1第3步验收、
  8efabee第3步文档。
- `git rev-list --left-right --count origin/main...HEAD`：`0 3`，已知签发1个加本任务2个提交。
- `git push result`：not_attempted。
- `remote_sync_status`：local_ahead_origin。

该实际查询记录随同一文档收尾提交修订保存，最终哈希通过第1节命令定位，
结束回执再次核对状态、分支和cached origin差异。本轮未访问即时远端，无提交失败。

本轮完成后停止第4步，等待silo-solver-1010审查，未启动第5步或发送其他对话消息。
下一步仅建议先验收本闭环，再单独定义后续任务的模型与证据；推荐GPT-6 Sol/high。
现有结果限固定普通DAG连续凸组合主问题、可行seed及浮点数值条件，保留LP已知数值债；
资源、整数、一般可行性阶段、增量维护和性能优势均需后续独立授权与证据。
