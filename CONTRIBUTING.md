# Contributing

感谢关注 SpecNotary。SpecNotary 的核心承诺是：**门禁只做确定性判定，不假装读懂自然语言**。所有贡献都不得破坏这一点。

## 开发环境

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                      # 依赖仅 pyyaml + jsonschema
python3 tests/test_cli.py             # 全量回归（无 pytest 依赖）
python3 tests/test_mutations.py       # 变异矩阵：打印 KILL_RATE，须 100%
python3 tests/test_doc_consistency.py # 文档声明与实现一致性
```

## 改动规则

1. **每条新 FAIL/WARN 规则必须带一个会失败的测试。** 只有样例全绿不算证据；测试必须证明「坏输入确实被拦下」。
2. **新增机读对象必须同时在 `tests/test_mutations.py` 补变异算子**（唯一性 / 引用闭合 / 自相矛盾，按适用性）。Schema 里新增的「对象数组」字段若没有对应变异家族，`test_matrix_covers_every_object_family` 会从 Schema 发现并 FAIL，不必再手抄名单。
3. **文档承诺变了，`tests/test_doc_consistency.py` 必须同步跟上。** 卖防漂的工具不能自己漂：能力表语义、渲染器版本、CLI 子命令与 flag 都由该测试对着代码校验。
4. **断言产物，不要只断言退出码。** 写文件的命令必须回读文件内容。只看退出码会把「没写出文件」认证成预期。
5. **收紧或放宽任何规则时，两个方向都要有测试。** 为消除误报而加的豁免最容易把规则改成废纸；为收紧而改的判据最容易误伤真实内容。参照 `test_sync_semantics_detector_is_calibrated` 与 `test_real_ui_literals_are_not_placeholders` 的成对写法。
6. **注意规则之间的豁免共用。** 空话检测豁免 `「…」`，占位检测不豁免。新增豁免时问一句：别的规则会不会顺着这个豁免漏掉东西。
7. **机读 Schema / 规则语义变化必须同步三处**：`src/specnotary/schemas/`、`docs/gate-modes.md`、README 能力表。
8. **改了渲染器（`render_human`）必须递增 `RENDERER_VERSION`** 并重新生成 `examples/**/human/spec.md`，否则所有人读会以费解的方式 stale。
9. **人读正文禁止用机读 ID 冒充文案/状态/动作。** 修法是渲染器 glossary 全量展开 + 机读补中文标签，不是手改 `human/spec.md`。口径见 [`docs/human-view.md`](docs/human-view.md)。
10. **Node 目录只允许存在拒绝执行的 stub。** 不要提交任何第二套规则实现。
11. **改空话 / 占位词表必须同步 [`docs/empty-talk-corpus.md`](docs/empty-talk-corpus.md)**，并由 `test_empty_talk_corpus` 回放。那是公开校准集，不是一般 NLP 引擎。词表漏网的假详细由 Skill 语义拦，不得写进硬检查。
12. 样例一律虚构业务；禁止提交真实公司 PRD、内部资料或本机绝对路径。

## 提交前自查

```bash
python3 tests/test_cli.py             # 全量回归，必须全绿
python3 tests/test_mutations.py       # KILL_RATE 必须 100%
python3 tests/test_doc_consistency.py # 文档与实现一致
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
| 负例覆盖度量 | `tests/test_mutations.py` | 变异算子 × 对象族 → KILL_RATE |
| 文档不漂 | `tests/test_doc_consistency.py` | 承诺语句对着代码校验 |
