# 故意漂移原型

对照 `../prototype/` 的对齐稿。此目录用于演示原型一致性门禁：

- 旧 Spec 哈希 → stale
- 缺必需控件映射 → missing
- 引用不存在的控件 → mismatch
- 无规格业务动作 → extra
- 装饰无引用 → 不阻塞
- `semantic_warnings` → WARN（unverified）

检查（显式把漂移 manifest 传给门禁）：

```bash
./cli/run-check.sh examples/case-order-cancel-raw/machine/spec.yaml \
  examples/case-order-cancel-raw/human/spec.md \
  examples/case-order-cancel-raw/prototype-drift/prototype.manifest.yaml
```

预期 `RESULT: FAIL`，报告里按 missing / extra / stale / mismatch / unverified 归桶。
