# 2.1 不包含能量、湍流的单相流动分析

本目录维护 12 道题的题面。考生入口是各题 instruction.md；每题仅依赖本题 instruction.md、DATA.md 和通用 CONTRACT.md；不需读取节级共享文件或领域维护规范。设计依据见 [第 2 章规划](../../design/chapter-02-fluid-mechanics.md)。

| 编号 | 题面 | task |
|---|---|---|
| 2.1.1 | [2D 常黏度牛顿流体不可压缩流动稳态分析](newtonian-incompressible-steady-2d/instruction.md) | `newtonian-incompressible-steady-2d` |
| 2.1.2 | [2D 常黏度牛顿流体不可压缩流动瞬态分析](newtonian-incompressible-transient-2d/instruction.md) | `newtonian-incompressible-transient-2d` |
| 2.1.3 | [3D 常黏度牛顿流体不可压缩流动稳态分析](newtonian-incompressible-steady-3d/instruction.md) | `newtonian-incompressible-steady-3d` |
| 2.1.4 | [3D 常黏度牛顿流体不可压缩流动瞬态分析](newtonian-incompressible-transient-3d/instruction.md) | `newtonian-incompressible-transient-3d` |
| 2.1.5 | [2D 非牛顿流体不可压缩流动稳态分析](generalized-newtonian-incompressible-steady-2d/instruction.md) | `generalized-newtonian-incompressible-steady-2d` |
| 2.1.6 | [2D 非牛顿流体不可压缩流动瞬态分析](generalized-newtonian-incompressible-transient-2d/instruction.md) | `generalized-newtonian-incompressible-transient-2d` |
| 2.1.7 | [3D 非牛顿流体不可压缩流动稳态分析](generalized-newtonian-incompressible-steady-3d/instruction.md) | `generalized-newtonian-incompressible-steady-3d` |
| 2.1.8 | [3D 非牛顿流体不可压缩流动瞬态分析](generalized-newtonian-incompressible-transient-3d/instruction.md) | `generalized-newtonian-incompressible-transient-3d` |
| 2.1.9 | [2D 常黏度牛顿流体等温可压缩流动稳态分析](newtonian-isothermal-compressible-steady-2d/instruction.md) | `newtonian-isothermal-compressible-steady-2d` |
| 2.1.10 | [2D 常黏度牛顿流体等温可压缩流动瞬态分析](newtonian-isothermal-compressible-transient-2d/instruction.md) | `newtonian-isothermal-compressible-transient-2d` |
| 2.1.11 | [3D 常黏度牛顿流体等温可压缩流动稳态分析](newtonian-isothermal-compressible-steady-3d/instruction.md) | `newtonian-isothermal-compressible-steady-3d` |
| 2.1.12 | [3D 常黏度牛顿流体等温可压缩流动瞬态分析](newtonian-isothermal-compressible-transient-3d/instruction.md) | `newtonian-isothermal-compressible-transient-3d` |

## 维护状态与数据建设

本次完成题目文字与公开契约；各题 examples、references、cases 仅保留空目录占位，不含任何数值输入、答案或来源数据。它们依次用于公开输入输出样例、参考及溯源资料、算例输入。正文中的 JSON 片段仅说明格式，不是算例。

这些题尚未发布为可运行评测。既有 tasks 不迁移，发布器仍要求实际公开数据，不能用本次目录占位生成正式解题包。发布时须将各题 instruction.md、DATA.md 及通用 CONTRACT.md 一并提供，不向考生发布本维护说明或设计规划。数据完备后再接入发布和评测工具。

各题 instruction.md 中的误差阈值与资源是本版题目目标，尚无算例校准证据。后续数据建设须验证：物理适用性与适定性、稳态存在及分支确定性、初边值相容性、压力和出口语义、材料响应、数值参考精度、规定预算内的可解性，以及对声明范围的覆盖。参考误差应明显小于评分容差；不得仅凭输入校验通过或来源软件收敛就发布。若证据要求修改公开阈值或范围，应修订题目版本并在评测前统一冻结，不得暗改。

算例来源只进入各题 examples、references、cases；题面不包含来源软件配置、隐藏测试清单、参考算法或针对特定求解器的提示。
