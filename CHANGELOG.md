# Changelog

SpecNotary 遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；版本号遵循语义化版本。

## [0.3.0] - 2026-08-13

### Added

- **对外入口**：产品经理在试用页点按钮即可；感兴趣后把文件夹发给 AI 助手安装。产品经理只面对原料、确认、评审材料。不覆盖多人在线改稿。
- **维护边界**：机读装载（`spec_io`）/ 规则与证据（`libspec`）/ 人读渲染（`spec_render`）分文件；Schema 对象数组与变异家族、顶层键、形状消毒表互相发现遗漏。
- **WARN 最小接受账本**：`accepted_warnings`（谁/何时/为何）对得上则不再刷屏；缺字段或过期 id 在 ready 上 FAIL。账本与 `review` 不进 `spec_hash`，入账不打断人读/原型背书。
- **公开空话语料**：[`docs/empty-talk-corpus.md`](docs/empty-talk-corpus.md) 好坏句子集接到门禁测试（已知词表，不是一般可观察性 NLP）。
- **全局视角人读（阅读动线，当前渲染器 v11）**：目录、概览、范围、功能说明、架构总览、职责边界、数据契约、错误码、决策记录；门禁对账用的 HTML 注释放在文末；人读把文案键、状态枚举、业务动作、角色 ID 展开为中文；原料附录的处理结果也用中文；状态图按对象分组且不连箭头；主路径是功能说明的验收写法。口径见 [`docs/human-view.md`](docs/human-view.md)。
- **机读判定与维护者配件**：`check --json`（含 `fail_by_layer`）；`human --lang en`（中文输出逐字节不变）；`specnotary precommit` + `.pre-commit-hooks.yaml`；GitHub Action；`specnotary mcp`；浏览器试用页；英文 README；VHS 动图脚本；英文空话词表校准。GitHub Action / MCP 不是产品经理路径。
- **可安装包 `specnotary`**：`pip install .` 后获得统一命令 `specnotary check|human|report|sync`。
- **`specnotary sync`**：改机读后一条命令重新生成人读（真派生物）并复跑门禁；原型 manifest 哈希**不**自动刷新，须复核后显式 `--attest-prototype` 背书。
- **`specnotary check --explain`**：draft 规格打印 `READY-GAP`。
- **renderer_version**：人读头部记录渲染器版本；渲染器升级时给出「重新生成」提示。
- **原料覆盖**：`sources[].path` 必须真实存在；`ready` 至少一条 `covered`；每个必选 behavior/AC/control 必须被 SourceClaim 引用。
- **原型一致性**：HTML `data-spec-id` 排除注释；映射控件必须在 HTML 出现；interaction `from/to/trigger` 断链 FAIL；`required` screen 必须有 path；除 `decoration/visual` 外无 `spec_refs` 即 extra。
- **ready 完备性**：占位 `ui`/`defaults`/`states` 不算数；given/when/then 与 AC 正文非空且禁空话；`in_scope` 非空。
- 人读正文与按机读重渲染逐字对照（`body_hash`）——只改人读正文也会 FAIL。
- **`「…」` 内字面 UI 文案豁免空话扫描**；自由文本悬空引用检查；`specnotary markers` 存量对账 + 原型落点核对支持 React/Vue/Svelte 源文件。
- CI 工作流、LICENSE (MIT)、CONTRIBUTING、SECURITY、发布检查清单。

### Changed

- Python 源码移至 `src/specnotary/`；Schema 移至包内 `src/specnotary/schemas/`。
- `project.yaml` 从被检查规格所在目录向上查找，不再只读工具根目录。
- 评审就绪报告与人读头部改用相对路径，不写入本机绝对路径。
- 模板 `templates/machine/spec.template.yaml` 现在以 draft 直接通过门禁（占位 behavior/AC）。

### Fixed

- **人读裸 ID**：按机读标签全量展开状态/动作/文案键（含 lifecycle 后缀别名、`value_labels`、角色 id、默认值列表、控件显示条件、字段说明），并用测试钉住；禁止只改人读 Markdown。
- **输出自检报告给人看（渲染器 v11）**：标题「输出自检报告」；结构检查两档写成「必须改 / 需要你拍板」；处理结果、落到说明书哪一段、结论都用中文。试用页检查结果同步。
- **使用方式**：产品经理路径是试用页 + 把 GitHub 网址发给 Cursor / Codex；规格写在她正在用的文件夹里，不必把 SpecNotary 设成工作区；GitHub Action、MCP 标为非产品路径。
- **假详细两层**：词表补「形成闭环」「治理体系」「赋能」「抓手」等；词表漏网由助手按 Skill 用语义拦住，禁止写进硬检查的结构通过。
- **证据单调性**：ready 删除 `sources[].path` 不再绕过快照；原型自报 manifest 不能替代真实文件 `data-spec-id` 落点；YAML 与 JSON 重复键同等拒绝；嵌套非对象 item / 非 UTF-8 人读稳定 FAIL；人读头部 `body_hash` / `gate_mode` 不得伪造；空话规则是已知词表；旗舰订单样例把源外推断标成 assumption。
- **文档自检判据**：豁免改为「被引号引用，或否定紧邻该短语」；占位检测扫原文，不与空话的 `「…」` 豁免共用；写文件的命令必须回读产物。
- **结论分层出口**：`check --json` 新增 `fail_by_layer` / `warn_by_layer`；文本输出跨层时打印 `FAIL_LAYERS:`。
- **`sync` 与快照定义**：原型待背书不再阻断人读重生成；`content_hash` 在 `ready` 上 FAIL；空壳 title / 无 name 的 behavior / 模板占位词补齐；未知顶层字段 WARN（`x_` 前缀豁免）。
- **图形语义**：状态图改为不连线的状态集合，不按声明顺序画箭头。
- **文档自检范围**：CLI help、`action.yml`、playground；跨行匹配；「自动刷新」措辞变体；包 / CLI / 发布 tag 版本一致。
- **越界表述**：原料账本写成「**已登记**条目的下落，完整性须人工抽查」；`KILL_RATE` 100% 的分母是已登记变异，不是完整覆盖。
- **对象族规则**：跨类型 ID 撞车、`error_codes` 重复码、`data_contracts` 重复字段、`lifecycle` 重复状态、scope 自相矛盾、`responsibilities` 自我否定、`decisions.chosen` 悬空选项；`evidence` 引文须与 `source_ref` 文件名一致；人读 `generated_from` 须确指被检查的机读文件。
- **负例覆盖**：`tests/test_mutations.py` 变异矩阵（`KILL_RATE` 100% 并进 CI）；`tests/test_doc_consistency.py` 文档自检。
- **原料快照与原型背书**：`sources[].content_hash` 原料一变即 FAIL；`sync` 须显式 `--attest-prototype`；类型错误输入稳定 FAIL；AC 必须关联 behavior；`action_matrix` 缺 `allowed` 或同键矛盾行 FAIL；`--allow-invalid` 产物盖 `degraded`；MCP 与 CLI 共用同一装配。
- Node CLI（check 与 generate）不再可能冒充 `gate_mode: hard` / `RESULT: PASS`——一律退出码 3。
- `jsonschema` 未安装时 FAIL 而非静默降级。
- 显式传入不存在的人读/原型路径不再被跳过。

## [0.1.0] - 2026-08-11

首次可用：JSON Schema 门禁、Python-only 硬门禁、`action_matrix` 通用状态矩阵、SourceClaim 原料覆盖、人读 `spec_hash` 防漂、PrototypeManifest + `data-spec-id` 原型一致性、对齐/漂移双样例、评审就绪报告。
