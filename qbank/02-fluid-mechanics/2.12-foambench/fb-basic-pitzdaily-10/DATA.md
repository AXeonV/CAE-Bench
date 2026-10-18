# 2.12.39 数据说明

任务、资源与评价见[本题题面](instruction.md)，通用数组和引用规则见[CONTRACT](../../../../docs/CONTRACT.md)。`task` 精确为 `fb-basic-pitzdaily-10`，`physics.model` 精确为 `foambench-pitzdaily`。模型在本题内由下文完整定义；不从目录、源软件或其他题推断物理。

## 参数

`physics.parameters` 恰含下表，各项为 `{"value":有限标量,"unit":"表列代码"}`，所有值固定为本题给定值，不允许添加数值算法参数。单位不得隐式归一化或换算。物理支持范围为本题几何、参数和初边值；数据可改变网格离散及其合法实体编号，不暗示对任意其他材料或工况均有支持。

| 参数 | 固定值 | unit |
|---|---:|---|
| `density` | 1 | `kg/m3` |
| `kinematic_viscosity` | 0.001 | `m2/s` |
| `start_time` | 0 | `s` |
| `end_time` | 0.3 | `s` |

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
| `turbulent_kinetic_energy` | `m2/s2` | scalar |
| `turbulent_dissipation` | `m2/s3` | scalar |

## 几何、初态与时间

spatial_dimension=2。按顺序连接以下xy顶点（单位m）形成流体多边形：(-0.0206,0)、(0,0)、(0,-0.0254)、(0.206,-0.0254)、(0.290,-0.0166)、(0.290,0.0166)、(0.206,0.0254)、(-0.0206,0.0254)，再闭合。直线段边界，无曲线、圆角或额外厚度。inlet是x=−0.0206的端线，outlet是x=0.290的端线，其余均为walls（包含台阶竖壁）。二维平面全局xy，网格z=0。

初态轴恰为[0]，输出轴为0.01*i (i=1,…,30)。域内初始velocity=(0,0)、k=0.375、epsilon=14.855。突然启动允许t=0处初边界不相容；不额外要求入口角点连续。pressure是以出口为0的静压表压Pa；运动压力仅为内部可选变量，输出须乘density恢复Pa。初始压力由约束求得，不固定为任意初猜。

| role | variable | operator | location及data |
|---|---|---|---|
| initial | velocity | assign | domain；value为零vector场，m/s |
| initial | turbulent_kinetic_energy | assign | domain；value=0.375 m2/s2 |
| initial | turbulent_dissipation | assign | domain；value=14.855 m2/s3 |
| boundary | velocity | dirichlet | inlet；value为(25,0)的vector场，m/s |
| boundary | turbulent_kinetic_energy | dirichlet | inlet；value=0.375 m2/s2 |
| boundary | turbulent_dissipation | dirichlet | inlet；value=14.855 m2/s3 |
| boundary | pressure | normal_derivative | inlet及walls各一条；value=0 Pa/m |
| boundary | pressure | dirichlet | outlet；value=0 Pa |
| boundary | velocity | normal_derivative | outlet；value为零vector场，unit=1/s |
| boundary | turbulent_kinetic_energy | normal_derivative | outlet；value=0 m/s2 |
| boundary | turbulent_dissipation | normal_derivative | outlet；value=0 m/s3 |
| boundary | flow | smooth_wall | walls；mode={"option":"equilibrium"} |

smooth_wall包含光滑壁速度、k、epsilon边界关系，不再重复指定这三项的墙面边界。出口零导数条件在局部回流时仍为零导数，不暗加不同的回流入口值。表中scalar给定值在本题必须为所列常量或同值场；vector必须用场，初态场/边界场单位及quantity与variable相同。只允许这些条件与参数，不存在热方程、额外湍流变量、质量源或体力。

## 湍流闭合与近壁责任

求解标准 k–epsilon 雷诺平均模型；速度是平均速度，k为单位质量湍动能，epsilon为其单位质量耗散率，均非瞬时脉动。涡黏度 `mu_t=rho*Cmu*k^2/epsilon`，Cmu=0.09；采用Boussinesq应力，含各向同性项 `-2*rho*k*I/3`，压力输出不吸收该项。k方程的扩散系数为 `mu+mu_t/sigma_k`，epsilon方程为 `mu+mu_t/sigma_epsilon`；sigma_k=1、sigma_epsilon=1.3、C1=1.44、C2=1.92。k源为生产P减rho*epsilon，epsilon源为 `C1*epsilon*P/k-C2*rho*epsilon^2/k`。P由上述涡黏应力与平均速度梯度收缩得到，不另加浮力、转捩或可压缩耗散修正。不可压模型取div(u)=0；可压模型保留应力的膨胀项。无随机入口扰动。

墙面固定、光滑、不可穿透。采用平衡壁函数描述未解析近壁层：k法向梯度为零；壁面剪应力与切向速度反向，`u_tau=sqrt(|tau_w|/rho)`、`y_plus=y*u_tau/nu`、`u_plus=|u_parallel|/u_tau`，黏性层 `u_plus=y_plus`、对数层 `u_plus=ln(9.8*y_plus)/0.41`，在两式正的非零交点切换；取连续支。y是近壁计算位置到墙面的法向距离。耗散率壁面闭合在对数层为 `Cmu^(3/4)*k^(3/2)/(0.41*y)`，黏性层为 `2*nu*k/y^2`。近壁生产与壁面剪切一致，非负涡黏度在黏性层趋于零。不要求把对数关系直接用于几何墙面y=0。数值离散、近壁位置、网格和离散壁函数实现由考生负责，必须遵守这些光滑壁、常数和层区关系；不要求特定软件函数名。k与epsilon是非负物理量，退化k=0取mu_t=0；数值正则化不能成为额外物理输入。
