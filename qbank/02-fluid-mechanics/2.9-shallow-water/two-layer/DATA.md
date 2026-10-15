# 2.9.4 数据说明

本题与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、资源与评分见[本题 instruction](instruction.md)。`spatial_dimension=2`；`physics.model` 精确为 `fluid-reduced-two-layer-v1`，`physics.parameters` 使用下述集合，不声明 `contract_version`、`profile`、`analysis`、`materials`，无隐含参数或自动单位换算。

## 文件、几何与采样

输入 `problem.json` 引用一个 Gmsh MSH 4.1 ASCII 一阶三角形网格及边界线段和一个扁平 HDF5；计算域连通且固定。坐标 m，时间 s，二维采用全局xy平面。`locations.domain` 是恰含全部网格节点的 mesh/node location。所有外边界必须导出；法向 n 指向域外。边界条件使用真实 mesh/element、dimension=1 的 location，以不相交分区恰好覆盖全部外边界；位置名不决定物理。本题平面是实际水平面积，不再乘单位出平面厚度。

数组遵循通用契约 `[T,N,*component_shape]`，IDs 为身份而非行号。域节点输入 `value_kind=point`、`sampling.space=piecewise_linear`，使用网格线性形函数连续重建；边界输入 `value_kind=average`、`sampling.space=piecewise_constant`，每个边界面常值。所有输入场显式提供 `sampling`，`extrapolation=forbid`。

域条件 location=`domain`，data 恰含 `value`：字段表示 `{"value":{"field":"字段名"}}`，非初态标量亦可用 `{"value":{"value":数值,"unit":"单位"}}`。物理初态必须引用场。矢量只能引用字段，禁止 JSON 内联数组。边界字段 location 与其条件完全一致。每个输入场必须被一个或多个条件引用。域字段 quantity 等于所引用变量名；边界 `data.value` 的字段 quantity 等于 condition.variable，其他 data 键的字段 quantity 等于该键名。均匀标量采用 `{value,unit}`，不作隐式换算。

`start_time`、`end_time` 明确物理区间，初态时间轴单帧 `[start_time]`；初态与其他单帧输入使用 `sampling.time=constant`（初态仅赋值起点，其余单帧常量在整个区间恒定）。多帧非初态使用 `sampling.time=linear`，覆盖完整起止区间，样本间线性插值，禁止外推。输出时刻在起止闭区间内，不能由输出轴推断内部步长。初态与连续条件交界处必须物理相容。

## 参数与域条件

所有参数为 `{value:有限数,unit:规定代码}`，精确包含下列集合，不可省略或添加。`start_time`、`end_time`为任意有限实数；`bottom_drag`、`interface_drag`非负；其余参数严格正。`end_time>start_time`。`lower_density>upper_density`。

参数：`lower_density` (kg/m3)；`upper_density` (kg/m3)；`gravity` (m/s2)；`bottom_drag` (1/s)；`interface_drag` (kg/(m2.s))；`start_time` (s)；`end_time` (s)。

必需域条件（每项恰一次，data只含value；括号依次为 role/operator、单位、分量类型、值域）：

- `bed`：`material/geometry`，`m`，scalar，finite。
- `lower_depth`：`initial/assign`，`m`，scalar，positive。
- `lower_velocity`：`initial/assign`，`m/s`，vector，finite。
- `upper_depth`：`initial/assign`，`m`，scalar，positive。
- `upper_velocity`：`initial/assign`，`m/s`，vector，finite。

值域 `positive` 为严格正，`finite` 为有限。域条件每项恰一次，除列出的条件与边界外无额外源项或物性字段。

bed 是固定地形；其输入必须为单帧、sampling.time=constant，在整个物理区间保持不变，不包含移动床做功。

## 连续模型与闭合

以下为连续求解目标，数值算法自选。∇、div 在实际求解坐标计算。除下述重力或壁面驱动外无体力、质量源、热源、粗糙度、旋转或反应。

g=gravity。底高程b=bed，向上为正。两层下标l/u，ρl=lower_density、ρu=upper_density，ρl>ρu，r=ρu/ρl。每层满足∂t hj+div(hj uj)=0；Dl ul=−g∇(b+hl+r hu)−bottom_drag ul+K(uu−ul)/(ρl hl)；Du uu=−g∇(b+hl+hu)−K(uu−ul)/(ρu hu)，K=interface_drag，Dj=∂t+uj·∇。下层与床接触，上层与空气接触；无层间质量交换或扩散。限定光滑双曲稳定全湿解，避免对非守恒跨跃积作隐藏选择。

两层首版不支持亚临界或混合入射特征储槽，边界只允许layer_inlet完整超临界入流、layer_outflow完整超临界纯出流及layer_wall。layer_inlet直接指定两层h与完整水平u，四个状态场使用同一时间轴，标量常数允许；layer_outflow不指定外部状态，只允许内部信息流出。以外法向n定义vl=ul·n、vu=uu·n，四个重力波特征为矩阵[[vl,0,hl,0],[0,vu,0,hu],[g,r g,vl,0],[g,g,0,vu]]的特征值，另有切向平流特征vl、vu。入流全部特征严格负且实，出流全部严格正且实，禁止零速/复数及区间内分支改变。算例保证时间插值后的入流和所求出流状态在整个区间始终满足这些严格符号。墙条件为每层u·n=0，不可穿透自由滑移。

## 边界条件

每项 `role=boundary`。下列 variable、operator 和 data 键精确固定，所有列出键必需，不得添加。scalar 可为同 location 标量场或带单位常数；vector/tensor 必须为同 location 字段；option 使用 `{"option":"规定值"}`。

- operator=`layer_wall`，variable=`layers`；data：`mode`=option(impermeable)。
- operator=`layer_inlet`，variable=`layers`；data：`lower_depth`=scalar m positive; `lower_velocity`=vector m/s finite; `upper_depth`=scalar m positive; `upper_velocity`=vector m/s finite。

- operator=`layer_outflow`，variable=`layers`；data：`mode`=option(supercritical_outflow)。

## 输出与观测

`outputs` 至少请求 `lower_depth`, `upper_depth`, `lower_velocity`, `upper_velocity`；其余仅可从下表选择。字段名任意，quantity 必须符合表列，所有输出 float64。完整数组、分量标签和复制 IDs/时间轴规则按通用契约，不得隐式换算。

| quantity | unit | kind |
|---|---|---|
| `lower_depth` | `m` | scalar |
| `upper_depth` | `m` | scalar |
| `lower_velocity` | `m/s` | vector |
| `upper_velocity` | `m/s` | vector |
| `water_volume` | `m3` | scalar |

除 water_volume 外的域观测为真实网格节点点值，可使用节点子集，value_kind=point。只在物理场有唯一连续迹的位置和时刻请求点观测。边界分区交点及奇异角点若有多重迹或无界交换，不请求点值。不得把单元平均当作点值。

water_volume=∫(hl+hu)dA，使用 aggregate/source 指向恰含全部域单元的 location，operation=sum、value_kind=integral、单位m3；其余输出不使用 aggregate。

可直接按通用契约读写，无需SDK。可选 `caeoj.fluid_reduced.reduced_parameters(problem)` 读取常数；内部离散、无量纲化、插值与求解由考生负责。`layer_characteristic_speeds(hl,hu,vl,vu,g,r)` 返回四个重力波与两个切向速度，仅检验给定状态，不求边界演化。
