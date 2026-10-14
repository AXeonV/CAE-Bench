# 输入输出字段与连续含义

本文是[题面](instruction.md)的一部分；基础结构遵守[通用数据协议](../../docs/CONTRACT.md)。`task="PDEBench_2D_IncompressibleNavierStokes"`，`physics.model="inhomogeneous_incompressible_navier_stokes_2d"`，`spatial_dimension=2`。

## 几何、位置与采样

`main` 为覆盖 [0,1]×[0,1] m² 的一阶矩形 Gmsh MSH 4.1 网格，用于定义区域与四边；状态采样位置 `domain` 独立声明为 `kind=points`、`ids="point_ids"`、`coordinates="point_coordinates"`。点坐标为 float64 `[N,2]`，是 512² 个等距单元中心；不得将它们伪装成 Gmsh 节点或单元平均值。

初始场和静态强迫在相邻采样点间按 x/y 坐标作分片双线性插值。在最外中心点到物理边界之间沿外法向常值延拓，角部同时采用两个方向的常值延拓。该连续采样解释不取代 t>0 的零壁速条件。原始初速度还须执行题面指定的 Helmholtz 投影；t>0 输出为投影演化后的连续速度点值，t=0 则按输出节原样保留预投影记录。

编号只表示身份。独立点 IDs 为严格递增非负 int64；边界节点 IDs 为严格递增正 int64。各字段的第 i 行对应 IDs 的第 i 项；几何位置由显式点坐标或边界网格确定。`left/right` 为 x 最小/最大边界，`bottom/top` 为 y 最小/最大边界。各边界 location 引用相应维度 1 的 Physical Group，以节点 IDs 表示边界取值位置。组 tag 由清单提供。条件中的字段引用必须与条件 location 一致。

长度使用 m，时间使用 s，字段采用下表给出的单位；不进行隐式单位换算。

## 参数

`physics.parameters` 中每个参数采用 `{value,unit}`。以下参数必须显式给出，即使其值固定；不采用缺失参数的默认值。参数值与条件中重复声明的物理值必须相等。

| 参数 | 单位 | 定义与支持值 |
|---|---|---|
| `kinematic_viscosity` | `m2/s` | ν=0.01 |

## 输入场与时间轴

所有数值场为 float64。标量为 `kind=scalar`、`component_shape=[1]`、`components=["value"]`；空间矢量为 `kind=vector`、`component_shape=[2]`，分量顺序为 ["x","y"]。域场的 `location=domain`、`value_kind=point`。quantity 的具体字符串列于下表；下表对象名与默认数组 key 相同，程序必须实际读取 `array` 引用。

| fields 对象 | quantity | kind | 单位 | shape | time_axis | 含义 |
|---|---|---|---|---|---|---|
| `initial_velocity` | `velocity` | `vector` | `m/s` | `[1,N,2]` | `initial` | 原始速度采样 w₀；连续初速度采用题面定义的 Helmholtz 投影 |
| `initial_tracer` | `tracer` | `scalar` | `1` | `[1,N,1]` | `initial` | 随流输运标量 χ₀，允许正负值，不是流体质量密度 |
| `forcing` | `forcing` | `vector` | `m/s2` | `[1,N,2]` | `initial` | 不随时间变化的空间强迫 f |

`time_axes.initial="initial_times"` 引用 float64 `[0.0]`；`time_axes.output="times"` 引用含 0 且严格递增的请求时刻，范围以题面为准。`forcing` 使用 initial 时间轴，其值在整个求解区间恒定。 输出时间轴仅规定采样时刻，不是内部时间步。程序不能重新生成十进制时间轴替换输入。未列出的字段不得加入输入 HDF5；几何/网格记录可引用包内文件，`data_file` 指向输入 HDF5。

四个壁速字段均为必需输入场，关联关系如下：

| fields 对象及默认 array key | location |
|---|---|
| `wall_velocity_left` | `left` |
| `wall_velocity_right` | `right` |
| `wall_velocity_bottom` | `bottom` |
| `wall_velocity_top` | `top` |

它们均采用 quantity=`velocity`、float64 `[1,N_boundary,2]`、`kind=vector`、`component_shape=[2]`、`components=["x","y"]`、单位 `m/s`、`value_kind=point`，所有值为零。字段对象名与默认数组 key 相同；角点重复记录均为同一零值。四场均引用 `time_axis=conditions`；`time_axes.conditions="condition_times"` 映射到输入 HDF5 的 `condition_times=float64([0.0])`，表示整个 t>0 区间恒定，不表示只作用一次。

## 条件记录

条件记录的 variable 是待约束的数学量，允许与 fields 对象名不同。所有记录同时成立，列表顺序不表示优先级；下表是本题允许的算子全集。

| role / variable / operator | location | data 与数学含义 |
|---|---|---|
| initial / velocity / project_preserve_snapshot | domain | `value={field:"initial_velocity"}`，执行题面定义的连续 Helmholtz 投影。 |
| initial / tracer / assign | domain | `value={field:"initial_tracer"}`。 |
| source / velocity / tracer_force | domain | `value={field:"forcing"}`，方程加速度为 χf，χ 初值由 initial/tracer 指定。 |
| boundary / velocity / dirichlet | left/right/bottom/top 各一条 | `value` 分别引用 `wall_velocity_left`、`wall_velocity_right`、`wall_velocity_bottom`、`wall_velocity_top`；壁面矢量全零，t>0 生效。 |
| boundary / kinematic_pressure / mean | domain | `value={value:0,unit:"m2/s2"}`，面积平均运动学压力为零。 |

边界条件作用于条件表指定的位置。输入不允许重复冲突约束。

## 输出

| outputs 对象与默认 array key | quantity | kind | 单位 | shape | 含义 |
|---|---|---|---|---|---|
| `velocity` | `velocity` | `vector` | `m/s` | `[T,N,2]` | 连续速度 v 的点值 |

输出场沿用 `location=domain`、`time_axis=output`、float64 及上述标量/矢量规则。结果 HDF5 仅包含 outputs 指定的数值数组、原样复制的 `point_ids` 和 `times`；多字段共享的轴只保存一次，不导出初始场、坐标、强迫或未要求的量。

t=0 是预投影初始记录，velocity 必须原样输出 initial_velocity；t>0 输出投影演化后的连续速度点值。t=0 记录不要求满足散度约束；右初值 v(0+)=P(w₀) 仍按题面的 Helmholtz 投影定义。不输出 χ 或压力。

可用 `load_problem`、`read_constant`、`read_field`、`write_result` 读写。结构校验器检查引用和数组关联，不验证数学条件或数值解的正确性。
