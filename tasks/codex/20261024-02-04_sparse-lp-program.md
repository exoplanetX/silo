# 20261024-02-04：同源码warm与原工件溯源窄续接

## 身份与直接授权

- 原任务块SILO-SPARSE-LP-20261024的RR04，签发2026-10-25；起点9dcbfee8e63fa3dec18d202392cf59d22c93cffc。
- 用户直接回复call_b401b2090a634e03b64bcdcebf18fc2f：“授权该窄续接包（推荐）”。
- 获批问题包含：当前同源码启动前确认无并行重型作业，持续记录宿主负载，仅再做1轮原固定80项warm（上限3→4）；两份已构建工件SHA保持不变，用已验证pip命令重新验收8个全新环境。
- 原输入、阈值、60秒/1GiB、总预算及全部失败记录保持。同一Goal01a15208-bea9-7030-aacc-95d785e8fa58、分支、原输出根和追加账本；local-commit，无push/发布。
- 原01/02/03合同不可变；本页只覆盖下述窄差异。RR02报告仍为唯一当前总报告。本页匹配报告为tasks/reports/20261024-02-04_sparse-lp-program_report.md。
- 推荐GPT-6 Sol/high；主线程唯一写入，必要的独立复核只读，不声称已经切换模型。

## 唯一续接范围

1. 正式warm上限3→4，仅一次round4，固定8轨迹×cold/warm×5重复，1600修改状态与80初始状态。原配对顺序、收益门、原空间核验和资源保护保持，不改算法、输入或容差。生产source SHA必须保持889d191b05736d36de4cd935aecf15e77900d6e7c0f2c5bb8d6bef5914439669。
2. 启动前使用原20诊断批次中的一次新20秒宿主观察，确认无观测到的并行重型作业；该记录不超过5分钟且源码/脚本/输入/环境一致才启动。原轮次由唯一真实账本父进程预约，typed human authority消费一次；持续保存宿主采样及末尾身份核对。运行期负载作为完整上下文保留，不新增原收益/正确性门或删去慢项。
3. 对原delivery/2780871b-820e-4387-a5c7-e56c2e7d612a中的工件做一次新的完整8环境安装矩阵，原summary SHA845cf2bd5521033a59d76f055b2ca4f81de8e0a99b8b4b88ac134116890c649c。wheel SHA为f51459bf9ceefd4c53416ab05dadab3a48f84f82e98d4c3b1930e59c9bdaba96；sdist SHA为7ce7840765d12b3383bf4655475e00e3b25f242477d0c2d7e952e81e307f2657。禁止重建或替换这两份工件。
4. 以uv创建新环境和安装原锁定运行依赖，ensurepip启用环境内pip，pip安装原工件以写入真实archive SHA。原check_installed.py字节及所有溯源/solver断言保持；每个组合最多一次原规则允许的纯环境重试，溯源/断言/solver失败仍不能按网络故障重试。

允许修改scripts/sparse_program.py、scripts/sparse_program/{ledger,delivery,host_load}.py及对应纯工具拒绝测试，以落实上述一次性保护；允许更新tasks/README.md6.11、当前mirror、INDEX、本页小报告、RR02总报告和已有交付/伴学结果状态。现有runner/resources/warm/checker/cases/oracles及固定组driver保持，不用工具修复改写旧证据。

## 预算与关闭

沿用原SP3/SP4各10800秒及总28800秒实账，不跨桶/重置；启动warm整组前按4800秒保护预约。capacity2、Netlib2、quality3、diagnostic20上限均不变；最后完整quality只能使用原剩余第3次。
前3轮warm和首次8安装全部失败及成本完整保留。无第5轮warm、无第三套安装矩阵授权。任何本轮失败均登记未达，继续完成原有且独立可完成的交付义务；不得用预算余额扩大次数。
仍须原八项全部符合且最终独立只读GO才完成同一Goal。原研究C HOLD、D/E未开始、native延期、远端CI pending及两治理文件原哈希保护保持。
