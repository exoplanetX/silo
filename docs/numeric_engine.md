# 数值内核与重优化

统一LP走`lp/general.py`，默认dense引擎的MAX非负模型由`lp/kernel.py`的Phase I、人工列清理、
Phase II求解。Bland进入/离开规则处理退化，预算出口保留确定性原因。表格法和旧Revised
是保留历史域的参考后端。公共用户与一般RMP/MIP松弛共用新的原始核验链。

基求解默认NumPy QR、自有前/回代，不构造逆矩阵。一个basis身份的分解在基本值、对偶、
方向及dual pivot中复用；残差或奇异异常从实际基矩阵重分解一次，失败明确返回数值结果，
warm可再执行至多一次cold。factorizations/refactorizations/factor_reuses和primal/dual_pivots
均由实际调用计数。所有coupled行消去后，区间积可解析求解，仍经过原始KKT检查。

`from silo.lp.session import LPSession`创建拥有模型副本的会话，`solve()`复用上次语义基；
change_rhs/change_row_bounds/change_bounds、append_row/append_column验证后原子替换模型。
公共model属性返回副本。也可直接`solve(new_model, options, basis=previous.basis)`。
快照version2包含行/列语义键、系数及基本列身份。新增行可插在补界行之前；按身份核验旧
矩阵子块，新增slack扩基。模型/缩放改变旧系数、删行/列或坏基均有明确cold理由。
auto优先使用dual可行基，否则使用primal可行基；新增改善列通常进入primal。
显式primal不接受原始不可行基。RHS在原始/对偶都可行时dual可以零枢轴终止，诊断据实给0。
change_rhs对显式区间行拒绝并提示change_row_bounds；后者双None明确移除两侧。

缩放是正对角R/C：A_s=RAC,b_s=Rb,c_s=Cc，z=Cz_s，lambda=Rlambda_s，rc=rc_s/C。
MIP分支和整数核验始终在原始格。输入字典保存稀疏结构不表示内部稀疏求解。
max_dense_cells默认2000000，初始化前估算(m+n)*(3n+2m+1)个单元；此外仍有QR及数组副本，
这是保守规模门而非精确峰值RAM承诺。超限resource_limit；已分配数组异常不会转成最优结论。

primal/dual/integrality容差默认各1e-7，pivot=1e-10；互补和目标差默认各1e-7，分别
由complementarity_tolerance/objective_tolerance设置。原始可行只用primal，整数近似只用
integrality；对偶符号/驻点用dual。互补和目标采用各自容差与绝对贡献尺度，不能用较宽dual
去放宽primal。整数候选先还原为实际整数再核验原始行，拒绝不能作为节点不可行证明。

原始Farkas和点/射线将输入浮点数视为其实际二进制值，先转换再相乘/相加，沿用历史严格
核验方向。小分母有理重构只是候选；原始精确等式/不等式检查失败时不会发布不可行/无界。
LP最优KKT按冻结的浮点残差规则核验。超出float64精确整数表示的整数系数给input_conversion
数值结果，不默默取整。数值证据的支持范围与任意条件数上的稳定保证分别评价。

MILP两处目标剪枝采用归一化`node.bound >= incumbent`；primal容差不参与该比较。
显式gap参数的提前停止继续保留前沿，LP界的数值KKT支持域保持上述限制。
有限池一般CG终止另设精确门：原始二进制数据上的全池对偶可行、原始可行点及P=D。
raw float、小分母重构和现有basis精确重建都只是候选。核验共享proof操作、4096bit、
时间、LP枢轴及20轮预算；失败保留incumbent，不发布有限全池dual bound。
不可用float精确表示的有理目标以witness保留，primal bound向+inf、dual bound向−inf包络。

## 显式稀疏引擎与持久会话

`SolveOptions(lp_engine="sparse")`和`optimize --lp-engine sparse`选择CSC/LU路径。
基础导入与默认dense求解不加载SciPy；显式sparse需要Python>=3.11及`sparse` extra中的
SciPy1.16.3。SciPy只提供稀疏矩阵和LU，Phase I/II、primal/dual、定价、换基和退出由SILO实现。
原始规范见[稀疏矩阵契约](sparse_matrix_contract.md)及[基与会话契约](sparse_basis_session_contract.md)。

`max_sparse_nnz=1000000`、`max_factor_nnz=5000000`控制稀疏输入及因子fill；
`max_factor_updates=20`限制真实eta链。解B与B转置分别按正确顺序应用更新，
每次核对当前实际B残差。恢复重构必须废弃旧代次的未提交选择；新因子及完整状态先私有核验再发布。
近相关清理只在原始binary Fraction等式核验通过时删行；固定工作区和证明预算超限则保守失败。
证明的候选分母上限及流式核验、minor的条件性和暂存删行见基契约的精确依赖段及L0015。

version3被动快照保存语义基与不可变CSC数据，私有LU/eta由单一`LPSession`拥有。
相容RHS、bounds及增列可跨调用沿用实际数值因子；增行改变维数，保留语义warm并重建因子。
原始矩阵系数、行侧、变量坐标、尺度及私有策略身份共同限制复用。
默认dense、旧version2导入、分支和CG共用原空间验证；数值失败不能推出不可行或最优。
伴学推导、反例和练习见[L0012](../learning/lessons/L0012-reoptimizable-lp/README.md)及
[L0015](../learning/lessons/L0015-sparse-basis-updates/README.md)。
