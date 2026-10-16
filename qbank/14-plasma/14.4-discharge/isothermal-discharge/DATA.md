# isothermal-discharge 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-isothermal-discharge-v1`；task可省略，出现须为`isothermal-discharge`。spatial_dimension=1；不混用profile、contract_version、analysis或materials。

## 物理语义

固定中性库中只含电子和单正离子。E=−∂xφ，−ε∂xxφ=e(ni−ne)。Γe=−μe ne E−De∂xne，Γi=+μi ni E−Di∂xni，∂tne+∂xΓe=R，∂tni+∂xΓi=R，R=ki N ne−kr ne ni。左右端同时给定φ、ne、ni的库值；无默认绝缘、鞘层或二次发射。初态给ne、ni，电势每时刻由Poisson与电极值确定，不作为迭代初猜输入。各单元输运系数常数；t>0的解在内部界面各密度连续、各物种数通量连续，φ和ε∂xφ连续；初态按给定P1函数取弱初态，不额外要求其初始通量连续。输入初态为网格节点P1连续重建，系数为逐单元常值。输出均为真实单元长度平均。

## 全局参数

parameters恰含下表，标量均为{"value":数值,"unit":单位}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `end_time` | `s` | 物理终时τ，0<τ≤1000000 |
| `elementary_charge` | `C` | 正电荷量e>0 |
| `permittivity` | `F/m` | 均匀绝对介电常数ε>0 |
| `neutral_density` | `1/m3` | 固定中性库N>0 |

## 位置、几何与身份

meshes恰含main，geometries为空。main是沿全局x轴的连通区间[xL,xR]，2..256个非退化一阶线单元（Gmsh type1），所有节点y=z=0，只有这些线单元，无未用节点、间隙、分叉、重复或重叠。domain和cells分别恰含全部节点和全部线单元。编号按tag递增，单元在x方向的次序须由坐标和连接关系确定，不按tag猜测。left、right分别恰含最左和最右节点，条件作用于该端点。 locations恰含下表；网格IDs为正且严格递增。

| location | 支持范围与含义 |
|---|---|
| `domain` | mesh，1..257个；全部一阶区间网格节点 |
| `cells` | mesh，1..256个；全部区间单元 |
| `left` | mesh，1..1个；最左端点 |
| `right` | mesh，1..1个；最右端点 |

## 时间与数组

time_axes恰含initial、output、drive。initial轴恰为float64[1]的[0.0]；output轴含2..65帧，从0严格递增至end_time。输出含真实初态。drive轴含2..129帧，从0严格递增至end_time；所有drive场在相邻样本间分量线性插值，不允许外推。 initial轴上的材料或源表示全过程固定量，不是额外初态。内部时间步、稳定性限制及每步迭代策略由考生决定，输出时刻不是积分步长。

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。

fields恰含条件实际引用的字段；data键引用{"field":"逻辑字段名"}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{"value":有限标量,"unit":"单位"}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；initial场time=constant，drive场time=linear。space：domain节点为piecewise_linear（网格P1重建），cells为piecewise_constant（逐单元常值），端点为uniform。 输入value_kind：cells为average，其他位置为point。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

### `transport`

role=`material`、variable=`plasma_transport`、operator=`transport`、location=`cells`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `electron_mobility` | kind=`scalar`、component_shape=`[1]`，`m2/(V.s)`；取正数的电子迁移率μe>0，电荷负号另计 | initial |
| `ion_mobility` | kind=`scalar`、component_shape=`[1]`，`m2/(V.s)`；正离子迁移率μi>0 | initial |
| `electron_diffusion` | kind=`scalar`、component_shape=`[1]`，`m2/s`；De>0 | initial |
| `ion_diffusion` | kind=`scalar`、component_shape=`[1]`，`m2/s`；Di>0 | initial |
| `recombination` | kind=`scalar`、component_shape=`[1]`，`m3/s`；复合系数kr≥0 | initial |
| `ionization` | kind=`scalar`、component_shape=`[1]`，`m3/s`；固定ki≥0，不由局部场隐含推断 | initial |

### `initial`

role=`initial`、variable=`plasma_state`、operator=`initial`、location=`domain`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `electron_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；ne(t=0)>0 | initial |
| `ion_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；ni(t=0)>0 | initial |

### `left_reservoir`

role=`boundary`、variable=`reservoir`、operator=`left_reservoir`、location=`left`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `potential` | kind=`scalar`、component_shape=`[1]`，`V`；电极电势V(t) | drive |
| `electron_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；电子库Dirichlet密度>0 | drive |
| `ion_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；离子库Dirichlet密度>0 | drive |

### `right_reservoir`

role=`boundary`、variable=`reservoir`、operator=`right_reservoir`、location=`right`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `potential` | kind=`scalar`、component_shape=`[1]`，`V`；电极电势V(t) | drive |
| `electron_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；电子库Dirichlet密度>0 | drive |
| `ion_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；离子库Dirichlet密度>0 | drive |

## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为cells为average，其他位置为point，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
| `electron_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；ne的单元平均 | `cells` |
| `ion_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；ni的单元平均 | `cells` |
| `potential` | kind=`scalar`、component_shape=`[1]`，`V`；φ的单元平均 | `cells` |
| `electric_field` | kind=`scalar`、component_shape=`[1]`，`V/m`；Ex的单元平均 | `cells` |

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

初态和边界密度严格正，初态端点与t=0库值严格一致；数据保证直到τ密度保持正、max(ne,ni)≤0.01N及弱电离漂移扩散适用，解与观测有限。不强制爱因斯坦关系；这是明确给定有效输运系数的有限物理模型。 记hmin为最短网格区间，D*为所有扩散系数最大值，μ*为所有迁移率最大值；须τ D*/hmin²≤100000、τ μ* e(0.01N)/ε≤10000。此范围不指定显式或隐式算法。 所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
