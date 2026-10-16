# vlasov-poisson 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-vlasov-poisson-v1`；task可省略，出现须为`vlasov-poisson`。spatial_dimension=1；不混用profile、contract_version、analysis或materials。

## 物理语义

空间区间[xL,xR]周期，L=xR−xL；一移动负电物种与静止均匀正背景。∂t f+v∂x f+(q/m)E∂v f=0，n=∫f dv，−ε∂xxφ=q(n−n0)，E=−∂xφ。背景n0定义为初态总粒子数除以L，即n0=(1/L)∫∫f0 dv dx，全程固定，不是独立输入参数。φ、E和f的空间周期迹相等，且∫φ dx=0固定电势规范，∫E dx=0；不逐帧减去电荷背景。速度区间[vmin,vmax]被Nv个等宽箱划分，f0按每个空间单元×速度箱上的给定常值重建；区间外f=0。速度端点使用零入流；数据保证直到τ分布支撑都与速度端点保持正距离，故没有截断损失。观测distribution为每个相空间箱的双重平均，number_density、potential、electric_field为每个空间单元的长度平均。

## 全局参数

parameters恰含下表，标量均为{"value":数值,"unit":单位}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `end_time` | `s` | 物理终时τ，0<τ≤1000000 |
| `velocity_count` | `1` | 等宽速度箱数Nv，JSON整数8..128 |
| `velocity_min` | `m/s` | 速度区间左端vmin<0 |
| `velocity_max` | `m/s` | 速度区间右端vmax>0 |
| `mass` | `kg` | 移动物种质量m>0 |
| `charge` | `C` | 移动物种电荷q<0 |
| `permittivity` | `F/m` | 均匀绝对介电常数ε>0 |

## 位置、几何与身份

meshes恰含main，geometries为空。main是沿全局x轴的连通区间[xL,xR]，2..256个非退化一阶线单元（Gmsh type1），所有节点y=z=0，只有这些线单元，无未用节点、间隙、分叉、重复或重叠。domain和cells分别恰含全部节点和全部线单元。编号按tag递增，单元在x方向的次序须由坐标和连接关系确定，不按tag猜测。两端按周期迹关联，不合并其不同节点身份。 locations恰含下表；网格IDs为正且严格递增。

| location | 支持范围与含义 |
|---|---|
| `domain` | mesh，1..257个；全部区间网格节点 |
| `cells` | mesh，1..256个；全部一阶区间单元 |

## 时间与数组

time_axes恰含initial、output。initial轴恰为float64[1]的[0.0]；output轴含2..65帧，从0严格递增至end_time。输出含真实初态。 initial轴上的材料或源表示全过程固定量，不是额外初态。内部时间步、稳定性限制及每步迭代策略由考生决定，输出时刻不是积分步长。

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。distribution的component_shape=[Nv]，components依次v0、v1、…、v(Nv−1)，第j箱为[vmin+jΔv,vmin+(j+1)Δv]；端点对积分无影响。

fields恰含条件实际引用的字段；data键引用{"field":"逻辑字段名"}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{"value":有限标量,"unit":"单位"}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；initial场time=constant。space：domain节点为piecewise_linear（网格P1重建），cells为piecewise_constant（逐单元常值），端点为uniform。 输入value_kind：cells为average，其他位置为point。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

### `initial`

role=`initial`、variable=`distribution`、operator=`initial`、location=`cells`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`components`、component_shape=`[Nv]`，`s/m4`；每个空间单元、每个速度箱上的f0平均；按v递增排列；≥0 | initial |

## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为cells为average，其他位置为point，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
| `distribution` | kind=`components`、component_shape=`[Nv]`，`s/m4`；f在空间单元×速度箱上的平均 | `cells` |
| `number_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；n的空间单元平均 | `cells` |
| `potential` | kind=`scalar`、component_shape=`[1]`，`V`；零空间均值φ的单元平均 | `cells` |
| `electric_field` | kind=`scalar`、component_shape=`[1]`，`V/m`；Ex的单元平均 | `cells` |

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

区间网格至少2单元，Nv≥8；vmin严格负、vmax严格正，q严格负。初始f非负且总积分>0；按初态积分定义背景，保证周期Poisson相容。相空间箱只是输入重建及输出观测，不指定内部离散。正式数据须验证速度支撑、正则弱解和预算。 令L=xR−xL、ωp=sqrt(q²n0/(mε))；须τ ωp≤200、τ max(|vmin|,vmax)/L≤1000。 所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
