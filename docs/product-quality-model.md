# 产品质量模型 / Product Quality Model

> Draft 与 Review **共用**本文件。禁止在 Skill、Command 或样例里复制第二套标准。
> 本模型回答「产品方案是否合理、是否可评审」。它**不是** Structure Gate（`FAIL` / `DRAFT` / `PASS`）的判据。

## 与 Structure Gate 的分工

| 层 | 谁执行 | 结论 | 能证明 | 不能证明 |
|----|--------|------|--------|----------|
| **Product Review** | 助手按本模型做语义审查 | `PRODUCT_REVIEW: REVISE` \| `DECISION_NEEDED` \| `REVIEWABLE` | 目标/边界/架构/流程/UX 上的可观察问题与待拍板项 | 业务已拍板、实现已就绪 |
| **Structure Gate** | Python CLI（`specnotary check` 等） | `RESULT: FAIL` \| `DRAFT` \| `PASS` | Schema、引用、哈希、账本、防漂等确定性结构 | 商业边界对不对、核心抓没抓对、架构是否可扩展、流程是否现实、UX 是否优秀 |

**禁止：**

- 用增加必填字段冒充产品质量提升
- 让 Draft 给自己的输出判定质量通过
- 把本模型的语义判断写进 Python hard gate
- 输出 `PRODUCT_REVIEW: PASS`（与 Structure Gate 的 PASS 混淆）
- 宣称「Gate 通过 = 产品方案合理」

最终对外必须**分开**展示：Draft 状态 · Product Review 状态 · Structure Gate 状态 · 产品经理待拍板事项。
Product Review 绑定被审文件 `content_hash`；规格修改后旧报告标 stale，须重新 Review。Gate PASS 不能覆盖 stale/`REVISE`。

---

## 五维标准

### 1. 目标与核心（goals_and_core）

审查是否说清：

- 用户是谁、场景是什么、要解决什么问题、预期结果是什么
- 原料与方案的**语义一致性**（有原料时）；无原料时只能评内部一致性，并标 `source_fidelity: unavailable`
- 是否抓住真正要交付的核心能力，而不是用周边改动冒充目标

典型问题：范围标题写「改按钮颜色」，正文却是完整搜索系统。

### 2. 边界（boundary）

审查是否合理：

- 是否围绕目标收口，有没有遗漏闭环必需能力
- 是否过度扩张到宿主或其他模块已有能力
- 模块「负责 / 不负责」是否与目标匹配
- `in_scope` / `out_of_scope` 是否互相打架或空转

典型问题：把支付、风控、运营后台一并塞进本期「列表搜索」。

### 3. 产品 / 信息架构（architecture）

审查是否清楚：

- 核心对象、关系、归属、生命周期
- 页面 / 模块层级与信息流
- 扩展点与耦合是否失控（例如所有业务塞进一个「通用页」）
- 是否把技术组件图冒充产品/信息架构

### 4. 业务流程（flow）

审查是否可走通：

- 成功路径、分支、异常、终止、补偿
- `from` / `action` / `to`（或等价状态/动作矩阵）是否可达
- 重复提交、并发、跨角色交接是否有口径
- 行为与目标是否语义一致（搜索不得变成「删除全部并提示成功」）

### 5. UX 合理性（ux）

审查是否可操作、可恢复：

- 任务频率与心智模型
- 导航与按钮命名（避免万能「确定」且无上下文）
- 默认值、反馈、错误预防与恢复
- 一致性、认知负担、基本无障碍
- 危险或幂等操作是否可无限连点

---

## 结论语义（仅 Product Review）

| 结论 | 含义 | 何时用 |
|------|------|--------|
| `REVISE` | 当前快照存在 blocker 或 major | 不修订就不能拿去认真评审 |
| `DECISION_NEEDED` | 无 blocker/major，但有 `requires_decision: true` | 可以开会，但会前/会上要拍板 |
| `REVIEWABLE` | 无 blocker/major，且无待拍板 finding | 可以进入结构门禁与需求评审准备 |

**没有** `PRODUCT_REVIEW: PASS`。结构收口用 Structure Gate 的 `RESULT: PASS` / `DRAFT`。
不为 finding 增加工作流 status；只看当前快照。

---

## 源保真（source_fidelity）

| 值 | 含义 |
|----|------|
| `aligned` | 有原料；审查对照了原料与方案 |
| `partial` | 有部分原料或仅覆盖部分章节 |
| `unavailable` | **没有原始需求材料**；只能评内部一致性、架构、流程、UX，**不得**宣称与原料一致 |

---

## Draft 如何使用本模型

Draft 按五维**组织候选稿**，把源外信息标为 `assumption` / `pending` / `decision`。
Draft **不得**自评 `REVIEWABLE` 或任何「质量通过」。单独调用 `/draft-spec` 时停在候选稿，不自动跑 Review / Gate。

## Review 如何使用本模型

按五维出 finding（字段见 [`product-review-contract.md`](product-review-contract.md)）。
默认不修改被审文档。反例校准见 [`product-review-corpus.md`](product-review-corpus.md)。

## Gate 如何对待本模型

Gate **不读取、不执行**本模型。Gate 只做确定性结构检查。报告与 Skill 必须写明：Structure Gate 通过 ≠ 产品方案合理。
