# 12.1.1 数据契约

仅本题instruction、DATA及通用CONTRACT定义要求；以下为格式定义，不是可运行数值样例。

physics恰含model、parameters；model=`granular-forced-motion-v1`，task若给须为`granular-forced-motion`。spatial_dimension=3；meshes、geometries均为空，不混用profile/analysis/materials/contract_version。坐标为全局三维笛卡尔，长度m、时间s；移动位置由状态字段给出。

parameters恰含下表键，每项恰为value、unit，无默认、无隐式换算；数值有限，bool不能充当数值，整数必须为JSON整数。本题parameters为空对象。

| 参数 | unit | 范围与含义 |
|---|---|---|

locations恰含下表，全部kind=entities，仅含kind、ids。IDs为非负严格递增int64，不按ID大小猜属性或坐标。实体场value_kind=point指对象自身属性/状态，不是空间点、单元平均或区域积分。

| location | 数量 | 对象 |
|---|---|---|
| particles | 1..128 | 具有固定ID的球形颗粒；位置是未知状态，不用固定points伪装运动颗粒 |

time_axes恰含`drive`, `initial`, `observe`, `static`。static与initial各为[0.0]单帧，前者材料常数、后者物理初态，允许共用数组key。observe含1..256个严格递增时刻，0≤t≤tend、0<tend≤10 s，末项为tend；可请求t=0状态。drive含2..512个严格递增时刻，首项0、末项恰tend，逐粒子外载在相邻驱动时刻逐分量线性插值，不外推；observe无需与drive重合，内部时间步自行选择。

fields逻辑名和array key自由且不必相同；下列quantity各恰一个输入，禁止额外或未引用场，所有输入仅接受field，不允许常量/option代替。dtype=float64，value_kind=point，数组[T,N,*shape]保留全部轴。sampling恰为space=uniform、time=linear（drive轴）/constant（其他轴）、extrapolation=forbid。uniform不表示不同实体同值，不进行实体之间的插值。

| 输入quantity | location | time_axis | kind/shape | unit | 范围与含义 |
|---|---|---|---|---|---|
| mass | particles | static | scalar [1] | `kg` | 逐分量1e-12..10；粒子质量m_i |
| radius | particles | static | scalar [1] | `m` | 逐分量1e-06..0.1；固定球半径R_i |
| drag | particles | static | scalar [1] | `kg/s` | 逐分量0..10000.0；相对静止背景的线性平动阻力系数b_i |
| initial_position | particles | initial | vector [3] | `m` | 逐分量-100..100；t=0质心位置x_i |
| initial_velocity | particles | initial | vector [3] | `m/s` | 逐分量-1000.0..1000.0；t=0平动速度v_i |
| external_force | particles | drive | vector [3] | `N` | 逐分量-10000.0..10000.0；已包含重力等全部外加力，不再额外加g或浮力 |

scalar固定shape=[1]、components=["value"]。vector固定[3]及x/y/z。

conditions每个输入quantity恰一条，variable等于quantity，location同表，operator=prescribed，data恰为`{"value":{"field":"该输入场逻辑名"}}`。role：initial轴为initial、drive轴为source、static轴为material。顺序任意，无重复或隐藏条件。

物理语义：

三维无相互作用球形粒子，dx_i/dt=v_i，m_i dv_i/dt=Fext_i(t)−b_i v_i。背景静止、阻力线性，外力已包含重力等全部效应，不反求流场、不加布朗力。粒子可重叠或穿越，半径仅为对象属性，不进行碰撞、约束或自转计算。

合法问题族要求全程每个位置分量|x|≤100 m、速度分量|v|≤1000 m/s；这些响应尺度是正式数据须独立验证的适用条件，声明校验不演化轨迹。各粒子的质量、半径及阻力与初态/驱动按同一particles身份逐行关联，不能重排。难度界tend max_i(b_i/m_i)≤1e5。另用输入充分界逐粒子逐分量要求|x0|+tend |v0|+tend² max_drive|Fext|/(2mi)≤100 m，排除绝对位置误差低于float64可分辨尺度的输入。

outputs逻辑名和array key自由且唯一，每个下表quantity至少一次，允许多个独立命名的同quantity输出，逐个评分；禁止其他quantity。全部float64、value_kind=point、time_axis=observe，无sampling，分量标签沿上述规则。

| quantity | location | kind/shape | unit | 含义 |
|---|---|---|---|---|
| position | particles | vector [3] | `m` | 逐粒子的全局质心位置 |
| velocity | particles | vector [3] | `m/s` | 逐粒子的全局平动速度 |

结果只含全部outputs.array及所引用的IDs和observe时间数组，须逐值精确复制轴；不输出输入场、坐标、附加诊断或元数据。场数组为[T,N,*shape]，全部有限，不省轴、重排或悄悄截断。输入场总标量数与请求输出总标量数各≤2000000。HDF5扁平布局及dtype等通用细节依CONTRACT。结构通过不证明物理适用、数值正确或参考可信。
