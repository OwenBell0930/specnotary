# Skill 职责边界 / Skill boundary

## 中文

| Skill | 可以做 | 不可以做 |
|-------|--------|----------|
| **Draft**（`specnotary-draft`） | 从原料起草候选机读；源外标 assumption/pending/decision | 自评质量通过；单独调用时自动跑 Review/Gate |
| **Review**（`specnotary-review`） | 按唯一产品质量模型审查；YAML 绑定 `subject.content_hash`；先 YAML 后人读投影；改稿后标 stale 并复审 | 静默重写被审文档；自动拍板；`PRODUCT_REVIEW: PASS`；无 `source_materials` 声称 aligned/partial |
| **Gate**（`specnotary-gate`） | 跑 Python CLI 硬门禁与报告；对未标准化 Markdown 拒绝 hard PASS | 判断商业边界/架构可扩展/现实流程/UX 优劣；用 LLM 冒充 hard；用 Gate PASS 覆盖 stale/`REVISE` |
| **编排**（`specnotary` / `/write-spec`） | Draft → Review →（修订/拍板 → 重新 Review）→ Gate；已有文档可跳过 Draft | 把三层结论合并；改完规格不复审就引用旧 PRODUCT_REVIEW；扩展到实现/测试/交付 |

| 共性可以做 | 共性不可以做 |
|------------|----------------|
| 按规范从机读**生成人读** | 长期只改人读、不改机读 |
| 无 Python 时做**降级检查**并写明 `gate_mode: degraded` | 把降级写成与 CLI 同等效力；Node Deferred 当硬门禁 |
| 从原料拆 **SourceClaim**；用语义拦住词表漏掉的假详细 | 宣称 CLI 能独立理解任意自然语言；把语义判断写成硬检查 PASS |
| 生成原型时同步 **PrototypeManifest** + `data-spec-id` | 把 LLM 截图判断写成硬 FAIL |

公共质量模型（Draft/Review 唯一）：[`product-quality-model.md`](product-quality-model.md)。
审查契约（hash / stale / `source_materials`）：[`product-review-contract.md`](product-review-contract.md)。
已有文档可选 **normalize/projection**（只提取、不发明）后再 Gate，且须复审；不得冒充 Draft。

产品经理只面对原料、确认和评审材料。检查命令由 Skill 自己跑。

原则：**结构对错以机读 + 硬门禁为准；产品方案是否合理以绑定 hash 的 Product Review 为准。** 「独立」指能力与结论可分开调用/展示，不等于默认多 Agent。

## English

Draft writes candidates and must not self-score. Review binds `subject.content_hash`, writes YAML then Markdown, marks stale after subject changes, and re-reviews before quoting `PRODUCT_REVIEW`. Gate runs the Python CLI only, never hard-PASSes plain Markdown, and never overrides a stale/`REVISE` Product Review. `/write-spec` is Draft → Review → (edit → re-review) → Gate with separate verdicts.
