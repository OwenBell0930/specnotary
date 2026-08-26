---
name: gate-spec
description: >
  SpecNotary structure gate only. Run Python CLI check/report/sync. Plain
  Markdown without normalize must not get a hard PASS. Gate PASS cannot override
  a stale or REVISE Product Review.
---

# Run the structure gate（仅门禁）

1. 严格按 `skills/specnotary-gate/SKILL.md`。
2. 合法输入：machine spec。运行 `specnotary check`（需要时 `sync` / `report` / `confirm`）。
3. 普通 Markdown / 未标准化 PRD：**说明不满足 hard gate 输入要求**，不得伪造 `RESULT: PASS`。可建议先 `/review-spec`，再可选 normalize/projection（之后须重新 Review）。
4. Gate 不判断商业边界、架构可扩展性、现实流程或 UX 优劣；不得用 LLM 冒充 hard。
5. 输出 `RESULT: FAIL|DRAFT|PASS`（及 STRUCTURE_GATE / READY_GAP 若有），与 Product Review **分开**展示；Gate PASS 不能覆盖 stale/`REVISE`。
6. 写明：Structure Gate 通过不等于产品方案合理。
7. 不要让产品经理自己操作 CLI。
