# radiative-thermal-network 数据契约

入口problem.json与data_file所指扁平HDF5，路径相对清单。physics恰含model、parameters；model=`systems-radiative-thermal-network-v1`，task可省略，出现须为`radiative-thermal-network`。禁止profile、contract_version、analysis、materials混用，不接受本题未列的参数、条件、字段、位置或输出quantity。

## 物理与初边值

节点为等温储热体，绝对温度T_i、正热容C_i；C_i T_dot=S_i−(B q)_i+h_i(Ta_i−T_i)+sigmaSB Aenv_i(Ta_i^4−T_i^4)。
支路a→b传热率q=g_e(T_a−T_b)+sigmaSB Arad_e(T_a^4−T_b^4)，正向a→b。B为尾端+1、首端−1关联矩阵。sigmaSB固定5.670374419e−8 W/(m2.K4)。
Arad和Aenv是包含发射率、面积及交换因子的非负有效辐射面积，由输入直接给定，不再从几何推导或重复乘发射率。h是对节点独立外界温度Ta的传导／对流热导，不是单位面积换热系数。所有初始绝对温度T0给定。

实际数据保证全程正温度及集总均温／常热容适用。外界温度是给定热浴，不另计入节点图或未知状态。

## 参数

parameters为空对象，所有元件系数均由下列material字段逐对象给定，没有隐含全局数值参数。

## 对象、拓扑和身份

spatial_dimension=1，为一维端口／支路坐标标记；geometries、meshes均为空对象，没有缺失的CAD或求解网格。locations恰含nodes、edges，均为entities；nodes 2..128个真实储能节点，edges 1..256条真实元件支路。各自IDs为非负严格递增int64；不同表可出现相同ID，不能据此配对。无coordinates。edge_properties.endpoints的每行[tail,head]引用nodes的实际ID，禁止自环；忽略方向后的整个图须连通，允许环与并联，不以支路方向限制实际流动方向。除题目明文的对参考／环境连接外，没有未声明节点或支路。组件字段按所属location的ID行序，不按端点行序或ID数值作数组下标。

## 时间、存储与重建

time_axes恰含static、load、response。static引用float64[1]=[0.0]，用于不随时间变的属性和t=0初态。load引用float64[2..256]，从0严格递增至t_end>0。response引用float64[1..256]，严格递增且全部在[0,t_end]，可不含0或终点。load字段逐分量在相邻节点间线性插值，禁止外推；不同实体之间不插值。输出时刻不是内部积分步或控制更新时刻。

全部场的value_kind=point，表示对象自身的状态、参数或端口值，不能解释为任意空间点或区域平均／积分。数组必须有完整[T,N,*component_shape]。标量float64字段kind=scalar、component_shape=[1]、components=["value"]；多分量字段kind=components、shape和标签按下表。仅endpoints为int64；其他场均float64。输出均float64、response轴、不带sampling。

每个条件data键必须恰为{"field":"逻辑字段名"}；不接受value常量、内联数组、option或location替代，重复的相同元件值也显式写入数组。逻辑field名及array key可自由选择且可不同，quantity严格等于data键名；字段location与条件完全一致，单位／类型／轴按下表。fields恰为实际引用字段；同一字段可以被符合相同声明的多个条件引用，但不能用数组长度替代位置身份。

输入sampling显式为space=uniform、extrapolation=forbid；static字段time=constant，load字段time=linear。uniform不表示整个图数值相同，仅表示每个离散对象自身的属性／端口量，不进行对象间插值。static的material字段全程不变，initial字段只定义t=0而非迭代初猜；没有其他隐含初态或预平衡。

## 条件全集

每个下列operator恰一条，覆盖完整对应location。variable固定system_data；role、location如下；condition恰含role、variable、operator、location、data五键，data恰含该表全部键。表内“正／非负”约束作用于该字段所有值；未限制者为任意有限有符号实数。所有单位严格按表。

### `node_properties`

role=`material`，location=`nodes`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `heat_capacity` | `J/K` | float64 scalar [1] / value | C，节点集总热容；严格正 |
| `ambient_conductance` | `W/K` | float64 scalar [1] / value | h，节点对外界热导；非负 |
| `ambient_radiative_area` | `m2` | float64 scalar [1] / value | Aenv，对外界有效辐射面积；非负 |

### `edge_properties`

role=`material`，location=`edges`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `endpoints` | `1` | int64 components [2] / tail,head | [tail,head]为nodes中的实际int64 ID，不是行号；两端不同；按定义 |
| `conductance` | `W/K` | float64 scalar [1] / value | g，支路热导；严格正 |
| `radiative_area` | `m2` | float64 scalar [1] / value | Arad，支路有效辐射面积；非负 |

### `initial_nodes`

role=`initial`，location=`nodes`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `temperature` | `K` | float64 scalar [1] / value | T0，初始绝对温度；严格正 |

### `driving`

role=`source`，location=`nodes`，全部字段time_axis=`load`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `heat_source` | `W` | float64 scalar [1] / value | S，外部热率，正加热；按定义 |
| `ambient_temperature` | `K` | float64 scalar [1] / value | Ta，节点各自的外界绝对温度；严格正 |

condition片段示意（不是完整样例，逻辑名可变）：

```json
{"data":{"heat_capacity":{"field":"input_property"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求；逻辑输出名、array key自由但不得重复占用key。均为response轴、float64、point、无sampling；scalar为[1]/value，多分量按表。不重排、取绝对值或按图方向重新定向。

| quantity | unit | location | shape／components | 定义 |
|---|---|---|---|---|
| `temperature` | `K` | `nodes` | [1] / value | 节点绝对温度T |
| `heat_rate` | `W` | `edges` | [1] / value | 支路热率q，正向a→b |

结果HDF5恰含全部输出array、输出使用的locations之IDs和response时间数组，严格复制输入轴／身份。不额外写入属性、拓扑、未被输出复用的时间轴、坐标或其他数组；若输入不同轴共用相同key，只按输出需要复制一次，遵守CONTRACT的角色规则。

## 接收限制与证据

输入场／输出场各至多2000000数值分量，包含所有时间和分量轴，重复请求也计入。正式数据还须核验方程和元件适用性、全程状态接收限制、观测存在唯一性、参考误差及预算内可达精度；声明检查不会求解轨迹或代替这些证据。禁止以临时工具fixture作为正式输入或可信物理参考。
