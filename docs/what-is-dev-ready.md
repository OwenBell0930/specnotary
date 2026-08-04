# 什么叫「可开发」规格 / What “dev-ready” means

## 中文（最终态）

一份规格算**可开发**，当下游（研发、测试，或按规格实现的 Agent）**不必靠作者口述补洞**也能开工，并且关键行为**说得出怎么算做完**。

### 必须具备

1. **范围清楚**：做什么 / 不做什么；未决项单独列出，不装成已定。  
2. **对象与状态清楚**：角色、权限、主数据、关键状态（含默认值）。  
3. **行为可观察**：主路径与主要异常路径写到可验收（可用 Given-When-Then 或等价写法）。  
4. **接口感清楚**：关键输入输出、空结果、错误提示、并发或限额等默认策略（若适用）。  
5. **对象 AI（若本项目启用）**：工具边界、失败降级、人工接管、不可接受的输出类型；阈值可后补但不得用空话顶替。  
6. **机读主源完整**：人读只是机读的可读投影；以机读通过检查为准。

### 不算可开发（典型假详细）

- 只有目录和形容词（「支持搜索」「智能优化」）无可观察规则  
- 缺默认值、缺权限、缺空态/失败态  
- 人读写得很长，但机读缺字段或与人读不一致  
- 用写作助手的口吻代替产品决策  

### 非目标

- 不替代公司内部法定模板全文  
- 不做完整规格驱动开发（SDD：先规格后实现）重型流水线平台  
- 不在本期做 Web/MCP 主产品  

## English (working)

A spec is **dev-ready** when implementers can start without private verbal gaps, and critical behaviors have observable done-criteria. Machine-readable YAML/JSON is the source of truth; human docs are generated views. Open questions must be explicit. Empty marketing language is not a substitute for decisions.
