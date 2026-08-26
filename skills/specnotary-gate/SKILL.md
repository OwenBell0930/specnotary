---
name: specnotary-gate
description: >
  SpecNotary deterministic structure gate only. Runs existing Python CLI checks
  (schema, refs, hashes, ledger, anti-drift, FAIL/DRAFT/PASS). Never judges
  product-boundary quality or UX excellence. Use for /gate-spec.
---

# SpecNotary Gate（确定性结构门禁）

**只做 Structure Gate。** 使用现有 Python CLI：`check` / `report` / `sync` / `confirm` / `human` 等。
**不**判断商业边界、核心是否抓对、架构可否扩展、现实流程是否正确、UX 是否优秀。
**不**在调用 LLM 后仍声称 `gate_mode: hard`。

证明边界：[`docs/proof-boundary.md`](../../docs/proof-boundary.md)。
门禁模式：[`docs/gate-modes.md`](../../docs/gate-modes.md)。
产品质量语义**不在**本 Skill：见 [`docs/product-quality-model.md`](../../docs/product-quality-model.md)。

## 输入

- **硬门禁合法输入：** SpecNotary machine spec（YAML/JSON），可选人读与 prototype manifest
- **非合法硬门禁输入：** 普通 Markdown / 未标准化的 PRD

## 输出

- CLI 文本或 `--json` 判定：`RESULT: FAIL | DRAFT | PASS`，以及 `STRUCTURE_GATE` / `READY_GAP_COUNT`（若有）
- 需要时：`specnotary report` 写出输出自检报告
- 对外必须声明：**Structure Gate 通过不等于产品方案合理**
- Gate 结论与 Product Review **分开展示**；Gate PASS **不能**覆盖 `validity: stale` 或 `PRODUCT_REVIEW: REVISE`

## 停止边界

1. 跑完门禁（及用户点名的 `sync`/`report`）后停止
2. 不自动改写业务方案来「凑 PASS」
3. 不把 Product Review finding 写进 Python 规则
4. 普通文档未做 normalize/projection 时：**不得伪造 hard PASS**（见下）

## 普通文档 / Review+Gate 路径

若输入是普通 Markdown / PRD 且尚未映射为 machine spec：

1. 明确说明：**不满足 hard gate 输入要求**
2. 可建议先 `/review-spec`，必要时 **normalize/projection**（只提取、不发明；draft）；映射后旧 Review 标 stale 并重新 Review
3. **禁止**打印 `gate_mode: hard` + `RESULT: PASS`
4. 无 Python 时仅可 `gate_mode: degraded`，且不得冒充 hard

## 推荐命令

```bash
specnotary check <machine.yaml> --explain
specnotary sync <machine.yaml>                    # 人读；原型须另 --attest-prototype
specnotary report <machine.yaml>
specnotary confirm <machine.yaml> --by <name> --reason "<why>" --accept-all-warn
```

免安装：`./cli/run-check.sh` 等。Node CLI = Deferred，退出码 3，不得 hard PASS。

## 硬性禁止

- 用语义/LLM 结果冒充 deterministic hard gate
- 对未标准化 Markdown 伪造 PASS
- 宣称 Gate 证明了产品方案合理，或用 Gate PASS 覆盖 stale/`REVISE` 的 Product Review
- 重新引入「可开发 / 研发可直接开工」作为质量口径
