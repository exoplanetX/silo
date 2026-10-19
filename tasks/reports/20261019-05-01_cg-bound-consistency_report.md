# 第5步执行报告：CG数值界一致性

## 1. 合同、起点和范围

执行[20261019-05-01合同](../codex/20261019-05-01_cg-bound-consistency.md)，风险L2，
唯一目标为现有DAG凸组合CG的原始贡献差距与局部舍入判定。用户已授权这一原子任务，
开发对话是唯一写入/运行协调者；讨论对话负责验收。Git mode为local-commit，不push。

实际起点8ee397ec154b916dd1b922739a666dd33b453885，main、工作区干净，
cached origin/main...HEAD=0/1，唯一ahead为合同签发，已在本次交付授权内。
前序验收摘要f0c5f31，CG源码857397e，定价12bfa35、RMP48c242d、LP ad62e0f。
本轮没有额外源码漂移或即时远端查询；已读合同及其要求的规则、镜像、依赖和学习材料。
模型建议GPT-6 Sol/high，困难是有符号差距、公共c0与局部例外预算；未声称实际切换模型。

实现/测试提交A为15b403bcd7322a0b25ebb5380539dc5c4002c4ac；学习/报告B同属一个原子任务，
通过下方Git历史定位。
本报告提交在收尾后用下列命令定位，避免未来自身哈希：

~~~text
git log -1 --format=%H -- tasks/reports/20261019-05-01_cg-bound-consistency_report.md
~~~

## 2. 修改前的真实复现

修改生产代码前先新增自然反例测试，只读取原接口状态，实际得到
1 failed in0.24s：期望TOLERANCE_REACHED，旧代码返回NUMERICAL_ISSUE，
message为Numerical lower bound exceeds the upper bound。
没有使用缺新字段的AttributeError/import错误充当red。

四条平行路径原成本(-4,-4,3,3)，R/C基系数1/8、-1/4，conv基系数1，
弧增量为0/1，base_cost=-2、弧成本(-2,-2,5,5)。按C=1/2、R=7/8、conv=1行序，
seed=p11/p00、c0=-3，旧Revised实际权重(.75,.25000000000000006)，
pi=(C:0,R:7,conv:-4.875)。P=-1.7500000000000002，D=L=-1.75，rho=0，
原始差距-2.220446049250313e-16；独立原项g也为此负值，A=14.25、eta约5.684e-14。
本轮修改前又运行完整432族：391正常、41数值诊断，646轮，Revised199/17、Tableau192/24。
这些是当前实际旧代码运行，签发阶段的前瞻分类未计为新实现证据。

## 3. 数值修正与兼容性

[dag_column_generation.py](../../src/silo/decomposition/dag_column_generation.py)保存并复用同轮
浮点乘积p_i=c_i*x_i、d_j=b_j*pi_j，delta=min(0,rho)。
P=fsum(c0,p_i)、D=fsum(c0,d_j)，L直接fsum(c0,d_j,delta)，避免把c0先舍入进D。
旧字段numerical_gap保留fsum(P,-L)的有符号原值g_raw；新增objective_gap为
g=fsum(p_i,-d_j,-delta)，在原始贡献层消去公共c0。
roundoff_allowance为eta=32*ulp(A)，A=fsum(abs(p_i),abs(d_j),abs(delta))，不含c0。
A=0采用实际ulp(0)，未加max(1,A)地板。

两个字段追加在原accepted_path之后、默认None，旧位置参数构造与冻结/复制协议通过。
失败轮原界和新字段全部None，历史有效RMP、列注册表及所属轮号保持。
原始P核验、行可行性、非负权重、乘数符号、候选/改善分类、坐标与有限性条件没有放松。
没有修改RMP结果、权重或乘数，产出仍按既有列域与原始最小化坐标解释。

一致性使用g：非负正常通过；负g仅在eta<=tolerance且-g<=eta时接受，
其他负g数值诊断。eta超过用户容差只禁用负g例外，不能截eta或排除本来合法的非负g。
rho在容差内但g>tolerance继续诊断，正向阈值未加eta；rho严格改善仍为rho<-tolerance。
微小负g停止的message写明局部roundoff接受。全部原始负值保留，不裁剪/取绝对值/改权重。
有限乘积、总和、绝对贡献尺度和差距均检查，溢出失败。

精确算术下L=D+delta、g=P-L及平移下界定理沿用；浮点发布量未承诺逐位满足恒等式。
32是固定工程局部尺度，没有调大刷测试，也没有LP线性代数误差上界证明。
原v0.1.0“任何L>P失败、按发布差停止”由本合同明确修订，旧合同/报告保持原样。

## 4. 新版432族与独立核对

新增[回归模块](../../tests/verification/test_dag_cg_bound_consistency.py)。固定共享图
s->left_i->right_j->t有四条三弧路径，成本矩阵按00/01/10/11为
(4,1,2,6)、(-3,2,1,-4)、(0,0,0,0)、(-4,-4,3,3)、(9/4,-3/2,1/2,13/4)、(1,-5,-2,0)。
alpha、beta各取1/4、1/2、3/4，R=alpha+1/8、C=beta-1/4、conv=1均EQ。
R基1/8在首弧增加i，C基-1/4在末弧增加j，conv基1/弧0。
矩阵k从0起，偶k基成本1/c0=2、奇k基成本-2/c0=-3；首弧成本(i+1)/2、
末弧-(j+1)/4，中弧c_ij-base-(i+1)/2+(j+1)/4。
ID/原节点/图行/主行顺序逐项沿用合同，反序同时反转图、行与seed。

独立Fraction令x11=t、x00=1-alpha-beta+t、x01=beta-t、x10=alpha-t，
t在[max(0,alpha+beta-1),min(alpha,beta)]，从原始四成本求两端点精确最优。
两个端点的正权重路径分别作seed，54模型×2seed×2排列×2后端=432。
独立DFS/Fraction验证原列成本/向量；每轮从实际快照独立重算P/D/L/g_raw/g/A/eta。
对返回pi以Fraction精算全域最小rc与平移真下界，逐轮严格核对该精确下界不超过解析最优；
与已发布浮点估计的差另按既有绝对尺度核对。未用工程eta代替精确下界证明，未引用生产私有助手。

新版实测全部432次TOLERANCE_REACHED、0次诊断，Revised/Tableau各216次，
646轮（1轮266次、2轮118次、3轮48次），每轮原始数据与精确下界检查通过。
113个记录为微小负g，均为末轮，Revised65、Tableau48；范围
[-8.326672684688674e-16,-8.921435019309293e-18]。
所有646轮eta范围[32*ulp(0),1.1368683772161603e-13]。
新版g与旧发布差是不同统计口径，没有强求仍为41个负值，也没有改变数据、seed或系数32。

保留[原完整列LP对照](../../tests/verification/test_dag_column_generation_oracles.py)的
耦合退化主例、另8模型、双后端/排列及替代seed共40组；只调整本步字段/求值核对。
主例仍自动得到2->2->-1.5，limit、失败、列身份与所有权等原保护全部回归。

## 5. 大常数、边界和故障保护

真实conv单行图，seed成本1、另列0，c0取0、正负2^40、正负2^60，双后端共10次：
全部两轮、最终便宜路径权重1，首轮g=1、末轮g=0，首轮eta不随c0变化。
正负2^60首轮g_raw=0但rho=-1、g=1，正常继续；没有用大目标舍入后的相等提前停止。
另列成本1-5e-10的同样10次真实运行，一轮停止，pi/rho/g/eta一致，小正g约5e-10保留；
大常数可使g_raw=0。Fraction确认实际二进制成本仍有严格小改善。

合成RMP快照的黑箱边界覆盖：-g<eta、=eta、>eta；eta等于及略超过用户预算；
eta>tolerance但g=0正常停止。使用weight=1-2^-47、cost=pi=1，得到g=-eta=-2^-47，
相邻可表示weight定位边界，没有只测一个近似相等点。
正g在tolerance的相邻可表示数内/等/外都核对；略大于阈值即使增量小于eta也拒绝。
rho在负阈值等/内/外的原测试保留。

明确合成正冲突p=0、d=-8e-10、rho=-7e-10：g=A=1.5e-9、eta约6.6174e-24；
负冲突p=1-5e-10、d=1、rho=0：g=-5.000000413701855e-10、A=1.9999999995、
eta=7.105427357601002e-15，独立断言-g>eta。
两种冲突在c0=0及正负2^40都拒绝，大c0下独立重算g_raw虽为0也未掩盖/放大预算。
注入只证明防护，不声称自然后端生成所有这些残差。
A=0、正负贡献消去、绝对和溢出、非有限P/D/L、坏字段和程序异常保持可见均通过。
旧位置参数、追加字段None/只读、重复求解历史快照也通过。

## 6. 实际测试、修复与环境

真实red为第2节自然状态失败。局部实现后3个CG文件检查589 passed in1.10s，
其中新unit19项、新verification453项（432族+自然1+常数平移20），新增共472项；
原117项并入589。首次Ruff只有新回归文件1个导入块排序，限定该文件自动修正后四文件Ruff通过。
合同七文件targeted：932 passed in1.51s，其中既有DAG/RMP343项与本轮CG589项。
未放松数学断言、原始核验或用户容差。

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_column_generation.py tests/verification/test_dag_column_generation_oracles.py tests/verification/test_dag_cg_bound_consistency.py tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

完整check_quality.py exit0：2331 passed in8.35s，随后Ruff All checks passed，
没有跳过或警告。--write-index、普通结构与git diff --check通过；
摘要更新前为144份合同、141份报告、97模块、468个本地链接。
实现提交前scope为11个允许路径（摘要尚未更新）；7份Markdown的严格UTF-8、围栏、
公式定界符与339个本地链接通过，十节、六题、旧版本来源及draft/null通过。
实现全量检查后保持不变，后续仅真实基线/文档收尾，不重复全套。
摘要更新后结构复查为144份合同、141份报告、97模块、471个本地链接。
最终scope为12个允许文件；8份交付Markdown的严格UTF-8、围栏、公式及384个本地链接，
十节/六题/旧版来源/真实verified_code均通过，代码与测试和受测提交A一致。
使用现有.venv/Scripts/python.exe，Python3.13.9、pytest8.4.2，silo.__file__指向本检出
src/silo/__init__.py。console PATH前置本地.venv/Scripts。没有新依赖、外部solver、
worktree、性能实验或干净环境重建；沿用继承系统包的环境。

## 7. L0004 v0.2.0与只读服务

[正文](../../learning/lessons/L0004-column-generation/README.md)、
[练习](../../learning/lessons/L0004-column-generation/exercises.md)、
[解答](../../learning/lessons/L0004-column-generation/solutions.md)在原路径深化v0.2.0，
保留十节、E01–E04与初版857397e历史来源，新增E05/E06。CATALOG同步当前核验状态。
两个完整Python程序已直接提取compile/exec：退化主例双后端通过，
自然例保持原权重和负g，20次真实常数平移核对轮数、g及eta不变。

六题核对：E01三组rc原值通过；E02一般平移与缺总质量反例以推导核对，不冒充实验；
E03精确1.5e-9残差、阈值和微小改善通过；E04实际seed受限不可行、完整LP目标1/4，
新字段None；E05独立fsum得到g=-2.22e-16、A=14.25和eta=5.684e-14；
E06独立重算两类注入的g/A/eta，并由完整代码验证20次真实平移。
实现提交前保持draft/null；实际提交A后更新checked、
verified_code=15b403bcd7322a0b25ebb5380539dc5c4002c4ac、verified_on=2026-10-19。

合同记录签发阶段experiment_auditor已做只读证据设计，强化平移、三边界和-g>eta，
本轮均落实。该服务没有执行本轮实验或作严格误差证明，其意见未计为新实测。
本轮未发现需新增独立服务解决的实质疑点，未再调度专业Agent或并行写入。

## 8. Git、范围和停止

允许12文件：控制器、3个指定测试、当前API、L0004三文件、CATALOG、当前摘要、
新报告与派生INDEX。禁止模块、全局容差、exports、其他docs、旧合同/报告/资产/门控、
L0001–L0003、依赖/build/native与Skill/Agent保持原状。代码/测试A仅4个Python文件，
提交后cached origin差异0/2。摘要完成后的scope为全部12个允许文件。
单次命令Git身份参数沿用仓库既有身份，不改全局/仓库配置。

文档收尾首次提交后实际查询的Remote Sync Proof：

- `git status --short`：空，工作区干净。
- `git branch --show-current`：main。
- `git log --oneline -5`：本任务文档收尾、15b403b实现、8ee397e签发、f0c5f31第4步验收、
  85cdda3第4步文档。
- `git rev-list --left-right --count origin/main...HEAD`：`0 3`，已知签发1个加本任务2个提交。
- `git push result`：not_attempted。
- `remote_sync_status`：local_ahead_origin。

该实际查询记录随同一文档收尾提交修订保存，最终哈希通过第1节命令定位，
结束回执再次核对状态、分支和cached origin差异。本轮未访问即时远端，无提交失败。

完成后停在第5步，等待silo-solver-1010审查，不启动第6步、不发送其他对话消息。
下一步仅建议先验收局部数值判据，再单独定义后续任务；推荐GPT-6 Sol/high。
当前32ULP仍是工程约定，未提供一般LP误差上界、区间认证或资源/增量/性能能力。
