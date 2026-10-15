# planar-kinematics 数据契约

入口为UTF-8 problem.json及其data_file指定的扁平HDF5，路径相对清单解释。考生仅需本题instruction、DATA和通用CONTRACT。`spatial_dimension=2`；`physics`恰含model、parameters，model固定为`multibody-planar-kinematics-v1`；task可省略，出现时须为`planar-kinematics`。不允许profile、analysis、materials、contract_version。无未列键、条件或隐藏默认值。

## 物理与方法边界

平面刚体以质心x=(x,y)和连续展开转角θ描述，局部锚点s的全局位置p=x+R(θ)s，R=[[cosθ,−sinθ],[sinθ,cosθ]]。地面ID=-1，x=0、θ=0、速度及加速度均为0；地面锚点直接是全局坐标。a、b不能相同。本题不求力和转矩，也不含碰撞。

revolute精确约束p_b−p_a=0（x、y两行）；weld再加θ_b−θ_a−angle=0（第三行）。关节理想无摩擦、无质量。各记录按location名的Unicode字典序排列，同一记录内按上述行顺序拼接Φ；角驱动为θ_body−d(t)=0，d=a0+a1τ+a2τ²+a3τ³、τ=t−t0。关节约束与驱动不含罚参数。分支由初始位形连续延拓；不在闭环的另一装配分支跳转。
本题必须有角驱动，关节加驱动的Φ_q为3n×3n且全程可逆；给定初始位形满足Φ=0。由Φ(q,t)=0确定位形，速度和加速度是该同一连续分支对物理时间的一、二阶导数。不需要质量、外力或动力学初速度。

## 全局参数

parameters恰为下表全部项，各项为带单位有限标量的value/unit对象，布尔值不能作数值。

| 参数名 | 单位 | 含义及范围 |
|---|---|---|
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 终止时刻tf，tf>t0 |

## 位置与身份

`meshes={}`、`geometries={}`。locations全部为CONTRACT的entities，记录恰为kind=entities及ids引用；没有coordinates或伪造网格。每个实体的状态或参数保留自己的ID，物理位置来自输入场及条件参数。实际ID可不连续，不能用数组行号代替ID。保留位置名`bodies`，N=1..32。每个ID是一个可动刚体，不含地面。辅助位置仅供下列关节／驱动记录使用，每个含一个ID，不得与bodies同名；每个辅助位置必须被且仅被一条记录使用。a、b、body参数引用bodies中的实际ID；关节允许-1地面，且不得两端均为地面。同一无序体对允许不同锚点连接，但不得有冗余约束。最多129个locations；所有ID为CONTRACT规定的非负、严格递增int64，辅助位置ID不跨location配对。

## 时间和字段

必须有名为`initial`的单帧轴[t0]和名为`response`的输出轴，response全在[t0,tf]内、至多201帧且非空。不允许其他时间轴或加载场。所有输入字段均为initial轴单帧常量，不在时间上演化；字段名带0表示真实初态。输出时刻不是内部积分步；驱动由全程多项式定义。所有输入field显式sampling：space="uniform"，time="constant"，extrapolation="forbid"。uniform表示每个独立ID自身的离散参数，不在不同ID间作空间重建、平滑或平均。

所有表内字段均float64；kind=scalar固定shape=[1]、components=["value"]；vector使用全局前D分量及["x","y","z"]的前D项；所有数组为[T,N,*shape]，保留时间、ID、分量轴。表中角度使用rad及其时间导数；这里rad不是度。字段对象名和array key均自由，quantity对输入必须恰等于引用它的data键名，单位／kind／shape严格按表。字段必须和条件同location，不允许常量简写替代field，即使均匀亦然。输入fields恰为被条件引用的字段；同一field可复用，但不能靠同shape跨ID错配。

## 条件全集

### `body`

role=`material`、variable=`body`、operator=`body`；location=`bodies`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `position0` | field引用；vector [2]；m；初始质心位置 |
| `angle0` | field引用；scalar [1]；rad；初始体到全局转角θ0；不取模 |


### `revolute`

role=`boundary`、variable=`joint`、operator=`revolute`；location=任意单ID辅助entities位置，每个辅助location恰好一条记录；其ID只在本location内有意义。可出现零条或多条。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `a` | 常量`{"value":数值,"unit":"1"}`；第a体的实际ID，-1为地面；须整数（不接受小数形式或布尔值） |
| `b` | 常量`{"value":数值,"unit":"1"}`；第b体实际ID，-1为地面；须整数（不接受小数形式或布尔值） |
| `ax` | 常量`{"value":数值,"unit":"m"}`；a体局部锚点x |
| `ay` | 常量`{"value":数值,"unit":"m"}`；a体局部锚点y |
| `bx` | 常量`{"value":数值,"unit":"m"}`；b体局部锚点x |
| `by` | 常量`{"value":数值,"unit":"m"}`；b体局部锚点y |

### `weld`

role=`boundary`、variable=`joint`、operator=`weld`；location=任意单ID辅助entities位置，每个辅助location恰好一条记录；其ID只在本location内有意义。可出现零条或多条。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `a` | 常量`{"value":数值,"unit":"1"}`；第a体的实际ID，-1为地面；须整数（不接受小数形式或布尔值） |
| `b` | 常量`{"value":数值,"unit":"1"}`；第b体实际ID，-1为地面；须整数（不接受小数形式或布尔值） |
| `ax` | 常量`{"value":数值,"unit":"m"}`；a体局部锚点x |
| `ay` | 常量`{"value":数值,"unit":"m"}`；a体局部锚点y |
| `bx` | 常量`{"value":数值,"unit":"m"}`；b体局部锚点x |
| `by` | 常量`{"value":数值,"unit":"m"}`；b体局部锚点y |
| `angle` | 常量`{"value":数值,"unit":"rad"}`；约束θb−θa的常值 |

### `angle_drive`

role=`boundary`、variable=`angle`、operator=`angle_drive`；location=任意单ID辅助entities位置，每个辅助location恰好一条记录；其ID只在本location内有意义。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `body` | 常量`{"value":数值,"unit":"1"}`；被驱动体实际ID，不允许地面；须整数（不接受小数形式或布尔值） |
| `a0` | 常量`{"value":数值,"unit":"rad"}`；驱动θ(t)常数项 |
| `a1` | 常量`{"value":数值,"unit":"rad/s"}`；一次项 |
| `a2` | 常量`{"value":数值,"unit":"rad/s2"}`；二次项 |
| `a3` | 常量`{"value":数值,"unit":"rad/s3"}`；三次项 |

body恰一条覆盖bodies，不允许按子集拆分。未列出的算子一律不允许；字段正值要求见表。常量参数不能使用field替代。

## 输出

outputs逻辑名及array key自由；每个quantity必须出现，允许重复请求但每次须覆盖对应完整位置。输出轴恰为response；均float64、value_kind=point，不含sampling。

| quantity | 分量、单位与含义 | 位置 |
|---|---|---|
| `position` | vector [2]；m；全局质心位置 | `bodies`全部IDs |
| `angle` | scalar [1]；rad；连续展开的体到全局转角θ，不按2π取模 | `bodies`全部IDs |
| `velocity` | vector [2]；m/s；全局质心速度 | `bodies`全部IDs |
| `angular_velocity` | scalar [1]；rad/s；逆时针角速度ω | `bodies`全部IDs |
| `acceleration` | vector [2]；m/s2；全局质心加速度 | `bodies`全部IDs |
| `angular_acceleration` | scalar [1]；rad/s2；逆时针角加速度 | `bodies`全部IDs |

结果HDF5仅含输出arrays、所需IDs及时间轴，不重复坐标或输入字段；严格遵守输入行序。不能对角度取模、对速度作平移拟合或按量级重新归一化。

## 接收边界

所有理想约束必须全程独立，初始位形满足位置约束，初速度由驱动唯一确定；这属于数据接收保证，不由结构校验器证明。不求约束反力或驱动转矩，不得增加隐含自由度或改变给定关节。正式数据须核验相容性、唯一连续分支、所请求观测存在、无有限时间发散，并以独立基准证实预算内能达到目标。几何／约束适定、精度及预算目前没有正式数值验证；合法格式不能替代这些证据。
每个输入轴至多201帧，输入字段与输出字段各自总分量数至多2000000；不是对HDF5压缩后字节数的约束。
