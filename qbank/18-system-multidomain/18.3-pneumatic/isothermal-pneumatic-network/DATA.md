# isothermal-pneumatic-network 数据契约

入口problem.json与data_file所指扁平HDF5，路径相对清单。physics恰含model、parameters；model=`systems-isothermal-pneumatic-network-v1`，task可省略，出现须为`isothermal-pneumatic-network`。禁止profile、contract_version、analysis、materials混用，不接受本题未列的参数、条件、字段、位置或输出quantity。

## 物理与初边值

固定容腔理想气体，所有节点由充分恒温换热维持同一给定绝对温度Tg，气体比气体常数Rg。每节点绝对压力p>0满足[V_i/(Rg Tg)] p_dot=s_i−(B mdot)_i。
每条有向长毛细管a→b的质量流率mdot=H_e(p_a²−p_b²)，H>0为已给定等温层流导通系数，沿a→b为正。B为尾端+1、首端−1关联矩阵。不另用喷口临界流／绝热关系或以表压代入平方关系。管内储存与动量惯性忽略；初始绝对压力p0给定。

正式数据核验全程p>0、理想气体／等温层流毛细管假设和预算内可达精度；不将元件导通关系解释为任意压比喷口模型。

## 参数

parameters恰含下表所有项，每项仅value、unit，value为有限JSON实数，布尔不算数值，不隐式换单位。

| 键 | unit | 定义 |
|---|---|---|
| `gas_constant` | `J/(kg.K)` | Rg，比气体常数，严格正 |
| `gas_temperature` | `K` | Tg，共同恒定绝对温度，严格正 |


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
| `volume` | `m3` | float64 scalar [1] / value | V，固定容腔体积；严格正 |

### `edge_properties`

role=`material`，location=`edges`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `endpoints` | `1` | int64 components [2] / tail,head | [tail,head]为nodes中的实际int64 ID，不是行号；两端不同；按定义 |
| `conductance` | `kg/(s.Pa2)` | float64 scalar [1] / value | H，固定毛细质量导通系数；严格正 |

### `initial_nodes`

role=`initial`，location=`nodes`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `pressure` | `Pa` | float64 scalar [1] / value | p0>0，初始绝对压力；严格正 |

### `driving`

role=`source`，location=`nodes`，全部字段time_axis=`load`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `mass_injection` | `kg/s` | float64 scalar [1] / value | s，节点外部质量注入，允许有符号抽取；按定义 |

condition片段示意（不是完整样例，逻辑名可变）：

```json
{"data":{"volume":{"field":"input_property"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求；逻辑输出名、array key自由但不得重复占用key。均为response轴、float64、point、无sampling；scalar为[1]/value，多分量按表。不重排或取绝对值，不按图方向重新定向。

| quantity | unit | location | shape／components | 定义 |
|---|---|---|---|---|
| `absolute_pressure` | `Pa` | `nodes` | [1] / value | 节点绝对压力p |
| `mass_flow` | `kg/s` | `edges` | [1] / value | 支路mdot，正向a→b |

结果HDF5恰含全部输出array、输出使用的locations之IDs和response时间数组，严格复制输入轴／身份。不额外写入属性、拓扑、未被输出复用的时间轴、坐标或其他数组；若输入不同轴共用相同key，只按输出需要复制一次，遵守CONTRACT的角色规则。

## 接收限制与证据

输入场／输出场各至多2000000数值分量，包含所有时间和分量轴，重复请求也计入。正式数据还须核验方程和元件适用性、全程状态接收限制、观测存在唯一性、参考误差及预算内可达精度；声明检查不会求解轨迹或代替这些证据。
