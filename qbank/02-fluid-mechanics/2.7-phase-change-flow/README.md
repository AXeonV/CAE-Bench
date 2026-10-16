# 2.7 热质交换及相变多相流动

考生阅读入口为各题 `instruction.md`、同目录 `DATA.md` 与[通用契约](../../../docs/CONTRACT.md)；每题两份文件完整说明该题物理、参数、数据、资源和评分。

| 编号 | 题目 | 配置 |
|---|---|---|
| 2.7.1 | [三维不相变相间热质交换](interphase-exchange-3d/instruction.md) | 3D / `fluid-multiphase-interphase-exchange-v1` |
| 2.7.2 | [二维蒸发冷凝界面流动](evaporation-condensation-2d/instruction.md) | 2D / `fluid-multiphase-evaporation-condensation-v1` |
| 2.7.3 | [三维均匀混合沸腾流动](boiling-3d/instruction.md) | 3D / `fluid-multiphase-boiling-v1` |
| 2.7.4 | [三维等温空化流动](cavitation-3d/instruction.md) | 3D / `fluid-multiphase-cavitation-v1` |
| 2.7.5 | [二维熔化凝固伴随流动](melting-solidification-2d/instruction.md) | 2D / `fluid-multiphase-melting-solidification-v1` |

题面与必要协议已建设；独立审阅和数据阶段状态由章级维护记录单独报告。examples/references/cases未生成实际数据，未发布评测。

维护状态：各题资源与容差保留既有设计目标，尚待真实算例校准；数据制作须提供同预算独立基准、网格/时间误差和模型适用性证据，区分数值误差、模型误差与测量不确定度，不以复现来源软件或结构检查通过替代验证。pressure 及派生质量率的起始有限唯一右迹也须建立证据；不以任意离散压力或差分率代替。协议测试的临时 fixture 不作题库数据。
