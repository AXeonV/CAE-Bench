# 输入与输出

遵守[通用协议](../../../../docs/CONTRACT.md)，本题数学和评分要求见[题面](instruction.md)。所有长度为 m、时间为 s，无隐式单位换算。

`task="linear-periodic-transport-1d"`、`spatial_dimension=1`、`physics.model="linear_periodic_transport_1d"`。`physics.parameters` 恰含 `velocity={value:b,unit:"m/s"}`，b 的范围见题面。`geometries={}`；`meshes.main.file` 引用包内 Gmsh MSH 4.1 ASCII 网格。

网格覆盖全区间 [0,1]，含 1024 个等长一阶线单元，Physical Group 为 `(dimension=1,tag=1)`。`locations.domain` 为 `{kind:"mesh",mesh:"main",entity:"element",dimension:1,ids:"cell_ids",physical_group:{dimension:1,tag:1}}`，包含全部上述线单元。IDs 为严格递增的正 int64；其顺序对应场数组的空间行，几何邻接由网格确定。两端周期配对由坐标确定，不另列边界节点 location。节点 tag 和单元 tag 分属不同空间。

`data_file="input.h5"`，其中恰有下列数组：

| key | dtype | shape | 含义 |
|---|---|---|---|
| cell_ids | int64 | [1024] | domain 单元编号 |
| initial_times | float64 | [1] | 恰为 [0.0] |
| times | float64 | [T] | 输出请求时刻，范围见题面 |
| initial_state | float64 | [1,1024,1] | 初态单元常数，也是初态单元平均 |

`time_axes={initial:"initial_times",output:"times"}`。`fields.initial_state` 的描述为 `array="initial_state"`、`quantity="state"`、`location="domain"`、`time_axis="initial"`、`dtype="float64"`、`kind="scalar"`、`component_shape=[1]`、`components=["value"]`、`unit="1"`、`value_kind="average"`。每个原单元内采用所给常数，不进行点值插值或拟合。

`conditions` 恰含以下两条，顺序无关：

| role / variable / operator | location | data |
|---|---|---|
| initial / state / assign | domain | `{value:{field:"initial_state"}}` |
| boundary / state / periodic | domain | `{period_x:{value:1,unit:"m"}}` |

周期条件连接区间两端，周期为 1 m，不是每个单元各自周期。所有参数和条件必须显式给出，不设缺失项默认值。

`outputs` 恰含 `state`：`array="state"`、`quantity="state"`、`location="domain"`、`time_axis="output"`，其他字段属性与 initial_state 相同。输出 `state` 是 float64 `[T,1024,1]`，第 (t,i,0) 项为 times[t] 时刻 cell_ids[i] 所指原单元的长度平均。必须原样复制 cell_ids 和 times；输出 HDF5 恰含这三个 dataset，不导出初态、网格或中间结果。HDF5 属性、额外数组和外部链接不允许。

字段描述表中的实际 `array`、`location` 与 `time_axis` 引用拥有数据关联；禁止把对象名、单元编号或行号互相替代。结构检查仅检查存储与引用，不验证方程和解的正确性。
