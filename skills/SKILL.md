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
9. Dual goals: **dev-ready** specs + **review-ready** intake (source coverage / prototype consistency are Planned).
