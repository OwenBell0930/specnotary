# 发布检查清单（GitHub 公开前）

> **硬约束：公开推送必须先走「上架九步流程」并获得维护者同意；本清单只覆盖技术就绪项，不替代九步。**
> 当前状态：**未公开**。提交只进本地 remote。

## 技术就绪（可自动验证）

| # | 项 | 验证命令 / 位置 | 状态 |
|---|----|-----------------|------|
| 1 | 全量回归绿 | `python3 tests/test_cli.py` | ✅ 46 项 |
| 2 | 样例门禁 PASS | `./cli/run-check.sh examples/case-order-cancel-raw/machine/spec.yaml` | ✅ |
| 3 | 模板首触 PASS | `./cli/run-check.sh templates/machine/spec.template.yaml` | ✅ draft |
| 4 | pip 安装可用 | `pip install . && specanvil check …` | ✅ 已在 venv 实测 |
| 5 | CI 工作流就位 | `.github/workflows/ci.yml`（推送后自动生效） | ✅ |
| 6 | LICENSE / CHANGELOG / CONTRIBUTING / SECURITY | 根目录 | ✅ |
| 7 | 无本机绝对路径入库 | `rg "/Users/" --glob '!*.svg'` 应为空 | 发布前复查 |
| 8 | 无真实公司资料 / 未脱敏内容 | 人工复查 examples/ docs/ | 发布前复查 |
| 9 | 名称无混淆 | SpecAnvil（GitHub/npm/PyPI 检索无同名活跃项目，2026-08-12 核查） | ✅ |

## 发布时才执行（勿提前）

- 创建 GitHub 仓库（名称 `specanvil`），推送 `main` 与 tag `v0.2.0`。
- PyPI 发布 `specanvil`（`python -m build && twine upload`）。
- README 徽章从静态改为 CI 实时徽章。

## 明确不做

- 不在九步批准前添加任何 GitHub remote。
- 不把运营仓（owenbell-github-ops）任何内容带入公开仓。
