# transient-joule-feedback 数据契约

入口problem.json及data_file引用的扁平HDF5；路径相对清单。physics恰含model、parameters，model=`multiphysics-transient-joule-feedback-v1`；task可省略，出现须为`transient-joule-feedback`。禁止profile、contract_version、analysis、materials混用。未列出的参数、位置、条件、字段、源或初态均不接受。

## 物理定义

均匀导电杆0≤x≤L，theta=T−T0。sigma(theta)=sigma0/(1+a theta)，J=−sigma(theta) phi_x，J_x=0（每时刻准静态），c theta_t=k theta_xx+J²/sigma(theta)。
温度改变电导，电流解确定体积焦耳热，必须自洽；没有Seebeck、Peltier、位移电流或电磁波。电势左端固定0，右端施加V。

初态theta=0，V(0)=0。边界温升非负，且a theta_boundary≤0.1；所有加载节点满足a sigma0 V²/k≤0.1，数据另核验全域a theta≤0.25。不允许用截断电导掩盖失效。

## 参数全集

parameters恰含下表所有键；每项恰含value、unit，value为有限JSON实数（布尔不算数值），unit严格按表，不隐式换单位。下列符号用于本题方程，未另列的源均为0。

| 参数 | 单位 | 定义与范围 |
|---|---|---|
| `length` | `m` | L，区间长度；严格正 |
| `electric_conductivity` | `S/m` | sigma0，参考温度电导率；严格正 |
| `resistivity_slope` | `1/K` | a，电阻率温度系数；严格正 |
| `conductivity` | `W/(m.K)` | k，热导率；严格正 |
| `reference_temperature` | `K` | T0，无应力平衡参考绝对温度；严格正 |
| `heat_capacity` | `J/(m3.K)` | c，单位体积定应变热容；严格正 |


## 空间与身份

spatial_dimension=1；geometries与meshes为空对象。连续体区间由length=L定义，没有未提供的CAD或求解网格。locations恰含domain、left、right。domain为points，2..2048个真实物理采样点，coordinates为float64[N,1]，单位m，x∈[0,L]，坐标两两不同，可不含端点且不按x排序；IDs为非负严格递增int64[N]。数组行始终依IDs，不按坐标重排输出。left、right各为entities、各一项非负int64 ID，代表x=0／x=L处实际端口或端面（right在活塞题同时是活塞对象）；无coordinates或空间插值。两端ID相同也不表示同一对象，不跨location匹配。无其他locations或几何。域采样只定义输出点，不指定内部网格或离散模型。

## 时间与数组

time_axes恰含load、response。load引用float64[2..256]，从0严格递增到t_end>0；response引用float64[1..256]，严格递增且位于[0,t_end]，可以不包含0。所有输入场用load，输出场用response。load所有边界数据在t=0恰为0，包括温升、位移、压力、力、电压及牵引；两加载节点之间逐分量线性插值，禁止区间外外推。零初态为题目固定事实，不提供初猜或额外initial条件。response是观测时刻，不是内部步长。

输入场、输出场均float64，数组完整shape=[T,N,*component_shape]，本题统一采用scalar、component_shape=[1]、components=["value"]，value_kind=point。所有值均为实数，无复数或附加分量。逻辑field名和HDF5 array key可不同且自由；条件field引用前者，array引用后者。fields恰为条件实际引用的场，可由多个条件共享符合声明的同一场；不能按长度从其他位置借数据。

输入场sampling恰为space=uniform、time=linear、extrapolation=forbid。uniform只表示单个端口的值，不在不同端口之间插值；没有域输入场。quantity等于条件data键名，unit按下表，location与该条件相同，time_axis=load，dtype、kind、shape、components和value_kind按上述固定格式。所有data项必须用field引用，以明确加载时间支撑，不接受value常量。

## 条件全集

每个下列端口恰一条条件；未列端口按物理定义的固定零值闭合，不添加条件。role=boundary、variable=coupled_boundary、operator=prescribed、location为对应端口；data恰含该端口下表全部键，无额外键。condition本身恰含这五项。不同端口不能合并为一条条件。

### `left`

| data键 | unit | 物理值 |
|---|---|---|
| `temperature_rise` | `K` | theta(0,t) |

### `right`

| data键 | unit | 物理值 |
|---|---|---|
| `temperature_rise` | `K` | theta(L,t) |
| `voltage` | `V` | phi(L)；phi(0)=0始终固定 |

field表示片段（逻辑名可变，完整清单还需其他必填项）：

```json
{"data":{"temperature_rise":{"field":"boundary_value"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求，逻辑输出名与array key自由但不得重复占用数组key。均为上文类型、shape、components、float64及point，不带sampling，time_axis=`response`。domain输出是连续解在真实坐标的点值；端点取域内唯一迹，端面实体上的输出是该真实对象状态，不是区域积分。

| quantity | unit | location | 定义 |
|---|---|---|---|
| `temperature_rise` | `K` | `domain` | theta(x,t) |
| `electric_potential` | `V` | `domain` | phi(x,t) |

结果HDF5恰含所有输出array及所需locations的IDs、所需时间轴；严格复制输入轴和身份。domain坐标、输入场及不被输出使用的端口IDs不写入结果。不导出新网格或额外数组。

## 接收与验证边界

输入场／输出场各至多2000000数值分量（含时间和分量轴，重复输出也计入）。除可由声明检查器验证的参数、单位、轴和组合外，正式数据制作还须核验模型适用、小信号／小应变条件、解与观测存在唯一性、参考精度及预算可达性；声明通过不构成这些证据。无正式数据时不能把协议fixture当物理参考。
