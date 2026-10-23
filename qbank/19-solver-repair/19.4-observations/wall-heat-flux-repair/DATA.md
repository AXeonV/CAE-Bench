# 输入与输出

使用 [CONTRACT](../../../../docs/CONTRACT.md)。`task=wall-heat-flux-repair`，`physics.model=wall-energy-transport-v1`，`spatial_dimension=2`；`geometries`、`conditions` 为空，`meshes={"channel":{"file":"mesh.msh"}}`。网格为 Gmsh MSH 4.1 ASCII，单位 m，全局 xy 平面，z=0；所有场均按显式 tag 排序，不按文件读取顺序解释。

几何是矩形通道，长 L、高 H，x=0 与 x=L 为左右端，y=0 与 y=H 为两壁。内部及首层可非正交；物理外边界仍是该矩形。网格只含一阶四边形区域单元和导出的边界线单元，节点数 100…3000。Physical Group 为 `(2,10)` 区域，`(1,1)` 下壁、`(1,2)` 上壁、`(1,3)` 左端、`(1,4)` 右端。L、H 由实际坐标定义。无需按某个结构化公式生成网格。

全部字段为 float64；ID 为 int64、严格递增。`time_axes={"steady":"times"}`、`times=[0]` 秒，表示稳态求值而非迭代时刻。场数组为 `(1,位置数量,分量数)`；scalar 仍保留最后一维 1。所有输入和结果有限。

## 位置和边界数据

`locations` 恰含以下位置：

| 名称 | 定义 |
|---|---|
| nodes | mesh=channel，entity=node，ids=node_ids，覆盖全部节点 |
| wall | mesh=channel，entity=node，ids=wall_ids，恰覆盖上下壁节点并集 |
| inlet | mesh=channel，entity=node，ids=inlet_ids，physical_group={dimension:1,tag:3} |
| bottom_edges | mesh=channel，entity=element，dimension=1，ids=bottom_edge_ids，physical_group={dimension:1,tag:1} |
| top_edges | 同上，ids=top_edge_ids，physical_group={dimension:1,tag:2} |
| bottom_integral | kind=aggregate，source=bottom_edges，ids=bottom_observation_id=[0]，operation=sum |
| top_integral | kind=aggregate，source=top_edges，ids=top_observation_id=[0]，operation=sum |
| diagnostic | kind=entities，ids=diagnostic_ids=[0]，代表本次求解的诊断记录 |

前五项 kind=mesh。数组名在输入 HDF5 中与表中一致。唯一输入 field 为 `inlet_temperature`，array 同名，quantity=temperature，unit=K，location=inlet，time_axis=steady，dtype=float64，kind=scalar，component_shape=[1]，components=[value]，value_kind=point，sampling={space:piecewise_linear,time:constant,extrapolation:forbid}。其值为 250…450 K，表示左端边界节点给定温度，节点间沿线性边插值；速度为零时该场忽略且左右端改为绝热对称边界。非零流动时入口温度与两壁端点连续。

## 参数和离散设置

`physics.parameters` 恰含以下 value/unit 对象：

| 名称 | 单位 | 定义、范围 |
|---|---|---|
| density | kg/m^3 | 常密度，.5…3 |
| heat_capacity | J/(kg*K) | 常定压比热，500…2000 |
| viscosity | Pa*s | 常动力黏度，.001….1 |
| conductivity | W/(m*K) | 常导热系数，1…20 |
| velocity | m/s | 入口及两壁沿+x速度，0….2 |
| bottom_temperature | K | 下壁恒温，250…450；热流模式时忽略 |
| top_temperature | K | 上壁恒温，250…450 |
| bottom_heat_flux | W/m^2 | 下壁给定向流体输入的热流，-2000…2000；恒温模式时忽略 |
| boundary_mode | 1 | 0=上下恒温；1=下壁给定热流、上壁恒温，仅允许零速度 |
| cfl | 1 | 固定 CFL，.5…20 |
| iterations | 1 | 最大迭代数，整数 100…30000 |

非零速度时两壁只沿切向滑动，网格不移动；左端给定上表速度及输入温度剖面，右端指定零表压，温度使用原生流出处理。所有工况无重力和体热源，初温为上下参数温度均值。压力为相对于出口零值的表压。

真实求解采用 FDS、一阶空间对流、加权最小二乘梯度、隐式 Euler、FGMRES/ILU；线性容差 1e-10、最多 30 步。参考量纲采用 rho_ref=1 kg/m³、u_ref=1 m/s、T_ref=300 K。求解可在最大步数前停止，但必须达到日志 `rms[T]≤-8`，正常退出且全部结果有限。运行器只按该量纲转换温度和其它输出，不修正物理结果。

## 输出

输出均为 steady 时轴；scalar 的 component_shape=[1]、components=[value]，其余为 components。字段名与 array 名一致，均为 float64。

| field | quantity | unit | location | kind / 分量 | value_kind |
|---|---|---|---|---|---|
| temperature | temperature | K | nodes | scalar | point |
| velocity | velocity | m/s | nodes | components / x,y | point |
| pressure | pressure | Pa | nodes | scalar | point |
| wall_heat_flux | heat_flux | W/m^2 | wall | scalar | point |
| bottom_heat_rate | heat_rate | W | bottom_integral | scalar | integral |
| top_heat_rate | heat_rate | W | top_integral | scalar | integral |
| temperature_residual | log10_residual | 1 | diagnostic | scalar | point |

热流以流体外法向为正：热量离开流体为正、进入为负。因此给定下壁输入热流 f 对应报告下壁热流 -f；恒温边界不预先规定其热流。热率取原求解器对该壁的积分，采用二维单位深度 1 m。逐壁点输出为原生 Heat_Flux，不由驱动按温度另算；热率取原生历史 `HF(hot)`、`HF(cold)`。点值和积分分别比较，不能互相替代。

参考匹配容差见题面，既不是连续解析解的截断误差容差，也不允许以小残差掩盖错误温度或壁面热流。可信运行器调用 SDK `write_result` 写 HDF5，考生只提交三份源码。输入目录的 problem.json、input.h5、mesh.msh 与公开工具一起足以独立运行。
