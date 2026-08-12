# 门禁模式 / Gate modes

| 模式 | 何时 | 效力 |
|------|------|------|
| `hard` | **Python** CLI 已执行（`specanvil check` / `./cli/run-check.sh`） | 可作为本地「自动测试跑通」依据 |
| `degraded` | 无 Python，Skill+LLM 代跑 | **仅参考**；不得冒充 hard PASS |

> **Node CLI：Deferred。** `cli/node/` 与 `SPECANVIL_RUNTIME=node` **拒绝**冒充 hard PASS（退出码 3），且不携带任何影子规则集。硬门禁只有 Python；无 Python 时用 Skill 并标 `gate_mode: degraded`。

## hard 结果分层

| 级别 | 含义 | 处理 |
|------|------|------|
| **FAIL** | Schema 不通过、引用断裂、ready 却空话/占位、原料文件缺失、人读/原型漂移、Pending 未闭合等 | 必须修到 0 条 FAIL |
| **WARN** | 缺线框/空态、legacy `cancel_matrix`、assumption 待确认等 | 尽量清零；保留须人工确认 |
| **PASS** | FAIL_COUNT=0 | 若仍有 WARN，标注「PASS with WARN」 |

## 校验分层

1. **JSON Schema**（`src/specanvil/schemas/machine-spec.schema.json`）— 类型、enum、必填  
2. **确定性规则** — ID 唯一、跨对象引用、ready 完备性（占位 ui/defaults/states 不算数；given/when/then 与 AC 非空且禁空话，`「…」`内的字面 UI 文案豁免；`in_scope` 非空）、Pending 五字段  
3. **原料覆盖** — `sources[].path` 必须存在；ready 至少 1 条 `covered`；每个必选 behavior/AC/control 须被 claim 引用；`omitted` / 未闭合 `conflict` 在 `ready` 上 FAIL；`assumption` 为 WARN  
4. **人读 stale** — 人读头 `spec_hash` 必须等于当前机读内容哈希；`renderer_version` 必须等于当前渲染器版本（版本不符给出单条「重新生成」提示）；正文须与按机读重渲染逐字一致（只改正文也 FAIL）  
5. **原型一致性** — 若存在 `prototype/prototype.manifest.yaml`：manifest 哈希、必需控件/行为映射、禁止无规格业务动作、HTML `data-spec-id` 落点核对（注释不算命中）、interaction `from/to/trigger` 不得断链、`required` screen 必须有 path；`semantic_warnings` 仅为 WARN。无 manifest 时跳过（ready 下 WARN，不挡 PASS）

依赖：`pip install .`（或仅 `pip install pyyaml jsonschema` 走 `cli/run-*.sh`）

## draft 差距报告

```bash
specanvil check <machine.yaml> --explain
```

对 draft 规格额外打印 `READY-GAP`：若现在把 `status` 翻成 `ready` 会新增哪些 FAIL。确定性 dry-run，判定零 LLM。

## 一键同步哈希链

```bash
specanvil sync <machine.yaml>
```

改机读之后：重新生成人读、刷新 `prototype.manifest.yaml` 的 `generated_from_spec.hash`、复跑门禁。机读本身有 FAIL 时拒绝同步。

## 评审就绪报告

```bash
specanvil report examples/case-order-cancel-raw/machine/spec.yaml
```

输出 omitted / assumption / conflict / pending / out_of_scope 汇总与原型问题归桶。报告不是硬门禁本体；门禁仍以 `specanvil check` 为准。

## Pending 五字段（status=ready 时）

每条待闭合必须含：`id` · `missing` · `impact` · `owner` · `status`。  
`status=ready` 时不得残留 `open` / `待确认` / `tbd` 的 Pending。

## 生成人读

`specanvil human`（或 `./cli/run-generate-human.sh`）在机读仍有 FAIL 时**拒绝写入**，除非传入 `--allow-invalid`。
