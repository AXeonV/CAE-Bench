# 2.13.14 双 Gaussian 源 Poisson 势：数据与连续定义

遵循 [CONTRACT](../../../../docs/CONTRACT.md)。task="cc-2d-poisson-equation"，physics.model="cfdcodebench-c14-v1"，spatial_dimension=2。
协议坐标和时刻遵守 CONTRACT，分别以 m、s 表示。下面连续方程使用归一化坐标 x*=x/(1 m)、时间 t*=t/(1 s)，省略星号；两者数值恰与协议值相同，不另换算。所有输出场及公开权重为题定无量纲量，单位字符串为 "1"；温度读数的标度如本页特别说明。
physics.parameters={}；模型及其固定参数由本页完整定义，不读取外部默认配置。

## 连续问题

\[
\frac{\partial^2 p}{\partial x^2} + \frac{\partial^2 p}{\partial y^2} = b(x, y)
\]

where:
- \( p(x, y) \): scalar potential (e.g., pressure)
- \( b(x, y) \): source term made of two Gaussian sources of width \( \sigma = 0.05 \):
\[
  b = 100\, e^{-\left[(x - L_x/4)^2 + (y - L_y/4)^2\right] / (2\sigma^2)} - 100\, e^{-\left[(x - 3L_x/4)^2 + (y - 3L_y/4)^2\right] / (2\sigma^2)}, \quad L_x = 2,\ L_y = 1
\]

计算域与时间范围：

- Spatial domain: \( x \in [0, 2], y \in [0, 1] \)

边界：

- Dirichlet boundary conditions:
  \( p = 0 \) at \( x = 0, 2 \) and \( y = 0, 1 \)

初态：

稳态或特征值任务无物理时间初态。

补充及优先定义：

p 是有固定 Dirichlet 边界的势，不消均值。零初值仅为稳态迭代猜测。



## 实际输入

problem.json 的 data_file 指向包内 input.h5。meshes、geometries 为空字典，conditions 为空列表：上述条件为本模型固定定义。
不得加入未声明的条件、参数或场。observations 为 points；coordinates 引用 float64[N,D] 的显式坐标。所有二维观测严格位于域内；一维允许端点。圆环坐标为 (r*cos(theta),r*sin(theta))，径向球对称问题的单坐标为 r。
location 对象名为 observations，其 ids 引用非负、唯一、有序身份 int64[N]；行顺序只由该轴决定。IDs 均须实际读取；points 位置还必须读取 coordinates，entities 没有坐标。
允许 N 在1到65536之间；圆管特征值任务固定 N=1。
time_axes.output 引用 float64[1]：稳态或谱观测标记0，不是迭代时间。所有数组 key 从 manifest 引用读取，不依赖文件中的默认命名。

唯一 fields 对象 weights：quantity="observation_weight"，scalar，float64，[1,N,1]，components=["value"]，component_shape=[1]，unit="1"，location="observations"，time_axis="output"。
权重为严格正且有限的公开积分/观测权重，只决定公开评分的空间加权；无需提交。
一维/矩形权重可为一致点观测权或正控制体权；圆环权包含径向 Jacobian，球对称径向权包含壳体积。
输入不含必须使用的计算网格；可以在任意内部离散上求解后重建。

## 输出与采样语义

- `p`：quantity="p"，默认 array="p"。


每个 outputs 对象均为 scalar、float64、component_shape=[1]、components=["value"]、unit="1"，location="observations"，time_axis="output"，数组 shape=[1,N,1]。
value_kind="point"；输出是连续解在给定坐标的点值，不是任意计算单元的平均值。
只导出 outputs 引用的数值数组以及原样复制的 IDs 和输出时间轴；不导出输入权重、坐标、初态或其他未要求场。
需要所有字段及全部点；未要求的速度、压力、通量或特征向量不作为额外必交物。
