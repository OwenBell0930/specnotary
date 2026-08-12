<!-- generated_from: examples/case-list-search/machine/spec.yaml -->
<!-- spec_id: SPEC-LIST-SEARCH-001 -->
<!-- spec_version: 0.1 -->
<!-- spec_hash: bdd58eafb2f2f61c4c44844f613da83e57b5cfebceda8ecc7f9153822a2d4897 -->
<!-- body_hash: 635111c645b012954ff826dcb0f2c1d5b9bde66bc0867595d1ab8982d5a040cd -->
<!-- gate_mode: hard -->
<!-- 以机读 YAML 为唯一准据；禁止长期只改本文件 -->
# 商品列表 · 标题/ID 搜索

> **文档类型**：可开发的需求规格说明书（人读视图）  
> **规格 ID**：`SPEC-LIST-SEARCH-001` · **状态**：`ready` · **版本**：`0.1`  
> **机读哈希**：`bdd58eafb2f2f61c…`

**EN title:** Product list · Title/ID search

## 1. 范围

### 1.1 本期做

- 按商品标题模糊匹配
- 按商品 ID 精确匹配
- 空结果展示固定文案

### 1.2 本期不做（白名单外，不展开）

- 语义检索、同义词扩展、跨店聚合

**对照基线：** 虚构自营商城后台商品列表（不含向量检索）

## 2. 角色与权限

| 角色 | 说明 | 可执行动作 |
|------|------|------------|
| `merchant_ops` | 商家运营 | search_own_products |
| `platform_admin` | 平台管理员 | search_all_products |

## 3. 状态与允许动作

**生命周期（编号供流程对照）：**
1. `idle`
2. `searching`
3. `results`
4. `empty`

| 状态 | 动作 | 是否允许 | 说明 |
|------|------|----------|------|
| `idle` | `submit_search` | 允许 | 可提交关键词 |
| `searching` | `submit_search` | 禁止 | 请求进行中，按钮置灰 |
| `results` | `submit_search` | 允许 | 可再次搜索 |
| `empty` | `submit_search` | 允许 | 可修改关键词重试 |

## 4. 页面与交互

**入口：** 商品列表页顶部搜索栏

### 4.1 线框

```text
┌─ 商品列表 ────────────────────────────┐
│ [关键词________] [搜索]               │
│ 结果表… / 空态文案                    │
└───────────────────────────────────────┘
```

### 4.2 控件规格

| 控件 | 文案/占位 | 显示条件 | 交互 | 失败反馈 |
|------|-----------|----------|------|----------|
| inp_keyword | 请输入标题或商品 ID | 始终 | 输入 | — |
| btn_search | 搜索 | 始终；searching 时置灰 | 提交搜索 | 搜索失败，请稍后重试 |

## 5. 主路径（编号）

### 步骤 1 · 标题模糊搜索

- **Given：** 运营在商品列表页，列表有数据
- **When：** 输入标题片段并点击搜索
- **Then：** 返回标题包含关键词的商品，按更新时间倒序，每页 20 条

### 步骤 2 · 空结果

- **Given：** 关键词无匹配
- **When：** 点击搜索
- **Then：** 列表为空，展示文案「无匹配商品，请调整关键词」

## 6. 默认值与提示文案

### 6.1 默认值

| 项 | 值 |
|----|----|
| `page_size` | `20` |
| `match_mode` | `fuzzy_title_or_exact_id` |
| `max_keyword_len` | `64` |

### 6.2 空态 / 拦截文案（须与界面一致）

| 场景 | 文案 |
|------|------|
| `no_match` | 无匹配商品，请调整关键词 |
| `keyword_too_long` | 关键词最长 64 字 |

## 7. 验收标准（AC）

- **AC-01**（行为 `B1`）：输入「蓝牙」可看到标题含「蓝牙」的商品行
- **AC-02**（行为 `B2`）：输入不存在关键词时页面展示固定空态文案

## 8. 信息待闭合项（Pending）

无。

## 9. 对象 AI

- enabled: `False`

## 10. 原料覆盖（SourceClaim）

| ID | 处置 | 摘要 | 规格引用 |
|----|------|------|----------|
| `SRC-CLM-LS-01` | `covered` | 按标题模糊搜、按商品 ID 精确搜 | `B1`, `AC-01`, `inp_keyword`, `btn_search` |
| `SRC-CLM-LS-02` | `covered` | 无匹配时展示固定空态文案 | `B2`, `AC-02` |
| `SRC-CLM-LS-03` | `out_of_scope` | 不做语义检索 | — |
| `SRC-CLM-LS-04` | `assumption` | 默认每页 20 条（原料未写死，产品补默认） | `defaults.page_size` |
