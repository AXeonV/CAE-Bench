# normal-contact 数据契约

入口为UTF-8 problem.json及其data_file指定的扁平HDF5，路径相对清单解释。考生仅需本题instruction、DATA和通用CONTRACT。`spatial_dimension=2`；`physics`恰含model、parameters，model固定为`multibody-normal-contact-v1`；task可省略，出现时须为`normal-contact`。不允许profile、analysis、materials、contract_version。无未列键、条件或隐藏默认值。

## 物理与方法边界

平面圆盘以质心x、连续转角θ、速度v、自旋ω、质量m、惯量I及半径r表示，无关节、无地面接触。只对显式列出的不同圆盘对施加接触，未列对不相互作用。候选对可共享圆盘。对a、b取d=x_b−x_a、l=|d|>0、n=d/l、t=(-n_y,n_x)、δ=r_a+r_b−l，u_n=(v_b−v_a)·n。δ>0时N=max(0,kn δ−cn u_n)，δ≤0时N=0；接触对b施加Nn，对a反向，无接触转矩。m v̇=F+ΣFcontact、I ω̇=torque、ẋ=v、θ̇=ω。合外力已含重力。接触是本题指定的有限刚度材料响应，不是刚性非穿透约束；不得自行增加恢复系数或冲量跳跃。

## 全局参数

parameters恰为下表全部项，各项为带单位有限标量的value/unit对象，布尔值不能作数值。

| 参数名 | 单位 | 含义及范围 |
|---|---|---|
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 终止时刻tf，tf>t0 |

## 位置与身份

`meshes={}`、`geometries={}`。locations全部为CONTRACT的entities，记录恰为kind=entities及ids引用；没有coordinates或伪造网格。每个实体的状态或参数保留自己的ID，物理位置来自输入场及条件参数。实际ID可不连续，不能用数组行号代替ID。保留位置名`bodies`，N=1..32。每个ID是一个可动刚体，不含地面。辅助位置每个含一个ID，恰被一条contact记录使用；a、b均是bodies中的实际ID，且a≠b，同一无序体对不得重复。只计算显式候选对，允许一个刚体参与多对。最多129个locations；所有ID为CONTRACT规定的非负、严格递增int64，辅助位置ID不跨location配对。

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
| `radius` | field引用；scalar [1]；m；圆盘半径r>0；惯量独立给定，质量可非均匀 |


### `loads`

role=`source`、variable=`load`、operator=`loads`；location=`bodies`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `force` | field引用；vector [2]；N；全局质心合外力，已包含重力 |
| `torque` | field引用；scalar [1]；N.m；质心合外转矩，逆时针为正 |


### `contact`

role=`boundary`、variable=`contact`、operator=`contact`；location=任意单ID辅助entities位置，每个辅助location恰好一条记录；其ID只在本location内有意义。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `a` | 常量`{"value":数值,"unit":"1"}`；第a体实际ID；须整数（不接受小数形式或布尔值） |
| `b` | 常量`{"value":数值,"unit":"1"}`；第b体实际ID；须整数（不接受小数形式或布尔值） |
| `stiffness` | 常量`{"value":数值,"unit":"N/m"}`；法向刚度kn>0 |
| `damping` | 常量`{"value":数值,"unit":"kg/s"}`；法向阻尼cn≥0；≥0 |

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

初态及全程须保持l>0，最大重叠不超过较小半径的5%；可从已接触的压缩状态开始，不要求初始δ=0。输出仅位置及速度，不请求接触切换时不唯一的加速度。正式数据须核验相容性、唯一连续分支、所请求观测存在、无有限时间发散，并以独立基准证实预算内能达到目标。几何／约束适定、精度及预算目前没有正式数值验证；合法格式不能替代这些证据。
每个输入轴至多201帧，输入字段与输出字段各自总分量数至多2000000；不是对HDF5压缩后字节数的约束。
