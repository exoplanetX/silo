# SILO 可靠研究原型基线

本轮来源：[唯一合同](../tasks/codex/20261026-03-01_reliability-io.md)、
[计划](../tasks/phases/reliability_io_20261026.md)。签发315fecbbd8f601edf7283949a7ea1d444700c987；
已验收算法锚点a9f321374d4ca4758aa63d178f224c33b2a1eb0f，原候选0.3.0a1。
新候选目标0.3.0a2，目前处于执行中；实际来源与结果由
[报告](../tasks/reports/20261026-03-01_reliability-io_report.md)记录。

支持域为既有一般形式LP/MILP，dense/sparse两引擎，原生算法不调用外部优化器。
稀疏程序已经验收的2000变量/5000行/100000非零和warm4结论限原固定输入及该次运行，
不代表任意同尺寸模型或一般工业稳定性。原研究C HOLD、D/E未开始、native延期。
本合同仅增加文件互操作和同域独立核验，不改算法、预处理、搜索、容差或失败语义。

LP公开API是`solve(model, SolveOptions(...))`；会话使用`LPRelaxationSession`。
格式为既有JSON、free-MPS及[严格SILO-LP-1](lp_format.md)。CLI `optimize` 输出schema2解；
`convert`只转换模型。JSON/MPS原行为保持。失败状态包括infeasible、unbounded、limit、
numerical_failure、invalid_model和unsupported，不能把未收敛结果当最优证明。

冻结32基础模型（24LP/8MILP）和4修改状态；oracle使用原始数据的精确有理数、
顶点/对偶依据、Farkas矛盾或改善方向，MILP完整枚举有限整数格。
每例最多20000候选基、2000000有理运算、30秒。输入/profile/oracle/比较器先提交再修改生产代码。
这是操作性保留集，同一执行者能读取，不称真正盲测；pytest不运行正式接受集。

格式核对采用精确二进制有理语义；浮点解沿既有`1e-7`原始可行、对偶、互补、
目标及整数分量规则。继承界和gap遵循现有数值协议，不能外推到任意条件数下方向安全。
默认缩放/预处理保持；固定四个间隙MILP用`cuts=False, heuristics=False`检查基础分支。
一轮160请求、最多两轮；LP10秒、MILP30秒、整轮15分钟。

复现按[格式文档的入口](lp_format.md)执行。新证据只落在`outputs/reliability_io_20261026/`，
本地自动验证累计60分钟、局部20批、全质量2次；单独账本不改旧Goal。
资源快照仅说明CPU/RAM/解释器/依赖，测试子进程BLAS/OMP/MKL线程设1，
不施加新的宿主门，不操作用户进程；OneDrive保持退出。

本地工件检查固定Windows3.13×dense/sparse×wheel/sdist四环境；远端固定4源码质量、
8安装job（各两个独立工件环境）、1外部格式job。实际CI未取得之前保持待完成。
只允许一次任务分支push；CI和工件必须绑定真实SHA、平台、解释器、模块来源和报告。
不创建PR、tag、Release或PyPI发行。
