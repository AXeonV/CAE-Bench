# elastic-beam 数据契约

本题与instruction、通用CONTRACT共同构成完整契约。入口为UTF-8 `problem.json`和扁平HDF5，网格为MSH 4.1 ASCII；文件相对清单解析，名称不携带物理条件。`physics`恰为model与parameters，`physics.model="solid-elastic-beam-v1"`；`task`若出现必须为`elastic-beam`。`spatial_dimension=1`。只接受本题定义的模型和键。

## 分析与材料

一根沿全局x轴严格递增的直梁，线性Euler–Bernoulli弯曲；横向w是抽象横向挠度而非x位移。连续方程(EIw″)″=q。跨单元w、w′及无集中力偶处内力连续。端力按虚功定义，右端F=−(EIw″)′、M=EIw″，左端符号相反。不求轴向伸长、扭转或剪切变形；恰有一个端点clamp，另一个端点可end_load。

`physics.parameters={}`，本题无全局标量参数；EI由材料条件给出。

数值均为有限实数，布尔值不能作为数值。

## 几何、位置与数组身份

`meshes`恰含main，`locations.domain`是main全部顶维单元所用节点，`locations.cells`是main全部1维单元；IDs按tag递增。计算域是输入非退化一阶直线段（Gmsh type 1）拼成的精确参考域，不以可选CAD替代。未用坐标为0；输出采样身份始终使用参考位置。内部分网、升阶或重网格自由，但输出映回固定身份。域连通无悬挂节点。

其他mesh位置允许同一main的顶维cells单元子集（只用于输出）、节点子集或边界0维单元子集。输入须导出每个外边界实体。每条边界记录的实体集合由引用的location IDs明确给出，Physical Group若声明须与这些IDs完全一致。梁只有一条无分叉区间，domain包括其全部节点；ends位置恰含一个实际端点节点，按x最小／最大确定左右。梁内部单元端点不允许clamp或end_load。

aggregate位置仅支持source引用覆盖整个域的cells，IDs恰含一项；operation=sum对应integral，operation=mean对应average。具体观测按本题输出表请求，不接受边界或单元子集聚合。字段对象名、HDF5 key和tag是三种身份：条件`{"field":"logical_name"}`引用fields对象；`fields.logical_name.array`才是HDF5 key。各对象名自由选择（domain、cells保留位置名除外），不得由名称推断quantity或数组key。

## 时间、连续解释和输入场

所有时间轴恰为单帧[0.0]，输出引用steady轴；它是静力存储标记，不是物理启动初态；不接受多帧条件或时间插值。

输入场恰为被条件引用的fields，全部float64。标量kind=scalar、component_shape=[1]、components=["value"]；数组始终[T,N,*component_shape]，不得省略任何轴。标量数据参数允许表中单位的带单位常量，或同location、相同quantity／unit／kind的显式field。只允许条件表列出的参数，无额外选项或默认单位。

每个输入field必须显式sampling。节点场space=piecewise_linear，沿一阶输入单元唯一P1重建（边界节点在边界单元上重建）。element场space=piecewise_constant，表示每个单元上的常值。所有场extrapolation=forbid，禁止范围外外推。所有输入场time=constant。

## 条件全集

每条记录的role、variable、operator、location及data全部显式。下表是本题唯一允许的operator；不得通过列表顺序覆盖冲突条件。

| operator | role／variable | 位置类别 | data精确键与类型 | 含义与组合 |
|---|---|---|---|---|
| `clamp` | `boundary`／`deflection` | ends | `value`：scalar，`m`，quantity=`deflection`；端挠度<br>`rotation`：scalar，`rad`，quantity=`slope`；dw/dx | 同时固定w与w′ |
| `end_load` | `boundary`／`end_load` | ends | `force`：scalar，`N`，quantity=`force`；端横向集中力<br>`moment`：scalar，`N.m`，quantity=`moment`；与w′共轭的端弯矩 | 虚功Fδw+Mδw′；未声明端自由，默认F=M=0 |
| `line_load` | `source`／`line_load` | cells | `value`：scalar，`N/m`，quantity=`line_load`；沿正横向的均布线载荷q | 一条覆盖cells，每单元常数 |
| `flexural_rigidity` | `material`／`rigidity` | cells | `value`：scalar，`N.m2`，quantity=`rigidity`；EI>0 | 一条覆盖cells，每单元常数 |

必须出现：`line_load`, `flexural_rigidity`。cells类的每个算子恰一条且覆盖全部cells。节点边界允许多条互不重叠记录。固定约束必须足以排除刚体和机构；无条件的边界按本题零自然载荷处理，不能添加隐含对称或弹簧。

## 请求输出与结果HDF5

outputs中的逻辑名称及array key自由，quantity必须来自下表。每个必需quantity至少出现一次，可在不同允许采样子集重复请求。结果只包含每个输出array及其IDs和时间轴，严格沿用输入行序、dtype及全部轴；不得重复坐标或输入场。所有输出float64且有限。

| quantity（均必需） | 单位 | kind／位置与采样 | 定义 |
|---|---|---|---|
| `deflection` | `m` | scalar；domain或其节点子集的point；不接受单元中心替代 | 沿正横向的挠度w |
| `slope` | `rad` | scalar；domain或其节点子集的point；不接受单元中心替代 | 梁截面转角dw/dx |
| `bending_moment` | `N.m` | scalar；cells或其单元子集，average | 梁弯矩EI·w″，按长度平均 |

输出scalar的component_shape=[1]，components=["value"]。
节点输出取连续解在给定节点的值。单元average按参考长度（边界按其自身维数的测度）积分再除测度，不取节点算术均值或单元中心点值。

## 合法范围与保证

除上文明确的自由键和时间轴名外不增加字段或条件组合。数据制作方须确认材料适用、网格非退化、载荷与约束相容、解在规定分支上可确定、所请求点值及平均存在，并在题面预算内用独立基准达到目标精度。这些是数据接收条件，不是结构校验器已经证明的事实；尚无正式数据时不声称已获验证。
