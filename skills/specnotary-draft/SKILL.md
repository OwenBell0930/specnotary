---
name: specnotary-draft
description: >
  Draft-only SpecNotary skill. Turns raw requirement material into a candidate
  machine spec (and optional human projection) without self-scoring quality or
  running Review/Gate. Use when the user asks /draft-spec or only wants a draft.
---

# SpecNotary Draft（仅起草）

**只做高质量起草。** 不跑 Product Review，不跑 Structure Gate，不得给自己的输出判定质量通过。

产品边界：需求原料 → 产品方案与标准文档候选稿。不扩展到技术栈、实现任务、测试计划、覆盖率、研发实施或多人在线协作。

公共质量组织标准（写什么、标什么假设）：[`docs/product-quality-model.md`](../../docs/product-quality-model.md)。
**禁止**在本 Skill 复制第二套质量规则。

## 输入

- 必需：需求原料（PRD / 工单 / FAQ / 口述整理稿等）
- 可选：业务背景、宿主产品已有能力说明
- 安装：若无 `specnotary`，`pip install "git+https://github.com/OwenBell0930/specnotary.git"`（不必把 SpecNotary 设成工作区）

## 输出

- 案卷目录 + 已钉哈希的 `sources[]`（`specnotary new` / `ingest`）
- 候选机读 YAML（通常 `status: draft`）
- 按需生成的人读说明书（生成器产出，禁止长期手改）
- 源外信息必须标 `assumption` / `pending` / `decision`（含首轮 `D-PROTOTYPE` 未确认则保持 pending）

## 停止边界

单独调用本 Skill / `/draft-spec` 时：

1. 交候选稿与「原文没写、规格补了猜测」清单后 **停止**
2. **不**自动执行 Review
3. **不**自动执行 Gate
4. **不**输出 `PRODUCT_REVIEW:` 或伪装终稿 `RESULT: PASS`
5. Draft 状态对外写：`DRAFT_STATUS: CANDIDATE`（或等价中文：候选稿已生成，未经独立审查）

## 起草步骤

1. `specnotary new <case-dir> --from <raw-file> ...` 钉原料；需要时 `ingest`
2. 拆 `source_claims`；源外推断不得标 `covered`
3. 按质量模型五维组织机读：目标与核心、边界、产品/信息架构、流程、UX（字段仍走现有 Schema，不新增「质量分」字段）
4. 首轮问清 `D-PROTOTYPE`；未确认不猜
5. 需要给人看时用生成器出人读；改正文即违纪
6. 停止。若用户要审查或门禁，请其改用 `/review-spec`、`/gate-spec` 或全流程 `/write-spec`

## 硬性禁止

- 自评「质量通过 / REVIEWABLE / 可上会终稿」
- 静默把猜测写成事实
- 产出实现任务、技术栈、测试方案
- 只改人读不改机读
