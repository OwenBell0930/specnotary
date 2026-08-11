# Spec Kit v0.2 优化执行方案：产品经理评审就绪版

> 文档用途：供 Cursor 按顺序实施，不作为当前已完成功能说明。  
> **采纳决议（2026-08-07）：** 可开发 ∩ 评审就绪（并集）；Node=Deferred；按 P0→P1→P2 开干。P0 / P1 已落地。**P2（2026-08-11）已落地** PrototypeManifest / `data-spec-id` / 对齐+漂移样例 / 报告 missing·extra·stale·mismatch·unverified。  
> 目标用户：不承担全栈开发、主要负责需求收口与评审准备的产品经理 / BA。  
> 核心场景：需求评审前，将零散原料整理为方案与 PRD 级规格，并检查原料、机读规格、人读文档、Agent 原型之间的意图一致性。  
> 执行原则：先让门禁可信，再增加一致性能力；未通过本阶段验收，不进入下一阶段。

---

## 1. 本轮产品决策

### 1.1 最终定位

本项目不是覆盖研发、测试、发布全流程的 SDD 平台，也不负责验证生产代码是否实现需求。

本项目是一个面向产品经理的 **需求评审就绪工具包**：

1. 接收 PRD 草稿、工单、FAQ、会议纪要、功能清单、原型说明等需求原料；
2. 由 Agent / Skill 将原料结构化为机读规格；
3. 由确定性 CLI 检查结构、引用、覆盖状态与未决事项；
4. 由机读规格生成人读方案 / PRD 视图；
5. Agent 根据机读规格生成可演示原型，并同时生成原型清单；
6. 输出评审前一致性报告，指出遗漏、擅自新增、冲突、未决和原型不一致。

一句话价值：

> 在需求评审前，证明“原始要求没有漏、方案没有编、人读没有漂、原型没有擅自改需求”。

### 1.2 漂移的限定定义

本项目中的“漂移”统一改称 **需求意图漂移**，只覆盖以下链路：

```text
需求原料 → 机读规格 → 人读方案/PRD → Agent 原型
```

本期不覆盖：

- 任务与代码的对应关系；
- 代码实现正确性；
- 测试用例、测试结果和验收执行；
- 发布、部署和运行时监控；
- 任意源代码的语义逆向分析。

AC 可以继续作为 PRD 中的“可观察完成条件”，但本期不建立 AC 到测试用例、测试结果的追踪关系。

### 1.3 载体调整

面向产品经理时，Skill / Agent 应是主要交互入口，CLI 是背后的确定性校验器。

| 层级 | 定位 | 是否首期必须 |
|---|---|---:|
| Agent / Skill | 接收自然语言和文件、引导补充、起草机读规格、解释报告 | 是 |
| Python CLI | Schema、引用、覆盖、哈希和原型清单的确定性门禁 | 是 |
| Templates / Examples | 提供可复制的业务规格和原型清单示例 | 是 |
| GitHub Spec Kit / OpenSpec Adapter | 接入已有生态，不重建完整 SDD 流程 | 后续 |
| GitHub Action | 团队仓库自动检查 | 后续 |
| Web / MCP / 桌面客户端 | 独立产品界面或协议服务 | 暂不做 |

首版停止维护第二套 Node 规则实现。只保留 Python 作为唯一硬门禁运行时，直到出现明确的 Node 用户需求。

---

## 2. 产品边界

### 2.1 用户任务

产品经理在评审前需要完成：

1. 确认所有输入材料已经被读取和登记；
2. 区分原始事实、产品决策、Agent 推导、假设和待确认项；
3. 将范围、对象、角色、状态、规则、页面、控件、文案、行为和异常路径收口；
4. 形成研发和测试能够理解的人读方案 / PRD；
5. 形成可用于评审沟通的 Agent 原型；
6. 知道原料到方案、方案到原型之间具体缺了什么、多了什么、冲突在哪里。

### 2.2 非目标

- 不替代企业现有完整 PRD 模板；
- 不承诺把任意原料一次性自动生成正确需求；
- 不把 LLM 的语义判断包装成确定性硬门禁；
- 不要求产品经理理解或手写 YAML；
- 不把视觉风格、像素级还原纳入首期一致性门禁；
- 不建设用户、权限、项目管理、模板管理等后台；
- 不同时维护 Python 和 Node 两套不同规则。

---

## 3. 核心对象及关系

### 3.1 核心对象

| 对象 | 说明 | 生命周期 / 状态 |
|---|---|---|
| `SourceMaterial` | 一份原始材料，如 PRD 草稿、FAQ、纪要、图片说明 | registered / superseded |
| `SourceClaim` | 从原料中拆出的原子要求、约束、事实或问题 | confirmed / assumption / pending / conflict / out_of_scope |
| `MachineSpec` | 唯一准据，承载对象、状态、规则、页面和行为 | draft / review_ready / deprecated |
| `HumanSpec` | 由 MachineSpec 确定性生成的人读视图 | generated / stale |
| `PrototypeManifest` | Agent 原型中的页面、控件、交互、状态与规格引用 | draft / aligned / stale |
| `ConsistencyReport` | 原料覆盖、人读一致性、原型覆盖和阻塞项报告 | generated |

### 3.2 对象关系

```text
SourceMaterial 1 ── n SourceClaim
SourceClaim    n ── n MachineSpec Entity
MachineSpec    1 ── 1 HumanSpec
MachineSpec    1 ── n Prototype Element
以上关系共同生成 ConsistencyReport
```

### 3.3 规格实体

MachineSpec 中首期保留或补充以下实体：

- `scope`：本期做 / 不做；
- `actors`：角色；
- `objects`：业务对象及归属；
- `permissions`：角色能执行的动作；
- `states`：状态与转换；
- `rules`：业务约束、默认策略、限额；
- `views`：页面 / 弹窗 / 区域；
- `controls`：控件、显隐、文案、动作、失败反馈；
- `behaviors`：Given / When / Then 和异常路径；
- `acceptance`：评审阶段的可观察完成条件；
- `pending`：问题、影响、责任人、期望确认时间、是否阻塞评审；
- `source_claims`：原料原子项及其处理结果。

所有主要实体必须有稳定 ID，供人读视图和原型清单引用。

---

## 4. 三段一致性检查

### 4.1 原料 vs 机读规格

需要识别五类结果：

| 类型 | 定义 | 处理 |
|---|---|---|
| covered | 原料要求已进入机读规格 | 通过 |
| omitted | 原料要求没有进入规格，也没有解释 | review_ready 时 FAIL |
| assumption | Agent / 产品经理补充了原料未明确说明的内容 | 必须显式标记，默认 WARN |
| conflict | 两份原料或原料与当前决策冲突 | 未闭合时 FAIL |
| out_of_scope | 明确不在本期实现 | 记录理由后通过 |

每个 `SourceClaim` 至少包含：

```yaml
- id: SRC-CLM-001
  source_ref: SRC-001
  quote_or_summary: 买家可取消未发货订单
  kind: requirement
  disposition: covered
  spec_refs: [B-001, RULE-001]
  confidence: high
```

注意：原料语义拆分由 Agent 完成，CLI 只确定性检查 ID、引用和处置状态。CLI 不得宣称自己能独立理解任意自然语言材料。

### 4.2 机读规格 vs 人读方案 / PRD

HumanSpec 必须始终由 MachineSpec 生成：

- HumanSpec 头部写入机读文件路径、规格版本和内容哈希；
- `render` 每次覆盖生成，不提供“合并手工修改”能力；
- `check` 比较当前 MachineSpec 哈希与 HumanSpec 中记录的哈希；
- 哈希不一致或重新生成有 Diff 时，标记 `HumanSpec: stale` 并 FAIL；
- 人工补充应先进入 MachineSpec，再重新生成人读视图。

这一段不使用 LLM，必须完全确定性。

### 4.3 机读 / 人读规格 vs Agent 原型

不要求 CLI 理解任意前端代码。Agent 在生成原型时必须同时生成 `prototype.manifest.yaml`：

```yaml
prototype_version: "0.1"
generated_from_spec:
  id: SPEC-ORDER-001
  hash: sha256:...
screens:
  - id: SCREEN-ORDER-DETAIL
    spec_refs: [VIEW-001]
    path: prototype/order-detail.html
    controls:
      - id: PROTO-BTN-CANCEL
        spec_refs: [CTRL-001, B-001]
        selector: "[data-spec-id='CTRL-001']"
        states: [visible, disabled]
interactions:
  - id: PROTO-FLOW-CANCEL
    spec_refs: [B-001]
    from: SCREEN-ORDER-DETAIL
    trigger: PROTO-BTN-CANCEL
    to: DIALOG-CANCEL-CONFIRM
```

确定性检查：

- 原型使用的 Spec ID 是否存在；
- 每个必需页面、控件和行为是否至少有一个原型映射；
- 原型是否声明了规格中不存在的额外业务行为；
- 原型基于的 Spec 哈希是否过期；
- 必需文案 ID、状态和交互是否在 Manifest 中覆盖。

Agent 语义检查：

- 截图中的文案是否可能与规格冲突；
- 控件显隐、禁用态和失败反馈是否可能不一致；
- 原型是否通过视觉或交互暗示了额外业务规则。

Agent 语义检查只能输出 WARN，并必须包含证据位置与置信度。首期不得因纯 LLM 判断直接 FAIL。

---

## 5. Gate 规则

### 5.1 Hard FAIL：必须确定性复现

- JSON Schema 不通过；
- `status` 非法；
- ID 重复；
- 任意 `spec_refs` 指向不存在实体；
- `review_ready` 仍有阻塞型 Pending；
- `review_ready` 存在未处置的 SourceClaim；
- SourceClaim 标记 `covered` 但没有任何 `spec_refs`；
- HumanSpec 哈希与 MachineSpec 不一致；
- PrototypeManifest 引用不存在的 Spec ID；
- PrototypeManifest 基于旧 Spec 哈希；
- 标记为“原型必需”的页面、控件或行为没有映射。

### 5.2 WARN：需要产品经理确认

- Agent 推导出的 assumption；
- 原料之间存在已记录但暂不阻塞评审的差异；
- 模糊、不可观察或可能歧义的描述；
- 原型包含额外的非业务装饰或交互；
- LLM 发现的潜在语义不一致；
- 可选页面、控件或异常态未进入原型。

### 5.3 禁止作为硬规则

- 仅通过关键词命中“智能”“体验好”等词就直接 FAIL；
- 没有证据位置的 LLM 判断；
- 视觉像素差异；
- 未经结构化声明的任意代码语义猜测。

模糊词规则可以继续保留，但在没有上下文判定前降为 WARN。

---

## 6. 对外命令与产品经理使用方式

### 6.1 产品经理看到的主流程

产品经理不需要直接操作 CLI。主要入口应是 Skill / Agent 指令：

> 读取 `inputs/` 中的需求原料，整理为评审就绪方案，生成原型并检查一致性。

Agent 内部执行：

```text
登记原料
→ 提取 SourceClaim
→ 起草 / 更新 MachineSpec
→ 运行硬门禁
→ 生成人读方案
→ 生成原型及 PrototypeManifest
→ 运行一致性检查
→ 输出评审就绪报告
```

### 6.2 CLI 最小接口

首期只保留三个公开动作：

```bash
specready check project.yaml
specready render project.yaml
specready report project.yaml
```

其中 `project.yaml` 只负责声明路径和评审策略：

```yaml
name: order-cancel-demo
locale: zh-CN
sources: inputs/source-index.yaml
machine_spec: machine/spec.yaml
human_spec: human/spec.md
prototype_manifest: prototype/prototype.manifest.yaml
report: reports/review-readiness.md
```

不要让用户分别记忆多个 Python / Node / Shell 入口。

---

## 7. 分阶段实施计划

### P0：让当前门禁可信且可泛化

任务：

1. 确定 Python 为唯一硬门禁运行时，停止宣传和维护 Node 等价能力；
2. 将 JSON Schema 变为实际执行的第一层校验；
3. 补齐嵌套 Schema：actor、permission、state、transition、view、control、behavior、acceptance、pending；
4. 增加 ID 唯一和跨对象引用校验；
5. 将 `cancel_matrix`、买家、订单取消等领域写死内容改为通用状态 / 动作模型；
6. 生成器发现 FAIL 时不得返回成功结果，除非显式传入 `--allow-invalid`；
7. `project.example.yaml` 不得自动充当真实配置；没有 `project.yaml` 时使用程序默认值；
8. `.cursor/` 默认加入 `.gitignore`，不得提交本机绝对路径和外部运营仓指针；
9. README 增加能力状态表：Available / Planned / Deferred。

验收：

- `status: banana` 必须 FAIL；
- AC 引用不存在的 Behavior 必须 FAIL；
- Permission 引用不存在的 Actor 必须 FAIL；
- 两个非订单业务样例能够正确生成通用人读文档；
- 所有规则都有至少一个 PASS 和一个 FAIL 测试；
- README 不再把 Node 描述成等价硬门禁。

### P1：实现原料 → 机读 → 人读一致性

任务：

1. 增加 `SourceMaterial` 与 `SourceClaim` Schema；
2. Skill 负责从原料提取 SourceClaim，并要求证据位置；
3. CLI 检查每个 SourceClaim 的处置状态和引用；
4. 增加 MachineSpec 内容哈希；
5. HumanSpec 写入来源、版本和哈希；
6. `check` 能识别人读文档过期或被单独手改；
7. `report` 输出 omitted / assumption / conflict / pending / out_of_scope 汇总。

验收案例：

- 原料中的一条要求未进入规格且未解释：FAIL；
- Agent 新增一个原料没有的规则但标记 assumption：WARN；
- 两份原料互相冲突且未闭合：FAIL；
- 人读文档被手改或机读更新后未重新生成：FAIL；
- 所有原料项均被覆盖或明确处置：PASS。

### P2：实现规格 → Agent 原型一致性

任务：

1. 定义 `PrototypeManifest` Schema；
2. 调整原型生成 Skill：生成原型时必须同步生成 Manifest；
3. 原型元素使用 `data-spec-id` 或等价稳定标记；
4. CLI 校验页面、控件、行为、状态、文案引用和 Spec 哈希；
5. 增加一个符合规格的原型和一个故意漂移的原型；
6. 报告明确区分 missing / extra / stale / mismatch / unverified。

验收案例：

- 必需按钮未出现在 Manifest：FAIL；
- Manifest 引用不存在的控件：FAIL；
- 原型基于旧 Spec 生成：FAIL；
- 原型新增一个业务动作但无 Spec 引用：FAIL；
- 纯视觉装饰没有 Spec 引用：不阻塞；
- LLM 怀疑截图文案与规格不一致：WARN，并带证据。

### P3：开源发布与生态接入

任务：

1. 发布前更换项目名称，避免与 `github/spec-kit` 混淆；
2. 增加 Python 安装配置，使用户可以一条命令安装；
3. 增加 LICENSE、SECURITY、CONTRIBUTING、CHANGELOG；
4. 增加 CI，执行 Schema、规则、生成器和案例回归；
5. 将本项目包装为 GitHub Spec Kit / OpenSpec 的扩展或 Preset，而不是重建完整 SDD 平台；
6. 有外部团队仓库使用后，再增加 GitHub Action。

验收：

- 新用户可以从空目录完成一次示例；
- README 中所有标记 Available 的能力都有可复制命令和测试；
- 公开仓库不含本机路径、个人运营资产、内部资料或敏感记录；
- 至少一个外部用户可以不手写 YAML 完成评审前流程。

---

## 8. README 能力状态规则

预期目标可以写，但必须与当前能力分层展示：

| 状态 | 含义 | README 写法 |
|---|---|---|
| Available | 已实现且有测试 | 放入 Quick Start 和能力列表 |
| Experimental | 已实现但接口可能变化 | 明确标实验性和限制 |
| Planned | 目标明确但尚未实现 | 只放 Roadmap，不提供成功示例 |
| Deferred | 已决定暂不建设 | 放 Non-goals / Later |

不得删除愿景，但不得用现在时描述尚未实现的行为。

当前建议：

- YAML 校验与人读生成：Available；
- 任意原料自动转机读：Planned；
- 原料覆盖检查：Available；
- 原型一致性检查：Available；
- Node 等价硬门禁：Deferred；
- Web / MCP：Deferred。

---

## 9. Cursor 执行约束

1. 严格按照 P0 → P1 → P2 → P3 顺序执行；
2. 不得在 P0 验收完成前继续美化 README、SVG 或新增业务案例；
3. 每个阶段先补测试，再修改实现，再更新能力状态；
4. 不得同时维护两套独立规则引擎；
5. LLM 语义判断与确定性规则必须分层，输出中标明证据和置信度；
6. 不得把计划中的能力写成已完成；
7. 不得引入 Web、MCP、数据库、账号系统或管理后台；
8. 不得复制任何公司或客户的非公开模板、规则、案例、提示词和文档；
9. 保留现有用户改动，修改前先检查 Git 状态，不覆盖未提交文件；
10. 每完成一个阶段，输出：变更文件、测试结果、未完成项、已知限制和下一阶段入口。

---

## 10. v0.2 完成定义

同时满足以下条件，才可称为 v0.2：

- 产品经理可通过 Skill 提交原料，不需要手写 YAML；
- 每条原料要求都能看到其处置结果；
- 机读规格通过真实 Schema 和引用门禁；
- 人读方案能证明由当前机读版本生成且没有单独漂移；
- Agent 原型带有可检查的 Manifest；
- 报告能够指出遗漏、擅自新增、冲突、过期和未验证项；
- 所有 Hard FAIL 均由确定性规则产生；
- 关键链路至少包含一组 PASS 和一组故意失败的合成案例；
- README 对 Available、Planned、Deferred 的描述与实现一致。

达到以上条件后，本项目的核心证明不再是“会生成一份漂亮 PRD”，而是：

> 能把产品经理的需求原料、正式方案和 Agent 原型组织成一条可解释、可复核、可在评审前收口的需求证据链。
