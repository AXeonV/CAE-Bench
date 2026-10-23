# 固流能量观测数据

通用结构、数组格式及输出支持量遵循 [CONTRACT](../../../../docs/CONTRACT.md)。每例为一个实验，入口为 `problem.json`，数据文件固定 `input.h5`，`task=solid-fluid-energy-observation-repair`。下面完整定义本题模型、输入、实际观测和符号。

## 声明、身份与时间

`geometries={}`、`meshes={}`、`conditions=[]`。几何和网格由本节参数交给固定真实库生成，无外部网格文件。`locations` 恰为 `{"experiments":{"kind":"entities","ids":"experiment_ids"}}`，其中 `experiment_ids` 为 int64[1]，值为 `[1]`。该实体表示一次整体实验，不是网格节点、空间点或单元。

`time_axes` 恰为 `{"initial":"initial_time","frames":"times"}`。`initial_time` 为 float64[1]、值 `[0]`，单位s，仅供两组输入系数引用。`times` 为 float64[nt]，单位s；显式场和稳态均为 `[0]`，瞬态为 `[0,dt,2dt,…,step_count*dt]`，各值由整数序号乘dt生成。稳态的逻辑0表示收敛终场，原生求解器的稳态伪时间不作为物理瞬态时间。瞬态0表示原生初始场，随后为每个隐式Euler步终场，不能跳过初态或插值重采样。

`physics.model` 只允许以下十个字符串。模型名明确指定坐标、执行分支及材料接口；不另传数字类别参数。

|模型|维度D|执行分支|材料接口|
|---|---|---|---|
|explicit-cartesian-normal-standard-v1|3|显式有限元场|普通、标准属性名|
|explicit-cartesian-normal-renamed-v1|3|显式有限元场|普通、重命名属性|
|explicit-cartesian-ad-standard-v1|3|显式有限元场|AD、标准属性名|
|explicit-cartesian-ad-renamed-v1|3|显式有限元场|AD、重命名属性|
|explicit-rz-normal-standard-v1|2|显式有限元场|普通、标准属性名|
|explicit-rz-normal-renamed-v1|2|显式有限元场|普通、重命名属性|
|explicit-rz-ad-standard-v1|2|显式有限元场|AD、标准属性名|
|explicit-rz-ad-renamed-v1|2|显式有限元场|AD、重命名属性|
|coupled-rz-steady-v1|2|固流耦合稳态|AD、标准属性名|
|coupled-rz-transient-v1|2|固流耦合瞬态|AD、标准属性名|

`spatial_dimension=D`。标准属性名为比热 `cp`、密度 `rho`；重命名为 `heat_capacity`、`mass_density`，由原生接口的cp/rho参数显式选择。属性名变化不改变物理量、数值或单位。

## 全部标量参数

`physics.parameters` 恰含下表所有键，每项为 `{"value":有限标量,"unit":"表中代码"}`。计数及阶次取整数；不使用缺省值。带下标s/f分别指固体／流体。

|键|精确单位代码|范围或含义|
|---|---|---|
|length_x, length_y|m|各为0.1至1，分别记Lx、Ly|
|length_z|m|Cartesian为0.1至1，记Lz；RZ精确为0|
|nx|1|x方向单元数，4、6或8|
|ny|1|y方向单元数，2至8|
|nz|1|Cartesian的z方向单元数2至8；RZ精确为0|
|density_solid, density_fluid|kg/m3|ρs、ρf；显式族1至2000，耦合族1至20|
|specific_heat_solid, specific_heat_fluid|J/(kg*K)|cs、cf；显式族1至5000，耦合族1至20|
|conductivity_solid, conductivity_fluid|W/(m*K)|ks、kf；显式族均为1，耦合族各0.5至5|
|viscosity|Pa*s|μ；显式族为1，耦合族0.1至2|
|heat_transfer_coefficient|W/(m2*K)|h；显式族为1，耦合族0.5至5|
|temperature_reference|K|Tref；显式族为300，耦合族250至350|
|inlet_speed|m/s|U；显式族为0，耦合族0.1至1|
|source_constant, source_radial, source_axial|W/m3|s0、sr、sz；显式族各−100至100，耦合族各0至10且至少一项大于0|
|source_time_slope|1/s|α；显式／稳态为0，瞬态0至1|
|dt|s|显式／稳态为0；瞬态0.05至0.2|
|step_count|1|显式／稳态为0；瞬态整数1至4|
|velocity_order|1|显式族为2；耦合族为1或2|

耦合族另满足 `ρf*U*(Lx/2)/μ≤10`。所有物性在本相内均匀且恒定，温度依赖、浮力、重力、黏性耗散及相变均不在范围。

Cartesian域为 `[0,Lx]×[0,Ly]×[0,Lz]`。RZ域为 `[0,Lx]×[0,Ly]`，`r=x`、物理轴向坐标为y，绕全局y轴旋转；真实体积测度为 `dV=2πr dr dy`，外圆柱侧壁面积测度为 `dA=2πLx dy`。本题没有二维平面单位厚度约定。均匀网格分别为HEX27和QUAD9几何单元；x方向前一半为固体Ωs、后一半为流体Ωf，界面x=Lx/2与单元面重合、测度为零。

## 两组输入系数

`fields` 恰有下表两项。每项 `array=quantity=字段名`，`location=experiments`、`time_axis=initial`、`dtype=float64`、`kind=components`、`value_kind=point`，`sampling={"space":"uniform","time":"constant","extrapolation":"forbid"}`。它们是同一实验的多项式系数，不是把网格场或整体积分假装成采样点；没有空间／时间插值。

|字段／HDF5 key|单位|shape／component_shape|components顺序|
|---|---|---|---|
|temperature_coefficients|K|[1,1,10]／[10]|constant, xi, eta, zeta, xi2, xi_eta, xi_zeta, eta2, eta_zeta, zeta2|
|velocity_coefficients|m/s|[1,1,12]／[12]|x_constant, x_xi, x_eta, x_zeta, y_constant, y_xi, y_eta, y_zeta, z_constant, z_xi, z_eta, z_zeta|

显式族令 `ξ=x/Lx`、`η=y/Ly`、`ζ=z/Lz`；RZ时ζ=0。温度系数依次乘 `[1,ξ,η,ζ,ξ²,ξη,ξζ,η²,ηζ,ζ²]` 并求和。首系数为250至350，其余各为−10至10。速度系数按全局x/y/z分成三行，每行四个，分别乘 `[1,ξ,η,ζ]` 并求和，各系数−1至1。RZ温度的zeta、xi_zeta、eta_zeta、zeta2系数及所有速度zeta系数、整个z速度分量均精确为零。

温度在两相均定义，速度只在流体定义。真实MOOSE以SECOND/LAGRANGE温度Aux变量和SECOND/LAGRANGE_VEC速度Aux变量插值给定函数，随后直接调用原生后处理器；该族不求解传热或动量PDE，没有边界或Robin模型。固体体热源为 `s=s0+sr*ξ+sz*η`。五项输出在同一逻辑时刻0观测，Robin功率定义为0。

耦合族两组系数数组仍必须存在且所有项精确为零，表示本族不使用显式多项式系数；实际初边值由下一节定义。

## 固流耦合模型和离散责任

仅RZ、无旋流。流体满足不可压缩质量守恒与无体力Navier–Stokes动量方程，固体不流动。温度为两相共用的连续变量，固体满足 `ρs cs ∂tT−div(ks grad T)=s`，流体满足 `ρf cf(∂tT+u·grad T)−div(kf grad T)=0`；稳态去除时间项。源仅在固体，为 `(s0+sr*ξ+sz*η)*(1+αt)`。界面温度连续、法向导热连续，无接触热阻。

入口y=0的流体速度为 `u_x=0`、`u_y=4Uχ(1−χ)`，其中 `χ=(x−Lx/2)/(Lx/2)`。流体内外壁x=Lx/2、Lx速度均为零。出口y=Ly采用固定库Laplace黏性形式与分部积分压力的自然条件，即 `(μ grad u−p I)n=0`，这里n为流体向外法向；不另加作者压力锚定。径向及轴向导数由原生RZ实现处理。初始流体内部速度为 `(1e−15,1e−15,0) m/s`，边界速度由上述Dirichlet值覆盖；不是先求一个稳态初场。

温度初值在两相均为Tref。外圆柱壁r=Lx满足 `−kf grad T·n=h(T−Tref)`，其余外边界为零向外导热通量，包括轴、底面和顶面；入口不额外指定温度。稳态初始温度仅为求解初猜。源为正表示加热，Robin功率为正表示向外散热；实际离散场可局部低于Tref，不裁剪小负散热值。

方法固定为原生MOOSE连续有限元：温度和压力FIRST/LAGRANGE，速度按velocity_order为FIRST或SECOND/LAGRANGE_VEC；QUAD9几何不将低阶变量变成二阶变量。使用原生INSADMass及PSPG、INSADMomentumAdvection/Viscous/Pressure及SUPG、INSADEnergyAdvection及SUPG、ADHeatConduction、INSADStabilized3Eqn，稳定化倍率alpha=1，黏性采用laplace形式、压力分部积分。瞬态增加原生动量和两相热时间导数，隐式Euler以步终源及通量求解；Newton及直接LU处理原离散方程。原生输入模板固定这些方法设置，可信运行器只传入本题参数并读取求解结果。要求修复后处理接口并保持该离散求解过程；不要求考生重新选择离散模型。

## 全部输出

`outputs` 恰有下表五项，均为float64、`array=quantity=输出名`、`location=experiments`、`time_axis=frames`、`kind=scalar`、`component_shape=[1]`、`components=["value"]`、`value_kind=point`，shape为 `[nt,1,1]`。实验实体上的数值定义为以下积分，不是空间点值。

|输出／HDF5 key|单位|定义|
|---|---|---|
|energy_solid|J|`Es=∫Ωs ρs cs T dV`|
|energy_fluid|J|`Ef=∫Ωf ρf cf T dV`|
|advection_power|W|`Qadv=∫Ωf ρf cf u·grad T dV`|
|source_power|W|`Qsrc=∫Ωs s dV`|
|robin_power|W|耦合族为 `Qrobin=∫r=Lx h(T−Tref)dA`；显式族为0|

能量按温度T本身积分，不减Tref。Qadv正号对应流体显热方程左侧；仅流体区域参与，并使用该模型指定的普通／AD材料和属性名。离散速度不保证逐点散度为零，因此 `∮∂Ωf ρf cf T u·n dA = Qadv + ∫Ωf ρf cf T div(u)dV`，不能直接用边界焓流替换Qadv。

稳态整体收支为 `Qadv+Qrobin−Qsrc`；瞬态第n≥1步还包括 `[(Es+Ef)n−(Es+Ef)n−1]/dt`。这些表达式说明观测与离散热残量的关系，不能强制归零或用于修正输出；t=0没有前一步储能差商。评分对象是固定真实有限元场的原生能量观测，不要求输出连续温度／速度解析解。

结果文件还须按CONTRACT复制experiment_ids及frames对应times等必需支持数组；两组输入系数不作为输出。每一行按实验身份、每一帧按给定times对应，不能只交五个数值数组而遗漏支持量。
