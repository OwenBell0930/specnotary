# Changelog

SpecAnvil 遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；版本号遵循语义化版本。

## [0.2.0] - 2026-08-12

### Added

- **可安装包 `specanvil`**：`pip install .` 后获得统一命令 `specanvil check|human|report|sync`。
- **`specanvil sync`**：改机读后一条命令重生成人读并刷新原型 manifest 哈希，再复跑门禁。
- **`specanvil check --explain`**：draft 规格打印 `READY-GAP`——距 `ready` 还差哪些硬项（确定性 dry-run，无须先翻状态再逐条读 FAIL）。
- **renderer_version**：人读头部记录渲染器版本；渲染器升级时给出一条明确的「重新生成」提示，而不是费解的正文哈希不匹配。
- **原料覆盖硬化**：`sources[].path` 必须真实存在；`ready` 至少一条 `covered`；每个必选 behavior/AC/control 必须被 SourceClaim 引用。
- **原型一致性硬化**：HTML `data-spec-id` 排除注释；映射控件必须在 HTML 出现；interaction `from/to/trigger` 断链 FAIL；`required` screen 必须有 path；除 `decoration/visual` 外无 `spec_refs` 即 extra。
- **ready 完备性硬化**：占位 `ui`/`defaults`/`states` 不算数；given/when/then 与 AC 正文非空且禁空话；`in_scope` 非空。
- 人读正文与按机读重渲染逐字对照（`body_hash`）——只改人读正文也会 FAIL。
- **实测驱动的三项硬化**（用真实项目文档实测后落地）：`「…」`内字面 UI 文案豁免空话扫描（真实按钮名「智能识别」不再误报）；自由文本悬空引用检查（提及 `P-*`/`AC-*`/`SRC-*` 必须存在，ready FAIL / draft WARN）；`specanvil markers` 存量对账命令 + 原型落点核对支持 React/Vue/Svelte 源文件（注释不算命中）。
- CI 工作流（GitHub Actions）、LICENSE (MIT)、CONTRIBUTING、SECURITY、发布检查清单。

### Changed

- 更名 **SpecAnvil**（原工作名 Spec Kit），消除与 github/spec-kit 的混淆；仓库目录名不变。
- Python 源码移至 `src/specanvil/`；Schema 移至包内 `src/specanvil/schemas/`。
- `project.yaml` 从被检查规格所在仓库向上查找，不再只读工具仓根目录。
- 评审就绪报告与人读头部改用相对路径，不再泄露本机绝对路径。
- 模板 `templates/machine/spec.template.yaml` 现在以 draft 直接通过门禁（占位 behavior/AC）。

### Fixed

- Node CLI（check 与 generate）不再可能冒充 `gate_mode: hard` / `RESULT: PASS`——一律退出码 3，且不携带影子规则集。
- `jsonschema` 未安装时 FAIL 而非静默降级。
- 显式传入不存在的人读/原型路径不再被跳过。

## [0.1.0] - 2026-08-11

初始三阶段（P0-P2）：JSON Schema 门禁、Python-only 硬门禁、`action_matrix` 通用状态矩阵、SourceClaim 原料覆盖、人读 `spec_hash` 防漂、PrototypeManifest + `data-spec-id` 原型一致性、对齐/漂移双样例、评审就绪报告。
