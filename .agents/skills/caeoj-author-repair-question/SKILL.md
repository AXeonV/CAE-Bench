---
name: caeoj-author-repair-question
description: 从开源求解器的真实 issue 与修复证据中筛选候选，或将其制作为 CAE-Bench-OJ 源码修复题；覆盖缺陷复现、参考验证、可信编译判题及既有出题流程衔接。
---

# 真实求解器修复题

把真实缺陷转化为考察可复用求解器修复能力的问题族。仅搜集来源时交付候选与证据；要求出题时再落实规划、公开材料、判题和数据；实际 Benchmark 仅在本次任务包含时运行。

先读[题库哲学](../../../qbank/PHILOSOPHY.md)和目标章规划。无需按现有题目筛 issue；可据有价值的缺陷提出单独章节，再由规划确定能力范围。issue 提供真实动机和取证入口，不自动定义整道题或每个算例。

## 工作流

1. **筛选与取证。** 按[来源与题目建设](references/workflow.md)记录 issue、解决讨论、PR／提交和复现材料。区分关闭、合并、实际检出与数值正确；证据不足就列缺口，不把“closed”当修复完成。
2. **定义修复能力。** 明确缺陷触发条件、可观测错误、要求保留的行为、问题族与提交边界。调用 [caeoj-author-question](../caeoj-author-question/SKILL.md) 完成必要规划、题面、DATA 及独立设计／考生审阅。限定源文件、入口或语言须由修复目标和现有库接口支持，并写入公开要求。
3. **复现与参考。** 固定缺陷基线及修复材料，在同一可信驱动下实际重放。按来源流程构建参考，用独立数学路径、另一实现、可核验实验或其他适合问题的依据核对。原件与修复版的差异仅证明检出能力；同一有缺陷实现产出和自检不构成独立正确性证据。
4. **接入判题。** 优先复用现有源码修复后端，按[可信构建与验证](references/backend.md)核对其适用范围，再由 [caeoj-configure-judge](../caeoj-configure-judge/SKILL.md) 配置及验证。需要框架适配时复用该技能要求的独立审阅，不为每题复制 verifier。
5. **制数与审计。** 按 [caeoj-source-cases](../caeoj-source-cases/SKILL.md) 建设有有效差异的实际算例，由 [caeoj-manage-data](../caeoj-manage-data/SKILL.md) 管理池与选样，并交 [caeoj-data-review](../caeoj-data-review/SKILL.md) 核对全部实际材料。明确原始复现、改编工况及新增回归，不冒称都来自 issue。
6. **按阶段验收。** 分别报告题面完成、缺陷检出、参考验证、公开包可用、可信后端验证、数据就绪和模型实测。用户要求 Benchmark 时交 [caeoj-run-benchmark](../caeoj-run-benchmark/SKILL.md)，沿用本次模型与尝试预算；低分不触发追加求解。

## 交付边界

- 公开 instruction／DATA／CONTRACT 足以独立做题；来源解释、参考生产、修复答案、验收证据放维护材料。公开源码保留许可证及必要归属信息，不能用“避免泄题”删除法定声明。
- 可信驱动只完成输入转换、库 API 调用和输出转换；不得替考生补缺失物理或纠正错误结果。若要求修复特定入口，数值成绩与方法合规分别核查，不能仅凭通过样例断言修复发生在该入口。
- 上游整项 PR 与实际应用的修复子集分别记录。题面缩小范围时说明覆盖及限制，不静默忽略仍属承诺范围的缺陷。
- Chrono 的历史型号、单文件约束、容差、算例数与构建限时都只是实例。后续题按其目标重新确定，不复制为默认规则。

首个实例的工具与证据入口见[Chrono 作者材料](../../../qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair/author/README.md)及[实施记录](../../../qbank/design/reviews/chrono-846-repair-implementation.md)；按需阅读，不把历史成绩写成操作规则。
