# Changelog

SpecNotary 遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；版本号遵循语义化版本。

## [0.2.0] - 2026-08-12

### Added

- **全局视角人读（渲染器 v3）**：对照优秀解决方案说明书的阅读动线重建——目录、概览（叙述/设计原则/环境约束）、架构总览、职责边界（负责/不负责）、数据契约（字段表+规则+示例）、错误码、决策记录（未拍板在 ready 上 FAIL）；生命周期图与主路径图由机读**确定性生成**，架构图 mermaid 源码入机读随规格防漂；判断性文字在起草期写入机读字段，渲染器不创作。
- **增长面（发布前建设）**：`check --json` 机读判定；`human --lang en` 英文人读（中文输出逐字节不变，防漂按记录语言重渲染）；`specnotary precommit` + `.pre-commit-hooks.yaml`；GitHub Action（`action.yml`，PR 按文件标注）；`specnotary mcp` stdio server（Agent 可调用门禁，Experimental）；Pyodide Playground（浏览器零安装试用，已本地实测）；英文 README；VHS 动图脚本；英文空话词表校准（seamless / intuitive / user-friendly 等）。
- **可安装包 `specnotary`**：`pip install .` 后获得统一命令 `specnotary check|human|report|sync`。
- **`specnotary sync`**：改机读后一条命令重生成人读并刷新原型 manifest 哈希，再复跑门禁。
- **`specnotary check --explain`**：draft 规格打印 `READY-GAP`——距 `ready` 还差哪些硬项（确定性 dry-run，无须先翻状态再逐条读 FAIL）。
- **renderer_version**：人读头部记录渲染器版本；渲染器升级时给出一条明确的「重新生成」提示，而不是费解的正文哈希不匹配。
- **原料覆盖硬化**：`sources[].path` 必须真实存在；`ready` 至少一条 `covered`；每个必选 behavior/AC/control 必须被 SourceClaim 引用。
- **原型一致性硬化**：HTML `data-spec-id` 排除注释；映射控件必须在 HTML 出现；interaction `from/to/trigger` 断链 FAIL；`required` screen 必须有 path；除 `decoration/visual` 外无 `spec_refs` 即 extra。
- **ready 完备性硬化**：占位 `ui`/`defaults`/`states` 不算数；given/when/then 与 AC 正文非空且禁空话；`in_scope` 非空。
- 人读正文与按机读重渲染逐字对照（`body_hash`）——只改人读正文也会 FAIL。
- **实测驱动的三项硬化**（用真实项目文档实测后落地）：`「…」`内字面 UI 文案豁免空话扫描（真实按钮名「智能识别」不再误报）；自由文本悬空引用检查（提及 `P-*`/`AC-*`/`SRC-*` 必须存在，ready FAIL / draft WARN）；`specnotary markers` 存量对账命令 + 原型落点核对支持 React/Vue/Svelte 源文件（注释不算命中）。
- CI 工作流（GitHub Actions）、LICENSE (MIT)、CONTRIBUTING、SECURITY、发布检查清单。

### Changed

- 更名 **SpecNotary**（曾用名 Spec Kit → SpecAnvil）：Spec Kit 与 GitHub 官方 spec-kit 混淆，SpecAnvil 与 specanvil.com（2026-03 上线的同定位产品）撞名——外部审计发现后弃用。Notary（公证人）与产品本质同构：不创作内容，只钉快照、验签章、出证明；与 CNCF Notary Project（OCI 制品签名）无关。仓库目录名不变。
- Python 源码移至 `src/specnotary/`；Schema 移至包内 `src/specnotary/schemas/`。
- `project.yaml` 从被检查规格所在仓库向上查找，不再只读工具仓根目录。
- 评审就绪报告与人读头部改用相对路径，不再泄露本机绝对路径。
- 模板 `templates/machine/spec.template.yaml` 现在以 draft 直接通过门禁（占位 behavior/AC）。

### Fixed

- **外部红队修复包（2026-08-12 审计，11 条负例全部封死）**：原料内容哈希钉死快照（`sources[].content_hash`，原料一变即 FAIL）；`sync` 不再静默重新认证原型（须显式 `--attest-prototype`，背书是动作不是副作用）；任意类型错误的输入稳定 FAIL 不再崩溃；AC 必须关联 behavior；`action_matrix` 缺 `allowed` 或同键矛盾行 FAIL；`--allow-invalid` 产物改盖 `degraded` 并标注 forced；MCP 与 CLI 共用同一装配（`project_hint` 合并一致）；`human` 默认输出对齐 `human/spec.md`；样例补齐「ID 精确搜」行为与业务动因登记；自动主路径流程图移除（渲染器 v4——行为常为互斥分支，串成顺序流是错误语义）；证明边界唯一口径见 `docs/proof-boundary.md`。
- Node CLI（check 与 generate）不再可能冒充 `gate_mode: hard` / `RESULT: PASS`——一律退出码 3，且不携带影子规则集。
- `jsonschema` 未安装时 FAIL 而非静默降级。
- 显式传入不存在的人读/原型路径不再被跳过。

## [0.1.0] - 2026-08-11

初始三阶段（P0-P2）：JSON Schema 门禁、Python-only 硬门禁、`action_matrix` 通用状态矩阵、SourceClaim 原料覆盖、人读 `spec_hash` 防漂、PrototypeManifest + `data-spec-id` 原型一致性、对齐/漂移双样例、评审就绪报告。
