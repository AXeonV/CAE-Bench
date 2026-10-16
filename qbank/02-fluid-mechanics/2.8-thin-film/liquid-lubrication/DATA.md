# 2.8.1 数据说明

本题与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、资源与评分见[本题 instruction](instruction.md)。`spatial_dimension=2`；`physics.model` 精确为 `fluid-reduced-liquid-lubrication-v1`，`physics.parameters` 使用下述集合，不声明 `contract_version`、`profile`、`analysis`、`materials`，无隐含参数或自动单位换算。

## 文件、几何与采样

输入 `problem.json` 引用一个 Gmsh MSH 4.1 ASCII 一阶三角形网格及边界线段和一个扁平 HDF5；计算域连通且固定。坐标 m，时间 s，二维采用全局xy平面。`locations.domain` 是恰含全部网格节点的 mesh/node location。所有外边界必须导出；法向 n 指向域外。边界条件使用真实 mesh/element、dimension=1 的 location，以不相交分区恰好覆盖全部外边界；位置名不决定物理。本题平面是实际水平面积，不再乘单位出平面厚度。

数组遵循通用契约 `[T,N,*component_shape]`，IDs 为身份而非行号。域节点输入 `value_kind=point`、`sampling.space=piecewise_linear`，使用网格线性形函数连续重建；边界输入 `value_kind=average`、`sampling.space=piecewise_constant`，每个边界面常值。所有输入场显式提供 `sampling`，`extrapolation=forbid`。

域条件 location=`domain`，data 恰含 `value`：字段表示 `{"value":{"field":"字段名"}}`，非初态标量亦可用 `{"value":{"value":数值,"unit":"单位"}}`。物理初态必须引用场。矢量只能引用字段，禁止 JSON 内联数组。边界字段 location 与其条件完全一致。每个输入场必须被一个或多个条件引用。域字段 quantity 等于所引用变量名；边界 `data.value` 的字段 quantity 等于 condition.variable，其他 data 键的字段 quantity 等于该键名。均匀标量采用 `{value,unit}`，不作隐式换算。

稳态所有时间轴恰为单帧 `[0]`，所有输入 `sampling.time=constant`，无物理初态。连续条件交界处必须物理相容。

## 参数与域条件

所有参数为 `{value:有限数,unit:规定代码}`，精确包含下列集合，不可省略或添加。`reference_pressure`为任意有限实数；其余参数严格正。

参数：`density` (kg/m3)；`viscosity` (Pa.s)；`reference_pressure` (Pa)；`cavitation_pressure` (Pa)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `gap`：`material/geometry`，`m`，scalar，positive。
- `lower_velocity`：`material/geometry`，`m/s`，vector，finite。
- `upper_velocity`：`material/geometry`，`m/s`，vector，finite。

值域 `positive` 为严格正，`finite` 为有限，`fraction` 为闭区间[0,1]。域条件每项恰一次，除列出的条件与边界外无额外源项或物性字段。

## 连续模型与闭合

以下为连续求解目标，数值算法自选。∇、div 在实际求解坐标计算。除下述壁面或边界驱动外无体力、质量源、热源、粗糙度、旋转或反应。

h=gap，z∈[0,h]为真实跨隙方向，输入lower_velocity/upper_velocity是面内速度U0/U1；下壁z=0，上壁z=h。忽略跨隙压力梯度、惯性和面内黏性扩散，无滑移，薄隙渐近模型；几何与运动满足薄膜假设，壁面法向运动通过给定h的时间导数表示，不改变2D计算域。μ=viscosity，q单位m²/s，通量及空化约束如下。p为绝对静压，载荷为∫域(p−reference_pressure)dA，向上为正，单位N。所有侧边给定film_pressure。

液体空化题采用质量守恒的充满率θ：p≥pc、0≤θ≤1、(p−pc)(1−θ)=0，q=−h³∇p/(12μ)+hθ(U0+U1)/2，稳态div q=0；pc=cavitation_pressure。θ是以液体密度计的薄膜占据率，不是可压缩液体密度。在空化区输运方向由平均壁速决定，采用上游充满率的守恒弱解，滞止未定区域不纳入算例；入口边界fraction给出从域外进入的θ，仅在对流入流分支生效，满膜p>pc边界的fraction必须为1。边界p不能低于pc，边界p=pc时允许0≤fraction≤1。

## 边界条件

每项 `role=boundary`。下列 variable、operator 和 data 键精确固定，所有列出键必需，不得添加。scalar 可为同 location 标量场或带单位常数；vector/tensor 必须为同 location 字段。

- operator=`film_pressure`，variable=`pressure`；data：`value`=scalar Pa positive; `fraction`=scalar 1 fraction。

## 输出与观测

`outputs` 至少请求 `pressure`, `film_fraction`；其余仅可从下表选择。字段名任意，quantity 必须符合表列，所有输出 float64。完整数组、分量标签和复制 IDs/时间轴规则按通用契约，不得平移压力或隐式换算。

| quantity | unit | kind |
|---|---|---|
| `pressure` | `Pa` | scalar |
| `film_fraction` | `1` | scalar |
| `film_flux` | `m2/s` | vector |
| `load` | `N` | scalar |

除 load 外的域观测为真实网格节点点值，可使用节点子集，value_kind=point。只在物理场有唯一连续迹的位置和时刻请求点观测；涉及导数的通量还须有唯一相应空间/时间导数迹。边界分区交点及奇异角点若有多重迹或无界交换，不请求点值。不得把单元平均当作点值。

pressure 是绝对静压。film_flux=q=∫₀ʰu dz，单位 m2/s，沿全局xy分量表示。load=∫域(p−reference_pressure)dA，向上为正。load 使用 aggregate/source 指向恰含全部域单元的 location，operation=sum、value_kind=integral，单位 N；其余输出不使用 aggregate。film_fraction=θ，为以液体密度计的占据率。

可直接按通用契约读写，无需SDK。可选 `caeoj.fluid_reduced.reduced_parameters(problem)` 读取常数；内部离散、无量纲化、插值与求解由考生负责。
