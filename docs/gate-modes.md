# 门禁模式 / Gate modes

| 模式 | 何时 | 效力 |
|------|------|------|
| `hard` | 本机 Python/Node CLI 已执行 | 可作为本地「自动测试跑通」依据 |
| `degraded` | 无运行时，Skill+LLM 代跑 | **仅参考**；不得冒充 hard PASS |

## hard 结果分层（对齐可入库思想）

| 级别 | 含义 | 处理 |
|------|------|------|
| **FAIL** | 结构缺失、ready 却空话、Pending 未闭合等 | 必须修到 0 条 FAIL |
| **WARN** | 缺线框/空态等会降低可开发性，但未达一票否决 | 尽量清零；保留须人工确认 |
| **PASS** | FAIL_COUNT=0 | 若仍有 WARN，标注「PASS with WARN」 |

## Pending 四要素（status=ready 时）

每条待闭合必须含：`id` · `missing` · `impact` · `owner` · `status`。  
`status=ready` 时不得残留 `open` / `待确认` 的 Pending。
