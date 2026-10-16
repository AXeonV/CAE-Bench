# 12.6.2 数据契约

仅本题instruction、DATA及通用CONTRACT定义要求；以下为格式定义，不是可运行数值样例。

physics恰含model、parameters；model=`granular-fragmentation-v1`，task若给须为`granular-fragmentation`。spatial_dimension=1；meshes、geometries均为空，不混用profile/analysis/materials/contract_version。spatial_dimension仅为有限维粒群的存储标记，不引入空间方程。

parameters恰含下表键，每项恰为value、unit，无默认、无隐式换算；数值有限，bool不能充当数值，整数必须为JSON整数。

| 参数 | unit | 范围与含义 |
|---|---|---|
| bin_count | `1` | 2≤value≤64；粒级数K，JSON整数 |
| monomer_volume | `m3` | 1e-24≤value≤1e-06；每个基础体积单元v0 |

locations恰含下表，全部kind=entities，仅含kind、ids。IDs为非负严格递增int64，除明确的bins身份规则外，不按ID大小猜属性或坐标。实体场value_kind=point指对象自身属性/状态，不是空间点、单元平均或区域积分。

| location | 数量 | 对象 |
|---|---|---|
| bins | 2..64 | IDs恰为1..K，第k级体积为k v0，不是粒径或质量 |
| system | 1..1 | 唯一均匀粒群总体 |

time_axes恰含`initial`, `observe`, `static`。static与initial各为[0.0]单帧，前者材料常数、后者物理初态，允许共用数组key。observe含1..256个严格递增时刻，0≤t≤tend、0<tend≤10 s，末项为tend；可请求t=0状态。所有核和材料响应在整个分析时间内保持不变；输出时刻不约束内部步长。

fields逻辑名和array key自由且不必相同；下列quantity各恰一个输入，禁止额外或未引用场，所有输入仅接受field，不允许常量/option代替。dtype=float64，value_kind=point，数组[T,N,*shape]保留全部轴。sampling恰为space=uniform、time=constant、extrapolation=forbid。uniform不表示不同实体同值，不进行实体之间的插值。

| 输入quantity | location | time_axis | kind/shape | unit | 范围与含义 |
|---|---|---|---|---|---|
| initial_density | bins | initial | scalar [1] | `1/m3` | 逐分量0..1e+24；初始各级数量密度n_k(0)，非概率/体积分数 |
| breakage_rate | bins | static | scalar [1] | `1/s` | 逐分量0..100000000.0；各级破碎频率a_k，a_1=0 |
| daughter_count | system | static | components ['K', 'K'] | `1` | 逐分量0..64；b_jk为一个第k级母粒子产生第j级子粒子的期望数量 |

scalar固定shape=[1]、components=["value"]。表中K=bin_count，components矩阵shape=[K,K]，标签按行优先为c1..c(K²)；矩阵不展平为数组轴，最后一轴变化最快。

conditions每个输入quantity恰一条，variable等于quantity，location同表，operator=prescribed，data恰为`{"value":{"field":"该输入场逻辑名"}}`。role：initial轴为initial、static轴为material。顺序任意，无重复或隐藏条件。

物理语义：

均匀稀相粒群，粒级k体积k v0，n_k为每总体积数密度。dn_j/dt=Σ_{k=j+1}^K a_k b_jk n_k−a_j n_j。a1=0，b_jk=0对j≥k；对每k≥2有Σ_{j=1}^{k−1}j b_jk=k。b为期望子粒子个数，可为非整数，不是概率或质量分数；每个母粒子的事件频率a乘一次，不额外除/乘子粒子总数。即使a_k=0，b的该列仍须完整守恒。无聚并、外部源、输运或粒级外碎屑；v0 Σ k n_k守恒。

bins数量恰K；每个量数组行与bins的1..K身份一致；system恰一个对象。初始φ=v0 Σ k n_k≤0.1，保证稀相，本题φ为全局实体属性而非网格体积积分。b矩阵行j为子粒级、列k为母粒级；所有j≥k项必须精确0，a1必须精确0，每k≥2列的加权和与k差≤1e−12 k；按原值计算，不自行归一化。难度界tend max(a)≤1e5。

outputs逻辑名和array key自由且唯一，每个下表quantity至少一次，允许多个独立命名的同quantity输出，逐个评分；禁止其他quantity。全部float64、value_kind=point、time_axis=observe，无sampling，分量标签沿上述规则。

| quantity | location | kind/shape | unit | 含义 |
|---|---|---|---|---|
| size_density | bins | scalar [1] | `1/m3` | 各级n_k(t) |
| number_density | system | scalar [1] | `1/m3` | Σ_k n_k(t) |
| solid_fraction | system | scalar [1] | `1` | v0 Σ_k k n_k(t)，本题为稀相名义固相体积分数 |

结果只含全部outputs.array及所引用的IDs和observe时间数组，须逐值精确复制轴；不输出输入场、坐标、附加诊断或元数据。场数组为[T,N,*shape]，全部有限，不省轴、重排或悄悄截断。输入场总标量数与请求输出总标量数各≤2000000。HDF5扁平布局及dtype等通用细节依CONTRACT。结构通过不证明物理适用、数值正确或参考可信。
