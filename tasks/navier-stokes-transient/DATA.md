# 输入字段与连续条件

本文是瞬态题的程序输入约定。`physics.model=incompressible_navier_stokes`；ρ 为 `density`（kg/m3），μ 为 `dynamic_viscosity`（Pa.s），矩形由 `x0,y0,length_x,length_y`（m）声明。所有参数采用 `{value,unit}`，单位不自动换算。

## 网格、时间与初始场

网格为矩形上的等距笛卡尔点阵及一阶三角形，两方向各 n+1 个节点；单周期 n∈{4,16,24,32,48,64}，双周期 n∈{16,24,32,48,64}。边界和域以 Gmsh Physical Groups 指定。NPZ 节点场按声明的递增 tag 排列，禁止按网格读取顺序解释。几何坐标允许浮点读写舍入误差。

`time_axes.initial` 引用 `[0.0]`；`time_axes.conditions` 也引用单元素 `[0.0]`，其值表示整个 t>0 区间中恒定的条件；`time_axes.output` 是请求的输出时刻。三个轴的含义不同，不根据轴长推断内部积分步长。

`initial / velocity / assign` 条件的 `data.value:{field:...}` 引用 `initial_velocity[1,N,2]`，单位 m/s。连续解释按边界类型区分：

- **单周期通道**：初始速度沿周期方向，横向分量为零，在该方向上不变；跨壁方向在相邻网格层之间线性插值。初始场可有正负值和局部突变，突变指相邻层差异，连续解释仍为分片线性。体加速度和壁面速度同样平行于周期方向。
- **双周期正方形**：无体加速度。初始速度是每方向整数波数绝对值≤2的二维周期三角多项式（含常数项），这里整数波数 (mₓ,mᵧ) 对应相位 `2π[mₓ(x−x₀)/L+mᵧ(y−y₀)/L]`，L 为边长。节点样本唯一确定其连续场，且满足不可压缩约束。周期边上重复的对应节点值相等，不计为两个独立自由度。

初始场仅给出速度。t=0 的速度取输入给定的节点值；t=0 压力仍须满足方程约束与压力规范。运动壁面可以在 t=0 突然施加，初始层边界数据不替换为 t>0 的壁面值。

范围中的 `Re=UL/(μ/ρ)`：通道 L 取两壁距离，U 为壁面、稳态剖面和初始剖面的最大速度幅值；双周期 L 取边长，U 为连续初始场的最大速度模。Re 不作为重复输入参数。

## 条件记录

| role / variable / operator | data 与数学含义 |
|---|---|
| `source / velocity / acceleration` | `value:{field:...}` 是 domain 节点上的恒定矢量加速度，m/s2。方程右端 **+ρa**。 |
| `boundary / velocity / dirichlet` | `value:{field:...}` 是壁面节点上的恒定速度矢量，m/s；作用于 t>0，每条壁面为恒定值。 |
| `boundary / velocity_pressure / periodic` | 从边 location；`master_physical_tag:{value:JSON整数,unit:"1"}` 指定主边的一维 Physical Group。使用 Gmsh `$Periodic` 节点对应与平移，速度、压力和对应导数周期相等，压力跳跃为零。每对只在从边声明一条记录。 |
| `boundary / pressure / mean` | domain 上 `value:{value:0,unit:"Pa"}`，规定 **面积平均压力为零**；不是 domain 节点全部取零，也不是壁面压力条件。 |

双周期有两条 periodic 记录、无壁面速度条件；单周期有一条 periodic 记录和两条壁面速度条件。匹配由组 tag 和 Gmsh 周期映射决定，JSON 表的名称与记录次序均不决定约束。

周期通道中体加速度驱动的是流向动量，输出 p 是周期压力。等价压差表示的线性总压力部分 `−ρa·(x,y)` 不属于输出 p。双周期域也使用面积零均值压力，不能用重复边界节点的算术平均代替面积平均。

## 输出与工具

`velocity` 为 float64 `[T,N,2]`，最后轴固定全局 x/y；`pressure` 为 `[T,N,1]`。输出仅包含清单要求的字段和对应 `node_ids`、`times`，不复制 `initial_times`、`condition_times`、初始场或坐标。

可用 `load_problem`、`read_constant`、`read_field`、`write_result` 读写；Gmsh 周期映射通过 `getPeriodicNodes` 读取。校验器只检查协议结构与引用，不验证初始场散度、周期物理相等、压力规范或求解结果。
