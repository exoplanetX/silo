# SILO-PROTOTYPE-20261023：原始模型、变换与结果规格

2026-10-23，M1编码前冻结。总计划和验收门槛保持，历史MAX标准形接口通过显式换算兼容。

## 原始对象与KKT

原始Model保留变量名、行名及目标min/max。Constraint兼容旧sense/rhs，新增可选
lower_bound/upper_bound；任一显式侧出现时按该区间解释，缺失侧为无界。
只读row_bounds给出两侧；旧sense/rhs行分别映射LE/GE/EQ。JSON行可用lower/upper，
null表示缺失侧；变量lower=null表示负无穷，upper=null表示正无穷。系数及c0必须有限。

令s=+1(min)、−1(max)，按最小化s(c0+cᵀx)定义非负Y_lower/Y_upper、Z_lower/Z_upper。
stationarity为s*c−AᵀY_lower+AᵀY_upper−Z_lower+Z_upper=0。
互补分别为Y_lower*(Ax−row_lower)、Y_upper*(row_upper−Ax)、
Z_lower*(x−lower)、Z_upper*(upper−x)=0。缺失一侧乘子严格为0；等式的两侧差可非唯一。
对偶目标为s*c0+row_lowerᵀY_lower−row_upperᵀY_upper
+lowerᵀZ_lower−upperᵀZ_upper，只对存在的侧求和，等于s*原始目标。
返回side multipliers遵循该最小化约定，旧signed dual值与之显式区分。
统一公共signed dual为d=s*(Y_lower−Y_upper)，reduced cost为r=c−Aᵀd；
因此s*r−Z_lower+Z_upper=0。返回原始方向dual objective为s乘上述对偶目标。

## 可逆账本

canonical目标统一为MAX −s*(c0+cᵀx)，变量非负；x=o+Tz。
有限下界x=l+z；仅上界x=u−z；自由变量x=z_plus−z_minus；固定变量x=l。
整数位移/反射只取整数，整数下/上界分别ceil/floor，无整数点是域不可行。
区间行保留原始身份，拆为各存在侧，原始活动减A*o；有限变量上界补行。
命名由账本生成并防冲突，不靠名称后缀猜恢复。

原始primal=o+Tz，射线=T*d（不加o），原始目标直接重算。
canonical MAX行对偶lambda的LE>=0、GE<=0；原始上侧Y=lambda，下侧Y=−lambda，
等式按lambda正负分解两侧。有限下界位移的Z_lower=−canonical reduced_cost，
补上界行的Z_upper=该行lambda；仅上界反射Z_upper=−reduced_cost。
自由变量Z两侧为0；固定变量以h=s*c+Aᵀlambda选择Z_lower=max(h,0)、Z_upper=max(−h,0)。
可验证KKT而不指定退化对偶唯一值。MILP最优不发布“LP对偶最优”声明。

presolve仅有限pass活动界传播，记录每次收紧的来源行侧及当时其他变量界版本。
连续界推导为原始行不等式正倍数加其他变量界正倍数；恢复时逆序将新界乘子
推回来源行/旧界。整数取整只用于整数域/节点松弛，不能冒充原始连续LP的等价变换。
删冗余行只在恢复身份明确时采用，未推导出恢复关系时保留行。
原始固定变量与传播后固定变量必须区分。例如min x，0<=x<=2，行x=1，
传播后虽x固定，回解须有行dual=1、rc=0及原始两界乘子0；不得将派生固定
当作原始固定并赋原始下界乘子1。新界乘子沿来源链逆推，恢复后再次核验互补。

缩放使用正对角R/C，A_scaled=R*A*C，b_scaled=R*b、c_scaled=C*c，
z=C*z_scaled、lambda=R*lambda_scaled、rc=rc_scaled/C。
整数原始坐标不改变整数格；仅连续LP松弛的内部坐标可缩放，MIP分支/整数核验仍在原空间。

## 原始空间核验与证据

默认primal/dual/integrality=1e-7，pivot=1e-10。行残差允许
tol*(1+abs(bound)+sum(abs(a_j*x_j)))；stationarity采用对应绝对贡献尺度，
互补与目标也按绝对贡献尺度。容差在本规格冻结，不按实例放宽。
原始点、乘子及目标重构失败返回numerical_failure。
不可行需验证Farkas非负侧乘子、零法向组合及严格正矛盾常数；未取得则数值失败。
无界需原始可行点、满足所有衰退侧的非零射线及s*cᵀd<0；整数无界还需整数兼容点/射线。
尽可能用有理重构并精确检查证明对象；不能核实的确定结论不发布。
顶点枚举仅适用于其有极点的声明域。自由变量x=y、目标x−y的最优直线没有
顶点，固定验收使用精确可行点和KKT对偶真值；顶点集空不能推出不可行。

## 公共API与限额

silo.solve(model, options=None)按变量域分派。SolveOptions冻结时间/节点/LP轮数/gap、
presolve/scaling/cuts/heuristic、LP方法和节点策略；非法选项拒绝。
SolveResult区分status、termination_reason、has_primal_solution、primal/dual bound、
absolute/relative gap、iterations/nodes/elapsed、KKT和证据、结构化diagnostics。
有限gap分母max(1,abs(primal_bound),abs(dual_bound))；无incumbent或无穷dual bound时gap=None。
限额可保留经原始核验的incumbent；未知或LP无界节点保守参与前沿，不能产生虚假有限gap。
结果JSON schema_version=2，新统一CLI使用该结构；旧命令/旧solution writer保留兼容输出。

free-MPS支持NAME/OBJSENSE/ROWS/COLUMNS/RHS/RANGES/BOUNDS/ENDATA及INTORG/INTEND；
bound类型LO/UP/FX/FR/MI/PL/BV/LI/UI。无objective RHS表示c0=0，objective RHS取−c0。
多个RHS/RANGE/BOUND集合、未知扩展、fixed-column语法、SOS/二次段明确拒绝，不能悄然忽略。
输入书写顺序保留确定性；RANGES按E/L/G的标准侧方向还原到区间行。
