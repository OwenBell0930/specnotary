# 人读视图口径

人读 Markdown 是机读 YAML 的说明书投影，不是第二份准据。渲染器只摆放机读里已有的字段，并把**机读 ID 展开成中文**。

## 人读里该看见什么

| 机读里的东西 | 人读怎么写 | 反例 |
|--------------|------------|------|
| `empty_states.file_too_large` | 「单个文件不能超过 50MB」 | 展示 file_too_large |
| 状态枚举 `terminated`（有 `states.labels.import_terminated` 或 `value_labels`） | 已终止（`terminated`） | 状态变为 terminated |
| 业务动作 `create_import_task` | 创建导入任务（`create_import_task`） | 只写英文，像接口名 |
| 角色 `corpus_admin` / `system` | 语料管理员（`corpus_admin`） | 显示条件里留裸 ID |
| 字段名 `created_at`、错误码、`spec_refs` | 保持机读 ID（对账列） | 把字段名翻译成另一套 |

`terminated` 与 `import_terminated` 不是两种状态：前者是任务字段的枚举值，后者是状态矩阵里的 lifecycle id。人读都要用同一套中文，括号里保留各自的机读 ID。

## 改漏了一个 ID 家族时怎么修

不要补那一句人读。按这次顺序做：

1. 机读是否已有中文（`empty_states` / `labels` / `action_labels` / `value_labels` / `actors[].zh`）。
2. 渲染器 `_human_id_pairs` 是否收录了这一族，以及 `prose()` 是否覆盖了那一章的字段（Given/Then、控件显示条件、字段说明、默认值列表、错误触发）。
3. 递增 `RENDERER_VERSION`，重生样例人读，加一条测试钉住「正文不得出现裸枚举」。

当前渲染器版本以代码里的 `RENDERER_VERSION` 为准（文档自检会核对「渲染器 vN」）。

## 输出自检报告

给产品经理开会看，不是给开发对账看。由 `specnotary report` 生成，禁止手改。

| 别只写 | 要写成 |
|--------|--------|
| WARN | 需要你拍板：规格补了原文没有的猜测，或可点页面稿还没核实。不挡结构过关，但业务上你还没认。 |
| FAIL | 必须改：有一条就不能当终稿。 |
| PASS | 结构通过（PASS）：规则里自洽，可以开会。不表示业务已拍板。 |
| covered / assumption / conflict | 已写入规格 / 原文没写、规格补了猜测 / 原文互相打架 |
| `B-CAT-01, btn_cat_create` | 功能「创建分类」（`B-CAT-01`）；页面控件「新建分类」（`btn_cat_create`） |
| SRC-CLM-001 不解释 | 原料条目编号：从原始需求说明拆出来的每一条，只用来对账，不是页面编号 |

跟用户说话时同样禁止只甩这些英文。

## 跟用户指路

不要写「请刷新 `human/spec.md`」（短名会打开产品仓里的商城样例）。不要写成 Markdown 超链接并把空格换成 `%20`（`Cursor%20Projects` 会被当成真实文件夹名，提示 File not found）。

写法：反引号里写完整绝对路径，空格就是空格，不要 `%20`，不要包成 `[文字](路径)`。练习规格在产品仓同级沙箱 `specnotary-sandbox/corpus-import-vdb/human/spec.md`。

需要对方看见文件时，由助手打开该路径，不要让用户去点聊天里的链接。
