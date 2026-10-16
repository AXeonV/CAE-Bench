# planar-multibody 数据契约

入口为UTF-8 problem.json及其data_file指定的扁平HDF5，路径相对清单解释。考生仅需本题instruction、DATA和通用CONTRACT。`spatial_dimension=2`；`physics`恰含model、parameters，model固定为`multibody-planar-multibody-v1`；task可省略，出现时须为`planar-multibody`。不允许profile、analysis、materials、contract_version。无未列键、条件或隐藏默认值。

## 物理与方法边界

平面刚体以质心x=(x,y)和连续展开转角θ描述，局部锚点s的全局位置p=x+R(θ)s，R=[[cosθ,−sinθ],[sinθ,cosθ]]。地面ID=-1，x=0、θ=0、速度及加速度均为0；地面锚点直接是全局坐标。a、b不能相同。外力作用于质心，外转矩逆时针为正；没有额外重力、浮力、隐含阻尼或碰撞。

revolute精确约束p_b−p_a=0（x、y两行）；weld再加θ_b−θ_a−angle=0（第三行）。关节理想无摩擦、无质量。各记录按location名的Unicode字典序排列，同一记录内按上述行顺序拼接Φ；关节约束不含罚参数。分支由初始位形连续延拓；不在闭环的另一装配分支跳转。
本题不允许角驱动或弹性连接。M逐体为diag(m,m,I)，运动满足M q̈=Q+Φ_qᵀλ、Φ=0；λ只表示理想关节约束力。初态q0、q̇0满足位置及速度约束，Φ_q全程满行秩。允许无关节的自由体、多连杆及闭环，不允许切换关节拓扑。

## 全局参数

parameters恰为下表全部项，各项为带单位有限标量的value/unit对象，布尔值不能作数值。

| 参数名 | 单位 | 含义及范围 |
|---|---|---|
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 终止时刻tf，tf>t0 |

## 位置与身份

`meshes={}`、`geometries={}`。locations全部为CONTRACT的entities，记录恰为kind=entities及ids引用；没有coordinates或伪造网格。每个实体的状态或参数保留自己的ID，物理位置来自输入场及条件参数。实际ID可不连续，不能用数组行号代替ID。保留位置名`bodies`，N=1..32。每个ID是一个可动刚体，不含地面。辅助位置仅供下列关节记录使用，每个含一个ID，不得与bodies同名；每个辅助位置必须被且仅被一条记录使用。a、b参数引用bodies中的实际ID；仅关节允许-1地面，且不得两端均为地面。同一无序体对允许不同锚点连接，但不得有冗余约束。最多129个locations；所有ID为CONTRACT规定的非负、严格递增int64，辅助位置ID不跨location配对。

## 时间和字段

必须有名为`initial`的单帧轴[t0]和名为`response`的输出轴，response全在[t0,tf]内、至多201帧且非空。其他轴仅可用于loads引用的场；这些加载轴单帧时必须为[t0]，表示整个[t0,tf]常量，多帧时首末恰为t0、tf，逐分量连续分段线性插值，不外推。非loads字段均为initial轴单帧常量，不在时间上演化；字段名带0表示真实初态。输出时刻不是内部积分步；不得跳过未请求的中间载荷历史。所有输入field显式sampling：space="uniform"，time在loads多帧时为"linear"、其余"constant"，extrapolation="forbid"。uniform表示每个独立ID自身的离散参数，不在不同ID间作空间重建、平滑或平均。

所有表内字段均float64；kind=scalar固定shape=[1]、components=["value"]；vector使用全局前D分量及["x","y","z"]的前D项；所有数组为[T,N,*shape]，保留时间、ID、分量轴。表中角度使用rad及其时间导数；这里rad不是度。字段对象名和array key均自由，quantity对输入必须恰等于引用它的data键名，单位／kind／shape严格按表。字段必须和条件同location，不允许常量简写替代field，即使均匀亦然。输入fields恰为被条件引用的字段；同一field可复用，但不能靠同shape跨ID错配。

## 条件全集

### `body`

role=`material`、variable=`body`、operator=`body`；location=`bodies`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `position0` | field引用；vector [2]；m；初始质心位置 |
| `angle0` | field引用；scalar [1]；rad；初始体到全局转角θ0；不取模 |
| `mass` | field引用；scalar [1]；kg；质量m>0 |
| `inertia` | field引用；scalar [1]；kg.m2；质心平面转动惯量I>0 |
| `velocity0` | field引用；vector [2]；m/s；初始质心速度 |
| `omega0` | field引用；scalar [1]；rad/s；初始角速度ω，逆时针为正 |


### `loads`

role=`source`、variable=`load`、operator=`loads`；location=`bodies`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `force` | field引用；vector [2]；N；全局质心合外力，已包含重力 |
| `torque` | field引用；scalar [1]；N.m；质心合外转矩，逆时针为正 |


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

body及loads均恰一条覆盖bodies，不允许按子集拆分。未列出的算子一律不允许；字段正值要求见表。常量参数不能使用field替代。

## 输出

outputs逻辑名及array key自由；每个quantity必须出现，允许重复请求但每次须覆盖对应完整位置。输出轴恰为response；均float64、value_kind=point，不含sampling。

| quantity | 分量、单位与含义 | 位置 |
|---|---|---|
| `position` | vector [2]；m；全局质心位置 | `bodies`全部IDs |
| `angle` | scalar [1]；rad；连续展开的体到全局转角θ，不按2π取模 | `bodies`全部IDs |
| `velocity` | vector [2]；m/s；全局质心速度 | `bodies`全部IDs |
| `angular_velocity` | scalar [1]；rad/s；逆时针角速度ω | `bodies`全部IDs |

结果HDF5仅含输出arrays、所需IDs及时间轴，不重复坐标或输入字段；严格遵守输入行序。不能对角度取模、对速度作平移拟合或按量级重新归一化。

## 接收边界

所有理想约束必须全程独立，初态满足对应位置／速度约束；这属于数据接收保证，不由结构校验器证明。约束作用力只由Φ_qᵀλ定义，不能另加杆长、摩擦、驱动弹簧或稳定化物理。正式数据须核验相容性、唯一连续分支、所请求观测存在、无有限时间发散，并以独立基准证实预算内能达到目标。几何／约束适定、精度及预算目前没有正式数值验证；合法格式不能替代这些证据。
每个输入轴至多201帧，输入字段与输出字段各自总分量数至多2000000；不是对HDF5压缩后字节数的约束。
