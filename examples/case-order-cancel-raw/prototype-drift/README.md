# 故意漂移原型

对照 `../prototype/` 的对齐稿。本目录用于演示 P2 门禁：

- 旧 Spec 哈希 → stale
- 缺必需控件映射 → missing
- 引用不存在的控件 → mismatch
- 无规格业务动作 → extra
- 装饰无引用 → 不阻塞
- `semantic_warnings` → WARN（unverified）

检查：

```bash
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "cli/python")
from libspec import load_spec, validate
root = Path("examples/case-order-cancel-raw")
data = load_spec(root / "machine/spec.yaml")
print(validate(data, {}, spec_path=root/"machine/spec.yaml",
               manifest_path=root/"prototype-drift/prototype.manifest.yaml"))
PY
```
