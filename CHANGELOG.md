# Changelog

SpecNotary 遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；版本号遵循语义化版本。

## [0.3.0] - 2026-08-13

### Added

- **全局视角人读（渲染器 v5）**：对照优秀解决方案说明书的阅读动线重建——目录、概览（叙述/设计原则/环境约束）、架构总览、职责边界（负责/不负责）、数据契约（字段表+规则+示例）、错误码、决策记录（未拍板在 ready 上 FAIL）；图只画机读真正声明过的关系（状态集合不连箭头、不自动生成主路径流程图），架构图 mermaid 源码入机读随规格防漂；判断性文字在起草期写入机读字段，渲染器不创作。
- **增长面（发布前建设）**：`check --json` 机读判定；`human --lang en` 英文人读（中文输出逐字节不变，防漂按记录语言重渲染）；`specnotary precommit` + `.pre-commit-hooks.yaml`；GitHub Action（`action.yml`，PR 按文件标注）；`specnotary mcp` stdio server（Agent 可调用门禁，Experimental）；Pyodide Playground（浏览器零安装试用，已本地实测）；英文 README；VHS 动图脚本；英文空话词表校准（seamless / intuitive / user-friendly 等）。
- **可安装包 `specnotary`**：`pip install .` 后获得统一命令 `specnotary check|human|report|sync`。
- **`specnotary sync`**：改机读后一条命令重新生成人读（真派生物）并复跑门禁；原型 manifest 哈希**不**自动刷新，须复核后显式 `--attest-prototype` 背书。
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

- **第四轮自检（2026-08-13）——针对「盲区如何产生」而非重跑清单**：修上一轮为消除误报而引入的过宽豁免（文档自检曾豁免任何含「不」的行，导致「刷新原型哈希，不必手动改」这类真承诺全部漏过）——改用结构性判据（措辞被引号引用、否定紧邻该短语），并为检测器本身加**双向校准测试**（5 条真承诺必须命中 + 6 条规则讨论必须豁免）；修占位检测与空话豁免的**规则交互盲区**：空话检测豁免 `「…」` 内文案以免误伤真实按钮名「智能识别」，而模板把占位词写作「占位」，共用豁免让所有模板空壳都能过 ready——占位改扫原文，并配对补上「真实 UI 文案不得误判为占位」的测试；强化只验退出码/文件存在的弱测试（新增「命令必须真的产生副作用」的通用回归）。
- **结论分层出口**：`check --json` 新增 `fail_by_layer` / `warn_by_layer`（machine / source / human / prototype），文本输出跨层时打印 `FAIL_LAYERS:`，GitHub Action 按层给出「该改哪个产物」的修复提示——证据分层是产品核心叙事，出口不该把它压平成字符串前缀。
- **第三轮外部复评修复包（2026-08-13，14 项）**：`sync` 语义修回其承诺——原型待背书**不再阻断**人读重生成（此前带原型的项目里普通 sync 完全不可用，而当时的测试只断言退出码，把 bug 固化成了预期）；`content_hash` 在 `ready` 上从 WARN 升为 FAIL，兑现「PASS 意味着登记基于未变化快照」的定义；**YAML 重复键直接拒绝加载**（`status: banana` + `status: ready` 曾静默取后值）；补齐空壳与占位类缺口（`title: {}`、behavior 无 `name`、given/when/then 与 AC/overview 残留模板占位词）；`permissions.can` 未出现在 `action_matrix` 给 WARN（不同抽象层，不宜 FAIL）；未知顶层字段给 WARN（`x_` 前缀豁免），避免拼错字段静默蒸发；`_lang({})` 不再返回字面 `{}`。
- **图形语义（渲染器 v5）**：状态图改为**不连线的状态集合**——此前按声明顺序连箭头，在订单样例里画出了业务上不存在的 `completed --> cancelled`；教训是文字标注「这不是流程图」救不了错误的图形语义。
- **文档自检补三个盲区**：扫描范围（漏了 CLI help 与 `action.yml`/playground）、跨行匹配（注释在命令上一行）、措辞变体（「自动刷新」）；新增版本单一来源检查（包/CLI/发布 tag 必须一致，包版本随之提为 0.3.0）与状态图无箭头检查。CHANGELOG 的历史版本段落豁免当前版本口径检查。
- **越界表述收紧**：README 与人读渲染文案改为「**已登记**原料条目的下落，账本完整性须人工抽查」；`SECURITY.md` 补 MCP 本地文件信任边界（不联网 ≠ 读取范围受限）；`proof-boundary.md` 补「`KILL_RATE` 100% 的分母是已登记变异，不是完整覆盖」——第三轮在满分状态下仍打出 7 条新缺口，全部已补入矩阵（现 50 个变异，含解析期变异）。
- **第二轮独立审查修复包（2026-08-12，9 项）**：补齐 v3 新对象缺失的规则家族——跨类型 ID 撞车、`error_codes` 重复码、`data_contracts` 重复字段、`lifecycle` 重复状态、`in_scope`/`out_of_scope` 自相矛盾、`responsibilities` 自我否定、`decisions.chosen` 悬空选项；封两处证据链绕过——`evidence` 引文必须与 `source_ref` 指向的文件名一致（原料整体掉包即暴露）、人读 `generated_from` 来源声明须确指被检查的机读文件（迁移只 WARN，伪造则 FAIL）；修正两处文档漂移（能力表仍写「`sync` 自动刷新原型哈希」、渲染器版本 v3/v4 不一致，`docs/gate-modes.md` 还在描述已删除的主路径图）；README 补起草量级预期。
- **两项防退化机制**：`tests/test_mutations.py` 变异矩阵（43 个变异 × 6 类算子 × 13 个对象族，`KILL_RATE` 100% 并进 CI，新增对象不补算子即 FAIL）；`tests/test_doc_consistency.py` 文档自检（子命令 / flag / 渲染器版本 / `sync` 语义 / 品牌 / 禁止手抄测试数）。全量回归从 132 秒降到 22 秒（纯逻辑用例改进程内调用，另留端到端用例守 bash 包装）。
- **外部红队修复包（2026-08-12 审计，11 条负例全部封死）**：原料内容哈希钉死快照（`sources[].content_hash`，原料一变即 FAIL）；`sync` 不再静默重新认证原型（须显式 `--attest-prototype`，背书是动作不是副作用）；任意类型错误的输入稳定 FAIL 不再崩溃；AC 必须关联 behavior；`action_matrix` 缺 `allowed` 或同键矛盾行 FAIL；`--allow-invalid` 产物改盖 `degraded` 并标注 forced；MCP 与 CLI 共用同一装配（`project_hint` 合并一致）；`human` 默认输出对齐 `human/spec.md`；样例补齐「ID 精确搜」行为与业务动因登记；自动主路径流程图移除（渲染器 v5——行为常为互斥分支，串成顺序流是错误语义）；证明边界唯一口径见 `docs/proof-boundary.md`。
- Node CLI（check 与 generate）不再可能冒充 `gate_mode: hard` / `RESULT: PASS`——一律退出码 3，且不携带影子规则集。
- `jsonschema` 未安装时 FAIL 而非静默降级。
- 显式传入不存在的人读/原型路径不再被跳过。

## [0.1.0] - 2026-08-11

初始三阶段（P0-P2）：JSON Schema 门禁、Python-only 硬门禁、`action_matrix` 通用状态矩阵、SourceClaim 原料覆盖、人读 `spec_hash` 防漂、PrototypeManifest + `data-spec-id` 原型一致性、对齐/漂移双样例、评审就绪报告。
