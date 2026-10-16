# slab-modes 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model=`optics-slab-modes-v1`，task可省略，出现须为`slab-modes`。禁止profile、contract_version、analysis、materials混用；不接受未列条件、字段或组合。

## 物理定义

无耗非磁性平板沿z导波，折射率只依赖x：x<0为nL，有限层按厚度排列于[0,H]，x>H为nR。e^(+iωt−iβz)，k0=2π/λ0，β>0。TE剖面f=Ey满足f''+(k0²n²−β²)f=0且f、f'连续；TM剖面f=Hy满足(n^−2 f')'+(k0²−β²/n²)f=0且f、n^−2 f'连续。两端为真正无限包层的指数衰减，不用有限箱体零边界代替。只求β/k0>max(nL,nR)的实导模，按neff从大到小取前m个；数据保证至少m个且远离截止，模态简单无排序简并。每个剖面为实，∫全实轴 f² dx=1，包含无限包层尾部，且f(0)>0定相；输出为归一化剖面，单位m^(−1/2)，不冒充物理场振幅或单位功率模态。receivers只用横坐标x，y=z=0。

## 全局参数

parameters恰含下表全部项，每项只有value和unit，数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `wavelength` | `m` | 真空波长λ0>0 |
| `left_index` | `1` | x<0包层折射率nL>0 |
| `right_index` | `1` | x>H包层折射率nR>0 |
| `polarization` | `1` | JSON整数0=TE(Ey)，1=TM(Hy) |
| `mode_count` | `1` | 请求m个导模，JSON整数1..8；数据保证至少存在m个 |

## 几何、对象和身份

spatial_dimension=1，固定坐标为m。locations恰为下表，无其他位置。entities为真实离散对象，IDs非负严格递增；不按ID数值猜坐标或物理参数。points为真实坐标且不能伪装成entities。层按layers IDs的数组行序沿正轴排列。meshes及geometries必须为空，无隐藏空间网格。spatial_dimension为物理维数或分层／有限维系统的协议标记，不引入额外空间方程。receivers.coordinates实际为[N,1]，只存x；(x,0,0)仅表示物理嵌入，y=z=0不占HDF5列。

| location | 完整支持与含义 |
|---|---|
| `layers` | entities，1..32个；按IDs行序沿正轴排列的有限层；ID本身不表示厚度或坐标 |
| `modes` | entities，1..8个；恰m个导模，IDs固定0..m−1，对应neff从大到小 |
| `receivers` | points，1..256个；真实横向采样点(x,0,0)，可在芯层或包层 |

## 时间、数组与重建

time_axes恰含键optical，其引用的float64[1]数组为[0.0]，所有输入和输出只引用该轴。0仅为单频／状态存储标记，不是物理初态或频谱轴。

所有输入场和输出场均float64，IDs为int64，时间轴按CONTRACT为float64。场数组[T,N,*component_shape]不省略轴。scalar固定[1]及components=["value"]；components按表中shape行优先展平为c1..cL；复量最内层2依次实／虚，不用复数dtype或幅相。表中m代入mode_count，实剖面shape=[m]，第j分量对应modes ID j。条件data引用fields逻辑名，该对象的array才是HDF5 key，两者名称自由。fields恰为实际引用项；quantity等于data键名，value例外等于条件variable。字段必须与条件同location，不能按相同长度借别处数据。scalar data可用同单位有限实数value/unit常量或显式field，非scalar类型只能field，不允许内联数组。输入sampling必须显式：time=constant、extrapolation=forbid，entities的space=uniform、value_kind=point。不作实体间插值或隐藏时间演化。

## 条件全集

### `layers`

role=`material`，variable=`optical_layer`，operator=`layers`，location=`layers`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `index` | scalar [1]，`1`；各层实折射率n>0；严格正 |
| `thickness` | scalar [1]，`m`；各层厚度h>0；严格正 |

## 输出

每个quantity至少出现一次，可重复请求；逻辑名和array key自由，但不得改变quantity、单位或位置。全部float64，无sampling，shape和components按上述规则，均引用optical。

| quantity | 类型、单位和含义 | 完整位置与value_kind |
|---|---|---|
| `effective_index` | scalar [1]，`1`；neff=β/k0，按从大到小排序 | `modes`全部对象，point |
| `mode_profile` | components ['m']，`m^(-1/2)`；所有m个实归一化剖面；分量顺序同modes IDs | `receivers`全部对象，point |

结果HDF5只含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标、新网格或额外数组。

## 接收限制

离散对象及接收点数量按DATA各表；唯一时间轴1帧；全部输入／输出场各至多2000000数值分量。正式数据须独立核验本题模型适用、参数相容、所请求观测存在、参考精度与预算内可达性；校验器只检查声明，不证明物理或数值准确性。有限层最大折射率须严格大于两包层；模态存在数量、截止距离和谱间隔须由数据制作独立核验，不能由给定mode_count假称已证明。
