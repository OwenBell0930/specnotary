# 什么叫「评审就绪的标准需求规格说明书」 / Review-ready Requirements Spec

## 中文（最终态）

SpecNotary 产出的正式名字是：**评审就绪的标准需求规格说明书**。
它不是完整商业 PRD 百科，也不是研发实施书或测试计划。它让产品经理在需求评审前把范围、产品/信息架构、角色、状态、交互、业务数据、错误定义、默认值、假设、冲突和未决摊开。写作由 Skill 起草，质检由 CLI 判定；用户只输入原料、确认结果、拿报告去评审。

机读（YAML/JSON）= 唯一准据（改这里）；人读（Markdown）= 同一契约的说明书视图（由 CLI 生成）。

一份规格算**评审就绪**，当参会者不必靠作者临场口述补洞，就能判断本期做什么、方案怎么运转、哪些地方还要拍板。

### 必须具备

1. **范围清楚**：做什么 / 不做什么；未决项单独列出，不装成已定。  
2. **产品与信息架构清楚**：核心业务对象、页面/模块层级、信息流和产品模块的负责/不负责边界明确；不把技术组件图冒充产品架构。
3. **对象与状态清楚**：角色、权限、主数据、关键状态（含默认值）。
4. **行为可观察**：主路径与主要异常路径写出前提、动作和可见结果（Given-When-Then 或等价），供评审逐条判断。
5. **方案口径清楚**：业务数据契约、关键输入输出、空结果、错误含义、触发条件、重试口径和用户文案属于标准产品定义；不在这里规定开发语言或测试方案。
6. **原型方案已拍板**：明确本次不制作，或明确静态 HTML、本地服务等载体；选择制作时原型必须与规格对账。
7. **对象 AI（若启用）**：工具边界、失败降级、人工接管、不可接受输出。
8. **机读准据完整**：人读只是投影；以机读通过硬门禁为准。人读正文用中文讲界面文案、状态和业务动作，机读 ID 只出现在括号或对账列。

### 不算评审就绪（典型假详细）

- 「支持智能取消」「体验要好、尽快退款」无可观察规则  
- 缺订单状态机、缺权限、缺空态/失败态  
- 人读写得很长，机读缺字段或与人读不一致  

### 非目标

- 不替代公司内部完整 PRD 法定模板全文  
- 不做重型规格驱动开发平台  
- 不生成技术栈、实现任务、测试策略、覆盖率或交付证据
- 本期不做 Web/MCP 主产品  

## English (working)

**Review-ready Requirements Specification** (not a full business PRD encyclopedia, implementation plan, or QA plan). Machine YAML/JSON is the source of truth; human Markdown is the generated review view. Reviewers can inspect scope, behavior, assumptions, conflicts, and open questions without relying on private verbal context.
