# 2.13.21 二维 Rayleigh–Bénard 对流：数据与连续定义

遵循 [CONTRACT](../../../../docs/CONTRACT.md)。task="cc-2d-rayleigh-benard-convection"，physics.model="cfdcodebench-c21-v1"，spatial_dimension=2。
协议坐标和时刻遵守 CONTRACT，分别以 m、s 表示。下面连续方程使用归一化坐标 x*=x/(1 m)、时间 t*=t/(1 s)，省略星号；两者数值恰与协议值相同，不另换算。所有输出场及公开权重为题定无量纲量，单位字符串为 "1"；温度读数的标度如本页特别说明。
physics.parameters={}；模型及其固定参数由本页完整定义，不读取外部默认配置。

## 连续问题

\[
\text{Momentum equation:} \\
\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\nabla p + \nu \nabla^2 \mathbf{u} + b \mathbf{e}_z \\
\text{Buoyancy (temperature) transport:} \\
\frac{\partial b}{\partial t} + \mathbf{u} \cdot \nabla b = \kappa \nabla^2 b \\
\text{Incompressibility:} \\
\nabla \cdot \mathbf{u} = 0
\]

where:
- \( \mathbf{u}(x, z, t) = (u, w) \): velocity field
- \( p(x, z, t) \): pressure
- \( b(x, z, t) \): total buoyancy/temperature variable
- \( \nu = (Ra/Pr)^{-1/2} \): kinematic viscosity
- \( \kappa = (Ra\cdot Pr)^{-1/2} \): thermal diffusivity
- \( Ra = 2 \times 10^6 \), \( Pr = 1 \): Rayleigh and Prandtl numbers, where \(\mathbf{e}_z\) is the unit vector of Z direction.

计算域与时间范围：

- Spatial domain: \( x \in [0, 4],\ z \in [0, 1] \)
- Temporal domain: \( t \in [0, 50] \)

边界：

- Top boundary \( z = L_z \): \( \mathbf{u} = 0 \), \( b = 0 \)
- Bottom boundary \( z = 0 \): \( \mathbf{u} = 0 \), \( b = L_z \)
- Horizontal boundaries: periodic for all variables

初态：

\[
  \mathbf{u}(x, z, 0) = 0, \quad b(x, z, 0) = L_z - z + 10^{-3} \sin(\pi z / L_z) \cos(\pi x)
\]
with \( L_z = 1 \) (a small deterministic perturbation of the linear profile that triggers convection).

补充及优先定义：

b 是原无量纲总浮力/温度变量，不是减去1-z后的偏差。原 x-z 平面在协议中映射为 x-y，w 为第二方向分量。压力无独立初态，仅固定常数基准。

压力 p 的候选与参考分别减去全部观测点上的加权均值后评分；允许常数基准差，不拟合比例或相位。

## 实际输入

problem.json 的 data_file 指向包内 input.h5。meshes、geometries 为空字典，conditions 为空列表：上述条件为本模型固定定义。
不得加入未声明的条件、参数或场。observations 为 points；coordinates 引用 float64[N,D] 的显式坐标。所有二维观测严格位于域内；一维允许端点。圆环坐标为 (r*cos(theta),r*sin(theta))，径向球对称问题的单坐标为 r。
location 对象名为 observations，其 ids 引用非负、唯一、有序身份 int64[N]；行顺序只由该轴决定。IDs 均须实际读取；points 位置还必须读取 coordinates，entities 没有坐标。
允许 N 在1到65536之间；圆管特征值任务固定 N=1。
time_axes.output 引用 float64[1]：唯一物理终止时刻 50.0；不是内部步长。所有数组 key 从 manifest 引用读取，不依赖文件中的默认命名。

唯一 fields 对象 weights：quantity="observation_weight"，scalar，float64，[1,N,1]，components=["value"]，component_shape=[1]，unit="1"，location="observations"，time_axis="output"。
权重为严格正且有限的公开积分/观测权重，只决定公开评分的空间加权；无需提交。
一维/矩形权重可为一致点观测权或正控制体权；圆环权包含径向 Jacobian，球对称径向权包含壳体积。
输入不含必须使用的计算网格；可以在任意内部离散上求解后重建。

## 输出与采样语义

- `u`：quantity="u"，默认 array="u"。
- `w`：quantity="w"，默认 array="w"。
- `b`：quantity="b"，默认 array="b"。
- `p`：quantity="p"，默认 array="p"。


每个 outputs 对象均为 scalar、float64、component_shape=[1]、components=["value"]、unit="1"，location="observations"，time_axis="output"，数组 shape=[1,N,1]。
value_kind="point"；输出是连续解在给定坐标的点值，不是任意计算单元的平均值。
只导出 outputs 引用的数值数组以及原样复制的 IDs 和输出时间轴；不导出输入权重、坐标、初态或其他未要求场。
需要所有字段及全部点；未要求的速度、压力、通量或特征向量不作为额外必交物。
