# 2.3.2 数据声明

本文与[本题任务](instruction.md)、[通用数据协议](../../../../docs/CONTRACT.md)完整定义本题输入输出。

## 文件与模型

每例为 problem.json、其引用的单个输入 HDF5、单个 Gmsh MSH 4.1 ASCII 网格及可选几何。

`task` 为 `rans-steady-3d`；`physics.model` 必须为 `fluid-energy-incompressible-rans-steady-v1`；`spatial_dimension` 必须为 3。模型由显式标识确定，不从 task、对象名或文件名推断。禁止同时出现 `contract_version`、`profile`、`analysis`、`materials`。

几何以分片网格为准。流体单元为一阶四面体/六面体/棱柱/金字塔，边界为一阶三角形/平面四边形。允许上述种类混合。恰有一个网格与一个完整流体域 mesh-element location，维度为 spatial_dimension，IDs 恰含全部流体单元，不得用别名重复声明完整域。

## 参数与材料响应

`physics.parameters` 必须恰含下表参数，每项为 `{"value":数值,"unit":"代码"}`，数值有限，无隐藏缺省或额外参数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| reference_temperature | K | 正值 Tref |
| minimum_temperature, maximum_temperature | K | 0 < Tmin <= Tref <= Tmax，Tmin < Tmax；所有物理状态须在该闭区间 |
| density | kg/m3 | 正常数 rho0 |
| reference_pressure | Pa | 正绝对基准 p0，输出是 p-p0 的表压 |
| reference_viscosity | Pa.s | 正值 muref |
| viscosity_exponent | 1 | 有限实数 a |

牛顿剪切响应 `mu(T)=muref (T/Tref)^a`，其中 muref=reference_viscosity、a=viscosity_exponent。不含剪切依赖、记忆或结构变量。

质量与惯性使用常密度 rho0=density。温度固定为 Tref，不求能量或温度反馈，体加速度力密度为 `rho0 a_body`。压力为 `p-p0` 表压，p0=reference_pressure；包括静水变化，全域体积平均表压固定为 0。

采用 Reynolds 平均；恒密度时 Reynolds/Favre 速度一致。

所有状态温度必须位于 [Tmin,Tmax]。无给定体加速度时相应源项为 0。

## 位置、场与连续重建

条件只能位于完整流体域或同网格外边界 element location；禁止节点、探针或 aggregate 条件。条件引用场的 location 必须与条件完全相同。tag 是身份，不是数组行号；所有位置名、场名、时间轴名、网格名和 HDF5 key 从声明读取。

全部输入场为 float64、value_kind=average，表示对应流体单元或边界实体上的空间平均，显式声明 sampling：space="piecewise_constant"、time="constant"、extrapolation="forbid"。每个实体内重建为常值，不跨实体插值；边界棱角多值按各面一侧迹解释，不将多个面条件叠加到角点。constant 恰有一个样本，时刻为 [0]，表示时间恒定的稳态条件，禁止其他时间采样。输入 fields 只声明被条件引用的场。

所有矢量必须用 HDF5 场，标量可用带单位常数或场；不接受内联数组。scalar 的 component_shape=[1]、components=["value"]；vector 的 component_shape=[3]、components=["x","y","z"]。场数组保留 `[T,N,*component_shape]`，不省略或隐式广播轴。

## 本题条件的完整集合

除下表外不接受其他条件。data 的键必须恰好符合表格，不接受额外参数；所有条件同时生效，顺序无优先级。数值标量写为 `{"value":数值,"unit":"代码"}` 或 `{"field":"场名"}`；矢量必须引用场。表中场 quantity 与 variable 同名。

| role / variable / operator | location | data | 含义 |
|---|---|---|---|
| boundary / velocity / moving_wall | 外边界实体子集 | value: velocity 场，m/s vector | 光滑壁无滑移，速度相对固定域的法向分量必须为 0，只可切向运动 |
| source / acceleration / assign | 完整流体域 | value: acceleration 场，m/s2 vector | 显式体加速度，含给定重力 |

每个外边界实体恰有一条机械条件。禁止热条件和热源。禁止物理初态和 time_start/time_end 参数。每种 source 至多一条全域记录。

## 输出与观测

每例必须恰好请求下表全部物理量，无额外物理量或位置；全部输出为完整流体域单元上的体积平均、float64、value_kind=average，不以单元中心点值代替体积平均。不同输出可使用不同合法时间轴。

| quantity | kind | unit | 含义 |
|---|---|---|---|
| velocity | vector | m/s | 速度平均场 |
| pressure | scalar | Pa | 域平均为 0 的表压 |

全部输出时刻固定为 [0]，仅为稳态存储标记。

结果 HDF5 恰含 outputs 请求数组、对应 IDs 与时间轴，共享支持 key 只存一次，不写额外数组或元数据；shape、dtype、扁平 HDF5 存储、网格与引用规则遵循通用协议。结构合法不证明物理或数值准确性。

可使用公共工具包的 `load_problem` 与 `write_result` 读写协议；`fluid_energy_properties(problem,T,pressure=None)` 读取上述材料响应，`fluid_energy_condition_values(problem,condition,parameter,time)` 按上述重建返回 `[N,*component_shape]`。这些助手不求解流动、不选择湍流闭合，也不补全未声明的材料。
