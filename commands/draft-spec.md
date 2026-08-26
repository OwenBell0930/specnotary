---
name: draft-spec
description: >
  Draft-only SpecNotary. Produce a candidate machine spec from raw material.
  Do not self-score quality; do not run Review or Gate.
---

# Draft a SpecNotary candidate（仅起草）

1. 若未安装：`pip install "git+https://github.com/OwenBell0930/specnotary.git"`。
2. 严格按 `skills/specnotary-draft/SKILL.md`。
3. 质量组织标准只引用 `docs/product-quality-model.md`，禁止复制第二套。
4. 交候选稿与假设/未决清单后**停止**。不自动 Review/Gate。
5. 对外：`DRAFT_STATUS: CANDIDATE`。不要宣称质量通过或终稿 PASS。
6. 对产品经理只问缺什么原料、原型是否做；不要让她跑内部命令。
