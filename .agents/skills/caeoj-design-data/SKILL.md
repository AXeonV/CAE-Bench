---
name: caeoj-design-data
description: 根据 CAE-Bench-OJ 题面设计自包含 DATA.md，明确输入输出与采样语义，反馈物理歧义，并在现有表示不足时补足接口能力。
---

# 数据契约设计

以 instruction.md 或用户给定题面为要求来源，读取 `docs/CONTRACT.md`。按[设计与验证流程](references/workflow.md)将任务事实、考生自由、算例变化量和观测映射为 DATA.md；题面不足时提出缺口及最小方案，出题任务中反馈 [caeoj-author-question](../caeoj-author-question/SKILL.md)。

DATA 完整定义本题字段、单位、条件、数组身份、空间／时间采样、输出和支持组合。通用结构引用 CONTRACT；任务、评分及资源由 instruction 拥有。考生无需其他题、维护文档或源码补定义。物理欠定、边界冲突或观测不唯一时给具体反例，不在接口中暗加模型或缩小范围。

先复用已有表示。确需实现拓展时按[职责设计](../../../qbank/design/CORE-AND-EXTENSIONS.md)定位核心、物理扩展、本题公开规则或维护工具，再按[运行说明](../../../qbank/maintenance/RUNTIME.md)核对真实接口及公开装配。只修改有缺口的层；HF 定位与装配属于[数据管理](../caeoj-manage-data/SKILL.md)，不进入 problem.json 的物理声明。

验证分为两部分：

- 维护方从最终 DATA 独立挑选有区分力的合法／非法变体，检查文档与工具双向一致；实现或装配变更时验证公开包独立安装和真实消费链，详见流程。
- 交付前调用 [caeoj-candidate-review](../caeoj-candidate-review/SKILL.md)，默认题面模式，可复用总出题流程对同一最终版本的审阅；修订后复核受影响内容。考生审阅不能替代工具验证。

临时 fixture 只用于接口验证，不写成正式数据。已有实际数据时交 [caeoj-data-review](../caeoj-data-review/SKILL.md) 做完整审计；无数据时如实标记未审计。

交付 DATA、必要题面修订及实现、审阅处理和验证证据。分别报告契约、工具、实际数据及数值／资源验证状态；本技能不默认制作数据或发布评测。
