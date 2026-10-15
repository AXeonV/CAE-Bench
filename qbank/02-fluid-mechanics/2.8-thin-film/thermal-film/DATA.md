# 2.8.3 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-thermal-film-v1`；spatial_dimension=2，瞬态start_time/end_time明确给定。

求固定密度牛顿液体薄膜中的压力与厚度平均温度，包含温黏反馈、剪切耗散及向两壁散热。采用本题公开的温度跨隙均匀闭合，不额外求跨隙温度剖面；不含空化。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `density`：`kg/m3`。
- `viscosity`：`Pa.s`。
- `reference_pressure`：`Pa`。
- `heat_capacity`：`J/(kg.K)`。
- `conductivity`：`W/(m.K)`。
- `reference_temperature`：`K`。
- `temperature_coefficient`：`1/K`。
- `heat_transfer`：`W/(m2.K)`。
- `start_time`：`s`。
- `end_time`：`s`。

必需域条件（location=`domain`、data只含value）：

- `gap`：role=material、operator=geometry，`m`、scalar、positive。
- `lower_velocity`：role=material、operator=geometry，`m/s`、vector、finite。
- `upper_velocity`：role=material、operator=geometry，`m/s`、vector、finite。
- `temperature`：role=initial、operator=assign，`K`、scalar、positive。
- `wall_temperature`：role=material、operator=geometry，`K`、scalar、positive。

允许边界算子：`film_pressure`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界；侧边温度随film_pressure.data.temperature给出，不另设temperature_wall分区。

## 输出

quantity支持：`pressure`, `temperature`, `film_flux`, `load`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。
