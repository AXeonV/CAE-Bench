# frictional-impact 数据契约

入口为UTF-8 problem.json及其data_file指定的扁平HDF5，路径相对清单解释。考生仅需本题instruction、DATA和通用CONTRACT。`spatial_dimension=2`；`physics`恰含model、parameters，model固定为`multibody-frictional-impact-v1`；task可省略，出现时须为`frictional-impact`。不允许profile、analysis、materials、contract_version。无未列键、条件或隐藏默认值。

## 物理与方法边界

每体恰属于一个互不共享圆盘的碰撞对；无地面、关节、持续力或耦合多接触。0标记瞬时事件。取n=(x_b−x_a)/|x_b−x_a|、t=(-n_y,n_x)、ρ_a=r_a n、ρ_b=−r_b n；ω×ρ=(-ωρ_y,ωρ_x)。碰前u=v_b+ω_b×ρ_b−v_a−ω_a×ρ_a，u_n=u·n<0、u_t=u·t。两体外切，接收容差为||x_b−x_a|−r_a−r_b|≤1e-10 max(1 m,r_a+r_b)，n由实际质心确定，不投影位置。j_n=−(1+e)u_n/(1/m_a+1/m_b)，K_t=1/m_a+1/m_b+r_a²/I_a+r_b²/I_b，j_t=clip(−u_t/K_t,−μj_n,μj_n)。作用于b的J=j_n n+j_t t，对a为−J；v_a⁺=v_a−J/m_a、v_b⁺=v_b+J/m_b，ω_a⁺=ω_a+[ρ_a×(−J)]/I_a、ω_b⁺=ω_b+(ρ_b×J)/I_b。叉积p×f=p_xf_y−p_yf_x。圆盘几何使法切向有效质量解耦；这是本题明确采用的Newton法向恢复与最大耗散切向截断，不推广到任意形状或冲量时程。

## 全局参数

parameters恰为下表全部项，各项为带单位有限标量的value/unit对象，布尔值不能作数值。

| 参数名 | 单位 | 含义及范围 |
|---|---|---|
| `restitution` | `1` | 法向恢复系数e；范围[0,1] |
| `friction` | `1` | 冲量库仑系数μ；≥0 |

## 位置与身份

`meshes={}`、`geometries={}`。locations全部为CONTRACT的entities，记录恰为kind=entities及ids引用；没有coordinates或伪造网格。每个实体的状态或参数保留自己的ID，物理位置来自输入场及条件参数。实际ID可不连续，不能用数组行号代替ID。保留位置名`bodies`，N=1..32。每个ID是一个可动刚体，不含地面。辅助位置每个含一个ID，恰被一条collision或contact记录使用；a、b均是bodies中的实际ID，且a≠b，同一无序体对不得重复。所有bodies被互不共享的碰撞对恰好覆盖。最多129个locations；所有ID为CONTRACT规定的非负、严格递增int64，辅助位置ID不跨location配对。

## 时间和字段

所有time_axes恰为`event`，值为单帧[0.0]；输入场和输出都引用event，初速度是事件前左极限，输出是事件后右极限。输入field sampling恰为{"space":"uniform","time":"constant","extrapolation":"forbid"}；不作时间插值。

所有表内字段均float64；kind=scalar固定shape=[1]、components=["value"]；vector使用全局前D分量及["x","y","z"]的前D项；所有数组为[T,N,*shape]，保留时间、ID、分量轴。角速度使用rad/s，不是度每秒。字段对象名和array key均自由，quantity对输入必须恰等于引用它的data键名，单位／kind／shape严格按表。字段必须和条件同location，不允许常量简写替代field，即使均匀亦然。输入fields恰为被条件引用的字段；同一field可复用，但不能靠同shape跨ID错配。

## 条件全集

### `body`

role=`material`、variable=`body`、operator=`body`；location=`bodies`，恰一条记录覆盖该位置全部IDs。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `position0` | field引用；vector [2]；m；初始质心位置 |
| `mass` | field引用；scalar [1]；kg；质量m>0 |
| `inertia` | field引用；scalar [1]；kg.m2；质心平面转动惯量I>0 |
| `velocity0` | field引用；vector [2]；m/s；初始质心速度 |
| `omega0` | field引用；scalar [1]；rad/s；初始角速度ω，逆时针为正 |
| `radius` | field引用；scalar [1]；m；圆盘半径r>0；惯量独立给定，质量可非均匀 |


### `collision`

role=`boundary`、variable=`collision`、operator=`collision`；location=任意单ID辅助entities位置，每个辅助location恰好一条记录；其ID只在本location内有意义。必须出现。 data恰含下列全部键：

| data键 | 表示及含义 |
|---|---|
| `a` | 常量`{"value":数值,"unit":"1"}`；第a体实际ID；须整数（不接受小数形式或布尔值） |
| `b` | 常量`{"value":数值,"unit":"1"}`；第b体实际ID；须整数（不接受小数形式或布尔值） |

body恰一条覆盖bodies，不允许按子集拆分。未列出的算子一律不允许；字段正值要求见表。常量参数不能使用field替代。

## 输出

outputs逻辑名及array key自由；每个quantity必须出现，允许重复请求但每次须覆盖对应完整位置。输出轴恰为event；均float64、value_kind=point，不含sampling。

| quantity | 分量、单位与含义 | 位置 |
|---|---|---|
| `post_velocity` | vector [2]；m/s；碰撞后全局质心速度 | `bodies`全部IDs |
| `post_omega` | scalar [1]；rad/s；碰撞后角速度 | `bodies`全部IDs |
| `impulse` | vector [2]；N.s；作用于b体的全局接触冲量J | 该算子每个辅助位置，全部记录均须被请求 |

结果HDF5仅含输出arrays、所需IDs及时间轴，不重复坐标或输入字段；严格遵守输入行序。不能对速度作平移拟合或按量级重新归一化。

## 接收边界

正式数据须核验相容性、唯一连续分支、所请求观测存在、无有限时间发散，并以独立基准证实预算内能达到目标。几何／约束适定、精度及预算目前没有正式数值验证；合法格式不能替代这些证据。
每个输入轴至多201帧，输入字段与输出字段各自总分量数至多2000000；不是对HDF5压缩后字节数的约束。
