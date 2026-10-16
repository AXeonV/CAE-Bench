# 输入输出数据

本题使用 [通用数据协议](../../../../docs/CONTRACT.md)，只要求回传已给定的数组，不涉及物理求解、插值、单位换算或时间推进。

## 输入清单

入口为 `problem.json`；所有文件路径相对其所在目录解析，与程序工作目录无关。

| 清单字段 | 本题约定 |
|---|---|
| `task` | 必填，固定为 `"smoke-test"` |
| `spatial_dimension` | 1、2 或 3 |
| `data_file` | 输入 HDF5 文件的相对路径 |
| `geometries`、`meshes` | 按通用协议描述可选几何与网格；网格采用 Gmsh MSH 4.1 ASCII |
| `locations` | 网格节点、节点子集、指定维度的网格单元或独立采样点；IDs 与点坐标按通用协议存储 |
| `time_axes` | 名称到输入 HDF5 时间数组 key 的映射，允许单帧或多帧、非等间隔及负时间 |
| `fields` | 全部输入场描述，结构及必需键见通用协议第 6 节 |
| `outputs` | 与 `fields` 完全相同，包含相同对象名及描述；每个输出数组直接对应同 key 的输入数组 |
| `conditions` | 必填，可为 `[]`；非空记录的范围及含义见下文 |
| `physics` | 可选；出现时 `model` 为 `"identity"`，`parameters` 可包含带单位的 `conductivity` 常量，单位 `W/(m.K)` |

本题不使用 `contract_version`、`profile`、`analysis`、`materials` 或场的 `sampling`。位置与场的对象名、HDF5 key、`quantity`、单位和分量标签以清单为准，不固定为某个示例中的名称。`quantity` 是非空描述标签，不决定回传方法；`kind` 对应的分量标签仍须遵守通用协议。无需根据几何、标签或物理名称重新计算数值。

## 数组与对应关系

每个场通过 `array` 读取输入 HDF5 dataset，通过 `location` 查找 IDs，通过 `time_axis` 查找时间数组。元数据对象名与 HDF5 key 可以不同。实体 tag 或独立点 ID 是身份，不是数组下标；网格文件的实体排列不决定场数组的行顺序。

场 dtype 为 `float64`、`int64` 或 `bool`；形状固定为 `[T,N,*component_shape]`。标量保留最后的长度 1 轴，空间矢量为 `[T,N,D]`，完整二阶张量为 `[T,N,D,D]`，一般分量场使用声明的分量形状。分量顺序按 `components` 与通用协议，不转置、展平、重排或广播。浮点值有限。

节点和独立点场为 `value_kind: "point"`；单元场为 `"average"` 或 `"integral"`。这些标记描述输入数组，不要求从网格计算平均或积分。多帧数据直接按给定时间顺序回传，不在帧间插值。

## 附带的条件与参数

条件及 `physics` 只用于携带协议元数据，不构成待求解的热传导或其他物理问题，也不覆盖 `fields` 中的值。即使条件常量与输入场值不同，仍回传输入场。

每条条件均有 `role`、`variable`、`location`、`operator`、`data`。`location` 引用已声明的位置；`data` 仅有必需键 `value`，其值为带单位有限标量 `{"value": 100.0, "unit": "K"}` 或输入场引用 `{"field": "left_temperature"}`。引用对象名而不是数组 key，引用场的位置必须与条件一致。以下是本题允许的记录：

| role / operator | variable | data.value 的单位／表示 |
|---|---|---|
| `boundary / dirichlet` | `temperature` | `K` 的常量或标量温度场引用 |
| `initial / assign` | `temperature` | `K` 的常量或标量温度场引用 |
| `source / assign` | `heat_source` | `W/m3` 的常量或标量源项场引用 |
| `material / assign` | `conductivity` | `W/(m.K)` 的常量或标量导热系数场引用 |

条件无需补充或输出，也不用于合成缺失的场。`physics.parameters.conductivity` 同样是元数据常量，不参与回传运算。

## 输出文件

结果为独立的 HDF5 文件，只包含以下 key 的并集，共用 key 只写一份：

1. 每个 `outputs` 场的 `array`，保留对应输入数组的 dtype、shape 及索引对应关系，值按题面容差判分。
2. 每个输出 location 引用的 IDs 数组，与输入的 dtype、shape、数值及顺序完全一致。
3. 每个输出 time_axis 引用的时间数组，与输入完全一致。

不输出网格、点坐标、JSON 元数据或未被输出引用的支持数组；不得遗漏或增加 key。输入 HDF5 可能含点坐标等辅助数组，因此不能简单把整个输入文件复制为结果。通用协议允许的无损压缩与内部存储布局可自由选择，不要求文件字节一致。
