# 第二章：流体力学分析

本章每道题的考生材料仅由本题 instruction.md、DATA.md 和通用 docs/CONTRACT.md 组成：instruction.md 给出任务、方法要求、资源和评分；DATA.md 就地定义该题全部物理参数、条件、采样与输出。无需阅读章节共享文件、领域协议、其他题目或维护记录。各节目录只承担导航作用。

核心65题的评分模板、judge及Harbor配置采用逐例quantity绑定；另保留24道固定问题兼容题。配置、case装配、参考资格和发行验收分别记录，不能由目录存在推断就绪。维护流程见[评测配置说明](../maintenance/EVALUATION.md)，本次纳入范围与验证见[RC2记录](../design/reviews/release-assembly-rc2-2026-10-23/README.md)。

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
| 2.13 | [CFDCodeBench固定问题兼容专题](2.13-cfdcodebench/README.md) | 24 |

核心 **65题**，固定问题兼容专题 **24题**。核心规划见[逐题实施清单](../design/chapter-02-task-plan.md)，兼容专题单独报告成绩，不将其固定问题成绩外推为问题族泛化能力。本页是维护索引，开发目录和发行纳入范围分别管理。

实际选样以逐题data-manifest.json与装配回执为准，资格与未决项保留在对应维护证据。临时测试fixture不属于正式算例；格式样例只说明结构，不能作为数值参考。
