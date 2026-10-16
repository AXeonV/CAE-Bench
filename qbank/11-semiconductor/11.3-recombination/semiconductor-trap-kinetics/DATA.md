# 11.3.2 数据契约

本文件与instruction.md及通用CONTRACT.md构成完整要求；无额外领域文档依赖。以下为格式定义，未提供可运行算例或参考答案。

`spatial_dimension=1`；physics.model固定`semiconductor-trap-kinetics-v1`；task若给必须为`semiconductor-trap-kinetics`。仅使用physics及其parameters，不混用profile、analysis、materials、contract_version。meshes和geometries均为空对象，长度为m、时间为s，有限维实体不引入空间方程。

physics.parameters恰含下表键，每项恰为`{"value":数值,"unit":"表中单位"}`，无默认、无自动换算；布尔值不能作为数值。

| 键 | unit | 范围与含义 |
|---|---|---|
| trap_density | `1/m3` | ≥100000000.0，≤1e+25；每体积陷阱数Nt |
| capture_n | `m3/s` | ≥1e-22，≤1e-10；电子俘获系数cn |
| capture_p | `m3/s` | ≥1e-22，≤1e-10；空穴俘获系数cp |
| n1 | `1/m3` | ≥1000000.0，≤1e+25；电子发射平衡密度n1 |
| p1 | `1/m3` | ≥1000000.0，≤1e+25；空穴发射平衡密度p1；ni²=n1 p1，不另输入ni |

locations恰含下表位置；IDs为非负、严格递增int64，不能按ID数值推断坐标。entities只有kind和ids，不带伪坐标。

| location | 类型及数量 | 对象 |
|---|---|---|
| bodies | entities，1..128 | 彼此独立的均匀体；无空间输运，不用ID推导位置或体积 |

time_axes恰含`drive`, `initial`, `observe`, `static`。static及initial各恰[0.0]，标记/物理初态分工不同，允许共用数组key。observe含1..256个严格递增时刻，末时刻0<tend≤1 s；drive含2..512个严格递增时刻，首项0、末项恰等于tend。observe位于[0,tend]内，不要求与drive重合。所有drive场在相邻时刻逐值线性插值、禁止区间外推；内部步长自行选择，不由任一时间数组指定。

fields的逻辑名和array key由清单给出，不必相同；每个下表quantity恰一个输入场，不能有其他输入场。每场dtype=float64、value_kind=point。所有场kind=scalar、component_shape=[1]、components=["value"]；数组形状[T,N,1]，不省略长度为1的轴。所有输入均以field呈现，不接受常量替代、option或隐式广播。

| 输入quantity | location | time_axis | unit | 范围与定义 |
|---|---|---|---|---|
| initial_occupation | bodies | initial | `1` | ≥0，≤1；陷阱初始电子占据概率f0 |
| initial_electron | bodies | initial | `1/m3` | ≥1000000.0，≤1e+25；初始载流子密度 |
| initial_hole | bodies | initial | `1/m3` | ≥1000000.0，≤1e+25；初始载流子密度 |
| generation | bodies | drive | `1/(m3.s)` | ≥0，≤1e+35；成对产生G(t)≥0 |

每个输入场显式sampling：space=uniform；drive轴time=linear，其他轴time=constant；extrapolation=forbid。各位置为独立对象自身的值，uniform不表示不同对象数值相等或可在对象之间插值。静态场各自单帧，在整个分析区间保持不变，不将static标记误作有效驱动区间长度。

conditions恰有每个输入quantity一条：variable等于该quantity；location同表；operator固定`prescribed`；data恰含value且为`{"field":"该场逻辑名"}`。role：initial轴为initial；其他为source。顺序任意，各记录只引用对应场，不允许重复或未使用场。

物理重建、闭合和边界：

每个独立均匀体中陷阱电子占据概率f，电子俘获/发射净率An=cn[n(1−f)−n1 f]，空穴俘获/发射净率Ap=cp[p f−p1(1−f)]，单位s^−1。dn/dt=G−Nt An，dp/dt=G−Nt Ap，df/dt=An−Ap。en=cn n1、ep=cp p1；陷阱中带电子参与电荷账目，n−p+Nt f守恒。f是单个陷阱的电子占据概率，不是空穴占据或密度。无空间场、接触、辐射、Auger或额外准稳态SRH项，不能把df/dt设为0。

outputs逻辑名与array key任意且各自唯一；下表quantity每种至少一次，允许同一quantity多个独立命名的输出，均使用表中固定location/time_axis/分量；禁止其他quantity。不写输出sampling。所有输出float64、value_kind=point。

| quantity | location | time_axis | unit | 分量与含义 |
|---|---|---|---|---|
| occupation | bodies | observe | `1` | scalar [1]；电子占据陷阱的概率f(t) |
| electron_density | bodies | observe | `1/m3` | scalar [1]；相应体内瞬时密度 |
| hole_density | bodies | observe | `1/m3` | scalar [1]；相应体内瞬时密度 |

结果dataset形状[T,N,*component_shape]，只写各outputs.array及所引用的IDs、时间数组；不写坐标、输入场、额外诊断或元数据。输出为各独立实体在指定时刻的状态/属性，按ID行序存储，不作对象间平均。输入场总标量数与全部请求输出标量数分别≤2000000，全部值有限，禁止默默截断。输入/输出HDF5的扁平、dtype与精确复制规则依CONTRACT。
