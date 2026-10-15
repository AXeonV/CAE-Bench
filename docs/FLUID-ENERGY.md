# 封闭域能量与湍流配置 v1

> 维护方实现参考，不是第二章考生的额外协议依赖。每题完整要求以该题 instruction.md、DATA.md 及通用 CONTRACT.md 为准。

本规范使用[通用协议](CONTRACT.md)的 `physics`、带单位标量、场与条件，定义第二章 2.2—2.4 的有限首版。`physics.model` 显式启用下表模型；`task` 不携带任何物理缺省。不得同时使用 CFD 2.1 的 contract_version/profile/analysis/materials 四键。既有无此前缀的输入保持旧语义；此前缀的未知模型必须拒绝。以下规范、题目 DATA.md 与 COMMON.md 共同构成公开契约。

## 模型与维度

| physics.model | 物理／材料 | 方法责任 | 分析 | D |
|---|---|---|---|---|
| fluid-energy-lowmach-laminar-steady-v1 | 热膨胀牛顿液体、低速热流 | 层流 | 稳态 | 2/3 |
| fluid-energy-lowmach-laminar-transient-v1 | 同上 | 层流 | 瞬态 | 2/3 |
| fluid-energy-inviscid-laminar-steady-v1 | 无黏理想气体、平滑等熵流 | 无湍流闭合 | 稳态 | 2/3 |
| fluid-energy-inviscid-laminar-transient-v1 | 无黏理想气体、完整能量 | 无湍流闭合 | 瞬态 | 2/3 |
| fluid-energy-compressible-laminar-steady-v1 | 黏性导热理想气体 | 层流 | 稳态 | 2/3 |
| fluid-energy-compressible-laminar-transient-v1 | 同上 | 层流 | 瞬态 | 2/3 |
| fluid-energy-incompressible-rans-steady-v1 | 恒密度牛顿流体 | 稳态 RANS | 稳态平均 | 2/3 |
| fluid-energy-incompressible-urans-transient-v1 | 同上 | URANS | 非定常平均 | 3 |
| fluid-energy-incompressible-resolved-statistics-v1 | 同上 | 尺度解析 | 区间统计 | 3 |
| fluid-energy-isothermal-rans-steady-v1 | 等温理想气体 | 稳态 RANS | 稳态平均 | 3 |
| fluid-energy-lowmach-rans-steady-v1 | 热膨胀牛顿液体、低速热流 | 稳态 RANS | 稳态平均 | 3 |
| fluid-energy-lowmach-urans-transient-v1 | 同上 | URANS | 非定常平均 | 3 |
| fluid-energy-lowmach-resolved-statistics-v1 | 同上 | 尺度解析 | 区间统计 | 3 |
| fluid-energy-compressible-rans-steady-v1 | 黏性导热理想气体 | 稳态 RANS | 稳态平均 | 3 |

所有模型均为单相、固定的连通封闭流体域；无开口、周期面、粗糙壁、旋转坐标系、反应、相变、辐射、固体域或几何变形。允许内孔与多个固体障碍物，边界运动仅是给定切向速度，不改变域。二维为 xy 平面、出平面均匀，并非轴对称；整体质量按单位厚度解释。网格是一阶三角形/四边形或四面体/六面体/棱柱/金字塔，边界一阶线段/三角形/平面四边形；几何以该分片网格为准。首版以封闭域避免入口湍流生成和可压缩开口特征的额外隐含假定，移动壁与体加速度仍可驱动强制/自然/混合对流和封闭域湍流。

## 固定物理材料和状态

`physics.parameters` 必须恰含下列适用参数；所有项目均为 `{"value":数值,"unit":"代码"}`，无隐藏缺省。

| 参数 | 单位 | 适用性与范围 |
|---|---|---|
| reference_temperature | K | 全部；正值 Tref |
| minimum_temperature, maximum_temperature | K | 全部；0 < Tmin <= Tref <= Tmax，Tmin < Tmax；所有物理状态须在该闭区间 |
| density | kg/m3 | 非气体；正常数 rho0 |
| reference_pressure | Pa | 非气体；正绝对基准 p0，输出是 p-p0 的表压 |
| specific_gas_constant | J/(kg.K) | 气体；正值 R |
| mean_density | kg/m3 | 仅气体稳态；正值，指定总体质量/域体积；瞬态质量由初态确定，禁止此参数 |
| heat_capacity_ratio | 1 | 求能量的气体；gamma > 1，cp=gamma R/(gamma-1)，cv=R/(gamma-1) |
| isentropic_reference_density | kg/m3 | 仅无黏稳态；正值 rhos，使 T=Tref (rho/rhos)^(gamma-1)，排除未声明的稳态熵分布 |
| reference_viscosity | Pa.s | 除无黏模型外；正值 muref |
| viscosity_exponent | 1 | 除无黏模型外；有限实数 a |
| bulk_viscosity | Pa.s | 黏性气体；非负常数 zeta；是独立体积黏度而非第二黏度系数 |
| reference_conductivity | W/(m.K) | 求能量且有黏性；正值 kref |
| conductivity_exponent | 1 | 求能量且有黏性；有限实数 b |
| heat_capacity | J/(kg.K) | 低速液体热流；正常数 cp |
| thermal_expansion | 1/K | 低速液体热流；beta>=0，beta max(|Tmin-Tref|,|Tmax-Tref|)<=0.1 |
| time_start, time_end | s | 瞬态与统计；有限实数且 start<end |
| statistics_start, statistics_end | s | 仅统计；start<=a<b<=end |
| statistics_step | s | 仅统计；正值 delta，(b-a)/delta 是 1..100000 的整数 |

牛顿剪切响应 `mu(T)=muref (T/Tref)^a`、傅里叶导热 `k(T)=kref (T/Tref)^b`。a=b=0 是常物性；状态变化不含剪切依赖、记忆或结构变量。黏性气体采用三维材料应力约定 `tau=2 mu [D-(div u)I/3]+zeta (div u)I`，其中 `D=(grad u+grad u^T)/2`。二维平面流动仍使用三维材料的系数1/3，出平面速度及导数为0；不能改用二维无迹系数1/2。黏性耗散采用同一个应力的 `tau:grad u`，不以另一套二维应力计算。热完全理想气体满足绝对静压 p=rho R T；等温模型固定 T=Tref，不求能量。无黏模型严格忽略黏性与热导；瞬态允许有限强度压缩波、接触间断和激波，要求熵可容许解，不含真空；稳态只含平滑、无激波的等熵分支。无黏稳态当前固定封闭滑移域未提供环流或初态选择信息，仅纳入由等熵状态、体加速度与质量库存唯一确定的静水平衡，u=0；非零环流分支不在本版题目范围。此保证须由数据制作者提供适定性证据，格式校验不能证明。气体所有状态 p,rho,T>0；除无黏瞬态外气体马赫数（以 sqrt(gamma R T) 计；等温以 sqrt(R Tref) 计）不超过0.8。无黏瞬态上限为3。低速液体以 Boussinesq 热膨胀表达自然/混合对流：质量和惯性使用 rho0，体加速度 a 的力密度为 rho0[1-beta(T-Tref)]a；压力输出包括静水变化，域体积平均表压固定为0。非热不可压缩模型使用 rho0 a。液体保留黏性耗散；可压缩能量包含压缩功和适用的黏性耗散。无给定热源或体加速度时其值为0。

RANS/URANS 采用 Reynolds 平均；可压缩 RANS 的速度和温度采用 Favre 平均（rho 加权），静压和密度用 Reynolds 平均。不可压缩与低速模型的 Reynolds/Favre 速度一致。闭合、近壁处理、湍流热输运闭合与数值法由考生选择，光滑壁无滑移。URANS 的 U、k 与积分长度尺度采用公开标准化的建模初始化：初始 Reynolds 应力为各向同性 `2k/3 I`；含能量 URANS 的初始温度方差和速度温度协方差均为0。模型专有状态按所选闭合，由 k、积分长度尺度及这些公共二阶状态初始化。此声明没有给出完整随机速度场、能谱或精确物理 ensemble，不要求考生猜测它们；任务目标是 URANS 平均演化的工程近似。正式参考与容差须验证允许的闭合选择及高阶初始化差异均不会超过误差预算，不能以隐藏参考闭合补足输入。统计题必须进行三维尺度解析，允许 DNS 或有物理依据的 LES，不接受把 RANS 闭合方差直接当解析统计；初态 velocity 是完整瞬时速度，之后自行发展。尺度解析不足、平均窗口未达到目标的不确定度属于数值/建模误差，不能改变观测定义。

## 位置、时间及连续输入

恰有一个网格与一个完整流体域 mesh-element location，维度 D、IDs 恰为全部流体单元。不得以两个别名重复声明完整域。条件只能在该域或同网格外边界 element location 上；无节点、探针或 aggregate 条件。条件场的 location 必须与条件相同；tag 表示身份，不能用数组行号替代。

全部输入场为 float64、value_kind=average，表示对应流体单元或边界实体上的空间平均；使用显式 `sampling={"space":"piecewise_constant","time":"constant或linear","extrapolation":"forbid"}`。空间内重建为该实体上的常值，不在实体之间连续插值；边界棱角的多值按各面的一侧迹解释，不能叠加面条件到角点。constant 恰有一个样本并在整个物理区间保持不变；linear 至少两帧，在相邻时刻分段线性且覆盖整个积分区间，禁止区间外外推。稳态所有输入场恰有时刻[0]；初态场恰有[time_start]。输入表只声明被条件引用的场。

所有矢量都必须使用场，标量可以用显式带单位常数或场；不接受内联数组。scalar 的分量 shape=[1]、标签[value]；vector 为[D]、[x,y,z]前D项；tensor 为[D,D]及通用协议完整笛卡尔标签。场数组保留[T,N,*shape]。输出时刻不是内部步长。

## 条件的完整集合

下表是允许集合，data 的键必须恰好符合表格，不接受额外参数。所有条件同时生效，顺序无优先级。

| role / variable / operator | location | data | 确切含义 |
|---|---|---|---|
| boundary / velocity / moving_wall | 外边界实体子集 | value: velocity 场，m/s vector | 黏性模型无滑移速度；必须相对固定域法向为0，只可切向运动 |
| boundary / velocity / slip_wall | 外边界实体子集 | impermeable: {option:yes} | 仅无黏模型；u·n=0，自由切向，绝热 |
| boundary / temperature / temperature | 外边界实体子集 | value: K scalar | 仅求能量黏性模型；给定壁温 |
| boundary / temperature / outward_heat_flux | 外边界实体子集 | value: W/m2 scalar，场quantity=heat_flux | 仅求能量黏性模型；向外导热通量 -k grad(T)·n，正值为流体失热；0为绝热 |
| initial / velocity / assign | 全域 | value: velocity 场 | 瞬态/统计初始速度；URANS 为 Reynolds 平均，统计题为瞬时值 |
| initial / temperature / assign | 全域 | value: K scalar | 求能量瞬态/统计的初温 |
| initial / density / assign | 全域 | value: kg/m3 scalar | 气体瞬态初密度；正值，初静压由状态响应得出 |
| initial / turbulent_kinetic_energy / assign | 全域 | value: m2/s2 scalar | 仅 URANS；k>=0 |
| initial / turbulence_length_scale / assign | 全域 | value: m scalar | 仅 URANS；积分长度>0 |
| source / acceleration / assign | 全域 | value: acceleration 场，m/s2 vector | 体加速度，包括显式重力；低速液体按上述热膨胀修正 |
| source / heat_source / assign | 全域 | value: W/m3 scalar | 仅求能量模型（无黏稳态除外）；正为流体受热 |

每个外边界面恰有一条机械条件；求能量黏性模型还须恰有一条热条件，允许两套分区不一致。稳态热黏性模型至少一片给定温度壁，用于确定温度绝对水平；稳态能量收支、质量库存与稳态存在性仍须数据制作者保证。无黏稳态的热状态由公开等熵关系确定，不能另加壁温/热流。非能量模型不能请求热条件。瞬态/统计恰有各适用初态变量的一条全域赋值；稳态禁止物理初态。每种 source 至多一条全域记录。初态的空间常值重建可有间断，壁面迹与初态的瞬时角点不要求人为覆盖，演化按给定边界的一侧极限。

以下仅为条件结构片段，不是可运行算例（名称需引用实际清单）：

```json
{"role":"boundary","variable":"velocity","location":"wall","operator":"moving_wall","data":{"value":{"field":"wall_velocity"}}}
```

## 输出与统计定义

所有输出均为全域流体单元上的体积平均、float64、value_kind=average，不支持额外输出位置或未列物理量；每例必须请求本模型全部适用输出，允许不同输出使用不同的合法时间轴。

| quantity | kind / unit | 适用 |
|---|---|---|
| velocity | vector / m/s | 全部 |
| pressure | scalar / Pa | 全部；非气体表压、气体绝对静压 |
| temperature | scalar / K | 求能量模型 |
| density | scalar / kg/m3 | 气体 |
| velocity_covariance | tensor / m2/s2 | 统计题，完整对称矩阵 |
| temperature_variance | scalar / K2 | 含能量统计题 |
| turbulent_heat_flux | vector / K.m/s | 含能量统计题；速度温度协方差，不含rho cp，也不是 W/m2 热流 |

稳态输出时刻固定[0]，它只是存储标记。瞬态输出时刻在[start,end]内，包含实际请求的全部帧。统计输出时刻固定[b]，不把它理解成末帧瞬时场。统计样本时刻恰为 a+j delta，j=0..M、M=(b-a)/delta（两端都包含）。对每个流体单元先求该单元的空间平均瞬时 u_j、T_j、p_j，再对 S=M+1 样本等权求均值；不允许先局部平方再空间平均，因为那会增加单元内方差。cov=Σ(u_j-ubar)⊗(u_j-ubar)/S；温度方差=Σ(T_j-Tbar)^2/S；热流协方差=Σ(u_j-ubar)(T_j-Tbar)/S。平均静压仍满足指定域平均规范。统计题没有密度变化，不做 Favre 加权，也不使用 S-1 无偏估计或连续时间积分平均。

SDK 提供 `fluid_energy_properties(problem,T,pressure=None)` 精确读取材料响应，气体需绝对压力；`fluid_energy_condition_values(problem,condition,parameter,time)` 返回[N,*component_shape]；`fluid_energy_statistics(times,velocity,temperature=None)` 按上述离散样本计算均值和中央矩。其 times 是实际等距统计网格，velocity shape=[S,N,D]、可选温度[S,N,1]。SDK 不求解流动、不选择湍流闭合或补全未声明材料。

## 声明检查的边界

`validate-input` 的领域检查拒绝未知模型、参数/条件/单位/位置/维度/初态/时间/边界覆盖等不相容声明，不换算单位、不修补答案。通用层负责 shape、dtype、引用、IDs 和存储。网格几何连通、外面归属与切向壁速由领域层检查。温度有效范围和显式初密度的正值可检查；正压、马赫数、低速适用性、全域积分初态的不可压缩约束、求解后材料有效范围、稳态存在性与给定质量库存的物理解均是数据建设与求解验证责任，格式通过并不证明这些。
