# 空话语料校准集

门禁扫的是**已知词表**，不是一般「可观察性」判断。改 `VAGUE` / `UNOBSERVABLE_AC` / 占位规则时必须改本文件，并由 `test_empty_talk_corpus` 对着基线规格回放。

位置：`ac` = `acceptance[].zh`；`then` = `behaviors[].then.zh`。

## 必须拦

| 位置 | 句子 |
|------|------|
| ac | 功能符合预期 |
| ac | 功能正常 |
| ac | 体验好 |
| ac | 界面足够美观 |
| ac | Users are satisfied |
| ac | The feature works |
| ac | works correctly |
| ac | good UX |
| ac | as fast as we can |
| then | 体验好就行 |
| then | 尽量快返回 |
| then | 智能化处理 |
| then | 智能搜索并展示 |
| then | 智能推荐相关商品 |
| then | 足够智能即可 |
| then | 智能地完成取消 |
| then | 方便地退款 |
| then | 尽快退款 |
| then | 尽量给用户好体验 |
| then | good UX overall |
| then | respond quickly |
| then | a seamless flow |
| then | an intuitive page |
| then | user-friendly cancellation |
| then | user friendly search |
| then | as fast as possible |
| then | blazingly fast results |
| then | best-in-class experience |
| then | 形成闭环 |
| then | 完善治理体系并赋能一线 |
| ac | 形成闭环 |
| ac | 治理体系完善 |

## 不得拦

这些句子必须**不**因空话、占位或「不可观察」被否决（其它规则另说）。

| 位置 | 句子 |
|------|------|
| ac | 关键词提交后 300ms 内列表仅含标题匹配行，空结果展示「没有符合条件的商品」 |
| ac | 输入「蓝牙」可看到标题含「蓝牙」的商品行 |
| ac | 材料状态变为待补充，页面展示缺失材料清单 |
| then | 点击「智能识别」后目录整树替换，编号重算 |
| then | 智能识别置信度低于 0.80 时转人工复核并记录 score |
| then | 订单从 unpaid 变为 cancelled，2 秒内关单且券释放 |
| then | 列表展示数据治理任务的名称与状态，失败展示「任务失败，请重试」 |

## 词表之外，须助手用语义拦

硬检查**不会**把下面这类句子判为必须改——它们没撞上词表，但研发仍要猜按钮、状态、失败文案。使用场景里助手本来就会读懂中文，起草时必须自己拦住：标「原文没写、规格补了猜测」或「还没定」，**禁止**标成已写入规格。

| 位置 | 句子 | 为什么假详细 |
|------|------|----------------|
| then | 本模块治理到位 | 没说谁在哪一页做什么、成功失败长什么样 |
| then | 业务跑通 | 没说状态怎么变、页面展示什么 |
| ac | 与周边系统对齐 | 没说对齐哪张表、失败怎么办 |

产品经理看到的「结构通过」只保证没撞词表、结构自洽。这类漏网要助手问你，或写进输出自检报告里需要你拍板。
