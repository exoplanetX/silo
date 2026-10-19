# L0007解答与核对依据

题意见 [练习](exercises.md)，后端完整程序见 [正文第6节](README.md#6-核验与复现)。

## L0007-E01

旧非基与新列均设0，增列模型在(x,0)处的左端等于A_Ox=b；x_B与B都未改变，故仍可行。
新列可能令rc_new=c_new-a_newᵀpi_old<0，破坏旧MIN对偶可行性；旧原点与原始可行基
保持，必须重算当前乘数/约化成本并继续Phase II。新可行域包含旧可行域，故MIN最优
不增。严格下降需要沿改善方向走正步长；退化枢轴的步长可为0，目标便可暂时保持。

## L0007-E02

新基应为(0,2)，非基为(1)，基槽语义顺序仍(original,x)、(slack,cap)。若沿用(0,1)，
会错误把q设为基本变量。原变量的键按original角色和原名，结构列按slack/surplus角色
与source_constraint；名称貌似结构列的原变量具有不同角色键。

快照保存完整有序原始模型旧数据、列语义清单和基槽键。旧primal/dual/rc数组不保存
或复用；新模型重新解基、重新计算乘数。constructor冻结内容不替代每轮元数据、基
和原始点验证；一个无内容的hash/eligible标志不能给出这些依据。

## L0007-E03

完整两行为x+q=1、x=1，因此x=1、q=0、目标2。只保留a则q=1、x=0、目标0。
矩阵[[1,1],[1,0]]行列式-1、秩2；初始矩阵[[1],[1]]只有秩1。初始列投影的重复
没有覆盖新增列。故初轮可发布核验通过的最优2，但快照不可用；加q必须完整cold。
本轮已有全行非人工基且资格通过后，下一轮加r可warm。取r=1给最优-1，目标2→2→-1。
反转行序或让q仅进入b，结论同样成立；对应四条自然历史在RMP单元测试中覆盖。

## L0007-E04

旧MIN乘数(2,0)，q成本0、系数(1,1)，故rc_q=-2。B为单位阵，B⁻¹Aq=(1,1)，
旧基本值(x,slack_cap)=(1,0)，比率为(1,0)，slack_cap离基，步长0。实际进入q但
q仍为0，目标保持2。加q后可用pi=(2,-2)，LE行cap乘数非正；x与q的rc均0。
新增r系数(1,0)、成本-1，rc_r=-3；cap仍强制q=0，conv可由r=1满足，最优-1。
正文程序检查warm枢轴数，单元观察实际ratio=0与映射基，不能只把相同目标叫退化。

## L0007-E05

成功add保留旧快照供下一轮核验，失败add保留模型/缓存。普通solve始终cold并清空
可选缓存。新入口的非Revised参数在任何修改前TypeError。warm失败/cold成功后，
attempted=True、used_warm=False、cold_count=1，缓存依据cold最终合格基重建。
cold非最优或最终数学核验失败清空缓存；下一次只有fresh cold可重建资格，不能偷偷
拿更早快照。旧删行或其他资格不足保留有效OPTIMAL但不缓存；LP通过而RMP最终
核验失败则发布空字段NUMERICAL_ISSUE并清空缓存。

warm_iterations只记warm Phase II，cold_iterations记cold既有Phase I/II总和；
limit按各run使用，不能将回退开销藏在一次limit内。0次枢轴也可是真warm，但必须
观察确实进入Phase II。warm已核验无界仍cold一次，最终cold的无界门控独立执行。

## L0007-E06

当前概率单纯形再切一个均值区间。顶点要么只有一个正权重，要么均值约束在lo或hi
取等号且最多两个正权重；若三个以上为正，可在保持和与均值的零空间中双向移动，
故该点不是顶点。两个不同r值i,j的端点权重为λ_i=(endpoint-r_j)/(r_i-r_j)，
λ_j=1-λ_i，过滤非负/区间可行后比较线性目标即可。本固定族r互异且有限，成立。

以下标准库程序核对成本(2,0,-1)对应(p1,p0,p2)、c0=7、区间[1/2,3/2]的
两种加列顺序，按每个原项Fraction计算：

```python
from fractions import Fraction as F
from itertools import combinations

r = {'p1': F(1), 'p0': F(0), 'p2': F(2)}
c = {'p1': F(2), 'p0': F(0), 'p2': F(-1)}
def optimum(names):
    points = [{n: F(n == chosen) for n in names} for chosen in names]
    for i, j in combinations(names, 2):
        for bound in (F(1, 2), F(3, 2)):
            weight = (bound-r[j])/(r[i]-r[j])
            points.append({n: weight if n == i else 1-weight if n == j else F(0)
                           for n in names})
    valid = [x for x in points if min(x.values()) >= 0 and
             F(1, 2) <= sum(r[n]*x[n] for n in names) <= F(3, 2)]
    return min(F(7)+sum(c[n]*x[n] for n in names) for x in valid)
assert [optimum(n) for n in [('p1',), ('p1','p0'), ('p1','p0','p2')]] == [9, 8, F(25,4)]
assert [optimum(n) for n in [('p1',), ('p1','p2'), ('p1','p2','p0')]] == [9, F(15,2), F(25,4)]
print('L0007 analytic vertices passed')
```

两区间×三成本组×两加列序×六行序×两符号表示=144历史；每条四轮得到576 opt-in。
首轮144cold，后续432warm；两个独立cold owner分别用Revised/Tableau跑四轮，共1152。
必须另外观察cold入口、Phase I/II、实际传入问题/基和新增列非基身份；答案和flag
无法证明内部没有冷求解。0枢轴复用也需要实际Phase II调用证据。

后续效率比较应固定求解域/初始列/加入顺序、检查同一数学结果，分别记录cold、warm、
失败回退、预处理/构造/线性系统/枢轴/定价成本与时间。当前完整重建可能占较大比例，
省去Phase I的机制证据不能直接推出运行时间提升、高维数值稳健性或研究创新。

## 实际核对范围

2026-10-20按90b377f723f047f723949aaace87f1385f42bb74核对：正文11次公开RMP调用、
这里的解析程序、六题计算/推导与新225项版本化测试通过。完整质量为3669项与Ruff通过，
实际检查见[执行报告](../../../tasks/reports/20261020-02-01_rmp-reoptimization_report.md)。
E06效率实验仍是建议，没有作为本步运行时间提升证据。
