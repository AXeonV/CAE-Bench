# 流体降维、稀薄与记忆材料配置 v1

本文规范 2.8—2.11 的首版给定模型。使用通用 [CONTRACT](CONTRACT.md) 的既有 physics、conditions、fields、outputs 和 aggregate 结构，不启用 CFD 的四键声明。`physics.model` 必须是下表完整版本标识，未知 `fluid-reduced-` 名称拒绝。题号不决定物理；模型版本决定物理。没有缺省参数或自动单位换算。相同 JSON 的物理解释不随章节、来源软件或求解方法改变。

## 1. 共用几何、数组及采样

一个连通固定域，一个 Gmsh MSH 4.1 ASCII 一阶单纯形网格：2D 三角形与边界线段，3D 四面体与边界三角形。坐标 m，时间 s。`locations.domain` 必须是恰含所有网格节点的 mesh/node location。外边界必须全部导出，法向由域内部指向外部；边界条件使用真实 mesh/element、dimension=D-1 的 location，以不相交分区恰好覆盖全部外边界。位置名字不携带边界物理意义。非2D平面降维题的二维量按单位出平面厚度；薄膜与浅水的2D平面是实际水平面积，不再乘单位厚度。

域条件用 location=`domain`，data 恰为 `{"value":{"field":"..."}}` 或非初态的标量SI常数。物理初态必须是场，时间轴单帧 `[start_time]`。矢量／张量条件必须引用字段，不允许JSON内联矢量。边界字段的 location 与条件完全一致。各输入场只通过一个或多个明确的条件被赋予物理角色；不接受未使用输入场。字段quantity必须等于所引用域变量名；边界data.value的字段quantity等于条件variable，其余边界data键的字段quantity等于该键名。域节点场 `value_kind=point`，sampling.space=`piecewise_linear`，用网格线性形函数连续重建；边界面场 `value_kind=average`，sampling.space=`piecewise_constant`，每个面常值。标量均匀常数只用 `{value,unit}`。完整张量按全局笛卡尔分量，二维构象是2×2平面块，未求的Azz=1、Axz=Ayz=0，迹及弹性能相当于三维平面流；对称容差1e-12仅用于输入诊断，不改变材料数学定义。

所有输入必须有 sampling，extrapolation=`forbid`。初态及单帧常量用time=`constant`（在整个物理区间恒定，初态仅赋值起点）；多帧非初态用time=`linear`、覆盖完整起止区间，相邻样本线性插值。稳态所有时间轴单帧 `[0]`。瞬态参数明确 start_time/end_time，输出时刻都在该闭区间内，不决定内部时间步。连续条件交界处及初态需物理相容，制造方负责适定性；校验器不证明它。

## 2. 模型及精确参数集合

每个参数为 `{value:有限数,unit:下表代码}`，不得省略或增添。除下述例外，全部参数严格正；reference_pressure、cavitation_pressure、start_time、end_time、temperature_coefficient 可为有限实数，但绝对空化压力另须正；drag_rate、bottom_drag、interface_drag、heat_transfer、breakdown、slip_length、temperature_jump_length 非负。end_time>start_time；zero_viscosity≥infinite_viscosity；lower_density>upper_density。等温滑移的temperature_jump_length必须为0。温度移位系数允许正负，但数据保证运行状态中的黏度有限且正。

### `fluid-reduced-liquid-lubrication-v1`

2D，稳态；求薄隙内不可压缩牛顿液体的压力及质量守恒空化占据率。给定上下壁面切向运动及间隙，不求固体变形。允许满膜与空化区共同存在；不能将负压简单截断后丢失质量。

参数：`density` (kg/m3)；`viscosity` (Pa.s)；`reference_pressure` (Pa)；`cavitation_pressure` (Pa)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `gap`：`material/geometry`，`m`，scalar，positive。
- `lower_velocity`：`material/geometry`，`m/s`，vector，finite。
- `upper_velocity`：`material/geometry`，`m/s`，vector，finite。

支持观测：`pressure`, `film_fraction`, `film_flux`, `load`。

### `fluid-reduced-gas-film-v1`

2D，瞬态；求等温理想气体在给定薄隙与壁面运动下的瞬态压力、密度和厚度积分体积通量。无滑移、无稀薄修正；本题的压缩储存与2.10的分子非平衡能力不同。

参数：`viscosity` (Pa.s)；`specific_gas_constant` (J/(kg.K))；`reference_temperature` (K)；`reference_pressure` (Pa)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `gap`：`material/geometry`，`m`，scalar，positive。
- `lower_velocity`：`material/geometry`，`m/s`，vector，finite。
- `upper_velocity`：`material/geometry`，`m/s`，vector，finite。
- `pressure`：`initial/assign`，`Pa`，scalar，positive。

支持观测：`pressure`, `density`, `film_flux`, `load`。

### `fluid-reduced-thermal-film-v1`

2D，瞬态；求固定密度牛顿液体薄膜中的压力与厚度平均温度，包含温黏反馈、剪切耗散及向两壁散热。采用本题公开的温度跨隙均匀闭合，不额外求跨隙温度剖面；不含空化。

参数：`density` (kg/m3)；`viscosity` (Pa.s)；`reference_pressure` (Pa)；`heat_capacity` (J/(kg.K))；`conductivity` (W/(m.K))；`reference_temperature` (K)；`temperature_coefficient` (1/K)；`heat_transfer` (W/(m2.K))；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `gap`：`material/geometry`，`m`，scalar，positive。
- `lower_velocity`：`material/geometry`，`m/s`，vector，finite。
- `upper_velocity`：`material/geometry`，`m/s`，vector，finite。
- `temperature`：`initial/assign`，`K`，scalar，positive。
- `wall_temperature`：`material/geometry`，`K`，scalar，positive。

支持观测：`pressure`, `temperature`, `film_flux`, `load`。

### `fluid-reduced-nonnewtonian-film-v1`

2D，稳态；求Carreau无记忆液体薄膜压力和积分通量。跨隙剪切响应由公开材料固定，不能用任意有效黏度替代。等温、满膜，无结构状态；与2.11的历史演化有别。

参数：`density` (kg/m3)；`reference_pressure` (Pa)；`zero_viscosity` (Pa.s)；`infinite_viscosity` (Pa.s)；`time_constant` (s)；`power_index` (1)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `gap`：`material/geometry`，`m`，scalar，positive。
- `lower_velocity`：`material/geometry`，`m/s`，vector，finite。
- `upper_velocity`：`material/geometry`，`m/s`，vector，finite。

支持观测：`pressure`, `film_flux`, `load`。

### `fluid-reduced-fully-wet-steady-v1`

2D，稳态；求非平坦底面上单层水体的定常水深与深度平均水平速度，含线性底摩擦。求真正定常解；无物理初态。全域严格正水深，不要求非静水修正。

参数：`density` (kg/m3)；`gravity` (m/s2)；`drag_rate` (1/s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `bed`：`material/geometry`，`m`，scalar，finite。

支持观测：`depth`, `velocity`, `water_flux`, `water_volume`。

### `fluid-reduced-fully-wet-transient-v1`

2D，瞬态；从给定水深与水平速度初态演化全湿单层浅水，包含床坡、重力波和底摩擦。水深在整个观测区间保持严格正值；守恒弱解及熵条件见协议。

参数：`density` (kg/m3)；`gravity` (m/s2)；`drag_rate` (1/s)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `bed`：`material/geometry`，`m`，scalar，finite。
- `depth`：`initial/assign`，`m`，scalar，positive。
- `velocity`：`initial/assign`，`m/s`，vector，finite。

支持观测：`depth`, `velocity`, `water_flux`, `water_volume`。

### `fluid-reduced-wetting-drying-v1`

2D，瞬态；求单层浅水的湿润扩展和退水，允许初态与演化中的干区。干床状态、守恒变量和速度观测约定明确固定；不将任意数值干湿阈值作为物理参数。

参数：`density` (kg/m3)；`gravity` (m/s2)；`drag_rate` (1/s)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `bed`：`material/geometry`，`m`，scalar，finite。
- `depth`：`initial/assign`，`m`，scalar，nonnegative。
- `velocity`：`initial/assign`，`m/s`，vector，finite。

支持观测：`depth`, `velocity`, `water_flux`, `water_volume`。

### `fluid-reduced-two-layer-v1`

2D，瞬态；求稳定分层的两层不可混溶水体，每层有独立厚度与深度平均速度，含床面及相间摩擦。首版限定光滑全湿、双曲稳定解，不含混合、卷吸、冲击、非静水或层消失。

参数：`lower_density` (kg/m3)；`upper_density` (kg/m3)；`gravity` (m/s2)；`bottom_drag` (1/s)；`interface_drag` (kg/(m2.s))；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `bed`：`material/geometry`，`m`，scalar，finite。
- `lower_depth`：`initial/assign`，`m`，scalar，positive。
- `lower_velocity`：`initial/assign`，`m/s`，vector，finite。
- `upper_depth`：`initial/assign`，`m`，scalar，positive。
- `upper_velocity`：`initial/assign`，`m/s`，vector，finite。

支持观测：`lower_depth`, `upper_depth`, `lower_velocity`, `upper_velocity`, `water_volume`。

### `fluid-reduced-isothermal-slip-v1`

2D，稳态；求单原子理想气体连续介质的黏性可压缩等温流动，壁面服从给定一阶应力滑移长度。保持所有温度为给定正常数，不求能量；不以无滑移代替滑移。

参数：`molecule_mass` (kg)；`molecule_diameter` (m)；`reference_temperature` (K)；`slip_length` (m)；`temperature_jump_length` (m)；`reference_pressure` (Pa)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

无域初态或物性场；全部材料由带单位参数给定。

支持观测：`density`, `velocity`, `pressure`, `traction`。

### `fluid-reduced-thermal-slip-v1`

2D，稳态；求单原子理想气体黏性可压缩流动与能量，含壁面一阶速度滑移和温度跳跃。材料传输、气壁长度由输入显式固定；本题不含热蠕移项。

参数：`molecule_mass` (kg)；`molecule_diameter` (m)；`reference_temperature` (K)；`slip_length` (m)；`temperature_jump_length` (m)；`reference_pressure` (Pa)；`heat_conductivity` (W/(m.K))。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

无域初态或物性场；全部材料由带单位参数给定。

支持观测：`density`, `velocity`, `pressure`, `temperature`, `heat_flux`, `traction`。

### `fluid-reduced-transition-gas-v1`

3D，稳态；求三维单原子硬球气体的稳态Boltzmann输运，二体弹性碰撞和气壁散漫／镜面混合反射均由输入固定。宏观温度允许空间变化；不以连续体闭合代替指定碰撞问题。

参数：`molecule_mass` (kg)；`molecule_diameter` (m)；`reference_temperature` (K)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

无域初态或物性场；全部材料由带单位参数给定。

支持观测：`density`, `velocity`, `temperature`, `pressure`, `traction`, `heat_flux`。

### `fluid-reduced-free-molecular-v1`

3D，稳态；求三维无分子间碰撞的稳态输运，保留完整气壁散射与储槽注入。允许多次壁面反射；不能假定所有分子只飞行一次。分子直径仍显式提供，用于适用性记录，不参与碰撞项。

参数：`molecule_mass` (kg)；`molecule_diameter` (m)；`reference_temperature` (K)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

无域初态或物性场；全部材料由带单位参数给定。

支持观测：`density`, `velocity`, `temperature`, `pressure`, `traction`, `heat_flux`。

### `fluid-reduced-viscoelastic-steady-v1`

2D，稳态；求等温不可压缩Oldroyd-B流体的定常速度、静压和构象张量。聚合物记忆状态与入口构象由材料历史决定；无物理初值，不允许把构象默认重置为单位阵。

参数：`density` (kg/m3)；`solvent_viscosity` (Pa.s)；`polymer_viscosity` (Pa.s)；`relaxation_time` (s)；`reference_pressure` (Pa)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

无域初态或物性场；全部材料由带单位参数给定。

支持观测：`velocity`, `pressure`, `polymer_stress`, `conformation`, `traction`。

### `fluid-reduced-viscoelastic-transient-v1`

2D，瞬态；从明确给定的速度与对称正定构象初态演化等温Oldroyd-B流动。构象初态不是数值初猜；不能仅给速度而丢失预应力历史。

参数：`density` (kg/m3)；`solvent_viscosity` (Pa.s)；`polymer_viscosity` (Pa.s)；`relaxation_time` (s)；`reference_pressure` (Pa)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `velocity`：`initial/assign`，`m/s`，vector，finite。
- `conformation`：`initial/assign`，`1`，tensor，spd。

支持观测：`velocity`, `pressure`, `polymer_stress`, `conformation`, `traction`。

### `fluid-reduced-thixotropic-transient-v1`

2D，瞬态；求含结构生成和剪切破坏的不可压缩触变液体流动，初始结构和入口结构均显式给出。结构本构为公开固定有限首版，不包括屈服或黏弹性。

参数：`density` (kg/m3)；`reference_pressure` (Pa)；`base_viscosity` (Pa.s)；`structure_viscosity` (Pa.s)；`build_time` (s)；`breakdown` (1)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `velocity`：`initial/assign`，`m/s`，vector，finite。
- `structure`：`initial/assign`，`1`，scalar，fraction。

支持观测：`velocity`, `pressure`, `structure`, `extra_stress`, `traction`。

### `fluid-reduced-thermal-generalized-newtonian-v1`

3D，瞬态；求三维不可压缩Carreau液体流动与温度，包含温黏反馈和黏性耗散。该题无记忆，区别于本节构象及触变能力，也区别于2.1的等温流变。

参数：`density` (kg/m3)；`reference_pressure` (Pa)；`zero_viscosity` (Pa.s)；`infinite_viscosity` (Pa.s)；`time_constant` (s)；`power_index` (1)；`heat_capacity` (J/(kg.K))；`conductivity` (W/(m.K))；`reference_temperature` (K)；`temperature_coefficient` (1/K)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `velocity`：`initial/assign`，`m/s`，vector，finite。
- `temperature`：`initial/assign`，`K`，scalar，positive。

支持观测：`velocity`, `pressure`, `temperature`, `extra_stress`, `traction`, `heat_flux`。

### `fluid-reduced-thermal-viscoelastic-v1`

2D，瞬态；从速度、温度及构象初态演化二维不可压缩热Oldroyd-B液体。黏度与松弛时间共享公开温度移位因子，聚合物弹性能与溶剂／松弛耗散分开记账；不含相变或化学反应。

参数：`density` (kg/m3)；`solvent_viscosity` (Pa.s)；`polymer_viscosity` (Pa.s)；`relaxation_time` (s)；`reference_pressure` (Pa)；`heat_capacity` (J/(kg.K))；`conductivity` (W/(m.K))；`reference_temperature` (K)；`temperature_coefficient` (1/K)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `velocity`：`initial/assign`，`m/s`，vector，finite。
- `conformation`：`initial/assign`，`1`，tensor，spd。
- `temperature`：`initial/assign`，`K`，scalar，positive。

支持观测：`velocity`, `pressure`, `temperature`, `polymer_stress`, `conformation`, `traction`, `heat_flux`。

## 3. 给定连续物理与闭合

以下为指定材料／物理模型，数值算法自由；不以来源配置补足方程。∇、div在实际求解坐标上计算。Lij=∂ui/∂xj，D=(L+Lᵀ)/2，γ=sqrt(2D:D)。除明确给定的重力与壁面外无体力、质量源、热源、粗糙度、旋转或反应。

### 3.1 薄膜

z∈[0,h]为真实跨隙方向，输入lower_velocity/upper_velocity是面内速度U0/U1；下壁z=0，上壁z=h。忽略跨隙压力梯度、惯性和面内黏性扩散，无滑移，薄隙渐近模型；几何与运动满足薄膜假设，壁面法向运动通过给定h的时间导数表示，不改变2D计算域。普通牛顿满膜 q=−h³∇p/(12μ)+h(U0+U1)/2，q单位m²/s；不可压缩质量方程∂t h+div q=0（稳态去掉时间项）。p为绝对静压，载荷为∫域(p−reference_pressure)dA，向上为正，单位N。所有侧边给定film_pressure。间隙h使用分片线性时间重建时，内部采样结点的∂t h取右侧分段导数，起点取右迹，最终端点取左迹；单帧恒定h的导数为0。依赖该导数的瞬时压力、通量及载荷也使用同一时间迹约定，不对相邻左右答案取平均。

液体空化题采用质量守恒的充满率θ：p≥pc、0≤θ≤1、(p−pc)(1−θ)=0，q=−h³∇p/(12μ)+hθ(U0+U1)/2，稳态div q=0；pc=cavitation_pressure。θ是以液体密度计的薄膜占据率，不是可压缩液体密度。在空化区输运方向由平均壁速决定，采用上游充满率的守恒弱解，滞止未定区域不纳入算例；入口边界fraction给出从域外进入的θ，仅在对流入流分支生效，满膜p>pc边界的fraction必须为1。边界p不能低于pc，边界p=pc时允许0≤fraction≤1。

气膜：ρ=p/(R Tref)，μ为常数，∂t(ρh)+div(ρq)=0；初始压力严格正，无空化和滑移；h可随时间变化。所有p、T为绝对量。

热液膜：ρ为常数，μ(T)=viscosity·a(T)，a(T)=exp[−temperature_coefficient(T−Tref)]。厚度均匀T的闭合为ρcp[h∂t T+q·∇T]=div(k h∇T)+Φ−2H(T−Tw)，H=heat_transfer，Tw=wall_temperature（两壁相同）。Φ=h³|∇p|²/(12μ)+μ|U1−U0|²/h；两项均按单位平面面积的功率计。侧边温度采用data.temperature Dirichlet，包含进出流；wall_temperature是给定面内场不是求解固体。无空化、无压力功或热膨胀。

Carreau薄膜：μ(γ)=μinf+(μ0−μinf)[1+(τγ)²]^((n−1)/2)。在每个面内位置解跨隙局部边值问题 ∂z[μ(|∂z u|)∂z u]=∇p，u(0)=U0、u(h)=U1；q=∫0^h u dz。γ此处为跨隙速度梯度模长，这是忽略小量后的sqrt(2D:D)。满膜div q=0。不能将牛顿通量公式直接代入任意标称黏度。

### 3.2 浅水

底高程b=bed，向上为正；水深h≥0、自由面η=b+h、q=h u。单层：∂t h+div(hu)=0；∂t(hu)+div(hu⊗u+g h²I/2)=−g h∇b−drag_rate·hu。材料恒密度，气压均匀并消去，无科氏力、风、降雨、入渗或黏性横向扩散。全湿题h严格正。干湿题用非负水深的守恒熵解，h=0时hu=0且输出u=0，不规定数值干湿阈值。静止干床与水面相容；床面连续分片线性。不连续水流采用满足物理能量不增的熵弱解。节点点值只在唯一连续迹存在处请求；数据保证观测节点不落在激波/接触跳跃或速度无唯一极限的干湿前沿上，不能用某个数值单元平均冒充点值。

两层下标l/u，ρl>ρu，r=ρu/ρl。每层满足∂t hj+div(hj uj)=0；Dl ul=−g∇(b+hl+r hu)−bottom_drag ul+K(uu−ul)/(ρl hl)；Du uu=−g∇(b+hl+hu)−K(uu−ul)/(ρu hu)，K=interface_drag，Dj=∂t+uj·∇。下层与床接触，上层与空气接触；无层间质量交换或扩散。限定光滑双曲稳定全湿解，避免对非守恒跨跃积作隐藏选择。

水墙为不可穿透自由滑移（每层u·n=0）。储槽边界data给出外部状态，按法向一维浅水Riemann问题连接内部和储槽状态，只注入入射特征；流出特征取内部状态，切向速度随入流取储槽、出流取内部。单层不把全部储槽状态一律强制为Dirichlet。两层首版不支持亚临界或混合入射特征储槽，边界只允许layer_inlet完整超临界入流、layer_outflow完整超临界纯出流及layer_wall。layer_inlet直接指定两层h与完整水平u，四个状态场使用同一时间轴，标量常数允许；layer_outflow不指定外部状态，只允许内部信息流出。以外法向n定义vl=ul·n、vu=uu·n，四个重力波特征为矩阵[[vl,0,hl,0],[0,vu,0,hu],[g,r g,vl,0],[g,g,0,vu]]的特征值，另有切向平流特征vl、vu。入流全部特征严格负且实，出流全部严格正且实，禁止零速/复数及区间内分支改变。制造方保证这些严格符号在整个区间成立；检查器检验入流采样状态，不能证明时间插值和所求出流状态始终满足分支。稳态全湿至少有一个储槽，不纳入欠定的闭池总水量问题；瞬态可全墙。

### 3.3 滑移连续体与动理学

气体为单组分单原子、分子质量m、直径d、kB=1.380649e−23 J/K、R=kB/m、cv=3R/2。滑移题解稳态可压缩质量／动量守恒，ρ=p/(R T)，σ=−pI+μ(L+Lᵀ−(2/3)divu I)，μ(T)=5 sqrt(m kB T/π)/(16 d²)。二维仍是三维分子的平面空间流动，体黏度为零。等温T=Tref；热滑移解ρcv u·∇T=−p divu+τ:L+div(k∇T)，k=heat_conductivity；不是等温求解后再输出给定温度。速度滑移墙u·n=Uw·n=0，(u−Uw)t=−slip_length·(σn)t/μ，热墙T−Tw=−temperature_jump_length·∂nT；长度为给定材料气壁参数，模型不含热蠕移。壁面几何固定，Uw必须切向。入口给定速度及适用的温度；出口给定总牵引σn=−p_ext n（并非另外强制内部静压=p_ext），热出口∂nT=0。reference_pressure与reference_temperature为气体参考状态，仅用于定义参考平均自由程λref=m/(sqrt(2)πd²ρref)、ρref=reference_pressure/(R reference_temperature)，两者均须正；不再叠加压力均值约束。至少一处出口固定绝对压力；出口数据保证无回流。滑移输入与状态应处在一阶连续模型适用区，数据制作方记录Kn证据。

动理学f(x,c)为三维速度空间的分子数密度分布，n=∫f dc，ρ=mn，u=∫c f dc/n，T=m∫|c−u|²f dc/(3kB n)，p=nkB T。稳态c·∇x f=Q(f,f)。硬球题二体碰撞的总截面πd²，微分截面对立体角为d²/4；Q=∫R³∫S²(d²/4)|c−c*|[f(c′)f(c*′)−f(c)f(c*)]dΩdc*，c′=(c+c*)/2+|c−c*|ω/2，c*′=(c+c*)/2−|c−c*|ω/2。自由分子题Q=0；不使用BGK或未说明的碰撞频率。

气壁Uw切向固定：在壁面系w=c−Uw，明确定义fw(w)=f(Uw+w)。对进入气体的w·n<0，fw(w)=(1−α)fw,out(w−2(w·n)n)+α nw (m/(2πkBTw))^(3/2)exp[−m|w|²/(2kBTw)]；仅当α>0时nw由零净法向分子通量唯一决定；α=0时纯镜面项已满足零法向通量，不需要或定义nw。α=accommodation为镜面/完全热适应散漫反射的混合概率，0≤α≤1。储槽入流半空间c·n<0取由density、velocity、temperature定义的完整Maxwellian，出流取内部解；至少一处储槽。无需输入分布数组或伪造速度坐标：入射分布由这些明确物理参数解析定义，内部速度离散自选。数据保证储槽可达、无与储槽隔离的自由轨道支撑任意稳态存量。

### 3.4 记忆与热流变材料

所有2.11题不可压缩：divu=0、ρDtu=divσ；σ=−pI+τ。无体力。p为Pa静压：无traction_outlet时以域体积平均p=reference_pressure固定唯一规范；有出口时由给定牵引固定压力，reference_pressure仅用于记录基准而不再叠加平均约束。速度墙和入口给定Dirichlet；出口指定完整σn矢量。构象/结构只在真正入流指定，出口采用无入射记忆的自然对流，数据保证traction_outlet无回流；墙无穿透，不额外施加构象法向梯度。

Oldroyd-B：Dt A−LA−ALᵀ=−(A−I)/λ；τ=2ηsD+τp，τp=ηp(A−I)/λ。A必须对称正定；二维采用Azz=1平面解。稳态没有物理初态；入口必须提供构象。瞬态必须提供起点A，任何预伸长均保留；速度初态满足不可压缩和边界相容。无人工应力扩散，数值稳定化不得改变收敛目标。

触变：Dt ξ=(1−ξ)/build_time−breakdown·ξ·γ，0≤ξ≤1；μ=base_viscosity+structure_viscosity·ξ，τ=2μD。入口必须给ξ。结构不携带额外弹性应力，不产生屈服判据。

热模型在本节直接定义a(T)=exp[−temperature_coefficient(T−reference_temperature)]。热Carreau：μ(T,γ)=a(T){μinf+(μ0−μinf)[1+(τγ)²]^((n−1)/2)}；τ=2μD；ρcp DtT=div(k∇T)+2μD:D。温度初态必需，全部外边界另有temperature_wall Dirichlet，位置分区独立完整覆盖。

热Oldroyd：ηs(T)=ηs,ref a(T)、ηp(T)=ηp,ref a(T)、λ(T)=λref a(T)，故G=ηp/λ常数。τ同等温，构象方程用局部λ(T)。弹性自由能为G[tr A−ln det A−d]/2（平面中Azz=1贡献为零）；热方程ρcp DtT=div(k∇T)+2ηs D:D+G[tr(A+A⁻¹−2I)]/(2λ)。聚合物τp:D包含可逆储能，不能全部直接作为热源。无热膨胀，cp、k、ρ常数；壁温与初温均绝对K。

## 4. 全部边界算子与参数

下列每项role=boundary，列出的data键全部必需且不得添加其他键。scalar为带单位常数或同location标量场；vector/tensor只能为同location场；option是精确类别。变量/算子及数据格式为规范的一部分。

### `fluid-reduced-liquid-lubrication-v1`

- `film_pressure`，variable=`pressure`；data：`value`=scalar Pa positive; `fraction`=scalar 1 fraction。

### `fluid-reduced-gas-film-v1`

- `film_pressure`，variable=`pressure`；data：`value`=scalar Pa positive。

### `fluid-reduced-thermal-film-v1`

- `film_pressure`，variable=`pressure`；data：`value`=scalar Pa positive; `temperature`=scalar K positive。

### `fluid-reduced-nonnewtonian-film-v1`

- `film_pressure`，variable=`pressure`；data：`value`=scalar Pa positive。

### `fluid-reduced-fully-wet-steady-v1`

- `water_wall`，variable=`water`；data：`mode`=option(impermeable)。
- `water_reservoir`，variable=`water`；data：`depth`=scalar m positive; `velocity`=vector m/s finite。

### `fluid-reduced-fully-wet-transient-v1`

- `water_wall`，variable=`water`；data：`mode`=option(impermeable)。
- `water_reservoir`，variable=`water`；data：`depth`=scalar m positive; `velocity`=vector m/s finite。

### `fluid-reduced-wetting-drying-v1`

- `water_wall`，variable=`water`；data：`mode`=option(impermeable)。
- `water_reservoir`，variable=`water`；data：`depth`=scalar m positive; `velocity`=vector m/s finite。

### `fluid-reduced-two-layer-v1`

- `layer_wall`，variable=`layers`；data：`mode`=option(impermeable)。
- `layer_inlet`，variable=`layers`；data：`lower_depth`=scalar m positive; `lower_velocity`=vector m/s finite; `upper_depth`=scalar m positive; `upper_velocity`=vector m/s finite。

- `layer_outflow`，variable=`layers`；data：`mode`=option(supercritical_outflow)。

### `fluid-reduced-isothermal-slip-v1`

- `slip_wall`，variable=`gas`；data：`velocity`=vector m/s finite。
- `slip_inlet`，variable=`gas`；data：`velocity`=vector m/s finite。
- `slip_outlet`，variable=`gas`；data：`pressure`=scalar Pa positive。

### `fluid-reduced-thermal-slip-v1`

- `slip_wall`，variable=`gas`；data：`velocity`=vector m/s finite; `temperature`=scalar K positive。
- `slip_inlet`，variable=`gas`；data：`velocity`=vector m/s finite; `temperature`=scalar K positive。
- `slip_outlet`，variable=`gas`；data：`pressure`=scalar Pa positive。

### `fluid-reduced-transition-gas-v1`

- `gas_wall`，variable=`gas`；data：`velocity`=vector m/s finite; `temperature`=scalar K positive; `accommodation`=scalar 1 fraction。
- `gas_reservoir`，variable=`gas`；data：`density`=scalar kg/m3 positive; `velocity`=vector m/s finite; `temperature`=scalar K positive。

### `fluid-reduced-free-molecular-v1`

- `gas_wall`，variable=`gas`；data：`velocity`=vector m/s finite; `temperature`=scalar K positive; `accommodation`=scalar 1 fraction。
- `gas_reservoir`，variable=`gas`；data：`density`=scalar kg/m3 positive; `velocity`=vector m/s finite; `temperature`=scalar K positive。

### `fluid-reduced-viscoelastic-steady-v1`

- `velocity_wall`，variable=`velocity`；data：`value`=vector m/s finite。
- `velocity_inlet`，variable=`velocity`；data：`value`=vector m/s finite; `conformation`=tensor 1 spd。
- `traction_outlet`，variable=`traction`；data：`value`=vector Pa finite。

### `fluid-reduced-viscoelastic-transient-v1`

- `velocity_wall`，variable=`velocity`；data：`value`=vector m/s finite。
- `velocity_inlet`，variable=`velocity`；data：`value`=vector m/s finite; `conformation`=tensor 1 spd。
- `traction_outlet`，variable=`traction`；data：`value`=vector Pa finite。

### `fluid-reduced-thixotropic-transient-v1`

- `velocity_wall`，variable=`velocity`；data：`value`=vector m/s finite。
- `velocity_inlet`，variable=`velocity`；data：`value`=vector m/s finite; `structure`=scalar 1 fraction。
- `traction_outlet`，variable=`traction`；data：`value`=vector Pa finite。

### `fluid-reduced-thermal-generalized-newtonian-v1`

- `velocity_wall`，variable=`velocity`；data：`value`=vector m/s finite。
- `velocity_inlet`，variable=`velocity`；data：`value`=vector m/s finite。
- `traction_outlet`，variable=`traction`；data：`value`=vector Pa finite。
- `temperature_wall`，variable=`temperature`；data：`value`=scalar K positive。

### `fluid-reduced-thermal-viscoelastic-v1`

- `velocity_wall`，variable=`velocity`；data：`value`=vector m/s finite。
- `velocity_inlet`，variable=`velocity`；data：`value`=vector m/s finite; `conformation`=tensor 1 spd。
- `traction_outlet`，variable=`traction`；data：`value`=vector Pa finite。
- `temperature_wall`，variable=`temperature`；data：`value`=scalar K positive。

## 5. 观测、符号与必需输出

场名任意，quantity必须在模型允许列表。所有输出float64。全部模型的点观测只在物理场具有唯一连续迹的位置/时刻请求；依赖导数的应力、通量等还须有唯一相应空间/时间导数迹。尤其分片线性速度初态在单元交界节点常无唯一梯度，2.11初始extra_stress仅能在各邻接导数给出相同物理应力处请求，否则该节点时刻不得请求，不能默认为单元平均。气壁/储槽交角、边界分区交线及奇异角点若有多重迹或无界交换，不请求其点值；边界面平均仅在积分存在且唯一时请求。制造方负责并记录这些保证，结构校验不证明导数正则性。3.1明确的间隙时间结点单侧迹是唯一允许的指定迹例外。状态采用真实网格节点点值（可为子集），traction/heat_flux采用真实外边界面平均值，load/water_volume采用aggregate/source指向恰含全部域单元的location、operation=sum、value_kind=integral，单位分别为N与m³。其余输出不使用aggregate，不制造汇总探针。

pressure是连续体绝对/带固定规范静压或动理学p=nkBT；density是局部kg/m³，velocity是面内/空间速度m/s，temperature是绝对K。film_fraction为θ；film_flux为∫u dz，**气膜也为体积通量**而非质量通量。water_flux=h u，water_volume=∫h dA；两层water_volume=∫(hl+hu)dA。薄膜load定义见3.1。conformation为A无量纲完整张量；polymer_stress为τp，extra_stress为总偏应力τ；structure为ξ。

traction=σn，是域外作用于流体的力/面积（气体对壁面取相反号），单位Pa；二维常规流体若另作积分按单位出平面厚度。本版只要求traction面平均，不增加力的伪点。动理学壁面traction=−m∫c[(c−Uw)·n]f dc；仅在gas_wall上请求。heat_flux为向外法向热交换矢量：连续体[−k∇T·n]n，动理学为n(m/2)∫|c−Uw|²[(c−Uw)·n]f dc；动理学仅在gas_wall上请求，单位W/m²。滑移墙能量输出沿气体法向导热，不混入滑移机械功。壁面traction使用完整压力及黏性/非平衡动量交换。

所有模型至少请求主要状态：薄膜pressure（空化再加film_fraction、热膜再加temperature）；单层水depth+velocity；双层水的两个depth和velocity；连续体气体velocity+pressure（热题再加temperature）；动理学density+velocity+temperature；2.11的velocity+pressure，Oldroyd再加conformation+polymer_stress，触变再加structure，热题再加temperature。其余允许观测可选择，不要求没有请求的输出。各quantity单位如下。

| quantity | unit | kind |
|---|---|---|
| pressure | `Pa` | scalar |
| density | `kg/m3` | scalar |
| temperature | `K` | scalar |
| velocity | `m/s` | vector |
| film_fraction | `1` | scalar |
| film_flux | `m2/s` | vector |
| depth | `m` | scalar |
| lower_depth | `m` | scalar |
| upper_depth | `m` | scalar |
| lower_velocity | `m/s` | vector |
| upper_velocity | `m/s` | vector |
| water_flux | `m2/s` | vector |
| structure | `1` | scalar |
| conformation | `1` | tensor |
| polymer_stress | `Pa` | tensor |
| extra_stress | `Pa` | tensor |
| traction | `Pa` | vector |
| heat_flux | `W/m2` | vector |
| load | `N` | scalar |
| water_volume | `m3` | scalar |

## 6. SDK、验证和边界

`caeoj.fluid_reduced.reduced_parameters(problem)`读取明确常数；`reduced_viscosity(model,parameters,shear_rate,temperature=None,structure=None)`计算上述标量黏度（Oldroyd返回溶剂黏度，不把聚合物记忆压成有效黏度）；`maxwellian(n,u,T,m,c)`计算三维数分布，单位s³/m⁶。模块还提供`reduced_time_derivative(times,values,time)`，按第3.1节取分片线性时间导数的右迹/末端左迹；`layer_characteristic_speeds(hl,hu,vl,vu,g,r)`返回两层四个重力波速度和两个切向平流速度，仅检验给定状态，不求解边界演化。无量纲化、插值、内部分子速度网格和流动求解由考生负责。通用Problem/结果写出保留真实编号与轴。

检查器 `check_fluid_reduced(problem, errors)`在通用检查通过后执行；E_FLUID报告精确模型/参数集合、单位及范围、网格维度与边界覆盖、条件参数/角色/场引用、采样、初态、输出组合等声明错误。检查不求解PDE，也不证明Kn适用性、薄隙比、全湿性、双曲稳定、稳态存在、参考准确性或预算可解性。制造方必须独立验证这些保证。

协议最小fixture仅在临时目录生成：运行 `.venv/bin/python -m unittest discover -s tests -p test_fluid_reduced.py`。测试中逐模型生成真实MSH/HDF5/problem.json，通过公开validate_input；错误变体验证拒绝；材料计算与Maxwellian采用独立手算预期。它们不是题目examples或数值参考；未提供题库数据，无评测发布。旧模型不启用本检查器，已有旧CFD结构与解释不迁移。
