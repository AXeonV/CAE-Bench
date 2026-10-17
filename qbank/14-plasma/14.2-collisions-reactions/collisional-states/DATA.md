# collisional-states 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-collisional-states-v1`；task可省略，出现须为`collisional-states`。spatial_dimension=3；不混用profile、contract_version、analysis或materials。

## 物理语义

均匀带电粒子与无限中性热浴发生给定离散态碰撞，不跟踪随机单粒子样本。dn_i/dt=Σ_{j≠i}(K_ji n_j−K_ij n_i)。态速度和粒子质量、电荷恒定；碰撞可以向热浴交换动量和能量，不强制细致平衡。系综电流J=qΣ_i n_i v_i，动能密度W=(m/2)Σ_i n_i|v_i|²。无空间输运或外场加速。

## 全局参数

parameters恰含下表，标量均为{"value":数值,"unit":单位}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `end_time` | `s` | 物理终时τ，0<τ≤1000000 |
| `state_count` | `1` | 速度态数S，JSON整数2..16 |

## 位置、几何与身份

meshes及geometries均为空，系统不提供空间网格。entities是真实粒子、物种、状态或层对象，不是伪造空间探针。 locations恰含下表；entities的IDs非负严格递增，system恰一对象；ID数值不携带物理含义。对象之间无默认邻接或插值。

| location | 支持范围与含义 |
|---|---|
| `states` | entities，2..16个；S个固定离散速度态，IDs为0..S−1 |
| `system` | entities，1..1个；唯一碰撞系综 |

## 时间与数组

time_axes恰含initial、output、drive。initial轴恰为float64[1]的[0.0]；output轴含2..65帧，从0严格递增至end_time。输出含真实初态。drive轴含2..129帧，从0严格递增至end_time；所有drive场在相邻样本间分量线性插值，不允许外推。 initial轴上的材料或源表示全过程固定量，不是额外初态。内部时间步、稳定性限制及每步迭代策略由考生决定，输出时刻不是积分步长。

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。转移矩阵shape=[S,S]，按[i,j]最后轴优先展开，components依次为from_0_to_0、from_0_to_1、…、from_(S−1)_to_(S−1)。

fields恰含条件实际引用的字段；data键引用{"field":"逻辑字段名"}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{"value":有限标量,"unit":"单位"}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；initial场time=constant，drive场time=linear。space=uniform，仅表示对象自身属性，不作对象间空间重建。 输入value_kind：所有位置为point。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

### `states`

role=`material`、variable=`velocity_state`、operator=`states`、location=`states`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `velocity` | kind=`vector`、component_shape=`[3]`，`m/s`；各速度态v_i | initial |

### `particles`

role=`material`、variable=`particle`、operator=`particles`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `mass` | kind=`scalar`、component_shape=`[1]`，`kg`；各态共同质量m>0 | initial |
| `charge` | kind=`scalar`、component_shape=`[1]`，`C`；各态共同非零电荷q | initial |

### `transitions`

role=`material`、variable=`transition_rate`、operator=`transitions`、location=`system`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`components`、component_shape=`[S,S]`，`1/s`；K_ij(t)：从态i转入态j的单位时间率；Kii=0，非对角非负 | drive |

### `population`

role=`initial`、variable=`state_density`、operator=`population`、location=`states`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`scalar`、component_shape=`[1]`，`1/m3`；各态初始数密度n_i≥0，总数密度>0 | initial |

## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为所有位置为point，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
| `state_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；各态数密度n_i | `states` |
| `current_density` | kind=`vector`、component_shape=`[3]`，`A/m2`；系综电流J | `system` |
| `kinetic_energy_density` | kind=`scalar`、component_shape=`[1]`，`J/m3`；系综动能密度W | `system` |

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

states数必须等于S。每帧K对角线严格零，非对角非负；初始人口总和严格正。 须τ max帧max_i Σ_j Kij≤10000，限制单位时段碰撞尺度。 所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
