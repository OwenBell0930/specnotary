---
name: write-spec
description: >
  Default full SpecNotary flow: Draft, Product Review bound to subject hash with
  re-review after edits, then Structure Gate. Backward-compatible orchestrator.
---

# Write a SpecNotary spec（默认全流程）

编排器：严格按 `skills/specnotary/SKILL.md`。

1. 若未安装：`pip install "git+https://github.com/OwenBell0930/specnotary.git"`（不必把 SpecNotary 设成工作区）。
2. 依次：原料登记 → Draft → Review（YAML 绑定 `subject.content_hash`，再写 MD）→ 修订/拍板后**标 stale 并重新 Review**（直至当前版本有有效结论）→ Gate → 人读与自检报告。
3. 结束时**分开展示**：`DRAFT_STATUS`、`PRODUCT_REVIEW`（仅 current 且 hash 匹配）、`STRUCTURE_GATE`/`RESULT`、待拍板事项。禁止用 Gate PASS 覆盖 stale/`REVISE`；禁止 `PRODUCT_REVIEW: PASS`。
4. 对产品经理只问：还缺什么原料、结果对不对、哪些要拍板、评审材料在哪。
5. 不要让她操作内部工具或改内部文件。

单能力入口：

- `/draft-spec` → `skills/specnotary-draft/SKILL.md`
- `/review-spec` → `skills/specnotary-review/SKILL.md`
- `/gate-spec` → `skills/specnotary-gate/SKILL.md`
