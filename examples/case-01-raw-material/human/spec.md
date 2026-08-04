<!-- generated_from: /Users/zhaosi./Documents/Cursor Projects/spec-kit/examples/case-01-raw-material/machine/spec.yaml -->
<!-- gate_mode: hard -->
<!-- DO NOT long-term edit without updating machine source -->

# 书架助手 · 文档搜索与索引重建
# ShelfHelp · Document search & index rebuild

- **ID:** `SPEC-SHELF-001`
- **Status:** `ready`
- **Spec version:** `0.1`

## Scope / 范围

### In scope / 范围内

- 按标题、文档编号模糊搜索 / Fuzzy search by title and document id
- 成员只读；管理员可触发索引重建 / Members read-only; admins can rebuild index

### Out of scope / 范围外

- 全文语义问答 / RAG 回答 / Semantic QA / RAG answers

### Open questions / 待决

- （无 / none）

## Actors & permissions / 角色与权限

- `member`: 成员 / Member
- `admin`: 管理员 / Admin
- `member` can `search, view_result`
- `admin` can `search, view_result, rebuild_index`

## Defaults & empty states / 默认值与空态

```yaml
max_concurrent_rebuilds: 1
page_size: 20
search_fields:
- title
- doc_id
search_match: fuzzy
```
- **no_match:** 没有找到匹配的文档。试试编号或换个关键词。 / No matching documents. Try an id or another keyword.
- **no_permission:** 你没有权限查看该文档。 / You do not have permission to view this document.

## Object AI / 对象 AI

- enabled: `False`

## Behaviors / 行为

### `B1` 搜索文档

- **Given:** 用户已登录且具备 search 权限 / User is signed in with search permission
- **When:** 输入关键词并提交搜索 / User submits a keyword search
- **Then:** 返回匹配列表；字段含 title、doc_id；分页大小默认 20；无匹配展示 no_match 文案 / Return matches with title and doc_id; default page size 20; show no_match copy when empty

### `B2` 重建索引

- **Given:** 用户为 admin，且当前没有进行中的重建任务 / User is admin and no rebuild is running
- **When:** 点击重建索引 / Clicks rebuild index
- **Then:** 创建唯一重建任务；若已有任务则拒绝并提示「已有重建进行中」 / Start the only rebuild job; if one exists, reject with in-progress message

## Acceptance / 验收

- `A1` (B1): Given 成员已登录 When 搜索不存在的关键词 Then 看到 no_match 中文案且不暴露他人私有路径 / Given member signed in When searching a missing keyword Then see no_match copy without leaking private paths
- `A2` (B2): Given 已有重建任务 When admin 再次点击重建 Then 被拒绝且提示进行中 / Given a rebuild is running When admin clicks rebuild again Then reject with in-progress message
