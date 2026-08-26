---
name: review-spec
description: >
  SpecNotary product-quality review for a machine spec or existing PRD/Markdown.
  Bind report to subject content_hash; re-review after any subject change.
  Default: do not modify the subject. Write YAML then Markdown projection.
---

# Review product quality（仅审查）

1. 严格按 `skills/specnotary-review/SKILL.md`。
2. 唯一质量标准：`docs/product-quality-model.md`；契约：`docs/product-review-contract.md`；反例：`docs/product-review-corpus.md`。
3. 支持 machine spec 与普通 PRD/Markdown。默认**不修改**被审文档。
4. **先**写 `reports/product-review.yaml`（含 `subject.content_hash`、`source_materials`、`validity`），**再**写 `reports/product-review.md`（投影，不得独立加结论）。
5. 结论只能是 `PRODUCT_REVIEW: REVISE|DECISION_NEEDED|REVIEWABLE`（禁止 PASS）；对外仅当 `validity: current` 且磁盘 hash 匹配。
6. 无原料时必须 `source_fidelity: unavailable` 且 `source_materials: []`。
7. 被审文档修改、normalize/projection、拍板改规格后：旧报告 `stale`，必须重新 Review。Gate PASS 不能覆盖。
8. 报告写明：Structure Gate 通过不等于产品方案合理。
