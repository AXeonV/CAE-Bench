# jones-chain 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model=`optics-jones-chain-v1`，task可省略，出现须为`jones-chain`。禁止profile、contract_version、analysis、materials混用；不接受未列条件、字段或组合。

## 物理定义

固定共同横向xy基底、单频e^(+iωt)峰值Jones向量e=(Ex,Ey)。各元件矩阵已给定，按elements的IDs行序先J1后J2…作用，eout=JN…J2J1 ein；矩阵在同一基底，无隐含旋转、传播相位或基底重置。J†J≼I，只含确定、无去偏振的被动元件。对输出定义S0=|Ex|²+|Ey|²，S1=|Ex|²−|Ey|²，S2=2Re(Ex Ey*)，S3=2Im(Ex Ey*)，I=S0/(2Z)。S3的符号以此公式为准，不借左／右旋名称猜测；不归一化Stokes、不丢弃总强度或全局相位。

## 全局参数

parameters恰含下表全部项，每项只有value和unit，数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `impedance` | `Ohm` | 背景波阻抗Z>0 |

## 几何、对象和身份

spatial_dimension=1，固定坐标为m。locations恰为下表，无其他位置。entities为真实离散对象，IDs非负严格递增；不按ID数值猜坐标或物理参数。points为真实坐标且不能伪装成entities。元件按elements IDs的数组行序依次作用。meshes及geometries必须为空，无隐藏空间网格。spatial_dimension为物理维数或分层／有限维系统的协议标记，不引入额外空间方程。

| location | 完整支持与含义 |
|---|---|
| `elements` | entities，1..64个；同一固定xy横向基底下的有序Jones元件，按IDs行序依次作用 |
| `states` | entities，1..64个；彼此独立的输入偏振态 |

## 时间、数组与重建

time_axes恰含键optical，其引用的float64[1]数组为[0.0]，所有输入和输出只引用该轴。0仅为单频／状态存储标记，不是物理初态或频谱轴。

所有输入场和输出场均float64，IDs为int64，时间轴按CONTRACT为float64。场数组[T,N,*component_shape]不省略轴。scalar固定[1]及components=["value"]；components按表中shape行优先展平为c1..cL；复量最内层2依次实／虚，不用复数dtype或幅相。Stokes为实[4]数组，不增加复轴。条件data引用fields逻辑名，该对象的array才是HDF5 key，两者名称自由。fields恰为实际引用项；quantity等于data键名，value例外等于条件variable。字段必须与条件同location，不能按相同长度借别处数据。scalar data可用同单位有限实数value/unit常量或显式field，非scalar类型只能field，不允许内联数组。输入sampling必须显式：time=constant、extrapolation=forbid，entities的space=uniform、value_kind=point。不作实体间插值或隐藏时间演化。矩阵value[0,e,a,b,0/1]为J_ab实／虚部，a为输出x/y、b为输入x/y；检查最大奇异值≤1+1e−12，生产数据保证J†J≼I；不归一化或修正矩阵。

## 条件全集

### `elements`

role=`material`，variable=`jones_matrix`，operator=`elements`，location=`elements`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `value` | components [2, 2, 2]，`1`；复Jones矩阵J；J†J≼I，被动无增益 |

### `states`

role=`source`，variable=`jones`，operator=`states`，location=`states`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `value` | components [2, 2]，`V/m`；Ex、Ey复振幅，最内层实虚 |

## 输出

每个quantity至少出现一次，可重复请求；逻辑名和array key自由，但不得改变quantity、单位或位置。全部float64，无sampling，shape和components按上述规则，均引用optical。

| quantity | 类型、单位和含义 | 完整位置与value_kind |
|---|---|---|
| `jones` | components [2, 2]，`V/m`；输出Ex、Ey复振幅 | `states`全部对象，point |
| `stokes` | components [4]，`V2/m2`；按S0,S1,S2,S3顺序 | `states`全部对象，point |
| `intensity` | scalar [1]，`W/m2`；S0/(2Z) | `states`全部对象，point |

结果HDF5只含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标、新网格或额外数组。

## 接收限制

离散对象数量按DATA各表；唯一时间轴1帧；全部输入／输出场各至多2000000数值分量。正式数据须独立核验本题模型适用、参数相容、所请求观测存在、参考精度与预算内可达性；校验器只检查声明，不证明物理或数值准确性。零态、零矩阵及理想偏振片允许，不把被动性误解为可逆性。
