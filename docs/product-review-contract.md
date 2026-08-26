# 产品质量审查契约 / Product Review Contract

> Agent / 人工 eval 的**输出形状**约定。校验形状与报告内部一致性 ≠ 证明语义判断正确。
> 质量维度定义见 [`product-quality-model.md`](product-quality-model.md)；反例见 [`product-review-corpus.md`](product-review-corpus.md)。

## 产出文件

相对案卷根目录：

| 文件 | 用途 |
|------|------|
| `reports/product-review.yaml` | **唯一机读准据**（先写/先改这里） |
| `reports/product-review.md` | 同一报告的人读投影；**不得**独立增加结论或改写 verdict |

写/更新顺序：**先 YAML，再写或更新 MD**，使 MD 的 `PRODUCT_REVIEW`、subject hash、finding id、`gate_note` 与 YAML 一致。本批不要求渲染器；助手按本契约维护投影即可。

默认**不修改**被审文档。需要映射为 machine spec 时走 **normalize / projection**（见下），不得冒充 Draft。

## 顶层字段（YAML）

```yaml
review_version: "1"
subject:
  path: <被审文件路径>
  kind: machine_spec | markdown_prd | other
  content_hash: <sha256 小写 64 hex>   # 被审文件字节哈希；报告只对该 hash 有效
source_fidelity: aligned | partial | unavailable
source_materials: []   # 见下；aligned/partial 至少一项；unavailable 必须 []
model_ref: docs/product-quality-model.md   # 固定值
validity: current | stale
verdict: REVISE | DECISION_NEEDED | REVIEWABLE   # 禁止 PASS
summary:
  zh: <非空中文总评>
findings: []
decisions_needed: []
gate_note:
  zh: Structure Gate 通过不等于产品方案合理。   # 固定原文
```

### subject.content_hash 与 stale

1. 每次写出 Review 时，对**当时**被审文件字节计算 `sha256`，写入 `subject.content_hash`。
2. 报告**只**对该 hash 有效。对外给出 `PRODUCT_REVIEW:` 时，必须 `validity: current` 且磁盘上被审文件哈希仍等于 `subject.content_hash`。
3. 下列任一发生后，旧报告必须标 `validity: stale`（或移出对外路径），**不得**再引用其结论；须对新内容**重新 Review** 后，才能对外给出当前 `PRODUCT_REVIEW`：
   - 被审文档被修改
   - 执行了 normalize / projection（映射产出新机读或改写了被审文件）
   - 产品经理拍板导致的规格修改
4. Structure Gate 结果始终**独立**展示。Gate `PASS` / `DRAFT` **不能**覆盖 stale 或 `REVISE` 的 Product Review。

### source_materials 与 source_fidelity

| `source_fidelity` | `source_materials` | 含义 |
|-------------------|--------------------|------|
| `aligned` / `partial` | **至少一项** `{path, content_hash}` | 本次对照实际打开过的原料快照 |
| `unavailable` | **必须 `[]`** | 没有原始需求材料；只能评内部一致性 |

`source_materials` **只**证明「本次审查对照了哪些快照」，**不**证明原料账本完整或每一句原料都已登记。禁止无 `source_materials` 却声称 `aligned` / `partial`。

## finding 必填字段

| 字段 | 说明 |
|------|------|
| `id` | 稳定编号，如 `F-BOUND-01` |
| `dimension` | `goals_and_core` \| `boundary` \| `architecture` \| `flow` \| `ux` |
| `severity` | `blocker` \| `major` \| `minor` \| `question` |
| `observation` | 观察到什么（中文；界面「」文案；机读 ID 放括号） |
| `evidence` 或 `spec_refs` | 至少其一；`evidence` 若出现必须非空；`spec_refs` 每项非空 |
| `impact` | 若不改，评审或用户会怎样 |
| `direction` | 修订方向（不替产品经理选定唯一商业答案，除非原文已有） |
| `confidence` | `high` \| `medium` \| `low` |
| `requires_decision` | `true` \| `false` |
| `owner` | 可确定时填写；不确定可省略 |

**不**给 finding 增加工作流 `status` 字段。结论只看**当前快照**里的 severity / `requires_decision`。

## 结论汇总规则（报告内部一致性）

1. 当前快照中**任一** `blocker` 或 `major` → 必须 `REVISE`；`REVISE` 至少含一条 `blocker`/`major`
2. 无 `blocker`/`major`，且至少一条 `requires_decision: true` → `DECISION_NEEDED`
3. 无 `blocker`/`major`，且没有任何 `requires_decision: true` → `REVIEWABLE`
4. **禁止** `verdict: PASS` 与正文 `PRODUCT_REVIEW: PASS`

Markdown 投影须含：

```text
PRODUCT_REVIEW: REVISE|DECISION_NEEDED|REVIEWABLE
```

以及与 YAML 一致的 subject `content_hash`、finding `id` 列表、固定 `gate_note`。禁止与 Structure Gate 的 `RESULT:` 合并成一句「全部通过」。

## Normalize / projection（可选）

部门已有文档、需要 Structure Gate 时：

1. 只能提取已有内容，不得优化、补写或发明
2. 缺失写 `pending` / `assumption`
3. 保留原文引用与原料 `content_hash`
4. 映射结果先是 `status: draft`；未经确认不得标 `ready` / 不得宣称终稿 PASS
5. 对外名称必须是 **normalize** 或 **projection**，禁止称为 Draft
6. 映射一旦改写或新写机读，旧 Product Review → `stale`，须对映射结果**重新 Review**
7. 普通 Markdown **未**标准化时，`/gate-spec` 必须说明不满足 hard gate 输入要求，**不得伪造** `RESULT: PASS`

## Schema

形状与内部一致性：`src/specnotary/schemas/product-review.schema.json`。
通过形状校验 ≠ 审查做对了。

## Eval 说明（非 CI 语义证明）

下列无法用确定性单测「证明 LLM 总会发现」：范围与目标不一致、行为与功能名相反、架构过度耦合、可重复提交无防护、UX 命名与反馈不足。

CI 锁：契约存在、Schema 负例、fixture YAML+MD 最小投影一致、入口可发现、文档要求「改后复审 / hash 绑定」。
