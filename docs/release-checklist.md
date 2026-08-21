# 发布检查清单（GitHub 公开）

> 当前状态：**已公开**。[github.com/OwenBell0930/specnotary](https://github.com/OwenBell0930/specnotary) · tag `v0.3.0`。
> 产品路径仍是：试用页 + 把 GitHub 网址发给 Cursor / Codex。规格写在正在用的文件夹里即可。不做团队线上改稿。

## 技术就绪（可自动验证）

| # | 项 | 验证命令 / 位置 | 状态 |
|---|----|-----------------|------|
| 1 | 全量回归绿 | `python3 tests/test_cli.py`（**数量以命令输出为准，不在文档手抄**） | ✅ 2026-08-19 |
| 2 | 样例门禁 PASS | `./cli/run-check.sh examples/case-order-cancel-raw/machine/spec.yaml` | ✅ |
| 3 | 模板首触 PASS | `./cli/run-check.sh templates/machine/spec.template.yaml` | ✅ draft |
| 4 | pip 安装可用 | `pip install . && specnotary check …` | ✅ 已在 venv 实测 |
| 5 | CI 工作流就位 | `.github/workflows/ci.yml`（推送后自动生效） | ✅ |
| 6 | LICENSE / CHANGELOG / CONTRIBUTING / SECURITY | 根目录 | ✅ |
| 7 | 无本机绝对路径入库 | `git grep "/Users/" -- ':!*.svg' ':!docs/release-checklist.md'` | ✅ 2026-08-19 复查 |
| 8 | 无真实公司资料 / 未脱敏内容 | 样例为虚构商城；`launch/` 不入库 | ✅ 2026-08-19 复查 |
| 9 | 名称无混淆 | **SpecNotary**：GitHub 无同名仓/用户/组织；npm/PyPI/crates.io 无 `specnotary`；与 CNCF Notary Project 领域不同（README 已声明） | ✅ 2026-08-19 |
| 10 | 个人资产隔离 | 运营仓 MEMORY 不入 git；仅 `.cursor/rules/*.mdc` 产品规则 | ✅ |
| 11 | 按说明书独立安装试用 | 未参与开发的助手按 README 安装并打开试用页 | ✅ 2026-08-19 |
| 12 | 承诺与证明对齐 | README 中英承诺语句逐条对照 `docs/proof-boundary.md` | ✅ |
| 13 | 变异矩阵与文档自检绿 | `python3 tests/test_mutations.py`（KILL_RATE 100%）· `python3 tests/test_doc_consistency.py` | ✅ 2026-08-19 |
| 14 | 版本单一来源 | 包 / CLI / tag `v0.3.0` | ✅ 发布时打 tag |

## 增长面就绪（**不是产品经理路径**）

GitHub Action / MCP / pre-commit 给维护者。当前用法：把网址发给助手在本机检查。

| 项 | 位置 | 状态 |
|----|------|------|
| 机读判定 `--json` | `specnotary check --json` | ✅ 有测试 |
| 英文 README + 英文人读 | `README.en.md` · `--lang en` | ✅ 有测试 |
| pre-commit 钩子 | `.pre-commit-hooks.yaml` | ✅ |
| GitHub Action | `action.yml` + `scripts/action_gate.py` | 代码有；**非产品路径** |
| MCP server | `specnotary mcp` | 代码有；**非产品路径** |
| Playground | `playground/index.html` | ✅ 可开 GitHub Pages |
| 终端动图脚本 | `scripts/demo.tape` | 待 `brew install vhs` 后生成 gif |
| 发布物料 | `launch/`（不入库） | 草稿齐；Show HN / 中文帖不是 git 公开的前置 |

## 公开后可选（不挡 git）

- PyPI 发布 `specnotary`（`python -m build && twine upload`）
- GitHub Pages 验证 playground
- README 徽章改为 CI 实时徽章；预埋 good first issues
- `vhs scripts/demo.tape` 生成 `docs/assets/demo.gif`

## 明确不做

- 不把运营仓任何内容带入公开仓。
- 不把团队 GitHub 协同当作产品经理使用方式。
