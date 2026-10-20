# 2.13.23 圆管扰动的最右增长率：数据与连续定义

遵循 [CONTRACT](../../../../docs/CONTRACT.md)。task="cc-pipe-flow-disk-evp"，physics.model="cfdcodebench-c23-v1"，spatial_dimension=1。
协议坐标和时刻遵守 CONTRACT，分别以 m、s 表示。下面连续方程使用归一化坐标 x*=x/(1 m)、时间 t*=t/(1 s)，省略星号；两者数值恰与协议值相同，不另换算。所有输出场及公开权重为题定无量纲量，单位字符串为 "1"；温度读数的标度如本页特别说明。
physics.parameters={}；模型及其固定参数由本页完整定义，不读取外部默认配置。

## 连续问题

\[
\text{Linearized incompressible Navier–Stokes equations (in cylindrical coordinates):} \\
\nabla \cdot \mathbf{u} + \partial_z w = 0 \\
s \mathbf{u} + w_0 \partial_z \mathbf{u} + \nabla p - \frac{1}{Re}(\nabla^2 \mathbf{u} + \partial_z^2 \mathbf{u}) = 0 \\
s w + w_0 \partial_z w + \mathbf{u} \cdot \nabla w_0 + \partial_z p - \frac{1}{Re}(\nabla^2 w + \partial_z^2 w) = 0
\]

where:
- \( \mathbf{u}(r, \phi) \): in-plane perturbation velocity
- \( w(r, \phi) \): axial velocity perturbation
- \( p(r, \phi) \): pressure perturbation
- \( s \): eigenvalue representing temporal growth/decay rate
- \( w_0(r,z) = 1 - r^2 \): laminar background flow
- \( Re = 10^4 \): Reynolds number

计算域与时间范围：

- Radial domain: \( r \in [0, 1] \)
- Azimuthal domain: \( \phi \in [0, 2\pi] \)
- Axial domain: \( z \in (-\infty, \infty) \), represented by a fixed axial wave number \( k_z = 1 \); use azimuthal wave number \( m = 5 \)

边界：

- No-slip at the pipe wall \( r = 1 \):
  - \( \mathbf{u}(r=1) = 0 \)
  - \( w(r=1) = 0 \)
- Periodic in azimuthal \( \phi \) and axial \( z \) directions (implicitly handled by Fourier expansion)

初态：

稳态或特征值任务无物理时间初态。

补充及优先定义：

取非零速度模态 exp(s*t+i*m*phi+i*kz*z)，固定 m=5、kz=1、Re=10000；取该物理谱实部最大的增长率，只输出其实部。横向 grad/div/向量 Laplace 是欧氏圆盘算子，不能漏曲率耦合；中心要求笛卡尔光滑与有限能正则性。无需提交特征向量。



## 实际输入

problem.json 的 data_file 指向包内 input.h5。meshes、geometries 为空字典，conditions 为空列表：上述条件为本模型固定定义。
不得加入未声明的条件、参数或场。observations 为 entities，恰有一个模态身份；没有伪坐标，s 是该模态族最右实增长率。
location 对象名为 observations，其 ids 引用非负、唯一、有序身份 int64[N]；行顺序只由该轴决定。IDs 均须实际读取；points 位置还必须读取 coordinates，entities 没有坐标。
允许 N 在1到65536之间；圆管特征值任务固定 N=1。
time_axes.output 引用 float64[1]：稳态或谱观测标记0，不是迭代时间。所有数组 key 从 manifest 引用读取，不依赖文件中的默认命名。

唯一 fields 对象 weights：quantity="observation_weight"，scalar，float64，[1,N,1]，components=["value"]，component_shape=[1]，unit="1"，location="observations"，time_axis="output"。
权重为严格正且有限的公开积分/观测权重，只决定公开评分的空间加权；无需提交。
一维/矩形权重可为一致点观测权或正控制体权；圆环权包含径向 Jacobian，球对称径向权包含壳体积。
输入不含必须使用的计算网格；可以在任意内部离散上求解后重建。

## 输出与采样语义

- `s`：quantity="s"，默认 array="s"。


每个 outputs 对象均为 scalar、float64、component_shape=[1]、components=["value"]、unit="1"，location="observations"，time_axis="output"，数组 shape=[1,N,1]。
value_kind="point"；这是实体身份上的谱标量，不作空间点采样或空间积分。
只导出 outputs 引用的数值数组以及原样复制的 IDs 和输出时间轴；不导出输入权重、坐标、初态或其他未要求场。
需要所有字段及全部点；未要求的速度、压力、通量或特征向量不作为额外必交物。
