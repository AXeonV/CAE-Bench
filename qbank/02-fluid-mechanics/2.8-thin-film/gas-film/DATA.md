# 2.8.2 数据说明

本题与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、资源与评分见[本题 instruction](instruction.md)。`spatial_dimension=2`；`physics.model` 精确为 `fluid-reduced-gas-film-v1`，`physics.parameters` 使用下述集合，不声明 `contract_version`、`profile`、`analysis`、`materials`，无隐含参数或自动单位换算。

## 文件、几何与采样

输入 `problem.json` 引用一个 Gmsh MSH 4.1 ASCII 一阶三角形网格及边界线段和一个扁平 HDF5；计算域连通且固定。坐标 m，时间 s，二维采用全局xy平面。`locations.domain` 是恰含全部网格节点的 mesh/node location。所有外边界必须导出；法向 n 指向域外。边界条件使用真实 mesh/element、dimension=1 的 location，以不相交分区恰好覆盖全部外边界；位置名不决定物理。本题平面是实际水平面积，不再乘单位出平面厚度。

数组遵循通用契约 `[T,N,*component_shape]`，IDs 为身份而非行号。域节点输入 `value_kind=point`、`sampling.space=piecewise_linear`，使用网格线性形函数连续重建；边界输入 `value_kind=average`、`sampling.space=piecewise_constant`，每个边界面常值。所有输入场显式提供 `sampling`，`extrapolation=forbid`。

域条件 location=`domain`，data 恰含 `value`：字段表示 `{"value":{"field":"字段名"}}`，非初态标量亦可用 `{"value":{"value":数值,"unit":"单位"}}`。物理初态必须引用场。矢量只能引用字段，禁止 JSON 内联数组。边界字段 location 与其条件完全一致。每个输入场必须被一个或多个条件引用。域字段 quantity 等于所引用变量名；边界 `data.value` 的字段 quantity 等于 condition.variable，其他 data 键的字段 quantity 等于该键名。均匀标量采用 `{value,unit}`，不作隐式换算。

`start_time`、`end_time` 明确物理区间，初态时间轴单帧 `[start_time]`；初态与其他单帧输入使用 `sampling.time=constant`（初态仅赋值起点，其余单帧常量在整个区间恒定）。多帧非初态使用 `sampling.time=linear`，覆盖完整起止区间，样本间线性插值，禁止外推。输出时刻在起止闭区间内，不能由输出轴推断内部步长。初态与连续条件交界处必须物理相容。

## 参数与域条件

所有参数为 `{value:有限数,unit:规定代码}`，精确包含下列集合，不可省略或添加。`reference_pressure`、`start_time`、`end_time`为任意有限实数；其余参数严格正。`end_time>start_time`。

参数：`viscosity` (Pa.s)；`specific_gas_constant` (J/(kg.K))；`reference_temperature` (K)；`reference_pressure` (Pa)；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `gap`：`material/geometry`，`m`，scalar，positive。
- `lower_velocity`：`material/geometry`，`m/s`，vector，finite。
- `upper_velocity`：`material/geometry`，`m/s`，vector，finite。
- `pressure`：`initial/assign`，`Pa`，scalar，positive。

值域 `positive` 为严格正，`finite` 为有限。域条件每项恰一次，除列出的条件与边界外无额外源项或物性字段。

## 连续模型与闭合

以下为连续求解目标，数值算法自选。∇、div 在实际求解坐标计算。除下述壁面或边界驱动外无体力、质量源、热源、粗糙度、旋转或反应。

h=gap，z∈[0,h]为真实跨隙方向，输入lower_velocity/upper_velocity是面内速度U0/U1；下壁z=0，上壁z=h。忽略跨隙压力梯度、惯性和面内黏性扩散，无滑移，薄隙渐近模型；几何与运动满足薄膜假设，壁面法向运动通过给定h的时间导数表示，不改变2D计算域。普通牛顿满膜 q=−h³∇p/(12μ)+h(U0+U1)/2，q单位m²/s。p为绝对静压，载荷为∫域(p−reference_pressure)dA，向上为正，单位N。所有侧边给定film_pressure。间隙h使用分片线性时间重建时，内部采样结点的∂t h取右侧分段导数，起点取右迹，最终端点取左迹；单帧恒定h的导数为0。依赖该导数的瞬时压力、通量及载荷也使用同一时间迹约定，不对相邻左右答案取平均。

气膜：R=specific_gas_constant，Tref=reference_temperature，μ=viscosity；ρ=p/(R Tref)，μ为常数，∂t(ρh)+div(ρq)=0；初始压力严格正，无空化和滑移；h可随时间变化。所有p、T为绝对量。

## 边界条件

每项 `role=boundary`。下列 variable、operator 和 data 键精确固定，所有列出键必需，不得添加。scalar 可为同 location 标量场或带单位常数；vector/tensor 必须为同 location 字段。

- operator=`film_pressure`，variable=`pressure`；data：`value`=scalar Pa positive。

## 输出与观测

`outputs` 至少请求 `pressure`；其余仅可从下表选择。字段名任意，quantity 必须符合表列，所有输出 float64。完整数组、分量标签和复制 IDs/时间轴规则按通用契约，不得平移压力或隐式换算。

| quantity | unit | kind |
|---|---|---|
| `pressure` | `Pa` | scalar |
| `density` | `kg/m3` | scalar |
| `film_flux` | `m2/s` | vector |
| `load` | `N` | scalar |

除 load 外的域观测为真实网格节点点值，可使用节点子集，value_kind=point。只在物理场有唯一连续迹的位置和时刻请求点观测；涉及导数的通量还须有唯一相应空间/时间导数迹。边界分区交点及奇异角点若有多重迹或无界交换，不请求点值。不得把单元平均当作点值。

pressure 是绝对静压。film_flux=q=∫₀ʰu dz，单位 m2/s，气膜也为体积通量而非质量通量。load=∫域(p−reference_pressure)dA，向上为正。load 使用 aggregate/source 指向恰含全部域单元的 location，operation=sum、value_kind=integral，单位 N；其余输出不使用 aggregate。density=ρ=p/(R Tref)，单位kg/m3。间隙时间结点单侧导数迹按连续模型段落约定，相关压力、通量与载荷使用同一迹，不能取左右平均。

可直接按通用契约读写，无需SDK。可选 `caeoj.fluid_reduced.reduced_parameters(problem)` 读取常数；内部离散、无量纲化、插值与求解由考生负责。`reduced_time_derivative(times,values,time)` 按右迹/末端左迹求分片线性时间导数。
