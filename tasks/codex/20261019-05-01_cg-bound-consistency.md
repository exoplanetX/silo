# 第 5 步交付：CG 数值界一致性与舍入判定

## 1. 元信息、批准范围和基线

- ID：20261019-05-01_cg-bound-consistency。已扫描同日合同/报告，TT=01–04已用，
  本任务为新TT=05、RR=01，保留旧合同及历史报告。
- 类型/风险：L2，现有CG控制器的数值正确性与结果解释修正。
- 用户在第4步验收、推送和本项建议后明确批准“可以，把任务写详细后就可以交付执行了”。
  授权覆盖本合同的一个原子任务：实现、回归、学习修订、报告及本地提交。
- 来源：tasks/phases/phase_07_decomposition.md 后续扩展、第4步闭环及其验收发现。
  Phase 9 open/parked、native deferred and unapproved、Phase 10 not started均保持。
- 签发/验收：silo-solver-1010，thread 01a1254a-b349-77d0-8c66-d4b711cd511f。
- 唯一实施/文件写入协调：silo-solver开发，
  thread 01a15208-bea9-7030-aacc-95d785e8fa58。
- 工作目录：E:/OneDrive/workspace/codex/silo-solver。
- 签发前实际HEAD：f0c5f317b8b7c2550ac574e8f27616df7b247dff，main，工作区干净，
  cached origin/main...HEAD=0/0；上一轮push成功并核对即时远端同一完整哈希。
- CG源码基线：857397e0cebdcfeb1c6c5ff325c17e0aa09c151b；
  第4步文档85cdda3、验收f0c5f31。定价12bfa35、RMP48c242d、LP ad62e0f保持。
- 本次签发只增加合同、更新摘要与INDEX；从其提交执行。唯一新增签发提交形成的
  已知local-ahead属于当前批准的交付流程，明确允许直接继续，无需再次询问。
  其他源码漂移、分歧或无关脏文件须保留现场并报告，不覆盖/重置。
- 签发提交用 git log -1 --format=%H -- 本合同路径定位。
- Git mode：local-commit，结束后本地提交并停止；上一轮push授权已完成，
  本合同不授权推送本轮未来实现。
- Expected report：tasks/reports/20261019-05-01_cg-bound-consistency_report.md。
- Learning delivery：更新learning/lessons/L0004-column-generation/的三文件及CATALOG，
  目标讲解版本v0.2.0，保留稳定ID与原路径，本步深化同一主题。
- 模型建议：GPT-6 Sol / high。具体困难为有符号差距、公共常数消去、局部舍入例外
  与真实停止容差之间的一致性；建议不代表切换模型。

## 2. 现状、反例与唯一目标

第4步已按其保守范围验收并推送：自动CG跨过P不变的退化轮，目标2 -> 2 -> -1.5；
1859项测试、Ruff、结构及L0004通过。旧规则对任何L>P直接NUMERICAL_ISSUE。

审查中的54个解析模型各配两个seed端点、两种排列、两个后端，共432次运行；
391次收敛，41次因L-P仅2.22e-16至8.88e-16而诊断，其中Tableau24、Revised17。
这些失败末轮原始目标距精确最优同样不超过8.88e-16，构成自然运行的舍入反例。
签发前在未改源码的f0c5f31上再次复现同一391/41计数；新判据仅在这些既有末轮
快照上作前瞻分类，432次均满足拟定判据，最大eta约5.68e-14。
这属于签发设计依据，不是新控制器已经实现或测试通过的证据。

本步唯一目标：在原有固定普通DAG、连续conv=1主问题内，修正数值界一致性判定，
原样保留已发布标量的差距，同时从原始贡献项消去公共c0计算稳定有符号差距；
用固定局部ULP尺度容纳微小负差距，继续拒绝实质矛盾和无效证据。

本合同明确替代第4步中“任何L>P都失败”和“仅用已舍入P-L作停止差距”的当前行为。
数学上的凸组合平移定理、原始最小化pi、完整路径域与用户容差不变。
不可修改旧合同来消除版本差异，L0004须说明新旧约定。

开始前读AGENTS.md、tasks/README.md、project_profile.md、technical_route.md、
remote_sync_proof.md、learning/README.md、WRITING_GUIDE.md、第4步合同/报告；
再读dag_column_generation.py、RMP、DAG定价、对应unit/verification、API和L0004。

## 3. 明确区分原始量与消去公共常数的差距

本轮当前列集S及完整固定行集J，定义有限浮点乘积
\[
p_i=c_i x_i,\quad d_j=b_j\pi_j,\quad
\delta=\min(0,\rho),\quad \rho=\min_{p\in U}(c_p-a_p^\top\pi).
\]
p_i使用图重构的当前列成本及经核验RMP原始权重；d_j包含conv行。
rho仍来自现有完整定价并由控制器从原图重构，不另换符号或加入c0。

使用同一批乘积与math.fsum计算：
\[
P=\mathrm{fsum}(c_0,\{p_i\}),\quad
D=\mathrm{fsum}(c_0,\{d_j\}),\quad
L=\mathrm{fsum}(c_0,\{d_j\},\delta),
\]
\[
g_{\rm raw}=\mathrm{fsum}(P,-L),\qquad
g=\mathrm{fsum}(\{p_i\},\{-d_j\},-\delta).
\]
列表记号表示把各项放入一个求和序列；避免先算两笔大总数再相减。
L直接对原始项求和，避免先把c0舍入进D再加delta。精确算术中仍有L=D+delta、
g=P-L=(P-D)-delta；浮点发布量可能不逐位满足这些等式，必须诚实解释。

- 现有numerical_upper_bound、dual_objective、rho、numerical_lower_bound保留P/D/rho/L。
- 现有numerical_gap保留g_raw，允许带符号；不得裁零、取绝对值或改写成g。
- 新增objective_gap字段记录g，停止及界一致性依据此值。
  g与g_raw都保留，后者是发布量的直接差，前者从原始项消去公共常数。
- 新增roundoff_allowance记录下一节eta。
  两个字段追加在DagColumnGenerationIteration现有字段之后，默认None；
  保持原字段顺序与既有位置参数可用。状态枚举/入口参数不扩展。
- 私有计算可作窄重构，保存并复用真实乘积；不要为了复核把所有乘积重新乘一遍，
  不读取RMP私有模型，不引入通用数值策略类或用户可调新阈值。
- 继续核对P与RMP发布目标、原始行可行性、权重非负、乘数符号、候选字段、
  数值有限性和本轮坐标；不放松既有DEFAULT_TOLERANCE核验。

精确条件下L<=z*<=P的定理沿用L0004；本步新判据仅改善浮点一致性和停止解释，
不能把小负g包装成严格对偶界证明或声称已修复LP后端所有误差。

## 4. 固定局部舍入例外与停止规则

令
\[
A=\mathrm{fsum}(\{|p_i|\},\{|d_j|\},|\delta|),\qquad
\eta=32\,\mathrm{ulp}(A).
\]
使用math.ulp；A=0使用其实际ulp(0)，不人为加max(1,A)地板。
系数32是本步固定工程约定，用局部数值尺度上的若干末位单位容纳舍入影响。
它不包含c0，不是LP线性代数误差的严格上界，不是新精度证明。
不得依据通过率调大系数，或把32作为一般误差界/论文理论结论。

按下面顺序接入既有循环：

1. 继续先完成RMP与完整定价及候选重构核验。
2. 计算P/D/L、g_raw、g、A、eta，所有乘积/总和/尺度/差距都须有限。
   有限输入的产品、绝对尺度和或合并算术溢出时NUMERICAL_ISSUE。
3. g>=0无需负差距例外。g<0仅在eta<=tolerance且-g<=eta时通过一致性判定；
   其他负g为NUMERICAL_ISSUE。
   eta>tolerance时禁用负差距例外，不把eta截成tolerance，也不自动拒绝原本非负的g。
4. rho>=-tolerance但g>tolerance时仍NUMERICAL_ISSUE；
   正向停止阈值不加eta。rho的严格改善分类仍为rho<-tolerance，不能放宽为另一阈值。
5. 仍显著负rc的已有路径、坏字段、后端失败、异常NO_PATH等保留既有失败规则。
6. 只有rho>=-tolerance、g<=tolerance且第3项一致性通过时TOLERANCE_REACHED。
   若以微小负g通过，message明确说明按局部舍入判据接受；所有原始负值照常发布。
7. rho<-tolerance且候选是新列时仍每轮最多加一列；退化、limit和快照所属轮次保持。
   不以g_raw=0或目标不变提前停止。

这条新增例外同时受eta与用户tolerance限制，不能把允许的正gap提高到tolerance+eta。
当eta>tolerance时，正常非负差距保留原有数值含义；本步只禁用新增负差距例外，
不声称对大尺度数据给出严格精度保证。

只有全部同轮检查成功才发布本轮界/g_raw/g/eta；失败轮新字段和原界字段均None。
保留最后有效RMP与列集轮号，不把失败前历史证据标成本轮结果。
如需message诊断可写入已计算的原因/数值，不把失败字段填成“可用界”。

## 5. 最小自然反例与大常数风险

### 5.1 自然舍入反例

s到t的四条平行路径p00/p01/p10/p11，数据为：

| 路径 | 原始成本 | R系数 | C系数 |
|---|---:|---:|---:|
| p00 | -4 | 1/8 | -1/4 |
| p01 | -4 | 1/8 | 3/4 |
| p10 | 3 | 9/8 | -1/4 |
| p11 | 3 | 9/8 | 3/4 |

图base_cost=-2、base_coefficients={conv:1,R:1/8,C:-1/4}；
弧成本=(-2,-2,5,5)，各弧R/C增量为对应0/1指标。
图row_names=(R,conv,C)。主问题行按C=1/2、R=7/8、conv=1排列，均EQ；
seed依次p11、p00，c0=-3。Revised在现有版本返回权重
0.75和0.25000000000000006，pi=(C:0,R:7,conv:-4.875)，rho=0，
P=-1.7500000000000002、D=L=-1.75，精确最优-7/4。

旧版因此NUMERICAL_ISSUE；新版应按局部判据TOLERANCE_REACHED，保留负差距、
返回的真实权重和eta，不能把lambda改成手算值来“修好”证据。

### 5.2 公共目标常数消去

真实小图：conv=1，seed路径成本1，另一路成本0。
c0分别取0、正负2^40、正负2^60，两个后端均应保留两轮流程和正确最终路径。
签发前现有API已核对这些10次真实运行；c0=正负2^60时第一轮g_raw已经为0，
rho仍为-1，说明原始量相减会丢失差距。新版应记录第一轮objective_gap=1，
继续加列，第二轮objective_gap=0；eta不因c0平移而改变。

用明确合成的RMP快照另外检验：
- seed成本0、原始权重1、pi_conv=-8e-10，另列成本-1.5e-9，则rho=-7e-10，
  P0-D0=8e-10，g=1.5e-9>默认tolerance。c0取正负2^40时g_raw可为0，
  新版仍须NUMERICAL_ISSUE，不能被“无改善+发布差距0”误导。
- 两列成本均1，seed权重1-5e-10、pi_conv=1，得到g约-5e-10，远大于局部eta；
  大c0也不能扩大负gap例外，仍须诊断。
  此类负冲突测试须独立计算并断言-g>eta，记录A、eta、g，避免大尺度掩盖注入。

注入只证明防护，不声称正常后端自然生成所有合成乘数/残差。

## 6. 独立解析回归族：54模型、432运行

新增 tests/verification/test_dag_cg_bound_consistency.py，独立构造以下有限族。
只用生产公开接口，不能引用控制器的私有目标、尺度、路径或求和助手当oracle。

图为s -> left_i -> right_j -> t，i,j属于{0,1}，共有四条三弧路径。
六个路径成本矩阵按00/01/10/11顺序为：
(4,1,2,6)、(-3,2,1,-4)、(0,0,0,0)、(-4,-4,3,3)、
(9/4,-3/2,1/2,13/4)、(1,-5,-2,0)。
alpha、beta各取1/4、1/2、3/4，固定conv=1、R=alpha+1/8、C=beta-1/4。
R基系数1/8，在s->left_i弧加i；C基系数-1/4，在right_j->t弧加j；
conv基系数1，全部弧conv增量0。所有行为EQ。

为精确复现历史族，矩阵索引k从0起，base_cost偶k为1、奇k为-2，
c0偶k为2、奇k为-3；首弧成本(i+1)/2，末弧成本-(j+1)/4，
中弧成本c_ij-base_cost-(i+1)/2+(j+1)/4。
弧ID依次start0/start1、end0/end1、middle00/middle01/middle10/middle11；
原节点序(right1,s,left0,t,right0,left1)，图行序(C,conv,R)，主行序(conv,R,C)。

独立Fraction解析：
\[
x_{11}=t,\quad x_{00}=1-\alpha-\beta+t,\quad
x_{01}=\beta-t,\quad x_{10}=\alpha-t,
\]
\[
\max(0,\alpha+\beta-1)\le t\le\min(\alpha,\beta).
\]
由原始四成本直接求两个端点的目标最小值。两个端点的正权重路径分别作为seed，
初始顺序00/01/10/11；原/反序各一次，反序同时反转节点/弧/图行/主行/seed。
54模型 x 2端点seed x 2排列 x 2后端 = 432次。解析式保留Fraction精确值；
源列汇总及返回pi的平移真下界也用独立Fraction重算。

要求：
- 记录旧基线391/41的来源，并在修改前至少实际复现第5.1节自然失败；
  不把缺新字段的AttributeError或import错误当作数值red。
- 新版432次均应在正常预算内TOLERANCE_REACHED，最终目标/权重可行性符合解析值。
- 每轮独立复算原始列、P/D/rho/L、g_raw、g、A、eta；末轮满足本合同规则。
  独立精确下界检查与数值估计比较分开，不用工程eta替代数学证明。
- 给出正常收敛数、诊断数、实际轮数、负g接受数量及范围、最大eta和双后端分布；
  不要求每轮对偶/列顺序相同，不固定新版必须仍有41个负g。
- 不靠调32、改图/seed/成本/原始权重或容差刷过432；若出现其他原因，记录证据、
  区分底层已知数值债与本步问题。必须超出范围才能完成时停止并报告。
- 保留原第4步主例、8个不同模型的完整列LP对照，体现新旧功能均可复现。

## 7. 区分性保护测试

在现有unit及新verification中覆盖：

- 第5.1节真实反例，输出保留原始量与微小负g，不能裁剪或修正权重。
- eta边界必须黑箱分别覆盖：eta<=tolerance且g=-eta接受，略越界(-g>eta)拒绝，
  eta>tolerance时即使-g<=eta也拒绝；另有eta>tolerance且g>=0的正常停止例。
  eta不成为正向gap放宽，测试不能只覆盖一个近似相等点。
  可用精确二进制快照定位边界，测试独立计算期望，明确注入来源。
- 正g恰为tolerance、略大、略小；rho恰在-tolerance及两侧。
  正向g与rho阈值均不随eta扩大，不用abs(g)替换有符号门控。
- 原有P-D=8e-10、rho=-7e-10的1.5e-9正差距和约-5e-10负差距仍失败；
  第5.2节大常数下也失败，避免常数掩盖或放大预算。
- 第5.2节真实10次常数平移运行：最终路径、轮数、g和eta保持一致；
  展示大常数下g_raw与g不同，不误标严格零最优差距。
  再用路径成本1与1-5e-10、seed取1，c0作同样五种平移并配两后端，
  实际保持同一pi/rho、g约5e-10、同一eta与一轮容差停止；原始g_raw可为0。
  平移不变性按同一列/乘数/rho条件检查，不强求不同退化基产生相同pi。
- A=0、正负贡献抵消、有限乘积/绝对和/总和溢出与非有限输入/结果；
  新字段的None、只读快照、旧位置参数构造和重复求解所有权。
- 已有显著负rc路径、RMP/定价失败、后续轮失败、limit=1/2/3、退化目标不动、
  坏候选/坐标/改善分类等原保护继续通过。异常程序错误保持可见。

测试先定义真实症状与期望；允许受控快照注入，不放松生产证据检查来迎合测试。

## 8. 允许文件与范围锁

唯一允许：
- src/silo/decomposition/dag_column_generation.py：局部目标贡献、求和、判据、
  两个追加迭代字段及对应说明；不改公开入口参数/状态枚举/列域。
- tests/unit/test_dag_column_generation.py；
  tests/verification/test_dag_column_generation_oracles.py仅调整本步字段核对；
  新增tests/verification/test_dag_cg_bound_consistency.py。
- docs/dag_column_generation.md：当前判据、字段和读取/版本差异。
- learning/lessons/L0004-column-generation/README.md、exercises.md、solutions.md；
  learning/CATALOG.md。
- .silo-dos/project_profile.md：本步真实状态/基线/限制与建议。
- 本任务匹配新报告；派生tasks/INDEX.md。

禁止LP/core/modeling/presolve/mip/cuts/CLI/io/外部接口、restricted_master.py、
dag_pricing.py、utils/numerics.py、decomposition/__init__.py、通用CG/日志/toy、
L0001–L0003、旧合同/报告、研究资产/notes、其他docs、ROADMAP/阶段/其他.silo-dos门控、
Skill/Agent、任务规则、依赖/build/native。禁止改全局容差、加外部solver、
修改RMP结果/乘数/权重、添加可行性定价/热启动/资源定价/性能优化或重写原始探针。
这是一个数值判定任务，支持性字段/测试/学习均服务同一目标。

## 9. Learning delivery：L0004 v0.2.0

保留十节、篇目路径和L0004-E01至E04身份；针对当前判据修订E03等受影响解答，
说明v0.1.0的严格L>P规则如何演进，原主例手算和对偶平移定理继续成立。
追加L0004-E05（自然反例、局部ULP与负g）、E06（公共c0消去及差距掩盖）和完整解答。
不单独建L0005复制同一主题。

原理包括实数代数恒等式与浮点求值顺序、原始差距与objective_gap、局部尺度/32ULP
工程约定及其限度；例子同时展示真实舍入反例和大c0；映射私有贡献求和与公开字段。
研究意义解释错误诊断如何影响后续迭代/耗时比较；局限须明确LP核验和DAG浮点边界、
32不是严格算法误差界，有限族通过不意味着一般数值稳定或精确LP核验。
正文完整可执行例至少运行自然反例和常数消去，保留第4步退化自动例可复现性。

verified_code使用真正包含本修正的完整实现提交，checked与verified_on依实际核验；
可代码/测试A提交后再学习/报告B，同一原子任务。提交前draft/null，保留旧版本来源记录，
不把旧857397e当成本步新数值规则的已核验基线。

## 10. 执行、检查与验收

1. 记录HEAD/branch/status/cached origin差异、解释器及silo.__file__，
   确认本次签发提交及已知ahead授权。开发对话是唯一写入协调者。
2. 复现最小自然失败；建立独立族与保护检查，再实现局部修正。
3. 签发阶段experiment_auditor已做一次只读证据设计复核，建议强化平移、例外三边界
   和注入实际-g>eta检查，已纳入；服务未跑实验/未改文件，不计作数学证明或新实测。
   执行时仅在发现独立实质疑点时补充有边界复核，
   由主执行线程负责实现和实测，不启动模型对照或并行写入。
4. 形成真实代码基线，完成L0004、API、报告/摘要/INDEX，再提交收尾。
5. 使用已有环境，从根目录执行：

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_dag_column_generation.py tests/verification/test_dag_column_generation_oracles.py tests/verification/test_dag_cg_bound_consistency.py tests/unit/test_dag_pricing.py tests/verification/test_dag_pricing_oracles.py tests/unit/test_restricted_master.py tests/verification/test_restricted_master_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

实际运行正文代码/六题的有限核对，检查十节、稳定题号、UTF-8、链接、围栏、公式及
真实verified_code。稳定全量之后纯文档收尾不重复全套；后续代码改变/失败/新疑点再补跑。

验收：最小自然例与432族恢复；原始负值不改写；消去c0的g与有限eta字段可解释；
实质正/负gap及其他无效证据不被例外吞掉；大常数不掩盖差距或扩大预算；
旧功能、全量质量、L0004、文件范围和Git约定通过。
发现需要改LP/RMP/定价器、提高32/容差或扩展列域才能通过，报告最小缺口并停止扩展。
完成本任务后停止，不自动进入下一步。

## 11. 报告与结束回执

报告记录实际起点、旧症状和最小red、新字段/公式/常数/比较顺序及版本语义；
432族完整数据/生成方法/解析独立性、逐轮与最终数量、自然/注入证据区别；
g_raw与g差异、负g接受范围、eta范围和禁用例外分支、实质矛盾/大c0保护的结果；
原始核验未放松的证据、测试失败/修复、质量/结构/教学检查及作用边界；
变更文件、scope偏离、只读服务实际范围、实现/学习提交及未解决问题。
禁止将签发的前瞻分类、只读审查或历史数据重复计作新实现实测。

Git记录status、branch、log -5、cached origin差异、push not_attempted、
remote_sync_status；单次命令Git身份参数，不改全局配置。
报告自身提交通过
git log -1 --format=%H -- tasks/reports/20261019-05-01_cg-bound-consistency_report.md
在提交后定位。最终回执包含当前能力、实际验证、L0004修订、限制、本地提交及未推送。
在开发对话报告后停止，等待silo-solver-1010审查，不向其他对话发消息。
