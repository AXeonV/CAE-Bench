# 2.8.2 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-gas-film-v1`；spatial_dimension=2，瞬态start_time/end_time明确给定。

求等温理想气体在给定薄隙与壁面运动下的瞬态压力、密度和厚度积分体积通量。无滑移、无稀薄修正；本题的压缩储存与2.10的分子非平衡能力不同。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `viscosity`：`Pa.s`。
- `specific_gas_constant`：`J/(kg.K)`。
- `reference_temperature`：`K`。
- `reference_pressure`：`Pa`。
- `start_time`：`s`。
- `end_time`：`s`。

必需域条件（location=`domain`、data只含value）：

- `gap`：role=material、operator=geometry，`m`、scalar、positive。
- `lower_velocity`：role=material、operator=geometry，`m/s`、vector、finite。
- `upper_velocity`：role=material、operator=geometry，`m/s`、vector、finite。
- `pressure`：role=initial、operator=assign，`Pa`、scalar、positive。

允许边界算子：`film_pressure`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界。

## 输出

quantity支持：`pressure`, `density`, `film_flux`, `load`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。
