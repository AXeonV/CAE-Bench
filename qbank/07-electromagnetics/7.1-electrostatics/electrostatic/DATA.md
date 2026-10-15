# electrostatic 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰为model、parameters；model=`electromagnetic-electrostatic-v1`，task可省略，出现须为`electrostatic`。禁止profile、contract_version、analysis或materials混用；不能以题号补物理。

## 物理定义

二维xy平面、z平移不变，材料逐三角形常数，各向同性线性。E=−∇V。D=εE，div D=ρf。内部界面V连续、D法向连续，无额外界面自由电荷。外法向n指向计算域外；Dirichlet固定V，normal_flux给D·n；其余外边界D·n=0。至少一条Dirichlet锚定绝对电势。二维面积／边界积分按单位z长度解释；没有隐含厚度。

## 全局参数

parameters恰含下表项，每项只有value和unit；有限实数，布尔不能作数值，整数须JSON整数。空表表示parameters={}。

| 参数 | 单位 | 含义与范围 |
|---|---|---|


## 几何和身份

meshes恰含main；MSH4.1 ASCII，坐标m，spatial_dimension=2。main只含非退化一阶三角形type2及全部外边界线type1，全部节点z=0。无未用节点、悬挂节点、重叠体、自交或非流形公共面；域通过完整公共边／面连通；每个外面导出一次，不导出更低维单元。domain恰为main全部节点，cells恰为全部体单元；其他location仅main节点、体单元或外边界元素的非空子集。tag为身份不是行号，Physical Group若声明必须与IDs精确相符，组名不定义物理。禁止points或aggregate。禁止entities。节点边界取所有顶点均属于该节点集的全部完整外面，节点集须恰等于这些面的顶点并。Dirichlet至少一条，各节点边界的节点集互不相交；所有边界作用面不得重叠。已声明边界与其余默认自然边界共享端点时按弱解解释，数据须保证所需观测存在。

## 时间、数组与重建

time_axes仅含键steady，其引用的float64[1]数组恰为[0.0]，所有字段和输出引用该轴。0仅为静态存储标记。

条件data引用fields逻辑名，其array才是HDF5 key，两者名称自由。fields恰为全部实际引用项；quantity等于data键名，value例外等于条件variable。字段须与条件同location。数组[T,N,*component_shape]不省略轴；scalar=[1]、components=["value"]；vector固定[2]及x/y。所有数值float64。scalar数据可用同单位有限数值value/unit常量或field；vector必须field，不允许内联数组。输入value_kind节点为point、单元为average；节点sampling.space=piecewise_linear，为一阶网格上的唯一P1重建，元素为piecewise_constant，元素值即该元素常值。sampling必须显式，extrapolation=forbid，时间单帧constant。只作上述空间／实体重建，无额外时间演化。无本题未列数据、选项、模型或隐藏默认值。

## 条件全集

### `material`

role=`material`，variable=`electromagnetic`，operator=`material`；location为cells完整体域，恰一条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `permittivity` | scalar [1]，F/m；绝对介电常数ε>0；严格正 |

### `dirichlet`

role=`boundary`，variable=`potential`，operator=`dirichlet`；location为上述闭包规则的外边界节点集，可多条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `value` | scalar [1]，V；给定电势 |

### `volume_source`

role=`source`，variable=`charge_density`，operator=`volume_source`；location为cells完整体域，恰一条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `value` | scalar [1]，C/m3；自由体电荷ρf |

### `normal_flux`

role=`boundary`，variable=`displacement_flux`，operator=`normal_flux`；location为外面元素集，可多条。可不出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `value` | scalar [1]，C/m2；域外正的D·n |

## 输出

逻辑名与array key自由，每个quantity至少出现一次，可重复请求；全部float64，无sampling，时间轴为steady，shape及components遵守前述规则。

| quantity | 类型、单位与含义 | 位置与value_kind |
|---|---|---|
| `potential` | scalar [1]，V；电势V | cells或非空体单元子集，average |
| `electric_field` | vector [2]，V/m；E=−∇V | cells或非空体单元子集，average |
| `electric_displacement` | vector [2]，C/m2；D=εE | cells或非空体单元子集，average |

体单元按实际三角面积积分再除体积／面积，不得把点值当作积分平均；在所用场表示下与积分严格等价的重心值、节点均值或求积公式允许使用。结果仅含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标或新网格。

## 接收限制

至多5000三角形、6000节点。唯一时间轴含1帧，输入场和输出场各至多4000000数值分量。正式数据须独立核验几何与材料适用、源及边界条件相容、正则／唯一响应、观测存在和预算内精度；校验器不证明这些性质。结构合法不代表电磁结果正确。
