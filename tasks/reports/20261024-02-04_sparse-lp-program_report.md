# RR04同源码与原工件窄续接记录

当前状态（2026-10-25）：8安装和质量通过；warm4原数值/性能80/80独立GO，连续宿主监督失败，完整受控轮HOLD；4/4已用满。
[RR04合同](../codex/20261024-02-04_sparse-lp-program.md)；[唯一当前总报告](20261024-02-02_sparse-lp-program_report.md)。

用户直接回复call_b401b2090a634e03b64bcdcebf18fc2f：“授权该窄续接包（推荐）”。
仅正式warm3→4及原工件SHA不变的一次8新环境矩阵；前3轮及首次溯源失败保留。
原生产source889d191b05736d36de4cd935aecf15e77900d6e7c0f2c5bb8d6bef5914439669、输入、阈值、60秒/1GiB、全部预算保持。
先完成工具一次性保护独立复核和原最后一次完整质量，再用原工件安装；新宿主预检通过后仅运行固定round4。
同一Goal及原账本；local-commit，无push/发布。实际收据和终局随后在此登记，不提前声明GO。

工具源码经独立只读复核GO，15条命令3.5817468秒，0求解/测试/安装/写入。
真实回传reviews/rr04_guard_review_raw.md，结构化收据reviews/rr04_guard_source_go.json。
完整质量第3/3次56.2786357秒，6607测试、结构及全仓Ruff均成功，代码提交fa0ee44。
质量scope在启动前固定；该次之后不改源码、测试、脚本或固定输入。

原工件复验220.3045731秒，八个组合均新环境首轮通过，无重试、无重建。
新summary为delivery/7909ec92-6b7c-46f3-8d12-33e5c74d1f10/summary.json；
reused_from绑定首次summary及唯一人类权限，wheel/sdist保持合同中原SHA。
原检查器核验真实direct_url archive SHA、site-packages来源、dense缺SciPy/sparse锁定SciPy、
四会话修改、JSON/MPS CLI、研究例和F1–F4；外部优化器调用为0。
随后quality/delivery汇总检查通过，0.9789662秒，reviews/rr04_quality_delivery_readiness.json。

新预检分别20.4283652/20.4177340秒，均quiet=false且0solver，原diagnostic达到20/20。
第一窗两XeLaTeX合计约0.713核，第二窗Python约0.981核；这仅是当窗观测，不能证明warm3超时原因。
busy记录分别位于host/baseline_rr04_6f12fe70-aa62-4e5b-8526-b3882e7c9c47和
host/baseline_rr04_1561fed0-d91c-4eb5-bd90-e595e7a2439b。未终止其他进程，未消费warm4。
用户随后批准[RR05宿主预检包](../codex/20261024-02-05_sparse-lp-program.md)，仅≤3个额外零求解窗口单列记账。

RR05第2窗quiet通过后，唯一warm4执行436.0637343秒：80/80、1600修改/80初始正确，
五重复中位3.503361倍、8/8不回退，独立重算GO；summary SHA67075757acf4802a8ad040deeffa82d2f3ee80c91c9d60bf685e39825c452088。
但监督sample_count0、ctypes共享函数argtypes被资源guard覆盖，整体CLI退出1；原warm返回0。
监督SHAa773fb43a27c9ea3a84705b0fe5a301ba3b7b741c4ad56509bc61205edf2cf32，缺失日志无法补写。
原始结果与失败均保留，补丁在隔离副本真实红/绿回归，未应用跟踪代码；无第5轮权限。
当前整体仍HOLD，进一步收口所需的具体补丁及额度见RR02总报告第17节。
