# magnetized-plasma-slab 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-magnetized-plasma-slab-v1`；task可省略，出现须为`magnetized-plasma-slab`。spatial_dimension=1；不混用profile、contract_version、analysis或materials。

## 物理语义

采用Re[F(x)exp(−iωt)]。层从x=0依次到H=Σh，两侧为相同ε、μ的无等离子体半空间，无右入射。背景磁场Bx沿+x且全空间恒定。每层的横向u满足m(ν−iω)u=q(E+u×Bx e_x)，J=n q u；纵向场和速度为零。Maxwell为∇×E=iωμH场、∇×H场=J−iωεE；界面Ey、Ez、Hy、Hz连续，无自由面电流。入射／反射振幅定义于x=0，透射振幅定义于x=H。左侧E=Ei exp(ikx)+Er exp(−ikx)，右侧E=Et exp(ik(x−H))，k=ωsqrt(εμ)，波阻抗Z=sqrt(μ/ε)，各行波H场=传播单位方向×E/Z。R=|Er|²/|Ei|²，T=|Et|²/|Ei|²，不按各偏振分别除入射分量。输出层内场包含所有反射与透射；不求随机粒子、热运动、非线性密度或纵向电静波。

## 全局参数

parameters恰含下表，标量均为{"value":数值,"unit":单位}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `angular_frequency` | `1/s` | 角频率ω>0，单位不另乘2π |
| `permittivity` | `F/m` | 两侧背景和全部层的束缚电荷介电常数ε>0 |
| `permeability` | `H/m` | 各处磁导率μ>0 |
| `mass` | `kg` | 移动负电物种质量m>0 |
| `charge` | `C` | 移动负电物种q<0 |

## 位置、几何与身份

meshes及geometries均为空，系统不提供空间网格。entities是真实粒子、物种、状态或层对象，不是伪造空间探针。 locations恰含下表；entities的IDs非负严格递增，system恰一对象；ID数值不携带物理含义。points的IDs非负严格递增，coordinates为float64[N,D]米制坐标。对象之间无默认邻接或插值。

| location | 支持范围与含义 |
|---|---|
| `layers` | entities，1..32个；沿+x的均匀层；行序决定层次 |
| `system` | entities，1..1个；唯一入射／散射系统 |
| `receivers` | points，1..256个；层内真实一维空间接收点，坐标单位m |

## 时间与数组

time_axes恰含initial、output。initial和output两轴均恰为float64[1]的[0.0]，0仅为稳态存储标记。 initial轴上的材料或源表示全过程固定量，不是额外初态。

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。`incident.value`的components固定为`["y_real", "y_imag", "z_real", "z_imag"]`。 `reflected_amplitude`的components固定为`["y_real", "y_imag", "z_real", "z_imag"]`。 `transmitted_amplitude`的components固定为`["y_real", "y_imag", "z_real", "z_imag"]`。 `electric_amplitude`的components固定为`["y_real", "y_imag", "z_real", "z_imag"]`。 `magnetic_amplitude`的components固定为`["y_real", "y_imag", "z_real", "z_imag"]`。

fields恰含条件实际引用的字段；data键引用{"field":"逻辑字段名"}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{"value":有限标量,"unit":"单位"}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；initial场time=constant。space=uniform，仅表示对象自身属性，不作对象间空间重建。 输入value_kind：所有位置为point。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

### `layers`

role=`material`、variable=`plasma_layer`、operator=`layers`、location=`layers`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `thickness` | kind=`scalar`、component_shape=`[1]`，`m`；每层厚h>0 | initial |
| `density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；移动物种平衡数密度n>0，静止正背景中和 | initial |
| `collision_frequency` | kind=`scalar`、component_shape=`[1]`，`1/s`；正的动量碰撞率ν>0 | initial |

### `magnetic`

role=`source`、variable=`magnetic_field`、operator=`magnetic`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`scalar`、component_shape=`[1]`，`T`；所有层及两侧共同的恒定有符号背景Bx，沿+x | initial |

### `incident`

role=`source`、variable=`incident_electric`、operator=`incident`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`components`、component_shape=`[2,2]`，`V/m`；x=0处向右入射的Ey、Ez复振幅，非零 | initial |

## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为所有位置为point，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
| `reflected_amplitude` | kind=`components`、component_shape=`[2,2]`，`V/m`；x=0处Er的Ey、Ez | `system` |
| `transmitted_amplitude` | kind=`components`、component_shape=`[2,2]`，`V/m`；x=H处Et的Ey、Ez | `system` |
| `electric_amplitude` | kind=`components`、component_shape=`[2,2]`，`V/m`；接收点总场Ey、Ez | `receivers` |
| `magnetic_amplitude` | kind=`components`、component_shape=`[2,2]`，`A/m`；接收点总场Hy、Hz | `receivers` |
| `reflectance` | kind=`scalar`、component_shape=`[1]`，`1`；总功率反射率R | `system` |
| `transmittance` | kind=`scalar`、component_shape=`[1]`，`1`；总功率透射率T | `system` |

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

每层n、ν、h严格正；入射两复分量的总模平方>0。接收点须严格位于某一层内部，不在界面或半空间，ID行序不代表x顺序。正碰撞率限定有耗响应；正式数据需校准近共振难度及场观测精度。 1e−14≤ε≤1e−8 F/m，1e−8≤μ≤1e−4 H/m；各层须0.001≤ν/ω≤100、sqrt(n q²/(mε))/ω≤30、|q Bx|/(mω)≤30；总光学厚度ωsqrt(εμ)H≤100；入射复矢量模长在[1e−6,1e6] V/m。 所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
