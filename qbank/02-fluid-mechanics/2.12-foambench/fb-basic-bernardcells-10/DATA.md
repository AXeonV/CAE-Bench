# 数据定义：底部加热封闭腔的贝纳德对流

## 范围与状态

本题是2.12.69的自包含接口定义。`task` 必须精确为 `fb-basic-bernardcells-10`。采用 [CONTRACT](../../../../docs/CONTRACT.md) 的 `physics` 路径，不使用CFD profile。`physics.model` 必须精确为 `foambench-bernardcells`，`spatial_dimension=2`。此模型是文档契约草案，尚未装配领域声明检查、网格、HDF5或数值参考；以下文件与数组均为未来数据包要求，不表示当前目录已有可运行输入。

## 几何、方程与材料

域为0<x<9m、0<y<1m；floor为y=0，ceiling为y=1，side_walls为x=0及x=9，wall为这四边的并集。二维场在z不变，无前后壁面。温度角点按floor/ceiling定温，side_walls仅对其开边施加绝热。

采用标准不可压缩Boussinesq层流模型：∇·u=0，∂tu+u·∇u=−∇π/ρ0+ν∇²u−β(T−T0)g，∂tT+u·∇T=α∇²T。ρ0=1 kg/m3，T0=300K，β=0.001/K，g=(0,−9.81)m/s2，ν=μ/ρ0=0.001m2/s，α=0.001m2/s，对应Pr=1。热容量取712J/(kg.K)，导热系数κ=ρ0 cp α=0.712W/(m.K)。除浮力外密度恒为ρ0；不求解声学、变密度质量输运、黏性发热、辐射或湍流。π=p−ρ0 g·x是扣除恒定参考密度静水压后的动力压力，单位Pa，每一时刻以域面积均值π=0固定规范；输出pressure即π，不输出绝对静压或源软件p_rgh。无额外体源，温差是唯一热驱动。

`physics.parameters` 只允许下面列出的带单位有限标量；值固定为本移植变体，隐藏数据不得无声明更换物理参数。公式中的固定热化学/闭合系数按本页定义，不在JSON中存放多项式字符串、列表或可执行表达式。边界值在条件中明确存储，重复标量必须与表中一致。

| 参数 | 值 | 单位 |
| --- | --- | --- |
| end_time | 1000 | s |
| output_interval | 50 | s |
| bottom_temperature | 315.0 | K |
| top_temperature | 290.0 | K |
| reference_density | 1 | kg/m3 |
| reference_temperature | 300 | K |
| expansion_coefficient | 0.001 | 1/K |
| dynamic_viscosity | 0.001 | Pa.s |
| thermal_diffusivity | 0.001 | m2/s |
| heat_capacity | 712 | J/(kg.K) |
| gravity_y | -9.81 | m/s2 |

## 初始、边界及源项

法向n始终指向域外，所有速度与向量按全局(x,y)顺序。边界在0至1000s保持不变。除本页模型已定义的反应/浮力/闭合源外无其他源项。初始状态是瞬态起始条件，不是可任意改变的数值初猜。

所有四壁无滑移u=0。floor温度T=315K，ceiling温度T=290K，side_walls为∂nT=0。压力法向梯度由动量方程与不可穿透条件一致确定，不额外指定绝对压力；域面积均值为0。

初始温度T=300K。初始速度由流函数ψ=1e-4 sin²(πx/9) sin²(πy) m2/s定义，u=(∂yψ,−∂xψ)；因此全域无散且四壁速度严格为0。该明确的小扰动替代不满足封闭域无穿透约束的均匀横流。不可压缩压力由约束求得，不将π=0初猜作为额外独立初始条件。

## 文件、位置与采样

未来输入包包含 `problem.json`、Gmsh MSH 4.1 ASCII `mesh.msh`、`input.h5`，可选 `domain.geo`。路径相对problem.json，清单 `meshes.main.file=mesh.msh`；坐标为m，Gmsh第三坐标为0，网格拓扑二维。几何可由 `geometries.domain` 引用并由网格记录链接；实际离散以msh为准。`locations.domain` 是全部二维域单元，`kind=mesh, mesh=main, entity=element, dimension=2, ids=domain_ids`。每个条件边界名称在locations中定义为相应一维边单元集合，记录 `kind=mesh, mesh=main, entity=element, dimension=1, ids=<名称>_ids`，并以 `physical_group={dimension:1,tag:整数}` 显式绑定；domain绑定维度2组。组号在实际清单给出，不能靠组名称推断条件；并集wall或outlet可用单独Physical Group表示，同一边可属于多个组但不得产生矛盾条件。

输出 `locations.samples={"kind":"points","ids":"sample_ids","coordinates":"sample_coordinates"}`；sample_ids为非负严格递增int64[N]，sample_coordinates为float64[N,2]，全为流体内部固定点，不含边界、角点和固体。输出为点值，不是单元平均；激波恰过采样点时取该时刻求解场的熵解外侧极限，若两侧极限不同则取两侧算术平均。没有自动生成中心点或隐含网格顺序。所有mesh位置的ID为正严格递增int64；边界单元ID不是domain单元ID。

`time_axes.initial=initial_times`，initial_times为float64[1]=[0]；`time_axes.output=output_times`，output_times为float64[21]，第j项为j×50s。输出时间与内部积分步长无关。没有统计平均或伪时间。时间轴由输入提供并在结果中逐值复制，不重算或重排。

初始场在domain单元上以 `value_kind=average` 存储，各单元的值严格为上文解析初态的单元平均；入口/边界数值场在相应边单元上同样为average。除下文单列的非均匀 initial_velocity 外，其余均匀输入场的空间采样 `sampling={"space":"uniform","time":"constant","extrapolation":"hold"}`，表示给定位置全部单元上的同一常值并在整个物理区间保持，不从相邻边或域外外推。均匀矢量和组分也必须以完整数组存储，禁止内联JSON数值列表或省略实体轴；均匀标量条件可用带单位常数。每个变量的初始字段命名 `initial_<变量>`，time_axis为initial；边界字段命名 `<边界>_<变量>`，time_axis也为initial，作为全时段常量使用。此命名表的变量由下列条件表逐项枚举；为constant表达的标量无需另造field。所有字段dtype=float64，标量component_shape=[1]/components=["value"]，速度[2]/["x","y"]，质量分数[5]/["CH4","O2","N2","CO2","H2O"]，单位与对应输出一致。

## 条件清单

每个表格中逗号列出的变量或位置均展开为独立条件记录，不在JSON键内塞逗号列表。每条记录恰含 `role,variable,operator,location,data`。数值常数写成 `{"value":数值,"unit":"单位"}`，字段引用 `{"field":"字段对象名"}`；data键列未标为可选的均必需，不接收其他算子或参数。value/backflow_value是数据参数名，不是未声明表达式。条件不依排列先后生效；初态和边界在t=0的相交点遵守前述优先规则。

| role | variable | location | operator | data键与物理含义 |
| --- | --- | --- | --- | --- |
| initial | velocity, temperature | domain | assign | 各变量一条，value引用对应initial字段 |
| boundary | velocity | wall | dirichlet | value引用全0二维速度字段 |
| boundary | temperature | floor, ceiling | dirichlet | 各边一条，value为本题定温，单位K |
| boundary | temperature | side_walls | normal_derivative | value=0 K/m |
| boundary | pressure | wall | momentum_compatible | normal_speed=0 m/s；压力梯度由上文动量一致性定义 |
| source | pressure | domain | mean_gauge | value=0 Pa，表示每时刻域面积均值约束，不是质量或动量体源 |


域内全部常系数和显式公式源已由physics和本页方程定义，不额外添加material/source记录。mean_gauge（若出现）是以source角色承载的非局部规范约束，不是物理体源。momentum_compatible/open_velocity/slip等含无数据分支的算子仍须带表列的数值参数，避免用未知字段或空data暗示物理。

例如某均匀二维边界速度条件采用 `data={"value":{"field":"wall_velocity"}}`，该field必须位于同一location；边界温度常数采用 `data={"value":{"value":300,"unit":"K"}}`。示例仅说明类型，实际变量、位置与数值以本题上述定义为准。标量0导数表示相应变量的零法向导数；矢量0导数必须引用显式二维零field，不将一个标量隐式广播为两个分量。

## 输出

`outputs` 必须逐项为下面结构，所有字段共用samples/output，T=21、N=len(sample_ids)，无空间/时间重建或隐式轴。单位和quantity字符串由此固定，压力含义以模型段落为准。

```json
{
  "velocity": {
    "array": "velocity",
    "quantity": "velocity",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "vector",
    "component_shape": [
      2
    ],
    "components": [
      "x",
      "y"
    ],
    "unit": "m/s",
    "value_kind": "point"
  },
  "pressure": {
    "array": "pressure",
    "quantity": "pressure",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "Pa",
    "value_kind": "point"
  },
  "temperature": {
    "array": "temperature",
    "quantity": "temperature",
    "location": "samples",
    "time_axis": "output",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "K",
    "value_kind": "point"
  }
}
```

结果 `result.h5` 必须恰包含各输出array、sample_ids与output_times；float64场shape为[T,N,*component_shape]，IDs和时间的dtype/shape/值/顺序与输入完全一致。不写坐标、网格、初态、边界场、额外诊断或元数据。input.h5恰包含locations引用的IDs和坐标、time_axes数组、fields数组，不夹带未引用数据。上述全部条件、字段、ID与几何边界须在数据制作时交叉核验；通用结构检查不验证方程、模型闭合、网格分辨率或数值准确度。

初始速度的特殊采样规则：initial_velocity字段采用space=piecewise_constant、time=constant、extrapolation=hold，数组仅存储上述解析流函数速度的单元平均。连续物理初态由本页解析式唯一确定，不把单元平均重建成另一个分片常数初态；其余均匀输入场仍按uniform规则。
