---
name: specnotary-review
description: >
  Independent SpecNotary product-quality review. Reviews machine specs or
  existing PRD/Markdown against the shared product quality model. Binds the
  report to subject content_hash; marks stale after subject changes and
  re-reviews before quoting PRODUCT_REVIEW. Default: do not modify the subject.
---

# SpecNotary Review（产品质量审查）

**只做审查。** 默认不修改被审文档；不替产品经理拍板；不宣布 Structure Gate 结果（除非用户另行要求 Gate）。

公共标准（唯一）：[`docs/product-quality-model.md`](../../docs/product-quality-model.md)。
输出形状：[`docs/product-review-contract.md`](../../docs/product-review-contract.md)。
反例校准：[`docs/product-review-corpus.md`](../../docs/product-review-corpus.md)。

「独立」指能力与结论可单独调用/展示；默认同一助手顺序执行 ≠ 组织上或模型上下文上的独立审查者。需要真正审查者独立时，在**新上下文**单独调用 `/review-spec` 或人工复核。

## 输入

任选其一或组合：

- SpecNotary machine spec（YAML/JSON）
- 普通已有 PRD / Markdown
- 可选：原始需求材料（用于源保真；没有则必须 `source_fidelity: unavailable` 且 `source_materials: []`）

## 输出

先写 **YAML（唯一机读准据）**，再写/更新 **MD（人读投影，不得独立加结论）**：

- `reports/product-review.yaml`
- `reports/product-review.md`

必填要点：

- `subject.content_hash`：被审文件 sha256（小写 64 hex）；报告**只对该 hash 有效**
- `validity: current`（写出时）；磁盘文件哈希仍匹配才可对外引用
- `source_materials`：本次实际对照的原料快照；`aligned`/`partial` 至少一项；`unavailable` 必须 `[]`
- `model_ref: docs/product-quality-model.md`
- `gate_note.zh` 固定为：`Structure Gate 通过不等于产品方案合理。`
- 结论：`PRODUCT_REVIEW: REVISE|DECISION_NEEDED|REVIEWABLE`（禁止 PASS）

当前快照中任一 `blocker`/`major` → `REVISE`（不为 finding 增加 status 字段）。

## 停止边界

1. 写出与当前 subject hash 绑定的 YAML+MD 后停止（除非用户明确要求接着 Gate 或修订）
2. **默认不改**被审文档
3. 不自动 `confirm`、不自动把 `pending` 标成已决
4. 无原料时只评内部一致性 / 架构 / 流程 / UX，并标 `source_fidelity: unavailable`
5. 不把语义判断写进 Python CLI，不调用 LLM 后声称 deterministic hard gate

## 审查步骤

1. 读被审文件，计算 `content_hash`，记录 `kind`
2. 登记本次打开的原料到 `source_materials`（或确认 unavailable + `[]`）
3. 按五维检查；对照反例语料 ANTI-01…ANTI-05
4. 按契约汇总 `verdict` / `decisions_needed`（与 findings 结构一致）
5. **先写 YAML**（`validity: current`），再写 MD 投影
6. 用人话向产品经理复述必须改 / 需要拍板的项

## 修订后必须重新 Review

下列任一发生后：将被审文档修改、normalize/projection、或产品经理拍板改规格 → 旧报告标 `validity: stale`，**禁止**再用其 `PRODUCT_REVIEW`；对新内容重新走本 Skill。Gate PASS **不能**覆盖 stale 或 `REVISE`。

## 可选：normalize / projection

仅当用户明确要求映射以送入 Structure Gate 时：只提取、不发明；结果 draft；称 normalize/projection 不称 Draft；映射后旧 Review → stale，并对映射结果重新 Review。

## 硬性禁止

- `PRODUCT_REVIEW: PASS`
- 无 `source_materials` 声称 `aligned`/`partial`
- 对被审文件已变仍引用旧 hash 的结论
- 静默重写方案冒充「已修好」
- 复制第三套质量标准
- 扩展到实现/测试/交付管理
