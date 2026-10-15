# 2.9.4 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-two-layer-v1`；spatial_dimension=2，瞬态start_time/end_time明确给定。

求稳定分层的两层不可混溶水体，每层有独立厚度与深度平均速度，含床面及相间摩擦。首版限定光滑全湿、双曲稳定解，不含混合、卷吸、冲击、非静水或层消失。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `lower_density`：`kg/m3`。
- `upper_density`：`kg/m3`。
- `gravity`：`m/s2`。
- `bottom_drag`：`1/s`。
- `interface_drag`：`kg/(m2.s)`。
- `start_time`：`s`。
- `end_time`：`s`。

必需域条件（location=`domain`、data只含value）：

- `bed`：role=material、operator=geometry，`m`、scalar、finite。
- `lower_depth`：role=initial、operator=assign，`m`、scalar、positive。
- `lower_velocity`：role=initial、operator=assign，`m/s`、vector、finite。
- `upper_depth`：role=initial、operator=assign，`m`、scalar、positive。
- `upper_velocity`：role=initial、operator=assign，`m/s`、vector、finite。

允许边界算子：`layer_wall`, `layer_inlet`, `layer_outflow`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界。

## 输出

quantity支持：`lower_depth`, `upper_depth`, `lower_velocity`, `upper_velocity`, `water_volume`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。

本题边界仅支持完整超临界入流、完整超临界纯出流及墙；不支持亚临界储槽。入射/出射符号、精确状态与同步时间轴约束见模型协议3.2。
