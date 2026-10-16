# 2.6 分散多相流动

考生阅读入口为各题 `instruction.md`、同目录 `DATA.md` 与[通用契约](../../../docs/CONTRACT.md)；每题两份文件完整说明该题物理、参数、数据、资源和评分。

| 编号 | 题目 | 配置 |
|---|---|---|
| 2.6.1 | [三维稀疏颗粒单向输运](passive-particles-3d/instruction.md) | 3D / `fluid-multiphase-passive-particles-v1` |
| 2.6.2 | [三维颗粒双向动量反馈](coupled-particles-3d/instruction.md) | 3D / `fluid-multiphase-coupled-particles-v1` |
| 2.6.3 | [三维气泡与液滴分散输运](bubbles-droplets-3d/instruction.md) | 3D / `fluid-multiphase-bubbles-droplets-v1` |
| 2.6.4 | [三维高浓度分散相流动](dense-dispersed-3d/instruction.md) | 3D / `fluid-multiphase-dense-dispersed-v1` |

题面与必要协议已建设；独立审阅和数据阶段状态由章级维护记录单独报告。examples/references/cases未生成实际数据，未发布评测。

维护状态：各题资源与容差保留既有设计目标，尚待真实算例校准；数据制作须提供同预算独立基准、网格/时间误差和模型适用性证据，区分数值误差、模型误差与测量不确定度，不以复现来源软件或结构检查通过替代验证。pressure 及派生质量率的起始有限唯一右迹也须建立证据；不以任意离散压力或差分率代替。协议测试的临时 fixture 不作题库数据。
