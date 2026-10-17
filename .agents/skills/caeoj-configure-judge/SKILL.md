---
name: caeoj-configure-judge
description: 将 CAE-Bench-OJ 题面和 DATA 的评分、执行要求映射到当前配置与判题框架，按需修复适配并验证实际生效。
---

# 评测配置

读取题目 instruction.md、DATA.md 和 CONTRACT，按[配置流程](references/workflow.md)建立“公开要求→配置／实现→实际生效证据”的映射。当前配置消费见[评测维护说明](../../../qbank/maintenance/EVALUATION.md)，源码入口见[定位索引](references/current-backend.md)。

每个case的reference/grading.json是实际判题唯一配置；author/grading-template.json仅用于制数，judge-config.json只拥有执行设置，缺case配置即停止。适用指标的 atol/rtol 来自明确的数值规则，不补默认值或另设容差入口。输出对象名、quantity、评价项及HDF5 key分别绑定，不靠猜测补字段。资源可由模板继承，记录合并后的值及消费者；JSON/TOML 可解析不代表限制或判据实际生效。

框架足够时只改配置；有缺口时按[实现职责](../../../qbank/design/CORE-AND-EXTENSIONS.md)做必要适配。保持公开评分、配置和执行等价，不以放宽阈值、减少输出或取消隔离换取可运行。评分／资源目标缺失反馈出题，字段问题反馈 DATA，实际数据冲突反馈数据审计；不递归扩大任务。

按风险验证策略覆盖、阈值边界、非法输出、程序失败与基础设施错误、资源及总预算，以及公开工具／verifier 一致性。装配变更时验证公开包独立安装；细节见流程。重大框架或评分适配须独立 subagent 审阅需求映射和测试证据，再处理意见；无法执行时注明缺口。

无正式数据可完成配置和临时 fixture 验证，明确待绑定项；不制作假正式包。独立考生文档审阅可复用匹配版本记录，但不能替代实际加载与执行验证。

交付配置及必要实现、要求映射和证据；区分文本完成、数据绑定、框架支持、实际执行、容差／资源校准及发布状态。数据或配置变更后重建受影响产物。实际模型评测由 [caeoj-run-benchmark](../caeoj-run-benchmark/SKILL.md) 协调，不默认追加收费运行或发布。
