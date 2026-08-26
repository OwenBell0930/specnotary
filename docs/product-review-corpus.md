# 产品质量审查反例语料 / Product Review Corpus

> 这些方案可以**结构合法**（Schema、引用、空话词表均可能过 Structure Gate），但 Product Review **必须**指出问题。
> 用于人工 / Agent eval 校准，**不是**硬门禁词表。不要为「LLM 一定找得到」伪造单元测试 PASS。

质量维度见 [`product-quality-model.md`](product-quality-model.md)。

## 使用方式

1. Review 前先读本语料，确认五类坏味道都在检查清单里。
2. Eval 时：给助手结构合法的坏稿（或下列摘要），期望产出含对应 `dimension` / `severity` 的 finding，且 `PRODUCT_REVIEW` ≠ 沉默通过。
3. 同时可对同一坏稿跑 `specnotary check`：允许 `STRUCTURE_GATE: PASS` 或 `RESULT: DRAFT`，并在报告中写明 **Gate 通过 ≠ 产品方案合理**。

---

## ANTI-01 · 范围与目标不一致（goals_and_core / boundary）

**摘要：** `in_scope` / 标题只写「调整列表页按钮颜色」，正文却定义完整商品搜索（关键词、筛选、分页、空态、权限）。

| 期望 | 值 |
|------|----|
| dimension | `goals_and_core` 和/或 `boundary` |
| severity | `blocker` 或 `major` |
| 要点 | 目标与方案体量不符；要么改范围陈述，要么砍掉搜索能力 |

Structure Gate：若字段齐全、无空话，**可以**结构通过。

---

## ANTI-02 · 行为与功能语义相反（flow / goals_and_core）

**摘要：** 功能名叫「搜索商品」，`when` 是提交关键词，`then` 却是删除全部商品并提示「搜索成功」。

| 期望 | 值 |
|------|----|
| dimension | `flow`（可兼 `goals_and_core`） |
| severity | `blocker` |
| 要点 | 可观察结果与用户任务相反；不可标成已评审通过 |

Structure Gate：给定/当/则句子具体且无词表命中时，**可以**结构通过。

---

## ANTI-03 · 架构过度耦合（architecture）

**摘要：** 检索、下单、退款、客服会话、运营配置全部塞进同一个「通用工作台页面」，无对象归属与模块边界。

| 期望 | 值 |
|------|----|
| dimension | `architecture` |
| severity | `major` 或 `blocker` |
| 要点 | 页面/模块层级与对象生命周期混乱；扩展点与耦合失控 |

Structure Gate：有一份 `architecture.mermaid` 且职责字段语法合法时，**可以**结构通过。

---

## ANTI-04 · 检索中允许无限重复提交（flow / ux）

**摘要：** 检索进行中「搜索」按钮始终可点；每次点击新开请求，无取消、无合并、无频控；结果顺序与加载态未定义。

| 期望 | 值 |
|------|----|
| dimension | `flow` 和/或 `ux` |
| severity | `major` |
| 要点 | 重复提交、竞态与反馈缺失 |

Structure Gate：行为条数够、控件有文案时，**可以**结构通过。

---

## ANTI-05 · UX 命名与反馈不足（ux）

**摘要：** 唯一主按钮文案为「确定」；始终可连点；失败时页面只显示「失败」，无原因、无重试、无恢复路径。

| 期望 | 值 |
|------|----|
| dimension | `ux` |
| severity | `major`（连点导致重复业务时可为 `blocker`） |
| 要点 | 命名无任务上下文；错误预防与恢复不足 |

Structure Gate：控件与空态字段存在且非占位词时，**可以**结构通过。

---

## 报告口径（验收 F）

审查报告必须同时写清：

1. 上列问题已被 Product Review 指出（对应 finding）。
2. 若 Structure Gate 结构通过，加一句：**Structure Gate 通过不等于产品方案合理。**
3. 最终分开展示 Draft / Product Review / Structure Gate / 待拍板事项，不合并成单一「PASS」。
