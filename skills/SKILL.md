---
name: specanvil
description: >
  Use when the user works on SpecAnvil / 规格工程 / machine-first specs.
---

# SpecAnvil Skill（辅）

主载体是 **Python CLI + 模板脚手架**。此 Skill 负责起草机读与无运行时的降级检查。

## Rules

1. **Machine source is authoritative.** Edit YAML first; generate human 可开发的需求规格说明书 from it.
2. Prefer **YAML**. Human view must include wireframe, controls table, state/action matrix, numbered steps, AC, Pending five-fields.
3. Before claiming PASS: run `specanvil check` (or `./cli/run-check.sh`) — **FAIL must be 0**; WARN should be cleared or explicitly accepted.
4. Hard gate runtime is **Python only**. Node CLI is Deferred — it exits 3 and must never print `gate_mode: hard` / `RESULT: PASS`.
5. If no Python: degraded Skill check with `gate_mode: degraded` only.
6. Never long-term edit only the human doc. Generator refuses to write when machine has FAIL (unless `--allow-invalid`). After machine edits run `specanvil sync` to refresh the hash chain.
7. Do not copy proprietary scaffold/business PRDs into the product tree; fictional examples only.
8. Use `states.action_matrix` (`state` / `action` / `allowed`); `cancel_matrix` is legacy.
9. Dual goals: **dev-ready** specs + **review-ready** intake. Prototype check runs only when a manifest exists; otherwise WARN and skip.
10. For drafts, use `specanvil check --explain` to enumerate the READY-GAP instead of guessing.

## 提取 SourceClaim（Skill 职责）

CLI **不读懂**任意自然语言。Skill 从 `inputs/` 拆原子项，写入机读 `sources` + `source_claims`。

每条 claim 必须有：

- `id`、`source_ref`（指向 `sources[].id`，且 `sources[].path` 必须真实存在）
- `quote_or_summary` 或 `evidence`（证据位置：文件 + 行/段落）
- `disposition`：`covered` | `omitted` | `assumption` | `conflict` | `out_of_scope` | `pending`
- `covered` 必须带 `spec_refs`，且只能指规格实体（behavior / AC / 控件 / `defaults.x` / `empty_states.x`）

ready 的硬要求：至少 1 条 `covered`；每个必选 behavior/AC/control 都被某条 claim 引用（`coverage_optional: true` 可豁免）。

然后跑：

```bash
specanvil check <machine.yaml>
specanvil human <machine.yaml> <human.md>
specanvil report <machine.yaml> [report.md]
```

## 生成原型时必须同步 Manifest（Skill 职责）

CLI **不解析任意前端框架**。Agent 生成可演示原型时必须同时写 `prototype/prototype.manifest.yaml`。

- 每个业务控件加稳定标记：`data-spec-id="<机读控件或行为 ID>"`（写进真实 DOM/JSX，注释不算）
- 存量项目先跑 `specanvil markers <machine.yaml> <源码目录>` 对账缺哪些标记，回填后再写 manifest
- `generated_from_spec.hash` = 当前机读 `spec_hash`（`specanvil check` 会打印；改机读后用 `specanvil sync` 自动刷新）
- 规格里未标 `prototype_optional` 的控件 / 行为必须映射
- 无规格引用的控件/交互 → FAIL（仅 `role: decoration|visual` 豁免）；interaction 的 `from/to/trigger` 必须指向已声明的 id
- LLM 对截图/文案的怀疑只能进 `semantic_warnings`（WARN，须带 evidence + confidence）

然后跑：

```bash
specanvil check <machine.yaml> [human.md] [prototype.manifest.yaml]
```
