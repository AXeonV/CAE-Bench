# 2.10.1 数据说明

本题与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、资源与评分见[本题 instruction](instruction.md)。`spatial_dimension=2`；`physics.model` 精确为 `fluid-reduced-isothermal-slip-v1`，`physics.parameters` 使用下述集合，不声明 `contract_version`、`profile`、`analysis`、`materials`，无隐含参数或自动单位换算。

## 文件、几何与采样

输入 `problem.json` 引用一个 Gmsh MSH 4.1 ASCII 一阶三角形网格及边界线段和一个扁平 HDF5；计算域连通且固定。坐标 m，时间 s，二维采用全局xy平面。`locations.domain` 是恰含全部网格节点的 mesh/node location。所有外边界必须导出；法向 n 指向域外。边界条件使用真实 mesh/element、dimension=1 的 location，以不相交分区恰好覆盖全部外边界；位置名不决定物理。二维积分按单位出平面厚度。

数组遵循通用契约 `[T,N,*component_shape]`，IDs 为身份而非行号。输入全部为边界场： `value_kind=average`、`sampling.space=piecewise_constant`，每个边界面常值。所有输入场显式提供 `sampling`，`extrapolation=forbid`。

边界字段 location 与其条件完全一致。每个输入场必须被一个或多个条件引用。边界 `data.value` 的字段 quantity 等于 condition.variable，其他 data 键的字段 quantity 等于该键名。均匀标量采用 `{value,unit}`，不作隐式换算。

稳态所有时间轴恰为单帧 `[0]`，所有输入 `sampling.time=constant`，无物理初态。连续条件交界处必须物理相容。

## 参数与域条件

所有参数为 `{value:有限数,unit:规定代码}`，精确包含下列集合，不可省略或添加。`slip_length`、`temperature_jump_length`非负；其余参数严格正。`temperature_jump_length=0`。

参数：`molecule_mass` (kg)；`molecule_diameter` (m)；`reference_temperature` (K)；`slip_length` (m)；`temperature_jump_length` (m)；`reference_pressure` (Pa)。

本题不接受域初态或物性条件；全部材料由带单位参数给定。

值域 `positive` 为严格正，`finite` 为有限。除列出的边界外无额外条件或源项。

## 连续模型与闭合

以下为连续求解目标，数值算法自选。∇、div 在实际求解坐标计算；Lij=∂ui/∂xj，D=(L+Lᵀ)/2，γ=sqrt(2D:D)。除下述壁面或边界驱动外无体力、质量源、热源、粗糙度、旋转或反应。

气体为单组分单原子、分子质量m=molecule_mass、直径d=molecule_diameter、kB=1.380649e−23 J/K、R=kB/m、cv=3R/2。滑移题解稳态可压缩质量／动量守恒，ρ=p/(R T)，σ=−pI+μ(L+Lᵀ−(2/3)divu I)，μ(T)=5 sqrt(m kB T/π)/(16 d²)。二维仍是三维分子的平面空间流动，体黏度为零。等温T=Tref=reference_temperature，不求能量。下标t为沿壁面切向分量，Uw为墙条件data.velocity。速度滑移墙u·n=Uw·n=0，(u−Uw)t=−slip_length·(σn)t/μ；长度为给定材料气壁参数，模型不含热蠕移。壁面几何固定，Uw必须切向。入口data.velocity给定速度；出口data.pressure=p_ext给定总牵引σn=−p_ext n（并非另外强制内部静压=p_ext）。reference_pressure与reference_temperature为气体参考状态，仅用于定义参考平均自由程λref=m/(sqrt(2)πd²ρref)、ρref=reference_pressure/(R reference_temperature)，两者均须正；不再叠加压力均值约束。至少一处出口固定绝对压力；出口数据保证无回流。滑移输入与状态应处在一阶连续模型适用区，算例保证其适用性。
稳态守恒方程为div(ρu)=0、div(ρu⊗u)=divσ，τ=σ+pI；无体力。

## 边界条件

每项 `role=boundary`。下列 variable、operator 和 data 键精确固定，所有列出键必需，不得添加。scalar 可为同 location 标量场或带单位常数；vector/tensor 必须为同 location 字段。

- operator=`slip_wall`，variable=`gas`；data：`velocity`=vector m/s finite。
- operator=`slip_inlet`，variable=`gas`；data：`velocity`=vector m/s finite。
- operator=`slip_outlet`，variable=`gas`；data：`pressure`=scalar Pa positive。

## 输出与观测

`outputs` 至少请求 `velocity`, `pressure`；其余仅可从下表选择。字段名任意，quantity 必须符合表列，所有输出 float64。完整数组、分量标签和复制 IDs/时间轴规则按通用契约，不得平移压力或隐式换算。

| quantity | unit | kind |
|---|---|---|
| `density` | `kg/m3` | scalar |
| `velocity` | `m/s` | vector |
| `pressure` | `Pa` | scalar |
| `traction` | `Pa` | vector |

除 traction 外的域观测为真实网格节点点值，可使用节点子集，value_kind=point。只在物理场有唯一连续迹的位置和时刻请求点观测；涉及导数的通量、应力还须有唯一相应空间/时间导数迹。边界分区交线、气壁/储槽交角及奇异角点若有多重迹或无界交换，不请求点值；边界面平均仅在积分存在且唯一时请求。不得把单元平均当作点值。

density 是局部kg/m3，velocity 是全局空间速度m/s。pressure 是绝对静压；traction=σn。traction 是域外作用于流体的力/面积，气体对壁面力取反号；traction 使用真实外边界面平均值（value_kind=average），单位Pa，壁面牵引包括完整压力及黏性/非平衡动量交换。不使用 aggregate 或伪造整体探针。

可直接按通用契约读写，无需SDK。可选 `caeoj.fluid_reduced.reduced_parameters(problem)` 读取常数；内部离散、无量纲化、插值与求解由考生负责。
