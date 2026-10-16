# 2.11.2 数据说明

本题与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、资源与评分见[本题 instruction](instruction.md)。`spatial_dimension=2`；`physics.model` 精确为 `fluid-reduced-viscoelastic-transient-v1`，`physics.parameters` 使用下述集合，不声明 `contract_version`、`profile`、`analysis`、`materials`，无隐含参数或自动单位换算。

## 文件、几何与采样

输入 `problem.json` 引用一个 Gmsh MSH 4.1 ASCII 一阶三角形网格及边界线段和一个扁平 HDF5；计算域连通且固定。坐标 m，时间 s，二维采用全局xy平面。`locations.domain` 是恰含全部网格节点的 mesh/node location。所有外边界必须导出；法向 n 指向域外。边界条件使用真实 mesh/element、dimension=1 的 location，以不相交分区恰好覆盖全部外边界；位置名不决定物理。二维积分按单位出平面厚度。

数组遵循通用契约 `[T,N,*component_shape]`，IDs 为身份而非行号。域节点输入 `value_kind=point`、`sampling.space=piecewise_linear`，使用网格线性形函数连续重建；边界输入 `value_kind=average`、`sampling.space=piecewise_constant`，每个边界面常值。所有输入场显式提供 `sampling`，`extrapolation=forbid`。

域条件 location=`domain`，data 恰含 `value`：字段表示 `{"value":{"field":"字段名"}}`，非初态标量亦可用 `{"value":{"value":数值,"unit":"单位"}}`。物理初态必须引用场。矢量/张量只能引用字段，禁止 JSON 内联数组。边界字段 location 与其条件完全一致。每个输入场必须被一个或多个条件引用。域字段 quantity 等于所引用变量名；边界 `data.value` 的字段 quantity 等于 condition.variable，其他 data 键的字段 quantity 等于该键名。均匀标量采用 `{value,unit}`，不作隐式换算。

`start_time`、`end_time` 明确物理区间，初态时间轴单帧 `[start_time]`；初态与其他单帧输入使用 `sampling.time=constant`（初态仅赋值起点，其余单帧常量在整个区间恒定）。多帧非初态使用 `sampling.time=linear`，覆盖完整起止区间，样本间线性插值，禁止外推。输出时刻在起止闭区间内，不能由输出轴推断内部步长。初态与连续条件交界处必须物理相容。

完整构象张量按全局笛卡尔2×2平面块表示，Azz=1、Axz=Ayz=0；迹与弹性能对应三维平面流。对称容差1e-12仅为输入诊断，不改变对称正定材料定义。

## 参数与域条件

所有参数为 `{value:有限数,unit:规定代码}`，精确包含下列集合，不可省略或添加。`reference_pressure`、`start_time`、`end_time`为任意有限实数；其余参数严格正。`end_time>start_time`。

参数：`density` (kg/m3)；`solvent_viscosity` (Pa.s)；`polymer_viscosity` (Pa.s)；`relaxation_time` (s)；`reference_pressure` (Pa)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `velocity`：`initial/assign`，`m/s`，vector，finite。
- `conformation`：`initial/assign`，`1`，tensor，spd。

值域 `finite` 为有限，`spd` 为对称正定。域条件每项恰一次，除列出的条件与边界外无额外源项或物性字段。

## 连续模型与闭合

以下为连续求解目标，数值算法自选。∇、div 在实际求解坐标计算；Lij=∂ui/∂xj，D=(L+Lᵀ)/2，γ=sqrt(2D:D)。除下述壁面或边界驱动外无体力、质量源、热源、粗糙度、旋转或反应。

Dt=∂t+u·∇，ρ=density。本题不可压缩：divu=0、ρDtu=divσ；σ=−pI+τ。无体力。p为Pa静压：无traction_outlet时以域体积平均p=reference_pressure固定唯一压力规范；有出口时由给定牵引固定压力，reference_pressure仅用于记录基准而不再叠加平均约束。速度墙和入口给定Dirichlet；出口指定完整σn矢量。构象只在真正入流指定，出口采用无入射记忆的自然对流，数据保证traction_outlet无回流；墙无穿透，不额外施加构象法向梯度。

ηs=solvent_viscosity、ηp=polymer_viscosity、λ=relaxation_time。Oldroyd-B：Dt A−LA−ALᵀ=−(A−I)/λ；τ=2ηsD+τp，τp=ηp(A−I)/λ。A必须对称正定；二维采用Azz=1平面解。入口必须提供构象。瞬态必须提供起点A，任何预伸长均保留；速度初态满足不可压缩和边界相容。无人工应力扩散，数值稳定化不得改变收敛目标。

## 边界条件

每项 `role=boundary`。下列 variable、operator 和 data 键精确固定，所有列出键必需，不得添加。scalar 可为同 location 标量场或带单位常数；vector/tensor 必须为同 location 字段。

- operator=`velocity_wall`，variable=`velocity`；data：`value`=vector m/s finite。
- operator=`velocity_inlet`，variable=`velocity`；data：`value`=vector m/s finite; `conformation`=tensor 1 spd。
- operator=`traction_outlet`，variable=`traction`；data：`value`=vector Pa finite。

## 输出与观测

`outputs` 至少请求 `velocity`, `pressure`, `conformation`, `polymer_stress`；其余仅可从下表选择。字段名任意，quantity 必须符合表列，所有输出 float64。完整数组、分量标签和复制 IDs/时间轴规则按通用契约，不得平移压力或隐式换算。

| quantity | unit | kind |
|---|---|---|
| `velocity` | `m/s` | vector |
| `pressure` | `Pa` | scalar |
| `polymer_stress` | `Pa` | tensor |
| `conformation` | `1` | tensor |
| `traction` | `Pa` | vector |

除 traction 外的域观测为真实网格节点点值，可使用节点子集，value_kind=point。只在物理场有唯一连续迹的位置和时刻请求点观测；涉及导数的通量、应力还须有唯一相应空间/时间导数迹。边界分区交点及奇异角点若有多重迹或无界交换，不请求点值；边界面平均仅在积分存在且唯一时请求。不得把单元平均当作点值。

pressure 是带上述唯一压力规范的Pa静压。traction=σn，为域外作用于流体的力/面积Pa；它采用真实外边界面平均值（value_kind=average）。polymer_stress=τp，为Pa完整张量；conformation=A，为无量纲完整张量。全部输出不使用 aggregate，不制造汇总探针。

可直接按通用契约读写，无需SDK。可选 `caeoj.fluid_reduced.reduced_parameters(problem)` 读取常数；内部离散、无量纲化、插值与求解由考生负责。`reduced_viscosity(model,parameters,shear_rate,temperature=None,structure=None)` 可计算上述标量黏度；Oldroyd返回溶剂黏度，不能把记忆压成有效黏度。
