# nonlinear-hydraulic-network 数据契约

入口problem.json与data_file所指扁平HDF5，路径相对清单。physics恰含model、parameters；model=`systems-nonlinear-hydraulic-network-v1`，task可省略，出现须为`nonlinear-hydraulic-network`。禁止profile、contract_version、analysis、materials混用，不接受本题未列的参数、条件、字段、位置或输出quantity。

## 物理与初边值

每节点为压力储存容腔，以共同恒定储槽压力为零点的表压p满足C_i p_dot=s_i−G_i p_i−(B q)_i。C为体积顺应性，G为对该共同储槽的线性泄漏导纳。
每支路a→b的体积流率q沿a→b为正，由R q+D q|q|=p_a−p_b唯一确定。R>0、D≥0，无液柱惯性；不能忽略平方压降或先指定流向。B为尾端+1、首端−1的关联矩阵。初始各节点p0给定，支路初流率由该瞬时压差关系确定。

实际数据保证全程无空化及元件模型有效；声明检查不证明该适用性。表压可为负，不擅加大气压到输出。

## 参数

parameters为空对象，所有元件系数均由下列material字段逐对象给定，没有隐含全局数值参数。

## 对象、拓扑和身份

spatial_dimension=1，为一维端口／支路坐标标记；geometries、meshes均为空对象，没有缺失的CAD或求解网格。locations恰含nodes、edges，均为entities；nodes 2..128个真实储能节点，edges 1..256条真实元件支路。各自IDs为非负严格递增int64；不同表可出现相同ID，不能据此配对。无coordinates。edge_properties.endpoints的每行[tail,head]引用nodes的实际ID，禁止自环；忽略方向后的整个图须连通，允许环与并联，不以支路方向限制实际流动方向。除题目明文的对参考／环境连接外，没有未声明节点或支路。组件字段按所属location的ID行序，不按端点行序或ID数值作数组下标。

## 时间、存储与重建

time_axes恰含static、load、response。static引用float64[1]=[0.0]，用于不随时间变的属性和t=0初态。load引用float64[2..256]，从0严格递增至t_end>0。response引用float64[1..256]，严格递增且全部在[0,t_end]，可不含0或终点。load字段逐分量在load轴相邻时间采样点之间线性插值，禁止外推；不同实体之间不插值。输出时刻不是内部积分步或控制更新时刻。

全部场的value_kind=point，表示对象自身的状态、参数或端口值，不能解释为任意空间点或区域平均／积分。数组必须有完整[T,N,*component_shape]。标量float64字段kind=scalar、component_shape=[1]、components=["value"]；多分量字段kind=components、shape和标签按下表。仅endpoints输入场为int64，其他输入场均float64；IDs为int64。输出均float64、response轴、不带sampling。

条件data中每个键对应的值必须恰为{"field":"逻辑字段名"}；不接受value常量、内联数组、option或location替代，重复的相同元件值也显式写入数组。逻辑field名及array key可自由选择且可不同，quantity严格等于data键名；字段location与条件完全一致，单位／类型／轴按下表。fields恰为实际引用字段；同一字段可以被符合相同声明的多个条件引用，但不能用数组长度替代位置身份。

输入sampling显式为space=uniform、extrapolation=forbid；static字段time=constant，load字段time=linear。uniform不表示整个图数值相同，仅表示每个离散对象自身的属性／端口量，不进行对象间插值。static的material字段全程不变，initial字段只定义t=0而非迭代初猜；没有其他隐含初态或预平衡。

## 条件全集

每个下列operator恰一条，覆盖完整对应location。variable固定system_data；role、location如下；condition恰含role、variable、operator、location、data五键，data恰含该表全部键。表内“正／非负”约束作用于该字段所有值；未限制者为任意有限有符号实数。所有单位严格按表。

### `node_properties`

role=`material`，location=`nodes`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `compliance` | `m3/Pa` | float64 scalar [1] / value | C，容腔体积顺应性；严格正 |
| `leakage` | `m3/(Pa.s)` | float64 scalar [1] / value | G，到共同压力零点的泄漏导纳；非负 |

### `edge_properties`

role=`material`，location=`edges`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `endpoints` | `1` | int64 components [2] / tail,head | [tail,head]为nodes中的实际int64 ID，不是行号；两端不同；按定义 |
| `resistance` | `Pa.s/m3` | float64 scalar [1] / value | R，线性流阻；严格正 |
| `quadratic_resistance` | `Pa.s2/m6` | float64 scalar [1] / value | D，平方压降系数；非负 |

### `initial_nodes`

role=`initial`，location=`nodes`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `pressure` | `Pa` | float64 scalar [1] / value | p0，初始表压；按定义 |

### `driving`

role=`source`，location=`nodes`，全部字段time_axis=`load`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `injection` | `m3/s` | float64 scalar [1] / value | s，外部流入节点体积流率，正为注入；按定义 |

condition片段示意（不是完整样例，逻辑名可变）：

```json
{"data":{"compliance":{"field":"input_property"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求；逻辑输出名、array key自由但不得重复占用key。均为response轴、float64、point、无sampling；scalar为[1]/value，多分量按表。不重排或取绝对值，不按图方向重新定向。

| quantity | unit | location | shape／components | 定义 |
|---|---|---|---|---|
| `pressure` | `Pa` | `nodes` | [1] / value | 节点表压p |
| `volume_flow` | `m3/s` | `edges` | [1] / value | 支路q，按a→b正向 |

结果HDF5恰含全部输出array、输出使用的locations之IDs和response时间数组，严格复制输入轴／身份。不额外写入属性、拓扑、未被输出复用的时间轴、坐标或其他数组；若输入不同轴共用相同key，只按输出需要复制一次，遵守CONTRACT的角色规则。

## 接收限制与证据

输入场／输出场各至多2000000数值分量，包含所有时间和分量轴，重复请求也计入。正式数据还须核验方程和元件适用性、全程状态接收限制、观测存在唯一性、参考误差及预算内可达精度；声明检查不会求解轨迹或代替这些证据。
