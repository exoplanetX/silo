# 20261024-02-06：连续监督缺陷的一次收口包

原SILO-SPARSE-LP-20261024任务块RR06，2026-10-25签发，起点51d7c2a。
用户直接回复call_de30bd6eb2384ab388f2c29188b6049d：“授权该监督收口包（推荐）”。
授权明确：记录器二文件补丁通过真实并发回归及独立工程审核后，应用补丁和一次性额度门，完整质量3→4、原固定warm4→5各仅追加1次；宿主预检≤3×20秒，包含RR05余1窗、新增≤2窗。保持算法、原工件SHA、输入、阈值、60秒/1GiB及总预算，保留失败，连续记录及最终独立GO后完成原目标。

同一Goal01a15208-bea9-7030-aacc-95d785e8fa58、分支和原追加账本；RR02仍唯一当前总报告。本页小报告为tasks/reports/20261024-02-06_sparse-lp-program_report.md。原合同不变；本页窄覆盖RR04正式次数与RR05代码冻结，仅限如下收口。

## 精确修补与一次性权限

- 已审二文件补丁为outputs/sparse_lp_program_20261024/proposals/observer_private_bindings/observer_private_bindings.patch，SHAdac3381fd06c668dcc22794ba629efd4dd22ff4aeab190af0bc2932a03533f97。
- host_load.Sampler使用私有ctypes.WinDLL("kernel32")函数对象，避免与真实资源guard共享argtypes；引入同一真实资源监控与观察线程的5样本交错回归。原solver、resources/runner/warm/checker/cases/oracles及固定驱动保持。
- 允许scripts/sparse_program.py、scripts/sparse_program/{ledger,host_load}.py及tests/unit/test_sparse_host_load.py落实额外一次quality和warm的精确人类授权、同源、真实parent及一次child消费门；加入缺授权/跨源/超次/错误命令拒绝测试。保持默认额度，只有typed human_supervision_recovery才启用quality4/warm5。
- 原生产source889d191b05736d36de4cd935aecf15e77900d6e7c0f2c5bb8d6bef5914439669不变；两工件及8安装结果复用原SHA，不重建/重安装。
- 原正式80child、1600修改/80初始、五重复/交替顺序、原真值/KKT/1.5中位收益/6-of-8门及60秒1GiB全部不变。所有80项均执行，不能剔除慢项。

## 预检、预算与终验

RR05未用的1窗转入本包，总窗口最多3（新增最多2）；在同一host根和账本单列host-preflight，0solver。唯一human_supervision_recovery及逐窗记录核对旧余量，禁止再单独消费被转移的旧RR05余窗。quiet标准、20秒10样本、5分钟有效期和身份冻结保持；运行期负载持续如实记录为上下文，保留原数值门。

先集成精确修补、静态/组件/独立门，再做唯一完整quality4；该命令通过、代码固定及有效预检后启动唯一warm5。运行监督前后source/scripts/inputs/environment一致，trace完整并与结果绑定；独立复核全部原始结果、收益及监督记录后才签最终GO。

沿用SP3/SP4各10800秒及全局28800秒；warm整组仍按4800秒保护预约，质量1200秒保护。诊断20/20、capacity2/2、Netlib2/2及其他原限额保持。全部旧失败、warm4数值GO/监督HOLD及真实成本保留，不重置、不跨桶。

无第6轮warm、第5次质量或本包第4窗权限；本次失败须保留未达，不再自行增加。允许维护README6.11、mirror、INDEX、当前RR02总报告、本页报告与已有伴学/交付状态。local-commit，无push/发布；两治理文件原哈希保护，原研究C HOLD/D/E未开始、native延期和远端CI pending保持。推荐GPT-6 Sol/high，不声称已切模型。
