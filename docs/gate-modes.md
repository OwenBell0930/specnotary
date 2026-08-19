# 门禁模式 / Gate modes

| 模式 | 何时 | 效力 |
|------|------|------|
| `hard` | **Python** CLI 已执行（`specnotary check` / `./cli/run-check.sh`） | 可作为本地「自动测试跑通」依据 |
| `degraded` | 无 Python，Skill+LLM 代跑 | **仅参考**；不得冒充 hard PASS |

> **Node CLI：Deferred。** `cli/node/` 与 `SPECNOTARY_RUNTIME=node` **拒绝**冒充 hard PASS（退出码 3），且不携带任何影子规则集。硬门禁只有 Python；无 Python 时用 Skill 并标 `gate_mode: degraded`。

## hard 结果分层

| 级别 | 含义 | 处理 |
|------|------|------|
| **FAIL** | Schema 不通过、引用断裂、ready 却空话/占位、原料文件缺失、人读/原型漂移、Pending 未闭合等 | 必须修到 0 条 FAIL |
| **WARN** | 缺线框/空态、legacy `cancel_matrix`、assumption 待确认等 | 尽量清零；保留须 `specnotary confirm --by --reason` 写入账本 |
| **PASS** | FAIL_COUNT=0 | 若仍有 WARN，标注「PASS with WARN」；对得上的 `accepted_warnings`（谁/何时/为何）不再刷屏 |

## 校验分层

1. **JSON Schema**（`src/specnotary/schemas/machine-spec.schema.json`）— 类型、enum、必填  
2. **确定性规则** — **YAML 与 JSON 重复键直接拒绝加载**（同一键两次赋值意味着准据本身歧义）；ID 唯一（含跨类型不撞车）、跨对象引用、不自相矛盾（scope / 矩阵 / 职责）；ready 完备性（占位 ui/defaults/states 不算数；`title` 非空；behavior 必须有 `name`；given/when/then 与 AC 非空、禁空话词表、禁模板占位词（占位/待补/TODO…）——注意**空话检测豁免 `「…」` 内的字面 UI 文案，占位检测不豁免**（模板把占位词写在「」里，共用豁免会放过所有模板空壳）；`待补` 不误伤 `待补充`；`in_scope` 非空）、Pending 五字段、**决策记录未拍板或 `decided` 无 chosen 在 ready 上 FAIL**、自由文本悬空引用（`P-*` / `AC-*` / `SRC-*` / `D-*` 提及即必须存在；ready FAIL，draft WARN）；ready 缺 `overview`、`permissions.can` 未出现在 `action_matrix`、未知顶层字段（`x_` 前缀豁免）均为 WARN；嵌套非对象 item 与非 UTF-8 人读稳定 FAIL，不崩溃  
3. **原料覆盖** — ready 上每个 `sources[]` **必须有 path 且文件存在**（删除 path 不能绕过快照）；**`content_hash` 在 ready 上必填且须匹配**（PASS 的定义包含「登记基于未变化的快照」，不钉死则该定义不成立；draft 上缺 path / 缺 hash 为 WARN），原料一变全体 claims stale FAIL；`evidence` 引文文件名须与 `source_ref` 指向的文件一致（换文件即暴露）；ready 至少 1 条 `covered`；每个必选 behavior/AC/control 须被 claim 引用；`omitted` / 未闭合 `conflict` 在 `ready` 上 FAIL；`assumption` 为 WARN（可用 `accepted_warnings` 入账后不再刷屏；缺 by/date/reason 在 ready 上 FAIL；过期 id 在 ready 上 FAIL）  
4. **人读 stale** — 人读头 `spec_hash` 必须等于当前机读内容哈希；`renderer_version` 必须等于当前渲染器版本（版本不符给出单条「重新生成」提示）；正文须与按机读重渲染逐字一致（只改正文也 FAIL）；头部 `body_hash` 若存在必须等于正文哈希；`gate_mode` 若存在必须为 `hard`，除非同时有 `forced`（此时必须为 `degraded`）  
5. **原型一致性** — 若存在 `prototype/prototype.manifest.yaml`：manifest 哈希、必需控件/行为映射、禁止无规格业务动作、映射必须落在真实文件的属性位 `data-spec-id`（HTML 与 React/Vue/Svelte 源文件均可；注释、`<script>` 字符串不算命中；source/claim ID 不能给 UI 控件背书）、interaction `from/to/trigger` 不得断链、`required` screen 必须有 path；`semantic_warnings` 仅为 WARN。无 manifest 时跳过（ready 下 WARN，不挡 PASS）。自报 mapping 而无文件 ≠ 原型层 PASS。

依赖：`pip install .`（或仅 `pip install pyyaml jsonschema` 走 `cli/run-*.sh`）

## 结论分层（按「该改哪个产物」归类）

一次 FAIL 可能来自四个不同的产物，修法完全不同。文本输出在跨层时打印 `FAIL_LAYERS:`，`--json` 给出 `fail_by_layer` / `warn_by_layer`，集成方不必解析消息前缀：

| 层 | 含义 | 怎么修 |
|----|------|--------|
| `machine` | 机读规格本身不合规 | 改 YAML |
| `source` | 原料或覆盖账本漂了 | 复核 SourceClaim / 更新 `content_hash` |
| `human` | 派生物过期 | `specnotary sync <spec>` |
| `prototype` | 背书过期 | 复核原型后 `specnotary sync <spec> --attest-prototype` |

## 集成出口

这些给维护者和助手，**不是产品经理的使用方式**。产品经理把文件夹交给助手；助手默认跑 `specnotary check` / `report`。不覆盖和开发同事在 GitHub 上一起改稿。

- **`specnotary check --json`**：机读判定（fail/warn/`fail_by_layer`/ready_gap/exit_code），本机脚本可调用。
- **`specnotary precommit <spec...>`**：多文件聚合检查，配 `.pre-commit-hooks.yaml` 一行接入（维护者可选）。
- **GitHub Action**（根目录 `action.yml`）：**非产品路径**。以后若有人把规格放进 GitHub 才用。
- **`specnotary mcp`**：**非产品路径**。助手按 Skill 跑命令即可。
- **`specnotary human --lang en`**：英文人读视图；语言记录在头部，防漂校验按记录语言重渲染。
- **Playground**（`playground/index.html`）：浏览器里点按钮试用，零安装零上传；属降级环境，完整判定仍以助手跑的检查为准。

## draft 差距报告

```bash
specnotary check <machine.yaml> --explain
```

对 draft 规格额外打印 `READY-GAP`：若现在把 `status` 翻成 `ready` 会新增哪些 FAIL。确定性 dry-run，判定零 LLM。

## 一键同步派生物（背书须显式）

```bash
specnotary sync <machine.yaml>                      # 重新生成人读 + 复跑门禁
specnotary sync <machine.yaml> --attest-prototype   # 复核原型后，显式背书刷新 manifest 哈希
```

人读是**派生物**（真的被重新渲染），sync 直接重生成——**原型是否待背书不影响这一步**（否则用户无法区分「人读没同步」与「原型没背书」）。原型**不是**派生物（sync 不重新生成原型），所以默认不刷新 `generated_from_spec.hash`——机读变更后原型保持 stale FAIL（此时 sync 退出码为 1，但人读已经更新），直到人/Agent 复核原型并显式 `--attest-prototype`。背书是动作，不是副作用。两类哈希效力差异详见 [`proof-boundary.md`](proof-boundary.md)。机读本身有非原型 FAIL 时拒绝同步。

## 存量项目接入（retrofit）

```bash
specnotary markers <machine.yaml> <前端源码目录>
```

对账源码里已有的 `data-spec-id`（支持 .html/.tsx/.jsx/.vue/.svelte，注释里的不算）：列出已匹配、非法标记、以及必选控件/行为还缺哪些标记。回填完成后再写 manifest 接入原型门禁。此命令仅对账，不是门禁。

## 输出自检报告

```bash
specnotary report examples/case-order-cancel-raw/machine/spec.yaml
```

写出 `reports/review-readiness.md`，标题是「输出自检报告」。给产品经理开会看：原始说明每条怎么处理了（已写入规格 / 原文没写、规格补了猜测 / 原文互相打架 / 本期不做…）、已经拍过板的提醒、可点页面稿对得上吗、结构是否通过。处理结果和结论用中文；英文 FAIL / WARN / PASS 只在括号里对账。报告不是检查工具本身；检查仍以 `specnotary check` 为准。

## 写作入口与 WARN 账本

```bash
specnotary new <case-dir> --from <raw-file> [--kind ops|prd|faq|speckit|ticket|raw] [--id]
specnotary ingest <raw-file> --spec <machine.yaml> --kind speckit   # 薄适配：只登记+钉哈希
specnotary confirm <machine.yaml> --by <name> --reason "<why>" --accept-all-warn
# 逐条接受：specnotary confirm <spec> --by <name> --reason "<why>" --accept assumption:SRC-CLM-008
```

`new` / `ingest` 不把自然语言变成 YAML。`confirm` 把当前 WARN id 写入 `accepted_warnings`（谁/何时/为何）；该字段与 `review` 不进 `spec_hash`，所以入账不会让人读或原型背书过期。空话对错句子见 [`empty-talk-corpus.md`](empty-talk-corpus.md)。

## Pending 五字段（status=ready 时）

每条待闭合必须含：`id` · `missing` · `impact` · `owner` · `status`。  
`status=ready` 时不得残留 `open` / `待确认` / `tbd` 的 Pending。

## 生成人读

`specnotary human`（或 `./cli/run-generate-human.sh`）在机读仍有 FAIL 时**拒绝写入**，除非传入 `--allow-invalid`。

### 人读阅读动线（渲染器 v11）

先全局后细节：目录、概览、范围、**功能说明**、架构总览、职责边界、数据契约、角色权限、状态与允许动作、页面与交互、主路径（功能说明的验收写法）、默认值文案、错误码、AC、Pending、决策记录、对象 AI、原料落在规格里的情况（附录）。章节按机读实际内容动态编号。门禁对账用的 HTML 注释放在文末，避免 Markdown 预览出现空白。人读把机读 ID **全部**展开为中文：提示文案键 → 「界面原文」；状态枚举 / lifecycle / 业务动作 / 角色 → 中文名（括号里保留机读 ID）。附录的处理结果也用中文（已写入规格，而不是 covered）。不要在说明书正文里留下 `file_too_large`、`terminated`、`create_import_task` 这种裸字段。口径见 [`human-view.md`](human-view.md)。

**图只画机读真正声明过的关系。** 这是踩过两次坑后的硬规矩：

- 状态图渲染为**不连线的状态集合**——此前它按声明顺序连箭头，在订单样例里画出了 `completed --> cancelled` 这种业务上根本不存在的转移。转移真相只在 `action_matrix` 里。
- **不自动生成主路径流程图**（v4 起）：behaviors 常是互斥分支，串成顺序流等于断言机读从未声明的流程。
- 架构图的 mermaid 源码存在机读 `architecture.mermaid` 里，由作者显式声明——图进哈希链，一样防漂。

教训写在这里以免重犯：**用文字标注「这不是流程图」救不了错误的图形语义**，读者先看形状。判断性文字（概览、设计原则、决策理由）在**起草期**写入机读字段（Skill 辅助），渲染器只摆放、不创作。
