<!-- generated_from: examples/case-03-reverse-manual/machine/spec.yaml -->
<!-- gate_mode: hard -->
<!-- DO NOT long-term edit without updating machine source -->

# 报销助手 · 发票识别与审批
# Expense assist · Invoice OCR & approval

- **ID:** `SPEC-EXPENSE-001`
- **Status:** `ready`
- **Spec version:** `0.1`

## Scope / 范围

### In scope / 范围内

- 发票图片识别金额与日期并生成草稿 / OCR amount/date from invoice image into draft
- 经理审批通过/驳回（驳回必填原因） / Manager approve/reject with mandatory reject reason

### Out of scope / 范围外

- 自动打款与税务申报 / Auto payout and tax filing

### Open questions / 待决

- （无 / none）

## Actors & permissions / 角色与权限

- `employee`: 员工 / Employee
- `manager`: 经理 / Manager
- `employee` can `upload, edit_draft_amount_date, submit`
- `manager` can `approve, reject`

## Defaults & empty states / 默认值与空态

```yaml
currency: CNY
currency_editable: false
reject_reason_min_chars: 5
```

## Object AI / 对象 AI

- enabled: `True`
- failure_fallback: OCR 失败则进入全手工录入金额与日期
- confidence_threshold: `0.7`
- tools_boundary:
  - 仅允许调用发票 OCR；不得调用外部支付 / Invoice OCR only; no external payment tools
- human_takeover_when:
  - 模型置信度 < 0.7 / Model confidence < 0.7

## Behaviors / 行为

### `B1` 上传并生成草稿

- **Given:** 员工已登录 / Employee signed in
- **When:** 上传发票图片 / Uploads invoice image
- **Then:** 生成含金额、日期、币种=CNY 的草稿；置信度<0.7 时标黄并阻止提交直至人工确认 / Create draft with amount, date, currency=CNY; if confidence<0.7 mark amber and block submit until human confirm

### `B2` 经理驳回

- **Given:** 草稿处于待审批 / Draft pending approval
- **When:** 经理驳回 / Manager rejects
- **Then:** 必须填写不少于 5 字原因，否则无法提交驳回 / Require reject reason ≥5 chars or reject action fails

## Acceptance / 验收

- `A1` (B1): Given 置信度 0.65 When 员工点提交 Then 被阻断并提示需人工核对 / Given confidence 0.65 When employee submits Then block with human-check prompt
- `A2` (B2): Given 待审批 When 经理驳回原因为 3 个字 Then 无法完成驳回 / Given pending When reject reason has 3 chars Then reject cannot complete
