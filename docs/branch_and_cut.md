# 一般MILP、前沿与GMI

用户入口`solve`按变量域分派，整数界先ceil/floor，再按原始行做有理数活动传播和向外浮点化。
所有节点LP共用一般模型/QR/缩放/原始核验链。原来的BranchAndBoundSolver继续提供历史有限域参考。

搜索用F=s*(c0+c'x)最小化坐标。queued节点存有效继承下界，active节点在限额、数值或gap出口
重新纳入前沿；全部合法children登记后才关闭父节点。新有限LP dual bound与继承界取max。
B=min(incumbent,所有开放有效界)，原方向primal=s*U、dual=s*B。
有incumbent且B有限时，absolute=U−B，relative=absolute/max(1,abs(P),abs(D))。
未知/无界未解决节点按−inf计，gap=None。JSON含positive_infinity/negative_infinity/finite/missing
bound kind。time/node/LP iteration/gap是不同termination_reason，gap出口status=limit。

默认确定性best-bound，可选DFS；分支使用积累pseudocost，缺乏记录时按分数性与变量序回退。
有限rounding启发式只在根或每16节点尝试至多两点；整数先实际取整，再核验原始行/界，
拒绝候选不能关闭节点。近整数但取整不可行时继续合法floor/ceil分支；无法推进则保留数值失败。
局部节点LP基复用按完整语义身份核验，失败至多一次cold；结构化统计记录实际调用。

LP无界三态：严格原始整数anchor+整数兼容改善ray证明整数无界；分数anchor可合法分支；
其余保留unresolved/limit。继承有限界与子LP无界冲突时保留conflict/unresolved，dual无穷、gap缺失。
公开无界点与目标来自同一核验witness；若有理点无法无损表示为float，保留证明且不公布舍入点。

GMI仅从核验过的Phase-II非人工基、明确整数basic坐标生成。原始方程和有效节点箱重建未缩放
Fraction基，故不对缩放的整数列直接取fraction。xB=bbar−Σa_j*z_j，z>=0，f0=frac(bbar)：
整数非基列alpha_j=f_j（f_j<=f0）或f0*(1−f_j)/(1−f0)；连续列alpha_j=a_j（a_j>=0）
或−f0*a_j/(1−f0)。GE割Σalpha*z>=f0；负a用floor，连续列不取fraction。
严格split/modular推导见[L0013](../learning/lessons/L0013-general-milp/README.md)。

变量位移/反射和slack通过显式AffineCoordinate回原始x；slack仅在其原始表达系数、常数和
相关变量确证整数时标整数。自由拆分无法唯一投影的非零项拒绝。接近整数f0、爆炸系数、
无可靠exact基或超budget均跳过割，不改变节点整数可行域。basis上限80，精确Farkas重建上限160，
proof_operation_limit默认2000000，含构造/消元的deadline及4096bit系数门；拒绝会留下正常搜索或
保守限额，不能用跳过证明宣称不可行。

Exact割转float时设delta=a_float−a_exact，取节点箱上min(delta'x)，令b_float<=b_exact+min(delta'x)，
所以新割向外放松。需要的误差侧无界即拒绝。记录非基keys/maps、整数标签、基本列身份、有效箱、
exact系数、float误差及RHS限制。所有GMI显式NODE_LOCAL；只沿后代继承，单独复制tuple防止兄弟污染。
每节点默认最多2轮、每轮3割，默认只到depth2；验证、规范去重、加行和重优化真正执行。

验证入口：`tests/unit/test_prototype_mip.py`的96有限枚举MILP、原始mixed cut、局部祖先、
三态无界、各限额；`test_prototype_proof_boundaries.py`的整数转换、公开点一致性、箱浮点方向与
变换/标签/预算。固定规模仅在M5，有限测试不代表工业性能、任意条件数或新颖算法结论。
