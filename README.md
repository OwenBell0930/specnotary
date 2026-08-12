<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecAnvil — 可开发的需求规格说明书" width="100%"/>
</p>

<h1 align="center">SpecAnvil</h1>

<p align="center">
  <strong>把含糊需求锻成可开发规格的硬门禁。</strong><br/>
  CLI 工具包 + 模板脚手架（辅：Cursor Skill）<br/>
  产出：<strong>可开发的需求规格说明书</strong> · 兼做<strong>需求评审就绪</strong>收口<br/>
  机读 YAML 为准据 · 人读施工图 · 确定性门禁（FAIL / WARN / Pending）
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
  <img alt="carrier" src="https://img.shields.io/badge/carrier-CLI%20%2B%20Scaffold%20%2B%20Skill-0B6BCB"/>
  <img alt="gate" src="https://img.shields.io/badge/gate-FAIL%20%7C%20WARN%20%7C%20Pending-DC2626"/>
  <img alt="runtime" src="https://img.shields.io/badge/hard%20gate-Python-159947"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0B6BCB"/>
  <img alt="node" src="https://img.shields.io/badge/Node-Deferred-94A3B8"/>
  <img alt="author" src="https://img.shields.io/badge/by-OwenBell-0F172A"/>
</p>

> 原工作名 Spec Kit；为免与 GitHub 官方 spec-kit 混淆而更名。与工作流类 SDD 工具的关系见 [`docs/positioning.md`](docs/positioning.md)。

---

<a id="value"></a>

## Value · 解决什么问题

**并集目标（都要满足）：**

1. **可开发** — 研发能按表开工，测试能按 AC 验收  
2. **评审就绪** — 评审前证明：原料没漏、方案没编、人读没漂、原型没跑偏

**一句话：** 把含糊的 PRD / 工单 / FAQ，锻成可开发规格；口号式「假详细」会被确定性门禁拦下。

| 痛点 | SpecAnvil 怎么处理 |
|------|-------------------|
| 需求写了很长，研发仍要猜显隐、文案、默认值 | 人读视图强制线框 · 控件表 · 状态/动作矩阵 · 编号主路径 |
| 「智能 / 尽快 / 体验好」冒充可开发 | 硬门禁 `FAIL`：空话 given/when/then、不可观察 AC、占位 ui/defaults 直接否决 |
| 人读与机读各改各的，越改越漂 | **以机读 YAML 为唯一准据**（single source of truth）；人读只由生成器产出，改正文即 FAIL |
| 评审时说不清原料哪句落到了哪条规格 | SourceClaim 覆盖闭环：每条原料有处置，每个必选实体有出处 |
| 原型与规格各自演化 | PrototypeManifest + HTML `data-spec-id` 落点核对 |
| 未决事项假装已就绪 | `Pending` 须齐五字段；挂在 `ready` 上 → `FAIL` |
| 没装 Python 就没法跑硬门禁 | 可用 Skill 降级检查，必须标 `gate_mode: degraded`；Node CLI = Deferred |

<p align="center">
  <img src="docs/assets/ipo-flow.svg" alt="输入 → 处理 → 输出 / Input → Process → Output" width="100%"/>
</p>

### 谁用 · 什么时候用

| 场景 | 做什么 |
|------|--------|
| 产品 / BA 收口需求 | 从原料起草机读 YAML，`--explain` 看差距，跑门禁，生成人读施工图 |
| 需求评审前 | 用 `specanvil report` 确认原料覆盖、Pending 闭合、假详细被拦下 |
| 研发开工前 | 用控件表与状态/动作矩阵对齐「能不能做、做到哪」 |
| 测试写用例前 | 用 AC 与空态文案当验收输入 |
| Agent / Skill 协作 | Skill 起草机读；CLI 当确定性验收，可挂 CI |
| 复盘假详细稿 | 对照 `case-order-cancel-bad`：看哪些规则会打死坏稿 |

**不是什么：** 不是又一份口号式 PRD 模板，也不是完整商业 PRD / 全链路 SDD 平台。上游 PRD 仍是**原料**；正式产出名是**可开发的需求规格说明书**（并用于评审收口）。

### 能力状态（诚实分层）

| 能力 | 状态 | 说明 |
|------|------|------|
| YAML/JSON 机读校验（Schema + 规则） | **Available** | `specanvil check` / `./cli/run-check.sh` |
| ready 差距报告 | **Available** | `specanvil check --explain` 打印 `READY-GAP` |
| 人读施工图生成 | **Available** | `specanvil human`（FAIL 时拒绝写入） |
| 一键同步哈希链 | **Available** | `specanvil sync`：重生成人读 + 刷新原型哈希 + 复跑门禁 |
| FAIL / WARN / Pending 分层 | **Available** | 见 `docs/gate-modes.md` |
| 通用 `action_matrix`（非订单域样例） | **Available** | 见 `examples/case-list-search/` |
| Skill 起草 / 降级检查 | **Available** | 降级须标 `degraded` |
| 原料覆盖（SourceClaim） | **Available** | 原料文件必须存在；必选实体必须被引用；`specanvil report` |
| 人读哈希 / stale 检测 | **Available** | `spec_hash` + 正文逐字对照 + `renderer_version`；只改正文也 FAIL |
| 原型 Manifest 一致性 | **Available** | manifest 哈希 + `data-spec-id` 落点（HTML/React/Vue 源）；无 manifest 则跳过并 WARN |
| 存量项目标记对账 | **Available** | `specanvil markers`：列出已标/非法/待回填的 `data-spec-id` |
| 悬空引用检查 | **Available** | 文本提及 `P-*`/`AC-*`/`SRC-*` 必须真实存在 |
| pip 安装 | **Available** | `pip install .`（PyPI 发布待九步批准） |
| 任意原料一键转机读 | **Planned** | Skill + 人工确认 |
| Node 等价硬门禁 | **Deferred** | stub 直接拒绝，绝不冒充 hard PASS |
| Web / MCP | **Deferred** | — |

---

<a id="overview"></a>

## Overview · 工具长什么样

**载体：**

| 层 | 是什么 | 职责 |
|----|--------|------|
| **CLI**（主 · Python） | `specanvil check / human / report / sync`（或 `cli/run-*.sh` 免安装） | 硬门禁；机读 → 人读；覆盖报告；哈希链同步 |
| **Scaffold**（主） | `templates/` · `examples/` | 字段体例与施工图级样例 |
| **Skill**（辅） | `skills/` | 起草机读；无运行时的降级检查 |

<p align="center">
  <img src="docs/assets/flow.svg" alt="SpecAnvil 主流程" width="100%"/>
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

**安装（二选一）：**

```bash
pip install .                     # 得到 specanvil 命令
# 或零安装：pip install pyyaml jsonschema 后直接用 ./cli/run-*.sh
```

**跑一遍样例：**

```bash
# 1) 硬门禁 — FAIL 必须清零（自动核对人读与原型）
specanvil check examples/case-order-cancel-raw/machine/spec.yaml

# 2) 看假详细如何被拦下
specanvil check examples/case-order-cancel-bad/machine/spec.yaml

# 3) 非订单域样例（通用 action_matrix）
specanvil check examples/case-list-search/machine/spec.yaml

# 4) 评审就绪报告（原料覆盖 + 原型归桶）
specanvil report examples/case-order-cancel-raw/machine/spec.yaml
```

**开一个新规格：**

```bash
mkdir -p my-feature/machine && cp templates/machine/spec.template.yaml my-feature/machine/spec.yaml
specanvil check my-feature/machine/spec.yaml --explain   # draft 即 PASS；READY-GAP 告诉你距 ready 差什么
# ……填内容；改完机读后一条命令同步人读与原型哈希：
specanvil sync my-feature/machine/spec.yaml
```

**回归：**

```bash
python3 tests/test_cli.py
```

> [!NOTE]
> 无 Python：用 `skills/` 做降级检查，必须写明 `gate_mode: degraded`。  
> 非 Cursor 用户：把 `skills/SKILL.md` 当提示词喂给任意 LLM 起草机读，再用 CLI 判定；CLI 本身不解析自然语言。  
> Node CLI = **Deferred**，不是等价硬门禁。

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
| **FAIL** | 硬阻塞（空话 then/AC、占位 ui/defaults、引用断裂、原料文件缺失、人读/原型漂移…） | 任意 1 条 → **FAIL** |
| **WARN** | 质量债（缺 empty_states、缺 step_id、assumption 待确认…） | 单独不否决；建议清零 |
| **Pending** | 未决项须含五字段：`id` / `missing` / `impact` / `owner` / `status` | 挂在 `ready` 上且未闭合 → **FAIL** |

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

坏稿会被哪些规则打死（示例）：Schema 非法 status、缺 `ui` / `states` / `actors`、引用断裂、then 含「智能/尽快/体验好」、AC 不可观察、`ready` 仍留 `open_questions`。

更多说明：[`examples/README.md`](examples/README.md)

---

<a id="structure"></a>

## Structure

<p align="center">
  <img src="docs/assets/architecture.svg" alt="CLI / Scaffold / Skill 构成" width="100%"/>
</p>

| 路径 | 作用 |
|------|------|
| [`src/specanvil/`](src/specanvil/) | Python 包：门禁规则、渲染器、Schema（pip 安装的主体） |
| [`cli/`](cli/) | 免安装包装：`run-check.sh` · `run-generate-human.sh` · `run-report.sh` · `run-sync.sh` |
| [`templates/`](templates/) | 机读 / 人读 / 原型 manifest 体例（模板本身过门禁） |
| [`examples/`](examples/) | 施工图级样例（含对齐与漂移双原型） |
| [`skills/`](skills/) | 辅：起草与降级 |
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 「可开发」定义 |

**产物分工**

| 产物 | 定位 |
|------|------|
| 机读 YAML/JSON | **唯一准据**（改这里） |
| 人读 Markdown | 同一规格的说明书 / 施工图视图（由 CLI 生成） |
| 上游 PRD / 工单 / FAQ | **原料**，不是 SpecAnvil 的正式产出名 |

**纪律：** 外部 PRD 脚手架仅作只读灵感；业务母版不写入本工具目录。

---

<a id="docs"></a>

## Documentation

| Doc | 内容 |
|-----|------|
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 什么叫「可开发」 |
| [`docs/gate-modes.md`](docs/gate-modes.md) | hard / degraded；原料覆盖与 stale |
| [`docs/positioning.md`](docs/positioning.md) | 与 GitHub spec-kit / OpenSpec 的关系 |
| [`docs/skill-boundary.md`](docs/skill-boundary.md) | CLI 与 Skill 边界 |
| [`docs/release-checklist.md`](docs/release-checklist.md) | 公开前技术就绪清单（九步之外的部分） |
| [`CHANGELOG.md`](CHANGELOG.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) | 版本 · 贡献 · 安全 |
| [`examples/README.md`](examples/README.md) | 案例索引 |
| [`skills/SKILL.md`](skills/SKILL.md) | Skill 规则 |

---

## Status

OwenBell · SpecAnvil 本地建设中 · 上传 GitHub 前走九步复核（**上传即公开**）
