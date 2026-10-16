# 11.2.1 数据契约

本文件与instruction.md及通用CONTRACT.md构成完整要求；无额外领域文档依赖。以下为格式定义，未提供可运行算例或参考答案。

`spatial_dimension=1`；physics.model固定`semiconductor-drift-steady-v1`；task若给必须为`semiconductor-drift-steady`。仅使用physics及其parameters，不混用profile、analysis、materials、contract_version。meshes和geometries均为空对象，长度为m、时间为s。

physics.parameters恰含下表键，每项恰为`{"value":数值,"unit":"表中单位"}`，无默认、无自动换算；布尔值不能作为数值。

| 键 | unit | 范围与含义 |
|---|---|---|
| length | `m` | ≥1e-09，≤0.01；区间长度L，0<x<L |
| temperature | `K` | ≥200，≤500；等温温度T |
| permittivity | `F/m` | ≥1e-12，≤1e-09；绝对介电常数ε |
| intrinsic_density | `1/m3` | ≥100000000.0，≤1e+23；本征密度ni |
| tau_n | `s` | ≥1e-12，≤1；SRH电子寿命τn |
| tau_p | `s` | ≥1e-12，≤1；SRH空穴寿命τp |
| mobility_n | `m2/(V.s)` | ≥1e-06，≤1；电子迁移率μn |
| mobility_p | `m2/(V.s)` | ≥1e-06，≤1；空穴迁移率μp |

locations恰含下表位置；IDs为非负、严格递增int64，不能按ID数值推断坐标。points.coordinates为float64[N,1]真实x坐标。

| location | 类型及数量 | 对象 |
|---|---|---|
| profile | points，2..1024 | 包含x=0及x=L的剖面结点，按ID行序x严格递增；输入重建支撑，不是指定求解网格 |
| receivers | points，1..256 | 严格位于0<x<L的输出点；ID行序不要求坐标递增，允许重复坐标 |
| contacts | points，2..2 | 第一行x=0，第二行x=L的真实边界点 |

time_axes恰含`static`。static恰[0.0]，仅作稳态/静态标记。

fields的逻辑名和array key由清单给出，不必相同；每个下表quantity恰一个输入场，不能有其他输入场。每场dtype=float64、value_kind=point。所有场kind=scalar、component_shape=[1]、components=["value"]；数组形状[T,N,1]，不省略长度为1的轴。所有输入均以field呈现，不接受常量替代、option或隐式广播。

| 输入quantity | location | time_axis | unit | 范围与定义 |
|---|---|---|---|---|
| doping | profile | static | `1/m3` | ≥-1e+25，≤1e+25；完全电离的净掺杂C=ND−NA，允许正负及零 |
| contact_potential | contacts | static | `V` | ≥-2，≤2；两端电势ψ，绝对基准由输入固定 |
| contact_electron | contacts | static | `1/m3` | ≥1000000.0，≤1e+25；对应载流子的理想接触Dirichlet密度 |
| contact_hole | contacts | static | `1/m3` | ≥1000000.0，≤1e+25；对应载流子的理想接触Dirichlet密度 |
| generation | profile | static | `1/(m3.s)` | ≥0，≤1e+35；外部成对产生率G≥0 |

每个输入场显式sampling：profile位置space=piecewise_linear，其他位置space=uniform；time=constant；extrapolation=forbid。profile按真实x在相邻结点间线性重建，定义整个闭区间，不延拓到区间外；其他位置为各独立对象/边界自身的值，uniform不表示不同对象数值相等或可在对象之间插值。静态场各自单帧，在整个分析区间保持不变。

conditions恰有每个输入quantity一条：variable等于该quantity；location同表；operator固定`prescribed`；data恰含value且为`{"field":"该场逻辑名"}`。role：contacts位置非initial为boundary；doping为material；其他为source。顺序任意，各记录只引用对应场，不允许重复或未使用场。

物理重建、闭合和边界：

取电子电荷−q，q=1.602176634e−19 C，kB=1.380649e−23 J/K，VT=kB T/q；电势ψ单位V，电场E=−∂xψ。均匀材料、等温、完全电离、非简并Boltzmann统计；不含异质结、能带收缩、场依赖迁移率、隧穿、雪崩或热反馈。Poisson为−ε∂xxψ=q(p−n+C)。常规电流Jn=qμn nE+qDn∂xn，Jp=qμp pE−qDp∂xp，Dn=μnVT、Dp=μpVT。连续方程∂tn=(∂xJn)/q+G−R，∂tp=−(∂xJp)/q+G−R。SRH采用中带隙陷阱n1=p1=ni，R=(np−ni²)/[τp(n+ni)+τn(p+ni)]；这里R为净复合率，可负，不把外部G并入R。两端均为理想储库，分别直接给ψ、n、p；不再用局部电中性或接触功函数覆盖给定值。本题∂tn=∂tp=0，输入时间只是稳态标记。只包括有唯一正密度稳态的工况，不通过某个任意初猜或隐藏扫描方向选支。输出为该稳态的ψ、n、p、Jn、Jp；非零G/R时各分电流可随位置变化，稳态总传导电流应守恒。

连续模型无材料内部界面；净掺杂在profile处连续、导数可折变。所有输入及实际解须在非简并等温模型适用范围；不包含密度负值、非唯一稳态或无法在预算内达标的病态工况。该适用承诺需由正式数据的独立建模与参考证据落实，声明检查不求解并不证明之。

outputs逻辑名与array key任意且各自唯一；下表quantity每种至少一次，允许同一quantity多个独立命名的输出，均使用表中固定location/time_axis/分量；禁止其他quantity。不写输出sampling。所有输出float64、value_kind=point。

| quantity | location | time_axis | unit | 分量与含义 |
|---|---|---|---|---|
| potential | receivers | static | `V` | scalar [1]；ψ(x,t) |
| electron_density | receivers | static | `1/m3` | scalar [1]；n(x,t) |
| hole_density | receivers | static | `1/m3` | scalar [1]；p(x,t) |
| electron_current | receivers | static | `A/m2` | scalar [1]；向+x的常规传导电流密度Je |
| hole_current | receivers | static | `A/m2` | scalar [1]；向+x的常规传导电流密度Jh |

结果dataset形状[T,N,*component_shape]，只写各outputs.array及所引用的IDs、时间数组；不写坐标、输入场、额外诊断或元数据。输出点值为上述连续模型在给定坐标/时刻的值，不是内部单元均值；重复坐标保持不同ID行。输入场总标量数与全部请求输出标量数分别≤2000000，全部值有限，禁止默默截断。输入/输出HDF5的扁平、dtype与精确复制规则依CONTRACT。
