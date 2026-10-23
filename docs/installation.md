# 安装与发行物验证

本页的 M5 检查脚本和 CI 配置已准备。实际构建、安装、对照测试与平台资格以总任务报告的
运行记录为准；配置文件存在不构成对应平台已经通过的证据。

## 运行环境

包声明 Python 3.10 及以上，原生运行时依赖 NumPy。SciPy 只用于可选外部求解对照。
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

## CI 状态

[quality.yml](../.github/workflows/quality.yml) 配置四个 Windows/Linux × Python 3.10/3.12
组合，执行源代码质量检查、冻结证据静态核验、构建及两个工件的独立安装检查。
流水线不包含 PyPI、GitHub Release、标签或发行物发布步骤。
远端 runner 尚未执行时，跨平台状态保持 pending；本地结果写入总任务报告。
