# spatial-free-rigid 数据契约

入口为UTF-8 problem.json及其data_file指定的扁平HDF5，路径相对清单解释。考生仅需本题instruction、DATA和通用CONTRACT。`spatial_dimension=3`；`physics`恰含model、parameters，model固定为`multibody-spatial-free-rigid-v1`；task可省略，出现时须为`spatial-free-rigid`。不允许profile、analysis、materials、contract_version。无未列键、条件或隐藏默认值。

## 物理与方法边界

本题由相互独立的三维自由刚体组成，无关节和接触。每体以质心全局坐标x、全局速度v、体坐标角速度ω及体到全局的单位四元数q=(w,xq,yq,zq)表示。使用Hamilton乘法，(w,u)⊗(s,v)=(ws−u·v,wv+su+u×v)，R(q)a由q⊗(0,a)⊗q*的向量部分给出。动力学为m v̇=F、ẋ=v、I ω̇+ω×(Iω)=τ、q̇=0.5 q⊗(0,ω)。I和τ均在随体坐标；F在全局。惯性关于质心，恒定对称正定且主惯量满足三角不等式，初始四元数范数1（接收容差1e-12）。姿态从给定初态连续演化，q和−q不作为可任意切换的输出；不能每帧强制w≥0。没有额外重力或阻尼。

## 全局参数

parameters恰为下表全部项，各项为带单位有限标量的value/unit对象，布尔值不能作数值。

| 参数名 | 单位 | 含义及范围 |
|---|---|---|
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 终止时刻tf，tf>t0 |

## 位置与身份

`meshes={}`、`geometries={}`。locations全部为CONTRACT的entities，记录恰为kind=entities及ids引用；没有coordinates或伪造网格。每个实体的状态或参数保留自己的ID，物理位置来自输入场及条件参数。实际ID可不连续，不能用数组行号代替ID。保留位置名`bodies`，N=1..32。每个ID是一个可动刚体，不含地面。只允许保留位置，不允许其他location；所有ID为非负、严格递增int64。

## 时间和字段

必须有名为`initial`的单帧轴[t0]和名为`response`的输出轴，response全在[t0,tf]内、至多201帧且非空。其他轴仅可用于loads引用的场；这些加载轴单帧时必须为[t0]，表示整个[t0,tf]常量，多帧时首末恰为t0、tf，逐分量连续分段线性插值，不外推。非loads字段均为initial轴单帧常量，不在时间上演化；字段名带0表示真实初态。输出时刻不是内部积分步；不得跳过未请求的中间载荷历史。所有输入field显式sampling：space="uniform"，time在loads多帧时为"linear"、其余"constant"，extrapolation="forbid"。uniform表示每个独立ID自身的离散参数，不在不同ID间作空间重建、平滑或平均。

所有表内字段均float64；kind=scalar固定shape=[1]、components=["value"]；vector使用全局前D分量及["x","y","z"]的前D项；components类型采用表中shape，标签依行优先展平固定为c1,c2,...,cL（L是shape各维乘积）。所有数组为[T,N,*shape]，保留时间、ID、分量轴。表中角度使用rad及其时间导数；这里rad不是度。字段对象名和array key均自由，quantity对输入必须恰等于引用它的data键名，单位／kind／shape严格按表。字段必须和条件同location，不允许常量简写替代field，即使均匀亦然。输入fields恰为被条件引用的字段；同一field可复用，但不能靠同shape跨ID错配。

## 条件全集

### `body`

role=`material`、variable=`body`、operator=`body`；location=`bodies`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `mass` | field引用；scalar [1]；kg；质量m>0 |
| `inertia` | field引用；components [3,3]；kg.m2；质心体坐标惯性I，对称正定且三个主惯量满足三角不等式 |
| `position0` | field引用；vector [3]；m；初始质心位置 |
| `quaternion0` | field引用；components [4]；1；单位四元数，分量w,x,y,z；体坐标到全局的主动旋转 |
| `velocity0` | field引用；vector [3]；m/s；初始全局质心速度 |
| `omega0` | field引用；components [3]；rad/s；初始体坐标角速度，分量wx,wy,wz |


### `loads`

role=`source`、variable=`load`、operator=`loads`；location=`bodies`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `force` | field引用；vector [3]；N；全局质心合外力，已包含重力 |
| `torque` | field引用；components [3]；N.m；体坐标质心合外转矩 |


body及loads均恰一条覆盖bodies，不允许按子集拆分。未列出的算子一律不允许；字段正值要求见表；矩阵对称／正定含义按物理部分。常量参数不能使用field替代。

## 输出

outputs逻辑名及array key自由；每个quantity必须出现，允许重复请求但每次须覆盖对应完整位置。输出轴恰为response；均float64、value_kind=point，不含sampling。

| quantity | 分量、单位与含义 | 位置 |
|---|---|---|
| `position` | vector [3]；m；全局质心位置 | `bodies`全部IDs |
| `velocity` | vector [3]；m/s；全局质心速度 | `bodies`全部IDs |
| `quaternion` | components [4]；1；体到全局的四元数w,x,y,z，连续沿用初态符号 | `bodies`全部IDs |
| `angular_velocity` | components [3]；rad/s；体坐标角速度wx,wy,wz | `bodies`全部IDs |

结果HDF5仅含输出arrays、所需IDs及时间轴，不重复坐标或输入字段；严格遵守输入行序。不能对四元数逐帧切换符号、对速度作平移拟合或按量级重新归一化。

## 接收边界

正式数据须核验相容性、唯一连续分支、所请求观测存在、无有限时间发散，并以独立基准证实预算内能达到目标。几何／约束适定、精度及预算目前没有正式数值验证；合法格式不能替代这些证据。
每个输入轴至多201帧，输入字段与输出字段各自总分量数至多2000000；不是对HDF5压缩后字节数的约束。
