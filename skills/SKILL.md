---
name: specnotary
description: >
  Use when the user works on SpecNotary or needs a spec written and checked.
  Talk to the product manager in raw material / confirm / review pack only;
  run the CLI yourself. Draft IA → behaviors → YAML → prototype, then gate.
---

# SpecNotary Skill（写作执行器）

产品经理只做三件事：**交出原料、确认结果、拿材料去评审**。检查步骤由你来跑，不要让她操作内部工具或改内部文件。

用户把 GitHub 网址发给你时：不必要求她把 SpecNotary 设成当前工作区。在她已经打开的文件夹里写规格即可。安装：

```bash
pip install "git+https://github.com/OwenBell0930/specnotary.git"
```

若她已经克隆了源码，也可用 `pip install .`。然后按下面顺序工作。对她只问：还缺什么原料、这几条假设认不认、评审材料在哪个文件。

```bash
specnotary new <case-dir> --from <raw-file> [--kind ops|prd|faq|speckit|ticket|raw] [--id]
# …本 Skill 起草机读 / 人读 / 原型…
specnotary check <machine.yaml> --explain
specnotary sync <machine.yaml>                    # 人读；原型须另 --attest-prototype
specnotary confirm <machine.yaml> --by <name> --reason "<why>" --accept-all-warn
specnotary report <machine.yaml>                  # 写出输出自检报告，给她开会
```

GitHub spec-kit / OpenSpec 的 `spec.md` **不要试图一键转 YAML**。登记为原料：

```bash
specnotary ingest <spec.md> --spec <machine.yaml> --kind speckit
```

## Rules

1. **Machine source is authoritative.** Edit YAML first; generate the human 可开发的需求规格说明书 from it.
2. Prefer **YAML**. Human view must include wireframe, controls table, state/action matrix, numbered steps, AC, Pending five-fields.
3. Before claiming PASS: run `specnotary check` — **FAIL must be 0**. Remaining WARN: ask the product manager in plain language（需要你拍板：原文没写、规格补了猜测，认不认）；then **you** run `specnotary confirm --by --reason --accept-all-warn`（记下是谁、哪天、为什么）。不要让她自己执行这条命令，也不要口头说「已经接受」却不入账。对她不要只说 WARN / FAIL / PASS。
4. Hard gate runtime is **Python only**. Node CLI is Deferred — it exits 3 and must never print `gate_mode: hard` / `RESULT: PASS`.
5. If no Python: degraded Skill check with `gate_mode: degraded` only.
6. Never long-term edit only the human doc. Generator refuses to write when machine has FAIL (unless `--allow-invalid`). After machine edits run `specnotary sync` to refresh the hash chain.
7. Do not copy proprietary scaffold/business PRDs into the product tree; fictional examples only.
8. Use `states.action_matrix` (`state` / `action` / `allowed`); `cancel_matrix` is legacy.
9. Dual goals: **dev-ready** specs + **review-ready** intake. Prototype check runs only when a manifest exists; otherwise WARN and skip.
10. For drafts, use `specnotary check --explain` to enumerate the READY-GAP instead of guessing.
11. **CLI does not understand natural language.** `new` / `ingest` only copy the file and pin `content_hash`. You extract claims. Empty-talk calibration: [`docs/empty-talk-corpus.md`](../docs/empty-talk-corpus.md).
12. **假详细分两层。** 硬检查只扫已知词表（含「形成闭环」「治理体系」「赋能」「抓手」等口号搭配）。词表漏掉的、听起来完整但研发仍要猜按钮/状态/失败文案/默认值的句子（例如「本模块治理到位」「业务跑通」「与周边系统对齐」），你必须用语义拦住：标 assumption 或 pending，问产品经理，禁止标 covered。不要把这类句子交给硬检查去「读懂」——硬检查不做语义公证，结构通过不等于句子已经可开发。
13. **人读正文用中文。** 界面文案走 `empty_states`；状态名走 `states.labels` / `value_labels`；可执行动作是业务动作（`action_labels`），不是接口路径。用户抱怨人读全是英文 ID 时：补机读中文 + 改渲染器全量展开 + 升 `RENDERER_VERSION`，禁止只改人读 Markdown。见 [`docs/human-view.md`](../docs/human-view.md)。给她看的输出自检报告同样：处理结果、结论、落到哪一段都用中文；原料条目编号要解释。
14. **跟人说话时写绝对路径。** 禁止只写 `human/spec.md`（会打开商城样例）。禁止把路径空格写成 `%20` 再做成 Markdown 链接（Cursor 按字面找文件，会 File not found）。空格保持为空格，放在反引号里；需要她看文件时由你打开，不要让她点聊天超链接。练习规格在产品仓同级沙箱 `specnotary-sandbox/corpus-import-vdb/`。

## 写作主路径（按这个顺序写机读）

`specnotary new` 只给草稿脚手架和已钉哈希的原料。你补全：

1. **原料账本** — `sources[]` 已由 `new`/`ingest` 登记。从 `input/` 拆 `source_claims`（见下）。
2. **产品 / 信息架构** — `in_scope` / `out_of_scope` / `overview` / `architecture.mermaid` / `responsibilities` / `actors` / `permissions`。
3. **功能与交互** — `states.lifecycle` + `states.labels` / `action_labels` / 必要时 `value_labels` + `action_matrix`；`ui.entry` / `wireframe` / `controls`（含 `visible_when`、失败文案）；`defaults`；`empty_states`（界面原文）；`behaviors`（given/when/then 可观察，可用机读键，人读会展开成中文）；`acceptance`；`data_contracts`；`error_codes`；`decisions`（未拍板不得 `ready`）；`pending` 五字段。
4. **静态原型** — `prototype/main.html`（或框架源）每个业务控件 `data-spec-id`；同步 `prototype.manifest.yaml`。
5. **质检** — `check` → `sync`（改机读后）；原型复核后 `--attest-prototype`；产品经理确认假设后由你 `confirm` + `report`。

## 起草全局视角（判断性文字写进机读）

渲染器只摆放、不创作：

- `overview`：summary（谁在什么场景做什么）+ design_principles（评审最常问的取舍）+ environment_constraints
- `architecture.mermaid`：调用关系图源码（进哈希链防漂）
- `responsibilities`：每个角色 owns / not_owns
- `data_contracts`：实体字段表 + 规则
- `error_codes`：code / 触发 / 可重试 / 用户文案
- `decisions`：分歧点 + 选项 + 拍板结果；**未拍板不得标 ready**

## 提取 SourceClaim

每条 claim 必须有：

- `id`、`source_ref`（指向 `sources[].id`；ready 上 `sources[].path` 必须真实存在且带 content_hash）
- `quote_or_summary` 或 `evidence`（证据位置：文件 + 行/段落）
- `disposition`：`covered` | `omitted` | `assumption` | `conflict` | `out_of_scope` | `pending`
- `covered` 必须带 `spec_refs`，且只能指规格实体（behavior / AC / 控件 / `defaults.x` / `empty_states.x`）

ready 的硬要求：至少 1 条 `covered`；每个必选 behavior/AC/control 都被某条 claim 引用（`coverage_optional: true` 可豁免）。

源外推断标 `assumption`，不要写成 `covered`。assumption 是 WARN，由用户 `confirm` 入账，不要改成 FAIL。

## 生成原型时必须同步 Manifest

CLI **不解析任意前端框架**。生成可演示原型时必须同时写 `prototype/prototype.manifest.yaml`。

- 每个业务控件加稳定标记：`data-spec-id="<机读控件或行为 ID>"`（写进真实 DOM/JSX，注释不算）
- 存量项目先跑 `specnotary markers <machine.yaml> <源码目录>` 对账缺哪些标记，回填后再写 manifest
- `generated_from_spec.hash` = 当前机读 `spec_hash`（`specnotary check` 会打印）。改机读后该哈希**不会**被自动刷新：先复核原型是否仍与新机读一致，再显式 `specnotary sync <spec> --attest-prototype` 背书
- 规格里未标 `prototype_optional` 的控件 / 行为必须映射
- 无规格引用的控件/交互 → FAIL（仅 `role: decoration|visual` 豁免）；interaction 的 `from/to/trigger` 必须指向已声明的 id
- LLM 对截图/文案的怀疑只能进 `semantic_warnings`（WARN，须带 evidence + confidence）

然后跑：

```bash
specnotary check <machine.yaml> [human.md] [prototype.manifest.yaml]
```
