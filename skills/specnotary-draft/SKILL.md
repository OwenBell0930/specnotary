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
3. **先定边界再列功能**：写清用户结果、本期范围、后续阶段、宿主已有能力、替换的旧语义与必须保持的基线；被排除项不得出现在本期状态、流程或验收里
4. **先定对象再画页面**：在 `data_contracts` 为核心业务对象写职责/归属、唯一性、关系、事实类型、生命周期、生产者/消费者，以及历史事实与当前结论的边界；页面消费了未定义对象时，补对象或建 Pending
5. **再定信息架构**：用 `architecture.surfaces` 说明入口/列表/详情/过程/结果/输出物分别回答什么问题、读写哪些对象、跳到哪里、权威状态来自哪里；禁止让不同页面维护第二套业务状态
6. **最后写功能契约**：仍以 `behaviors[]` 为唯一功能实体。普通只读功能可保持 Given/When/Then；涉及写入、权限、跨对象副作用或异步处理时，补 `entry_ref`、`actor_refs`、`reads/writes`、状态变化、异常、幂等、恢复、权限与验收引用
7. 权限简单时保留 `actor + can`；需要对象/状态级授权时用 `permissions[].rules[]`，并保持列表、详情、按钮、深链与 API 同一规则，前端显隐不能替代服务端授权
8. 验收不只写成功路径；关键异常、部分成功、重复执行和恢复要有可观察结果，并按需回指角色、对象、状态、权限和页面
9. Pending 分两类：事实缺口用 `kind: fact`，不得虚构二选一；真正产品取舍用 `kind: decision`，给互斥可执行选项、建议、理由/代价，但推荐项在拍板前不得进入正式需求
10. 首轮问清 `D-PROTOTYPE`；未确认不猜
11. 需要给人看时用生成器出人读；改正文即违纪
12. 停止。若用户要审查或门禁，请其改用 `/review-spec`、`/gate-spec` 或全流程 `/write-spec`

这些字段按复杂度渐进采用，不为填满模板扩建产品。Draft 组织候选方案，但仍不得给自己的边界、架构、流程或 UX 判定 `REVIEWABLE`。

## 硬性禁止

- 自评「质量通过 / REVIEWABLE / 可上会终稿」
- 静默把猜测写成事实
- 产出实现任务、技术栈、测试方案
- 只改人读不改机读
