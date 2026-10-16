# 11.5.1 数据契约

本文件与instruction.md及通用CONTRACT.md构成完整要求；无额外领域文档依赖。以下为格式定义，未提供可运行算例或参考答案。

`spatial_dimension=1`；physics.model固定`semiconductor-landauer-v1`；task若给必须为`semiconductor-landauer`。仅使用physics及其parameters，不混用profile、analysis、materials、contract_version。meshes和geometries均为空对象，长度为m、时间为s，有限维实体不引入空间方程。

physics.parameters恰含下表键，每项恰为`{"value":数值,"unit":"表中单位"}`，无默认、无自动换算；布尔值不能作为数值。

| 键 | unit | 范围与含义 |
|---|---|---|
| temperature_left | `K` | ≥1，≤1000；左储库温度TL |
| temperature_right | `K` | ≥1，≤1000；右储库温度TR |
| chemical_left | `J` | ≥-1e-17，≤1e-17；左电化学势μL，相对共同能量零点 |
| chemical_right | `J` | ≥-1e-17，≤1e-17；右电化学势μR，共同零点 |
| degeneracy | `1` | JSON整数，≥1，≤16；额外简并度g，包含自旋；不再隐含乘2 |

locations恰含下表位置；IDs为非负、严格递增int64，不能按ID数值推断坐标。entities只有kind和ids，不带伪坐标。

| location | 类型及数量 | 对象 |
|---|---|---|
| spectrum | entities，2..4096 | 有序能量谱结点对象，按ID行序能量严格递增；不伪造空间坐标 |
| system | entities，1..1 | 唯一双端器件整体 |

time_axes恰含`static`。static恰[0.0]，仅作稳态/静态标记。

fields的逻辑名和array key由清单给出，不必相同；每个下表quantity恰一个输入场，不能有其他输入场。每场dtype=float64、value_kind=point。所有场kind=scalar、component_shape=[1]、components=["value"]；数组形状[T,N,1]，不省略长度为1的轴。所有输入均以field呈现，不接受常量替代、option或隐式广播。

| 输入quantity | location | time_axis | unit | 范围与定义 |
|---|---|---|---|---|
| energy | spectrum | static | `J` | ≥-1e-17，≤1e-17；E_j；共同能量基准，有限能带之外透射为0 |
| transmission | spectrum | static | `1` | ≥0，≤128；所有横向通道透射之和T(E_j)，不含g |

每个输入场显式sampling：space=uniform；time=constant；extrapolation=forbid。各位置为独立对象自身的值，uniform不表示不同对象数值相等或可在对象之间插值。静态场各自单帧，在整个分析区间保持不变。

conditions恰有每个输入quantity一条：variable等于该quantity；location同表；operator固定`prescribed`；data恰含value且为`{"field":"该场逻辑名"}`。role：其他为source。顺序任意，各记录只引用对应场，不允许重复或未使用场。

物理重建、闭合和边界：

两端理想Fermi储库，弹性相干且无相互作用的输运；透射谱已给定，不要求由几何或散射势重建。q=1.602176634e−19 C、kB=1.380649e−23 J/K、h=6.62607015e−34 J.s。fα(E)=1/[1+exp((E−μα)/(kB Tα))]。在完整输入能带[E0,EN−1]积分，T(E)为结点间分段线性、区间外为0。向右电子数流Ndot=(g/h)∫T(E)[fL−fR]dE；向右常规电流I=−q Ndot。离开左储库热流QL=(g/h)∫(E−μL)T(E)[fL−fR]dE。包含输入g一次，不额外乘自旋2；能量全用J，不隐式使用eV。QL不是总能流，也不是两端热流之和。

相邻能量严格递增、跨度为正；能量结点是积分支撑，不是时间或空间点。接近零温的边缘仍采用给定正温Fermi函数，不用阶跃替代；可加密积分，不能仅把输入谱结点作固定求积规则。

outputs逻辑名与array key任意且各自唯一；下表quantity每种至少一次，允许同一quantity多个独立命名的输出，均使用表中固定location/time_axis/分量；禁止其他quantity。不写输出sampling。所有输出float64、value_kind=point。

| quantity | location | time_axis | unit | 分量与含义 |
|---|---|---|---|---|
| electric_current | system | static | `A` | scalar [1]；向右常规电流I（电子粒子向右时I<0） |
| heat_left | system | static | `W` | scalar [1]；离开左储库的热流QL |

结果dataset形状[T,N,*component_shape]，只写各outputs.array及所引用的IDs、时间数组；不写坐标、输入场、额外诊断或元数据。输出为各独立实体在指定时刻的状态/属性，按ID行序存储，不作对象间平均。输入场总标量数与全部请求输出标量数分别≤2000000，全部值有限，禁止默默截断。输入/输出HDF5的扁平、dtype与精确复制规则依CONTRACT。
