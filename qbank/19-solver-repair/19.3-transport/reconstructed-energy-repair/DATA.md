# 输入与输出

沿用 [CONTRACT](../../../../docs/CONTRACT.md)。`task` 为 `reconstructed-energy-repair`，`physics.model` 为 `reconstructed-total-energy-v1`；`geometries`、`meshes`、`conditions` 均为空。完整 CFD 的固定几何由公开的 `public/flatplate.su2` 唯一定义，节点编号沿用该文件；直接重构只使用彼此独立的边状态，不构造全局网格。

全部数据均为 float64，ID 为 int64。`time_axes={"instant":"times"}`，`times=[0]` 秒。此时轴只标记一次算例求值，不代表稳态求解的迭代编号。场值为点值，数组统一为 `(1,实体数,分量数)`；scalar 仍保留最后一维 1。输入场采样为 `space=uniform,time=constant,extrapolation=forbid`。输出不声明 sampling。所有数值有限。

`physics.parameters` 恰含下列 value/unit 对象。

| 名称 | 单位 | 定义与范围 |
|---|---|---|
| operation | 1 | 0：直接重构；1：完整 CFD |
| gamma | 1 | 比热比，1.1…1.67；完整 CFD 固定公开配置，忽略本值 |
| gas_constant | J/(kg*K) | 气体常数，200…500；仅直接重构使用 |
| kappa | 1 | MUSCL 混合参数，-1…1；仅直接重构使用 |
| relax | 1 | 重构松弛系数，0…1；仅直接重构使用 |
| muscl | 1 | 0 或 1；仅直接重构使用 |
| limiter | 1 | 0=NONE，1=VAN_ALBADA_EDGE，2=VENKATAKRISHNAN 点限幅；仅直接重构使用 |
| cfl | 1 | 完整 CFD 的 CFL，100…400；直接重构忽略本值 |
| iterations | 1 | 完整 CFD 主要迭代数，整数 2000…3000；之后另运行 100 步稳定性观察；直接重构忽略本值 |

## 直接重构

`spatial_dimension=d` 为 2 或 3。N 条独立边，1≤N≤32。`locations` 恰为 `edges:{kind:entities,ids:edge_ids}`、`ends:{kind:entities,ids:end_ids}`。`edge_ids=0…N-1`，`end_ids=0…2N-1`。边 i 的左、右节点状态分别放在 ends 的 `2i`、`2i+1`，不共享节点状态。

字段名、array 名一致。标量 `kind=scalar,component_shape=[1],components=[value]`；其余 `kind=components,component_shape=[分量数]`。

| 输入 field | quantity | 单位 | location | 分量及定义 |
|---|---|---|---|---|
| temperature | temperature | K | ends | 100…2000 |
| velocity | velocity | m/s | ends | x,y[,z]，每分量 -2000…2000 |
| pressure | pressure | Pa | ends | 1000…1e7 |
| density | density | kg/m^3 | ends | 1e-4…100 |
| enthalpy | specific_total_enthalpy | J/kg | ends | 已存储总焓，1e4…1e7 |
| gradient_temperature | temperature_gradient | K/m | ends | x,y[,z] |
| gradient_velocity | velocity_gradient | 1/s | ends | xx,xy[,xz],yx,yy[,yz][,zx,zy,zz]，先速度分量后坐标分量 |
| gradient_pressure | pressure_gradient | Pa/m | ends | x,y[,z] |
| limiters | primitive_limiter | 1 | ends | T,x,y[,z],p，均 0…1 |
| displacement | displacement | m | edges | 左节点到右节点的位移 x,y[,z]，每分量 -.2….2 |

梯度每分量绝对值不超过 1e8。输入密度须与理想气体状态一致：逐个边端点令 `rho_EOS=p/(R*T)`，要求 `abs(rho-rho_EOS) <= 1e-12 kg/m^3 + 1e-12*abs(rho_EOS)`。此为输入有效性容差，不用于纠正输入或替代输出评分容差。输入总焓代表非线性迭代阶段的已有状态，允许偏离 `Cp*T+|u|²/2`，不得将该偏差视为无效输入或自动抹除。这里只重构 T、速度、p；密度、总焓和保守量应保持相应状态一致性。具体物理约定为 `Cp=gamma*R/(gamma-1)`，两侧各自的总焓变化是 `Cp*(T_new-T_old)+(|u_new|²-|u_old|²)/2`，保留已有状态的偏差；密度使用重构后的 p、T 和理想气体 EOS。无重构或发生非物理状态回退时返回原状态。回退判断沿用库接口约定，不能删除保护。重构保留有限的正压、正密度或完整回退，不输出 NaN。

输出字段为 `temperature,velocity,pressure,density,enthalpy`，其描述符与对应输入一致但无 sampling；另有 `momentum`（quantity=`momentum_density`，unit=`kg/(m^2*s)`，d 个 x,y[,z] 分量）和 `energy`（quantity=`total_energy_density`，unit=`J/m^3`，标量）。均在 ends，后两者为该库真实的可压缩保守状态转换输出。

## 完整 CFD

`spatial_dimension=2`，不提供输入 fields。`locations` 恰为 nodes、wall 两组 points，以及 diagnostic 一组 entities，ids 分别引用 `node_ids=0…13899`、`wall_ids=0…99`、`diagnostic_ids=[0]`。points 的 coordinates 分别引用 float64 `[13900,2]` 的 `node_coordinates` 和 `[100,2]` 的 `wall_coordinates`，单位 m。nodes 沿用固定公开网格编号和坐标，wall 按公开网格中 wall 标记的横坐标递增排列。这里使用 RANS、SST、定常可压缩流、M0.2/Re5e6、绝热标准壁函数；其余全部参数与公开配置一致，不添加另一个物理补丁。

运行总计 `iterations+100` 步，最后 100 步是继续同一求解的稳定观察。必须正常退出、全部输出有限，最终日志 `rms[Rho]≤-10`、`rms[RhoE]≤-7`；最后 101 条相邻迭代记录的阻力系数 CD 极差不得超过最终绝对值的 1e-3。不得提前退出并把中间步当作最终结果。比较最后一步的完整场和壁面字段，而非十步历史。残差为求解器报告的 log10 值，不是物理时间。壁函数阶段节点的 T、rho、p 不一定同时被重置为平衡态，本题不以该处平衡公式另造修正场。可选 `--artifacts DIR` 仅保留原生输出和日志以便检查，不改变计算或 HDF5 内容。

| 输出 field=array | quantity | 单位 | location | 分量 |
|---|---|---|---|---|
| flow_density | flow_density | kg/m^3 | nodes | value |
| flow_momentum | flow_momentum_density | kg/(m^2*s) | nodes | x,y |
| flow_energy | flow_total_energy_density | J/m^3 | nodes | value |
| wall_cf | skin_friction_coefficient | 1 | wall | value，原生输出的流向摩擦系数 |
| residuals | log10_residual | 1 | diagnostic | density,momentum_x,momentum_y,energy,tke,omega |

上述各输出均为 float64 点值、instant 时轴；分量数为 1 时 scalar，其余 components。该 SST 配置的保守总能量包含湍动能分量，沿用原生 rhoE 定义；不能以采样温度和平均速度另造替代能量场。完整场由原生 ASCII VTK 抽取，保留其有效数字；驱动只转换格式，不补焓、不重算壁面摩擦或替代流场。

可信运行器负责调用 SDK `write_result` 写结果；考生只提交源码。样例的 input/problem.json、input.h5 与 output.h5 遵守同一协议。两个问题族以各自声明的字段逐点比较，不允许以整体均值代替。
