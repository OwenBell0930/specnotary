# 什么叫「可开发的需求规格说明书」 / Dev-ready Requirements Spec

## 中文（最终态）

本工具产出的正式名字是：**可开发的需求规格说明书**。  
它不是完整商业 PRD 百科，而是研发/测试/Agent **能开工、能验收** 的规格契约。写作由 Skill 起草，质检由 CLI 判定；用户只输入原料、确认结果、拿报告去评审。

机读（YAML/JSON）= 唯一准据（改这里）；人读（Markdown）= 同一契约的说明书视图（由 CLI 生成）。

一份规格算**可开发**，当下游不必靠作者口述补洞也能开工，并且关键行为说得出怎么算做完。

### 必须具备

1. **范围清楚**：做什么 / 不做什么；未决项单独列出，不装成已定。  
2. **对象与状态清楚**：角色、权限、主数据、关键状态（含默认值）。  
3. **行为可观察**：主路径与主要异常路径写到可验收（Given-When-Then 或等价）。  
4. **接口感清楚**：关键输入输出、空结果、错误提示、并发或限额等默认策略（若适用）。  
5. **对象 AI（若启用）**：工具边界、失败降级、人工接管、不可接受输出。  
6. **机读准据完整**：人读只是投影；以机读通过硬门禁为准。人读正文用中文讲界面文案、状态和业务动作，机读 ID 只出现在括号或对账列。

### 不算可开发（典型假详细）

- 「支持智能取消」「体验要好、尽快退款」无可观察规则  
- 缺订单状态机、缺权限、缺空态/失败态  
- 人读写得很长，机读缺字段或与人读不一致  

### 非目标

- 不替代公司内部完整 PRD 法定模板全文  
- 不做重型规格驱动开发平台  
- 本期不做 Web/MCP 主产品  

## English (working)

**Dev-ready Requirements Specification** (not a full business PRD encyclopedia). Machine YAML/JSON is the source of truth; human Markdown is the generated reading view. Implementers can start without private verbal gaps; critical behaviors have observable done-criteria.
