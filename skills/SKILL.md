---
name: spec-kit
description: >
  Use when the user works on Spec Kit / 规格工程 / machine-first specs.
---

# Spec Kit Skill（辅）

主载体是 **Python CLI + 模板脚手架**。本 Skill 负责起草机读与无运行时的降级检查。

## Rules

1. **Machine source is authoritative.** Edit YAML first; generate human 可开发的需求规格说明书 from it.
2. Prefer **YAML**. Human view must include wireframe, controls table, state/action matrix, numbered steps, AC, Pending four-fields.
3. Before claiming PASS: run `./cli/run-check.sh` — **FAIL must be 0**; WARN should be cleared or explicitly accepted.
4. Hard gate runtime is **Python only**. Node CLI is Deferred — never claim Node PASS as equivalent hard gate.
5. If no Python: degraded Skill check with `gate_mode: degraded` only.
6. Never long-term edit only the human doc. Generator refuses to write when machine has FAIL (unless `--allow-invalid`).
7. Do not copy proprietary scaffold/business PRDs into this repo; fictional examples only.
8. Use `states.action_matrix` (`state` / `action` / `allowed`); `cancel_matrix` is legacy.
9. Dual goals: **dev-ready** specs + **review-ready** intake (prototype consistency is Available / P2).

## 提取 SourceClaim（P1 · Skill 职责）

CLI **不读懂**任意自然语言。Skill 从 `inputs/` 拆原子项，写入机读 `sources` + `source_claims`。

每条 claim 必须有：

- `id`、`source_ref`（指向 `sources[].id`）
- `quote_or_summary` 或 `evidence`（证据位置：文件 + 行/段落）
- `disposition`：`covered` | `omitted` | `assumption` | `conflict` | `out_of_scope` | `pending`
- `covered` 必须带可解析的 `spec_refs`（行为 / AC / 控件 / `defaults.x`）

然后跑：

```bash
./cli/run-check.sh <machine.yaml>
./cli/run-generate-human.sh <machine.yaml> <human.md>
./cli/run-report.sh <machine.yaml> [report.md]
```

## 生成原型时必须同步 Manifest（P2 · Skill 职责）

CLI **不解析任意前端框架**。Agent 生成可演示原型时必须同时写 `prototype/prototype.manifest.yaml`。

- 每个业务控件加稳定标记：`data-spec-id="<机读控件或行为 ID>"`
- `generated_from_spec.hash` = 当前机读 `spec_hash`（`./cli/run-check.sh` 会打印）
- 规格里未标 `prototype_optional` 的控件 / 行为必须映射
- 无规格的业务动作 → FAIL；纯装饰放 `decorations`，可不写 `spec_refs`
- LLM 对截图/文案的怀疑只能进 `semantic_warnings`（WARN，须带 evidence + confidence）

然后跑：

```bash
./cli/run-check.sh <machine.yaml> [human.md] [prototype.manifest.yaml]
```
