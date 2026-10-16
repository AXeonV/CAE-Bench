# coherent-interference 数据契约

入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model=`optics-coherent-interference-v1`，task可省略，出现须为`coherent-interference`。禁止profile、contract_version、analysis、materials混用；不接受未列条件、字段或组合。

## 物理定义

均匀介质单频标量固定偏振近似，e^(+iωt)，k=2πn/λ0。U(r)=Σ_j a_j exp[−ik d_j·(r−r_j)]，I=|U|²/(2Z)。各波完全相干，共用固定相位参考约定，不逐波强度相加，不另作方向相关矢量偏振投影。Z显式给定用于强度归一化，振幅为峰值相量而非RMS。

## 全局参数

parameters恰含下表全部项，每项只有value和unit，数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `wavelength` | `m` | 真空波长λ0>0 |
| `refractive_index` | `1` | 均匀背景折射率n>0 |
| `impedance` | `Ohm` | 背景波阻抗Z>0；仅用于给定强度归一化 |
| `wave_count` | `1` | 模态数w，JSON整数1..32 |

## 几何、对象和身份

spatial_dimension=3，固定坐标为m。locations恰为下表，无其他位置。entities为真实离散对象，IDs非负严格递增；不按ID数值猜坐标或物理参数。points为真实坐标且不能伪装成entities。meshes及geometries必须为空，无隐藏空间网格。spatial_dimension为物理维数或分层／有限维系统的协议标记，不引入额外空间方程。

| location | 完整支持与含义 |
|---|---|
| `waves` | entities，1..32个；恰w个平面波，IDs固定0..w−1，矩阵索引按此顺序 |
| `receivers` | points，1..256个；真实三维接收点 |

## 时间、数组与重建

time_axes恰含键optical，其引用的float64[1]数组为[0.0]，所有输入和输出只引用该轴。0仅为单频／状态存储标记，不是物理初态或频谱轴。

所有输入场和输出场均float64，IDs为int64，时间轴按CONTRACT为float64。场数组[T,N,*component_shape]不省略轴。scalar固定[1]及components=["value"]；vector固定[3]及x/y/z；components按表中shape行优先展平为c1..cL；复量最内层2依次实／虚，不用复数dtype或幅相。条件data引用fields逻辑名，该对象的array才是HDF5 key，两者名称自由。fields恰为实际引用项；quantity等于data键名，value例外等于条件variable。字段必须与条件同location，不能按相同长度借别处数据。scalar data可用同单位有限实数value/unit常量或显式field，非scalar类型只能field，不允许内联数组。输入sampling必须显式：time=constant、extrapolation=forbid，entities的space=uniform、value_kind=point。不作实体间插值或隐藏时间演化。所有声明为单位方向的输入字段均须|norm(d)−1|≤1e−12；公式按原存储分量求值，不由考生归一化。此规则不作用于带长度单位的坐标。

## 条件全集

### `waves`

role=`source`，variable=`optical_wave`，operator=`waves`，location=`waves`；恰一条覆盖完整该位置。data恰含下表全部键：

| 键 | 类型、单位和含义 |
|---|---|
| `direction` | vector [3]，`1`；单位传播方向d_j |
| `reference` | vector [3]，`m`；每个模式的相位参考点r_j |
| `amplitude` | components [2]，`V/m`；参考点处复振幅a_j |

## 输出

每个quantity至少出现一次，可重复请求；逻辑名和array key自由，但不得改变quantity、单位或位置。全部float64，无sampling，shape和components按上述规则，均引用optical。

| quantity | 类型、单位和含义 | 完整位置与value_kind |
|---|---|---|
| `amplitude` | components [2]，`V/m`；相干标量复场U | `receivers`全部对象，point |
| `intensity` | scalar [1]，`W/m2`；平均强度 | `receivers`全部对象，point |

结果HDF5只含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标、新网格或额外数组。

## 接收限制

离散对象及接收点数量按DATA各表；唯一时间轴1帧；全部输入／输出场各至多2000000数值分量。正式数据须独立核验本题模型适用、参数相容、所请求观测存在、参考精度与预算内可达性；校验器只检查声明，不证明物理或数值准确性。
