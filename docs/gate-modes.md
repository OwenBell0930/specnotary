# 门禁模式 / Gate modes

| 模式 | 何时 | 效力 |
|------|------|------|
| `hard` | **Python** CLI 已执行（`./cli/run-check.sh`） | 可作为本地「自动测试跑通」依据 |
| `degraded` | 无 Python，Skill+LLM 代跑 | **仅参考**；不得冒充 hard PASS |

> **Node CLI：Deferred。** `cli/node/` 与 `SPEC_KIT_RUNTIME=node` **拒绝**冒充 hard PASS（退出码 3）。硬门禁只有 Python；无 Python 时用 Skill 并标 `gate_mode: degraded`。

## hard 结果分层

| 级别 | 含义 | 处理 |
|------|------|------|
| **FAIL** | Schema 不通过、引用断裂、ready 却空话、Pending 未闭合等 | 必须修到 0 条 FAIL |
| **WARN** | 缺线框/空态、legacy `cancel_matrix` 等 | 尽量清零；保留须人工确认 |
| **PASS** | FAIL_COUNT=0 | 若仍有 WARN，标注「PASS with WARN」 |

## 校验分层

1. **JSON Schema**（`schemas/machine-spec.schema.json`）— 类型、enum、必填  
2. **确定性规则** — ID 唯一、跨对象引用、ready 完备性、Pending 四要素  
3. **原料覆盖（P1）** — `sources[].path` 必须存在；ready 至少 1 条 `covered`；每个必选 behavior/AC/control 须被 claim 引用；`omitted` / 未闭合 `conflict` 在 `ready` 上 FAIL；`assumption` 为 WARN  
4. **人读 stale（P1）** — 人读头 `spec_hash` 必须等于当前机读内容哈希；正文须与按机读重渲染一致（只改正文也 FAIL）  
5. **原型一致性（P2）** — 若存在 `prototype/prototype.manifest.yaml`：哈希、必需控件/行为映射、禁止无规格业务动作、HTML `data-spec-id` 不计注释、映射控件 id 必须出现；`semantic_warnings` 仅为 WARN。无 manifest 时跳过（ready 下 WARN，不挡 PASS）  

依赖：`pip install pyyaml jsonschema`

## 评审就绪报告

```bash
./cli/run-report.sh examples/case-order-cancel-raw/machine/spec.yaml
```

输出 omitted / assumption / conflict / pending / out_of_scope 汇总。报告不是硬门禁本体；门禁仍以 `run-check.sh` 为准。

## Pending 四要素（status=ready 时）

每条待闭合必须含：`id` · `missing` · `impact` · `owner` · `status`。  
`status=ready` 时不得残留 `open` / `待确认` 的 Pending。

## 生成人读

`./cli/run-generate-human.sh` 在机读仍有 FAIL 时**拒绝写入**，除非传入 `--allow-invalid`。
