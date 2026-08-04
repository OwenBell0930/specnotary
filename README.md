# Spec Kit

**Machine-first specs that humans can still read.**  
**机读为主源的可开发规格脚手架** — by OwenBell

[![gate](https://img.shields.io/badge/gate-hard%20CLI-0B6BCB)](#)
[![runtime](https://img.shields.io/badge/runtime-python3%20%7C%20node-159947)](#)
[![lang](https://img.shields.io/badge/docs-zh%20%2B%20en-D97706)](#)

> Turn messy product inputs into **dev-ready** specs: YAML/JSON source of truth → generated Markdown → CLI hard gate.  
> 把立项书、假详细 PRD、用户手册等，收成**可开发**规格：机读主源 → 生成人读 → CLI 硬门禁。

---

## Why you might stay / 为什么值得看下去

大多数「PRD 模板」只有文档。Spec Kit 多了三样真东西：

1. **机读主源**（优先 YAML）——自动化与 Agent 的唯一真相  
2. **人读投影**——给评审用，由机读生成，禁止长期只改人读  
3. **CLI 硬门禁**——本地一条命令 PASS/FAIL（Python 或 Node 都行）

<p align="center">
  <img src="docs/assets/flow.svg" alt="Spec Kit main flow" width="100%" />
</p>

---

## 30-second tour / 30 秒看懂仓库

<p align="center">
  <img src="docs/assets/architecture.svg" alt="Repo architecture" width="100%" />
</p>

| Path | What |
|------|------|
| `templates/` | 机读 / 人读模板 |
| `examples/case-*` | **三个可点开的案例**（原料 / 坏稿 / 反推） |
| `cli/` | `run-check.sh` · `run-generate-human.sh` |
| `skills/` | Cursor Skill（辅：起草与降级） |
| `docs/` | 可开发定义、门禁模式、评分表 |

---

## Quick start / 快速开始

```bash
# 1) clone or open this folder
cd spec-kit

# 2) hard gate（自动检测 python3 或 node）
./cli/run-check.sh examples/case-01-raw-material/machine/spec.yaml

# 3) 从机读生成人读
./cli/run-generate-human.sh examples/case-01-raw-material/machine/spec.yaml \
  examples/case-01-raw-material/human/spec.md

# 4) 跑全部示例测试
python3 tests/test_cli.py
```

Node 用户若检查 YAML：`cd cli/node && npm i`

没有 Python/Node？用 `skills/SKILL.md` **降级**检查，结果必须标 `gate_mode: degraded`（不能冒充硬门禁）。

<p align="center">
  <img src="docs/assets/cli-preview.svg" alt="CLI preview" width="100%" />
</p>

---

## Showcase cases / 案例展示

### Case 01 — 需求原料 → 可开发规格

**输入：** 虚构立项摘录（找合同 PDF 太慢）  
**输出：** 搜索字段、权限、空态文案、并发重建上限都写死  

| | |
|-|-|
| 原料 | [`examples/case-01-raw-material/input/charter.zh.txt`](examples/case-01-raw-material/input/charter.zh.txt) |
| 机读 | [`examples/case-01-raw-material/machine/spec.yaml`](examples/case-01-raw-material/machine/spec.yaml) |
| 人读 | 运行 `run-generate-human.sh` 生成到 `human/spec.md` |

```bash
./cli/run-check.sh examples/case-01-raw-material/machine/spec.yaml
# → RESULT: PASS
```

---

### Case 02 — 假详细 PRD → 拦住 → 修好

**输入：**「支持智能搜索，体验要好」——像规格，其实不可开发  

<p align="center">
  <img src="docs/assets/before-after.svg" alt="Before after fake detailed PRD" width="100%" />
</p>

| 版本 | 文件 | 硬门禁 |
|------|------|--------|
| 坏稿机读 | [`machine/spec.yaml`](examples/case-02-bad-prd/machine/spec.yaml) | **FAIL**（缺 actors/defaults，then 过空） |
| 修好机读 | [`machine/spec.fixed.yaml`](examples/case-02-bad-prd/machine/spec.fixed.yaml) | **PASS** |
| 原文 | [`input/bad-prd.zh.md`](examples/case-02-bad-prd/input/bad-prd.zh.md) | — |

```bash
./cli/run-check.sh examples/case-02-bad-prd/machine/spec.yaml
# → RESULT: FAIL
./cli/run-check.sh examples/case-02-bad-prd/machine/spec.fixed.yaml
# → RESULT: PASS
```

这就是「门禁」：不是口号，是命令行红绿。

---

### Case 03 — 用户手册反推（对象 AI 权重高）

**输入：** 报销助手手册（OCR + 置信度 + 审批）  
**机读：** `object_ai.enabled=true`，置信度 &lt; 0.7 强制人工；币种锁定 CNY  

| | |
|-|-|
| 手册摘录 | [`input/manual.zh.txt`](examples/case-03-reverse-manual/input/manual.zh.txt) |
| 机读 | [`machine/spec.yaml`](examples/case-03-reverse-manual/machine/spec.yaml) |

```bash
./cli/run-check.sh examples/case-03-reverse-manual/machine/spec.yaml
# → RESULT: PASS（project_hint.object_ai_weight=high）
```

---

## Core rules / 核心规则（短）

| 规则 | 说明 |
|------|------|
| 机读为准 | 人读由机读生成；禁止长期只改人读 |
| 优先 YAML | 亦支持 JSON |
| 双运行时 | 有 `python3` 或 `node` 用硬门禁；都没有 → Skill 降级 |
| 对象 AI | 产品里的 AI 章节；权重由声明/LLM 判断；与「写作助手」不是一回事 |
| 上传公开 | 若发 GitHub：走九步复核；上传即公开 |

详解：[`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) · [`docs/gate-modes.md`](docs/gate-modes.md) · [`docs/skill-boundary.md`](docs/skill-boundary.md)

---

## Project declaration / 项目声明

```bash
cp project.example.yaml project.yaml
# edit object_ai_weight: low | medium | high
```

---

## Status / 状态

本地建设中的工程资产。示例均为**虚构脱敏**业务，不涉及真实客户与未授权材料。

MIT-spirited personal toolkit — attribution: **OwenBell**.
