# 2.4.3 数据声明

本文与[本题任务](instruction.md)、[通用数据协议](../../../../docs/CONTRACT.md)完整定义本题输入输出。

## 文件与模型

每例为 problem.json、其引用的单个输入 HDF5、单个 Gmsh MSH 4.1 ASCII 网格及可选几何。

`task` 为 `thermal-statistics-3d`；`physics.model` 必须为 `fluid-energy-lowmach-resolved-statistics-v1`；`spatial_dimension` 必须为 3。模型由显式标识确定，不从 task、对象名或文件名推断。禁止同时出现 `contract_version`、`profile`、`analysis`、`materials`。

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
| reference_conductivity | W/(m.K) | 正值 kref |
| conductivity_exponent | 1 | 有限实数 b |
| heat_capacity | J/(kg.K) | 正常数 cp |
| thermal_expansion | 1/K | beta>=0，beta max(abs(Tmin-Tref),abs(Tmax-Tref))<=0.1 |
| time_start, time_end | s | 有限实数且 start<end |
| statistics_start, statistics_end | s | start<=a<b<=end |
| statistics_step | s | 正值 delta，(b-a)/delta 是 1..100000 的整数 |

牛顿剪切响应 `mu(T)=muref (T/Tref)^a`，其中 muref=reference_viscosity、a=viscosity_exponent。傅里叶导热 `k(T)=kref (T/Tref)^b`，其中 kref=reference_conductivity、b=conductivity_exponent；a=b=0 为常物性。不含剪切依赖、记忆或结构变量。

质量与惯性使用常密度 rho0=density。Boussinesq 热膨胀的体加速度力密度为 `rho0[1-beta(T-Tref)]a_body`，beta=thermal_expansion；可表达强制、自然或混合对流，保留黏性耗散。压力为 `p-p0` 表压，p0=reference_pressure；包括静水变化，全域体积平均表压固定为 0。

所有状态温度必须位于 [Tmin,Tmax]。无给定体加速度或热源时相应源项为 0。

## 位置、场与连续重建

条件只能位于完整流体域或同网格外边界 element location；禁止节点、探针或 aggregate 条件。条件引用场的 location 必须与条件完全相同。tag 是身份，不是数组行号；所有位置名、场名、时间轴名、网格名和 HDF5 key 从声明读取。

全部输入场为 float64、value_kind=average，表示对应流体单元或边界实体上的空间平均，显式声明 sampling：space="piecewise_constant"、time="constant" 或 "linear"、extrapolation="forbid"。每个实体内重建为常值，不跨实体插值；边界棱角多值按各面一侧迹解释，不将多个面条件叠加到角点。constant 恰有一个样本，在整个物理区间保持不变；linear 至少两帧，相邻时刻分段线性并覆盖整个积分区间，禁止外推。初态场时刻恰为 [time_start]。输入 fields 只声明被条件引用的场。

所有矢量必须用 HDF5 场，标量可用带单位常数或场；不接受内联数组。scalar 的 component_shape=[1]、components=["value"]；vector 的 component_shape=[3]、components=["x","y","z"]；tensor 为完整 3×3 笛卡尔矩阵，分量标签按通用协议排列。场数组保留 `[T,N,*component_shape]`，不省略或隐式广播轴。

## 本题条件的完整集合

除下表外不接受其他条件。data 的键必须恰好符合表格，不接受额外参数；所有条件同时生效，顺序无优先级。数值标量写为 `{"value":数值,"unit":"代码"}` 或 `{"field":"场名"}`；矢量必须引用场。表中场 quantity 与 variable 同名，heat_flux 例外已注明。

| role / variable / operator | location | data | 含义 |
|---|---|---|---|
| boundary / velocity / moving_wall | 外边界实体子集 | value: velocity 场，m/s vector | 光滑壁无滑移，速度相对固定域的法向分量必须为 0，只可切向运动 |
| boundary / temperature / temperature | 外边界实体子集 | value: K scalar | 给定壁温 |
| boundary / temperature / outward_heat_flux | 外边界实体子集 | value: W/m2 scalar，场 quantity=heat_flux | 向外导热通量 -k grad(T)·n；正值为流体失热，0 为绝热 |
| initial / velocity / assign | 完整流体域 | value: m/s vector 场 | 完整瞬时初速度 |
| initial / temperature / assign | 完整流体域 | value: K scalar | 初温 |
| source / acceleration / assign | 完整流体域 | value: acceleration 场，m/s2 vector | 显式体加速度，含给定重力；按上述 Boussinesq 响应修正 |
| source / heat_source / assign | 完整流体域 | value: W/m3 scalar | 正值为流体受热 |

每个外边界实体恰有一条机械条件。每个外边界实体还恰有一条热条件，机械与热分区可不同。每个适用初态变量（velocity, temperature）恰有一条全域赋值；初态常值重建可有间断，不要求初态角点与壁面迹人为覆盖，演化按给定边界的一侧极限。每种 source 至多一条全域记录。

## 输出与观测

每例必须恰好请求下表全部物理量，无额外物理量或位置；全部输出为完整流体域单元上的体积平均、float64、value_kind=average，不以单元中心点值代替体积平均。不同输出可使用不同合法时间轴。

| quantity | kind | unit | 含义 |
|---|---|---|---|
| velocity | vector | m/s | 速度离散样本均值 |
| pressure | scalar | Pa | 域平均为 0 的表压的离散样本均值 |
| temperature | scalar | K | 温度离散样本均值 |
| velocity_covariance | tensor | m2/s2 | 完整对称速度协方差矩阵 |
| temperature_variance | scalar | K2 | 温度方差 |
| turbulent_heat_flux | vector | K.m/s | 速度温度协方差，不含 rho cp，不是 W/m2 热流 |

输出时刻固定为 [statistics_end]，是统计终点标记，不能输出末帧瞬时场。令 a=statistics_start、b=statistics_end、delta=statistics_step，统计样本时刻恰为 `a+j delta`，j=0..M、`M=(b-a)/delta`（两端均含），样本数 `S=M+1`。先求每个单元的空间平均瞬时 u_j、p_j、T_j，再对 S 个样本等权求均值。`velocity_covariance=Σ(u_j-ubar)⊗(u_j-ubar)/S`。`temperature_variance=Σ(T_j-Tbar)^2/S`；`turbulent_heat_flux=Σ(u_j-ubar)(T_j-Tbar)/S`。不能先局部平方再空间平均以增加单元内方差。平均静压仍满足域平均规范；密度不变化，不做 Favre 加权，不使用 S-1 无偏估计或连续时间积分平均。

结果 HDF5 恰含 outputs 请求数组、对应 IDs 与时间轴，共享支持 key 只存一次，不写额外数组或元数据；shape、dtype、扁平 HDF5 存储、网格与引用规则遵循通用协议。结构合法不证明物理或数值准确性。

可使用公共工具包的 `load_problem` 与 `write_result` 读写协议；`fluid_energy_properties(problem,T,pressure=None)` 读取上述材料响应；`fluid_energy_condition_values(problem,condition,parameter,time)` 按上述重建返回 `[N,*component_shape]`。`fluid_energy_statistics(times,velocity,temperature=None)` 按上述离散网格求均值与中央矩，times 为实际等距统计网格，velocity shape=[S,N,3]，可选 temperature shape=[S,N,1]。这些助手不求解流动、不选择湍流闭合，也不补全未声明的材料。
