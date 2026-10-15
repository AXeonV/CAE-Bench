# elastic-truss 数据契约

本题与instruction、通用CONTRACT共同构成完整契约。入口为UTF-8 `problem.json`和扁平HDF5，网格为MSH 4.1 ASCII；文件相对清单解析，名称不携带物理条件。`physics`恰为model与parameters，`physics.model="solid-elastic-truss-v1"`；`task`若出现必须为`elastic-truss`。`spatial_dimension=2`。只接受本题定义的模型和键。

## 分析与材料

输入为xy平面铰接直杆网络，节点共享tag表示铰接；交叉但不共享节点的杆不连接。忽略弯曲、剪切、自重和惯性。每杆轴向应变等于其两端位移差在初始杆轴的投影除以杆长；N=EAε，受拉为正；节点向量平衡。E全局，A每杆给定。支撑为全分量位移；不含机构、孤立节点或预应力。

| 参数名（physics.parameters 下） | 单位 | 值域与含义 |
|---|---|---|
| `young_modulus` | `Pa` | Young模量E；下界>0 |

以上参数全部必填；每项恰为`{"value":有限标量,"unit":"表中单位"}`，无隐藏缺省或额外参数。数值均为有限实数，布尔值不能作为数值。

## 几何、位置与数组身份

`meshes`恰含main，`locations.domain`是main全部顶维单元所用节点，`locations.cells`是main全部1维单元；IDs按tag递增。计算域是输入非退化一阶直线段（Gmsh type 1）拼成的精确参考域，不以可选CAD替代。未用坐标为0；输出采样身份始终使用参考位置。内部分网、升阶或重网格自由，但输出映回固定身份。

其他mesh位置允许同一main的顶维cells单元子集（只用于输出）、节点子集或边界0维单元子集。输入须导出每个外边界实体。每条边界记录的实体集合由引用的location IDs明确给出，Physical Group若声明须与这些IDs完全一致。杆系的位移和集中力可作用任意杆节点（包括连接节点）；cells是全部杆，domain是全部杆端节点。N为每根直杆平均内力。

aggregate位置仅支持source引用覆盖整个域的cells，IDs恰含一项；operation=sum对应integral，operation=mean对应average。具体观测按本题输出表请求，不接受边界或单元子集聚合。字段对象名、HDF5 key和tag是三种身份：条件`{"field":"logical_name"}`引用fields对象；`fields.logical_name.array`才是HDF5 key。各对象名自由选择（domain、cells保留位置名除外），不得由名称推断quantity或数组key。

## 时间、连续解释和输入场

所有时间轴恰为单帧[0.0]，输出引用steady轴；它是静力存储标记，不是物理启动初态；不接受多帧条件或时间插值。

输入场恰为被条件引用的fields，全部float64。标量kind=scalar、component_shape=[1]、components=["value"]；vector使用全局前2坐标，component_shape=[2]、components=["x","y"]；数组始终[T,N,*component_shape]，不得省略任何轴。标量数据参数允许表中单位的带单位常量，或同location、相同quantity／unit／kind的显式field。向量数据参数必须使用同location、相同quantity／unit／kind的显式field，即使均匀也不能使用常量简写。只允许条件表列出的参数，无额外选项或默认单位。

每个输入field必须显式sampling。节点场space=piecewise_linear，沿一阶输入单元唯一P1重建（边界节点在边界单元上重建）。element场space=piecewise_constant，表示每个单元上的常值。所有场extrapolation=forbid，禁止范围外外推。所有输入场time=constant。

## 条件全集

每条记录的role、variable、operator、location及data全部显式。下表是本题唯一允许的operator；不得通过列表顺序覆盖冲突条件。

| operator | role／variable | 位置类别 | data精确键与类型 | 含义与组合 |
|---|---|---|---|---|
| `displacement` | `boundary`／`displacement` | nodes | `value`：vector，`m`，quantity=`displacement`；位移向量；所有分量均被约束 | 给定全部位移分量，边界P1迹；同一节点只允许一条位移记录 |
| `nodal_force` | `source`／`force` | nodes | `value`：vector，`N`，quantity=`force`；作用于节点的外力 | 同一节点的已声明力相加；未声明为0 |
| `cross_section` | `material`／`area` | cells | `value`：scalar，`m2`，quantity=`area`；每杆横截面积A>0 | 必须一条覆盖全部杆，杆内常数 |

必须出现：`cross_section`。cells类的每个算子恰一条且覆盖全部cells。节点边界允许多条互不重叠记录。不同来源的nodal_force可累加。固定约束必须足以排除刚体和机构；无条件的边界按本题零自然载荷处理，不能添加隐含对称或弹簧。

## 请求输出与结果HDF5

outputs中的逻辑名称及array key自由，quantity必须来自下表。每个必需quantity至少出现一次，可在不同允许采样子集重复请求。结果只包含每个输出array及其IDs和时间轴，严格沿用输入行序、dtype及全部轴；不得重复坐标或输入场。所有输出float64且有限。

| quantity（均必需） | 单位 | kind／位置与采样 | 定义 |
|---|---|---|---|
| `displacement` | `m` | vector；domain或其节点子集的point；不接受单元中心替代 | 位移u，参考全局坐标分量 |
| `axial_force` | `N` | scalar；cells或其单元子集，average | 轴向内力，受拉为正 |

输出vector的component_shape=[2]，components=["x","y"]。
输出scalar的component_shape=[1]，components=["value"]。
节点输出取连续解在给定节点的值。单元average按参考长度（边界按其自身维数的测度）积分再除测度，不取节点算术均值或单元中心点值。

## 合法范围与保证

除上文明确的自由键和时间轴名外不增加字段或条件组合。数据制作方须确认材料适用、网格非退化、载荷与约束相容、解在规定分支上可确定、所请求点值及平均存在，并在题面预算内用独立基准达到目标精度。这些是数据接收条件，不是结构校验器已经证明的事实；尚无正式数据时不声称已获验证。
