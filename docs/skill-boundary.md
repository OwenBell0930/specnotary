# Skill 职责边界 / Skill boundary

## 中文

| Skill 可以做 | Skill 不可以做 |
|--------------|----------------|
| 从原料/旧稿起草或改写**机读准据（YAML）** | 宣布「已通过硬门禁」却未跑 CLI（除非明确是降级模式） |
| 按规范从机读**生成人读** | 长期只改人读、不改机读（会造成漂移） |
| 在无 Python 时做**降级检查**并写明 `gate_mode: degraded` | 把降级结果写成与 CLI 同等效力；把 Node Deferred CLI 当硬门禁 |
| 根据输入建议或询问**对象 AI 权重** | 偷偷提高/隐瞒 AI 范围 |
| 从原料拆 **SourceClaim**（须写证据位置）；用语义拦住词表漏掉的假详细（闭环/治理类口号） | 宣称 CLI 能独立理解任意自然语言原料；把语义判断写成硬检查的 PASS |
| 生成原型时同步写 **PrototypeManifest** + `data-spec-id` | 把 LLM 截图判断写成硬 FAIL；不写 Manifest 却宣称原型已对齐 |

产品经理只面对原料、确认和评审材料。检查命令由 Skill 自己跑，不要让产品经理操作内部工具。

原则：**对错以机读 + 硬门禁为准**；Skill 是写作与检查的执行器。SpecNotary 不覆盖多人在线一起改稿。

## English

Skills may draft/update the machine source, generate human views, and run **degraded** checks when no runtime exists. Skills must not claim a hard CLI pass without running the CLI, and must not edit only the human view long-term. `specnotary new` / `ingest` only pin source files; they do not parse prose.
