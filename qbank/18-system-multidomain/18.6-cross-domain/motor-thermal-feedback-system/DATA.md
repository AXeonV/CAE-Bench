# motor-thermal-feedback-system 数据契约

入口problem.json与data_file所指扁平HDF5，路径相对清单。physics恰含model、parameters；model=`systems-motor-thermal-feedback-system-v1`，task可省略，出现须为`motor-thermal-feedback-system`。禁止profile、contract_version、analysis、materials混用，不接受本题未列的参数、条件、字段、位置或输出quantity。

## 物理与初边值

每个systems对象是一套独立集总电机—惯性—热系统。反电动势K omega和电磁力矩K i使用同一正SI耦合常数K，保证功率转换一致。
R(T)=R0[1+a(T−Tref)]；L i_dot=U−R(T)i−K omega；J omega_dot=K i−B omega−tau；
Cth T_dot=R(T)i²+B omega²−H(T−Ta)。tau沿正转方向的阻力矩为正，可有符号。Ta是给定外界绝对温度，T为线圈与黏性耗散统一热节点的绝对温度，所有B omega²均进入该热节点；负载做功tau omega不进入该节点。
固定初态i=omega=0、T=Tref。不同systems之间无未声明耦合。

正式数据保证全程T>0、R(T)>0及固定电机／集总热模型适用。不考虑磁饱和、铁损或分布温度场。

## 参数

parameters为空对象，所有元件系数均由下列material字段逐对象给定，没有隐含全局数值参数。

## 对象、拓扑和身份

spatial_dimension=1，为一维端口／支路坐标标记；geometries、meshes均为空对象，没有缺失的CAD或求解网格。locations恰含systems，为entities；IDs为1..32个非负严格递增int64，代表独立的真实系统对象，不是伪空间采样点。每个对象内部连接按本题方程固定，不同对象互不耦合，也不默认共享状态。无coordinates或额外端口表。每个参数／输入／输出行对应该系统ID，不按ID数值作为数组下标。

## 时间、存储与重建

time_axes恰含static、load、response。static引用float64[1]=[0.0]，用于不随时间变的属性和t=0初态。load引用float64[2..256]，从0严格递增至t_end>0。response引用float64[1..256]，严格递增且全部在[0,t_end]，可不含0或终点。load字段逐分量在相邻节点间线性插值，禁止外推；不同实体之间不插值。输出时刻不是内部积分步或控制更新时刻。

全部场的value_kind=point，表示对象自身的状态、参数或端口值，不能解释为任意空间点或区域平均／积分。数组必须有完整[T,N,*component_shape]。标量float64字段kind=scalar、component_shape=[1]、components=["value"]；多分量字段kind=components、shape和标签按下表。仅endpoints为int64；其他场均float64。输出均float64、response轴、不带sampling。

每个条件data键必须恰为{"field":"逻辑字段名"}；不接受value常量、内联数组、option或location替代，重复的相同元件值也显式写入数组。逻辑field名及array key可自由选择且可不同，quantity严格等于data键名；字段location与条件完全一致，单位／类型／轴按下表。fields恰为实际引用字段；同一字段可以被符合相同声明的多个条件引用，但不能用数组长度替代位置身份。

输入sampling显式为space=uniform、extrapolation=forbid；static字段time=constant，load字段time=linear。uniform不表示整个图数值相同，仅表示每个离散对象自身的属性／端口量，不进行对象间插值。static的material字段全程不变，initial字段只定义t=0而非迭代初猜；没有其他隐含初态或预平衡。

## 条件全集

每个下列operator恰一条，覆盖完整对应location。variable固定system_data；role、location如下；condition恰含role、variable、operator、location、data五键，data恰含该表全部键。表内“正／非负”约束作用于该字段所有值；未限制者为任意有限有符号实数。所有单位严格按表。

### `properties`

role=`material`，location=`systems`，全部字段time_axis=`static`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `inductance` | `H` | float64 scalar [1] / value | L，电枢电感；严格正 |
| `resistance` | `Ohm` | float64 scalar [1] / value | R0，参考温度电阻；严格正 |
| `motor_constant` | `V.s/rad` | float64 scalar [1] / value | K，反电动势常数；SI数值也作力矩常数N.m/A；严格正 |
| `inertia` | `kg.m2` | float64 scalar [1] / value | J，转子惯量；严格正 |
| `drag` | `N.m.s/rad` | float64 scalar [1] / value | B，机械黏性阻力；非负 |
| `temperature_coefficient` | `1/K` | float64 scalar [1] / value | a，电阻温度系数；非负 |
| `reference_temperature` | `K` | float64 scalar [1] / value | Tref，初始与电阻参考绝对温度；严格正 |
| `heat_capacity` | `J/K` | float64 scalar [1] / value | Cth，统一热节点热容；严格正 |
| `heat_transfer` | `W/K` | float64 scalar [1] / value | H，对外界热导；严格正 |

### `driving`

role=`source`，location=`systems`，全部字段time_axis=`load`。

| data键 | unit | 类型／分量 | 定义与范围 |
|---|---|---|---|
| `voltage` | `V` | float64 scalar [1] / value | U，端电压；按定义 |
| `load_torque` | `N.m` | float64 scalar [1] / value | tau，外部有符号阻力矩；按定义 |
| `ambient_temperature` | `K` | float64 scalar [1] / value | Ta，外界绝对温度；严格正 |

condition片段示意（不是完整样例，逻辑名可变）：

```json
{"data":{"inductance":{"field":"input_property"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求；逻辑输出名、array key自由但不得重复占用key。均为response轴、float64、point、无sampling；scalar为[1]/value，多分量按表。不重排、取绝对值或按图方向重新定向。

| quantity | unit | location | shape／components | 定义 |
|---|---|---|---|---|
| `current` | `A` | `systems` | [1] / value | 电枢电流i |
| `angular_velocity` | `rad/s` | `systems` | [1] / value | 转速omega |
| `temperature` | `K` | `systems` | [1] / value | 统一热节点绝对温度T |

结果HDF5恰含全部输出array、输出使用的locations之IDs和response时间数组，严格复制输入轴／身份。不额外写入属性、拓扑、未被输出复用的时间轴、坐标或其他数组；若输入不同轴共用相同key，只按输出需要复制一次，遵守CONTRACT的角色规则。

## 接收限制与证据

输入场／输出场各至多2000000数值分量，包含所有时间和分量轴，重复请求也计入。正式数据还须核验方程和元件适用性、全程状态接收限制、观测存在唯一性、参考误差及预算内可达精度；声明检查不会求解轨迹或代替这些证据。禁止以临时工具fixture作为正式输入或可信物理参考。
