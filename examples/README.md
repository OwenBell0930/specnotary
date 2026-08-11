# Examples

主题：可开发规格 + 评审就绪样例（虚构脱敏）

| 案例 | 说明 | 门禁 |
|------|------|------|
| [case-order-cancel-raw](case-order-cancel-raw/) | 运营约束 → 施工图级机读/人读 | PASS |
| [case-order-cancel-bad](case-order-cancel-bad/) | 假详细 → FAIL；修好稿 PASS | FAIL→PASS |
| [case-order-cancel-ops-faq](case-order-cancel-ops-faq/) | 客服 FAQ 反推 | PASS |
| [case-list-search](case-list-search/) | 商品列表搜索（通用 `action_matrix`） | PASS |

人读含：线框、控件表、状态/动作矩阵、编号主路径、AC、Pending、原料覆盖表。  
覆盖报告：`./cli/run-report.sh <machine.yaml>`。
