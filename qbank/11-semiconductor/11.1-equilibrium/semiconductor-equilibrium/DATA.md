# 11.1.1 数据契约

本文件与instruction.md及通用CONTRACT.md构成完整要求；无额外领域文档依赖。以下为格式定义，未提供可运行算例或参考答案。

`spatial_dimension=1`；physics.model固定`semiconductor-equilibrium-v1`；task若给必须为`semiconductor-equilibrium`。仅使用physics及其parameters，不混用profile、analysis、materials、contract_version。meshes和geometries均为空对象，长度为m、时间为s。

physics.parameters恰含下表键，每项恰为`{"value":数值,"unit":"表中单位"}`，无默认、无自动换算；布尔值不能作为数值。

| 键 | unit | 范围与含义 |
|---|---|---|
| length | `m` | ≥1e-09，≤0.01；区间长度L，0<x<L |
| temperature | `K` | ≥200，≤500；等温温度T |
| permittivity | `F/m` | ≥1e-12，≤1e-09；绝对介电常数ε |
| intrinsic_density | `1/m3` | ≥100000000.0，≤1e+23；本征密度ni |

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

每个输入场显式sampling：profile位置space=piecewise_linear，其他位置space=uniform；time=constant；extrapolation=forbid。profile按真实x在相邻结点间线性重建，定义整个闭区间，不延拓到区间外；其他位置为各独立对象/边界自身的值，uniform不表示不同对象数值相等或可在对象之间插值。静态场各自单帧，在整个分析区间保持不变。

conditions恰有每个输入quantity一条：variable等于该quantity；location同表；operator固定`prescribed`；data恰含value且为`{"field":"该场逻辑名"}`。role：contacts位置非initial为boundary；doping为material；其他为source。顺序任意，各记录只引用对应场，不允许重复或未使用场。

物理重建、闭合和边界：

取电子电荷−q，q=1.602176634e−19 C，kB=1.380649e−23 J/K，VT=kB T/q；电势ψ单位V，电场E=−∂xψ。均匀材料、等温、完全电离、非简并Boltzmann统计；不含异质结、能带收缩、场依赖迁移率、隧穿、雪崩或热反馈。全器件具有共同平衡Fermi能级，ψ=0定义为n=p=ni；因此n=ni exp(ψ/VT)，p=ni exp(−ψ/VT)。求−εψ″=q[p−n+C(x)]，两端ψ给定。零点已固定，不允许事后平移电势或自行用接触电中性替换边值。热平衡没有外加准Fermi分裂，不求非平衡电流。

连续模型无材料内部界面；净掺杂在profile处连续、导数可折变。所有输入及实际解须在非简并等温模型适用范围；不包含密度负值、非唯一稳态或无法在预算内达标的病态工况。该适用承诺需由正式数据的独立建模与参考证据落实，声明检查不求解并不证明之。

outputs逻辑名与array key任意且各自唯一；下表quantity每种至少一次，允许同一quantity多个独立命名的输出，均使用表中固定location/time_axis/分量；禁止其他quantity。不写输出sampling。所有输出float64、value_kind=point。

| quantity | location | time_axis | unit | 分量与含义 |
|---|---|---|---|---|
| potential | receivers | static | `V` | scalar [1]；ψ(x,t) |
| electron_density | receivers | static | `1/m3` | scalar [1]；n(x,t) |
| hole_density | receivers | static | `1/m3` | scalar [1]；p(x,t) |
| electric_field | receivers | static | `V/m` | scalar [1]；E=−∂xψ |

结果dataset形状[T,N,*component_shape]，只写各outputs.array及所引用的IDs、时间数组；不写坐标、输入场、额外诊断或元数据。输出点值为上述连续模型在给定坐标/时刻的值，不是内部单元均值；重复坐标保持不同ID行。输入场总标量数与全部请求输出标量数分别≤2000000，全部值有限，禁止默默截断。输入/输出HDF5的扁平、dtype与精确复制规则依CONTRACT。
