# 输入输出字段与连续含义

本文是[题面](instruction.md)的一部分；基础结构遵守[通用数据协议](../../../../docs/CONTRACT.md)。`task="darcy-flow-2d"`，`physics.model="darcy_flow_2d"`，`spatial_dimension=2`。

## 几何、位置与采样

`main` 为 Gmsh MSH 4.1 ASCII 网格，覆盖 [0,1]×[0,1] m²。域由 Physical Group `(dimension=2, tag=1)` 标记；`domain` 为该组的全部一阶域单元，`entity=element`、`dimension=2`、`ids="cell_ids"`。网格由等长一阶矩形四边形构成；不拆成三角形再沿用原单元平均值。

空间系数 a 使用下述 coefficient_samples 的分片双线性重建；最外中心点到边界沿法向常值延拓。输出为每个原始单元上对应量的面积平均值。

编号只表示身份。单元及边界节点 IDs 为严格递增正 int64。各字段的第 i 行对应 IDs 的第 i 项；几何位置由网格确定。`left/right` 为 x 最小/最大边界，`bottom/top` 为 y 最小/最大边界。各边界 location 引用相应维度 1 的 Physical Group，节点 IDs 标识边界几何；cell_coupled_dirichlet 作用于这些边界上的原单元外侧面内部，不要求给边界节点另设状态数组。组 tag 由清单提供。条件中的字段引用必须与条件 location 一致。

长度使用 m，时间使用 s，字段采用下表给出的单位；不进行隐式单位换算。

## 参数

`physics.parameters` 中每个参数采用 `{value,unit}`。以下参数必须显式给出，即使其值固定；不采用缺失参数的默认值。参数值与条件中重复声明的物理值必须相等。

| 参数 | 单位 | 定义与支持值 |
|---|---|---|
| `source_strength` | `1/s` | f∈{0.01,0.1,1,10,100} |

## 输入场与时间轴

所有数值场为 float64。标量为 `kind=scalar`、`component_shape=[1]`、`components=["value"]`。系数字段的 `location=coefficient_samples`、`value_kind=point`；输出的 location=domain、value_kind=average。quantity 的具体字符串列于下表；下表对象名与默认数组 key 相同，程序必须实际读取 `array` 引用。

| fields 对象 | quantity | kind | 单位 | shape | time_axis | 含义 |
|---|---|---|---|---|---|---|
| `diffusivity` | `diffusivity` | `scalar` | `m2/s` | `[1,N,1]` | `output` | 正系数 a 的中心点采样，仅取 0.1 或 1 |

稳态采用 `time_axes.output="times"`，`times=float64([0.0])`，没有初始场时间轴。 输出原样复制该稳态时间轴。未列出的字段不得加入输入 HDF5；几何/网格记录可引用包内文件，`data_file` 指向输入 HDF5。

边界常量在条件 `data` 中显式给出，稳态边界始终生效；各边条件对原单元外侧面的内部点成立，面与面相交的单点不额外约束。

## 条件记录

条件记录的 variable 是待约束的数学量，允许与 fields 对象名不同。所有记录同时成立，列表顺序不表示优先级；下表是本题允许的算子全集。

| role / variable / operator | location | data 与数学含义 |
|---|---|---|
| material / state / assign | coefficient_samples | `value={field:"diffusivity"}`，指定 a。 |
| source / state / assign | domain | `value={value:f,unit:"1/s"}`，方程右侧为 +f。 |
| boundary / state / cell_coupled_dirichlet | 每条边 | external_value={value:0,unit:"1"}、cell_weight={value:0.5,unit:"1"}；边界面值为相邻原单元平均的 1/2。 |

边界条件作用于条件表指定的位置。输入不允许重复冲突约束。

## 输出

| outputs 对象与默认 array key | quantity | kind | 单位 | shape | 含义 |
|---|---|---|---|---|---|
| `state` | `state` | `scalar` | `1` | `[T,N,1]` | 稳态标量 u 的单元平均值 |

输出场沿用 `location=domain`、`time_axis=output`、float64 及上述标量/矢量规则。结果 HDF5 仅包含 outputs 指定的数值数组、原样复制的 `cell_ids` 和 `times`；多字段共享的轴只保存一次，不导出初始场、坐标、强迫或未要求的量。

T=1 表示稳态解，不表示在 t=0 求瞬态初值。

可用 `load_problem`、`read_constant`、`read_field`、`write_result` 读写。结构校验器检查引用和数组关联，不验证数学条件或数值解的正确性。

## 系数与非局部边界的源对齐

diffusivity 使用 location=coefficient_samples、value_kind=point；该 location 为 points，引用 coefficient_ids(int64[N]) 与 coefficient_coordinates(float64[N,2])，坐标为原单元中心；coefficient_ids 严格递增且非负，不能根据其数值推断与 cell_ids 的空间对应，实际关联由坐标和网格确定。系数按相邻中心点双线性插值，外侧到边界作法向常值延拓，角部两个方向均常值延拓。四边使用 cell_coupled_dirichlet：u_boundary=0.5×相邻原单元的解平均；原单元外侧面之间的交点不另约束。输出仍为 domain 原单元平均值。
