# 定位 · SpecNotary 与相邻工具的关系

一句话：**SpecNotary 判定「规格本身是否可开发、评审是否有证据」；工作流类 SDD 工具解决「怎么让人和 Agent 按规格干活」。二者互补，不互替。**

## 对照

| | SpecNotary | GitHub spec-kit (specify) | OpenSpec 类 | 传统 PRD 模板 |
|---|---|---|---|---|
| 核心物 | 机读 YAML 唯一准据 + 确定性门禁 | 工作流命令 + 提示词编排 | 规格目录与变更流程 | 文档模板 |
| 判定方式 | **确定性规则**（Schema/引用/哈希/覆盖），零 LLM | LLM 按阶段产出与自查 | 约定 + 人审 | 人审 |
| 「可开发」保证 | 空话 then/AC、占位 ui/defaults、断引用 → FAIL | 依赖模型与人自觉 | 依赖人自觉 | 无 |
| 「评审就绪」证据 | SourceClaim 覆盖闭环 + 人读/原型防漂哈希链 | 无此层 | 无此层 | 无 |
| 人读文档 | 由机读生成，手改即 FAIL | 手写为主 | 手写为主 | 手写 |
| 原型一致性 | manifest + `data-spec-id` 落点核对 | 无 | 无 | 无 |
| 依赖 | python3 + pyyaml + jsonschema | 自家 CLI + Agent | 各异 | 无 |

## 怎么搭配用

- **上游**：用 GitHub spec-kit / OpenSpec / 任意 PRD 流程产出原料——它们的输出就是 SpecNotary 的 `sources`。
- **中游**：Skill/LLM 起草机读 YAML（SpecNotary 的 CLI 不解析自然语言，判定与理解分层）。
- **下游**：`specnotary check` 挂进 CI 或 Agent 验收环，PASS 才算规格完成；`specnotary report` 给评审会当证据。

## 名称由来

曾用名 Spec Kit（与 GitHub 官方 spec-kit 同名，检索上等于不存在）、SpecAnvil（与 specanvil.com 的同定位产品撞名，外部审计发现后弃用）。Notary（公证人）与产品本质精确同构：**不创作内容，只钉快照、验签章、出证明**——原料内容哈希是公证存档，`--attest-prototype` 是公证背书，PASS 是限定范围内的公证书。与 CNCF Notary Project（OCI 容器制品签名规范）无关联，领域不同。

## 边界（不做什么）

- 不做自然语言理解门禁——那是 Skill/LLM 的辅助职责，结果必须标 `gate_mode: degraded`。
- 不做完整 SDD 平台 / 项目管理 / 工单系统。
- 不做像素级视觉走查；原型核对止步于 manifest + DOM 标记这条确定性链。
