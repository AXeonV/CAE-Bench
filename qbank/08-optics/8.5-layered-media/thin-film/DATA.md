# thin-film 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model=`optics-thin-film-v1`，task可省略，出现须为`thin-film`。禁止profile、contract_version、analysis、materials混用；不接受未列条件、字段或组合。

## 物理定义

平行无限层，z<0入射半空间、各实正折射率层及z>H出射半空间；无吸收、增益、磁性或粗糙面，e^(+iωt)。令p=n0 sinθ0，cosθ_j=√(1−p²/n_j²)>0，kz_j=(2π/λ0)n_j cosθ_j。TE取切向Ey，TM取固定全局切向Ex；反射也使用同一笛卡尔基底，不随传播方向翻转。相应光学导纳TE为Y_j=n_j cosθ_j/Z0，TM为Y_j=n_j/(Z0 cosθ_j)。每层切向场E=F exp(−ikz_j(z−z_left))+B exp(+ikz_j(z−z_left))，配对切向场G（不取复共轭）=Y_j(F exp(−ikz_j(z−z_left))−B exp(+ikz_j(z−z_left)))，各界面E和G连续。入射E振幅1，在z=0定义r，出射仅+z波，在z=H定义t；不把t再传播到其他参考面。R=|r|²，T=(Ys/Y0)|t|²。所有层及出射介质须p²/n_j²≤1−1e−8，排除倏逝和临界入射；不独立相加各界面反射强度，须保留多次反射相干。

## 全局参数

parameters恰含下表全部项，每项只有value和unit，数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `wavelength` | `m` | 真空波长λ0>0 |
| `input_index` | `1` | 入射半空间实折射率n0>0 |
| `output_index` | `1` | 出射半空间实折射率ns>0 |
| `vacuum_impedance` | `Ohm` | 真空波阻抗Z0>0 |
| `incidence_sine` | `1` | sinθ0，0≤s<1 |
| `polarization` | `1` | JSON整数0=TE，1=TM |

## 几何、对象和身份

spatial_dimension=1，固定坐标为m。locations恰为下表，无其他位置。entities为真实离散对象，IDs非负严格递增；不按ID数值猜坐标或物理参数。points为真实坐标且不能伪装成entities。层按layers IDs的数组行序沿正轴排列。meshes及geometries必须为空，无隐藏空间网格。spatial_dimension为物理维数或分层／有限维系统的协议标记，不引入额外空间方程。

| location | 完整支持与含义 |
|---|---|
| `layers` | entities，1..32个；按IDs行序沿正轴排列的有限层；ID本身不表示厚度或坐标 |
| `system` | entities，1..1个；唯一完整层系对象 |

## 时间、数组与重建

time_axes恰含键optical，其引用的float64[1]数组为[0.0]，所有输入和输出只引用该轴。0仅为单频／状态存储标记，不是物理初态或频谱轴。

所有输入场和输出场均float64，IDs为int64，时间轴按CONTRACT为float64。场数组[T,N,*component_shape]不省略轴。scalar固定[1]及components=["value"]；components按表中shape行优先展平为c1..cL；复量最内层2依次实／虚，不用复数dtype或幅相。条件data引用fields逻辑名，该对象的array才是HDF5 key，两者名称自由。fields恰为实际引用项；quantity等于data键名，value例外等于条件variable。字段必须与条件同location，不能按相同长度借别处数据。scalar data可用同单位有限实数value/unit常量或显式field，非scalar类型只能field，不允许内联数组。输入sampling必须显式：time=constant、extrapolation=forbid，entities的space=uniform、value_kind=point。不作实体间插值或隐藏时间演化。

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
| `reflection` | components [2]，`1`；固定切向电场基底的复振幅系数r | `system`全部对象，point |
| `transmission` | components [2]，`1`；固定切向电场基底的复振幅系数t | `system`全部对象，point |
| `reflectance` | scalar [1]，`1`；功率反射率R | `system`全部对象，point |
| `transmittance` | scalar [1]，`1`；功率透射率T | `system`全部对象，point |

结果HDF5只含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标、新网格或额外数组。

## 接收限制

离散对象数量按DATA各表；唯一时间轴1帧；全部输入／输出场各至多2000000数值分量。正式数据须独立核验本题模型适用、参数相容、所请求观测存在、参考精度与预算内可达性；校验器只检查声明，不证明物理或数值准确性。
