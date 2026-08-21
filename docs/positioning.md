# 定位 · SpecNotary 与相邻工具的关系

一句话：**SpecNotary 帮产品经理把含糊需求写成可开发规格并检查是否写够。** 先在试用页点按钮；感兴趣后把 GitHub 网址发给 Cursor 或 Codex，请它安装。规格写在她正在用的文件夹里即可，不必把 SpecNotary 设成工作区。之后只提供原料、确认结果、拿材料去评审。不覆盖和同事在线一起改稿。

## 对照

| | SpecNotary | GitHub spec-kit (specify) | OpenSpec 类 | 传统 PRD 模板 |
|---|---|---|---|---|
| 核心物 | 机读 YAML 准据 + 确定性门禁；Skill 起草全套产物 | 工作流命令 + 提示词编排 | 规格目录与变更流程 | 文档模板 |
| 判定方式 | **确定性规则**（Schema/引用/哈希/覆盖），零 LLM | LLM 按阶段产出与自查 | 约定 + 人审 | 人审 |
| 「可开发」保证 | 空话 then/AC、占位 ui/defaults、断引用 → FAIL | 依赖模型与人自觉 | 依赖人自觉 | 无 |
| 「评审就绪」证据 | 原料快照哈希 + 派生人读防漂 + 真文件 `data-spec-id` 落点（本组合） | 无此组合 | 无此组合 | 无 |
| 人读文档 | 由机读生成，手改即 FAIL | 手写为主 | 手写为主 | 手写 |
| 原型一致性 | manifest + `data-spec-id` 落点核对 | 无 | 无 | 无 |
| 对方文档 | 可 `ingest` 为 source 并钉哈希，**无一键转 YAML** | 产出 spec.md | 产出 markdown 规格 | 产出 PRD |
| 依赖 | python3 + pyyaml + jsonschema | 自家 CLI + Agent | 各异 | 无 |

## 怎么搭配用

- **上游**：用 GitHub spec-kit / OpenSpec / 任意 PRD 流程产出原料。把对方 `spec.md` 当文件登记：`specnotary ingest spec.md --spec machine/spec.yaml --kind speckit`。不解析、不生成 claims。
- **中游**：Skill/LLM 按 `skills/SKILL.md` 起草机读 YAML、人读与原型（CLI 不解析自然语言）。
- **下游**：助手跑检查；产品经理确认假设后拿报告去开会。不覆盖多人在线改同一份文件。

## 名称

套件里 **CLI 是公证人**：不创作内容，只钉快照、验签章、出证明——原料内容哈希是公证存档，`--attest-prototype` 是公证背书，PASS 是限定范围内的公证书。写作在 Skill 层。与 CNCF Notary Project（OCI 容器制品签名规范）无关联，领域不同。

## 边界（不做什么）

- 不做自然语言理解门禁——硬检查只扫词表。语义假详细（词表漏网的「治理到位」「业务跑通」）由助手在写作时拦住，不能拿来当结构通过的证明。
- 不覆盖产品经理与开发团队在线一起改稿；不把 GitHub 协同、流水线当作使用方式。
- 不做「任意 Markdown → 完整机读 YAML」导入。
- 不做完整 SDD 平台 / 项目管理 / 工单系统。
- 不做像素级视觉走查；原型核对止步于 manifest + DOM 标记这条确定性链。
