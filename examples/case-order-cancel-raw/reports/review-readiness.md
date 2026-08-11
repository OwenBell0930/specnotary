# 评审就绪报告 / Review-readiness report

- 机读：`examples/case-order-cancel-raw/machine/spec.yaml`
- 规格 ID：`SPEC-ORDER-CANCEL-001` · 状态：`ready`
- 机读哈希：`14a562b5f4e57d6cc93ea17fd42d00fae14dc2590871e0cdf23ff79408e45986`
- 人读：`/Users/zhaosi./Documents/Cursor Projects/spec-kit/examples/case-order-cancel-raw/human/spec.md`
- FAIL：0 · WARN：0

## 原料覆盖汇总

| 处置 | 条数 |
|------|------|
| `covered` | 4 |
| `omitted` | 0 |
| `assumption` | 0 |
| `conflict` | 0 |
| `out_of_scope` | 1 |
| `pending` | 0 |
| `undisposed` | 0 |

## 明细

| ID | 处置 | 摘要 | 引用 / 闭合 |
|----|------|------|-------------|
| SRC-CLM-001 | covered | 待支付订单取消后应关闭，并释放优惠券（若已锁定） | B1, AC-01 |
| SRC-CLM-002 | covered | 已支付未发货取消后须原路退款、库存回库，2小时内退款状态可查 | B2, AC-02, AC-03 |
| SRC-CLM-003 | covered | 履约中买家不可自助取消，只能联系客服 | B3, AC-04 |
| SRC-CLM-004 | covered | 风控命中订单禁止自助取消 | B4, AC-05 |
| SRC-CLM-005 | out_of_scope | 部分取消、改地址、跨境税、订阅购不在本期 | — |

## 门禁

**RESULT: PASS**
