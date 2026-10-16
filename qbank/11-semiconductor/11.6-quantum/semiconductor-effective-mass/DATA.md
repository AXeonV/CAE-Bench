# 11.6.1 数据契约

本文件与instruction.md及通用CONTRACT.md构成完整要求；无额外领域文档依赖。以下为格式定义，未提供可运行算例或参考答案。

`spatial_dimension=1`；physics.model固定`semiconductor-effective-mass-v1`；task若给必须为`semiconductor-effective-mass`。仅使用physics及其parameters，不混用profile、analysis、materials、contract_version。meshes和geometries均为空对象，长度为m、时间为s；layers/modes是离散层与模态标识，物理模型仍是一维空间本征问题。

physics.parameters恰含下表键，每项恰为`{"value":数值,"unit":"表中单位"}`，无默认、无自动换算；布尔值不能作为数值。

| 键 | unit | 范围与含义 |
|---|---|---|
| mode_count | `1` | JSON整数，≥1，≤8；请求前m个态，JSON整数 |

locations恰含下表位置；IDs为非负、严格递增int64，不能按ID数值推断坐标。points.coordinates为float64[N,1]真实x坐标；entities只有kind和ids，不带伪坐标。

| location | 类型及数量 | 对象 |
|---|---|---|
| layers | entities，1..64 | 沿+x依次拼接的层，第一层左端x=0 |
| modes | entities，1..8 | IDs必须恰0..m−1，对应能量从小到大 |
| receivers | points，1..256 | 严格位于0<x<H的真实点，可恰在材料界面 |

time_axes恰含`static`。static恰[0.0]，仅作稳态/静态标记。

fields的逻辑名和array key由清单给出，不必相同；每个下表quantity恰一个输入场，不能有其他输入场。每场dtype=float64、value_kind=point。除wavefunction输出外所有场kind=scalar、component_shape=[1]、components=["value"]；数组形状[T,N,1]，不省略长度为1的轴。所有输入均以field呈现，不接受常量替代、option或隐式广播。

| 输入quantity | location | time_axis | unit | 范围与定义 |
|---|---|---|---|---|
| thickness | layers | static | `m` | ≥1e-10，≤1e-06；各层厚度h |
| mass | layers | static | `kg` | ≥1e-33，≤1e-29；各层纵向有效质量的绝对值，不是相对自由电子质量 |
| band_edge | layers | static | `J` | ≥-1e-17，≤1e-17；各层常导带边U，相对公共零点 |

每个输入场显式sampling：space=uniform；time=constant；extrapolation=forbid。各位置为独立对象自身的值，uniform不表示不同对象数值相等或可在对象之间插值。静态场各自单帧，在整个分析区间保持不变。

conditions恰有每个输入quantity一条：variable等于该quantity；location同表；operator固定`prescribed`；data恰含value且为`{"field":"该场逻辑名"}`。role：thickness/mass/band_edge为material；其他为source。顺序任意，各记录只引用对应场，不允许重复或未使用场。

物理重建、闭合和边界：

单带一维有效质量模型，在[0,H]有限箱体求Hψ=Eψ，H算符为−(ℏ²/2)∂x[(1/m(x))∂x]+U(x)，ℏ=6.62607015e−34/(2π) J.s。m和U逐层常数，界面ψ及(1/m)ψ′连续，端点ψ(0)=ψ(H)=0；不得换为ψ′连续、周期边界或无限包层衰减。按能量严格升序取前m个简单本征态，无额外自旋简并计数。每态实且∫0^H ψ²dx=1，以ψ′(0)>0固定正负号；不能逐采样点翻号。输出界面处ψ为共同连续值；不请求界面导数。能量相对输入U共同零点，不做每例自动减基态处理。

H=各层thickness之和，layers按ID行序累加位置，接收点可乱序；modes数量恰mode_count且IDs=0..m−1。不将层宽当内部离散。谱条件性作为合法问题族的数据承诺：令Es=max(max(U)−min(U),ℏ²/(2 min(m)H²),1e−24 J)，前m个态与其相邻态（包括第m+1态）的能量间距均≥1e−6 Es，排除数值上不可分辨的近简并双阱。该条件需正式数据的独立谱与收敛证据验证，声明校验器不求谱；还须验证归一化波函数、定相和逐值精度在预算内可达。

outputs逻辑名与array key任意且各自唯一；下表quantity每种至少一次，允许同一quantity多个独立命名的输出，均使用表中固定location/time_axis/分量；禁止其他quantity。不写输出sampling。所有输出float64、value_kind=point。

| quantity | location | time_axis | unit | 分量与含义 |
|---|---|---|---|---|
| eigenenergy | modes | static | `J` | scalar [1]；按升序排列的m个本征能量 |
| wavefunction | receivers | static | `m^(-1/2)` | components [m]，m=mode_count，标签c1..cm；按modes行序的m个归一化实波函数 |

结果dataset形状[T,N,*component_shape]，只写各outputs.array及所引用的IDs、时间数组；不写坐标、输入场、额外诊断或元数据。输出点值为上述连续模型在给定坐标/时刻的值，不是内部单元均值；重复坐标保持不同ID行。输入场总标量数与全部请求输出标量数分别≤2000000，全部值有限，禁止默默截断。输入/输出HDF5的扁平、dtype与精确复制规则依CONTRACT。
