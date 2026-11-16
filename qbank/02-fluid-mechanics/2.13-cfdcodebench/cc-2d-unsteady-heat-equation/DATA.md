# 2.13.16 Gaussian 初温与持续热源：数据与连续定义

遵循 [CONTRACT](../../../../docs/CONTRACT.md)。task="cc-2d-unsteady-heat-equation"，physics.model="cfdcodebench-c16-v1"，spatial_dimension=2。
协议坐标和时刻遵守 CONTRACT，分别以 m、s 表示。下面连续方程使用归一化坐标 x*=x/(1 m)、时间 t*=t/(1 s)，省略星号；两者数值恰与协议值相同，不另换算。所有输出场及公开权重为题定无量纲量，单位字符串为 "1"；温度读数的标度如本页特别说明。
physics.parameters={}；模型及其固定参数由本页完整定义，不读取外部默认配置。

## 连续问题

\[
\frac{\partial T}{\partial t} - \alpha \left( \frac{\partial^2 T}{\partial x^2} + \frac{\partial^2 T}{\partial y^2} \right) = q(x, y, t)
\]

where:
- \( T(x, y, t) \): temperature field over time
- \( \alpha = 1 \): thermal diffusivity
- \( q(x, y, t) = Q_0 \exp\left(-\frac{x^2 + y^2}{2\sigma^2} \right) \): source term, with \( Q_0 = 200°C/s \) and \( \sigma = 0.1 \)

计算域与时间范围：

- Spatial domain: \( x, y \in [-1, 1] \), Temporal domain: \(t \in [0, 3]\)

边界：

\[ T(x, y, t) = 1 \quad \text{on all boundaries} \]

初态：

\[ T(x, y, 0) = 1 + 200 \cdot \exp\left(-\frac{x^2 + y^2}{2 \cdot 0.1^2}\right) \]

补充及优先定义：

t>0 边温1优先；内部初态按几乎处处意义给出。热源持续作用至终时，不能省略；评分背景为1。所有数值均无量纲。

温度 T 的候选与参考均减去公开固定背景1后计算尺度及误差。

## 实际输入

problem.json 的 data_file 指向包内 input.h5。meshes、geometries 为空字典，conditions 为空列表：上述条件为本模型固定定义。
不得加入未声明的条件、参数或场。observations 为 points；coordinates 引用 float64[N,D] 的显式坐标。所有二维观测严格位于域内；一维允许端点。圆环坐标为 (r*cos(theta),r*sin(theta))，径向球对称问题的单坐标为 r。
location 对象名为 observations，其 ids 引用非负、唯一、有序身份 int64[N]；行顺序只由该轴决定。IDs 均须实际读取；points 位置还必须读取 coordinates，entities 没有坐标。
允许 N 在1到65536之间；圆管特征值任务固定 N=1。
time_axes.output 引用 float64[1]：唯一物理终止时刻 3.0；不是内部步长。所有数组 key 从 manifest 引用读取，不依赖文件中的默认命名。

唯一 fields 对象 weights：quantity="observation_weight"，scalar，float64，[1,N,1]，components=["value"]，component_shape=[1]，unit="1"，location="observations"，time_axis="output"。
权重为严格正且有限的公开积分/观测权重，只决定公开评分的空间加权；无需提交。
一维/矩形权重可为一致点观测权或正控制体权；圆环权包含径向 Jacobian，球对称径向权包含壳体积。
输入不含必须使用的计算网格；可以在任意内部离散上求解后重建。

## 输出与采样语义

- `T`：quantity="T"，默认 array="T"。


每个 outputs 对象均为 scalar、float64、component_shape=[1]、components=["value"]、unit="1"，location="observations"，time_axis="output"，数组 shape=[1,N,1]。
value_kind="point"；输出是连续解在给定坐标的点值，不是任意计算单元的平均值。
只导出 outputs 引用的数值数组以及原样复制的 IDs 和输出时间轴；不导出输入权重、坐标、初态或其他未要求场。
需要所有字段及全部点；未要求的速度、压力、通量或特征向量不作为额外必交物。
