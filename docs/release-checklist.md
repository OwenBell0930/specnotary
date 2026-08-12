# 发布检查清单（GitHub 公开前）

> **硬约束：公开推送必须先走「上架九步流程」并获得维护者同意；本清单只覆盖技术就绪项，不替代九步。**
> 当前状态：**未公开**。提交只进本地 remote。

## 技术就绪（可自动验证）

| # | 项 | 验证命令 / 位置 | 状态 |
|---|----|-----------------|------|
| 1 | 全量回归绿 | `python3 tests/test_cli.py`（**数量以命令输出为准，不在文档手抄**） | ✅ |
| 2 | 样例门禁 PASS | `./cli/run-check.sh examples/case-order-cancel-raw/machine/spec.yaml` | ✅ |
| 3 | 模板首触 PASS | `./cli/run-check.sh templates/machine/spec.template.yaml` | ✅ draft |
| 4 | pip 安装可用 | `pip install . && specanvil check …` | ✅ 已在 venv 实测 |
| 5 | CI 工作流就位 | `.github/workflows/ci.yml`（推送后自动生效） | ✅ |
| 6 | LICENSE / CHANGELOG / CONTRIBUTING / SECURITY | 根目录 | ✅ |
| 7 | 无本机绝对路径入库 | `rg "/Users/" --glob '!*.svg'` 应为空 | 发布前复查 |
| 8 | 无真实公司资料 / 未脱敏内容 | 人工复查 examples/ docs/ | 发布前复查 |
| 9 | 名称无混淆 | **未通过**：specanvil.com 已存在且定位重合（2026-08-12 外部审计发现）；需改名或差异化决策，全渠道核查含域名/社交 | ❌ 阻断 |
| 10 | 个人资产隔离 | `.cursor/` 运营指针不入 git；`git ls-files .cursor/` 应为空 | ✅ 本轮已移除 |
| 11 | 外部无上下文红队 | 换一个未参与开发的模型/人，对照 `docs/proof-boundary.md` 打对抗负例，全部有 FAIL 或有边界解释 | 每次发布前执行 |
| 12 | 承诺与证明对齐 | README 中英承诺语句逐条对照 `docs/proof-boundary.md` | ✅ 本轮已校准 |

## 增长面就绪（本地已实现，发布后生效）

| 项 | 位置 | 状态 |
|----|------|------|
| 机读判定 `--json` | `specanvil check --json` | ✅ 有测试 |
| 英文 README + 英文人读 | `README.en.md` · `--lang en` | ✅ 有测试 |
| pre-commit 钩子 | `.pre-commit-hooks.yaml` | ✅ |
| GitHub Action | `action.yml` + `scripts/action_gate.py` | ✅（Marketplace 发布后实测） |
| MCP server | `specanvil mcp` | ✅ 冒烟测试 |
| Playground | `playground/index.html` | ✅ 本地浏览器实测（坏稿 FAIL / 修好稿 PASS） |
| 终端动图脚本 | `scripts/demo.tape` | 待 `brew install vhs` 后生成 gif |
| 发布物料 | `launch/`（不入库） | ✅ 草稿齐 |

## 发布时才执行（勿提前）

- 创建 GitHub 仓库（名称 `specanvil`），推送 `main` 与 tag `v0.3.0`；按 `launch/repo-metadata.md` 填 description/topics/social preview。
- `vhs scripts/demo.tape` 生成 `docs/assets/demo.gif` 并接入 README 首屏。
- PyPI 发布 `specanvil`（`python -m build && twine upload`）；验证 `uvx specanvil --version`。
- 开 GitHub Pages（root），线上验证 `playground/`。
- README 徽章从静态改为 CI 实时徽章；预埋 good first issues；执行 `launch/launch-checklist-48h.md`。

## 明确不做

- 不在九步批准前添加任何 GitHub remote。
- 不把运营仓（owenbell-github-ops）任何内容带入公开仓。
