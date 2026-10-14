# 输入输出字段与连续含义

本文是[题面](instruction.md)的一部分；基础结构遵守[通用数据协议](../../docs/CONTRACT.md)。`task="PDEBench_1D_Burgers"`，`physics.model="burgers_1d"`，`spatial_dimension=1`。

## 几何、位置与采样

`main` 为 Gmsh MSH 4.1 ASCII 网格，覆盖 [0,1] m。域由 Physical Group `(dimension=1, tag=1)` 标记；`domain` 为该组的全部一阶域单元，`entity=element`、`dimension=1`、`ids="cell_ids"`。网格由等长一阶线单元构成。

每个初始状态值定义为所属单元内的常数，单元边界的单点取值不影响平均值。输出为每个原始单元上对应量的长度平均值。

编号只表示身份。单元及边界节点 IDs 为严格递增正 int64。各字段的第 i 行对应 IDs 的第 i 项；几何位置由网格确定。条件中的字段引用必须与条件 location 一致。

长度使用 m，时间使用 s，字段采用下表给出的单位；不进行隐式单位换算。

## 参数

`physics.parameters` 中每个参数采用 `{value,unit}`。以下参数必须显式给出，即使其值固定；不采用缺失参数的默认值。参数值与条件中重复声明的物理值必须相等。

| 参数 | 单位 | 定义与支持值 |
|---|---|---|
| `diffusion_coefficient` | `m2/s` | κ∈{a/π : a∈{0.001,0.002,0.004,0.01,0.02,0.04,0.1,0.2,0.4,1,2,4}} |

## 输入场与时间轴

所有数值场为 float64。标量为 `kind=scalar`、`component_shape=[1]`、`components=["value"]`。域场的 `location=domain`、`value_kind=average`。quantity 的具体字符串列于下表；下表对象名与默认数组 key 相同，程序必须实际读取 `array` 引用。

| fields 对象 | quantity | kind | 单位 | shape | time_axis | 含义 |
|---|---|---|---|---|---|---|
| `initial_state` | `state` | `scalar` | `m/s` | `[1,N,1]` | `initial` | u 的初始单元平均值 |

`time_axes.initial="initial_times"` 引用 float64 `[0.0]`；`time_axes.output="times"` 引用含 0 且严格递增的请求时刻，范围以题面为准。输出时间轴仅规定采样时刻，不是内部时间步。程序不能重新生成十进制时间轴替换输入。未列出的字段不得加入输入 NPZ；几何/网格记录可引用包内文件，`data_file` 指向输入 NPZ。

## 条件记录

条件记录的 variable 是待约束的数学量，允许与 fields 对象名不同。所有记录同时成立，列表顺序不表示优先级；下表是本题允许的算子全集。

| role / variable / operator | location | data 与数学含义 |
|---|---|---|
| initial / state / assign | domain | `value={field:"initial_state"}`，t=0 赋值。 |
| boundary / state / periodic | domain | `period_x={value:1,unit:"m"}`；整个区间周期连接，不是每个单元独立周期。 |

周期条件作用于整个区间：按所声明各方向的长度将相对面几何位置配对，场及所需导数周期延拓。不得对每个单元单独施加周期。输入不允许重复冲突约束。

## 输出

| outputs 对象与默认 array key | quantity | kind | 单位 | shape | 含义 |
|---|---|---|---|---|---|
| `state` | `state` | `scalar` | `m/s` | `[T,N,1]` | u 的单元平均值 |

输出场沿用 `location=domain`、`time_axis=output`、float64 及上述标量/矢量规则。结果 NPZ 仅包含 outputs 指定的数值数组、原样复制的 `cell_ids` 和 `times`；多字段共享的轴只保存一次，不导出初始场、坐标、强迫或未要求的量。

t=0 输出为输入初值的对应平均值。

可用 `load_problem`、`read_constant`、`read_field`、`write_result` 读写。结构校验器检查引用和数组关联，不验证数学条件或数值解的正确性。
