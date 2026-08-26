# SpecNotary 助手约定

机读 YAML 是唯一准据。人读 Markdown 由渲染器生成，禁止长期手改。

**三项能力、一套质量模型：** Draft（起草）/ Review（独立产品质量审查）/ Gate（确定性结构门禁）。默认全流程用 `skills/specnotary/SKILL.md` 与 `/write-spec`；单能力用 `skills/specnotary-draft|review|gate` 与 `/draft-spec` `/review-spec` `/gate-spec`。公共标准只在 `docs/product-quality-model.md`，禁止复制多份。Draft 不自评；Review 禁止 `PRODUCT_REVIEW: PASS`；Gate 不做商业边界/UX 优劣判断。最终分开展示 Draft / Product Review / Structure Gate / 待拍板。已有文档可跳过 Draft，只走 Review + Gate；普通 Markdown 未 normalize 不得 hard PASS。

人读正文必须用中文讲界面文案、状态和业务动作；`file_too_large`、`terminated`、`create_import_task` 这类机读 ID 只出现在括号或对账列。用户抱怨人读全是英文 ID 时：补机读中文标签，改渲染器全量展开，递增 `RENDERER_VERSION`，不要只改那一句人读 Markdown。

假详细分两层：硬检查扫词表；词表漏掉的口号（「治理到位」「业务跑通」）由助手用语义拦住，不能当成结构已经过关。结构合法但方案不合理的反例见 `docs/product-review-corpus.md`。

给产品经理看的文件（说明书、输出自检报告、产品审查报告）和聊天：禁止只甩 WARN / FAIL / covered / assumption。必须改 / 需要你拍板 / 已写入规格 / 原文没写、规格补了猜测。原料条目编号要说清楚是从原始说明拆出来的对账编号。Structure Gate 通过不等于产品方案合理。

跟用户指路：反引号里写带真实空格的绝对路径，禁止只写 `human/spec.md`，禁止把空格写成 `%20` 再做成超链接。短名会打开商城样例；`%20` 会 File not found。需要她看文件时由助手打开，不要让她点聊天链接。

详见 `docs/human-view.md`、`docs/product-quality-model.md`、`docs/skill-boundary.md`、`skills/specnotary/SKILL.md`、`.cursor/rules/human-view-zh.mdc`、`.cursor/rules/cite-spec-path.mdc`。
