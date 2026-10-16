# elastic-plate 数据契约

本题与instruction、通用CONTRACT共同构成完整契约。入口为UTF-8 `problem.json`和扁平HDF5，网格为MSH 4.1 ASCII；文件相对清单解析，名称不携带物理条件。`physics`恰为model与parameters，`physics.model="solid-elastic-plate-v1"`；`task`若出现必须为`elastic-plate`。`spatial_dimension=2`。只接受本题定义的模型和键。

## 分析与材料

各向同性Kirchhoff–Love薄板，参考中面xy，w沿+z；弯曲刚度D=Eh³/[12(1−ν²)]，DΔ²w=q。全边界w=∂nw=0；无膜力、横向剪切变形、剪切锁定的隐藏离散要求或转动惯性。评价连续板弯曲而非输入网格的有限元刚度矩阵；厚度满足薄板适用条件由算例保证。

| 参数名（physics.parameters 下） | 单位 | 值域与含义 |
|---|---|---|
| `young_modulus` | `Pa` | Young模量E；下界>0 |
| `poisson_ratio` | `1` | Poisson比ν，严格小于0.5；下界≥0；上界≤0.49 |
| `thickness` | `m` | 恒定厚度h；下界>0 |

以上参数全部必填；每项恰为`{"value":有限标量,"unit":"表中单位"}`，无隐藏缺省或额外参数。数值均为有限实数，布尔值不能作为数值。

## 几何、位置与数组身份

`meshes`恰含main，`locations.domain`是main全部顶维单元所用节点，`locations.cells`是main全部2维单元；IDs按tag递增。计算域是输入非退化一阶三角形（type 2）拼成的精确参考域，不以可选CAD替代。未用坐标为0；输出采样身份始终使用参考位置。内部分网、升阶或重网格自由，但输出映回固定身份。域连通无悬挂节点。

其他mesh位置允许同一main的顶维cells单元子集（只用于输出）、节点子集或边界1维单元子集。输入须导出每个外边界实体。每条边界记录的实体集合由引用的location IDs明确给出，Physical Group若声明须与这些IDs完全一致。边界面外法向由相邻体决定，不能由节点存储方向猜。横向面载荷使用全部cells。不把内部面当外边界。

aggregate位置仅支持source引用覆盖整个域的cells，IDs恰含一项；operation=sum对应integral，operation=mean对应average。具体观测按本题输出表请求，不接受边界或单元子集聚合。字段对象名、HDF5 key和tag是三种身份：条件`{"field":"logical_name"}`引用fields对象；`fields.logical_name.array`才是HDF5 key。各对象名自由选择（domain、cells保留位置名除外），不得由名称推断quantity或数组key。

## 时间、连续解释和输入场

所有时间轴恰为单帧[0.0]，输出引用steady轴；它是静力存储标记，不是物理启动初态；不接受多帧条件或时间插值。

输入场恰为被条件引用的fields，全部float64。标量kind=scalar、component_shape=[1]、components=["value"]；数组始终[T,N,*component_shape]，不得省略任何轴。标量数据参数允许表中单位的带单位常量，或同location、相同quantity／unit／kind的显式field。只允许条件表列出的参数，无额外选项或默认单位。

每个输入field必须显式sampling。element场space=piecewise_constant，表示每个单元上的常值。所有场extrapolation=forbid，禁止范围外外推。所有输入场time=constant。

## 条件全集

每条记录的role、variable、operator、location及data全部显式。下表是本题唯一允许的operator；不得通过列表顺序覆盖冲突条件。

| operator | role／variable | 位置类别 | data精确键与类型 | 含义与组合 |
|---|---|---|---|---|
| `plate_clamp` | `boundary`／`deflection` | facets | `value`：scalar，`m`，quantity=`deflection`；挠度w=0<br>`slope`：scalar，`rad`，quantity=`normal_slope`；外法向导数∂nw=0 | 覆盖全部外边界；首版只支持齐次夹持，两个值必须均为零 |
| `pressure_load` | `source`／`pressure` | cells | `value`：scalar，`Pa`，quantity=`pressure`；沿正z方向压力q | 一条覆盖cells，单元内常数 |

必须出现：`pressure_load`, `plate_clamp`。cells类的每个算子恰一条且覆盖全部cells。固定约束必须足以排除刚体和机构；无条件的边界按本题零自然载荷处理，不能添加隐含对称或弹簧。

同一边界单元不能重复声明plate_clamp；夹持条件覆盖全部外边界。数据不含相互矛盾约束。

## 请求输出与结果HDF5

outputs中的逻辑名称及array key自由，quantity必须来自下表。每个必需quantity至少出现一次，可在不同允许采样子集重复请求。结果只包含每个输出array及其IDs和时间轴，严格沿用输入行序、dtype及全部轴；不得重复坐标或输入场。所有输出float64且有限。

| quantity（均必需） | 单位 | kind／位置与采样 | 定义 |
|---|---|---|---|
| `deflection` | `m` | scalar；domain或其节点子集的point；不接受单元中心替代 | 沿正横向的挠度w |
| `curvature` | `1/m` | tensor；cells或其单元子集，average | 板曲率张量−Hessian(w)，全局xy完整矩阵 |

输出tensor的component_shape=[2,2]，components按xx,xy,yx,yy完整行优先排列，不只存对称矩阵的独立项。
输出scalar的component_shape=[1]，components=["value"]。
节点输出取连续解在给定节点的值。单元average按参考面积（边界按其自身维数的测度）积分再除测度，不取节点算术均值或单元中心点值。

## 合法范围与保证

除上文明确的自由键和时间轴名外不增加字段或条件组合。数据制作方须确认材料适用、网格非退化、载荷与约束相容、解在规定分支上可确定、所请求点值及平均存在，并在题面预算内用独立基准达到目标精度。这些是数据接收条件，不是结构校验器已经证明的事实；尚无正式数据时不声称已获验证。
