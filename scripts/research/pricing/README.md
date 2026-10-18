# Pricing 研究资产与复现

这里维护 notes/26..30 对应的原始研究探针、来源清单和运行入口。探针是有限核验、
反例和参考实验，尚未形成 SILO 的正式定价器，也不提供性能加速结论。
研究判断继续在 silo-solver-1010 讨论；开发执行按单独合同推进。

## Archive probes

| 名称 | 原始源码 | 用途 |
|---|---|---|
| theory | [公式与反例](probes/pricing_theory_checks_20261011.py) | 精确有理数、界传递与固定对滞回等有限核对 |
| signature | [固定核验目录](probes/pricing_signature_checks_20261011.py) | 分组报告与结构反例；快照重建不代表动态树实现 |
| frontier | [状态与修复](probes/pricing_frontier_state_checks_20261011.py) | 小 DAG、精确状态和参考修复语义 |
| locality | [边界条件](probes/verify_boundary_conditions.py) | 固定随机种子的精确算术探针 |
| application | [外部参考应用例](../../../examples/research/pricing_application_probe.py) | 公开实例、显式预算和 SciPy/HiGHS RMP 参考 |

五份原始源码按字节保存，哈希、原始会话与结果身份见 [provenance.json](provenance.json)。
应用探针使用外部求解器，按项目规则放在 examples。其他四份位于 scripts。
维护工具 [run_probe.py](run_probe.py) 只将 locality/application 顶层 HERE 路径在执行时
重定位到忽略的输出目录；断言、数学逻辑和原始源文件保持不变。
原始探针的固定 date 字段属于历史元信息；每次实际运行时间另记入 run_manifest.json。

## Inputs

应用输入固定为 BartvanRossum/rcsp-benchmark 的
698703dd98607b3f010bdd859a608be1d3b08133，16 个文件逐一记录 URL、字节数和 SHA-256，
包含来源说明和原始 LICENSE，见 [source_manifest.json](source_manifest.json)。
原始数据不提交本仓库；按固定版本重建到 outputs。应用探针需要现有 optional-backends
中的 SciPy，另外四份只需 Python 标准库。此任务没有新增依赖。

从项目根目录执行：

~~~powershell
& .\.venv\Scripts\python.exe scripts/research/pricing/run_probe.py --verify
& .\.venv\Scripts\python.exe scripts/research/pricing/run_probe.py --prepare-inputs --fetch-missing
~~~

已有缓存也要通过全部字节数/哈希检查。下载失败或来源不符会停止，绝不回退到 latest。
--fetch-missing 是明确的联网选择；已有损坏缓存会报错，需要单独核对。

## Synthetic probes

~~~powershell
& .\.venv\Scripts\python.exe scripts/research/pricing/run_probe.py --probe theory --output outputs/research/pricing/my-run/theory
& .\.venv\Scripts\python.exe scripts/research/pricing/run_probe.py --probe signature --output outputs/research/pricing/my-run/signature
& .\.venv\Scripts\python.exe scripts/research/pricing/run_probe.py --probe frontier --output outputs/research/pricing/my-run/frontier
& .\.venv\Scripts\python.exe scripts/research/pricing/run_probe.py --probe locality --output outputs/research/pricing/my-run/locality
~~~

每个 --output 必须是新的目录，统一位于 outputs/research/pricing，避免覆盖旧证据。
每次产生 stdout、stderr、JSON 结果和运行清单；清单记录实际时间、解释器、
源码/运行器/输入清单哈希、退出码和结果哈希。超时或失败同样保留记录。
运行清单与完整结果由 Git 忽略，不作为本仓库的版本身份。

## Application

~~~powershell
& .\.venv\Scripts\python.exe scripts/research/pricing/run_probe.py --probe application --output outputs/research/pricing/my-run/application --timeout 180
~~~

原始预算保持 500000 个显式状态、3000000 条边、CG 最多 200 轮。输出中的
iteration-cap / explicit-state-budget 状态要原样解释；退出码 0 只表示有限核验执行完毕。
s6_t450 超预算不代表其完整状态图已建立；s2_t90 达迭代上限不代表完整列生成收敛。
参考脚本总时长不能解释为方法加速倍数。

## Historical results

五份原始 JSON 的文件名、字节数和 SHA-256 都在 provenance.json 的 historical_result
字段。原始 JSON、五篇笔记原件、五份源码、输入和 resfs 三份原件共 35 个文件，
在整理前已复制到项目同级的 silo-solver-backups/20261018-04-01_research-assets，
每个文件均与原件按哈希核对。该目录在 Git 仓库外；备份清单包含具体原路径。
这里只确认本地副本，不声称已检查 OneDrive 云端上传。

笔记中的“结果”链接指向此节，历史结果身份由清单定位；新运行结果使用独立输出目录。
本轮复现的实际范围与差异查
[纳管执行报告](../../../tasks/reports/20261018-04-02_research-assets_report.md)。
原始结果记录和新的运行证据保持各自来源，不能仅凭文件名相同认定对应。

## Maintenance

原始探针采用哈希校验，保持可核对的历史字节，质量入口仅对这五个确切文件跳过
Ruff 风格重写；维护中的 runner 与其余代码正常检查。后续算法改进应使用新任务
和 Git 提交，先明确原理、证据与学习交付，避免覆盖原始研究依据。
