<!-- generated_from: examples/case-order-cancel-bad/machine/spec.fixed.yaml -->
<!-- gate_mode: hard -->
<!-- DO NOT long-term edit without updating machine source -->

# 电商订单 · 未发货自助取消
# Commerce order · Buyer self-cancel before shipment

- **ID:** `SPEC-ORDER-CANCEL-001`
- **Status:** `ready`
- **Spec version:** `0.1`

## Scope / 范围

### In scope / 范围内

- 待支付订单买家自助取消 / Buyer self-cancel for unpaid orders
- 已支付未发货订单买家自助取消并原路退款、库存回库 / Buyer self-cancel for paid-unshipped orders with original-path refund and inventory release
- 履约中/已发货不可自助取消（引导售后或客服） / Fulfilling/shipped orders cannot self-cancel (route to after-sales/CS)

### Out of scope / 范围外

- 部分取消、改收货地址、跨境税费、订阅购 / Partial cancel, address change, cross-border tax, subscriptions

### Open questions / 待决

- （无 / none）

## Actors & permissions / 角色与权限

- `buyer`: 买家 / Buyer
- `seller_ops`: 商家运营 / Seller ops
- `cs_agent`: 客服 / Customer service
- `risk_engine`: 风控引擎 / Risk engine
- `buyer` can `cancel_unpaid, cancel_paid_unshipped`
- `cs_agent` can `force_cancel_with_reason`
- `seller_ops` can `view_cancel_logs`

## Defaults & empty states / 默认值与空态

```yaml
coupon_release_on_unpaid_cancel: true
inventory_release: immediate_on_cancel_success
refund_path: original
refund_visible_sla_hours: 2
risk_block_self_cancel: true
```
- **not_allowed:** 当前订单状态不支持自助取消，请联系客服或去售后中心 / This order cannot be self-cancelled. Contact CS or use after-sales.
- **risk_blocked:** 订单存在风险控制，暂不可自助取消 / Risk controls block self-cancel for this order.
- **refund_pending:** 取消成功，退款处理中，预计可在 2 小时内查询到账进度 / Cancelled. Refund in progress; status visible within 2 hours.

## Object AI / 对象 AI

- enabled: `False`

## Behaviors / 行为

### `B1` 取消待支付订单

- **Given:** 买家登录且订单状态=unpaid，风控未拦截 / Buyer signed in, order=unpaid, not risk-blocked
- **When:** 买家确认取消 / Buyer confirms cancel
- **Then:** 订单→cancelled；释放已锁优惠券；不产生退款单；库存若预占则释放 / Order→cancelled; release locked coupon; no refund slip; release held inventory if any

### `B2` 取消已支付未发货订单

- **Given:** 订单状态=paid_unshipped，风控未拦截，买家为下单人 / Order=paid_unshipped, not risk-blocked, actor is order owner
- **When:** 买家确认取消 / Buyer confirms cancel
- **Then:** 订单→cancelled；创建原路退款单；库存立即回库；页面展示 refund_pending 文案；2 小时内退款进度可查 / Order→cancelled; original-path refund created; inventory released now; show refund_pending; refund progress visible within 2h

### `B3` 履约中拦截自助取消

- **Given:** 订单状态=fulfilling 或 shipped / Order is fulfilling or shipped
- **When:** 买家点击取消 / Buyer taps cancel
- **Then:** 不改变订单状态；展示 not_allowed；提供客服/售后入口 / No state change; show not_allowed; offer CS/after-sales entry

## Acceptance / 验收

- `A1` (B1): Given unpaid 订单 When 取消成功 Then 状态为 cancelled 且无退款单且优惠券可再次使用 / Given unpaid order When cancel succeeds Then status cancelled, no refund slip, coupon reusable
- `A2` (B2): Given paid_unshipped When 取消成功 Then 库存 SKU 可用量 +1（单件单）且退款单存在且路径=original / Given paid_unshipped When cancel succeeds Then inventory +1 for single-qty order and refund slip exists with path=original
- `A3` (B3): Given fulfilling When 点击取消 Then 仍为 fulfilling 且看到 not_allowed / Given fulfilling When tapping cancel Then still fulfilling and see not_allowed
