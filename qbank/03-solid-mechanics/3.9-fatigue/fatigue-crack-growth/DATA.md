# fatigue-crack-growth 数据契约

本题与instruction、通用CONTRACT共同构成完整契约。入口为UTF-8 `problem.json`，MSH 4.1 ASCII和扁平HDF5；文件相对清单解析，名称不携带物理条件。`physics`恰为model与parameters，`physics.model="solid-fatigue-crack-growth-v1"`；`task`若出现必须为`fatigue-crack-growth`。`spatial_dimension=2`。不使用CFD的profile、analysis、materials或contract_version，不能混写多个模型。

## 分析与材料

观测点标识一条给定直线路径的初始裂尖位置；只解标量裂长ODE，固定位置不是移动网格节点。Y(a)=Y0+Y1(a/W)+Y2(a/W)²，ΔK=Y(a)Δσ√(πa)，ΔKr=√reference_intensity_squared，Kc=√critical_intensity_squared；da/dt=r C0(ΔK/ΔKr)^m。平方参数使用Pa2.m以保持整数幂SI单位。应力比固定R=0，故Kmax=ΔK；不包含闭合、阈值、过载迟滞或裂纹相互作用。初值显式给出，全部请求时刻位于a<W且ΔK<Kc的增长阶段，不允许跨失稳延长模型。临界状态与路径改变属于数据不合法，不要求编造失效后裂长。

| 参数名（physics.parameters 下） | 单位 | 值域与含义 |
|---|---|---|
| `growth_rate` | `m` | 参考ΔKr下每完整循环增长C0，循环计数无量纲；下界>0 |
| `reference_intensity_squared` | `Pa2.m` | 参考应力强度范围的平方ΔKr²>0；下界>0 |
| `growth_exponent` | `1` | Paris指数m；下界>0；上界≤8 |
| `width` | `m` | 路径尺度W；下界>0 |
| `geometry_constant` | `1` | Y0>0；下界>0 |
| `geometry_linear` | `1` | Y1≥0；下界≥0 |
| `geometry_quadratic` | `1` | Y2≥0；下界≥0 |
| `critical_intensity_squared` | `Pa2.m` | 临界应力强度平方Kc²>0；下界>0 |
| `start_time` | `s` | 初始时刻t0 |
| `end_time` | `s` | 末时刻tf，严格大于t0 |

以上参数全部必填；每项恰为`{"value":有限标量,"unit":"表中单位"}`，无隐藏缺省或额外参数。数值均为有限实数，布尔值不能作为数值。

## 几何、位置与数组身份

`meshes={}`、`geometries={}`；`locations.sites`为独立实际观测点，含递增非负IDs及float64[N,2]坐标（m），点之间独立、不插值。同一观测点的循环与裂长状态始终按ID行对应；坐标不决定隐含几何因子。不得新增参数曲线伪装成空间探针。

本题仅使用sites独立点point输出。字段对象名、HDF5 key和tag是三种身份：条件`{"field":"logical_name"}`引用fields对象；`fields.logical_name.array`才是HDF5 key。各对象名自由选择（domain、cells、sites保留位置名除外），不得由名称推断quantity或数组key。

## 时间、连续解释和输入场

`start_time=t0<end_time=tf`；输出轴恰为一个名为response的轴，时刻全部位于[t0,tf]，可包括初态。输入条件非初态多帧场必须首末恰为t0、tf；单帧constant加载场的定义域直接为整个[t0,tf]，这属于显式全程常量而非外推；其存储时刻必须为t0；初态场单帧且时刻恰为t0。每个输入场可引用不同轴；输出时刻不是求解器内部时间步，不可跳过未输出的中间加载历史。

输入场恰为被条件引用的fields，全部float64。标量kind=scalar、component_shape=[1]、components=["value"]；vector使用全局前D坐标；tensor使用[D,D]及xx,xy,…的全矩阵。数组始终[T,N,*component_shape]，不得省略任何轴。每个数据参数允许表中单位的带单位常量（仅标量），或同location、相同quantity／unit／kind的显式field；向量即使均匀也用field。只允许表中列出的参数，无额外选项或默认单位。

每个输入field必须显式sampling。节点场space=piecewise_linear，沿一阶输入单元用唯一P1重建（边界节点在边界线段／三角面上重建）；element场space=piecewise_constant，表内average表示其上的常值。sites场space=uniform表示每个独立点的时间记录、不进行跨点重建。所有场extrapolation=forbid，禁止范围外外推。初态／静态场time=constant；普通加载场time=linear，时间节点间逐分量线性；单帧加载场time=constant且声明为全程常量。先空间重建再时间插值，两者均线性；输出应力／状态的平均必须由求解场积分，不能用平均位移代替。

疲劳循环块另有唯一覆盖规则：所有source场共享同一不少于2帧的载荷轴，首末为t0、tf，sampling.time=previous（不接受linear）；[ti,ti+1)取第i帧，末帧仅作闭区间存储标记并与倒数第二帧相等。初始裂长仍用单帧constant。输出在断点上包含此前完整块的累积贡献，与采用右块继续演化相容。

## 条件全集

每条记录的role、variable、operator、location及data全部显式。下表列出本题唯一允许的operator；不在表中的条件非法。不得通过列表顺序覆盖冲突条件。

| operator | role／variable | 位置类别 | data精确键与类型 | 含义与组合 |
|---|---|---|---|---|
| `initial_length` | `initial`／`crack_length` | sites | `value`：scalar，`m`，quantity=`crack_length`；初始裂长a0，0<a0<width | 一条覆盖sites，单帧t0 |
| `stress_cycles` | `source`／`fatigue` | sites | `range`：scalar，`Pa`，quantity=`stress_range`；非负完整循环应力范围Δσ，不是半幅<br>`rate`：scalar，`1/s`，quantity=`cycle_rate`；非负完整循环数率r | 一条覆盖sites，各加载块内恒定 |

必须出现：`initial_length`, `stress_cycles`。initial类恰一条且覆盖domain或sites；sites类每个算子恰一条覆盖sites。

## 请求输出与结果HDF5

outputs中的逻辑名称及array key自由，quantity必须来自下表。每个必需quantity至少出现一次，可在不同允许采样子集重复请求。结果只包含每个输出array及其IDs和时间轴，严格沿用输入行序、dtype及全部轴；不得重复坐标或输入场。所有输出float64且有限，不返回复数dtype。

| quantity（均必需） | 单位 | kind／位置与采样 | 定义 |
|---|---|---|---|
| `crack_length` | `m` | scalar；sites，point | 给定一维裂纹路径上的标量裂长a |

## 合法范围与保证

除上文明确的自由键和时间轴名外不增加字段或条件组合。数据制作方须证明材料适用、网格非退化、载荷与约束相容、解在规定分支上可确定、所请求平均存在，并在题面预算内用独立基准达到目标精度。非线性分支保证是正式数据接收条件，不是校验器已经证明的事实。参数正值、JSON合法或低残差均不替代这些证据。尚无正式数据时不声称这些保证已获验证。
