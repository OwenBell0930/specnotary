# Contributing

感谢关注 SpecNotary。SpecNotary 的核心承诺是：**门禁只做确定性判定，不假装读懂自然语言**。所有贡献都不得破坏这一点。

## 开发环境

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .          # 依赖仅 pyyaml + jsonschema
python3 tests/test_cli.py # 全量回归（无 pytest 依赖）
```

## 改动规则

1. **每条新 FAIL/WARN 规则必须带一个会失败的测试。** 只有样例全绿不算证据；测试必须证明「坏输入确实被拦下」。
2. **机读 Schema / 规则语义变化必须同步三处**：`src/specnotary/schemas/`、`docs/gate-modes.md`、README 能力表。
3. **改了渲染器（`render_human`）必须递增 `RENDERER_VERSION`** 并重新生成 `examples/**/human/spec.md`，否则所有人读会以费解的方式 stale。
4. **Node 目录只允许存在拒绝执行的 stub。** 不要提交任何第二套规则实现。
5. 样例一律虚构业务；禁止提交真实公司 PRD、内部资料或本机绝对路径。

## 提交前自查

```bash
python3 tests/test_cli.py                                        # 必须全绿
./cli/run-check.sh examples/case-order-cancel-raw/machine/spec.yaml   # PASS
./cli/run-check.sh templates/machine/spec.template.yaml               # PASS (draft)
```

## 规则分层速查

| 层 | 位置 | 效力 |
|----|------|------|
| JSON Schema | `src/specnotary/schemas/` | 类型/枚举/必填 |
| 结构与引用 | `libspec._layer_structure` | ID 唯一、跨引用、矩阵 |
| ready 完备性 | `libspec._layer_ready` | 占位与空话否决 |
| 原料覆盖 | `libspec._validate_source_layer` | SourceClaim 证据链 |
| 人读防漂 | `libspec._validate_human_stale` | spec_hash + body_hash + renderer_version |
| 原型一致性 | `libproto.validate_prototype` | manifest 哈希 + HTML 落点 |
