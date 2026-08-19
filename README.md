<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecNotary — 可开发的需求规格说明书" width="100%"/>
</p>

<h1 align="center">SpecNotary</h1>

<p align="center">
  <strong>把含糊需求变成可开发规格——写作 + 质检全套。</strong><br/>
  用户只做三步：<strong>交出原料、确认结果、拿材料去评审</strong>。<br/>
  检查由 AI 助手代劳，你不必自己操作内部工具。
</p>

<p align="center">
  简体中文 · <a href="README.en.md">English</a>
</p>

<p align="center">
  <a href="#value">Value</a> ·
  <a href="#overview">Overview</a> ·
  <a href="#demo">Demo</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#gates">Gates</a> ·
  <a href="#examples">Examples</a> ·
  <a href="#structure">Structure</a> ·
  <a href="#docs">Docs</a>
</p>

<p align="center">
  <img alt="try" src="https://img.shields.io/badge/try-browser%20playground-0B6BCB"/>
  <img alt="gate" src="https://img.shields.io/badge/gate-FAIL%20%7C%20WARN%20%7C%20Pending-DC2626"/>
  <img alt="runtime" src="https://img.shields.io/badge/hard%20gate-Python-159947"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0B6BCB"/>
  <img alt="node" src="https://img.shields.io/badge/Node-Deferred-94A3B8"/>
  <img alt="author" src="https://img.shields.io/badge/by-OwenBell-0F172A"/>
</p>

> 与工作流类 SDD 工具的关系见 [`docs/positioning.md`](docs/positioning.md)。与 CNCF Notary Project（OCI 制品签名）无关。

---

<a id="value"></a>

## Value · 解决什么问题

**并集目标（都要满足）：**

1. **可开发** — 研发能按表开工，测试能按 AC 验收  
2. **评审就绪** — 评审前拿出证据链：原料快照未变且覆盖账本闭合、假设与未决被显式登记并硬拦、人读与准据逐字同源、原型落点未断链

**一句话：** 把含糊的 PRD / 工单 / FAQ，锻成可开发规格；口号式「假详细」会被确定性门禁拦下。

> 门禁能证明什么、不能证明什么，唯一口径见 [`docs/proof-boundary.md`](docs/proof-boundary.md)——PASS ≠ 业务正确，PASS = 结构与证据链闭合。

| 痛点 | SpecNotary 怎么处理 |
|------|-------------------|
| 需求写了很长，研发仍要猜显隐、文案、默认值 | 人读视图强制线框 · 控件表 · 状态/动作矩阵 · 编号主路径 |
| 「智能 / 尽快 / 体验好」冒充可开发 | 硬门禁 `FAIL`：空话 given/when/then、已知空话／占位词 AC、占位 ui/defaults 直接否决 |
| 人读与机读各改各的，越改越漂 | **以机读 YAML 为唯一准据**（single source of truth）；人读只由生成器产出，改正文即 FAIL |
| 评审时说不清原料哪句落到了哪条规格 | SourceClaim 账本：**已登记**的每条原料有处置、每个必选实体有出处，原料内容被哈希钉死（账本完整性由人抽查，见[证明边界](docs/proof-boundary.md)） |
| 原型与规格各自演化 | PrototypeManifest + HTML `data-spec-id` 落点核对 |
| 未决事项假装已就绪 | `Pending` 须齐五字段；挂在 `ready` 上 → `FAIL` |
| 没装 Python 就没法跑硬门禁 | 可用 Skill 降级检查，必须标 `gate_mode: degraded`；Node CLI = Deferred |

<p align="center">
  <img src="docs/assets/ipo-flow.svg" alt="输入 → 处理 → 输出 / Input → Process → Output" width="100%"/>
</p>

### 谁用 · 什么时候用

**用户只做三步：**

1. **交出原料** — 把原始需求说明发给 AI 助手
2. **确认结果** — 看说明书和页面稿对不对；原料没写清的假设需要你点头
3. **拿去评审** — 带上助手给出的输出自检报告去开会

先打开 [`playground/index.html`](playground/index.html) 点按钮看样例。自己的需求：把项目链接发给 AI 助手，请它按 [`skills/SKILL.md`](skills/SKILL.md) 帮你安装并工作。产品经理不必操作内部工具。

| 场景 | 做什么 |
|------|--------|
| 收一笔需求 | 交出原始说明，确认说明书和页面稿，带材料上会 |
| 需求评审前 | 看覆盖说明、已确认的假设、假详细有没有被拦住 |
| 交给研发 | 用说明书里的按钮、状态、验收句子看能不能做 |
| 交给测试 | 用验收句子和空态文案当用例输入 |
| 复盘假详细稿 | 对照 `case-order-cancel-bad`：看哪些写法会被拦住 |

**不是什么：** 不是又一份口号式需求模板，也不是项目管理或多人在线改稿。上游需求文档仍是**原料**；正式产出是**可开发的需求规格说明书**（并用于评审收口）。对方工具里的文档可以当原料进来，不会被自动改成我们的内部格式。

### 能力状态（诚实分层）

> 产品经理看上面三步即可。下表给 AI 助手和维护者对照，不是给你操作的清单。

| 能力 | 状态 | 说明 |
|------|------|------|
| YAML/JSON 机读校验（Schema + 规则） | **Available** | `specnotary check` / `./cli/run-check.sh` |
| 从原料建案 / 再登记一份原料 | **Available** | `specnotary new --from` · `specnotary ingest --spec`（钉哈希；不生成 claims） |
| WARN 接受账本 | **Available** | `specnotary confirm --by --reason --accept-all-warn`（谁/何时/为何；过期 id 在 ready 上 FAIL） |
| ready 差距报告 | **Available** | `specnotary check --explain` 打印 `READY-GAP` |
| 人读施工图生成 | **Available** | `specnotary human`（FAIL 时拒绝写入） |
| 一键同步派生物 | **Available** | `specnotary sync`：重生成人读 + 复跑门禁；原型背书须显式 `--attest-prototype` |
| FAIL / WARN / Pending 分层 | **Available** | 见 `docs/gate-modes.md` |
| 通用 `action_matrix`（非订单域样例） | **Available** | 见 `examples/case-list-search/` |
| Skill 起草 / 降级检查 | **Available** | 降级须标 `degraded` |
| 原料覆盖（SourceClaim） | **Available** | ready 上每个 source 必须有真实 path + content_hash；删除 path 不能绕过；必选实体必须被引用；`specnotary report` 写出输出自检报告 |
| 全局视角人读（目录/概览/功能说明/架构图/职责/数据契约/错误码/决策记录） | **Available** | 渲染器 v11；机读 ID 展开为中文；mermaid 图确定性生成，人读防漂 |
| 决策记录门禁 | **Available** | `decisions` 未拍板在 `ready` 上 FAIL |
| 人读哈希 / stale 检测 | **Available** | `spec_hash` + 正文逐字对照 + `renderer_version`；只改正文也 FAIL |
| 原型 Manifest 一致性 | **Available** | manifest 哈希 + 真实文件属性位 `data-spec-id`（HTML/React/Vue 源；script 字符串不算）；无 manifest 则跳过并 WARN |
| 存量项目标记对账 | **Available** | `specnotary markers`：列出已标/非法/待回填的 `data-spec-id` |
| 悬空引用检查 | **Available** | 文本提及 `P-*`/`AC-*`/`SRC-*` 必须真实存在 |
| 变异覆盖率度量 | **Available** | `tests/test_mutations.py`：变异算子 × 对象族，输出 `KILL_RATE` 并进 CI |
| 文档不漂自检 | **Available** | `tests/test_doc_consistency.py`：能力表语义/版本/子命令/flag 对着代码校验 |
| pip 安装 | **Available** | 克隆后 `pip install .`（PyPI 尚未发布） |
| 机读判定输出 | **Available** | `specnotary check --json`：含 `fail_by_layer`（machine/source/human/prototype，直接告诉集成方该改哪个产物） |
| 英文人读视图 | **Available** | `specnotary human --lang en`；中文输出逐字节不变 |
| pre-commit 钩子 | **维护者可选** | 助手本机检查即可。不是产品经理路径，也不做团队线上协同 |
| GitHub Action | **非产品路径** | 代码里有。当前用法是把文件夹交给助手在本机检查，不走 GitHub 协同 |
| MCP server | **非产品路径** | 代码里有。助手按 Skill 跑命令即可，不必再开一条协议 |
| 浏览器里点着试 | **Available** | [`playground/`](playground/index.html)：零安装，点按钮看不合格需求怎么被拦住 |
| 交给 Agent 安装后写自己的需求 | **Available** | 产品经理只提供原料并确认；Agent 按 Skill 起草并验收 |
| Node 等价硬门禁 | **Deferred** | stub 直接拒绝，绝不冒充 hard PASS |
| Web 服务端 | **Deferred** | — |

---

<a id="overview"></a>

## Overview · 工具长什么样

产品经理不必读这一节。下面写的是助手实际用到的内部结构。

**载体：**

| 层 | 是什么 | 职责 |
|----|--------|------|
| **CLI**（主 · Python） | `specnotary new / ingest / check / human / report / confirm / sync`（或 `cli/run-*.sh` 免安装） | 建案钉原料；硬门禁；机读 → 人读；覆盖报告；WARN 账本；哈希链同步 |
| **Scaffold**（主） | `templates/` · `examples/` | 字段体例与施工图级样例 |
| **Skill**（辅） | `skills/` | 起草机读；无运行时的降级检查 |

<p align="center">
  <img src="docs/assets/flow.svg" alt="SpecNotary 主流程" width="100%"/>
</p>

**能力一览（Available）**

| Capability | 白话 |
|------------|------|
| Machine-first | 改 YAML/JSON；人读由 CLI 生成；有 FAIL 时默认不生成 |
| Construction-grade human | 线框 · 控件表 · 状态/动作矩阵 · 编号主路径 · AC · Pending |
| Hard CLI gate | Python：`FAIL_COUNT` 必须为 0；Schema + ID/引用校验 |
| Degraded Skill | 无 Python 时可用，结果必须标 `degraded` |

---

<a id="demo"></a>

## Demo · 用真规格说话

<p align="center">
  <img src="docs/assets/before-after.svg" alt="假详细 vs 施工图密度" width="100%"/>
</p>

打开「电商未发货取消」人读视图的一截——有线框、控件显隐、失败文案原文。  
留人不靠空口号，靠**你能否按这张表开发**。

### 摘录 · 控件规格

| 控件 | 文案 | 显示条件 | 失败反馈 |
|------|------|----------|----------|
| `btn_cancel` | 取消订单 | 买家本人且状态∈{unpaid,paid_unshipped}且风控未拦截 | — |
| `btn_cancel_disabled` | 取消订单（置灰） | 状态∈{fulfilling,shipped} | 当前订单状态不支持自助取消，请联系客服或去售后中心 |
| `dlg_confirm_ok` | 确认取消 | 弹窗打开 | 取消失败，请稍后重试（网络/支付通道异常时） |

### 摘录 · 状态矩阵

| 状态 | 买家自助取消 | 说明 |
|------|--------------|------|
| `unpaid` | 允许 | 关单、释券、无退款单 |
| `paid_unshipped` | 允许 | 原路退款+回库；不自动回券 |
| `fulfilling` / `shipped` | 禁止 | `not_allowed` 原文提示 |

完整样例：

- 机读 → [`examples/case-order-cancel-raw/machine/spec.yaml`](examples/case-order-cancel-raw/machine/spec.yaml)
- 人读 → [`examples/case-order-cancel-raw/human/spec.md`](examples/case-order-cancel-raw/human/spec.md)

---

<a id="quick-start"></a>

## Quick Start

**产品经理**

1. 打开 [`playground/index.html`](playground/index.html)，点两个样例按钮（一份会被拦住，一份可以通过）。不用输入任何命令。
2. 感兴趣后，把**本机文件夹**交给 Cursor、Codex 或其他能改文件、能跑命令的 AI 助手，请它帮你安装，并按 [`skills/SKILL.md`](skills/SKILL.md) 工作。你和开发同事不需要在 GitHub 上一起改同一份规格。
3. 把你的需求草稿发给它。你只需补全缺的说明、确认写得对不对，然后拿评审材料去开会。

可以复制下面这段给助手（你自己不用执行）：

```text
请安装这份 SpecNotary（pip install .），并严格按 skills/SKILL.md 工作。
对我（产品经理）只问三件事：还缺什么原料、结果对不对、评审材料在哪。
不要让我操作内部工具，不要让我改内部文件。
```

**助手要执行的步骤**写在 [`skills/SKILL.md`](skills/SKILL.md)。自带样例在 `examples/`。

**回归：**

```bash
python3 tests/test_cli.py
```

> [!NOTE]
> **量级预期**：把含糊压成可开发规格是有成本的——样例里 12 行运营说明会展开成很长的说明书。适合多状态、多异常的复杂需求；极小改动不必用它。  
> 助手若环境里没有 Python，只能做降级检查，必须写明 `gate_mode: degraded`。  
> Node 运行时 = **Deferred**，不能冒充正式判定。

---

<a id="gates"></a>

## Gates

<p align="center">
  <img src="docs/assets/gate-layers.svg" alt="FAIL / WARN / Pending" width="100%"/>
</p>

<p align="center">
  <img src="docs/assets/cli-preview.svg" alt="CLI 门禁预览" width="100%"/>
</p>

| 层 | 含义 | 对 RESULT 的影响 |
|----|------|------------------|
| **FAIL**（给人看时叫「必须改」） | 硬阻塞（空话 then/AC、占位 ui/defaults、引用断裂、原料文件缺失、人读/原型漂移…） | 任意 1 条 → **FAIL** |
| **WARN**（给人看时叫「需要你拍板」） | 规格补了原文没有的猜测、可点页面稿还未核实等 | 单独不否决；记下是谁认的之后不再刷屏 |
| **Pending**（给人看时叫「还没定」） | 未决项须含五字段：`id` / `missing` / `impact` / `owner` / `status` | 挂在 `ready` 上且未闭合 → **FAIL** |

详解：[`docs/gate-modes.md`](docs/gate-modes.md)

---

<a id="examples"></a>

## Examples

| 案例 | 输入 | 门禁 | 跳转 |
|------|------|------|------|
| Order cancel · raw | 运营约束清单 | PASS | [打开](examples/case-order-cancel-raw/) |
| Order cancel · bad | 假详细 PRD → 修好稿 | FAIL → PASS | [打开](examples/case-order-cancel-bad/) |
| Order cancel · FAQ | 客服 FAQ 反推 | PASS | [打开](examples/case-order-cancel-ops-faq/) |
| List search | 商品列表搜索（非订单域） | PASS | [打开](examples/case-list-search/) |

坏稿会被哪些规则打死（示例）：Schema 非法 status、缺 `ui` / `states` / `actors`、引用断裂、then 含「智能搜索/尽快/体验好」、AC 命中已知空话词表、`ready` 仍留 `open_questions`。

更多说明：[`examples/README.md`](examples/README.md)

---

<a id="structure"></a>

## Structure

<p align="center">
  <img src="docs/assets/architecture.svg" alt="CLI / Scaffold / Skill 构成" width="100%"/>
</p>

| 路径 | 作用 |
|------|------|
| [`src/specnotary/`](src/specnotary/) | Python 包：门禁规则、渲染器、Schema（pip 安装的主体） |
| [`cli/`](cli/) | 免安装包装：`run-check.sh` · `run-generate-human.sh` · `run-report.sh` · `run-sync.sh` |
| [`templates/`](templates/) | 机读 / 人读 / 原型 manifest 体例（模板本身过门禁） |
| [`examples/`](examples/) | 施工图级样例（含对齐与漂移双原型） |
| [`skills/`](skills/) | 辅：起草与降级 |
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 「可开发」定义 |
| [`docs/human-view.md`](docs/human-view.md) | 人读正文用中文；机读 ID 只对账 |

**产物分工**

| 产物 | 定位 |
|------|------|
| 机读 YAML/JSON | **唯一准据**（改这里） |
| 人读 Markdown | 同一规格的说明书 / 施工图视图（由 CLI 生成） |
| 上游 PRD / 工单 / FAQ | **原料**，不是 SpecNotary 的正式产出名 |

**纪律：** 样例一律虚构；不要把真实业务母版放进 SpecNotary 产品树。

---

<a id="docs"></a>

## Documentation

| Doc | 内容 |
|-----|------|
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 什么叫「可开发」 |
| [`docs/gate-modes.md`](docs/gate-modes.md) | hard / degraded；原料覆盖与 stale |
| [`docs/positioning.md`](docs/positioning.md) | 与 GitHub spec-kit / OpenSpec 的关系（对方文档可 ingest，无一键转 YAML） |
| [`docs/empty-talk-corpus.md`](docs/empty-talk-corpus.md) | 空话好坏句子校准集（已知词表，不是一般 NLP） |
| [`docs/skill-boundary.md`](docs/skill-boundary.md) | CLI 与 Skill 边界 |
| [`docs/release-checklist.md`](docs/release-checklist.md) | 公开前技术就绪清单 |
| [`CHANGELOG.md`](CHANGELOG.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) | 版本 · 贡献 · 安全 |
| [`examples/README.md`](examples/README.md) | 案例索引 |
| [`skills/SKILL.md`](skills/SKILL.md) | Skill 规则 |

---

## Status

OwenBell · SpecNotary 公开预览（v0.3.0）· [GitHub](https://github.com/OwenBell0930/specnotary) · 产品路径：试用页 + 把文件夹交给 Cursor / Codex
