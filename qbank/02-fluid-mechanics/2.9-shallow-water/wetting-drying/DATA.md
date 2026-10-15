# 2.9.3 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-wetting-drying-v1`；spatial_dimension=2，瞬态start_time/end_time明确给定。

求单层浅水的湿润扩展和退水，允许初态与演化中的干区。干床状态、守恒变量和速度观测约定明确固定；不将任意数值干湿阈值作为物理参数。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `density`：`kg/m3`。
- `gravity`：`m/s2`。
- `drag_rate`：`1/s`。
- `start_time`：`s`。
- `end_time`：`s`。

必需域条件（location=`domain`、data只含value）：

- `bed`：role=material、operator=geometry，`m`、scalar、finite。
- `depth`：role=initial、operator=assign，`m`、scalar、nonnegative。
- `velocity`：role=initial、operator=assign，`m/s`、vector、finite。

允许边界算子：`water_wall`, `water_reservoir`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界。

## 输出

quantity支持：`depth`, `velocity`, `water_flux`, `water_volume`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。
