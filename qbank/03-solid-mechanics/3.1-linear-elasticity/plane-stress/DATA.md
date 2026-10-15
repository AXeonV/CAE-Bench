# plane-stress 数据契约

本题与instruction、通用CONTRACT共同构成完整契约。入口为UTF-8 `problem.json`，MSH 4.1 ASCII和扁平HDF5；文件相对清单解析，名称不携带物理条件。`physics`恰为model与parameters，`physics.model="solid-plane-stress-v1"`；`task`若出现必须为`plane-stress`。`spatial_dimension=2`。不使用CFD的profile、analysis、materials或contract_version，不能混写多个模型。

## 分析与材料

平面应力σzz=σxz=σyz=0；ε= sym∇u，σ=2με+λps tr(ε)I，μ=E/[2(1+ν)]，λps=Eν/(1−ν²)。厚度只乘体积与边界积分，载荷仍为Pa和N/m3。 静力平衡divσ+b=0。体无初始应力、无本征应变、材料均匀；位移约束排除刚体模态。

| 参数名（physics.parameters 下） | 单位 | 值域与含义 |
|---|---|---|
| `young_modulus` | `Pa` | Young模量E；下界>0 |
| `poisson_ratio` | `1` | Poisson比ν，严格小于0.5；下界≥0；上界≤0.49 |
| `thickness` | `m` | 实际恒定厚度h；下界>0 |

以上参数全部必填；每项恰为`{"value":有限标量,"unit":"表中单位"}`，无隐藏缺省或额外参数。数值均为有限实数，布尔值不能作为数值。小应变弹性各题的ε均是完整张量，剪切εxy不是工程剪切γxy；μ=E/[2(1+ν)]、λ=Eν/[(1+ν)(1−2ν)]，只有平面应力使用其专用λps。

## 几何、位置与数组身份

`meshes`恰含main，`locations.domain`是main全部顶维单元所用节点，`locations.cells`是main全部2维单元；IDs按tag递增。计算域是输入非退化一阶三角形（type 2）拼成的精确参考域，不以可选CAD替代。未用坐标为0；几何在加载中使用参考位置，即使变形也不重排采样身份。内部分网、升阶或重网格自由，但输出映回固定身份。除明确双体界面／裂面和杆系外，域连通无悬挂节点。体单元共享tag的公共面是完美粘结界面。

其他mesh位置允许同一main的顶维cells单元子集（只用于输出）、节点子集或边界1维单元子集。输入须导出每个外边界实体；边界面方向由相邻体决定，不能由节点存储方向猜。位移条件引用边界节点，牵引和接触引用外边界单元。连续体每条位移／fixed／实虚位移条件实际作用在全部顶点均属于该记录IDs的完整外边界单元之并；该节点集必须恰为这些完整面／边的顶点并，禁止孤立点或棱支撑。杆系与梁端点按其专用节点条件处理。内部材料／体力使用cells；不将单元平均误当中心点值。每条边界记录的实体集合由它引用的location IDs明确给出，Physical Group若声明须与这些IDs完全一致。除cohesive_pair的配对内部界面外，不把内面当外边界。

locations中整体观测可用aggregate，source引用cells或明确的边界实体集合，sum对应integral、mean对应average；IDs恰含一项。点／节点值用point，单元值用average，聚合不是虚构点坐标。字段对象名、HDF5 key和tag是三种身份：条件`{"field":"logical_name"}`引用fields对象；`fields.logical_name.array`才是HDF5 key。各对象名自由选择（domain、cells、sites保留位置名除外），不得由名称推断quantity或数组key。

## 时间、连续解释和输入场

所有时间轴恰为单帧[0.0]，输出引用steady轴；它是静力、特征值或复幅标记，不是物理启动初态；不接受多帧边界或时间插值。

输入场恰为被条件引用的fields，全部float64。标量kind=scalar、component_shape=[1]、components=["value"]；vector使用全局前D坐标；tensor使用[D,D]及xx,xy,…的全矩阵。数组始终[T,N,*component_shape]，不得省略任何轴。每个数据参数允许表中单位的带单位常量（仅标量），或同location、相同quantity／unit／kind的显式field；向量即使均匀也用field。只允许表中列出的参数，无额外选项或默认单位。

每个输入field必须显式sampling。节点场space=piecewise_linear，沿一阶输入单元用唯一P1重建（边界节点在边界线段／三角面上重建）；element场space=piecewise_constant，表内average表示其上的常值。sites场space=uniform表示每个独立点的时间记录、不进行跨点重建。所有场extrapolation=forbid，禁止范围外外推。初态／静态场time=constant；普通加载场time=linear，时间节点间逐分量线性；单帧加载场time=constant且声明为全程常量。先空间重建再时间插值，两者均线性；输出应力／状态的平均必须由求解场积分，不能用平均位移代替。

## 条件全集

每条记录的role、variable、operator、location及data全部显式。下表列出本题唯一允许的operator；不在表中的条件非法。不得通过列表顺序覆盖冲突条件。

| operator | role／variable | 位置类别 | data精确键与类型 | 含义与组合 |
|---|---|---|---|---|
| `displacement` | `boundary`／`displacement` | nodes | `value`：vector，`m`，quantity=`displacement`；位移向量；所有分量均被约束 | 给定全部位移分量，边界P1迹；同一节点只允许一条位移记录 |
| `traction` | `boundary`／`traction` | facets | `value`：vector，`Pa`，quantity=`traction`；外界对固体牵引t=σn | 在参考边界实体上分片常数；未声明的外边界为零牵引 |
| `body_force` | `source`／`body_force` | cells | `value`：vector，`N/m3`，quantity=`body_force`；每参考体积的外力 | 按输入单元分片常数；必须一条覆盖cells，零载也须给出 |

必须出现：`body_force`。cells类的每个算子恰一条且覆盖全部cells；一般节点边界允许多条互不重叠记录。固定约束必须足以排除刚体和机构；无条件的边界按本题零自然载荷处理，不能添加隐含对称或弹簧。

体域中同一实体同种边界只能一条；受位移约束节点所在边界面的其余未约束自由度按自然条件处理。给定牵引与位移可在共享棱边交会，但不能在整面重合。除这种相容交会外，数据不含相互矛盾约束；位移边界重叠节点不得重复声明。

## 请求输出与结果HDF5

outputs中的逻辑名称及array key自由，quantity必须来自下表。每个必需quantity至少出现一次，可在不同允许采样子集重复请求。结果只包含每个输出array及其IDs和时间轴，严格沿用输入行序、dtype及全部轴；不得重复坐标或输入场。所有输出float64且有限，不返回复数dtype。

| quantity（均必需） | 单位 | kind／位置与采样 | 定义 |
|---|---|---|---|
| `displacement` | `m` | vector；domain或其节点子集的point；不接受单元中心替代 | 位移u，参考全局坐标分量 |
| `stress` | `Pa` | tensor；cells或其单元子集，average | Cauchy应力；小应变时等同线性应力，完整对称矩阵 |
| `energy` | `J` | scalar；aggregate(sum)，source=cells且覆盖整个域，integral | 参考域上弹性储能积分 |

节点输出取连续解在给定节点的值；单元average按参考长度／面积／体积的Lebesgue测度作积分再除测度，不取节点算术均值。所有单元值使用参考域，即使超弹性Cauchy应力也以参考单元测度加权。线弹性储能U=½∫ε:σ，整体储能积分使用参考体积；二维平面应力乘实际thickness，其余二维按单位z长度输出。phase-field损伤energy按材料段含梯度项，其余elastic energy不含外力势；超弹性energy使用W。

## 合法范围与保证

除上文明确的自由键和时间轴名外不增加字段或条件组合。数据制作方须证明材料适用、网格非退化、载荷与约束相容、解在规定分支上可确定、所请求平均存在，并在题面预算内用独立基准达到目标精度。非线性分支保证是正式数据接收条件，不是校验器已经证明的事实。参数正值、JSON合法或低残差均不替代这些证据。尚无正式数据时不声称这些保证已获验证。
