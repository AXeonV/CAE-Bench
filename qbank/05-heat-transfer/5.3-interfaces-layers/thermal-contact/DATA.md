# thermal-contact 数据契约

入口为problem.json及data_file引用的扁平HDF5，路径相对清单。`spatial_dimension=3`；physics恰含model与parameters，model=`thermal-thermal-contact-v1`；task可省略，出现时必须为`thermal-contact`。不允许contract_version、profile、analysis或materials混用。除自由对象名和数组key外，不接受本题未列的模型、字段或条件。

## 物理定义

以热响应为分析目标，固体不运动、不变形，无未声明的热源或流动。热流q=−k∇T，界面无热阻时温度连续且法向导热热流守恒；输入单元共享节点tag的内部面均为这种完美热连接。空间非均匀材料参数按每个参考单元分片常数，材料跳变不暗加接触热阻。储热为C∂tT+div q=Q。thermal_pair给定温度可跳跃的成对独立表面，记录侧记为minus、partner为plus。逐点q_minus·n_minus=g(T_minus−T_plus)，q_plus·n_plus=−g(T_minus−T_plus)。g在minus三角面上分片常数，按几何配对传给plus；局部节点存储方向不决定正负。其他共享节点内部面仍完美热连接。

## 全局参数

parameters恰含下表全部项，每项恰为value和unit对象；值为有限实数，不含布尔值，整数项必须JSON整数。Tmin<Tmax，温区约束不是评分归一化基准。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 终止时刻tf，严格大于t0 |
| `temperature_min` | `K` | 适用温区下界Tmin>0 |
| `temperature_max` | `K` | 适用温区上界Tmax>Tmin |

## 几何、位置和身份

meshes恰含main，格式MSH4.1 ASCII；可选geometries按CONTRACT引用，但域以输入网格为准。顶维为3，只允许非退化一阶四面体type4及其一阶外边界三角形type2；每个外边界面导出一次，不允许非流形公共面或悬挂节点。保留locations.domain为全部顶维单元所用节点，locations.cells为全部顶维单元；两者恰好覆盖，不能有未用节点。其他位置只允许同网格节点子集、顶维单元子集或外边界单元子集；不允许points、entities、aggregate或其他网格。IDs按实际tag递增，组若声明必须精确匹配IDs；tag不是行号，组名不决定物理条件。二阶以上单元不属于本题支持集合。节点位置用于温度边界／初态；元素位置用于材料、热源和平均观测。给定温度的节点集必须是完整外边界面的顶点之并，作用面精确定义为所有顶点均属于该节点集的全部完整外面；该节点集必须恰好等于这些作用面的顶点并，不得选择同一节点并的另一组面。禁止孤立节点／棱支撑。各温度记录不能共享节点；不同类别边界可在棱上相交但不能覆盖同一完整面。面外法向由唯一相邻顶维单元确定，与面内节点顺序无关。thermal_pair的两侧使用不同节点及面tag，几何三角面逐顶点坐标完全重合且一一配对，相邻体位于公共面相反侧；partner不可与本侧相同或复用任一侧。接触表面不再施加其他边界。配对按完整几何顶点集合，不按行序；不支持非匹配网格或部分面接触。

## 时间与输入场

time_axes必须含initial单帧[t0]、response非空严格递增请求时刻；全部轴至多101帧。response位于[t0,tf]。材料、初态以及标注static的记录字段只用initial单帧；其他加载字段可用任意已声明轴：单帧必须在t0，表示全程常量；多帧须首末恰为t0、tf，逐分量连续分段线性插值，不外推。除initial、response外，不允许未被加载字段使用的轴。输出时刻不等于内部时间步，不能跳过未请求的中间载荷。

所有fields必须被条件引用，条件引用fields逻辑名，field.array才是HDF5 key；名称均自由，不靠名字推断quantity。输入field的quantity必须等于条件表给出的data键，只有value的quantity按以下规则：heat_source.value为heat_source；initial_temperature.value为temperature；temperature.value为temperature；heat_flux.value为heat_flux。全部输入field显式sampling，extrapolation=forbid；space在节点为piecewise_linear（沿一阶网格唯一P1重建），在元素为piecewise_constant（每实体常值）；time为constant（static或单帧）或linear（加载多帧）。先空间重建再时间插值；给定温度节点场在对应完整外表面P1重建。标量默认float64，shape=[1]、components=["value"]；vector为全局x/y/z前D分量。数组始终[T,N,*shape]；全部float64。标量data可用同location、同unit／quantity／kind的field引用，或`{"value":有限实数,"unit":"表中单位"}`表示全位置全程常量；不接受布尔值。矢量、张量只能field引用；禁止内联数组、跨location借相同长度或省略sampling。所有数值范围也适用于常量表示。输入field的value_kind在节点为point、在元素为average，表示上述P1节点值或实体常值；不接受integral。

## 条件全集

### `material`

role=`material`，variable=`thermal`，operator=`material`，location=cells全部单元。必须出现；恰一条覆盖整个位置。参数只随实体变化，不随时间变化。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `conductivity` | scalar [1]，`W/(m.K)`；导热率k>0 |
| `capacity` | scalar [1]，`J/(m3.K)`；体积热容量C>0 |

### `heat_source`

role=`source`，variable=`heat`，operator=`heat_source`，location=cells全部单元。必须出现；恰一条覆盖整个位置。允许上述加载历史。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`W/m3`；单位体积的净加热源Q，正值加热 |

### `initial_temperature`

role=`initial`，variable=`temperature`，operator=`initial_temperature`，location=domain全部节点。必须出现；恰一条覆盖整个位置。参数只随实体变化，不随时间变化。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`K`；初始绝对温度T0 |

### `temperature`

role=`boundary`，variable=`temperature`，operator=`temperature`，location=完整外边界面顶点之并的节点location。可不出现；可多条，但对应边界实体不得重复。允许上述加载历史。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`K`；给定边界绝对温度Tb |

### `heat_flux`

role=`boundary`，variable=`heat_flux`，operator=`heat_flux`，location=外边界单元location。可不出现；可多条，但对应边界实体不得重复。允许上述加载历史。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `value` | scalar [1]，`W/m2`；向外的导热热流，正值从域内流出 |

### `convection`

role=`boundary`，variable=`heat_flux`，operator=`convection`，location=外边界单元location。可不出现；可多条，但对应边界实体不得重复。允许上述加载历史。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `coefficient` | scalar [1]，`W/(m2.K)`；非负换热系数h |
| `ambient` | scalar [1]，`K`；外界温度Ta |

### `thermal_pair`

role=`boundary`，variable=`heat_flux`，operator=`thermal_pair`，location=外边界单元location。必须出现；可多条，但对应边界实体不得重复。允许上述加载历史。data恰含下列全部键：

| data键 | 类型、单位及含义 |
|---|---|
| `partner` | 另一侧几何重合外表面location；仅允许`{"location":"名称"}` |
| `conductance` | scalar [1]，`W/(m2.K)`；严格正界面热导g；按本侧实体分片常数 |

convection的精确关系为q·n=h(T−Ta)，heat_flux给定q·n；正值均向外。未声明的外边界为绝热q·n=0。每个完整外面至多一种边界记录，不以列表顺序覆盖；对流h=0合法并表示绝热。静态材料、体源及初态记录各算子恰一条覆盖表定全域；边界可多条互不重叠记录。Tmin、Tmax约束所有温度输入和物理解；环境温度也在此区间。初始温度与温度边界在t0相容。

## 输出及采样

outputs逻辑名称和array key自由，每个quantity至少一次；可重复请求。输出全部float64，轴为response，不含sampling；位置、单位、kind及分量按表，不允许其他quantity。

| quantity | 类型、单位与含义 | 位置及value_kind |
|---|---|---|
| `temperature` | scalar [1]，`K`；连续物理温度的实体平均值 | cells或其任意非空单元子集，average |
| `conductive_heat_flux` | vector [3]，`W/m2`；导热热流q；不包含对流携热 | cells或其任意非空单元子集，average |
| `interface_heat_flux` | scalar [1]，`W/m2`；本条thermal_pair记录侧向partner流出的面平均导热热流 | 每条thermal_pair记录侧完整面，average；每条均需请求 |

输出平均按实体实际体积（边界面观测按其实际面积）积分再除测度，不是单元中心值或节点算术均值。同一输出位置不规定内部求解网格。结果仅含输出array及其IDs、时间轴，严格沿用输入身份和行序；不复制坐标、输入字段或重新导出网格。

## 接收范围与验证边界

正式数据须确认材料响应在声明温区内有效、网格非退化、初边值相容、所请求平均／点态存在、物理解唯一，并以独立基准核验预算内可达设计精度。温区保证约束全程，不只约束请求帧；不能由Schema或残差自动证明。
至多4000个顶维单元、10000节点。各轴至多101帧，输入与输出场分别至多3000000个数值分量。没有正式数据时，不把工具fixture当物理／数值验证。
