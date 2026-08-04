---
name: spec-kit
description: >
  Draft or revise Spec Kit machine-readable specs (YAML preferred), generate human-readable
  views, infer or ask object_ai_weight, and run degraded checks only when CLI runtime is missing.
  Use when the user works on Spec Kit / 规格工程 / machine-first specs.
---

# Spec Kit Skill（辅）

## Rules

1. **Machine source is authoritative.** Edit YAML/JSON machine specs first; generate human markdown from them.
2. Prefer **YAML**. Use JSON only if the user requires it or YAML tooling is unavailable.
3. Before claiming PASS: run `./cli/run-check.sh <file>` when `python3` or `node` exists.
4. If neither runtime exists: say so, offer install guidance, then optional **degraded** check. Every degraded report must include `gate_mode: degraded` and must not be described as a hard gate.
5. `object_ai_weight`: infer from inputs when clear; otherwise ask the user; write into `project.yaml`.
6. Never long-term edit only the human doc.

## Inputs you may accept

Raw materials (RFP/bid text, feature lists, project charter, VOC, competitor notes, prototype writeups), existing PRD/spec drafts (any quality), reverse inputs (tech design, user manual, test cases, release notes) — all must be treated as desensitized/public-safe in shared contexts.

## Outputs

- Updated machine spec path
- Generated human spec path
- Gate report (`hard` or `degraded`)
