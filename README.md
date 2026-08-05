<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="Spec Kit — 可开发的需求规格说明书" width="100%"/>
</p>

<h1 align="center">Spec Kit</h1>

<p align="center">
  <strong>可开发的需求规格说明书</strong><br/>
  机读主源 · 人读施工图 · CLI 门禁（FAIL / WARN / Pending）
</p>

<p align="center">
  <a href="#overview">Overview</a> ·
  <a href="#why">Why</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#gates">Gates</a> ·
  <a href="#examples">Examples</a> ·
  <a href="#structure">Structure</a> ·
  <a href="#docs">Docs</a>
</p>

<p align="center">
  <img alt="gate" src="https://img.shields.io/badge/gate-FAIL%20%7C%20WARN%20%7C%20Pending-0B6BCB"/>
  <img alt="runtime" src="https://img.shields.io/badge/runtime-Python%20%7C%20Node-159947"/>
  <img alt="source" src="https://img.shields.io/badge/source-machine--first-D97706"/>
  <img alt="author" src="https://img.shields.io/badge/by-OwenBell-0F172A"/>
</p>

---

<a id="overview"></a>

## Overview

上游 PRD / 工单 / FAQ 是**原料**。  
本仓库把它们压成研发能按表开工、测试能按 AC 验收的**规格层**——不是又一份口号式 PRD 模板。

<p align="center">
  <img src="docs/assets/flow.svg" alt="Spec Kit 主流程" width="100%"/>
</p>

**Key capabilities**

| Capability | 白话 |
|------------|------|
| **Machine-first** | YAML（优先）/ JSON 是唯一真相源；人读由机读生成 |
| **Construction-grade human** | 线框 · 控件表 · 状态矩阵 · 编号主路径 · AC · Pending |
| **Hard CLI gate** | `FAIL` 必须为 0 才 PASS；`WARN` 暴露质量债 |
| **Degraded Skill path** | 无 Python/Node 时可降级，但必须标 `gate_mode: degraded` |
| **Dual runtime** | `python3` 或 `node`（`cli/node` 需先 `npm i`） |

---

<a id="why"></a>

## Why it sticks（用真规格说话）

<p align="center">
  <img src="docs/assets/before-after.svg" alt="假详细 vs 施工图密度" width="100%"/>
</p>

打开「电商未发货取消」人读视图的一截——有线框、控件显隐、失败文案原文。  
主页留人不靠空口号，靠**你能否按这张表开发**。

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

**Prerequisites:** `python3`（推荐）或 `node`（`cd cli/node && npm i`）

```bash
cd spec-kit

# 1) 硬门禁 — FAIL 必须清零
./cli/run-check.sh examples/case-order-cancel-raw/machine/spec.yaml

# 2) 看假详细如何被拦下
./cli/run-check.sh examples/case-order-cancel-bad/machine/spec.yaml

# 3) 机读 → 人读施工图
./cli/run-generate-human.sh \
  examples/case-order-cancel-raw/machine/spec.yaml \
  examples/case-order-cancel-raw/human/spec.md

# 4) 回归
python3 tests/test_cli.py
```

> [!NOTE]
> 无 Python/Node：用 `skills/` 做降级检查，结果必须写明 `gate_mode: degraded`，不得冒充硬门禁。

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
| **FAIL** | 硬阻塞（空话 AC、缺 ui/states、ready 挂未决…） | 任意 1 条 → **FAIL** |
| **WARN** | 质量债（缺 empty_states、缺 step_id…） | 单独不否决；建议清零 |
| **Pending** | 未决项须含：问题 / 负责人 / 截止 / 阻塞什么 | 挂在 `ready` 上 → **FAIL** |

详解：[`docs/gate-modes.md`](docs/gate-modes.md)

---

<a id="examples"></a>

## Examples

同一业务主题：**电商 · 未发货自助取消**（虚构脱敏）

| 案例 | 输入 | 门禁 | 跳转 |
|------|------|------|------|
| Order cancel · raw | 运营约束清单 | PASS | [打开](examples/case-order-cancel-raw/) |
| Order cancel · bad | 假详细 PRD → 修好稿 | FAIL → PASS | [打开](examples/case-order-cancel-bad/) |
| Order cancel · FAQ | 客服 FAQ 反推 | PASS | [打开](examples/case-order-cancel-ops-faq/) |

坏稿会被哪些规则打死（示例）：缺 `ui` / `states` / `actors`、then 含「智能/尽快/体验好」、AC 不可观察、`ready` 仍留 `open_questions`。

更多说明：[`examples/README.md`](examples/README.md)

---

<a id="structure"></a>

## Structure

<p align="center">
  <img src="docs/assets/architecture.svg" alt="仓库构成" width="100%"/>
</p>

| 路径 | 作用 |
|------|------|
| [`templates/machine`](templates/machine) · [`templates/human`](templates/human) | 机读主源模板 · 人读体例 |
| [`examples/`](examples/) | 施工图级样例 |
| [`cli/`](cli/) | `run-check.sh` · `run-generate-human.sh` |
| [`skills/`](skills/) | 辅：起草与降级 |
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 「可开发」定义 |

**定位**

| 产物 | 定位 |
|------|------|
| 机读 YAML/JSON | 可开发需求规格的**主源** |
| 人读 Markdown | 同一规格的**说明书 / 施工图视图** |
| 上游 PRD | **原料**，不是本工具的主产出名 |

**纪律：** 外部 PRD 脚手架仅作只读灵感；业务母版不写入本仓。

---

<a id="docs"></a>

## Documentation

| Doc | 内容 |
|-----|------|
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | 什么叫「可开发」 |
| [`docs/gate-modes.md`](docs/gate-modes.md) | hard / degraded 门禁模式 |
| [`examples/README.md`](examples/README.md) | 案例索引 |
| [`skills/SKILL.md`](skills/SKILL.md) | Skill 规则 |

---

## Status

OwenBell · 本地建设中 · 上传 GitHub 前走九步复核（**上传即公开**）
