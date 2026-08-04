<!-- generated_from: examples/case-02-bad-prd/machine/spec.fixed.yaml -->
<!-- gate_mode: hard -->
<!-- DO NOT long-term edit without updating machine source -->

# 工单列表搜索
# Ticket list search

- **ID:** `SPEC-TICKET-001`
- **Status:** `ready`
- **Spec version:** `0.1`

## Scope / 范围

### In scope / 范围内

- 按工单标题、工单号模糊搜索 / Fuzzy search by ticket title and ticket id
- 管理员与处理人可搜全量；只读访客仅搜自己可见工单 / Admin/assignee search all visible; readonly guest only own-visible tickets

### Out of scope / 范围外

- 用大模型改写查询或自动结单 / LLM query rewrite or auto-close

### Open questions / 待决

- （无 / none）

## Actors & permissions / 角色与权限

- `admin`: 管理员 / Admin
- `agent`: 处理人 / Agent
- `guest`: 只读访客 / Readonly guest
- `admin` can `search_all`
- `agent` can `search_all`
- `guest` can `search_own_visible`

## Defaults & empty states / 默认值与空态

```yaml
debounce_ms: 300
page_size: 20
search_fields:
- title
- ticket_id
search_match: fuzzy
```
- **no_match:** 没有符合条件的工单 / No tickets match your filters
- **forbidden:** 无权查看该工单 / Not allowed to view this ticket

## Object AI / 对象 AI

- enabled: `False`

## Behaviors / 行为

### `B1` 搜索工单

- **Given:** 用户已登录 / User signed in
- **When:** 在搜索框输入至少 1 个字符并等待 debounce / Types at least 1 character and waits for debounce
- **Then:** 按权限返回列表；默认 20 条；无匹配展示 no_match；越权展示 forbidden / Return list by permission; default 20; no_match / forbidden copy as applicable

## Acceptance / 验收

- `A1` (B1): Given guest When 搜索他人私有工单号 Then 不返回该工单正文并展示 forbidden 或相当于未命中的安全空态（二选一须在实现前锁定，本例锁定为 forbidden） / Given guest When searching another user's private ticket id Then do not return body and show forbidden
- `A2` (B1): Given agent When 搜索无匹配词 Then 2 秒内展示 no_match（P95） / Given agent When searching with no hits Then show no_match within 2s P95
