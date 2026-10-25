# 安装与发行物验证

当前本地候选为0.3.0a1，目标为Windows Python3.11/3.13 × dense/sparse × wheel/sdist
八个独立安装组合。实际完成状态、工件身份和失败重试以
[当前总报告](../tasks/reports/20261024-02-02_sparse-lp-program_report.md)及其原始收据为准。
下文0.2.0a1四组合属于保留的历史证据；远端CI保持pending。

## 运行环境

包声明 Python 3.10 及以上，默认dense运行时依赖NumPy。
显式sparse引擎要求Python>=3.11并安装`sparse` extra，固定SciPy1.16.3提供CSC和稀疏LU；
原生算法不调用SciPy优化器。外部HiGHS比较由另一个可选extra启用。
本轮本地验收目标为 Windows Python 3.11、3.13；CI 计划覆盖 Windows/Linux ×
Python 3.10、3.12。尚未运行的组合保持 pending。

在独立虚拟环境中安装一个明确的本地 wheel：

```text
python -m venv /absolute/path/to/fresh-environment
/absolute/path/to/fresh-environment/python -m pip install /absolute/path/to/silo_solver-VERSION-py3-none-any.whl
```

上例的解释器路径需按平台选择：Windows 为 `Scripts/python.exe`，Linux 为 `bin/python`。
用实际工件名替换 `VERSION`。从源码开发时可安装 `.[dev]`；发行物验证使用普通安装，
避免 editable 安装或源码路径注入掩盖包内容缺失。

## API 与文件入口

```python
from silo import solve
from silo.io import model_from_dict

model = model_from_dict({
    "sense": "minimize",
    "variables": [{"name": "x", "lower": None, "upper": 4}],
    "constraints": [{"name": "floor", "coefficients": {"x": 1}, "lower": -2}],
    "objective": {"coefficients": {"x": 1}, "constant": 3},
})
result = solve(model)
assert result.status == "optimal"
assert result.objective_value == 1
```

统一 CLI 使用 `python -m silo optimize model.json` 或
`python -m silo optimize model.mps`，成功输出 `schema_version=2` 的结构化结果。
模型格式和边界含义见 [JSON/free-MPS 格式](mps_format.md)。

## 可选 SciPy/HiGHS 对照

在另一个对照环境安装 `silo-solver[optional-backends]`，或先安装本地工件再安装
`scipy>=1.11`。原生求解环境可以完全不安装 SciPy。

```python
from silo import solve
from silo.interfaces.highs import compare_with_highs, highs_availability, solve_with_highs

print(highs_availability())
external = solve_with_highs(model)
comparison = compare_with_highs(model, solve(model))
```

`solve_with_highs` 通过 `linprog(method="highs")` 或 `milp` 执行真实外部求解，
映射目标 min/max、常数、行区间、连续/整数/二元域以及各类变量界。
缺少可选依赖时返回 `available=False`、`status="unavailable"` 和
`termination_reason="optional_dependency_missing"`。
结果保留原始 SciPy 状态、消息、版本、实际转发选项和未转发的原生控制参数。
返回点在原模型中另行核验；该核验只检查原始可行性和目标回算。

SciPy 与其 HiGHS 后端构成一条 `scipy_highs` 外部算法证据。
`compare_with_highs` 接收已经算出的原生结果，其输出属于补充对照。
MILP 的 `backend_relative_gap` 保留外部口径；`relative_gap` 使用 SILO 的
`abs(P-D)/max(1,abs(P),abs(D))`，目标常数及最大化方向计入原始 bound。
无可行点或无有限 dual bound 时不生成有限 gap。
接口映射参考 [SciPy linprog](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)
与 [SciPy milp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)。

## 0.3.0a1的稀疏选择与八组合隔离检查

明确安装当前本地工件和NumPy；sparse环境额外安装SciPy1.16.3，然后使用
`SolveOptions(lp_engine="sparse")`或`python -m silo optimize model.json --lp-engine sparse`。
dense环境中SciPy缺席；sparse环境中基础`import silo`仍延迟加载SciPy。
缺少所需稀疏依赖时按公开结果报告不可用原因，不自动调用外部优化器。

本程序通过`python scripts/sparse_program.py install-checks --candidate 0.3.0a1`，
从干净已提交Git归档构建两份工件，逐项比较全部Python模块、版本和依赖元数据。
构建目录与八个新环境位于源码导入路径以外，检查一律采用`python -I`及普通安装。
本次固定NumPy2.3.5；sparse固定SciPy1.16.3，dense要求SciPy不存在。
轮次、构建、下载、环境创建、每次失败和检查统一进入原SP4账本。
只允许同SHA工件的一次纯环境失败重试，失败环境及日志保留。

`scripts/sparse_program/check_installed.py`核对distribution/runtime、实际解释器、
`direct_url.json`工件SHA及全部已载入模块的site-packages来源，并检查四类会话修改、
LP/MILP的JSON/MPS CLI、公开研究例、全池精确终止及F1–F4回归。
外部优化器入口受到禁止调用检查。八组合分别给出结果，有限本地验证不替代远端CI。

RR04获批溯源复验使用`--reuse-delivery`明确指定首次构建目录，保留两份工件原SHA。
uv只创建环境并安装锁定运行依赖；环境内`python -I -m ensurepip --upgrade`后，
使用普通`python -I -m pip install --no-deps --no-cache-dir`安装原工件，
使`direct_url.json`记录真实archive SHA。已有工件时省略复用参数会在构建前拒绝。
原溯源检查器及失败记录保持；一次性复验权限不授权重复构建或反复安装。

## M5 的独立安装检查

M5 统一执行时先使用 `python -m build` 产生 wheel 和 sdist，并记录工件 SHA-256。
每个工件和 Python 版本各使用一个新的虚拟环境；wheel 与 sdist 不能在同一环境覆盖验证。
检查环境仅安装工件及其 NumPy 运行依赖，SciPy 必须缺席。

把 `scripts/prototype/check_installed.py` 复制到源码树以外的临时目录，在该目录运行：

```text
/absolute/path/to/fresh-environment/python -I /outside/source/check_installed.py --source-root /absolute/path/to/silo-solver --artifact /absolute/path/to/distribution --report /outside/source/installed-report.json
```

脚本要求当前目录处于源码树外，并核对包及已载入子模块来自该环境的 site-packages，
同时核对 distribution/runtime 版本、隔离模式、实际 Python/平台和工件 hash。
脚本依次执行一般 LP min/max 与 MILP API、LP/MILP 的 JSON/MPS CLI，以及包内
`silo.decomposition.general_master.covering_example()` 和
`silo.mip.research_example.run_example()`。检查包含原始可行性、整数性、目标、
最优 primal/dual bound 和 gap；它不读取仓库测试夹具或从 `src/` 导入。

脚本自身不构建或安装软件。输出 JSON 中只有实际执行成功才记为 `passed`；
失败返回非零退出码。发行物通过只能证明该次解释器、平台和工件组合。

## 本地实际安装证据（2026-10-24）

版本 `0.2.0a1` 已在 Windows 的四个独立源码树外环境中通过普通安装检查。
四个成功环境均关闭系统 site-packages，采用 `python -I`，运行时仅包含 NumPy、SILO
和环境自带的 pip/setuptools，未安装或导入 SciPy。每个环境实际执行 3 项一般模型 API、
4 项 LP/MILP JSON/MPS CLI 和两个包内研究例；目标分别为 LP `18/-18`、MILP `-1.75`、
覆盖 CG `2.5` 与 MIP 策略例 `-8.5`。所有包导入均来自对应环境的 site-packages，
安装记录 `direct_url.json` 中的 archive SHA-256 均与被检查工件一致。

| Python | NumPy | 工件 | 结果 | 检查进程墙钟秒 |
|---|---|---|---|---|
| 3.11.15 | 2.4.6 | wheel | passed | 2.230 |
| 3.11.15 | 2.4.6 | sdist | passed | 2.260 |
| 3.13.9 | 2.5.4 | wheel | passed | 2.010 |
| 3.13.9 | 2.5.4 | sdist | passed（第二次全新环境安装） | 2.100 |

构建使用已提交源的 `git archive` 副本。打包、README 和完整公开源码身份为
`d4c852f7112c6abfc2d799c42c924a6aa4cef188`，原生算法提交锚点为
`cc11a929189ea7cf6e8edde952640edc0f7f0090`。两者的源码差异仅是
`research_example.py` 的轨迹无穷值 JSON 序列化；算法和版本元数据差异检查通过。
归档源中 `src/**/*.py` 的路径与原始字节组合 SHA-256 为
`6d1c166b603fad6c1d459921ce9f420974f8f86a347a85e9a57e482ad76c846b`，
README SHA-256 为 `c0293ff894169c1b84fee46a12e1e117021a73d7bcee809595eba271bbbdaf8e`。

两份工件保存在 `dist/prototype/m5-install-20261024-01/`，其 SHA-256 为：

- `silo_solver-0.2.0a1-py3-none-any.whl`：
  `f6d63c7f10e11356cbac05fa7e454978272a2572e0d9d34a2061af3cfae4609b`。
- `silo_solver-0.2.0a1.tar.gz`：
  `ba237ec5fcc4e9cae5beb94e8768bd9e16da5810332cc882f82d0c5d5a23e4f8`。

Python 3.13 的第一次 sdist 安装在 NumPy 下载阶段遇到超时、TLS EOF 和部分下载文件
占用错误，耗时 216.418840 秒，尚未运行检查脚本。该失败环境、工件和完整日志均保留。
随后以同一份 sdist 在第五个全新环境关闭下载断点续传重试，24.044241 秒内完成安装和
检查；求解器、检查脚本和工件均未修改。构建、下载、环境创建、全部安装尝试及检查累计
347.144665 秒，其中两份工件的实际构建为 16.159296 秒。

完整命令、各步退出码、耗时、Python/NumPy 版本、工件与报告哈希及四份检查报告见
[安装汇总](../outputs/prototype/install/m5-install-20261024-01/final-summary.json)、
[首轮命令记录](../outputs/prototype/install/m5-install-20261024-01/commands.json) 和
[重试命令记录](../outputs/prototype/install/m5-install-20261024-01/py313-sdist-retry-01/commands.json)。
原始失败日志为
[py313-sdist-02-install.log](../outputs/prototype/install/m5-install-20261024-01/py313-sdist-02-install.log)。
这些工件与本地日志位于忽略目录，未作为二进制提交。

## CI 状态

[quality.yml](../.github/workflows/quality.yml) 配置四个 Windows/Linux × Python 3.10/3.12
组合，执行源代码质量检查、冻结证据静态核验、构建及两个工件的独立安装检查。
流水线不包含 PyPI、GitHub Release、标签或发行物发布步骤。
远端 runner 尚未执行时，跨平台状态保持 pending；本地结果写入总任务报告。
