# layered-rays 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model=`optics-layered-rays-v1`，task可省略，出现须为`layered-rays`。禁止profile、contract_version、analysis、materials混用；不接受未列条件、字段或组合。

## 物理定义

三维射线在平行平面分层介质中传播，层沿+z依次排列，界面z=0,h1,h1+h2,…,H；上下半空间折射率n0和nout。每条射线从z=0处向+z入射，按Snell定律保持界面切向n d连续，透射方向法向分量取正。若首个不能透射的界面发生全反射，将法向方向反号，终点为该界面交点，并立即终止，不再追踪反射支路；termination=1。若通过全部层及z=H出口，终点为H面交点、方向为出射介质透射方向，termination=0。首次入射界面全反射时终点仍为起点、光程0。累计光程只计已走过的有限层内∫n ds，不含上下半空间距离。允许偏折、全反射，不计算Fresnel功率分裂、相干相位或偏振。对所有潜在界面，q=n0²(dx²+dy²)，须满足|q/n_target²−1|≥1e−8，排除临界／掠射退化。

## 全局参数

parameters恰含下表全部项，每项只有value和unit，数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `input_index` | `1` | z<0的入射介质n0>0 |
| `output_index` | `1` | z>H的出射介质nout>0 |

## 几何、对象和身份

spatial_dimension=3，固定坐标为m。locations恰为下表，无其他位置。entities为真实离散对象，IDs非负严格递增；不按ID数值猜坐标或物理参数。points为真实坐标且不能伪装成entities。层按layers IDs的数组行序沿正轴排列。meshes及geometries必须为空，无隐藏空间网格。spatial_dimension为物理维数或分层／有限维系统的协议标记，不引入额外空间方程。

| location | 完整支持与含义 |
|---|---|
| `layers` | entities，1..32个；按IDs行序沿正轴排列的有限层；ID本身不表示厚度或坐标 |
| `rays` | entities，1..128个；各独立入射射线 |

## 时间、数组与重建

time_axes恰含键steady，其引用的float64[1]数组为[0.0]，所有输入和输出只引用该轴。0仅为静态存储标记，不是物理初态或频谱轴。

所有输入场和输出场均float64，IDs为int64，时间轴按CONTRACT为float64。场数组[T,N,*component_shape]不省略轴。scalar固定[1]及components=["value"]；vector固定[3]及x/y/z；条件data引用fields逻辑名，该对象的array才是HDF5 key，两者名称自由。fields恰为实际引用项；quantity等于data键名，value例外等于条件variable。字段必须与条件同location，不能按相同长度借别处数据。scalar data可用同单位有限实数value/unit常量或显式field，非scalar类型只能field，不允许内联数组。输入sampling必须显式：time=constant、extrapolation=forbid，entities的space=uniform、value_kind=point。不作实体间插值或隐藏时间演化。所有声明为单位方向的输入字段均须|norm(d)−1|≤1e−12；公式按原存储分量求值，不由考生归一化。此规则不作用于带长度单位的坐标。

## 条件全集

### `layers`

role=`material`，variable=`optical_layer`，operator=`layers`，location=`layers`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `index` | scalar [1]，`1`；各层实折射率n>0；严格正 |
| `thickness` | scalar [1]，`m`；各层厚度h>0；严格正 |

### `launch`

role=`source`，variable=`ray`，operator=`launch`，location=`rays`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `origin` | vector [3]，`m`；在z=0的起点 |
| `direction` | vector [3]，`1`；入射单位方向，d_z≥1e−4 |

## 输出

每个quantity至少出现一次，可重复请求；逻辑名和array key自由，但不得改变quantity、单位或位置。全部float64，无sampling，shape和components按上述规则，均引用steady。

| quantity | 类型、单位和含义 | 完整位置与value_kind |
|---|---|---|
| `terminal_position` | vector [3]，`m`；终点坐标 | `rays`全部对象，point |
| `terminal_direction` | vector [3]，`1`；终点方向 | `rays`全部对象，point |
| `optical_path` | scalar [1]，`m`；从发射到终止的∫n ds | `rays`全部对象，point |
| `termination` | scalar [1]，`1`；0=成功出射，1=首次全反射后终止 | `rays`全部对象，point |

结果HDF5只含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标、新网格或额外数组。

## 接收限制

离散对象数量按DATA各表；唯一时间轴1帧；全部输入／输出场各至多2000000数值分量。正式数据须独立核验本题模型适用、参数相容、所请求观测存在、参考精度与预算内可达性；校验器只检查声明，不证明物理或数值准确性。
