# 门禁模式 / Gate modes

| 模式 | 何时 | 效力 |
|------|------|------|
| `hard` | **Python** CLI 已执行（`./cli/run-check.sh`） | 可作为本地「自动测试跑通」依据 |
| `degraded` | 无 Python，Skill+LLM 代跑 | **仅参考**；不得冒充 hard PASS |

> **Node CLI：Deferred。** `cli/node/` 可能落后于 Python 规则，**不是**等价硬门禁。仅在显式 `SPEC_KIT_RUNTIME=node` 时使用，并会打印 WARN。

## hard 结果分层

| 级别 | 含义 | 处理 |
|------|------|------|
| **FAIL** | Schema 不通过、引用断裂、ready 却空话、Pending 未闭合等 | 必须修到 0 条 FAIL |
| **WARN** | 缺线框/空态、legacy `cancel_matrix` 等 | 尽量清零；保留须人工确认 |
| **PASS** | FAIL_COUNT=0 | 若仍有 WARN，标注「PASS with WARN」 |

## 校验分层（P0）

1. **JSON Schema**（`schemas/machine-spec.schema.json`）— 类型、enum、必填  
2. **确定性规则** — ID 唯一、跨对象引用、ready 完备性、Pending 四要素  

依赖：`pip install pyyaml jsonschema`

## Pending 四要素（status=ready 时）

每条待闭合必须含：`id` · `missing` · `impact` · `owner` · `status`。  
`status=ready` 时不得残留 `open` / `待确认` 的 Pending。

## 生成人读

`./cli/run-generate-human.sh` 在机读仍有 FAIL 时**拒绝写入**，除非传入 `--allow-invalid`。
