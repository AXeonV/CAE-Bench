# 流体多相配置 v1（2.5—2.7）

> 维护方实现参考，不是第二章考生的额外协议依赖。每题完整要求以该题 instruction.md、DATA.md 及通用 CONTRACT.md 为准。

本规范与 [通用契约](CONTRACT.md) 一起定义公开输入。它是固定 Euler 位置上的有限首版，不描述逐粒轨迹、移动坐标或碰撞接触网络。数值离散、界面追踪、线性代数、软件和内部网格由考生选择；以下物理响应、平均方式和交换定律不能更换。

## 启用、模型与范围

使用既有 `physics: {model, parameters}`，**不**同时使用 `profile/contract_version/analysis/materials`。model 必须为下表完整字符串加前缀 `fluid-multiphase-` 和后缀 `-v1`。未知名字和版本拒绝；task 名不携带物理含义。旧输入不启用本配置时保持原语义。新配置不改变 JSON 结构和 HDF5 编码。

| model 中段 | D | 分析对象与责任 |
|---|---|---|
| free-surface | 2、3 | 不可压缩牛顿液体 a 与无惯性、无黏性气体储槽；解析自由界面，忽略表面张力 |
| immiscible | 2、3 | 解析双方不可压缩牛顿流体，无相变，表面张力为零 |
| wetting | 2、3 | 双方不可压缩牛顿流体；恒定表面张力、给定接触角和 Navier 滑移 |
| passive-particles | 3 | 单分散球形颗粒 b 在载液 a 中单向输运；相平均，无反馈近似 |
| coupled-particles | 3 | 相平均颗粒，两相质量和动量耦合，给定线性阻力 |
| bubbles-droplets | 3 | 相平均不变形、不合并、不破碎的单分散泡滴；给定线性阻力，双方黏性 |
| dense-dispersed | 3 | 浓悬浮液相平均反馈、浓度压强和增黏；不求逐粒碰撞 |
| interphase-exchange | 3 | 共速双相、双温度、双稀溶质浓度，不相变的热质交换 |
| evaporation-condensation | 2 | 单一 Euler 速度场（允许两侧迹不同）、界面共温的尖锐界面低速蒸冷，给定界面动力学 |
| boiling | 3 | 共速、共温的均匀混合沸腾；体积成核/蒸冷动力学，不解析单个气泡 |
| cavitation | 3 | 等温共速混合空化；压力驱动相变与核含率 |
| melting-solidification | 2 | 等密度焓法、液相率温度关系与固定固体骨架的 mushy 阻力 |

全为瞬态、层流、无反应、无湍流、无界面活性剂、无辐射。除 free-surface 外，a、b 都是物理相。2D 是 xy 平面、单位出平面厚度；不是轴对称。边界不移动。所有相密度均为正常数；非等温过程忽略热膨胀、压缩功及黏性耗散。蒸冷、沸腾限定围绕给定饱和温度的低速近参考压力过程，不要求由状态方程预测饱和曲线。空化是明确的等温简化模型。不得将这些有限模型结果宣传为任意材料真实相变预测。

## 全局参数（必须逐项给出，禁止额外参数）

`physics.parameters.<name>` 均为 `{value: 有限数, unit: 下表代码}`，不接受选项、场引用或单位转换。时间起止可为任意有限实数，必须 end > start。所有注明“正”的量严格 >0，非负量允许零。

| 适用模型 | 名称 | unit；范围与含义 |
|---|---|---|
| 全部 | time_start、time_end | s；物理积分区间 |
| 全部 | density_a、viscosity_a、pressure_reference | kg/m3、Pa.s、Pa；均正；a 密度、动力黏度及绝对压力基准 |
| 除 free-surface、melting-solidification | density_b | kg/m3；正，b 密度 |
| immiscible、wetting、bubbles-droplets、interphase-exchange、evaporation-condensation、boiling、cavitation | viscosity_b | Pa.s；正，b 动力黏度 |
| wetting | surface_tension、contact_angle、slip_length | N/m、rad、m；均正，0 < 角度 < π；接触角穿过 a 相测量，滑移长度为物理参数 |
| 全部四种分散模型 | relaxation_time、diameter | s、m；正；线性阻力响应时间及球形分散相物理直径（适用性信息，不能另据此改阻力律） |
| dense-dispersed | packing_fraction、particle_modulus | 1、Pa；正；最大 b 体积分数 <1、浓度压强系数 |
| interphase-exchange、evaporation-condensation、boiling | heat_capacity_a、heat_capacity_b、conductivity_a、conductivity_b | J/(kg.K)、J/(kg.K)、W/(m.K)、W/(m.K)；均正，常定压比热和导热系数 |
| interphase-exchange | heat_exchange、mass_exchange | W/(m3.K)、1/s；非负；每混合体积交换系数 |
| interphase-exchange | diffusivity_a、diffusivity_b | m2/s；正，稀溶质扩散率 |
| evaporation-condensation、boiling、melting-solidification | latent_heat | J/kg；正 |
| evaporation-condensation、boiling | saturation_temperature | K；正，固定参考压力下饱和温度 |
| evaporation-condensation | interface_mass_coefficient | kg/(m2.s.K)；正，界面质量通量/温差 |
| boiling | evaporation_frequency、condensation_frequency | 1/s；正，体积蒸冷响应频率 |
| cavitation | saturation_pressure、pressure_rate、nuclei_fraction | Pa、kg/(m3.s.Pa)、1；均正，核体积分数 <1 |
| melting-solidification | heat_capacity_a、conductivity_a | J/(kg.K)、W/(m.K)；正；两态共同使用 |
| melting-solidification | solidus_temperature、liquidus_temperature | K；正；liquidus > solidus |
| melting-solidification | mushy_resistance、mushy_epsilon | kg/(m3.s)、1；正；阻力系数和分母正则量 |

## 物理响应及相标识

下文 α 为 a 相体积分数，β=1−α；u 为共速模型的速度，g 为输入的 acceleration；D(u) 为对称速度梯度。所有压力是**绝对静压**，不是去静水压。封闭双相/分散/熔凝域每个时刻的压力体积平均固定为 pressure_reference；free-surface 的液气界面外压为 pressure_reference。相变开边界储槽也取该绝对外压，无额外压力平移。

### 解析无相变界面

free-surface 在液体区域解常密度牛顿质量与动量守恒，界面物质输运、应力牵引为 −pressure_reference n，气体不求动量。气体中的输出速度扩展为零、压力扩展为 pressure_reference，故穿界面单元的输出是此扩展场的体积平均；不是液体内条件平均。immiscible/wetting 双方各自质量、牛顿动量守恒，界面速度连续且无相变。immiscible 牵引连续。wetting 令界面法向 n 从 a 指向 b、κ=div(n)，满足 `(stress_b−stress_a)n=surface_tension κ n`。壁面静态接触角按穿过 a 相定义，始终采用该角，无滞后；壁面无穿透、以壁面流体域外法向 n_w、P_t=I−n_w⊗n_w 定义各相切向牵引 `P_t stress_i n_w=−mu_i P_t u_i/slip_length`。接触线数值表示由考生选择，不能以网格相关滑移长度替代输入值。

初始 α 只能为 0 或 1，解释为每个输入体单元内精确相指示量，其边界集合确定初始界面，不能自选亚单元界面；初始两相都必须存在。随后 α 的观测是精确相指示函数的单元体积平均。无表面张力题不要求接触角。

### 分散相模型

α 为载液含率、β 为颗粒/泡滴含率，不解析其单个表面。输出 `flux_a=α u_a`、`flux_b=β u_b` 是**表观体积通量密度**；并非相内条件平均速度。β=0 时规定 flux_b=0，相 b 速度的延拓不参与评价。球径恒定，无尺寸分布、布朗运动、升力、附加质量、破碎、合并或相变。

被动模型的载液满足 div(u_a)=0 及常密度单相牛顿动量，完全忽略颗粒排液与动量反馈；颗粒满足 `∂t β+div(β u_b)=0`，其加速度为 `(u_a−u_b)/tau+g`，不受流体压力梯度。这是公开的单向点颗粒近似，α=1−β 仅用于报告占率和通量，不另强制载液质量方程。

其余三个模型双方满足 `∂t(α_i rho_i)+div(α_i rho_i u_i)=0`。相动量采用相质量输运、体力 α_i rho_i g、压力力 `−α_i grad(p)`，阻力作用于 b 为 `β rho_b (u_a−u_b)/tau`，a 受相反力。载液黏性应力为 `2 α mu_a D(u_a)`；颗粒的偏应力为零，bubbles-droplets 的 b 应力为 `2 β mu_b D(u_b)`。耦合模型无额外湍动或颗粒压强。dense-dispersed 另在 b 动量中加入 `−grad(P_b)`，`P_b=particle_modulus β²/(packing_fraction−β)`，并将载液黏度替换为 `mu_a/(1−β/packing_fraction)²`。这些都是固定物理闭合，不要求考生反推某来源软件模型。

三个稀疏模型要求全程 `0≤β<0.1`；dense-dispersed 要求 `0≤β<packing_fraction`。这些全程和连续解适用性由算例制作方证明，检查器仅能检查给定初态。壁面对 b 无质量通量，b 切向自由滑移；a 无滑移。初态输入 flux_a、flux_b，制作方保证缺相时相应通量为零。

### 不相变热质交换

interphase-exchange 采用共速、div(u)=0、α 物质输运，混合密度和黏度分别为体积加权。动量为保守变密度牛顿形式。α 严格在 (0,1)；两种温度可不同。每相热量方程为 `α_i rho_i cp_i D_t T_i=div(α_i k_i grad T_i)+Q_i`，`Q_a=H(T_b−T_a)`、Q_b=−Q_a。稀溶质浓度 c_i 的单位是每**该相体积** kg/m3，守恒量为 α_i c_i，扩散通量为 `−α_i diffusivity_i grad(c_i)`；相 a 的交换源 `S_a=M(c_b−c_a)`，S_b=−S_a。分配系数明确为 1。溶质仅被动输运，不改变相总质量、密度、黏度或温度；无化学反应。这不是载体相蒸发。封闭壁面溶质零通量，热壁温同时作用于两相。

### 蒸冷、均匀沸腾与等温空化

相 a 是液体、b 是蒸气。令 m 为每混合体积**从 a 到 b**的质量率；`∂t(α rho_a)+div(α rho_a u)=−m`，b 源为 +m，因此 `div(u)=m(1/rho_b−1/rho_a)`，不可擅自强制 div(u)=0。至少一个压力储槽用于体积交换。下述尖锐界面与均匀混合方法的速度/应力解释分别固定，不能混用。

**均匀沸腾/空化动量。** 两相在每个混合点共速，`rho=α rho_a+β rho_b`，`mu=α mu_a+β mu_b`；保守动量为 `∂t(rho u)+div(rho u⊗u)=−grad(p)+div(tau)+rho g`。其中 `tau=2 mu[D(u)−(div(u)/3) I]`，明确采用三维去迹的牛顿剪切应力、体黏度为零（Stokes 选择），不增加额外相变动量源、表面张力或相间滑移。相变引起的非零散度必须进入该应力，不得直接改用 `2 mu D(u)`。压力为绝对静压，不能将迹项暗中吸收后仍输出原pressure语义。

**尖锐蒸冷的运动学。** 输入和输出使用单一分片 Euler 速度场 `u(x,t)`，它在a/b相内部各有速度 `u_a/u_b`，允许界面两侧的**法向迹不同**；“单一场”不表示跨界面速度连续。界面法向n从a指向b，V为界面沿n的几何移动速度（有符号，单位m/s），界面质量通量 `j=K(T_interface−T_sat)` 取a→b为正。两侧严格满足 `rho_a(u_a·n−V)=rho_b(u_b·n−V)=j`，所以 `[u·n]=j(1/rho_b−1/rho_a)`；方括号始终表示b侧迹减a侧迹。切向速度迹连续。m=j δ_interface，δ为按实际界面面积定义的表面分布。固定全域输出velocity是该分片速度场的单元体积平均，不能用液体内条件平均或界面速度V代替。

**尖锐蒸冷的力学跳跃。** 各相内部 `div(u_i)=0`，解 `rho_i D_t u_i=div(stress_i)+rho_i g`，`stress_i=−p_i I+2 mu_i[D(u_i)−(div(u_i)/3) I]`，体黏度为零。二维为三维平面嵌入，取u_z=0、∂z=0，仍使用1/3去迹约定；相内部散度零时等价于 `2 mu_i D(u_i)`。速度梯度和牛顿应力只在各相内部求导，**不得**将跳跃速度的全局分布梯度代入黏性本构，制造δ黏性应力。界面无表面张力，完整牵引跳跃为 `[stress] n=j[u]`，包括质量动量通量造成的反冲；不可以牵引连续代替。保守分片动量的弱形式与此跳跃等价，不另重复加入反冲体源。

**尖锐蒸冷的热跳跃。** 温度两侧迹连续为T_interface。定义 `h_a=cp_a(T−T_sat)`、`h_b=cp_b(T−T_sat)+L`，导热通量 `q_i=−k_i grad(T_i)`；界面满足 `[k ∂n T]=j[h]`（等价于 `[q·n]=−j[h]`）。两态比热不同时必须使用实际界面温度处的 `[h]=L+(cp_b−cp_a)(T_interface−T_sat)`，不能只用jL。该跃迁与下述保守焓近似一致：忽略压力功、动能及黏性耗散对热量的贡献，不另假定完整总能量守恒。数值法可以显式追踪界面或采用收敛到相同分片跳跃问题的保守方法，不能凭“共速”删除反冲或质量膨胀。

`phase_change_rate` 输出是m的单元体积平均（界面质量率积分/单元体积），不要求返回数值平滑带的峰值。

沸腾题采用均匀分散体积率，不需给定泡核坐标。`m=f_ev rho_a α max(T−T_sat,0)/T_sat − f_cond rho_b β max(T_sat−T,0)/T_sat`。该规定允许纯液体中过热成核；不要求真实壁面微结构、经验壁面沸腾曲线或单个泡的脱离直径。

两种热相变的混合体积焓定义为 `H=α rho_a cp_a(T−T_sat)+β rho_b[cp_b(T−T_sat)+L]`；解 `∂t H+div(H u)=div(k grad T)`，k 体积加权，不另重复添加 latent_heat*m 源。沸腾的混合点共温，蒸冷的界面两侧温度连续；蒸冷的H和k在各相内取对应常物性，导热梯度按上述相内/热跳跃意义解释。蒸冷和沸腾模型在两态比热不同的时候也使用此完整焓定义。

空化不求温度，`m=C[α max(p_sat−p,0)−max(β−nuclei_fraction,0) max(p−p_sat,0)]`。这是本协议指定的压力线性动力学，不隐含 Rayleigh–Plesset 或其他商业闭合；p 为绝对静压，核率只进入上述式子。制作方保证体积分数始终可接受。

### 熔凝

a 是液态、b 是固定固体骨架，rho_b=rho_a，cp_b=cp_a，k_b=k_a，不重复输入。令 `f(T)=clip((T−T_s)/(T_l−T_s),0,1)`，α=f(T)，不用另给 α 初态。体积焓 `H=rho_a[cp_a(T−T_s)+L α]`，`∂tH+div(H u)=div(k_a grad T)`。速度满足 div(u)=0，且全域使用常黏度 mu_a=viscosity_a：`rho_a(∂t u+u·∇u)=−grad(p)+div(2 mu_a D(u))+rho_a g−A(1−α)²/(α³+epsilon)u`。不作 α 加权黏度；骨架速度固定为零。该有限 mushy 模型允许低于液相线的阻尼运动，不另解弹性或收缩。相变率输出按液体→固体为正，`m=−rho_a D_t α`，不是单纯 `−rho_a ∂t α`。

## 位置、场和时间的完整表示

恰好一个 Gmsh 一阶 D 维、按公共面连通的流体/混合域；允许三角/四边形或四面体/六面体/棱柱/金字塔，外边界必须导出一阶线段/三角/平面四边形。一个 `domain` 作用位置（名字可变）必须恰好覆盖全部 D 维单元；初态和 acceleration 条件共用该 location。全部场为 float64 的单元/边界实体 **average**，标量 [T,N,1]、向量 [T,N,D]，分量标签遵从 CONTRACT。不使用独立点或节点条件。额外未被条件引用的输入场拒绝。

每个输入场显式给 `sampling={space: uniform或piecewise_constant, time: constant或linear, extrapolation: forbid}`。空间解释为给定单元内常值；边界给定实体内常值。uniform 还要求同一帧全部实体值相等。constant 时轴必须只有一个时刻，该值在整个物理区间内恒定（包括初态单帧的标记作用，不是外推）；linear 数据轴至少覆盖 time_start—time_end，以相邻样本线性插值，不允许外推。初始场轴必须恰含 time_start。时间轴不规定内部时间步。

允许的物理场如下，禁止其他 quantity 或不匹配单位；输入场 quantity 必须与条件所需物理量匹配：

| quantity | kind / unit | 含义 |
|---|---|---|
| alpha | scalar / 1 | a 相体积分数，0≤α≤1 |
| velocity | vector / m/s | 共速/解析界面的速度（free-surface 使用前述气区扩展） |
| flux_a、flux_b | vector / m/s | αu_a、βu_b |
| pressure | scalar / Pa | 绝对静压 |
| acceleration | vector / m/s2 | 各相共同的外部体加速度，含全部重力；没有隐含地球重力 |
| temperature、temperature_a、temperature_b | scalar / K | 绝对温度，严格正 |
| concentration_a、concentration_b | scalar / kg/m3 | 每相体积溶质浓度，非负 |
| phase_change_rate | scalar / kg/(m3.s) | a→b 为正的体积质量率，只作为输出 |

标量初态/边界可以用 `{value,unit}` 常数；向量必须引用场，不允许 JSON 内联数组。常数正好表示整个作用区域和时间内的均匀数据。条件字段/常数数据类型不可用 option 互换。

## 条件清单与组合

每个条件仅有 CONTRACT 规定键。data 不得为空。全域初态每个所需变量**恰好一个** `role=initial, operator=assign, data={value: 标量常数或场引用}`：

- free-surface/immiscible/wetting/evaporation-condensation/boiling/cavitation：alpha、velocity；热相变另加 temperature。
- 四种分散：alpha、flux_a、flux_b。
- interphase-exchange：alpha、velocity、temperature_a、temperature_b、concentration_a、concentration_b。
- melting-solidification：velocity、temperature（α 从温度计算）。

每例恰好一个 `role=source, variable=acceleration, operator=assign, location=全域, data={value:{field:...}}`。即使零重力也必须显式给零向量场。

每个外边界实体必须恰好被一个 `role=boundary, variable=flow` 条件覆盖，不能用不同 tag 为同一几何面叠加条件；不得使用内部面。没有 material 条件。支持：

| operator | data 完整键与语义 |
|---|---|
| wall（非热） | `{mechanical:{option:no_slip}}`；wetting 改为 option=navier_wetting；分散相 b 用上述无穿透/切向滑移，不另提供第二条件 |
| wall（热） | mechanical 同上；另在 `{thermal:{option:adiabatic}}` 与 `{temperature:带单位常数或temperature场引用}` 中二选一；温度壁固定 Tw，绝热表示各相/混合导热向外通量零。没有隐藏热源；热由初态或热壁面驱动。溶质壁面永远零通量 |
| pressure_reservoir | 仅蒸冷/沸腾/空化；`{alpha:数值数据}`，热相变另必须有 temperature 数值数据。牵引为 `−pressure_reference n`，黏性切向牵引为零；流出时 α、温度法向导数为零，流入时用给定值；无额外规定法向速度。输入 α 是储槽来流相状态，不是强制流出相含率 |

蒸冷的储槽alpha必须在每个给定边界实体上恒定为纯相0或1：允许带单位常数，或time=constant的单帧、空间piecewise_constant/uniform场；禁止随时间切换纯相及任何分数含率插值。该纯相标签同时确定来流所用相物性。沸腾/空化的储槽alpha仍允许[0,1]分数和协议规定的线性时间变化；不可将尖锐界面限制机械施加于均匀混合模型。

pressure_reservoir 至少一个，余边界可为 wall。全部其他模型仅 wall。无滑移墙允许由瞬态重力/初态驱动；不是仅限静止解。初态的散度、边界相容、材料适用范围及连续问题可解性由数据制作方负责，检查器不通过数值投影偷偷修正初态。

下例仅是条件片段，location/field 必须在真实清单中声明，不是完整样例：

```json
{"role":"boundary","variable":"flow","location":"heated_wall","operator":"wall","data":{"mechanical":{"option":"no_slip"},"temperature":{"value":370.0,"unit":"K"}}}
```

## 输出与工程观测

必需输出恰好每个 quantity 一份，全部在初态同一全域 location 上，float64、average、单位/分量按上表；均使用同一输出时间轴，位于闭区间内且最后时刻必须为 time_end。可以包含起始时刻，但pressure和派生phase_change_rate在time_start的观测必须是连续问题确定的**有限且唯一右迹**（对单元平均亦如此）。制作方必须证明初边界和界面运动学/热跳跃足以给出该右迹；例如不能把不相容初始速度直接当作蒸冷界面解。若不存在有限唯一右迹或未建立其证据，输出轴不得包含time_start；所有输出共用一轴，必须一起从严格正的物理演化时间后请求。缺少该证据不能以低残差、离散步长有限值或随意选择初始压力/差分相变率代替。检查器只核查时轴声明，不求解右迹或验证制作方证据。

| 模型 | 输出 quantity 集合 |
|---|---|
| free-surface、immiscible、wetting | alpha、velocity、pressure |
| 四种分散模型 | alpha、flux_a、flux_b、pressure |
| interphase-exchange | alpha、velocity、pressure、temperature_a、temperature_b、concentration_a、concentration_b |
| evaporation-condensation、boiling | alpha、velocity、pressure、temperature、phase_change_rate |
| cavitation | alpha、velocity、pressure、phase_change_rate |
| melting-solidification | alpha、velocity、pressure、temperature、phase_change_rate |

alpha和phase_change_rate的真实单元平均乘单元体积，可精确复算相体积、常相密度下的相质量与总相变率（仅含浮点/已声明观测误差）；二维积分为每单位出平面厚度量。分散动量由直接报告的相通量均值线性组合 `rho_a*flux_a+rho_b*flux_b` 可精确积分；被动模型的颗粒反馈不计入载液方程。共速变密度动量rho*u、每相溶质量alpha_i*c_i、热量/焓中的alpha_i*T_i等是乘积量：**各因子的单元均值乘积一般不等于乘积的单元均值**。因此本输出集合只能以重建近似估计这些整体量，不能声称精确复算或据此执行严格守恒判分；若后续需要严格诊断，必须另行定义并验证相应守恒量观测。此限制不通过暗加未声明输出规避。界面总面积不能由体积分数数组唯一确定，故首版不将未定义的面积重建作为输出要求。不会给整体量伪造点坐标，也不要求模型内部相界面平滑函数。输出装配遵从 CONTRACT，不增加包外文件。

## SDK 与验证边界

`caeoj.fluid_multiphase.multiphase_parameters(problem)` 原样读取参数数值，不换单位。`multiphase_phase_mass(problem, alpha, cell_measures, phase='a')` 接受末轴为单元的 α 数组（调用方显式从 [T,N,1] 取 [...,0]）、正物理体积/二维面积 [N]，返回 rho*sum(fraction*measure)；支持 phase='b'，free-surface 的无质量气区不支持。它不从节点数量猜体积，也不验证调用方的几何积分精度。

`check_fluid_multiphase` 在通用结构/引用检查通过后执行，错误类别 E_FLUID。它核查 model、独立参数集合/单位/范围、维度、外面覆盖、初态、时间覆盖、quantity 组合和不相容声明。它不求解方程，不证明物理适定、网格精度、离散相轨迹、全程体积分数范围或参考真实性。

最小合法接口 fixture、非法组合与独立相质量手算预期由 `python -m unittest discover -s tests -p 'test_fluid_multiphase.py'` 临时生成/验证；该命令只在临时目录写网格和 HDF5，不为题库生成 examples/references/cases，也不发布评测。

维护补注：尖锐蒸冷输出 j δ_interface 的单元平均时，与流体单元公共面重合的界面测度各分配一半给两侧单元；相变界面不在外部储槽边界上占据正面积。熔凝 phase_change_rate 除起点有限唯一右迹外，仅在单元平均物质导数存在有限唯一经典值的时刻请求，不对左右导数不同的相线折点强行输出。
