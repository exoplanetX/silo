# 20261024-02-07：运行条件稳定性筛查与条件式收口

原SILO-SPARSE-LP-20261024任务块RR07，2026-10-25签发，起点edf1bc051164641887649c9a11f42d0c86ee8df9。
用户直接回复call_8b0bb8cd29ae4555b6794390d2bc8466：“授权你暂停并执行（推荐）”。
本页激活已审提案outputs/sparse_lp_program_20261024/proposals/runtime_stability/plan.md。
同一Goal01a15208-bea9-7030-aacc-95d785e8fa58、原分支/输出根/追加账本；RR02仍唯一总报告。
新授权允许续接原blocked Goal；不新建Goal，后续阻断审计从本次重新计数。

## 原完成线与唯一目的

原八项交付不变。两条诊断仅用于判断同步暂停这一受控条件是否具备正式复验前提，
不得替代80项验收，不声称OneDrive唯一因果。原算法source
889d191b05736d36de4cd935aecf15e77900d6e7c0f2c5bb8d6bef5914439669、原工件SHA、输入/真值/
KKT1e-7、五重复、正式60秒/1GiB、median1.5及6-of8门均保持；所有旧失败保留。

## 暂停、窄改动与验证

允许通过桌面界面临时暂停OneDrive，必要时退出客户端；记录原状态和动作时间，包结束无论成败均恢复原状态。
不得删除/移动/修改云端文件或权限，不改电源计划/priority/affinity，不改solver数学或选项。
桌面没有可定位窗口时按computer-use规则请求用户协助，不能猜句柄或绕过登录/安全界面。

允许scripts/sparse_program.py、scripts/sparse_program/{ledger,host_load}.py及相应工具拒绝测试落实
唯一typed human_runtime_stability_recovery：quality4→5、warm5→6、diagnostic20→22。
host覆盖OneDrive及同步进程，quiet阈值原值保持。同步覆盖补丁SHA
104df88e785392e032940624003d3870b56d538573d52582910d53a959b52376。
允许原outputs/components/下新增独立遥测/诊断驱动、主机采样、JSON收据；绑定其实际源码SHA。
保护resources/runner/warm/checker/cases/oracles等固定driver，原src/pyproject和两份工件不改，不重建/重安装。
工具先静态/组件/独立工程门，再唯一完整quality5，成功后冻结全部受检代码/测试/输入。

## 两次固定cold诊断

最多两条原BOUND02 cold轨迹，每条固定21次公开调用（1初始+20修改），请求/真值/调用顺序原样。
solver child仍60秒/1GiB；每批总保护75秒，另15秒只供遥测保存与结果收尾，不能算入或替换child wall。
全部失败、未返回和真实started/completed保持。每次记录完整child wall、user/kernel CPU、CPU/wall、
峰值RSS、进程读写字节/操作数；每约2秒记录总CPU、磁盘、同步进程和20逻辑核ActualFrequency，
并记录AC状态/活动电源GUID/priority/affinity和暂停状态。不得把缓存I/O计数直接当作物理盘归因。

首条前须有效quiet预检；两条连续完成于同一预检5分钟内，逐次核验暂停状态和原身份。
两条均完整21调用正确、原空间KKT/真值通过、完整child wall≤45秒、遥测完整，才能准入正式组。
AC/电源GUID/priority/affinity相同；频率按每样本20核ActualFrequency中位再取轨迹中位，
两条相对差abs(m1-m2)/max(m1,m2)≤10%，字段完整/正且相邻采样间隔≤5秒。
标志位仅原样保存，不附加未核实的功耗解释。该余量只控制是否启动正式组，不改变原正式完成线。
任一诊断错误、超时、超过45秒、身份/暂停/遥测/稳定条件未达，保存收尾证据后停止，不跑完整组或补诊断。

## 条件式warm6与预算

两诊断全部通过后，再取得新有效quiet预检并确认仍暂停，仅运行一次原固定warm6：
80child/1600修改/80初始、五重复、交替顺序、原输入/阈值/60秒1GiB及收益门原样。
必须持续记录主机、源/脚本/输入/环境冻结并绑定实际summary与trace；最终原八项和独立GO全过才完成Goal。

预检最多4×20秒，包含RR06未用1窗（转入并关闭旧包）及新增≤3窗；0solver，原quiet标准/5分钟有效期不变。
沿用SP3/SP4各10800秒和总28800秒，不跨桶/重置。两诊断最多150秒，host最多80秒，
quality仍1200秒保护，完整warm仍4800秒保护预约。原capacity2/Netlib2、旧费用和其他上限保持。
无第三条诊断、warm7、quality6或本包第五窗权限；本次未达保留未达，不自行增加。

允许维护tasks/README6.11、mirror、INDEX、本页小报告、RR02唯一总报告和已有伴学/交付状态。
匹配报告tasks/reports/20261024-02-07_sparse-lp-program_report.md；local-commit，无push/发布。
两治理文件按原SHA保护，原研究C HOLD/D/E未开始、native延期、远端CI pending保持。
推荐GPT-6 Sol/high，难点为Windows遥测和证据/计数一致性，不声称已切模型。
