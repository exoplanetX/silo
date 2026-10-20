# L0010 解答

**L0010-E01。** 初始2lambda_c=1/2，故a=3/4、c=1/4，P=9/2。
两条基列给pi_conv=4、pi_R=1，b的rc=1−4−1=−4。
增b后a=b=1/2、c=0，P=5/2；pi_conv=4、pi_R=−3，rho=0。
d,z资源2+1=3>2，虽其R特征恰为1/2仍不属于合法列域。
正文程序、原生示例及三模式手算unit实际核对这些值。

**L0010-E02。** 令delta=min(0,rho)，将自由conv乘数加delta。
每条完整资源列的conv系数1，故rc'_p=rc_p−delta>=0；其他行符号不变。
conv RHS1使对偶目标增加delta，弱对偶给L=D+delta<=z*。
一般覆盖模型没有统一系数及全局总权重1，这一单乘数平移不具备同样效果。
这是精确条件下的数学论证；浮点实现发布带局限的数值估计。

**L0010-E03。** 源4条弧检查后有(s,0)、(u,0)、(u,1)、(u,2)共4状态；
从(u,0)检查z后发现(t,1)，计数5状态/5转移。下一必要检查前触发TRANSITION_LIMIT，
CG返回PRICING_FAILURE。定价弧/行为空，usage/is_improving等为None；CG本轮所有界为空，
接受列为空，但当前有效RMP与其registry可保留。实际cap unit核对5/5及对应诊断。

**L0010-E04。** b,z资源(2,2)在第二维超限；d,z第一维超限。
a,z与c,z均(1,1)，合法组合固定a=3/4、c=1/4，目标仍9/2。
`test_zero_resources_agree_with_ordinary_reference_and_double_resources_bind`实际核对，
并检查汇候选资源(1,1)。资源约束删掉的列无法通过耦合行组合恢复合法性。

**L0010-E05。** 2^60附近浮点间隔大于本例局部差距，P和L都可能舍入为公共常数，
raw gap=0。原始贡献层消去c0后，初轮g=9/2−9/2−(−4)=4仍保留。
两种大正负常数回归实际通过。g<0只在eta=32ulp(绝对局部贡献和)<=tolerance且−g<=eta时接受；
否则返回数值失败。synthetic signed-gap测试核对近邻负差被接受及超局部余量被拒绝，
大c0不能放宽规则。该余量不等于严格LP误差界。

**L0010-E06。** 默认每轮一次公开RMP.solve；True每轮一次solve_reoptimized，
保存真实outcome和其最终MIN result。unit观察Revised实际Phase II入口、公开次数、
fresh owner和warm失败后的单次内部cold回退，而非仅看布尔值或运行时间。
主族每模式72调用/116轮；opt-in有72内部cold、44warm、无fallback。
每轮资源定价重新计算全部声明资源状态；RMP复用没有实现增量定价。

**L0010-E07。** 第二轮master失败：顶层仍配第一轮已解的2列和旧master，
失败history保留尝试的3列、失败outcome，无price且界为空。
若第二轮主目标已核验有效而pricing失败，顶层可配当前3列/当前master；
同轮资源诊断保留，界仍空。warm+内部cold均失败及later-price-failure unit分别实际核对。

**L0010-E08。** 原4在非负整数可加资源DAG、连续lambda及单conv参考模型中得到工程补齐；
原5仍需真实主问题/状态/对偶/强基线联合证据，原6需实际跨对偶机制，原7需完整成本评价。
有限正确性测试不能证明效率、原创性或应用成立。应用准备不足导致HOLD只说明
尚不具备判定所需的可核对证据，不能据此反驳应用结构假设。此题为概念辨析，无新实验。
