<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecNotary — 评审就绪的标准需求规格说明书" width="100%"/>
</p>

<h1 align="center">SpecNotary</h1>

<p align="center">
  <strong>把零散需求，变成经得起评审的产品方案。</strong><br/>
  <strong>专为产品经理与产品管理团队设计。</strong>高质量起草、产品质量审查、确定性结构门禁，一套工作流完成。<br/>
  让评审聚焦于<strong>目标、边界、产品与信息架构、业务流程和 UX</strong>，而不是现场补口径。<br/>
  <strong>Agent-first：</strong>在 Cursor 或 Codex 中发送 <a href="https://github.com/OwenBell0930/specnotary">github.com/OwenBell0930/specnotary</a>，直接在当前工作区使用。
</p>

<p align="center">
  <a href="#quick-start"><strong>立即开始</strong></a> ·
  <a href="https://owenbell0930.github.io/specnotary/playground/">在线体验</a> ·
  <a href="examples/product-review-fixture/reports/product-review.md">查看产品审查样例</a>
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
  <img alt="audience" src="https://img.shields.io/badge/for-Product%20Managers-7C3AED"/>
  <img alt="workflow" src="https://img.shields.io/badge/workflow-Draft%20%7C%20Review%20%7C%20Gate-0B6BCB"/>
  <img alt="agents" src="https://img.shields.io/badge/agents-Cursor%20%7C%20Codex-159947"/>
  <img alt="traceable" src="https://img.shields.io/badge/output-review--ready-0F766E"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0B6BCB"/>
  <img alt="author" src="https://img.shields.io/badge/by-OwenBell-0F172A"/>
</p>

---

<a id="value"></a>

## Value · 一眼看懂

**目标用户：** 需要把模糊业务诉求转成清晰产品方案的产品经理，以及负责统一需求质量的产品管理团队。

**核心场景：** 从接到 PRD、工单、会议纪要、FAQ 等需求原料，到需求评审开始之前。

**核心价值：** 帮你把“材料写完了”升级为“方案可以被有效评审”——目标与边界有依据，产品与信息架构清楚，流程和 UX 能讨论，假设、冲突与未决项能追溯。

| 能力 | 帮你完成什么 | 可独立调用 |
|------|--------------|------------|
| **Draft · 高质量起草** | 把零散原料组织为包含目标、范围、角色、架构、流程、交互、异常与决策的候选产品规格 | `/draft-spec` |
| **Review · 产品质量审查** | 按统一质量模型审查核心准确性、边界合理性、架构扩展性、流程逻辑与 UX，并给出有依据的审查结论 | `/review-spec` |
| **Gate · 确定性结构门禁** | 检查规格结构、原料追溯、人读/机读一致性及可选原型映射，输出可复核结果 | `/gate-spec` |

默认使用 `/write-spec` 跑完整流程；已有方案的团队可以只调用 Review + Gate。三项能力共用同一套[产品质量模型](docs/product-quality-model.md)，但各自结论保持独立。

### 你最终拿到什么

- **标准产品规格**：适合人阅读、讨论和评审
- **机读需求准据**：供 Cursor、Codex 等 Agent 继续引用
- **产品质量审查报告**：明确优势、风险、证据与待拍板事项
- **结构门禁结果**：对结构、追溯和文档漂移给出确定性结论
- **可选原型追溯**：需要原型时，让页面与规格条目保持映射

| 使用前 | 使用 SpecNotary 后 |
|--------|-------------------|
| 原料散落在文档、工单和口头信息里 | 汇总为一份有来源、有决策记录的评审材料 |
| 评审会上才发现目标、边界或流程没讲清 | 在会前通过 Draft 与 Review 提前暴露关键缺口 |
| 文档看起来完整，却无法判断产品方案是否合理 | 把产品质量与结构完整性分开审查，结论更清楚 |
| 人读文档、机读规格和原型各自演化 | 用准据、哈希与映射关系保持可追溯 |

<p align="center">
  <img src="docs/assets/ipo-flow.svg" alt="输入 → 处理 → 输出 / Input → Process → Output" width="100%"/>
</p>

### 三步完成一次需求评审准备

**用户只做三步：**

1. **交出原料** — 把需求说明、工单、会议纪要或已有方案交给 AI 助手
2. **确认关键决策** — 核对目标、边界、架构、流程和助手显式列出的假设
3. **拿材料去评审** — 携带标准规格、产品审查报告和门禁结果进入会议

最快的使用方式：把 [GitHub 网址](https://github.com/OwenBell0930/specnotary) 发给 Cursor 或 Codex，请它安装并按 [`skills/specnotary/SKILL.md`](skills/specnotary/SKILL.md) 工作。规格直接写在你的业务文件夹中，产品经理无需操作 CLI。

**个人产品经理**可以使用完整流程提高单份方案质量；**产品管理部门**可以只调用 Review + Gate，对已有文档做统一审查与门禁。

**产品边界：** 专注产品经理“接到需求原料 → 输出标准方案去评审”的阶段；研发实施与测试交付继续使用团队既有体系。

<details>
<summary><strong>维护者能力矩阵（点击展开）</strong></summary>

> 下表给 AI 助手和维护者核对实现状态；产品经理按上面的三步使用即可。

| 能力 | 状态 | 说明 |
|------|------|------|
| YAML/JSON 机读校验（Schema + 规则） | **Available** | `specnotary check` / `./cli/run-check.sh` |
| 从原料建案 / 再登记一份原料 | **Available** | `specnotary new --from` · `specnotary ingest --spec`（钉哈希；不生成 claims） |
| WARN 接受账本 | **Available** | `specnotary confirm --by --reason --accept-all-warn`（谁/何时/为何；过期 id 在 ready 上 FAIL） |
| ready 差距报告 | **Available** | `specnotary check --explain` 打印 `READY-GAP` |
| 人读评审稿生成 | **Available** | `specnotary human`（FAIL 时拒绝写入） |
| 一键同步派生物 | **Available** | `specnotary sync`：重生成人读 + 复跑门禁；原型背书须显式 `--attest-prototype` |
| FAIL / DRAFT / PASS 与问题分层 | **Available** | 见 `docs/gate-modes.md`；草稿结构通过也不会冒充终稿 PASS |
| 通用 `action_matrix`（非订单域样例） | **Available** | 见 `examples/case-list-search/` |
| Skill 起草 / 独立审查 / 降级检查 | **Available** | `/write-spec` 全流程；`/draft-spec` `/review-spec` `/gate-spec` 可拆；降级须标 `degraded` |
| 产品质量模型（Draft/Review 共用） | **Available** | [`docs/product-quality-model.md`](docs/product-quality-model.md)；审查契约与反例语料；**不**进 Python hard gate |
| 原料覆盖（SourceClaim） | **Available** | ready 上每个 source 必须有真实 path + content_hash；删除 path 不能绕过；必选实体必须被引用；`specnotary report` 写出输出自检报告 |
| 全局视角人读（目录/概览/功能说明/产品与信息架构/职责/数据契约/错误码/决策记录） | **Available** | 渲染器 v14；机读 ID 展开为中文；mermaid 图确定性生成，人读防漂 |
| 决策记录门禁 | **Available** | `decisions` 未拍板在 `ready` 上 FAIL |
| 人读哈希 / stale 检测 | **Available** | `spec_hash` + 正文逐字对照 + `renderer_version`；只改正文也 FAIL |
| 原型方案与 Manifest 一致性 | **Available** | `D-PROTOTYPE` 首轮必拍板；选择制作则 manifest 必须存在并核对哈希与真实 `data-spec-id`，选择不制作则不制造缺失告警 |
| 存量项目标记对账 | **Available** | `specnotary markers`：列出已标/非法/待回填的 `data-spec-id` |
| 悬空引用检查 | **Available** | 文本提及 `P-*`/`AC-*`/`SRC-*` 必须真实存在 |
| 变异覆盖率度量 | **Available** | `tests/test_mutations.py`：变异算子 × 对象族，输出 `KILL_RATE` 并进 CI |
| 文档不漂自检 | **Available** | `tests/test_doc_consistency.py`：能力表语义/版本/子命令/flag 对着代码校验 |
| pip 安装 | **Available** | `pip install "git+https://github.com/OwenBell0930/specnotary.git"`（不必把 SpecNotary 设成工作区；PyPI 尚未发布） |
| 机读判定输出 | **Available** | `specnotary check --json`：含 `fail_by_layer`（machine/source/human/prototype，直接告诉集成方该改哪个产物） |
| 英文人读视图 | **Available** | `specnotary human --lang en`；中文输出逐字节不变 |
| pre-commit 钩子 | **维护者可选** | 助手本机检查即可。不是产品经理路径，也不做团队线上协同 |
| GitHub Action | **非产品路径** | 代码里有。当前用法是把网址发给助手在本机检查，不走 GitHub 协同 |
| MCP server | **非产品路径** | 代码里有。助手按 Skill 跑命令即可，不必再开一条协议 |
| 浏览器里点着试 | **Available** | [在线 Playground](https://owenbell0930.github.io/specnotary/playground/)：零安装，点按钮看不合格需求怎么被拦住 |
| 交给 Agent 安装后写自己的需求 | **Available** | 产品经理只提供原料并确认；Agent 按 Skill 起草并验收 |
| Node 等价硬门禁 | **Deferred** | stub 直接拒绝，绝不冒充 hard PASS |
| Web 服务端 | **Deferred** | — |

</details>

---

<a id="overview"></a>

## Overview · 工具长什么样

产品经理不必读这一节。下面写的是助手实际用到的内部结构。

**载体（产品经理主入口是 Agent）：**

| 层 | 是什么 | 职责 |
|----|--------|------|
| **Agent Skills / Commands** | `/write-spec` `/draft-spec` `/review-spec` `/gate-spec` + `skills/` | **面向产品经理的主入口**：全流程编排或单能力调用 |
| **CLI**（Python） | `specnotary check / human / report / sync / …` | **Structure Gate 确定性执行引擎**（及建案/同步）；不是产品经理日常交互 |
| **Scaffold / Schema / Docs** | `templates/` · `examples/` · `docs/` | 支撑资产：字段体例、样例、质量模型与证明边界 |

<p align="center">
  <img src="docs/assets/flow.svg" alt="SpecNotary 主流程" width="100%"/>
</p>

**能力一览（Available）**

| Capability | 白话 |
|------------|------|
| Agent entry | Cursor/Codex 按 Skill/Command 工作；产品经理只交原料、确认、拿材料 |
| Machine-first | 改 YAML/JSON；人读由 CLI 生成；有 FAIL 时默认不生成 |
| Product Review | 语义审查绑定 `content_hash`；改后复审；与 Gate 结论分开 |
| Hard CLI gate | Python Structure Gate：`FAIL_COUNT` 必须为 0；Schema + ID/引用校验 |
| Degraded Skill | 无 Python 时可用，结果必须标 `degraded` |

---

<a id="demo"></a>

## Demo · 用真规格说话

<p align="center">
  <img src="docs/assets/before-after.svg" alt="假详细 vs 评审规格密度" width="100%"/>
</p>

打开「电商未发货取消」人读视图的一截——有线框、控件显隐、失败文案原文。
评审不靠空口号，靠**每条方案能否在这张表上被逐项判断**。

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

1. 打开 [在线 Playground](https://owenbell0930.github.io/specnotary/playground/)，点两个样例按钮（一份会被拦住，一份可以通过）。不用输入任何命令。
2. 感兴趣后，把 [GitHub 网址](https://github.com/OwenBell0930/specnotary) 发给 Cursor、Codex 或其他能改文件、能跑命令的 AI 助手，请它安装并按 Skill/Command 工作。规格写在你正在用的文件夹里即可，不必把 SpecNotary 设成当前工作区。
3. 按场景选用入口（由助手执行；你不必操作 CLI）：

| 场景 | 入口 | 说明 |
|------|------|------|
| 原料 → 完整评审包 | `/write-spec` | Draft → Review（改后复审）→ Gate；结论分开 |
| 只要候选稿 | `/draft-spec` | 只起草，不自动 Review/Gate |
| 已有文档只要产品质量审查 | `/review-spec` | 默认不改原文；绑定 `content_hash` |
| 已有文档：Review + Gate | `/review-spec` 再 `/gate-spec` | 可跳过 Draft；**普通 Markdown 不能直接 hard PASS**，须先合法 machine spec（或只提取的 normalize/projection 后再 Gate，且须复审） |
| 只要结构门禁 | `/gate-spec` | 仅合法 machine spec；Gate PASS ≠ 方案合理 |

可以复制下面这段给助手（你自己不用执行）：

```text
请从 https://github.com/OwenBell0930/specnotary 安装 SpecNotary（不必把它设成当前工作区）：
pip install "git+https://github.com/OwenBell0930/specnotary.git"
并严格按该仓 skills/specnotary/SKILL.md 工作。规格写在我现在这个文件夹里即可。
对我（产品经理）只问三件事：还缺什么原料、结果对不对、评审材料在哪。
不要让我操作内部工具，不要让我改内部文件。
```

**助手要执行的步骤**写在 [`skills/specnotary/SKILL.md`](skills/specnotary/SKILL.md)。自带样例在 `examples/`。

**回归：**

```bash
python3 tests/test_cli.py
```

> [!NOTE]
> **量级预期**：把含糊原料整理成评审规格是有成本的——样例里 12 行运营说明会展开成很长的说明书。适合多状态、多异常的复杂需求；极小改动不必用它。
> 助手若环境里没有 Python，只能做降级检查，必须写明 `gate_mode: degraded`。
> Node 运行时 = **Deferred**，不能冒充正式判定。

### Cursor Customize

Cursor 侧栏 **Customize** 上的官方目录是 [Marketplace](https://cursor.com/marketplace)。SpecNotary 已带 `.cursor-plugin/plugin.json`（Skill + `/write-spec` `/draft-spec` `/review-spec` `/gate-spec`，不含 MCP）。上架须把公开 Git 地址提交到 [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish)，由 Cursor 人工审核，通过后才会出现在 Customize 里。未上架前：把 GitHub 网址发给助手即可。

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
  <img src="docs/assets/architecture.svg" alt="Agent 入口 / CLI Gate 引擎 / 支撑资产" width="100%"/>
</p>

| 路径 | 作用 |
|------|------|
| [`src/specnotary/`](src/specnotary/) | Python 包：Structure Gate、渲染器、Schema |
| [`cli/`](cli/) | 免安装包装：`run-check.sh` · `run-generate-human.sh` · `run-report.sh` · `run-sync.sh` |
| [`templates/`](templates/) | 机读 / 人读 / 原型 manifest 体例（模板本身过门禁） |
| [`examples/`](examples/) | 评审规格级样例（含对齐与漂移双原型） |
| [`skills/`](skills/) · [`commands/`](commands/) | **用户入口**：全流程 + Draft / Review / Gate |
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 「评审就绪」定义（保留旧文件名以兼容链接） |
| [`docs/human-view.md`](docs/human-view.md) | 人读正文用中文；机读 ID 只对账 |

**产物分工**

| 产物 | 定位 |
|------|------|
| 机读 YAML/JSON | **唯一准据**（改这里） |
| 人读 Markdown | 同一规格的说明书 / 评审视图（由 CLI 生成） |
| 上游 PRD / 工单 / FAQ | **原料**，不是 SpecNotary 的正式产出名 |

**纪律：** 样例一律虚构；不要把真实业务母版放进 SpecNotary 产品树。

---

<a id="docs"></a>

## Documentation

| Doc | 内容 |
|-----|------|
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 什么叫「评审就绪」 |
| [`docs/product-quality-model.md`](docs/product-quality-model.md) | Draft/Review 唯一公共产品质量模型 |
| [`docs/product-review-contract.md`](docs/product-review-contract.md) | 产品审查报告字段与结论 |
| [`docs/product-review-corpus.md`](docs/product-review-corpus.md) | 结构合法但方案不合理的反例语料 |
| [`docs/gate-modes.md`](docs/gate-modes.md) | hard / degraded；原料覆盖与 stale |
| [`docs/proof-boundary.md`](docs/proof-boundary.md) | 门禁能证明 / 不能证明 |
| [`docs/positioning.md`](docs/positioning.md) | 与 GitHub spec-kit / OpenSpec 的关系（对方文档可 ingest，无一键转 YAML） |
| [`docs/empty-talk-corpus.md`](docs/empty-talk-corpus.md) | 空话好坏句子校准集（已知词表，不是一般 NLP） |
| [`docs/skill-boundary.md`](docs/skill-boundary.md) | CLI 与 Draft/Review/Gate Skill 边界 |
| [`docs/release-checklist.md`](docs/release-checklist.md) | 公开前技术就绪清单 |
| [`CHANGELOG.md`](CHANGELOG.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) | 版本 · 贡献 · 安全 |
| [`examples/README.md`](examples/README.md) | 案例索引 |
| [`skills/specnotary/SKILL.md`](skills/specnotary/SKILL.md) | 默认全流程编排 |

---

## Status

OwenBell · SpecNotary 公开预览（v0.3.0）· [GitHub](https://github.com/OwenBell0930/specnotary) · 产品路径：试用页 + 把网址发给 Cursor / Codex；不必把 SpecNotary 设成工作区
