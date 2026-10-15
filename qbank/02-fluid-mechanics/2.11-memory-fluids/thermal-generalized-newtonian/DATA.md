# 2.11.4 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-thermal-generalized-newtonian-v1`；spatial_dimension=3，瞬态start_time/end_time明确给定。

求三维不可压缩Carreau液体流动与温度，包含温黏反馈和黏性耗散。该题无记忆，区别于本节构象及触变能力，也区别于2.1的等温流变。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `density`：`kg/m3`。
- `reference_pressure`：`Pa`。
- `zero_viscosity`：`Pa.s`。
- `infinite_viscosity`：`Pa.s`。
- `time_constant`：`s`。
- `power_index`：`1`。
- `heat_capacity`：`J/(kg.K)`。
- `conductivity`：`W/(m.K)`。
- `reference_temperature`：`K`。
- `temperature_coefficient`：`1/K`。
- `start_time`：`s`。
- `end_time`：`s`。

必需域条件（location=`domain`、data只含value）：

- `velocity`：role=initial、operator=assign，`m/s`、vector、finite。
- `temperature`：role=initial、operator=assign，`K`、scalar、positive。

允许边界算子：`velocity_wall`, `velocity_inlet`, `traction_outlet`，以及`temperature_wall`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界；本题另有独立完整temperature_wall温度分区。

## 输出

quantity支持：`velocity`, `pressure`, `temperature`, `extra_stress`, `traction`, `heat_flux`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。
