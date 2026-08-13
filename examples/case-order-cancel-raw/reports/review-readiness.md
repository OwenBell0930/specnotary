# 评审就绪报告 / Review-readiness report

- 机读：`examples/case-order-cancel-raw/machine/spec.yaml`
- 规格 ID：`SPEC-ORDER-CANCEL-001` · 状态：`ready`
- 机读哈希：`fc0cc2a042ab1180648dd08570b42a9970eb296ad80ec28f6a9bb20f03c635d6`
- 人读：`examples/case-order-cancel-raw/human/spec.md`
- 原型：`examples/case-order-cancel-raw/prototype/prototype.manifest.yaml`
- FAIL：0 · WARN：6

## 原料覆盖汇总

| 处置 | 条数 |
|------|------|
| `covered` | 6 |
| `omitted` | 0 |
| `assumption` | 0 |
| `conflict` | 0 |
| `out_of_scope` | 1 |
| `pending` | 0 |
| `undisposed` | 0 |

## 明细

| ID | 处置 | 摘要 | 引用 / 闭合 |
|----|------|------|-------------|
| SRC-CLM-001 | covered | 待支付订单取消后应关闭，并释放优惠券（若已锁定） | B1, AC-01, btn_cancel, dlg_confirm_title, dlg_confirm_ok, dlg_confirm_cancel |
| SRC-CLM-002 | covered | 已支付未发货取消后须原路退款、库存回库，2小时内退款状态可查 | B2, AC-02, AC-03, btn_cancel |
| SRC-CLM-003 | covered | 履约中买家不可自助取消，只能联系客服 | B3, AC-04, btn_cancel_disabled |
| SRC-CLM-004 | covered | 风控命中订单禁止自助取消 | B4, AC-05 |
| SRC-CLM-005 | out_of_scope | 部分取消、改地址、跨境税、订阅购不在本期 | — |
| SRC-CLM-006 | covered | 背景与痛点：日单量约 8 万；客服被「点错想取消」工单淹没；库存被无效占用 | B1, B2, D-01 |
| SRC-CLM-007 | covered | 已发货走售后，不在本期 | B3, D-02 |

## 门禁

**RESULT: PASS**
- WARN: permission buyer: can=cancel_unpaid is not an action in states.action_matrix — confirm it is a capability label, not a state-machine action
- WARN: permission buyer: can=cancel_paid_unshipped is not an action in states.action_matrix — confirm it is a capability label, not a state-machine action
- WARN: permission buyer: can=view_refund_progress is not an action in states.action_matrix — confirm it is a capability label, not a state-machine action
- WARN: permission cs_agent: can=force_cancel_with_reason is not an action in states.action_matrix — confirm it is a capability label, not a state-machine action
- WARN: permission seller_ops: can=view_cancel_logs is not an action in states.action_matrix — confirm it is a capability label, not a state-machine action
- WARN: permission risk_engine: can=flag_block_self_cancel is not an action in states.action_matrix — confirm it is a capability label, not a state-machine action
