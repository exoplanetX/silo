# 第7步交付：LP无界终止核验与误报修正

## 1. 元信息、授权和实际基线

- ID：20261020-01-01_lp-unbounded-check。已扫描同日tasks/codex与tasks/reports，
  20261020尚无合同/报告，TT=01、RR=01空闲；“第7步”是开发序列，不是当日TT。
- 类型/风险：L2，现有Tableau/Revised的数值状态正确性修复；不改变项目阶段。
- 用户在第6步验收和具体第7步建议后明确批准“好，交付执行吧”；
  授权本合同一个原子任务的实现、测试、L0006、报告和本地提交。
- 来源：tasks/phases/phase_02_tableau_simplex.md、phase_03_revised_simplex.md的
  终止状态正确性；第2步合同第7节既有数值债；第6步验收总体评估。
- 签发/验收：silo-solver-1010，thread 01a1254a-b349-77d0-8c66-d4b711cd511f。
- 唯一实施协调：silo-solver开发，thread 01a15208-bea9-7030-aacc-95d785e8fa58。
  工作目录E:/OneDrive/workspace/codex/silo-solver。
- 实际签发前HEAD：e96e3e2709e413256ebbcdf880b811b341cf173a，干净main，
  cached origin/main...HEAD=0/8。八个已知本地提交按先后：
  8ee397e、15b403b、f0cc01a、b886458、8006344、02aed7d、70293f9、e96e3e2。
  用户已获知8个未推送提交后批准本步，继续授权覆盖上述八个及本次仅含合同/摘要/INDEX
  的签发提交；不为已知ahead再次询问。其他漂移/分歧/无关脏文件保留并报告，不重置。
- 从签发提交执行：git log -1 --format=%H -- tasks/codex/20261020-01-01_lp-unbounded-check.md。
  远端上次即时核对f0c5f31；本轮只核对cached引用，不以其冒充即时远端。
- 已验收基线：LP ad62e0f、RMP48c242d、定价12bfa35、CG15b403b、恢复02aed7d。
  3046项测试与Ruff已在第6步审查通过，不代替本步修改后的新验证。
- Git mode：local-commit；不push，不改全局/仓库Git身份。
- Expected report：tasks/reports/20261020-01-01_lp-unbounded-check_report.md。
- Learning delivery：新建learning/lessons/L0006-lp-unboundedness/README.md、
  exercises.md、solutions.md及CATALOG入口；已扫描L0001–L0005，L0006空闲。
- 推荐GPT-6 Sol / high；难点为近零枢轴、完整原始行、两种内部坐标与终止证据一致性。
  模型建议不表示实际切换；专业只读服务保持固定配置。
- Phase9保持open/parked、native deferred and unapproved、Phase10 not started。

## 2. 唯一目标和开始前阅读

唯一目标：两个LP后端的公开UNBOUNDED出口必须有完整原始模型的候选点和改善方向依据；
近零枢轴/清零/冗余行删除等使依据不足时，保守返回NUMERICAL_ISSUE。
本步不要求解决全部病态LP，也不将数值诊断替换为另一个未经核验的终态。

开始前完整阅读AGENTS.md、tasks/README.md、project_profile.md、technical_route.md、
remote_sync_proof.md、learning/README.md、WRITING_GUIDE.md；再读tableau.py、revised.py、
standard_form.py、optimality.py、core Model/Solution/Bounds，以及第1/2步合同/报告、
docs/lp_solver.md、docs/lp_duality.md、MIP无界修正报告和RMP/CG失败传播。

受支持LP的数学方向仍为MAX，连续变量、既有非负无有限上界域、LE/GE/EQ行。
MIN仍由RMP取反适配，不新增MIN直接求解、自由变量、一般变量界或新的解状态。

## 3. 已复现反例与原因核查

原始模型：
\[
\max z,\quad x-(1+5\times10^{-10})z=10^{10},\quad
x-z=10^{10},\quad x,z\ge0.
\]
两行相减强制z=0，x=10^10，有限最优值0。实际float的1+5e-10与1不同，
Fraction按实际输入值核查仍有相同结论。签发前主线程已再次运行，两后端均UNBOUNDED。

执行时先重现旧行为并记录实际内部路径，定位哪些信息在规范化、枢轴容差、
方向清零或人工列清理中丢失；不能只把“没有可选离基行”等同完整模型无界。
候选d=(1,1)满足第二行Ad=0，却违反第一行Ad=-(float(1+5e-10)-1)≠0；
即使该残差小于1e-9，沿x0+t*d会随t增长，无法支撑任意t>=0的可行射线。

单行epsilon*z<=b、epsilon>0但低于枢轴阈值，也有有限上界b/epsilon。
这类例子要与-epsilon*z<=b的真实无界例明确区分；小系数本身不是拒绝理由。

可从根目录独立运行的签发基线复现：

~~~powershell
@'
from silo.core.model import Model
from silo.core.variable import Variable
from silo.core.constraint import Constraint
from silo.core.objective import Objective
from silo.core.enums import ConstraintSense as S, OptimizationSense as O
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver
m = Model(
    name='step7-reproducer', variables=[Variable('x'), Variable('z')],
    constraints=[
        Constraint('r1', {'x': 1, 'z': -(1+5e-10)}, S.EQ, 1e10),
        Constraint('r2', {'x': 1, 'z': -1}, S.EQ, 1e10)],
    objective=Objective({'z': 1}, O.MAXIMIZE))
for backend in (TableauSimplexSolver, RevisedSimplexSolver):
    r = backend().solve(m)
    print(backend.__name__, r.status.value, r.message)
'@ | & ./.venv/Scripts/python.exe -
~~~

## 4. 数学核验：原始可行点与改善射线

对原MAX模型，充分依据为完整原变量坐标中的x0、d，l为实际原始下界：
\[
x^0\ge l,\quad A_{\rm LE}x^0\le b,\quad
A_{\rm GE}x^0\ge b,\quad A_{\rm EQ}x^0=b;
\]
\[
d\ge0,\quad A_{\rm LE}d\le0,\quad
A_{\rm GE}d\ge0,\quad A_{\rm EQ}d=0,\quad c^\top d>0.
\]
若原始变量下界有既有容差内的非零值，核验x0时仍须尊重实际原始界；
方向必须属于原始界的衰退方向，不假定规范化模型代替原输入。
本步不扩大求解域。支持域外、缺失/额外变量坐标、非有限数据、零/非改善方向或
任何原始行/变量界违背，都不能支持UNBOUNDED。

证明：对任意t>=0，x0+t*d仍满足每个原始行和界，而目标为
c0+c*x0+t*c*d，随t无上界。原目标常数c0不参与改善方向的判别。
只有d而没有原始可行点，不能排除“有衰退方向但可行域为空”的模型。

本步采用保守的终止候选精确检查：只在准备发布UNBOUNDED时，
用标准库Fraction对已有有限候选x0/d和原始模型数值做逐项乘积/求和与符号核验。
float按实际二进制值转换，int保留原整数；不先做浮点乘积再转Fraction，
不用Fraction(str(value))或limit_denominator投影成另一个模型/候选。
候选点与方向都按上述原始条件检查；所有判断成立才允许发布UNBOUNDED。
这不改变全局DEFAULT_TOLERANCE或正常单纯形迭代规则。

这是已有候选的核验，不是有理数求解器：不求精确逆、不做精确枢轴、候选修复、
有理重建或枚举。3*x=1且max z的真实无界模型，若只有x0≈1/3的浮点候选，
可能因精确原行不成立而返回NUMERICAL_ISSUE；必须明确记录这类保守拒绝的边界。
可证明数值模型实际有限二进制/整数数据上的候选充分条件，不声称所有真实无界模型
都能通过，也不恢复用户未提供的十进制精确意图。

## 5. 两个后端的最小接入

新增src/silo/lp/unboundedness.py作为LP层内部共享核验模块，不从lp/__init__.py
新增导出，不改变core Solution或CLI/JSON。函数/私有记录名字可按清晰最小实现调整。
核验器只读原始Model与完整候选，返回通过/拒绝原因；不调用solver、presolve、外部库求解，
不依赖decomposition/MIP，输入和候选不被修改。

在两个后端的Phase-II无离基行分支保留实际入基列和候选来源：
- 必须确认候选进入列是当前非基、列编号有效，基/列坐标无重复或冲突；
  若Tableau数值漂移令基本列被选中，直接NUMERICAL_ISSUE，不构造自相矛盾方向。
- 内部标准形可取d_entering=1，d_basic=-B^-1*A_entering，其余非基为0；
  原始变量投影须按实际角色/名称坐标处理，不能把松弛/剩余/人工列当原变量。
- x0来自该轮实际基的RHS；候选原始坐标齐全、有限。Tableau保留当前基和行RHS；
  Revised可在该终止候选处额外求解当前基，取得未清零的点/方向。
- 原始检查使用完整原Model，包括已删行、负RHS原方向和未清零小系数。
  检查前不能调用_clean_zero、夹成非负、删行、改RHS或修改方向来制造通过。
  若已有迭代状态发生过舍入，核验会拒绝不合法候选；不能放宽检查掩盖它。
- 为保留终止证据，可对两个模块的内部run记录追加带默认值的最小字段；
  具体为SimplexRunResult/RevisedRunResult；既有公开solve/solve_with_details参数、
  Solution字段和RevisedSimplexResult详情结构保持。
- 所有公开Phase-II UNBOUNDED路径均通过该门控，含无行模型、Phase-I之后及
  Revised既有兼容warm-start路径；不能只修solve而漏solve_with_details。
- 当前Phase I目标是负人工量和，理论上向上有界于0；内部若给UNBOUNDED，
  公开应为NUMERICAL_ISSUE并说明Phase-I矛盾。Revised已有保护保留，Tableau补齐。
  不将Phase-I内部射线用于原目标或产生原模型无界结论。

通过时保留兼容的UNBOUNDED消息关键词（旧Tableau测试要求no positive pivot row），
追加原始候选已核验说明；失败为NUMERICAL_ISSUE，消息区分point/direction/improvement/
coordinates/nonfinite/phase，尽量定位原始变量或行。内部候选缺失、无法构造/线性代数失败
均保守诊断，不重新求一次不同目标或递归调用solver。
公开非最优Solution仍objective_value=None、primal/slack/dual/reduced_cost/basis映射为空；
不把无界候选当最优解字段发布。既有最优、不可行、预算分支及对偶约定保持。

## 6. 固定240族、32组区分性对照与独立真值

新增tests/verification/test_lp_unboundedness_oracles.py，不依赖生产核验器给真值。
参数：
- epsilon=(-2^-24,-2^-32,0,2^-32,2^-24)；
- B=(1,2^32)，q=(2^-8,1,2^8)；
- 两行q*x-q*(1+epsilon)*z=q*B、x-z=B，x,z>=0，max z+c0，c0=-3；
- 行序原/反、变量序原/反、两个后端。
共5*2*3*2*2*2=240次，原始数据必须保持。

直接用Fraction逐项解释实际原始系数：epsilon≠0时z=0、x=B，最优c0，共192次；
epsilon=0时x0=(B,0)、d=(1,1)是精确见证，共48次。
q是二进制幂，给定数据不引入十进制意图误差。原式差不为零，不能靠容差判等。

签发前主线程以公开API实际运行：192有限中96 OPTIMAL、96误UNBOUNDED；
48真正无界均UNBOUNDED，两后端各半。细分按epsilon依次为
40 OPT/8误UNB、8 OPT/40误UNB、48真UNB、8 OPT/40误UNB、40 OPT/8误UNB。
q与行序也影响实际阈值，不能把大epsilon组全记成OPT。
上述是旧版签发基线，不计为新实现通过；开发在改动前逐项记录参数和旧状态。
新实现验收：
- 全部192次有限模型只允许OPTIMAL或NUMERICAL_ISSUE；
  OPTIMAL必须完整原始最优核验通过、目标为c0，绝不UNBOUNDED/INFEASIBLE；
- 保留改动前逐项记录的96个旧OPTIMAL个案；大epsilon组至少80次OPT、
  小epsilon组至少16次OPT。不能为只修无界出口而破坏既有正常最优路径；
- epsilon=0的48次仍必须UNBOUNDED，不能把所有终止一律降级NUMERICAL_ISSUE；
- 报告真实状态分布、两后端/排列、失败原因；保守诊断不能算成已求得最优解。
主反例原5e-10/1e10另行双后端覆盖，有限最优0或数值诊断，原始输入不改写。
在同一verification文件追加32次固定端到端对照，核心与对照共272次：
- 字面原式epsilon=5e-10、B=1e10、q=1、c0=0，行序2×变量序2×后端2，共8次，
  原始最优0或NUMERICAL_ISSUE，绝不UNBOUNDED/INFEASIBLE。
- -x+z<=-1、max z+5，变量序2×后端2，共4次；x0=(1,0)、d=(1,1)，必须UNBOUNDED。
- -x<=-2、-x>=-1、max z+5，变量序2×后端2，共4次；严格不可行，保持INFEASIBLE。
- sign*epsilon*z<=b、max z+5，epsilon取2^-32/2^-24、b取0/1、sign取-1/+1、
  后端2，共16次：8个负系数例必须UNBOUNDED；4个大正系数例保持OPTIMAL(5+b/epsilon)；
  4个小正系数例允许同一正确OPTIMAL或NUMERICAL_ISSUE。
共272次的解析分类为208有限、60真正无界、4不可行；有限例的100个既有正常OPT路径
须保留（240族96个及大正系数4个）。真实运行不能混同这些解析分类与求得最优的数量。

对发布UNBOUNDED的运行，以测试观察包装记录实际送给共享核验器的原Model/x0/d，
不能只拿自设合法见证代替真实候选；确认是完整原模型、调用实际门控，再由测试独立
Fraction原项计算核对所有点/方向条件与严格改善。测试oracle不调用生产核验器或
标准形/基重建助手，不改变候选或返回值；保留同一后端对比不能替代该独立依据。

## 7. 区分性单元测试与上层回归

新增tests/unit/test_lp_unboundedness.py，至少包括：
1. 核验器直接输入：合法点/方向，LE/GE/EQ、零系数省略、负RHS、空行集、
   非零c0、内部变量名貌似原名但坐标不同，完整坐标和所有权。
2. 合法方向但点不可行（含互相矛盾的固定坐标）、合法点但方向违背原行、
   d有微小负分量、c*d为0/负数、方向为0；不得只查方向。
3. 精确微小违背：Ad≠0但abs(Ad)<1e-9，点残差同类，均拒绝；
   近消去乘积必须先转换原项，不能普通float点积恰好为0就通过。
   int超过2^53的原值要保留，float对应实际二进制值；数值表示语义要有测试。
4. epsilon*z<=b的有限上界与-epsilon*z<=b的真正无界对照：
   epsilon取2^-32、2^-24，b取0、1；正系数应有限最优或数值诊断，负系数应保留
   可精确核验的真正UNBOUNDED。用无溢出/下溢的二进制幂缩放方向，
   防止绝对容差造成大小相关误判；任意浮点缩放本身可能舍入，不能声称其保持精确残差。
5. 真无界主例：无行max z；x-z=B、max z；-x<=-2、max x（负RHS/Phase I）；
   LE/GE/EQ混合含冗余行，需耦合改善两坐标的射线；既有真无界回归保持。
   另以-x<=-2、-x>=-1、max z构造负RHS矛盾模型，双后端应保持INFEASIBLE；
   有合法d=(0,1)不能弥补可行点缺失。该自然例与直接候选注入分别计数。
6. 3*x=1、max z的候选边界：若已有有限浮点点无法精确满足原行，
   明确NUMERICAL_ISSUE并写明限制，不能靠点容差当成严格依据。
   近矛盾x=1与x=1+2^-40、max z的完整模型也不得发布UNBOUNDED；
   本步允许现有INFEASIBLE或NUMERICAL_ISSUE，不要求重写一般不可行判定。
7. 缺失/额外坐标、NaN/inf、无效内部候选、终止候选基求解失败等返回清晰诊断；
   用合成/monkeypatch隔离Phase-I伪UNBOUNDED，两个公开后端均NUMERICAL_ISSUE。
   不把注入结果宣称正常后端自然出现；程序逻辑异常不吞成普通数值状态。
8. 已删原始行不能被绕过，保留负RHS、变量/行序及原目标常数；
   不仅直接测核验器，必须双后端实际公开solve（Revised含solve_with_details）
   证明确实经过门控，并覆盖无行与Phase I后入口。
9. MIN RMP上的同一有限反例（min -z+c0）不得发布最优假字段；
   未确认的UNBOUNDED应成为NUMERICAL_ISSUE并由RMP清空证据。
   旧CG/恢复器的MASTER_FAILURE或原始复核NUMERICAL传播保持；
   MIP底层数值失败应传播，不能制造UNBOUNDED/INFEASIBLE/最优incumbent。
   用测试替身区分保护路径；不改上层生产代码。
10. 旧真正MIP无界、整数不可行/分支可行性探针、RMP零列无界、
    CG/恢复三例、648族及数值gap规则完整回归。

## 8. 范围锁和允许文件

唯一允许修改/新增：
- 新src/silo/lp/unboundedness.py；src/silo/lp/simplex/tableau.py、
  revised.py仅为候选保留、终止核验和Phase-I矛盾诊断所需窄改。
- 新tests/unit/test_lp_unboundedness.py、
  tests/verification/test_lp_unboundedness_oracles.py。
- 新docs/lp_unboundedness.md；docs/README.md加入口；
  docs/lp_solver.md仅同步终止语义/新限制/链接；
  docs/development_layout.md仅补真实入口和依赖。
- 新learning/lessons/L0006-lp-unboundedness/的README.md、exercises.md、solutions.md，
  以及learning/CATALOG.md的新篇入口。
- .silo-dos/project_profile.md本步实际状态/基线/剩余限制；
  本任务新报告；派生tasks/INDEX.md。

禁止改core（含Solution/Status/变量界）、modeling、presolve、standard_form.py、
optimality.py、basis/pricing/ratio_test/pivot及其他LP模块、utils/global tolerance、
全部decomposition/MIP/cuts/uncertainty/interfaces/CLI/io、旧测试、L0001–L0005、
旧合同/报告、notes/研究资产、其他docs或.silo-dos门控、ROADMAP/阶段、
依赖/build/native、Skill/Agent。
不更改正常迭代枢轴政策、通用行删减/缩放、Phase-I清理逻辑或求解域；
不补全一般Farkas核验、一般状态框架、精确求解器、额外可行性求解、热启动/性能研究。
若仅靠窄终止保护仍需改禁区，记录最小缺口停止扩展，不自行重构。

## 9. L0006｜LP无界判定：可行点、改善方向与数值核验

遵循十节，链接L0001原始行约定和L0002/L0004/L0005的上层诊断边界。
正文必须从x0+t*d推导LE/GE/EQ及变量界的齐次条件，
区分“无离基行”的算法信号与完整原始模型依据；说明清零/删行/负RHS坐标恢复、
微小非零Ad为何不能当0、点与方向两部分缺一不可、c0不参与改善率。
给出主反例、一个耦合真无界例、tiny正/负系数对照、1/3候选保守拒绝的完整代码。
完整程序实际双后端运行并断言，不用私有构建助手伪造新solver通过。
研究价值：提高上层RMP/MIP/CG状态可信度，为效率研究固定正确基线；
成熟基础核验机制本身不构成论文贡献，精确标量候选检查也不等于通用精确LP求解。

至少五题L0006-E01起及完整答案：充分条件证明、主反例与小系数、两后端候选投影、
数值点/方向与精确条件、上层传播及支持边界。
明确本步会保守拒绝某些真实无界浮点候选、按实际数值解释模型、
不承诺高维/任意尺度/全部终态正确性或工业性能。
本步仅加强两个原生LP后端的直接无界出口；presolve独立终态、外部/替身后端与
MIP整数可行性证明仍保留各自边界，不将本核验自动外推到其他独立路径。
verified_code必须是包含新guard和两后端接入的完整实际提交；A前draft/null，
A后checked和真实日期/哈希，允许实现A后学习/报告B属于同一任务。

## 10. 执行、验收和停止

1. 记录实际HEAD、branch/status、cached origin差异、解释器与silo.__file__，
   核对八个已知本地及签发提交授权；唯一写入协调者。
2. 先重现旧主反例/240族和32对照，再写区分性检查、最小实现；
   import错误不算算法red，不以删旧测试或调整数据/阈值制造通过。
3. 定位两后端具体误报链条，记录候选来源与原始检查拒绝原因；
   签发前theory_architect只读复核支持“点+方向原始Fraction核验”，要求进入列非基、
   完整原模型及Phase-I矛盾保护；experiment_auditor要求字面反例、负RHS真假对照、
   点/方向独立Fraction原项oracle与上层传播，均落实。其“大epsilon全OPT”建议与实际
   q/行序基线冲突，由主线程按80/16细分和逐项保留96旧OPT裁决；验收以本合同为准。
   两项只读意见不计为实现通过或实测，未把意见重复计作独立运行。
4. 新测试明确列出成功保留与保守诊断的数量，真实无界必须有正对照。
5. 在现有环境从根目录执行：

~~~powershell
$env:PATH = (Join-Path $PWD '.venv/Scripts') + ';' + $env:PATH
& ./.venv/Scripts/python.exe -m pytest tests/unit/test_lp_unboundedness.py tests/verification/test_lp_unboundedness_oracles.py tests/unit/test_tableau_simplex.py tests/unit/test_revised_simplex.py tests/unit/test_revised_tableau_parity.py tests/unit/test_mip_unbounded_status.py tests/unit/test_restricted_master.py tests/verification/test_correctness_oracles.py tests/unit/test_dag_column_generation.py tests/unit/test_dag_feasibility.py tests/verification/test_dag_feasibility_oracles.py -q
& ./.venv/Scripts/python.exe scripts/check_project_structure.py --write-index
& ./.venv/Scripts/python.exe scripts/check_project_structure.py
& ./.venv/Scripts/python.exe scripts/check_quality.py
git diff --check
~~~

保留已有可选外部oracle的原有运行方式，但新guard/测试不得新增外部solver依赖或调用。
核验L0006完整程序、有限习题、十节/稳定题号、UTF-8/链接/围栏/公式与真实代码哈希。
代码稳定且完整质量通过后，纯文档收尾做轻量检查；代码再变/失败/实质疑点才补跑。

验收：主反例不再误报无界；272次按第6节分类；真假小系数和点/方向分开测试；
两个后端全部公开UNBOUNDED出口有原始核验；Phase-I无界不外泄；
既有功能/全量质量通过、非最优空字段、L0006实际核对、diff仅允许范围。
若回归暴露超范围债，原样报告，不放宽测试/容差；不能声称全部尺度稳健或全部LP状态已认证。

报告写清：实际基线、旧错/新状态、实际原因链、候选构造与完整原始核验、
精确float/int语义、Phase-I/Phase-II、272端到端/240核心/32对照/单元/注入/上层回归各自实际计数、
保守拒绝的真实无界例及原因、旧功能保留、L0006核验、实现/文档提交与未解决限制。
Git记录status/branch/log -5/cached差异、push not_attempted、remote_sync_status=local_ahead_origin；
身份仅使用单次命令参数。报告自身提交后通过git log -1 --format=%H -- 报告路径定位。
提交后停在第7步，等待silo-solver-1010审查，不自动进入重优化/第8步、
不push、不向其他对话发消息。
