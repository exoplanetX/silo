# SILO 本地开发工作台首版

- ID: 20261023-01-01_development-workbench。签发前扫描同日合同/报告，无已用 TT。
- 来源：本对话用户认可六页设计后明确指示“好，那就开始做吧”。
- 类型：用户批准的独立开发管理工具，L1；不计为原七步研究里程碑完成。
- 唯一问题：能否在 Codex 旁展示仓库真实状态、八维评价依据、目标与教学资料，并生成有来源的讨论上下文？
- 原目标保持：note26 的研究对象、原七步及 A–E 有界计划不变；A/B 已验收，C 签发前 HOLD，D/E 不自动启动。
- 本轮成功终点：六页可浏览、评价可追溯、A/B/C 准确、教学材料可读、上下文可复制；通过下面检查后交付停止。
- 推荐模型：GPT-6 Sol / medium；推荐不代表模型已切换。

## 基线、授权与范围

基线 main / cc5aeebd97b40561f02ba689cc0b065e9c94c415，cached origin/main...HEAD=0/32，未查询即时远端。
当前用户指示授权在此已有工作副本实现独立工作台；保留全部已有本地提交，不推送。
两项既有治理变动只读保留、排除暂存与提交：

- AGENTS.md SHA256=2347688089628bb58a3c185d95fa7d4c57bcf3a897baa40889560d58b63ec638
- 根案例通告 SHA256=0220d15620e8613a015da68697ace272817ee2e660049d0aabda3b5330a8e221

允许新增/修改：

- scripts/workbench.py 与 scripts/workbench/ 下 HTML、CSS、JS、显式来源映射 JSON。
- tests/unit/test_workbench.py：投影、缺失/过期来源、只读文件边界、HTTP 的确定性检查。
- docs/development_workbench.md、docs/README.md 的工作台入口。
- 本合同、同名执行报告、自动生成 tasks/INDEX.md。
- outputs/ 下忽略的临时 QA 材料；不提交生成物。

禁止修改：src/、求解器现有测试、依赖/打包、公共求解器 CLI/API/schema、ROADMAP、阶段计划、.silo-dos 状态、教学正文、既有合同与报告、Skill/Agent。
网页只读投影；不提供求解、任意命令执行、状态审批、文件写回或云端发布。
无第三方新增依赖、无外部字体/CDN；Python 标准库本地服务只监听 127.0.0.1。
评价初始判断有日期、支持域与来源；缺证、来源变化、未评价均显式展示，不以总分或任务数量计算目标完成率。
Learning delivery: not applicable；只导航/呈现已有 learning 正文，不新增数学主题或复制第二套正文。

## 检查与验收

1. 确定性测试验证仓库读取、任务合同与报告区分、稳定教学元信息、来源缺失/变化降为待复核，以及目录越界/非法路径拒绝。
2. JavaScript 语法检查、Ruff、任务索引刷新、scripts/check_project_structure.py 和 scripts/check_quality.py。
3. 本地 HTTP 与内嵌浏览器实查六页、搜索、证据查看、习题/解答、上下文生成和刷新；检查窄视口与空结果。
4. 治理文件哈希保持，src/ 与现有算法测试无改动；无虚构性能数据，网页刷新不运行测试。

## 有界执行、报告与 Git

本轮只执行本合同。浏览器检查最多两轮集中修复；出现范围外阻断时记录并停止，不追加算法/平台任务。
Git mode: local-commit；只提交允许文件，不 push。用户现有未提交文件不处理。
报告：tasks/reports/20261023-01-01_development-workbench_report.md。
报告记录实际检查、浏览器验证边界、剩余事项、Git/缓存远端状态与学习影响。
