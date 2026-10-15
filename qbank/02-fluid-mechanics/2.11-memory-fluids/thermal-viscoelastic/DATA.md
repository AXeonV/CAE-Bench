# 2.11.5 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-thermal-viscoelastic-v1`；spatial_dimension=2，瞬态start_time/end_time明确给定。

从速度、温度及构象初态演化二维不可压缩热Oldroyd-B液体。黏度与松弛时间共享公开温度移位因子，聚合物弹性能与溶剂／松弛耗散分开记账；不含相变或化学反应。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `density`：`kg/m3`。
- `solvent_viscosity`：`Pa.s`。
- `polymer_viscosity`：`Pa.s`。
- `relaxation_time`：`s`。
- `reference_pressure`：`Pa`。
- `heat_capacity`：`J/(kg.K)`。
- `conductivity`：`W/(m.K)`。
- `reference_temperature`：`K`。
- `temperature_coefficient`：`1/K`。
- `start_time`：`s`。
- `end_time`：`s`。

必需域条件（location=`domain`、data只含value）：

- `velocity`：role=initial、operator=assign，`m/s`、vector、finite。
- `conformation`：role=initial、operator=assign，`1`、tensor、spd。
- `temperature`：role=initial、operator=assign，`K`、scalar、positive。

允许边界算子：`velocity_wall`, `velocity_inlet`, `traction_outlet`，以及`temperature_wall`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界；本题另有独立完整temperature_wall温度分区。

## 输出

quantity支持：`velocity`, `pressure`, `temperature`, `polymer_stress`, `conformation`, `traction`, `heat_flux`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。
