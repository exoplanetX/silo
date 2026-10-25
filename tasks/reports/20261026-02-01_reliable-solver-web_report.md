# L0016 可靠求解器专题网页执行报告

合同：[20261026-02-01_reliable-solver-web](../codex/20261026-02-01_reliable-solver-web.md)。
本单只完成现有工作台的教学展示与指定旧卡片同步；不计为新算法、原研究 C/D/E 或稀疏 Goal 的推进。

## 交付与原目标覆盖

- 直接 URL：http://127.0.0.1:8765/#learning/L0016，单元定位追加 /R01 至 /R08。
- 开发伴学首页突出专题入口；正文十节完整呈现，八单元按 web_outline.json 的真实标题定位。
- 正文、练习、解答切换；八道解答初始全部折叠，读者主动展开。相关篇目、代码和原文模式可用。
- 讲解 v0.1.0、checked、verified_on=2026-10-26、verified_code=c220c0cfcba1b3a3e6b5b8e352a8f0366ddda189 均读取教材，不用页面打开时间替代。
- 新增本地小型 TeX→MathML 文本转换器；覆盖本篇实际公式语法，包括上下标、分式、矩阵、转置/逆、求和、不等式。未知语法明确回退，不执行宏或 HTML。
- S0–S4 读取规范编排数据；eta 矩阵和右端从 L0016-E03 提取。固定2×2有理代数使用 BigInt 分数，展示中间向量、当前方程残差和明确的错误顺序对照。
- 正文继续唯一维护于 learning/；没有复制教材正文、修改规范资料或增设在线求解器。

## 卡片同步与证据边界

按 docs/sparse_program_acceptance_20261025.md 的已签收范围同步入口、八维相关卡片、LP/MIP 能力定位和交付卡片：

- 基础研究工具阶段，稀疏 LP / 连续重优化有固定验收范围；MIP/分解仍偏基础研究原型。
- 本地候选0.3.0a1，8隔离环境已有核验，远端Windows/Linux CI pending；未公开发布。
- 最大固定LP为2000变量/5000行/100000非零，不给任意同尺寸模型成功保证。
- 3.503361限指定源/输入/本机warm4该轮五重复、八轨迹修改段比值中位数。
  保留warm3/5各5个cold超时、warm4附加宿主观察器0样本，以及跨运行稳定性、
  全程宿主受控实验成功和唯一变慢原因均未确立的限制。
- 原研究A/B已验收、C HOLD、D/E未开始和native延期保持，原七步目标不变。
- 四级能力矩阵按能力/支持域使用；“基础研究工具阶段”是用途定位，没有把两种量表数值互换。

只更新实际核对过的来源身份；浏览器仍显示13项其他旧来源变化提示，未以批量刷新哈希掩盖未审内容。
历史M1–M5数据保留；原研究A–E流程只呈现对应五项，避免混排成同一研究清单。

## 实际检查、次数与预算

1. 运行教材 examples.py **一次**，八组精确教学计算全部通过；未导入/调用 LP/MIP solver。
2. 专属 pytest **两次**：初次25通过/1失败，发现显式TeX空格未覆盖；集中修正后26通过，1.09秒。
   回归覆盖规范身份/路径、缺失单元/标题/版本、零分母、只读路径边界、全部正文公式、
   脚本文本转义、未知语法回退、两类交互答案与最新卡片的固定范围。
3. 三个JavaScript文件 node --check 通过；workbench.py 与专属测试 Ruff通过；git diff --check通过。
4. 浏览器初次完整检查及一次集中修正后复核：
   - 十节正文、R01–R08八个真实标题逐项定位成功。
   - 默认完整正文45个MathML公式、14个分式节点、8个矩阵节点；修正后回退数0。
   - S0–S4实际操作目标值依次 -1/2、1、5/4、7/5、1/2；前三次旧点失去可行性，最后一次仍可行。
   - 普通解(4,-1)、转置解(2,-1)，代回残差(0,0)；
     错误转置解(-2,13/2)，残差(-1/2,27/2)，页面明确标为错误。
   - 八道解答初始open=0，主动打开E03核对答案；原文/代码和专题入口均实际可用。
   - 480px窄视口clientWidth=465、scrollWidth=465，无页面横向溢出，矩阵/中间步骤可读；
     临时viewport已重置，浏览器error/warn为空。
   - 评价、计算基准和版本/交付页实际抽查，未继续显示旧候选或稠密QR的当前定位。
5. 项目结构与索引检查一次通过：163合同、160报告、126模块、609本地链接；历史例外保持。
   使用 scripts/check_project_structure.py --write-index 更新索引；git diff --check 通过。

自动检查累计远低于合同10分钟上限；examples.py只运行上述一次。没有运行6670项全项目套件、
正式基准、安装、宿主性能观察、云API或新构建链。未新增后续任务或Goal，未push/发布。

实际检查入口为 .venv/Scripts/python.exe learning/lessons/L0016-reliable-solver/examples.py；
.venv/Scripts/python.exe -m pytest tests/unit/test_workbench.py -q；
node --check scripts/workbench/app.js、math.js、reliability.js；
.venv/Scripts/python.exe -m ruff check scripts/workbench.py tests/unit/test_workbench.py。
两次测试/语法/Ruff命令组加结构检查的工具墙钟合计约5.42秒；未对性能进行计时实验。

## 修改路径与残余限制

scripts/workbench.py；scripts/workbench/{app.js,index.html,style.css,catalog.json,math.js,reliability.js}；
tests/unit/test_workbench.py；docs/development_workbench.md；本报告与tasks/INDEX.md。
MathML转换仅承诺本篇实际语法，其他篇目未知语法明确回退并提供原文，未扩展为通用TeX排版系统。
13项未审旧来源提示继续存在。网页只读；其计算是固定教学代数，不能当作新的求解器或性能验证。

## Git、保护与停止

- 开始：codex/sparse-lp-reoptimization，HEAD=537b742c21ff1ee4c1f50e950e99a299b1828371，
  cached origin/main...HEAD=0/99；工作区已有两项受保护治理变化。
- AGENTS.md SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638。
- 根案例通告SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221。
- 两保护文件不暂存、不回退，OneDrive保持退出；src/、learning/、.silo-dos、阶段文件、
  旧合同/封存报告均只读。未切分支，不修改现有Goal或算法。
- Git mode=local-commit，实际提交由 git log -1 --format=%H -- 本报告路径 定位；
  push skipped，未fetch即时远端。remote_sync_status=dirty_worktree / local_ahead。
- 交付后保持原分支，工作区仅保留两项治理变化；本次11个允许路径单独提交。
  单提交后缓存差异为0/100，最终以提交后终端实查确认。
- 达到本合同网页完成线后交付停止。后续建议：在实际阅读中收集问题，本轮不自动增项。
