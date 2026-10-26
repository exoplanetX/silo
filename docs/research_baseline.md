# SILO 可靠研究原型基线

本轮来源：[唯一合同](../tasks/codex/20261026-03-01_reliability-io.md)、
[计划](../tasks/phases/reliability_io_20261026.md)。签发315fecbbd8f601edf7283949a7ea1d444700c987；
已验收算法锚点a9f321374d4ca4758aa63d178f224c33b2a1eb0f，原候选0.3.0a1。
当前候选0.3.0a2，产品提交42892035db426c4739b6c1a7ad9648852d2b1dc8；实际来源与结果由
[报告](../tasks/reports/20261026-03-01_reliability-io_report.md)记录。

支持域为既有一般形式LP/MILP，dense/sparse两引擎，原生算法不调用外部优化器。
稀疏程序已经验收的2000变量/5000行/100000非零和warm4结论限原固定输入及该次运行，
不代表任意同尺寸模型或一般工业稳定性。原研究C HOLD、D/E未开始、native延期。
本合同仅增加文件互操作和同域独立核验，不改算法、预处理、搜索、容差或失败语义。

LP公开API是`solve(model, SolveOptions(...))`；会话使用`LPSession`。
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

本地6743项完整质量通过；96次格式往返、16手写正例、25拒绝例与2次微扰拒绝通过；
独立外部24文件解析通过（零外部优化）。正式首轮160请求全部通过，四个指定MILP各有2次实际分支，
四类编辑在dense/sparse均有真实warm入口；稀疏增列因身份变化重建，按实际诊断保留。
本地工件Windows3.13×dense/sparse×wheel/sdist四环境全部通过，每环境24请求、总96。
远端固定4源码质量、8安装job（各两个独立工件环境）、1外部格式job。
实际CI运行[40261995554](https://github.com/exoplanetX/silo/actions/runs/40261995554)绑定上述产品提交，
首轮最终failure：Windows3.12质量通过；Ubuntu3.10、Windows3.10的旧CG尾数精确断言失败，
Ubuntu3.12的旧RSS采样器缺VmHWM后抛StopIteration。依赖的8安装job及外部格式job未运行，
远端工件核验0/16、外部解析0/24。R1–R3和本地四环境完成，R4 HOLD，overall_complete=false。
这些是代码/配置路径失败，合同不允许第二次push或同SHA基础设施rerun；本轮已停止。
只允许一次任务分支push；CI和工件必须绑定真实SHA、平台、解释器、模块来源和报告。
不创建PR、tag、Release或PyPI发行。

一次非强制push成功同步产品提交至公共任务分支codex/sparse-lp-reoptimization；main未更新。
本地收尾文档提交不再次push，源码身份保持；旧Goal继续complete。

完整命令模板如下。输出路径应为未使用的位置；正式求解组、构建、安装与外部解析受合同轮次约束，
下面是复现说明，不会自动启动新的验收轮次。

```text
python -m scripts.reliability.freeze
python -m scripts.reliability.accept --formats --output UNUSED_FORMATS_JSON
python -m scripts.reliability.accept --solve --output UNUSED_ACCEPT_DIRECTORY/summary.json
python -m scripts.reliability.artifacts --build --output UNUSED_DIST_DIRECTORY
python -m scripts.reliability.artifacts --dist UNUSED_DIST_DIRECTORY --output UNUSED_INSTALL_DIRECTORY
python -m scripts.reliability.external --output UNUSED_EXTERNAL_DIRECTORY/summary.json
```

构建工具需要`build`，隔离安装/外部解析需要可获取所锁依赖的网络。外部highspy1.15.1
仅在单独验证环境安装；生产依赖范围未变。一次资源快照为20逻辑处理器、约32GiB内存、
可用约17.1GiB；它只说明开始时资源，不构成整段运行宿主稳定性证据。
