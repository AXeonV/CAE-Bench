# charged-orbits 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-charged-orbits-v1`；task可省略，出现须为`charged-orbits`。spatial_dimension=3；不混用profile、contract_version、analysis或materials。

## 物理语义

在全空间R³中演化各独立粒子。外电场E(x,t)=E0(t)+G(t)(x−r0)，G为对称矩阵；外磁场B0均匀恒定。无空间电荷反馈、粒子间力、碰撞、壁面、逃逸终止或辐射反作用。dx/dt=v，m dv/dt=q(E+v×B0)。非相对论模型不添加γ或速度裁剪。

## 全局参数

parameters恰含下表，标量均为{"value":数值,"unit":单位}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `end_time` | `s` | 物理终时τ，0<τ≤1000000 |

## 位置、几何与身份

meshes及geometries均为空，系统不提供空间网格。entities是真实粒子、物种、状态或层对象，不是伪造空间探针。 locations恰含下表；entities的IDs非负严格递增，system恰一对象；ID数值不携带物理含义。对象之间无默认邻接或插值。

| location | 支持范围与含义 |
|---|---|
| `particles` | entities，1..128个；互不作用的带电粒子 |
| `system` | entities，1..1个；唯一外场参数对象 |

## 时间与数组

time_axes恰含initial、output、drive。initial轴恰为float64[1]的[0.0]；output轴含2..65帧，从0严格递增至end_time。输出含真实初态。drive轴含2..129帧，从0严格递增至end_time；所有drive场在相邻样本间分量线性插值，不允许外推。 initial轴上的材料或源表示全过程固定量，不是额外初态。内部时间步、稳定性限制及每步迭代策略由考生决定，输出时刻不是积分步长。

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。

fields恰含条件实际引用的字段；data键引用{"field":"逻辑字段名"}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{"value":有限标量,"unit":"单位"}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；initial场time=constant，drive场time=linear。space=uniform，仅表示对象自身属性，不作对象间空间重建。 输入value_kind：所有位置为point。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

### `particles`

role=`material`、variable=`particle`、operator=`particles`、location=`particles`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `mass` | kind=`scalar`、component_shape=`[1]`，`kg`；静质量m，严格正 | initial |
| `charge` | kind=`scalar`、component_shape=`[1]`，`C`；有符号电荷q，非零 | initial |

### `launch`

role=`initial`、variable=`particle_state`、operator=`launch`、location=`particles`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `position` | kind=`vector`、component_shape=`[3]`，`m`；t=0位置x | initial |
| `velocity` | kind=`vector`、component_shape=`[3]`，`m/s`；t=0速度v | initial |

### `electric`

role=`source`、variable=`electric_field`、operator=`electric`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `offset` | kind=`vector`、component_shape=`[3]`，`V/m`；外场E0(t) | drive |
| `gradient` | kind=`tensor`、component_shape=`[3,3]`，`V/m2`；对称矩阵G(t)，E=E0+G(x−r0) | drive |
| `origin` | kind=`vector`、component_shape=`[3]`，`m`；固定参考点r0 | initial |

### `magnetic`

role=`source`、variable=`magnetic_field`、operator=`magnetic`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`vector`、component_shape=`[3]`，`T`；空间均匀且时间恒定的B0 | initial |

## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为所有位置为point，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
| `position` | kind=`vector`、component_shape=`[3]`，`m`；全局位置x(t) | `particles` |
| `velocity` | kind=`vector`、component_shape=`[3]`，`m/s`；速度v(t) | `particles` |

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

G各采样帧须严格对称。end_time严格正；数据保证全部所需轨道存在且有限。正式数据还须保证全过程|v|≤0.01c，c=299792458 m/s。 记τ=end_time、a=max粒子|q|/m，B=|B0|，G*=max帧||G||F。须τ a B≤200、τ sqrt(a G*)≤100；||·||F为Frobenius范数。 所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
