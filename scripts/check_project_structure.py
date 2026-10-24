"""Check project navigation; --write-index refreshes only tasks/INDEX.md.

The index records file presence, not task approval or execution success. Historical
exceptions are exact identities; an unexecuted issued task may have no report yet.
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

TASK_NAME = re.compile(r"(\d{8}-\d{2}-\d{2})_([a-z0-9]+(?:-[a-z0-9]+)*)\.md")
DOCS = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "tasks/README.md",
    "tasks/INDEX.md",
    "docs/README.md",
    "docs/development_layout.md",
    "notes/README.md",
    "notes/26_incremental_pricing_research_start.md",
    "notes/27_pricing_operation_alignment_and_structure_class.md",
    "notes/28_pricing_frontier_state_and_repair_baseline.md",
    "notes/29_pricing_application_structure_and_cost_gate.md",
    "notes/30_pricing_locality_conditions_and_nearest_neighbors.md",
    "scripts/research/pricing/README.md",
    ".silo-dos/project_profile.md",
    ".silo-dos/technical_route.md",
    ".silo-dos/decision_log.md",
)
EXTERNAL_SOLVERS = {"scipy", "gurobipy", "cplex", "highspy", "pulp", "ortools", "cvxpy"}


def sparse_numeric_import(node, module):
    """Allow the contracted optional matrix/LU adapter, never SciPy optimizers."""
    if not isinstance(node, ast.ImportFrom) or node.level:
        return False
    layer = module.split(".")[1] if "." in module else ""
    if layer not in ("modeling", "lp"):
        return False
    names = {alias.name for alias in node.names}
    if node.module == "scipy" and module == "silo.modeling.matrix_ops":
        return names == {"sparse"}
    allowed = {
        "scipy.sparse": {"coo_matrix", "csr_matrix", "csc_matrix", "hstack", "vstack", "eye"},
        "scipy.sparse.linalg": {"splu"},
    }
    return bool(names) and names <= allowed.get(node.module, set())


def inventory(root: Path, errors: list[str]) -> tuple[list[Path], list[Path], dict]:
    tasks = sorted((root / "tasks/codex").glob("*.md"))
    reports = sorted((root / "tasks/reports").glob("*.md"))
    exceptions = json.loads((root / "tasks/history_exceptions.json").read_text(encoding="utf-8"))
    groups: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        match = TASK_NAME.fullmatch(task.name)
        if match is None:
            errors.append(f"Malformed task filename: {task.name}")
        else:
            groups[match[1]].append(task.relative_to(root).as_posix())
    collisions = {key: values for key, values in groups.items() if len(values) > 1}
    if collisions != exceptions["collisions"]:
        errors.append("Task ID collisions differ from the exact historical exception groups")
    task_names = {path.name for path in tasks}
    report_names = {path.name for path in reports}
    report_only = set()
    for report in reports:
        contract = report.name.removesuffix("_report.md") + ".md"
        if not report.name.endswith("_report.md") or TASK_NAME.fullmatch(contract) is None:
            errors.append(f"Malformed report filename: {report.name}")
        elif contract not in task_names:
            report_only.add(report.name)
    if report_only != set(exceptions["report_only"]):
        errors.append("Unmatched reports differ from the exact historical exceptions")
    for name in exceptions["missing_report"]:
        if name not in task_names or name.removesuffix(".md") + "_report.md" in report_names:
            errors.append(f"Historical missing-report annotation needs explicit resolution: {name}")
    return tasks, reports, exceptions


def render_index(tasks: list[Path], reports: list[Path], exceptions: dict) -> str:
    report_names = {path.name for path in reports}
    lines = [
        "# SILO 任务与报告索引",
        "",
        "由 `python scripts/check_project_structure.py --write-index` 从项目根目录生成。",
        "规则见 [tasks/README.md](README.md)，当前状态见",
        "[project_profile](../.silo-dos/project_profile.md)。请修改来源文件后重新生成索引。",
        "",
        f"共 {len(tasks)} 份合同、{len(reports)} 份报告。报告存在只表示有记录；",
        "批准范围、执行是否成功及代码基线需要阅读合同、报告与对应 Git 提交。",
        "未出现同名报告的合同可能尚未执行；索引不据此推断完成或失败。",
        "",
        "## 合同与同名报告",
        "",
        "| 任务身份 / 合同 | 报告 | 说明 |",
        "|---|---|---|",
    ]
    for task in reversed(tasks):
        report = task.stem + "_report.md"
        notes = []
        if task.name.split("_", 1)[0] in exceptions["collisions"]:
            notes.append("历史编号碰撞；使用完整路径")
        if task.name in exceptions["missing_report"]:
            notes.append("历史报告缺口；结果未确认")
        record = f"[报告](reports/{report})" if report in report_names else "尚无同名报告"
        lines.append(f"| [{task.stem}](codex/{task.name}) | {record} | {'；'.join(notes)} |")
    lines.extend(["", "## 历史报告例外", ""])
    for name, reason in exceptions["report_only"].items():
        lines.append(f"- [{name}](reports/{name}): {reason}")
    lines.extend(
        [
            "",
            "## 追溯与修订",
            "",
            "同一任务的 RR 修订保留各自合同；历史编号碰撞通过完整路径区分。",
            "精确例外与原因见 [history_exceptions.json](history_exceptions.json)。",
            "该清单只描述已有缺口；新碰撞和新增无合同报告会使检查失败。",
            "",
            "查看报告所在提交：`git log -1 --format=%H -- tasks/reports/<report-file>`。",
            "报告内的基线用于复现；当前 Git 分支和同步状态应实时查询。",
            "",
        ]
    )
    return "\n".join(lines)


def check_versions(root: Path, errors: list[str]) -> None:
    project = (root / "pyproject.toml").read_text(encoding="utf-8")
    section = project.split("[project]\n", 1)[1].split("\n[", 1)[0]
    package = re.search(r'^version\s*=\s*"([^"]+)"', section, re.MULTILINE)
    citation_text = (root / "CITATION.cff").read_text(encoding="utf-8")
    citation = re.search(r'^version:\s*"([^"]+)"', citation_text, re.MULTILINE)
    tree = ast.parse((root / "src/silo/__init__.py").read_text(encoding="utf-8"))
    versions = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
    ]
    if not package or not citation or versions != [package[1]] or citation[1] != package[1]:
        errors.append("Package, runtime and citation versions disagree")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if package and f"## {package[1]} - Unreleased" in changelog:
        if re.search(r"^date-released:", citation_text, re.MULTILINE):
            errors.append("Unreleased development version has a citation release date")


def check_imports(root: Path, errors: list[str]) -> int:
    modules = {}
    for path in sorted((root / "src/silo").rglob("*.py")):
        name = ".".join(path.relative_to(root / "src").with_suffix("").parts)
        modules[name.removesuffix(".__init__")] = path
    edges: dict[str, set[str]] = defaultdict(set)
    for module, path in modules.items():
        package = module if path.name == "__init__.py" else module.rpartition(".")[0]
        layer = module.split(".")[1] if "." in module else ""
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                dependencies = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = package.split(".")[: len(package.split(".")) - node.level + 1]
                target = ".".join(base + ([node.module] if node.module else []))
                if not node.level:
                    target = node.module or ""
                dependencies = [target, *(f"{target}.{alias.name}" for alias in node.names)]
            else:
                continue
            for dependency in dependencies:
                if dependency in modules:
                    edges[module].add(dependency)
                if layer == "core" and dependency.startswith("silo."):
                    if dependency.split(".")[1] != "core":
                        errors.append(f"Core reverse dependency: {module} -> {dependency}")
                numeric_scipy = dependency.split(".")[0] == "scipy" and sparse_numeric_import(
                    node, module
                )
                if (
                    dependency.split(".")[0] in EXTERNAL_SOLVERS
                    and layer != "interfaces"
                    and not numeric_scipy
                ):
                    errors.append(f"External solver import outside interfaces: {module}")
    visited: set[str] = set()
    active: set[str] = set()

    def visit(module: str) -> None:
        if module in active:
            errors.append(f"Import cycle through {module}")
            return
        if module in visited:
            return
        active.add(module)
        for dependency in sorted(edges[module]):
            visit(dependency)
        active.remove(module)
        visited.add(module)

    for module in modules:
        visit(module)
    return len(modules)


def check_links(root: Path, errors: list[str]) -> int:
    count = 0
    for name in DOCS:
        path = root / name
        body = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
            target = target.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            count += 1
            if not (path.parent / unquote(parsed.path)).exists():
                errors.append(f"Broken local link: {name} -> {target}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-index", action="store_true", help="Refresh tasks/INDEX.md")
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    try:
        tasks, reports, exceptions = inventory(root, errors)
        check_versions(root, errors)
        modules = check_imports(root, errors)
        expected = render_index(tasks, reports, exceptions)
        index = root / "tasks/INDEX.md"
        if args.write_index and not errors:
            index.write_text(expected, encoding="utf-8", newline="\n")
        if not index.exists() or index.read_text(encoding="utf-8") != expected:
            errors.append(
                "Task index is stale; run scripts/check_project_structure.py --write-index"
            )
        links = check_links(root, errors)
        assets = subprocess.run(
            [sys.executable, "-B", str(root / "scripts/research/pricing/run_probe.py"), "--verify"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if assets.returncode:
            errors.append("Research asset verification failed: " + assets.stderr.strip())
    except (OSError, ValueError, KeyError, IndexError, SyntaxError) as exc:
        errors.append(str(exc))
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(
        f"Project structure OK: {len(tasks)} contracts, {len(reports)} reports, "
        f"{modules} modules, {links} local links; historical exceptions preserved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
