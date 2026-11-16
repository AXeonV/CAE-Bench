# 2.10.3 数据说明

本题与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、资源与评分见[本题 instruction](instruction.md)。`spatial_dimension=3`；`physics.model` 精确为 `fluid-reduced-transition-gas-v1`，`physics.parameters` 使用下述集合，不声明 `contract_version`、`profile`、`analysis`、`materials`，无隐含参数或自动单位换算。

## 文件、几何与采样

输入 `problem.json` 引用一个 Gmsh MSH 4.1 ASCII 一阶四面体网格及边界三角形和一个扁平 HDF5；计算域连通且固定。坐标 m，时间 s，三维采用全局xyz空间。`locations.domain` 是恰含全部网格节点的 mesh/node location。所有外边界必须导出；法向 n 指向域外。边界条件使用真实 mesh/element、dimension=2 的 location，以不相交分区恰好覆盖全部外边界；位置名不决定物理。

数组遵循通用契约 `[T,N,*component_shape]`，IDs 为身份而非行号。输入全部为边界场： `value_kind=average`、`sampling.space=piecewise_constant`，每个边界面常值。所有输入场显式提供 `sampling`，`extrapolation=forbid`。

边界字段 location 与其条件完全一致。每个输入场必须被一个或多个条件引用。边界 `data.value` 的字段 quantity 等于 condition.variable，其他 data 键的字段 quantity 等于该键名。均匀标量采用 `{value,unit}`，不作隐式换算。

稳态所有时间轴恰为单帧 `[0]`，所有输入 `sampling.time=constant`，无物理初态。连续条件交界处必须物理相容。

## 参数与域条件

所有参数为 `{value:有限数,unit:规定代码}`，精确包含下列集合，不可省略或添加。其余参数严格正。

参数：`molecule_mass` (kg)；`molecule_diameter` (m)；`reference_temperature` (K)。

本题不接受域初态或物性条件；全部材料由带单位参数给定。

值域 `positive` 为严格正，`finite` 为有限，`fraction` 为闭区间[0,1]。除列出的边界外无额外条件或源项。

## 连续模型与闭合

以下为连续求解目标，数值算法自选。∇、div 在实际求解坐标计算。除给定壁面与储槽驱动外无体力、质量源、热源、粗糙度、旋转或反应。

气体为单组分单原子，分子质量m=molecule_mass、直径d=molecule_diameter，kB=1.380649e−23 J/K。动理学f(x,c)为三维速度空间的分子数密度分布，n=∫f dc，ρ=mn，u=∫c f dc/n，T=m∫|c−u|²f dc/(3kB n)，p=nkB T。稳态c·∇x f=Q(f,f)。硬球题二体碰撞的总截面πd²，微分截面对立体角为d²/4；Q=∫R³∫S²(d²/4)|c−c*|[f(c′)f(c*′)−f(c)f(c*)]dΩdc*，c′=(c+c*)/2+|c−c*|ω/2，c*′=(c+c*)/2−|c−c*|ω/2。不使用BGK或未说明的碰撞频率。

气壁Uw切向固定：在壁面系w=c−Uw，明确定义fw(w)=f(Uw+w)。对进入气体的w·n<0，fw(w)=(1−α)fw,out(w−2(w·n)n)+α nw (m/(2πkBTw))^(3/2)exp[−m|w|²/(2kBTw)]；仅当α>0时nw由零净法向分子通量唯一决定；α=0时纯镜面项已满足零法向通量，不需要或定义nw。α=accommodation为镜面/完全热适应散漫反射的混合概率，0≤α≤1。储槽入流半空间c·n<0取由density、velocity、temperature定义的完整Maxwellian，出流取内部解；至少一处储槽。无需输入分布数组或伪造速度坐标：入射分布由这些明确物理参数解析定义，内部速度离散自选。数据保证储槽可达、无与储槽隔离的自由轨道支撑任意稳态存量。

## 边界条件

每项 `role=boundary`。下列 variable、operator 和 data 键精确固定，所有列出键必需，不得添加。scalar 可为同 location 标量场或带单位常数；vector/tensor 必须为同 location 字段。

- operator=`gas_wall`，variable=`gas`；data：`velocity`=vector m/s finite; `temperature`=scalar K positive; `accommodation`=scalar 1 fraction。
- operator=`gas_reservoir`，variable=`gas`；data：`density`=scalar kg/m3 positive; `velocity`=vector m/s finite; `temperature`=scalar K positive。

## 输出与观测

`outputs` 至少请求 `density`, `velocity`, `temperature`；其余仅可从下表选择。字段名任意，quantity 必须符合表列，所有输出 float64。完整数组、分量标签和复制 IDs/时间轴规则按通用契约，不得平移压力或隐式换算。

| quantity | unit | kind |
|---|---|---|
| `density` | `kg/m3` | scalar |
| `velocity` | `m/s` | vector |
| `temperature` | `K` | scalar |
| `pressure` | `Pa` | scalar |
| `traction` | `Pa` | vector |
| `heat_flux` | `W/m2` | vector |

除 traction、heat_flux 外的域观测为真实网格节点点值，可使用节点子集，value_kind=point。只在物理场有唯一连续迹的位置和时刻请求点观测；涉及导数的通量、应力还须有唯一相应空间/时间导数迹。边界分区交线、气壁/储槽交角及奇异角点若有多重迹或无界交换，不请求点值；边界面平均仅在积分存在且唯一时请求。不得把单元平均当作点值。

density 是局部kg/m3，velocity 是全局空间速度m/s，temperature 是绝对K。pressure=n kB T。traction 仅在 gas_wall 请求，为 −m∫c[(c−Uw)·n]f dc；heat_flux 仅在 gas_wall 请求，为 n(m/2)∫|c−Uw|²[(c−Uw)·n]f dc。traction 是域外作用于流体的力/面积，气体对壁面力取反号；traction/heat_flux 使用真实外边界面平均值（value_kind=average），单位分别Pa和W/m2，壁面牵引包括完整压力及黏性/非平衡动量交换。不使用 aggregate 或伪造整体探针。

可直接按通用契约读写，无需SDK。可选 `caeoj.fluid_reduced.reduced_parameters(problem)` 读取常数；内部离散、无量纲化、插值与求解由考生负责。`maxwellian(n,u,T,m,c)` 计算三维数分布，单位s3/m6；内部速度空间离散自选。
