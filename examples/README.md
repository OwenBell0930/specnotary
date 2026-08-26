# Examples

主题：评审就绪的标准需求规格样例（虚构脱敏）

| 案例 | 说明 | 门禁 |
|------|------|------|
| [case-order-cancel-raw](case-order-cancel-raw/) | 运营约束 → 评审规格级机读/人读 | PASS |
| [case-order-cancel-bad](case-order-cancel-bad/) | 假详细 → FAIL；修好稿 PASS | FAIL→PASS |
| [case-order-cancel-ops-faq](case-order-cancel-ops-faq/) | 客服 FAQ 反推 | PASS |
| [case-list-search](case-list-search/) | 商品列表搜索（通用 `action_matrix`） | PASS |
| [product-review-fixture](product-review-fixture/) | 产品审查报告**形状**样例（非真实审查结论） | Schema 形状 |

人读含：线框、控件表、状态/动作矩阵、编号主路径、AC、Pending、原料覆盖表。
覆盖报告：`./cli/run-report.sh <machine.yaml>`。
原型：`case-order-cancel-raw/prototype/`（对齐）与 `prototype-drift/`（故意漂移）。
