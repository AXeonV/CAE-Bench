# point-kinetics 数据契约

problem.json及data_file引用的扁平HDF5遵循通用CONTRACT，路径相对清单目录。physics恰含model、parameters；model=`radiation-point-kinetics-v1`。task可省略，若出现只能为`point-kinetics`；模型不由目录或ID推断。禁止profile、contract_version、analysis、materials混用。

## 物理定义

空间形状冻结的点堆中子动力学，n为相对中子数，C_i为与n相同固定尺度的缓发前驱状态。dn/dt=[(ρ(t)−β)/Λ]n+Σ_iλ_i C_i+s(t)，dC_i/dt=β_i n/Λ−λ_i C_i，β=Σ_iβ_i。反应性ρ=(k−1)/k为无量纲数，不按美元输入，不含自动温度反馈。Λ、β_i、λ_i及独立n(0)、C_i(0)给定，不假定初始缓发平衡，不以反应性反推空间分布。历史按输入连续分段线性插值，仅输出requests中的时刻；积分须正确处理其间的控制结点，不增加输出帧；没有未声明跳跃或瞬发跳跃近似。

## 全局参数

physics.parameters恰含下表全部项，每项仅value和unit；数值有限，布尔不能作数值，整数须JSON整数。

| 参数 | 单位 | 定义及范围 |
|---|---|---|
| `precursor_count` | `1` | 缓发组数B，JSON整数1..8 |
| `generation_time` | `s` | 有效瞬发代时间Λ>0 |

## 对象与几何

spatial_dimension固定1。meshes和geometries均为空。1仅为有限维系统的协议标记，不引入空间方程。locations恰含下表；IDs为int64、非负严格递增，system必须ID=[0]；其余固定ID规则按表。precursors的行序与输出C的分量序一致，fraction求和β必须<1；history.reactivity逐存储值绝对值≤0.5。

| location | 定义与数量 |
|---|---|
| `system` | entities，1..1项；整体点堆对象，ID固定0 |
| `precursors` | entities，1..8项；缓发组，恰B个，IDs固定0..B−1；分量按此顺序 |

## 时间与数组

time_axes恰含`control`、`requests`、`static`。static恰为float64[1]的[0.0]，静态参数及初态记录引用static。requests为float64[T]，1≤T≤256，所有值在[0,t_end]，严格递增；t_end定义为requests最后值且必须>0，不要求首项为0。输出时刻不是内部步长；初态总是在物理t=0。control为float64[K]，2≤K≤256，首项0、末项恰等于t_end；控制字段逐区间线性插值、端点取存储值，禁止外推。control和requests可不同，内部时间步自选。所有时间单位s，时间数组key自由。未列轴不允许，输出均引用requests。

字段全部float64，shape=[T,N,*component_shape]，T取所引用时间轴长度，N取location IDs长度。scalar为kind=scalar、component_shape=[1]、components=["value"]；其余为kind=components，shape按表代入b=precursor_count，components为按行优先展开的c1..cL（从c1开始、末轴变化最快）。所有value_kind=point，entities表示其对象自身参数或集总状态，不表示空间平均。条件data只用{"field":"逻辑字段名"}引用；对应fields记录的array才是HDF5 key，名称自由。fields恰为条件实际引用项；quantity等于data键名，键value例外等于该条件variable；字段必须同location及上述时间轴。单个字段可被多个相容引用共享，不能以数组等长代替身份。无内联常量／选项或隐式广播。每个输入字段必须显式sampling：space=uniform（每个独立对象自身的值，不在对象间插值），extrapolation=forbid；static的time=constant，control的time=linear。

## 条件全集

### `precursors`

conditions中恰一条：role=`material`，variable=`precursor`，operator=`precursors`，location=`precursors`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `fraction` | scalar [1]；`1`；β_i>0，各组和β<1 |
| `decay` | scalar [1]；`1/s`；λ_i>0 |

### `initial`

conditions中恰一条：role=`initial`，variable=`state`，operator=`initial`，location=`system`；完整覆盖该location，使用`static`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `population` | scalar [1]；`1`；n(0)>0，相对中子数 |
| `precursor_state` | components ['b']；`1`；C_i(0)≥0，与n相同的任意固定归一化尺度，不是平衡预设 |

### `history`

conditions中恰一条：role=`source`，variable=`driving`，operator=`history`，location=`system`；完整覆盖该location，使用`control`时间轴。data恰含下列键，无默认值：

| data键 | 类型、单位、含义与范围 |
|---|---|
| `reactivity` | scalar [1]；`1`；ρ(t)，定义(k−1)/k，绝对值≤0.5；不是美元单位 |
| `source` | scalar [1]；`1/s`；n方程中的外源s(t)≥0，与n归一化一致 |

## 输出

每个quantity至少出现一次，可重复请求，outputs逻辑名与array key自由；同quantity的单位、位置、shape均按表，float64、value_kind=point、时间轴=requests、无sampling。各输出按下表定义，不另作时间或空间平均。

| quantity | 类型、单位与含义 | location |
|---|---|---|
| `population` | scalar [1]；`1`；相对中子数n(t) | `system` |
| `precursor_state` | components ['b']；`1`；按缓发组IDs排列的C_i(t) | `system` |

结果仅含要求的输出array及其输入IDs／时间轴的精确副本，不导出坐标、输入场或额外数组。

## 接收限制

各表规模为公开上限；输入场总分量与输出场总分量分别不超过2000000。所有输入／输出浮点值有限。输入符合本题物理模型的适用范围，全部请求的观测存在且有限，并可在公开资源预算内达到评分精度。
