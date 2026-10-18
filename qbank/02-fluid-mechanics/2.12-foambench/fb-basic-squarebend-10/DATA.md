# 2.12.19 数据说明

任务、资源与评价见[本题题面](instruction.md)，通用数组和引用规则见[CONTRACT](../../../../docs/CONTRACT.md)。`task` 精确为 `fb-basic-squarebend-10`，`physics.model` 精确为 `foambench-squarebend`。模型在本题内由下文完整定义；不从目录、源软件或其他题推断物理。

## 参数

`physics.parameters` 恰含下表，各项为 `{"value":有限标量,"unit":"表列代码"}`，所有值固定为本题给定值，不允许添加数值算法参数。单位不得隐式归一化或换算。物理支持范围为本题几何、参数和初边值；数据可改变网格离散及其合法实体编号，不暗示对任意其他材料或工况均有支持。

| 参数 | 固定值 | unit |
|---|---:|---|
| `gas_constant` | 287.697668448209 | `J/(kg.K)` |
| `specific_heat_cp` | 1005 | `J/(kg.K)` |
| `dynamic_viscosity` | 0.0001 | `Pa.s` |
| `prandtl` | 1 | `1` |
| `turbulent_prandtl` | 0.85 | `1` |

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
| `temperature` | `K` | scalar |
| `turbulent_kinetic_energy` | `m2/s2` | scalar |
| `turbulent_dissipation` | `m2/s3` | scalar |

## 几何、稳态和条件

spatial_dimension=3。以下坐标均为m：横截面z∈[−0.025,0.025]；xy域为上游矩形 `[−0.05,0]×[0.025,0.075]`、右半环 `x≥0,0.025≤sqrt(x²+y²)≤0.075`、下游矩形 `[−0.5,0]×[−0.075,−0.025]` 的并集。接缝为内部流体连接，不施加边界。inlet为x=−0.05的上游端面，outlet为x=−0.5的下游端面，其余为walls。物理边界是半径25mm和75mm的圆弧；输入网格给出离散边界。只允许上述管形及其网格离散，不引入未声明的分支和粗糙度。

输出时间轴恰为[0]，表示稳态而非初始时刻。p为绝对静压，rho=p/(R*T)，h=Cp*T，导热率lambda=mu*Cp/Pr，湍流热扩散使用mu_t*Cp/Pr_t。能量守恒包括平均动能与黏性功；采用给定热物性，不采用等温或常密度近似。

| role | variable | operator | location及data |
|---|---|---|---|
| boundary | flow | massflow_profile | inlet；rate=0.5 kg/s，profile为同位置vector场，quantity=inlet_shape、unit=1 |
| boundary | temperature | dirichlet | inlet；value=1000 K |
| boundary | pressure | normal_derivative | inlet及walls，各一条；value=0 Pa/m |
| boundary | turbulence | intensity_length | inlet；intensity=0.05 (1)，length=0.005 m |
| boundary | pressure | dirichlet | outlet；value=110000 Pa |
| boundary | flow | pressure_open | outlet；backflow_velocity为vector场、quantity=velocity、值(0,0,0)m/s |
| boundary | temperature | inlet_outlet | outlet；backflow=1000 K |
| boundary | turbulent_kinetic_energy | inlet_outlet | outlet；backflow=1 m2/s2 |
| boundary | turbulent_dissipation | inlet_outlet | outlet；backflow=200 m2/s3 |
| boundary | flow | smooth_wall | walls；mode={"option":"equilibrium"} |
| boundary | temperature | normal_derivative | walls；value=0 K/m |

massflow_profile指定沿+x的无旋入口形状f=(d/0.025)^(1/7)，d为入口截面内点到四条边的最短距离，墙边f=0。profile场为(f,0,0)在入口面的平均值；按该字段的分片常值形状求统一正系数C，使积分 `∫rho*C*f dA=rate`，速度为C*profile；不能把0.5误作体积流量。rho取边界局部静压、指定温度的状态。intensity_length指定 `k=1.5*(intensity*|u|)^2`、`epsilon=Cmu^(3/4)*k^(3/2)/length`；rate、intensity、length必须为带单位常数，不允许场，profile必须为场。

pressure_open表示流出时速度法向导数为零；回流时切向速度取backflow_velocity的切向部分（此处零），法向分量由保持压力条件及质量守恒的开放边界求出，不再施加零法向速度。inlet_outlet表示u·n≥0时法向导数零、u·n<0时取backflow常量；零流量采用流出支。backflow均为常量。smooth_wall包含上述光滑壁的速度、k、epsilon条件，不重复对这些变量添加边界记录。其他参数、条件及源项均不允许。

## 湍流闭合与近壁责任

求解标准 k–epsilon 雷诺平均模型；速度是平均速度，k为单位质量湍动能，epsilon为其单位质量耗散率，均非瞬时脉动。涡黏度 `mu_t=rho*Cmu*k^2/epsilon`，Cmu=0.09；采用Boussinesq应力，含各向同性项 `-2*rho*k*I/3`，压力输出不吸收该项。k方程的扩散系数为 `mu+mu_t/sigma_k`，epsilon方程为 `mu+mu_t/sigma_epsilon`；sigma_k=1、sigma_epsilon=1.3、C1=1.44、C2=1.92。k源为生产P减rho*epsilon，epsilon源为 `C1*epsilon*P/k-C2*rho*epsilon^2/k`。P由上述涡黏应力与平均速度梯度收缩得到，不另加浮力、转捩或可压缩耗散修正。不可压模型取div(u)=0；可压模型保留应力的膨胀项。无随机入口扰动。

墙面固定、光滑、不可穿透。采用平衡壁函数描述未解析近壁层：k法向梯度为零；壁面剪应力与切向速度反向，`u_tau=sqrt(|tau_w|/rho)`、`y_plus=y*u_tau/nu`、`u_plus=|u_parallel|/u_tau`，黏性层 `u_plus=y_plus`、对数层 `u_plus=ln(9.8*y_plus)/0.41`，在两式正的非零交点切换；取连续支。y是近壁计算位置到墙面的法向距离。耗散率壁面闭合在对数层为 `Cmu^(3/4)*k^(3/2)/(0.41*y)`，黏性层为 `2*nu*k/y^2`。近壁生产与壁面剪切一致，非负涡黏度在黏性层趋于零。不要求把对数关系直接用于几何墙面y=0。数值离散、近壁位置、网格和离散壁函数实现由考生负责，必须遵守这些光滑壁、常数和层区关系；不要求特定软件函数名。k与epsilon是非负物理量，退化k=0取mu_t=0；数值正则化不能成为额外物理输入。
