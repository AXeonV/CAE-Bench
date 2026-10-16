# space-charge-beam 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-space-charge-beam-v1`；task可省略，出现须为`space-charge-beam`。spatial_dimension=1；不混用profile、contract_version、analysis或materials。

## 物理语义

负电束沿+x注入一维区间，单能、稳态、无碰撞、无背景和反射。v(x)=sqrt(2[W0−q(φ(x)−VL)]/m)>0，n(x)=Γ/v(x)，−εφ″=q n，E=−φ′。边界φ(xL)=VL、φ(xR)=VR；电势采用绝对给定基准。入射和出射均不反射粒子，未引入中和背景。只接收单调加速分支φ′>0，不允许虚阴极／多流；每个输出为相应空间单元的长度平均，密度平均不是Γ除以平均速度。

## 全局参数

parameters恰含下表，标量均为{"value":数值,"unit":单位}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
| `mass` | `kg` | 束粒子质量m>0 |
| `charge` | `C` | 负束粒子电荷q<0 |
| `permittivity` | `F/m` | 绝对介电常数ε>0 |
| `injection_energy` | `J` | 每粒子注入动能W0>0 |
| `particle_flux` | `1/(m2.s)` | 沿+x恒定数通量Γ>0 |

## 位置、几何与身份

meshes恰含main，geometries为空。main是沿全局x轴的连通区间[xL,xR]，2..512个非退化一阶线单元（Gmsh type1），所有节点y=z=0，只有这些线单元，无未用节点、间隙、分叉、重复或重叠。domain和cells分别恰含全部节点和全部线单元。编号按tag递增，单元在x方向的次序须由坐标和连接关系确定，不按tag猜测。left、right分别恰含最左和最右节点，条件作用于该端点。 locations恰含下表；网格IDs为正且严格递增。

| location | 支持范围与含义 |
|---|---|
| `domain` | mesh，1..513个；全部区间网格节点 |
| `cells` | mesh，1..512个；全部一阶区间单元 |
| `left` | mesh，1..1个；唯一最左端点 |
| `right` | mesh，1..1个；唯一最右端点 |

## 时间与数组

time_axes恰含initial、output。initial和output两轴均恰为float64[1]的[0.0]，0仅为稳态存储标记。 initial轴上的材料或源表示全过程固定量，不是额外初态。

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。

fields恰含条件实际引用的字段；data键引用{"field":"逻辑字段名"}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{"value":有限标量,"unit":"单位"}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；initial场time=constant。space：domain节点为piecewise_linear（网格P1重建），cells为piecewise_constant（逐单元常值），端点为uniform。 输入value_kind：cells为average，其他位置为point。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

### `left_potential`

role=`boundary`、variable=`potential`、operator=`left_potential`、location=`left`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`scalar`、component_shape=`[1]`，`V`；左电极电势VL | initial |

### `right_potential`

role=`boundary`、variable=`potential`、operator=`right_potential`、location=`right`；恰一条覆盖完整该位置，data恰含以下键：

| data键 | 类型、单位与含义 | 场时间轴 |
|---|---|---|
| `value` | kind=`scalar`、component_shape=`[1]`，`V`；右电极电势VR>VL | initial |

## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为cells为average，其他位置为point，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
| `potential` | kind=`scalar`、component_shape=`[1]`，`V`；绝对电势φ的单元平均 | `cells` |
| `electric_field` | kind=`scalar`、component_shape=`[1]`，`V/m`；Ex的单元平均 | `cells` |
| `number_density` | kind=`scalar`、component_shape=`[1]`，`1/m3`；n的单元平均 | `cells` |
| `velocity` | kind=`scalar`、component_shape=`[1]`，`m/s`；正向速度v的单元平均 | `cells` |

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

令e=−q、ΔV=VR−VL、vin=sqrt(2W0/m)、L=xR−xL；须0<eΔV≤W0且eΓL²/(ε vin ΔV)≤0.25，以限定温和空间电荷单调分支。接收域内非相对论全过程速度≤0.01c，c=299792458 m/s；正式数据仍须独立确认解和资源。  所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
