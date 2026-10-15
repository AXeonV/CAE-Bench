# 2.5 不相变界面多相流动

考生阅读入口为各题 `instruction.md`、同目录 `DATA.md` 与[通用契约](../../../docs/CONTRACT.md)；每题两份文件完整说明该题物理、参数、数据、资源和评分。

| 编号 | 题目 | 配置 |
|---|---|---|
| 2.5.1 | [二维自由液面瞬态流动](free-surface-2d/instruction.md) | 2D / `fluid-multiphase-free-surface-v1` |
| 2.5.2 | [三维自由液面瞬态流动](free-surface-3d/instruction.md) | 3D / `fluid-multiphase-free-surface-v1` |
| 2.5.3 | [二维不混溶双流体界面瞬态流动](immiscible-interface-2d/instruction.md) | 2D / `fluid-multiphase-immiscible-v1` |
| 2.5.4 | [三维不混溶双流体界面瞬态流动](immiscible-interface-3d/instruction.md) | 3D / `fluid-multiphase-immiscible-v1` |
| 2.5.5 | [二维毛细与润湿瞬态流动](capillary-wetting-2d/instruction.md) | 2D / `fluid-multiphase-wetting-v1` |
| 2.5.6 | [三维毛细与润湿瞬态流动](capillary-wetting-3d/instruction.md) | 3D / `fluid-multiphase-wetting-v1` |

题面与必要协议已建设；独立审阅和数据阶段状态由章级维护记录单独报告。examples/references/cases未生成实际数据，未发布评测。

维护状态：各题资源与容差保留既有设计目标，尚待真实算例校准；数据制作须提供同预算独立基准、网格/时间误差和模型适用性证据，区分数值误差、模型误差与测量不确定度，不以复现来源软件或结构检查通过替代验证。pressure 及派生质量率的起始有限唯一右迹也须建立证据；不以任意离散压力或差分率代替。协议测试的临时 fixture 不作题库数据。
