# 12.5.1 数据契约

仅本题instruction、DATA及通用CONTRACT定义要求；以下为格式定义，不是可运行数值样例。

physics恰含model、parameters；model=`granular-periodic-assembly-v1`，task若给须为`granular-periodic-assembly`。spatial_dimension=3；meshes、geometries均为空，不混用profile/analysis/materials/contract_version。坐标为全局三维笛卡尔，长度m、时间s；移动位置由状态字段给出。

parameters恰含下表键，每项恰为value、unit，无默认、无隐式换算；数值有限，bool不能充当数值，整数必须为JSON整数。

| 参数 | unit | 范围与含义 |
|---|---|---|
| stiffness | `N/m` | 0.0001≤value≤10000000.0；公共法向弹性刚度k |
| normal_damping | `kg/s` | 0≤value≤1000.0；公共法向阻尼γ，无隐藏质量乘数 |
| box_length | `m` | 0.0001≤value≤10；固定立方周期代表体边长L |

locations恰含下表，全部kind=entities，仅含kind、ids。IDs为非负严格递增int64，不按ID大小猜属性或坐标。实体场value_kind=point指对象自身属性/状态，不是空间点、单元平均或区域积分。

| location | 数量 | 对象 |
|---|---|---|
| particles | 1..128 | 具有固定ID的球形颗粒；位置是未知状态，不用固定points伪装运动颗粒 |
| system | 1..1 | 唯一周期代表体；整体物理属性使用entities状态，不伪装网格积分 |

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

scalar固定shape=[1]、components=["value"]。vector固定[3]及x/y/z；tensor固定[3,3]及xx,xy,xz,yx,yy,yz,zx,zy,zz，不用Voigt。

conditions每个输入quantity恰一条，variable等于quantity，location同表，operator=prescribed，data恰为`{"value":{"field":"该输入场逻辑名"}}`。role：initial轴为initial、drive轴为source、static轴为material。顺序任意，无重复或隐藏条件。

物理语义：

三维球形颗粒，质量和半径恒定，dx_i/dt=v_i，m_i dv_i/dt=Fext_i(t)−b_i v_i+Σ_j Fij。外力是已合成的实际力，背景静止，不自行增加重力、浮力、随机力或流体反馈。所有相互作用按无序对i<j各算一次，Fji=−Fij，允许同时多接触，不顺序执行两两瞬时速度跳跃。本题固定立方体在三个方向周期延拓；位置轨迹保留连续未包裹x。计算相互作用时逐分量取r=x_i−x_j−L floor((x_i−x_j)/L+1/2)，取最近像；不与自身镜像相互作用。令d=|r|>0，n=r/d从j指向i，δ=Ri+Rj−d，vn=(vi−vj)·n。δ>0时P=max(0,kδ−γ vn)，否则P=0；法向力为P n，γ直接以kg/s使用，不乘约化质量。δ=0时按非接触取P=0。此处r始终是上述最近像位移，不用未包裹位置差覆盖。初始位置在[0,L)³，输出仅宏观状态，不请求位置。V=L³，vbar=Σ mi vi/Σ mi，ci=vi−vbar。σ=−(Σ_i mi ci⊗ci+Σ_{i<j} r_ij⊗Fij)/V，拉为正；各对用同一最近像r和其作用在i上的Fij，不重复计数、不除2。Ekin=Σ mi|ci|²/2，配位数Z=2Nc/N（Nc恰为δ>0的对数，不以P>0计），φ=Σ4πRi³/(3V)。无自转、摩擦、黏附、墙或盒形变；名义堆积率不扣重叠。不是把颗粒应力除以各自任意体积后平均，也不把平均流动动能计入涨落应力。

合法问题族要求全程每个位置分量|x|≤100 m、速度分量|v|≤1000 m/s；这些响应尺度是正式数据须独立验证的适用条件，声明校验不演化轨迹。各粒子的质量、半径及阻力与初态/驱动按同一particles身份逐行关联，不能重排。难度界tend max_i(b_i/m_i)≤1e5。另有tend sqrt(k/min_i mi)≤1e5、tend γ/min_i mi≤1e5；全演化每对中心d>0且δ≤0.05 min(Ri,Rj)，排除中心重合及大变形。工具仅检查初态，正式数据须独立验证全程条件、事件附近收敛及短时轨迹可重复精度，不能用碰撞后不受控的混沌放大掩盖逐值判据。每对Ri+Rj<0.49L，保证接触不涉及最近像半盒歧义，单颗粒也须2Ri<0.49L；初态坐标各分量在[0,L)，运动时不包裹状态。输出时刻每对|δ|≥1e−8 min(Ri,Rj)，使配位计数避开刚接触/脱离的阈值；该全程/输出适用承诺需正式数据独立验证。名义φ≤0.74。

outputs逻辑名和array key自由且唯一，每个下表quantity至少一次，允许多个独立命名的同quantity输出，逐个评分；禁止其他quantity。全部float64、value_kind=point、time_axis=observe，无sampling，分量标签沿上述规则。

| quantity | location | kind/shape | unit | 含义 |
|---|---|---|---|---|
| stress | system | tensor [3, 3] | `Pa` | 拉应力为正的完整Cauchy张量σ |
| kinetic_energy | system | scalar [1] | `J` | 相对质量加权平均速度的平动涨落动能 |
| coordination | system | scalar [1] | `1` | 2 Nc/N，包括无接触粒子，Nc为δ>0的无序对数 |
| solid_fraction | system | scalar [1] | `1` | Σ_i 4πRi³/(3L³)，不扣除软球重叠体积 |

结果只含全部outputs.array及所引用的IDs和observe时间数组，须逐值精确复制轴；不输出输入场、坐标、附加诊断或元数据。场数组为[T,N,*shape]，全部有限，不省轴、重排或悄悄截断。输入场总标量数与请求输出总标量数各≤2000000。HDF5扁平布局及dtype等通用细节依CONTRACT。结构通过不证明物理适用、数值正确或参考可信。
