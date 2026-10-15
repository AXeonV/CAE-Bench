# 2.11.1 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-viscoelastic-steady-v1`；spatial_dimension=2，稳态所有轴为[0]，无物理初值。

求等温不可压缩Oldroyd-B流体的定常速度、静压和构象张量。聚合物记忆状态与入口构象由材料历史决定；无物理初值，不允许把构象默认重置为单位阵。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `density`：`kg/m3`。
- `solvent_viscosity`：`Pa.s`。
- `polymer_viscosity`：`Pa.s`。
- `relaxation_time`：`s`。
- `reference_pressure`：`Pa`。

必需域条件（location=`domain`、data只含value）：

无域初态条件。

允许边界算子：`velocity_wall`, `velocity_inlet`, `traction_outlet`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界。

## 输出

quantity支持：`velocity`, `pressure`, `polymer_stress`, `conformation`, `traction`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。
