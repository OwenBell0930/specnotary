---
name: spec-kit
description: >
  Draft or revise Spec Kit machine-readable specs (YAML preferred), generate human-readable
  views, infer or ask object_ai_weight, and run degraded checks only when CLI runtime is missing.
  Use when the user works on Spec Kit / 规格工程 / machine-first specs.
---

# Spec Kit Skill（辅）

## Rules

1. **Machine source is authoritative.** Edit YAML first; generate human 可开发的需求规格说明书 from it.
2. Prefer **YAML**. Human view must include wireframe, controls table, state matrix, numbered steps, AC, Pending four-fields.
3. Before claiming PASS: run `./cli/run-check.sh` — **FAIL must be 0**; WARN should be cleared or explicitly accepted.
4. If no runtime: degraded Skill check with `gate_mode: degraded` only.
5. Never long-term edit only the human doc.
6. Do not copy proprietary scaffold/business PRDs into this repo; fictional examples only.

## Inputs you may accept

Raw materials (RFP/bid text, feature lists, project charter, VOC, competitor notes, prototype writeups), existing PRD/spec drafts (any quality), reverse inputs (tech design, user manual, test cases, release notes) — all must be treated as desensitized/public-safe in shared contexts.

## Outputs

- Updated machine spec path
- Generated human spec path
- Gate report (`hard` or `degraded`)
