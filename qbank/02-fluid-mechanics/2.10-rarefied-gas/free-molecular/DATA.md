# 2.10.4 数据说明

本题使用[通用协议](../../../../docs/CONTRACT.md)与[流体配置](../../../../docs/FLUID-REDUCED.md)，不是cfd-2.1 profile。完整model：`fluid-reduced-free-molecular-v1`；spatial_dimension=3，稳态所有轴为[0]，无物理初值。

求三维无分子间碰撞的稳态输运，保留完整气壁散射与储槽注入。允许多次壁面反射；不能假定所有分子只飞行一次。分子直径仍显式提供，用于适用性记录，不参与碰撞项。

## 参数与条件

physics.parameters精确包含以下带单位有限常数；值域及相互约束见模型协议，不存在可省略的隐含默认值：

- `molecule_mass`：`kg`。
- `molecule_diameter`：`m`。
- `reference_temperature`：`K`。

必需域条件（location=`domain`、data只含value）：

无域初态条件。

允许边界算子：`gas_wall`, `gas_reservoir`。每个算子的variable、完整data键、选项和物理意义均由协议第3、4节给定，机械分区覆盖完整外边界。

## 输出

quantity支持：`density`, `velocity`, `temperature`, `pressure`, `traction`, `heat_flux`。主要状态为协议第5节必需集合，其余按outputs请求。压力基准、通量方向、温度、记忆张量、体积分和降维单位均使用同一协议，不作输出后平移、去均值或隐式换算。

本题无实际数据；examples/references/cases只保留空目录。协议结构测试不等于连续模型或材料响应在实际工况中的验证。
