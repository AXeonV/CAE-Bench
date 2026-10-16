# 11.4.1 数据契约

本文件与instruction.md及通用CONTRACT.md构成完整要求；无额外领域文档依赖。以下为格式定义，未提供可运行算例或参考答案。

`spatial_dimension=1`；physics.model固定`semiconductor-minority-diffusion-v1`；task若给必须为`semiconductor-minority-diffusion`。仅使用physics及其parameters，不混用profile、analysis、materials、contract_version。meshes和geometries均为空对象，长度为m、时间为s。

physics.parameters恰含下表键，每项恰为`{"value":数值,"unit":"表中单位"}`，无默认、无自动换算；布尔值不能作为数值。

| 键 | unit | 范围与含义 |
|---|---|---|
| length | `m` | ≥1e-09，≤0.01；区间长度L，0<x<L |
| diffusivity | `m2/s` | ≥1e-10，≤1；少数电子扩散系数D |
| lifetime | `s` | ≥1e-12，≤1；线性复合寿命τ |
| majority_density | `1/m3` | ≥1000000000000.0，≤1e+25；固定均匀多数空穴密度p0，仅界定低注入 |

locations恰含下表位置；IDs为非负、严格递增int64，不能按ID数值推断坐标。points.coordinates为float64[N,1]真实x坐标。

| location | 类型及数量 | 对象 |
|---|---|---|
| profile | points，2..1024 | 包含x=0及x=L的剖面结点，按ID行序x严格递增；输入重建支撑，不是指定求解网格 |
| receivers | points，1..256 | 严格位于0<x<L的输出点；ID行序不要求坐标递增，允许重复坐标 |
| contacts | points，2..2 | 第一行x=0，第二行x=L的真实边界点 |

time_axes恰含`drive`, `initial`, `observe`, `static`。static及initial各恰[0.0]，标记/物理初态分工不同，允许共用数组key。observe含1..256个严格递增时刻，末时刻0<tend≤1 s；drive含2..512个严格递增时刻，首项0、末项恰等于tend。observe位于[0,tend]内，不要求与drive重合。所有drive场在相邻时刻逐值线性插值、禁止区间外推；内部步长自行选择，不由任一时间数组指定。observe首项必须>0；不请求t=0初始剖面折点处可能未定义的导数通量/电流。

fields的逻辑名和array key由清单给出，不必相同；每个下表quantity恰一个输入场，不能有其他输入场。每场dtype=float64、value_kind=point。所有场kind=scalar、component_shape=[1]、components=["value"]；数组形状[T,N,1]，不省略长度为1的轴。所有输入均以field呈现，不接受常量替代、option或隐式广播。

| 输入quantity | location | time_axis | unit | 范围与定义 |
|---|---|---|---|---|
| surface_velocity | contacts | static | `m/s` | ≥0，≤10000000.0；两端表面复合速度S，时间恒定；0表示绝热粒子边界 |
| initial_excess | profile | initial | `1/m3` | ≥0，≤1e+23；初始超额少数电子u0≥0 |
| generation | profile | drive | `1/(m3.s)` | ≥0，≤1e+35；超额电子产生G≥0 |

每个输入场显式sampling：profile位置space=piecewise_linear，其他位置space=uniform；drive轴time=linear，其他轴time=constant；extrapolation=forbid。profile按真实x在相邻结点间线性重建，定义整个闭区间，不延拓到区间外；其他位置为各独立对象/边界自身的值，uniform不表示不同对象数值相等或可在对象之间插值。时间及空间线性重建可分离进行。静态场各自单帧，在整个分析区间保持不变，不将static标记误作有效驱动区间长度。

conditions恰有每个输入quantity一条：variable等于该quantity；location同表；operator固定`prescribed`；data恰含value且为`{"field":"该场逻辑名"}`。role：initial轴为initial；contacts位置非initial为boundary；其他为source。顺序任意，各记录只引用对应场，不允许重复或未使用场。

物理重建、闭合和边界：

一维均匀p型材料、固定多数空穴背景p0，忽略电场及空间电荷反馈。求超额少数电子u≥0，∂tu=D∂xxu−u/τ+G；这里u不是总电子密度，不另加本征平衡浓度。粒子通量Γ=−D∂xu。两端表面复合满足外向粒子流Γ·ν=S u；左ν=−1、右ν=+1，因而D u′(0)=SL u(0)，−D u′(L)=SR u(L)。无外部注入边界。t=0剖面为物理初态；允许与Robin边界导数不相容，取抛物型初边值问题t>0解，本题只请求严格正输出时刻。低注入要求全时空u≤0.01 p0；合法输入须max(u0)≤0.01p0且τ max(G)≤0.01p0，该充分界限与非负Robin条件共同约束范围。

outputs逻辑名与array key任意且各自唯一；下表quantity每种至少一次，允许同一quantity多个独立命名的输出，均使用表中固定location/time_axis/分量；禁止其他quantity。不写输出sampling。所有输出float64、value_kind=point。

| quantity | location | time_axis | unit | 分量与含义 |
|---|---|---|---|---|
| excess_density | receivers | observe | `1/m3` | scalar [1]；超额少数电子u |
| particle_flux | receivers | observe | `1/(m2.s)` | scalar [1]；向+x粒子通量Γ=−D∂xu，不是常规电流 |

结果dataset形状[T,N,*component_shape]，只写各outputs.array及所引用的IDs、时间数组；不写坐标、输入场、额外诊断或元数据。输出点值为上述连续模型在给定坐标/时刻的值，不是内部单元均值；重复坐标保持不同ID行。输入场总标量数与全部请求输出标量数分别≤2000000，全部值有限，禁止默默截断。输入/输出HDF5的扁平、dtype与精确复制规则依CONTRACT。
