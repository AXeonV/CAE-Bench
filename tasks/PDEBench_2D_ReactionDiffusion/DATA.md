# 输入输出字段与连续含义

本文是[题面](instruction.md)的一部分；基础结构遵守[通用数据协议](../../docs/CONTRACT.md)。`task="PDEBench_2D_ReactionDiffusion"`，`physics.model="reaction_diffusion_2d"`，`spatial_dimension=2`。

## 几何、位置与采样

`main` 为 Gmsh MSH 4.1 ASCII 网格，覆盖 [-1,1]×[-1,1] m²。域由 Physical Group `(dimension=2, tag=1)` 标记；`initial_domain` 为该组的全部一阶域单元，`entity=element`、`dimension=2`、`ids="initial_cell_ids"`。网格由等长一阶矩形四边形构成；不拆成三角形再沿用原单元平均值。

每个初始状态值定义为所属单元内的常数，单元边界的单点取值不影响平均值。输出为每个原始单元上对应量的面积平均值。

编号只表示身份。单元及边界节点 IDs 为严格递增正 int64。各字段的第 i 行对应 IDs 的第 i 项；几何位置由网格确定。`left/right` 为 x 最小/最大边界，`bottom/top` 为 y 最小/最大边界。各边界 location 引用相应维度 1 的 Physical Group，以节点 IDs 表示边界取值位置。组 tag 由清单提供。条件中的字段引用必须与条件 location 一致。

长度使用 m，时间使用 s，字段采用下表给出的单位；不进行隐式单位换算。

## 参数

`physics.parameters` 中每个参数采用 `{value,unit}`。以下参数必须显式给出，即使其值固定；不采用缺失参数的默认值。参数值与条件中重复声明的物理值必须相等。

| 参数 | 单位 | 定义与支持值 |
|---|---|---|
| `activator_diffusivity` | `m2/s` | D_u=10⁻³ |
| `inhibitor_diffusivity` | `m2/s` | D_v=5×10⁻³ |
| `reaction_offset` | `1` | k=5×10⁻³ |
| `activator_rate` | `1/s` | a=1 |
| `inhibitor_rate` | `1/s` | b=1 |

## 输入场与时间轴

所有数值场为 float64。标量为 `kind=scalar`、`component_shape=[1]`、`components=["value"]`。初始域场的 `location=initial_domain`、`value_kind=average`。quantity 的具体字符串列于下表；下表对象名与默认数组 key 相同，程序必须实际读取 `array` 引用。

| fields 对象 | quantity | kind | 单位 | shape | time_axis | 含义 |
|---|---|---|---|---|---|---|
| `initial_activator` | `activator` | `scalar` | `1` | `[1,N_initial,1]` | `initial` | u 的初始单元平均值 |
| `initial_inhibitor` | `inhibitor` | `scalar` | `1` | `[1,N_initial,1]` | `initial` | v 的初始单元平均值 |

`time_axes.initial="initial_times"` 引用 float64 `[0.0]`；`time_axes.output="times"` 引用含 0 且严格递增的请求时刻，范围以题面为准。输出时间轴仅规定采样时刻，不是内部时间步。程序不能重新生成十进制时间轴替换输入。未列出的字段不得加入输入 NPZ；几何/网格记录可引用包内文件，`data_file` 指向输入 NPZ。

边界从 t>0 生效，t=0 取给定初值；边界数据及其数学含义见条件表。相邻边角点条件一致。

## 条件记录

条件记录的 variable 是待约束的数学量，允许与 fields 对象名不同。所有记录同时成立，列表顺序不表示优先级；下表是本题允许的算子全集。

| role / variable / operator | location | data 与数学含义 |
|---|---|---|
| initial / activator / assign | initial_domain | `value={field:"initial_activator"}`。 |
| initial / inhibitor / assign | initial_domain | `value={field:"initial_inhibitor"}`。 |
| boundary / activator / normal_flux | 每条边 | `value={value:0,unit:"m/s"}`，−D_u∇u·n=0。 |
| boundary / inhibitor / normal_flux | 每条边 | `value={value:0,unit:"m/s"}`，−D_v∇v·n=0。 |

边界条件作用于条件表指定的位置。输入不允许重复冲突约束。

## 输出

| outputs 对象与默认 array key | quantity | kind | 单位 | shape | 含义 |
|---|---|---|---|---|---|
| `activator` | `activator` | `scalar` | `1` | `[T,N,1]` | u 的单元平均值 |
| `inhibitor` | `inhibitor` | `scalar` | `1` | `[T,N,1]` | v 的单元平均值 |

输出场沿用 `location=domain`、`time_axis=output`、float64 及上述标量/矢量规则。结果 NPZ 仅包含 outputs 指定的数值数组、原样复制的 `cell_ids` 和 `times`；多字段共享的轴只保存一次，不导出初始场、坐标、强迫或未要求的量。

t=0 输出从完整初值中按 domain 的细单元 IDs 选取相应平均值，不能把初始数组按输出行号直接截断。

可用 `load_problem`、`read_constant`、`read_field`、`write_result` 读写。结构校验器检查引用和数组关联，不验证数学条件或数值解的正确性。

## 完整初值与输出子集

N_initial=512²；initial_cell_ids 是完整细网格单元编号。输出 domain 同样是 main 的二维 element location，但只提供 cell_ids，省略 physical_group，选择原细网格中的 128² 个单元。N=len(cell_ids)；输出数组为 [T,N,1]。domain 的编号必须能在 initial_cell_ids 中逐项找到。两套 IDs 分别严格递增，空间关系由同一 Gmsh 网格确定。程序获得完整初值。
