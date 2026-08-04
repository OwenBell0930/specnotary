# Spec Kit / 规格工程脚手架

**OwenBell** · 本地脚手架 + CLI（主）· Skill（辅）  
机读规格为主源（优先 YAML）→ 生成人读规格 · 中英可工作说明

> 本仓库当前为**本地建设中**。未获作者同意前请勿当作已发布的 GitHub 正式版。

## What this is / 这是什么

A small kit to turn messy product inputs into **dev-ready specs**:

- **Machine-readable source of truth** (YAML preferred; JSON also supported)
- **Human-readable specs** generated from the machine source (via rules or Skill)
- **CLI gate** when Python or Node is available
- **Degraded mode** via Skill + LLM if no runtime is installed (must be labeled degraded)

把杂乱输入收成**可开发规格**：

- **机读为主源**（优先 YAML，兼支持 JSON）
- **人读由机读生成**（规范或 Skill）
- 有 Python/Node 时用 **CLI 硬门禁**
- 都没有时用 Skill+LLM **降级**（必须标明降级）

## Quick start / 快速开始

```bash
# Prefer YAML project declaration
cp project.example.yaml project.yaml

# Run check (auto-detect python3 or node)
./cli/run-check.sh path/to/spec.yaml
```

If neither runtime exists, use the Skill under `skills/` and treat results as **degraded**.

## Layout / 目录

见仓库内各文件夹；说明文档在 `docs/`。

## Gate modes / 门禁模式

See `docs/gate-modes.md`.
