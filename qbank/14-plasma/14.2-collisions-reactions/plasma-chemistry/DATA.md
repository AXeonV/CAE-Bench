# plasma-chemistry 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-plasma-chemistry-v1`；task可省略，出现须为`plasma-chemistry`。spatial_dimension=1；不混用profile、contract_version、analysis或materials。

## 物理语义

中性气体库N保持恒定，电子平均能量由外部维持，全部反应系数直接给定，不另解温度或电场。反应为e+g→2e+i、e+g→a、e+i→g、a+i→2g。定义Ii=ki N ne，Ia=ka N ne，R=kr ne ni，A=kn na ni；dne/dt=Ii−Ia−R，dni/dt=Ii−R−A，dna/dt=Ia−A。输出净电荷密度ρ=e(ni−ne−na)，不强制初始电中性，也不从ρ反推外电场。

## 全局参数

parameters恰含下表，标量均为{"value":数值,"unit":单位}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `end_time` | `s` | 物理终时τ，0<τ≤1000000 |
| `neutral_density` | `1/m3` | 固定中性库数密度N>0 |
| `elementary_charge` | `C` | 正的基本电荷量e>0 |

## 位置、几何与身份

meshes及geometries均为空，系统不提供空间网格。entities是真实粒子、物种、状态或层对象，不是伪造空间探针。 locations恰含下表；entities的IDs非负严格递增，system恰一对象；ID数值不携带物理含义。对象之间无默认邻接或插值。

| location | 支持范围与含义 |
|---|---|
| `system` | entities，1..1个；唯一均匀反应体积的局部密度状态 |

## 时间与数组

time_axes恰含initial、output、drive。initial轴恰为float64[1]的[0.0]；output轴含2..65帧，从0严格递增至end_time。输出含真实初态。drive轴含2..129帧，从0严格递增至end_time；所有drive场在相邻样本间分量线性插值，不允许外推。 initial轴上的材料或源表示全过程固定量，不是额外初态。内部时间步、稳定性限制及每步迭代策略由考生决定，输出时刻不是积分步长。

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。`initial.value`的components固定为`["electron", "positive_ion", "negative_ion"]`。 `number_density`的components固定为`["electron", "positive_ion", "negative_ion"]`。

fields恰含条件实际引用的字段；data键引用{"field":"逻辑字段名"}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{"value":有限标量,"unit":"单位"}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；initial场time=constant，drive场time=linear。space=uniform，仅表示对象自身属性，不作对象间空间重建。 输入value_kind：所有位置为point。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

### `initial`

role=`initial`、variable=`number_density`、operator=`initial`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`components`、component_shape=`[3]`，`1/m3`；ne、ni、na，依次电子、单正离子、单负离子；≥0 | initial |

### `rates`

role=`material`、variable=`reaction_rates`、operator=`rates`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `ionization` | kind=`scalar`、component_shape=`[1]`，`m3/s`；电子碰撞电离系数ki(t)≥0 | drive |
| `attachment` | kind=`scalar`、component_shape=`[1]`，`m3/s`；电子附着系数ka(t)≥0 | drive |
| `recombination` | kind=`scalar`、component_shape=`[1]`，`m3/s`；电子—正离子复合系数kr(t)≥0 | drive |
| `neutralization` | kind=`scalar`、component_shape=`[1]`，`m3/s`；负离子—正离子中和系数kn(t)≥0 | drive |

## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为所有位置为point，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
| `number_density` | kind=`components`、component_shape=`[3]`，`1/m3`；依次ne、ni、na | `system` |
| `charge_density` | kind=`scalar`、component_shape=`[1]`，`C/m3`；净自由电荷ρ | `system` |

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

初态非负，至少一种带电物种非零；数据保证全部请求时刻前max(ne,ni,na)≤0.01N且解有限。 须τ N max帧(ki+ka)≤100，τ (0.01N) max帧(kr+kn)≤10000；相同drive轴逐帧求和。 所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
