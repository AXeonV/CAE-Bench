# stress-life-fatigue 数据契约

本题与instruction、通用CONTRACT共同构成完整契约。入口为UTF-8 `problem.json`和扁平HDF5；文件相对清单解析，名称不携带物理条件。`physics`恰为model与parameters，`physics.model="solid-stress-life-fatigue-v1"`；`task`若出现必须为`stress-life-fatigue`。`spatial_dimension=2`。只接受本题定义的模型和键。

## 分析与材料

给定每个真实材料观测点的完整循环块；σeff=σa/[1−max(σm,0)/Su]；σeff>0时破坏循环数N=(S/σeff)^m，σeff=0时损伤率0；D(t)=∫t0^t r/N dt，D(t0)=0。所有块只按输入次序累计，无序列效应、耐久极限、应力场重算或裂纹反馈。D允许超过1，D=1是本模型失效判据；本题只输出有限的累计损伤，不以无穷寿命作为HDF5值。观测点不承载网格求解。

| 参数名（physics.parameters 下） | 单位 | 值域与含义 |
|---|---|---|
| `fatigue_strength` | `Pa` | Basquin参考强度S；下界>0 |
| `fatigue_exponent` | `1` | 指数m；下界>0 |
| `ultimate_strength` | `Pa` | Goodman极限强度Su；下界>0 |
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 末时刻tf，严格大于t0 |

以上参数全部必填；每项恰为`{"value":有限标量,"unit":"表中单位"}`，无隐藏缺省或额外参数。数值均为有限实数，布尔值不能作为数值。

## 几何、位置与数组身份

`meshes={}`、`geometries={}`；`locations.sites`为独立实际观测点，含递增非负IDs及float64[N,2]坐标（m），点之间独立、不插值。同一观测点的循环与损伤状态始终按ID行对应。

本题仅使用sites独立点point输出。字段对象名、HDF5 key和tag是三种身份：条件`{"field":"logical_name"}`引用fields对象；`fields.logical_name.array`才是HDF5 key。各对象名自由选择（sites保留位置名除外），不得由名称推断quantity或数组key。

## 时间、连续解释和输入场

`start_time=t0<end_time=tf`；输出轴恰为一个名为response的轴，时刻全部位于[t0,tf]，可包括初态。所有source场共享同一不少于2帧的载荷轴，首末恰为t0、tf。输出时刻不改变块的累计历史。

输入场恰为被条件引用的fields，全部float64。标量kind=scalar、component_shape=[1]、components=["value"]；数组始终[T,N,*component_shape]，不得省略任何轴。所有source数据参数必须显式使用同location、表中quantity／unit／kind的field引用；即使恒幅或各点相同，也不能用带单位常量简写。只允许条件表列出的参数，无额外选项或默认单位。

每个输入field必须显式sampling。sites场space=uniform表示每个独立点的时间记录，不进行跨点重建。所有场extrapolation=forbid，禁止范围外外推。source场sampling.time=previous；[ti,ti+1)取第i帧，末帧仅作闭区间存储标记并与倒数第二帧相等。不接受linear或constant循环源场。输出在断点上包含此前完整块的累积贡献，与采用右块继续演化相容。

## 条件全集

每条记录的role、variable、operator、location及data全部显式。下表是本题唯一允许的operator；不得通过列表顺序覆盖冲突条件。

| operator | role／variable | 位置类别 | data精确键与类型 | 含义与组合 |
|---|---|---|---|---|
| `cycle_blocks` | `source`／`fatigue` | sites | `amplitude`：scalar，`Pa`，quantity=`stress_amplitude`；已计数循环的非负幅值σa<br>`mean`：scalar，`Pa`，quantity=`mean_stress`；均值σm，必须小于Su<br>`rate`：scalar，`1/s`，quantity=`cycle_rate`；非负完整循环数率r，非反转数率 | 一条覆盖sites；每个时间区间是一块已计数恒幅循环，不执行雨流计数 |

必须出现：`cycle_blocks`。sites类每个算子恰一条覆盖sites。

## 请求输出与结果HDF5

outputs中的逻辑名称及array key自由，quantity必须来自下表。每个必需quantity至少出现一次，可在不同允许采样子集重复请求。结果只包含每个输出array及其IDs和时间轴，严格沿用输入行序、dtype及全部轴；不得重复坐标或输入场。所有输出float64且有限。

| quantity（均必需） | 单位 | kind／位置与采样 | 定义 |
|---|---|---|---|
| `fatigue_damage` | `1` | scalar；sites，point | 已累计Miner损伤，可大于1，不截断 |

输出scalar的component_shape=[1]，components=["value"]。

## 合法范围与保证

除上文明确的自由键和时间轴名外不增加字段或条件组合。数据制作方须确认材料模型适用、循环块与初态合法、各请求时刻的累计响应有限且可确定，并在题面预算内用独立基准达到目标精度。这些是数据接收条件，不是结构校验器已经证明的事实；尚无正式数据时不声称已获验证。
