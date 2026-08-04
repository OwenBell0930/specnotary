# Spec Kit

**可开发的需求规格说明书** — 机读主源 · 人读施工图式视图 · CLI 门禁（FAIL / WARN）  
OwenBell

> 上游 PRD / 工单 / FAQ 是**原料**。  
> 本仓库产出的是研发能按表开工、测试能按 AC 验收的**规格层**（不是又一份口号式 PRD 模板）。

---

## 为什么值得留下（用真规格说话）

打开下面摘录：这是「电商未发货取消」人读视图的一截——有线框、控件显隐、失败文案原文。  
这就是本仓库要逼出来的密度；主页不靠海报，靠**你能否按这张表开发**。

### 摘录 · 控件规格（来自案例生成稿）

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

完整文件：

- 机读：[`examples/case-order-cancel-raw/machine/spec.yaml`](examples/case-order-cancel-raw/machine/spec.yaml)
- 人读：[`examples/case-order-cancel-raw/human/spec.md`](examples/case-order-cancel-raw/human/spec.md)

---

## 三步上手

```bash
cd spec-kit

# 1) 硬门禁（FAIL 必须清零；WARN 尽量清）
./cli/run-check.sh examples/case-order-cancel-raw/machine/spec.yaml

# 2) 看假详细如何被拦下
./cli/run-check.sh examples/case-order-cancel-bad/machine/spec.yaml

# 3) 机读 → 人读说明书
./cli/run-generate-human.sh examples/case-order-cancel-raw/machine/spec.yaml \
  examples/case-order-cancel-raw/human/spec.md

python3 tests/test_cli.py
```

无 Python/Node：用 `skills/` 降级检查，结果必须标 `gate_mode: degraded`。

门禁说明：[`docs/gate-modes.md`](docs/gate-modes.md)

---

## 案例（同一业务：未发货取消）

| 案例 | 输入 | 门禁 |
|------|------|------|
| [case-order-cancel-raw](examples/case-order-cancel-raw/) | 运营约束清单 | PASS |
| [case-order-cancel-bad](examples/case-order-cancel-bad/) | 假详细 PRD → 修好稿 | FAIL → PASS |
| [case-order-cancel-ops-faq](examples/case-order-cancel-ops-faq/) | 客服 FAQ 反推 | PASS |

坏稿会被哪些规则打死（示例）：缺 `ui`/`states`/`actors`、then 含「智能/尽快/体验好」、AC 不可观察、`ready` 仍留 `open_questions`。

---

## 仓库里有什么

| 路径 | 作用 |
|------|------|
| `templates/machine` · `templates/human` | 机读主源模板 · 人读体例 |
| `examples/` | 施工图级样例（虚构电商，脱敏） |
| `cli/` | `run-check.sh` · `run-generate-human.sh` |
| `skills/` | 辅：起草与降级 |
| `docs/what-is-dev-ready.md` | 「可开发」定义 |

**纪律：** 外部 PRD 脚手架（如 prd-vibe）仅作只读灵感；业务母版不写入本仓。

---

## 定位

| 产物 | 定位 |
|------|------|
| 机读 YAML/JSON | 可开发需求规格的**主源** |
| 人读 Markdown | 同一规格的**说明书 / 施工图视图**（线框·控件表·状态矩阵·编号主路径·AC·Pending） |
| 上游 PRD | **原料**，不是本工具的主产出名 |

OwenBell · 本地建设中 · 上传 GitHub 前走九步复核（上传即公开）
