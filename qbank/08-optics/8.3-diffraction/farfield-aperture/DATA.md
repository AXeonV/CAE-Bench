# farfield-aperture 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model=`optics-farfield-aperture-v1`，task可省略，出现须为`farfield-aperture`。禁止profile、contract_version、analysis、materials混用；不接受未列条件、字段或组合。

## 物理定义

均匀背景中的指定标量角分布衍射模型，e^(+iωt)，λ=λ0/n，k=2π/λ。z=0有限孔径上U0、孔径外0。对单位出射方向s且s_z>0，A(s)=i s_z/λ ∫孔径 U0(x,y) exp[+ik(s_x x+s_y y)] dxdy。远处U(Rs)~A(s)exp(−ikR)/R，A单位V。radiant_intensity=|A|²/(2Z)，单位W/sr；这是每立体角功率，不是某个虚构距离的W/m²点强度。倾斜因子明确为s_z，不另选标量边界近似。

## 全局参数

parameters恰含下表全部项，每项只有value和unit，数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `wavelength` | `m` | 真空波长λ0>0 |
| `refractive_index` | `1` | 均匀背景折射率n>0 |
| `impedance` | `Ohm` | 背景波阻抗Z>0；仅用于给定强度归一化 |

## 几何、对象和身份

spatial_dimension=3，固定坐标为m。locations恰为下表，无其他位置。entities为真实离散对象，IDs非负严格递增；不按ID数值猜坐标或物理参数。points为真实坐标且不能伪装成entities。meshes恰为main，MSH4.1 ASCII，只含z=0的非退化一阶三角形type2，至多800三角形、4000所用节点；不导出边界线、点或其他单元，无未用节点、重叠或自交，允许孔洞和互不接触的孔径片。domain及aperture须完整；geometries若给仅作来源，求解几何以网格为准。

| location | 完整支持与含义 |
|---|---|
| `domain` | main的全部节点；孔径全部节点 |
| `aperture` | main的全部一阶三角形单元，dimension=2；孔径全部三角形 |
| `directions` | entities，1..256个；出射方向对象，无空间接收距离 |

## 时间、数组与重建

time_axes恰含键optical，其引用的float64[1]数组为[0.0]，所有输入和输出只引用该轴。0仅为单频／状态存储标记，不是物理初态或频谱轴。

所有输入场和输出场均float64，IDs为int64，时间轴按CONTRACT为float64。场数组[T,N,*component_shape]不省略轴。scalar固定[1]及components=["value"]；vector固定[3]及x/y/z；components按表中shape行优先展平为c1..cL；复量最内层2依次实／虚，不用复数dtype或幅相。条件data引用fields逻辑名，该对象的array才是HDF5 key，两者名称自由。fields恰为实际引用项；quantity等于data键名，value例外等于条件variable。字段必须与条件同location，不能按相同长度借别处数据。scalar data可用同单位有限实数value/unit常量或显式field，非scalar类型只能field，不允许内联数组。输入sampling必须显式：time=constant、extrapolation=forbid，entities的space=uniform、value_kind=point；孔径元素space=piecewise_constant、value_kind=average，表示每片唯一常值；domain节点不接受输入场。不作实体间插值或隐藏时间演化。所有声明为单位方向的输入字段均须|norm(d)−1|≤1e−12；公式按原存储分量求值，不由考生归一化。此规则不作用于带长度单位的坐标。

## 条件全集

### `aperture_field`

role=`source`，variable=`amplitude`，operator=`aperture_field`，location=`aperture`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `value` | components [2]，`V/m`；输入孔径复场U0，逐三角形常值，孔径外为0 |

### `directions`

role=`source`，variable=`direction`，operator=`directions`，location=`directions`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `value` | vector [3]，`1`；单位出射方向s，s_z≥1e−4 |

## 输出

每个quantity至少出现一次，可重复请求；逻辑名和array key自由，但不得改变quantity、单位或位置。全部float64，无sampling，shape和components按上述规则，均引用optical。

| quantity | 类型、单位和含义 | 完整位置与value_kind |
|---|---|---|
| `far_amplitude` | components [2]，`V`；远场系数A(s) | `directions`全部对象，point |
| `radiant_intensity` | scalar [1]，`W/sr`；每单位立体角功率|A|²/(2Z) | `directions`全部对象，point |

结果HDF5只含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标、新网格或额外数组。

## 接收限制

孔径至多800三角形、4000节点，其他对象数量按DATA各表；唯一时间轴1帧；全部输入／输出场各至多2000000数值分量。正式数据须独立核验本题模型适用、参数相容、所请求观测存在、参考精度与预算内可达性；校验器只检查声明，不证明物理或数值准确性。孔径几何须独立核验无重叠／自交。
