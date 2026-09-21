---
name: specnotary
description: >
  Default SpecNotary full-flow orchestrator: Draft, Product Review bound to
  subject hash with re-review after edits, then Structure Gate. Use for
  /write-spec; single capabilities use draft/review/gate skills.
---

# SpecNotary Skill（默认全流程编排）

产品经理只做三件事：**交出原料、确认结果、拿材料去评审**。检查步骤由你来跑。

**产品边界：** 需求原料 → 产品方案与标准文档 → 产品质量审查 → 确定性门禁 → 需求评审。
到评审材料交付即停止；不要产出开发语言、框架、实现任务、测试策略、覆盖率或交付证据。

**一个项目、一个品牌、一套公共质量模型**，三项能力可单独调用；本 Skill 是默认编排器。

| 能力 | Skill | Command | 单独调用时 |
|------|-------|---------|------------|
| Draft | [`skills/specnotary-draft/SKILL.md`](../specnotary-draft/SKILL.md) | `/draft-spec` | 只交候选稿，不自动 Review/Gate |
| Review | [`skills/specnotary-review/SKILL.md`](../specnotary-review/SKILL.md) | `/review-spec` | 只出审查报告，默认不改原文 |
| Gate | [`skills/specnotary-gate/SKILL.md`](../specnotary-gate/SKILL.md) | `/gate-spec` | 只跑结构门禁；普通 Markdown 不得 hard PASS |
| 全流程 | 本文件 | `/write-spec` | 下表顺序 |

公共质量模型：[`docs/product-quality-model.md`](../../docs/product-quality-model.md)。
审查契约（含 subject hash / stale / 复审）：[`docs/product-review-contract.md`](../../docs/product-review-contract.md)。
证明边界：[`docs/proof-boundary.md`](../../docs/proof-boundary.md)。

「独立审查」= 能力与结论可独立调用/展示。默认同一助手顺序编排 ≠ 组织或上下文上的独立审查者；需要时在新上下文单独 `/review-spec` 或人工复核。

产品管理部门可**跳过 Draft**，对已有文档只跑 Review + Gate（见「已有文档路径」）。

## 安装

不必把 SpecNotary 设成当前工作区。规格写在用户已打开的文件夹即可。

```bash
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'
pip install "git+https://github.com/OwenBell0930/specnotary.git"
```

无 Python ≥3.10 时：Gate 只能 `gate_mode: degraded`，不得冒充 hard PASS。

## 默认全流程（/write-spec）

严格按序，且**最终分开展示**四块状态（禁止合并成一句「全部通过」）：

1. **原料登记** — `specnotary new` / `ingest` 钉哈希
2. **Draft** — 按 `specnotary-draft` 起草候选稿；源外标 assumption/pending/decision；**Draft 不自评质量通过**
3. **Review** — 按 `specnotary-review` 审查；先写 `reports/product-review.yaml`（含 `subject.content_hash`），再写 `.md`；`validity: current`
4. **修订 / 拍板循环** — 有证据则改规格；`requires_decision` 询问产品经理（不替她拍板）。**每次**被审文档变更后：旧 Review → `stale`，**必须重新 Review**，直至**当前**文件 hash 上有可对外引用的结论（且非在应复审却未复审的 stale 状态）
5. **Gate** — 仅在当前版本已有有效 Product Review 结论之后，按 `specnotary-gate` 跑 `check` / 需要时 `sync` / `confirm` / `report`。Gate PASS **不能**覆盖 stale 或 `REVISE`
6. **交付** — 人读说明书 + 输出自检报告 + **当前**产品审查报告，供需求评审

结束时必须列出：

```text
DRAFT_STATUS: ...
PRODUCT_REVIEW: REVISE|DECISION_NEEDED|REVIEWABLE   # 仅 validity:current 且 hash 匹配
STRUCTURE_GATE / RESULT: FAIL|DRAFT|PASS
待拍板事项: ...
```

并写明：Structure Gate 通过不等于产品方案合理。

```bash
specnotary new <case-dir> --from <raw-file> [--kind ops|prd|faq|speckit|ticket|raw] [--id]
# Draft …
# Review → reports/product-review.* （绑定 content_hash）…
# 若修订/拍板 → 标 stale → 重新 Review …
specnotary check <machine.yaml> --explain
specnotary sync <machine.yaml>
specnotary confirm <machine.yaml> --by <name> --reason "<why>" --accept-all-warn
specnotary report <machine.yaml>
```

GitHub spec-kit / OpenSpec 的 `spec.md` **不要一键转 YAML**。登记为原料：

```bash
specnotary ingest <spec.md> --spec <machine.yaml> --kind speckit
```

## 已有文档路径（跳过 Draft）

```text
已有文档 → Review（绑定 hash）→（可选 normalize/projection → stale → 重新 Review）→ Gate → 需求评审
```

- Review 默认不改原文；先 YAML 后 MD
- normalize/projection：只提取、不发明；draft；不得称 Draft；之后必须重新 Review
- 未标准化 Markdown：Gate 拒绝 hard PASS
- 对外 PRODUCT_REVIEW 必须对应当前 subject hash；Gate 结论独立展示

## Rules

1. **Machine source is authoritative.** Edit YAML first; generate the human 评审就绪标准需求规格说明书 from it.
2. Prefer **YAML**. Ready review view must include product/information architecture, module boundaries, business data contracts and product error definitions, plus wireframe/controls/state-action/behaviors/AC/Pending as applicable. Draft 先定边界与对象，再定页面归属，最后以 `behaviors` 写功能契约；复杂写入按风险补对象读写、异常、幂等、恢复、权限和验收引用。Never turn them into technical architecture, implementation tasks, or test plans.
3. Before claiming a final Structure Gate `PASS`: status must be `ready` and **FAIL must be 0**. `RESULT: DRAFT` 只表示可带问题评审，不是终稿。Remaining WARN: ask the product manager；then **you** run `specnotary confirm`. 对她不要只说 WARN / FAIL / PASS。
4. Hard gate runtime is **Python only**. Node CLI is Deferred — exit 3; never `gate_mode: hard` / `RESULT: PASS`.
5. If no Python: degraded Skill check with `gate_mode: degraded` only.
6. Never long-term edit only the human doc. After machine edits run `specnotary sync`.
7. Do not copy proprietary scaffold/business PRDs into the SpecNotary product tree; fictional examples only.
8. Use `states.action_matrix` (`state` / `action` / `allowed`); `cancel_matrix` is legacy.
9. Single product goal: **review-ready product requirements**. Every case must record `D-PROTOTYPE` before `ready`.
10. For drafts, use `specnotary check --explain` for READY-GAP.
11. **CLI does not understand natural language.** `new` / `ingest` only pin files. You extract claims. Empty-talk: [`docs/empty-talk-corpus.md`](../../docs/empty-talk-corpus.md).
12. **假详细分两层。** 已知结构/词表问题由 Structure Gate；语义错配由 Product Review。禁止把语义判断写进 hard gate。
13. **人读正文用中文。** 见 [`docs/human-view.md`](../../docs/human-view.md)。跟人指路写带真实空格的绝对路径。
14. **Draft 不自评；改后必须复审；Gate 不做产品质量语义；三套结论不得合并。**

## 写作主路径（Draft 段）

`specnotary new` 只给脚手架和已钉哈希的原料。你补全原料账本与 `D-PROTOTYPE`，按「边界与复用基线 → 对象契约 → 页面/消费者视图 → 功能契约 → 异常恢复/权限/验收」组织单一机读规格、按需原型，然后交由 Review（含修订复审循环），再 Gate。不要在 Draft 段结束时宣称质量通过。

## 提取 SourceClaim

每条 claim：`id`、`source_ref`、`quote_or_summary` 或 `evidence`、`disposition`；`covered` 必须带真实 `spec_refs`。源外推断标 `assumption`。

## 已选择生成原型时必须同步 Manifest

`prototype/prototype.manifest.yaml` + `data-spec-id`；改机读后须显式 `sync --attest-prototype`。改机读也使 Product Review stale。
