# electrohydraulic-actuator-system 数据契约

入口problem.json与data_file所指扁平HDF5，路径相对清单。physics恰含model、parameters；model=`systems-electrohydraulic-actuator-system-v1`，task可省略，出现须为`electrohydraulic-actuator-system`。禁止profile、contract_version、analysis、materials混用，不接受本题未列的参数、条件、字段、位置或输出quantity。

## 物理与初边值

每个systems对象为一套独立闭式电机泵—双腔液压缸—弹簧阻尼质量系统。变量i、omega、x、v、pA、pB；pA/B为相对共同参考绝对压力p0的表压。
L i_dot=U−R0 i−K omega；J omega_dot=K i−B omega−D(pA−pB)；
Q=D omega−Cl(pA−pB)，正流量从腔B泵往腔A；x_dot=v；M v_dot=A(pA−pB)−c v−k x−F；
VA=VA0+A x，VB=VB0−A x；pA_dot=Kf(Q−A v)/VA，pB_dot=Kf(−Q+A v)/VB。
D是泵每转角排量m3/rad，其SI数值使压差反力矩D(pA−pB)和流量D omega功率一致；Cl是A向B的内部泄漏导纳，Q已减去泄漏，不能再次从腔方程扣漏流。
固定初态i=omega=x=v=pA=pB=0。U有符号端电压，F为沿−x方向的有符号外部阻力；无行程止挡或速度重置。

正式数据保证全程VA>0、VB>0、p0+pA>0、p0+pB>0，且无空化／止挡和常物性失效；声明检查只核验初始参数正性，不证明轨迹限制。

## 参数

parameters为空对象，所有元件系数均由下列material字段逐对象给定，没有隐含全局数值参数。

## 对象、拓扑和身份

spatial_dimension=1，为一维端口／支路坐标标记；geometries、meshes均为空对象，没有缺失的CAD或求解网格。locations恰含systems，为entities；IDs为1..32个非负严格递增int64，代表独立的真实系统对象，不是伪空间采样点。每个对象内部连接按本题方程固定，不同对象互不耦合，也不默认共享状态。无coordinates或额外端口表。每个参数／输入／输出行对应该系统ID，不按ID数值作为数组下标。

## 时间、存储与重建

time_axes恰含static、load、response。static引用float64[1]=[0.0]，用于不随时间变的属性和t=0初态。load引用float64[2..256]，从0严格递增至t_end>0。response引用float64[1..256]，严格递增且全部在[0,t_end]，可不含0或终点。load字段逐分量在load轴相邻时间采样点之间线性插值，禁止外推；不同实体之间不插值。输出时刻不是内部积分步或控制更新时刻。

全部场的value_kind=point，表示对象自身的状态、参数或端口值，不能解释为任意空间点或区域平均／积分。数组必须有完整[T,N,*component_shape]。标量float64字段kind=scalar、component_shape=[1]、components=["value"]；多分量字段kind=components、shape和标签按下表。本题全部输入场均float64；IDs为int64。输出均float64、response轴、不带sampling。

条件data中每个键对应的值必须恰为{"field":"逻辑字段名"}；不接受value常量、内联数组、option或location替代，重复的相同元件值也显式写入数组。逻辑field名及array key可自由选择且可不同，quantity严格等于data键名；字段location与条件完全一致，单位／类型／轴按下表。fields恰为实际引用字段；同一字段可以被符合相同声明的多个条件引用，但不能用数组长度替代位置身份。

输入sampling显式为space=uniform、extrapolation=forbid；static字段time=constant，load字段time=linear。uniform不表示整个图数值相同，仅表示每个离散对象自身的属性／端口量，不进行对象间插值。static的material字段全程不变，没有其他隐含初态或预平衡。

## 条件全集

每个下列operator恰一条，覆盖完整对应location。variable固定system_data；role、location如下；condition恰含role、variable、operator、location、data五键，data恰含该表全部键。表内“正／非负”约束作用于该字段所有值；未限制者为任意有限有符号实数。所有单位严格按表。

### `properties`

role=`material`，location=`systems`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `inductance` | `H` | float64 scalar [1] / value | L，电枢电感；严格正 |
| `resistance` | `Ohm` | float64 scalar [1] / value | R0，固定电枢电阻；严格正 |
| `motor_constant` | `V.s/rad` | float64 scalar [1] / value | K，反电动势常数；SI数值也作力矩常数N.m/A；严格正 |
| `inertia` | `kg.m2` | float64 scalar [1] / value | J，转子惯量；严格正 |
| `drag` | `N.m.s/rad` | float64 scalar [1] / value | B，机械黏性阻力；非负 |
| `pump_displacement` | `m3/rad` | float64 scalar [1] / value | D，泵排量；严格正 |
| `internal_leakage` | `m3/(Pa.s)` | float64 scalar [1] / value | Cl，双腔内部泄漏导纳；非负 |
| `mass` | `kg` | float64 scalar [1] / value | M，平移质量；严格正 |
| `piston_area` | `m2` | float64 scalar [1] / value | A，两腔相同有效活塞面积；严格正 |
| `linear_damping` | `N.s/m` | float64 scalar [1] / value | c，平移阻尼；非负 |
| `stiffness` | `N/m` | float64 scalar [1] / value | k，弹簧刚度；严格正 |
| `volume_a` | `m3` | float64 scalar [1] / value | VA0，x=0时腔A体积；严格正 |
| `volume_b` | `m3` | float64 scalar [1] / value | VB0，x=0时腔B体积；严格正 |
| `bulk_modulus` | `Pa` | float64 scalar [1] / value | Kf，液体体积模量；严格正 |
| `reference_pressure` | `Pa` | float64 scalar [1] / value | p0，共同参考绝对压力；严格正 |

### `driving`

role=`source`，location=`systems`，全部字段time_axis=`load`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `voltage` | `V` | float64 scalar [1] / value | U，电机端电压；按定义 |
| `load_force` | `N` | float64 scalar [1] / value | F，有符号外部阻力；按定义 |

condition片段示意（不是完整样例，逻辑名可变）：

```json
{"data":{"inductance":{"field":"input_property"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求；逻辑输出名、array key自由但不得重复占用key。均为response轴、float64、point、无sampling；scalar为[1]/value，多分量按表。不重排或取绝对值。

| quantity | unit | location | shape／components | 定义 |
|---|---|---|---|---|
| `current` | `A` | `systems` | [1] / value | 电枢电流i |
| `angular_velocity` | `rad/s` | `systems` | [1] / value | 转子角速度omega |
| `displacement` | `m` | `systems` | [1] / value | 活塞位移x |
| `velocity` | `m/s` | `systems` | [1] / value | 活塞速度v |
| `chamber_pressure` | `Pa` | `systems` | [2] / A,B | [pA,pB]，两腔表压 |

结果HDF5恰含全部输出array、输出使用的locations之IDs和response时间数组，严格复制输入轴／身份。不额外写入属性、拓扑、未被输出复用的时间轴、坐标或其他数组；若输入不同轴共用相同key，只按输出需要复制一次，遵守CONTRACT的角色规则。

## 接收限制与证据

输入场／输出场各至多2000000数值分量，包含所有时间和分量轴，重复请求也计入。正式数据还须核验方程和元件适用性、全程状态接收限制、观测存在唯一性、参考误差及预算内可达精度；声明检查不会求解轨迹或代替这些证据。
