# maxwell-cavity 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰为model、parameters；model=`electromagnetic-maxwell-cavity-v1`，task可省略，出现须为`maxwell-cavity`。禁止profile、contract_version、analysis或materials混用；不能以题号补物理。

## 物理定义

三维有界静止各向同性线性介质，ε、μ、σ均为逐四面体正实常数，e^(+iωt)相量。求curl(μ^−1 curl E)−(ω²ε−iωσ)E=−iωJs，H=i curl E/(ωμ)，时间平均损耗D=σ|E|²/2。全部外边界PEC：n×E=0；不附加E法向为0。内部无附加表面电流，E及H切向连续，分布意义方程含源所需自由电荷；不额外把div E设为0。保留位移电流，无端口、PML、开放辐射或本征模任务。

## 全局参数

parameters恰含下表项，每项只有value和unit；有限实数，布尔不能作数值，整数须JSON整数。空表表示parameters={}。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `frequency` | `Hz` | f>0，ω=2πf |

## 几何和身份

meshes恰含main；MSH4.1 ASCII，坐标m，spatial_dimension=3。main只含非退化一阶四面体type4及全部外边界三角形type2。无未用节点、悬挂节点、重叠体、自交或非流形公共面；域通过完整公共边／面连通；每个外面导出一次，不导出更低维单元。domain恰为main全部节点，cells恰为全部体单元；其他location仅main节点、体单元或外边界元素的非空子集。tag为身份不是行号，Physical Group若声明必须与IDs精确相符，组名不定义物理。禁止points或aggregate。禁止entities。PEC作用于全部外面，无boundary记录。

## 时间、数组与重建

time_axes仅含键harmonic，其引用的float64[1]数组恰为[0.0]，所有字段和输出引用该轴。0仅为相量存储标记。

条件data引用fields逻辑名，其array才是HDF5 key，两者名称自由。fields恰为全部实际引用项；quantity等于data键名，value例外等于条件variable。字段须与条件同location。数组[T,N,*component_shape]不省略轴；scalar=[1]、components=["value"]；复标量components [2]依次实虚，复向量components [3,2]按x/y/z各自实虚，组件标签按shape行优先展平c1..cL，不使用复数dtype、幅相或RMS。所有数值float64。scalar数据可用同单位有限数值value/unit常量或field；components必须field，不允许内联数组。输入value_kind节点为point、单元为average；节点sampling.space=piecewise_linear，为一阶网格上的唯一P1重建，元素为piecewise_constant，元素值即该元素常值。sampling必须显式，extrapolation=forbid，时间单帧constant。只作上述空间／实体重建，无额外时间演化。无本题未列数据、选项、模型或隐藏默认值。

## 条件全集

### `material`

role=`material`，variable=`electromagnetic`，operator=`material`；location为cells完整体域，恰一条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `permittivity` | scalar [1]，F/m；绝对介电常数ε>0；严格正 |
| `permeability` | scalar [1]，H/m；绝对磁导率μ>0；严格正 |
| `conductivity` | scalar [1]，S/m；电导率σ>0；严格正 |

### `current_source`

role=`source`，variable=`current_density`，operator=`current_source`；location为cells完整体域，恰一条。必须出现。data恰含以下全部键：

| 键 | 类型、单位、含义 |
|---|---|
| `value` | components [3, 2]，A/m2；外加体电流Js |

## 输出

逻辑名与array key自由，每个quantity至少出现一次，可重复请求；全部float64，无sampling，时间轴为harmonic，shape及components遵守前述规则。

| quantity | 类型、单位与含义 | 位置与value_kind |
|---|---|---|
| `electric_field` | components [3, 2]，V/m；E | cells或非空体单元子集，average |
| `magnetic_field` | components [3, 2]，A/m；H | cells或非空体单元子集，average |
| `joule_loss` | scalar [1]，W/m3；时间平均焦耳损耗 | cells或非空体单元子集，average |

体单元按实际体积积分再除体积／面积，不得把点值当作积分平均；在所用场表示下与积分严格等价的重心值、节点均值或求积公式允许使用。焦耳损耗先逐点计算再平均，不能从平均场平方得到。结果仅含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标或新网格。

## 接收限制

至多1800四面体、6000节点。唯一时间轴含1帧，输入场和输出场各至多4000000数值分量。正式数据须独立核验几何与材料适用、源及边界条件相容、正则／唯一响应、观测存在和预算内精度；校验器不证明这些性质。结构合法不代表电磁结果正确。
