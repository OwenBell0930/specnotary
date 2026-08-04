# Skill 职责边界 / Skill boundary

## 中文

| Skill 可以做 | Skill 不可以做 |
|--------------|----------------|
| 从原料/旧稿起草或改写**机读主源** | 宣布「已通过硬门禁」却未跑 CLI（除非明确是降级模式） |
| 按规范从机读**生成人读** | 长期只改人读、不改机读（会造成漂移） |
| 在无 Python/Node 时做**降级检查**并写明 `gate_mode: degraded` | 把降级结果写成与 CLI 同等效力 |
| 根据输入建议或询问**对象 AI 权重** | 偷偷提高/隐瞒 AI 范围 |

原则：**对错以机读 + CLI 硬门禁为准**；Skill 是写作与降级执行器。

## English

Skills may draft/update the machine source, generate human views, and run **degraded** checks when no runtime exists. Skills must not claim a hard CLI pass without running the CLI, and must not edit only the human view long-term.
