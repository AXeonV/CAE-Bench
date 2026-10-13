# 输入输出字段与连续含义

本文是[题面](instruction.md)的一部分；基础结构遵守[通用数据协议](../../docs/CONTRACT.md)。`task="PDEBench_2D_CompressibleNavierStokes"`，`physics.model="compressible_navier_stokes_2d"`，`spatial_dimension=2`。

## 几何、位置与采样

`main` 为 Gmsh MSH 4.1 ASCII/binary 网格，覆盖 [0,1]×[0,1] m²。域由 Physical Group `(dimension=2, tag=1)` 标记；`domain` 为该组的全部一阶域单元，`entity=element`、`dimension=2`、`ids="cell_ids"`。网格由等长一阶矩形四边形构成；不拆成三角形再沿用原单元平均值。

每个初始状态值定义为所属单元内的常数，单元边界的单点取值不影响平均值。输出为题面规定的守恒平均派生观测量。

编号只表示身份。单元及边界节点 IDs 为严格递增正 int64。各字段的第 i 行对应 IDs 的第 i 项；几何位置由网格确定。条件中的字段引用必须与条件 location 一致。

长度使用 m，时间使用 s，字段采用下表给出的单位；不进行隐式单位换算。

## 参数

`physics.parameters` 中每个参数采用 `{value,unit}`。以下参数必须显式给出，即使其值固定；不采用缺失参数的默认值。参数值与条件中重复声明的物理值必须相等。

| 参数 | 单位 | 定义与支持值 |
|---|---|---|
| `gamma` | `1` | γ=5/3 |
| `shear_viscosity` | `m2/s` | η：本题定义为运动学剪切系数 |
| `bulk_viscosity` | `m2/s` | ζ：本题定义为运动学体系数 |

## 输入场与时间轴

所有数值场为 float64。标量为 `kind=scalar`、`component_shape=[1]`、`components=["value"]`；空间矢量为 `kind=vector`、`component_shape=[2]`，分量顺序为 ["x","y"]。域场的 `location=domain`、`value_kind=average`。quantity 的具体字符串列于下表；下表对象名与默认数组 key 相同，程序必须实际读取 `array` 引用。

| fields 对象 | quantity | kind | 单位 | shape | time_axis | 含义 |
|---|---|---|---|---|---|---|
| `initial_density` | `density` | `scalar` | `kg/m3` | `[1,N,1]` | `initial` | ρ 的初始单元平均值，严格正 |
| `initial_velocity` | `velocity` | `vector` | `m/s` | `[1,N,2]` | `initial` | v 的初始单元平均值 |
| `initial_pressure` | `pressure` | `scalar` | `Pa` | `[1,N,1]` | `initial` | p 的初始单元平均值，严格正 |

`time_axes.initial="initial_times"` 引用 float64 `[0.0]`；`time_axes.output="times"` 引用含 0 且严格递增的请求时刻，范围以题面为准。输出时间轴仅规定采样时刻，不是内部时间步。程序不能重新生成十进制时间轴替换输入。未列出的字段不得加入输入 NPZ；几何/网格记录可引用包内文件，`data_file` 指向输入 NPZ。

## 条件记录

条件记录的 variable 是待约束的数学量，允许与 fields 对象名不同。所有记录同时成立，列表顺序不表示优先级；下表是本题允许的算子全集。

| role / variable / operator | location | data 与数学含义 |
|---|---|---|
| initial / density / assign | domain | `value={field:"initial_density"}`。 |
| initial / velocity / assign | domain | `value={field:"initial_velocity"}`。 |
| initial / pressure / assign | domain | `value={field:"initial_pressure"}`。 |
| boundary / fluid_state / periodic | domain | 活跃方向分别给 `period_x`、`period_y`、`period_z` 带单位长度；相对面的全部原始变量周期连接。 |

周期条件作用于整个矩形域：按所声明各方向的长度将相对面几何位置配对，场及所需导数周期延拓。不得对每个单元单独施加周期。输入不允许重复冲突约束。

## 输出

| outputs 对象与默认 array key | quantity | kind | 单位 | shape | 含义 |
|---|---|---|---|---|---|
| `density` | `density` | `scalar` | `kg/m3` | `[T,N,1]` | ρ 的单元平均值 |
| `velocity` | `mass_weighted_velocity` | `vector` | `m/s` | `[T,N,2]` | 平均动量除以平均密度，质量加权速度 |
| `pressure` | `conservative_pressure` | `scalar` | `Pa` | `[T,N,1]` | 由平均守恒量反算的压力 |

输出场沿用 `location=domain`、`time_axis=output`、float64 及上述标量/矢量规则。结果 NPZ 仅包含 outputs 指定的数值数组、原样复制的 `cell_ids` 和 `times`；多字段共享的轴只保存一次，不导出初始场、坐标、强迫或未要求的量。

t=0 输出为输入初值的对应平均值。

可用 `load_problem`、`read_constant`、`read_field`、`write_result` 读写。结构校验器检查引用和数组关联，不验证数学条件或数值解的正确性。

## 源对齐观测量

本题用密度加权定向黏性通量 Q_ij，系数单位为 m2/s。输出 density 为原单元平均密度；velocity=平均(ρv)/平均(ρ)，pressure=(γ−1)[平均(E)−|平均(ρv)|²/(2平均(ρ))]。初始单元内常数使 t=0 三者恰等于输入。提交程序必须按这些观测量输出，不能直接输出速度或压力的体积平均。
