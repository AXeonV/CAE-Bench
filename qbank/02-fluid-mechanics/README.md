# 第二章：流体力学分析

本章每道题的考生材料仅由本题 instruction.md、DATA.md 和通用 docs/CONTRACT.md 组成：instruction.md 给出任务、方法要求、资源和评分；DATA.md 就地定义该题全部物理参数、条件、采样与输出。无需阅读章节共享文件、领域协议、其他题目或维护记录。各节目录只承担导航作用。

65题的评分模板、judge及Harbor配置已按题面补齐，采用逐例quantity绑定；正式输入、参考及执行校准仍待建设。维护方流程与状态见[评测配置说明](../maintenance/EVALUATION.md)。

| 节 | 目录 | 题数 |
|---|---|---:|
| 2.1 | [无能量、无湍流单相流动](2.1-single-phase-flow/README.md) | 12 |
| 2.2 | [包含能量的单相层流](2.2-single-phase-energy/README.md) | 12 |
| 2.3 | [无能量的单相湍流](2.3-turbulent-flow/README.md) | 5 |
| 2.4 | [包含能量的单相湍流](2.4-turbulent-energy/README.md) | 4 |
| 2.5 | [不相变界面多相流](2.5-interface-flow/README.md) | 6 |
| 2.6 | [分散多相流](2.6-dispersed-flow/README.md) | 4 |
| 2.7 | [热质交换与相变流动](2.7-phase-change-flow/README.md) | 5 |
| 2.8 | [薄膜与润滑](2.8-thin-film/README.md) | 4 |
| 2.9 | [浅水与深度平均流动](2.9-shallow-water/README.md) | 4 |
| 2.10 | [稀薄气体](2.10-rarefied-gas/README.md) | 4 |
| 2.11 | [记忆与结构演化非牛顿流动](2.11-memory-fluids/README.md) | 5 |
| 2.13 | [CFDCodeBench 兼容题集](2.13-cfdcodebench/README.md) | 24 |

共计 **89 题**：65 道通用能力题与 24 道 CFDCodeBench 兼容题。2.13 的数据和验证状态见其[维护记录](2.13-cfdcodebench/author/README.md)。规划与维护状态见[逐题实施清单](../design/chapter-02-task-plan.md)及[章级进度与审阅证据](../design/reviews/chapter-02-progress.md)。本页是题库维护索引；正式提供考生材料时仅选择相应题目的完整公开依赖。

各题数据装配与发布状态由本题维护记录拥有，操作见[数据池操作](../maintenance/DATA-SYNC.md)。公开协议的最小测试 fixture 置于临时目录，不属于正式算例或参考答案；工具校验、数值验证与资源校准分别记录。
