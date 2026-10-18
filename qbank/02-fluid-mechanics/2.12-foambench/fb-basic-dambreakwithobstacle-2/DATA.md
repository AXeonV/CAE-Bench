# 2.12.25 数据说明

任务、资源与评价见[本题题面](instruction.md)，通用数组和引用规则见[CONTRACT](../../../../docs/CONTRACT.md)。`task` 精确为 `fb-basic-dambreakwithobstacle-2`，`physics.model` 精确为 `foambench-dambreakwithobstacle`。模型在本题内由下文完整定义；不从目录、源软件或其他题推断物理。

## 参数

`physics.parameters` 恰含下表，各项为 `{"value":有限标量,"unit":"表列代码"}`，所有值固定为本题给定值，不允许添加数值算法参数。单位不得隐式归一化或换算。物理支持范围为本题几何、参数和初边值；数据可改变网格离散及其合法实体编号，不暗示对任意其他材料或工况均有支持。

| 参数 | 固定值 | unit |
|---|---:|---|
| `air_density` | 1 | `kg/m3` |
| `water_density` | 1000 | `kg/m3` |
| `air_kinematic_viscosity` | 0.0001 | `m2/s` |
| `water_kinematic_viscosity` | 0.001 | `m2/s` |
| `surface_tension` | 0.07 | `N/m` |
| `gravity_z` | -9.81 | `m/s2` |
| `start_time` | 0 | `s` |
| `end_time` | 0.1 | `s` |

## 文件、位置与数组

输入是 `problem.json`、其引用的一个扁平 `input.h5` 和一个固定 Gmsh MSH 4.1 ASCII 网格；可附几何文件，路径均相对清单。`meshes.main` 指向网格，`geometries` 可为空。全部坐标采用 m，全局笛卡尔坐标；所有时间采用 s。只使用 `physics` 声明，不同时声明 `profile`、`contract_version`、`analysis`、`materials`。这里定义的模型是题面阶段的接口设计，尚未装配本题物理声明检查器；通用结构检查通过不代表本题合法或可运行评测。

`locations.domain` 是 mesh/element 位置，`dimension=spatial_dimension`，恰好包括全部流体域单元。每个边界分区为 mesh/element 位置，维度比域少1，恰好覆盖相应几何边界，不重叠且合起来覆盖全部外边界；含障碍时也覆盖障碍表面。分组由 Physical Group 的 `(dimension,tag)` 或显式IDs确定，不能靠位置名称推断。所有IDs为递增唯一int64；数组第i行对应IDs第i项，禁止用网格读取次序代替。

输入场及输出场全部 float64，标量 kind=scalar、component_shape=[1]、components=["value"]；速度 kind=vector、component_shape=[D]、components为全局x/y/z前D项。数组形状为 `[T,N,*component_shape]`。域值和边界值均采用 `value_kind=average`，即对单元体积/面积或边界面面积/长度的真实平均值，而非质心点值。条件引用场时必须引用 `fields` 的对象名，场与条件同location；数组key由 `array` 给出。quantity必须与下文指定物理量一致。每个输入场必须被条件引用；不得添加其他输入物理量或输出量。

所有输入场显式 `sampling={"space":"piecewise_constant","time":"constant","extrapolation":"forbid"}`：边界平均数据在每个边界实体上取常值、在整个分析区间恒定。均匀场也逐实体存储；矢量一律由HDF5字段表示，不用JSON内联数组。域初态若均匀则表示该常值；非均匀初态的连续定义由下文给出，输入平均值必须为其在各单元上的投影，不另行把投影平均值解释成不同连续初态。边界交线和角点是零测度集合，使用相邻面各自的迹，不用条件列表次序覆盖。

条件的 role、variable、operator、data 键仅允许下表及逐题补充列出的组合；没有默认条件、额外源项或隐含材料。表中的标量数据可为 `{"value":数值,"unit":"规定单位"}` 或同位置同单位标量场 `{"field":"字段名"}`；vector数据只能引用同位置场。常量类型在整个位置恒定。`normal_derivative` 的data恰含 `value`，指向域外单位法向的导数；零导数表示局部延拓，无额外牵引含义。`dirichlet`与`assign`的data恰含 `value`，分别指定边界值和物理起始值；scalar/vector的单位由variable表固定。initial/assign只在起点生效。其他算子恰含下文列明的键，不添加字符串表达式。

## 输出约定

`outputs` 恰含下表物理量各一次，字段对象名和数组key可由清单取合法名称；所有输出位于domain，使用同一输出时间轴，value_kind=average。输出是对输入网格单元的积分除以体积（二维为面积），即使内部另用离散，也须回到这些固定平均值。二维速度只有x、y，出平面分量恒为零；不进行出平面厚度积分。压力平均先按本题物理压力定义恢复，再取平均。

结果HDF5只包含完整输出数组，以及所用IDs与时间数组的原样副本；不输出坐标、网格和元数据。不得改变IDs/时间顺序或省去分量轴。间断和界面跨越单元时仍按单元平均，不请求没有唯一值的界面点值。


| quantity / variable | unit | kind |
|---|---|---|
| `velocity` | `m/s` | vector |
| `pressure` | `Pa` | scalar |
| `water_fraction` | `1` | scalar |

## 两相模型、几何和时间

spatial_dimension=3，流体域是[0,1]³扣除题面给出的闭合障碍体；固液界面作为walls边界导出，不能把障碍当作密度很大的流体区域。水指示函数alpha初始为水柱内1、其余0；domain上的water_fraction初态数组给出水柱与单元交叠体积/单元体积。初始velocity全为零。初态轴恰为[0]，输出轴恰为[0.02,0.04,0.06,0.08,0.1]。界面位置随流动演化，输出网格和IDs始终固定，内部是否细化由实现决定。

两相采用牛顿流体应力与不可压质量守恒；alpha随共有速度守恒输运，rho=alpha*rho_water+(1−alpha)*rho_air，动力黏度mu=alpha*rho_water*nu_water+(1−alpha)*rho_air*nu_air。连续物理界面无质量穿越，两侧速度连续，牵引跳跃为表面张力乘曲率，正曲率的水滴内压更高。alpha=1为纯水、0为纯空气，混合值表示局部水体积比例；不加入人工界面压缩的物理源。固壁为中性润湿90度接触角，不考虑接触角迟滞、接触线附加力或壁面粗糙度。

pressure是相对于共同大气基准的物理静压，单位Pa。若内部使用约化压力p_rgh，须恢复 `p= p_rgh + rho*g_z*z`（重力势参考z=0），再输出；不允许直接回传p_rgh。初始压力由不可压约束及边界求解，不把任意压力迭代初猜当作给定物理初态。

| role | variable | operator | location及data |
|---|---|---|---|
| initial | velocity | assign | domain；value引用零vector场m/s |
| initial | water_fraction | assign | domain；value引用上述投影scalar场，unit=1 |
| boundary | flow | no_slip | walls；velocity引用零vector场，quantity=velocity、unit=m/s |
| boundary | water_fraction | contact_angle | walls；angle=90 deg，常量 |
| boundary | flow | atmosphere | 开口y=1；total_pressure=0 Pa、backflow_velocity引用零vector场、backflow_fraction=0 (1) |

atmosphere定义：u·n≥0时速度和alpha法向导数零，静压p=total_pressure；u·n<0时alpha=backflow_fraction（纯空气），切向速度取backflow_velocity切向部分，法向通量由压力和质量守恒求解，静压 `p=total_pressure−rho*|u|²/2`。零通量采用流出分支。此处total_pressure是物理总表压，不是约化压力；回流速度字段不强制法向分量为零。no_slip指定u=0，压力法向关系由动量和不可穿透约束确定，不同时强加任意零梯度压力。contact_angle指定从水相内测量的静态接触角90度，对应界面在墙面正交；data.angle仅接受常量。所有条件恰按表出现，不另给pressure初态和重力源字段，重力由参数固定。
