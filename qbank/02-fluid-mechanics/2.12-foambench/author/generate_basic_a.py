"""Generate the first 40 statement-only ports; never creates numerical data."""
from pathlib import Path
import json
import hashlib
import re
from source_snapshot import read_source

ROOT = Path(__file__).resolve().parents[4]
SECTION = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'runs/foambench-import/FoamBench_basic.json'
REVISION = 'e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2'

def number(pattern, text):
    return float(re.search(pattern, text, re.I).group(1).rstrip('.'))

def fmt(value):
    return f'{value:.15g}'

def param_table(values):
    return '| 参数 | 固定值 | unit |\n|---|---:|---|\n' + '\n'.join(
        f'| `{key}` | {fmt(value)} | `{unit}` |' for key, (value, unit) in values.items())

COMMON = '''## 文件、位置与数组

输入是 `problem.json`、其引用的一个扁平 `input.h5` 和一个固定 Gmsh MSH 4.1 ASCII 网格；可附几何文件，路径均相对清单。`meshes.main` 指向网格，`geometries` 可为空。全部坐标采用 m，全局笛卡尔坐标；所有时间采用 s。只使用 `physics` 声明，不同时声明 `profile`、`contract_version`、`analysis`、`materials`。这里定义的模型是题面阶段的接口设计，尚未装配本题物理声明检查器；通用结构检查通过不代表本题合法或可运行评测。

`locations.domain` 是 mesh/element 位置，`dimension=spatial_dimension`，恰好包括全部流体域单元。每个边界分区为 mesh/element 位置，维度比域少1，恰好覆盖相应几何边界，不重叠且合起来覆盖全部外边界；含障碍时也覆盖障碍表面。分组由 Physical Group 的 `(dimension,tag)` 或显式IDs确定，不能靠位置名称推断。所有IDs为递增唯一int64；数组第i行对应IDs第i项，禁止用网格读取次序代替。

输入场及输出场全部 float64，标量 kind=scalar、component_shape=[1]、components=["value"]；速度 kind=vector、component_shape=[D]、components为全局x/y/z前D项。数组形状为 `[T,N,*component_shape]`。域值和边界值均采用 `value_kind=average`，即对单元体积/面积或边界面面积/长度的真实平均值，而非质心点值。条件引用场时必须引用 `fields` 的对象名，场与条件同location；数组key由 `array` 给出。quantity必须与下文指定物理量一致。每个输入场必须被条件引用；不得添加其他输入物理量或输出量。

所有输入场显式 `sampling={"space":"piecewise_constant","time":"constant","extrapolation":"forbid"}`：边界平均数据在每个边界实体上取常值、在整个分析区间恒定。均匀场也逐实体存储；矢量一律由HDF5字段表示，不用JSON内联数组。域初态若均匀则表示该常值；非均匀初态的连续定义由下文给出，输入平均值必须为其在各单元上的投影，不另行把投影平均值解释成不同连续初态。边界交线和角点是零测度集合，使用相邻面各自的迹，不用条件列表次序覆盖。

条件的 role、variable、operator、data 键仅允许下表及逐题补充列出的组合；没有默认条件、额外源项或隐含材料。表中的标量数据可为 `{"value":数值,"unit":"规定单位"}` 或同位置同单位标量场 `{"field":"字段名"}`；vector数据只能引用同位置场。常量类型在整个位置恒定。`normal_derivative` 的data恰含 `value`，指向域外单位法向的导数；零导数表示局部延拓，无额外牵引含义。`dirichlet`与`assign`的data恰含 `value`，分别指定边界值和物理起始值；scalar/vector的单位由variable表固定。initial/assign只在起点生效。其他算子恰含下文列明的键，不添加字符串表达式。

## 输出约定

`outputs` 恰含下表物理量各一次，字段对象名和数组key可由清单取合法名称；所有输出位于domain，使用同一输出时间轴，value_kind=average。输出是对输入网格单元的积分除以体积（二维为面积），即使内部另用离散，也须回到这些固定平均值。二维速度只有x、y，出平面分量恒为零；不进行出平面厚度积分。压力平均先按本题物理压力定义恢复，再取平均。

结果HDF5只包含完整输出数组，以及所用IDs与时间数组的原样副本；不输出坐标、网格和元数据。不得改变IDs/时间顺序或省去分量轴。间断和界面跨越单元时仍按单元平均，不请求没有唯一值的界面点值。
'''

TURB = '''## 湍流闭合与近壁责任

求解标准 k–epsilon 雷诺平均模型；速度是平均速度，k为单位质量湍动能，epsilon为其单位质量耗散率，均非瞬时脉动。涡黏度 `mu_t=rho*Cmu*k^2/epsilon`，Cmu=0.09；采用Boussinesq应力，含各向同性项 `-2*rho*k*I/3`，压力输出不吸收该项。k方程的扩散系数为 `mu+mu_t/sigma_k`，epsilon方程为 `mu+mu_t/sigma_epsilon`；sigma_k=1、sigma_epsilon=1.3、C1=1.44、C2=1.92。k源为生产P减rho*epsilon，epsilon源为 `C1*epsilon*P/k-C2*rho*epsilon^2/k`。P由上述涡黏应力与平均速度梯度收缩得到，不另加浮力、转捩或可压缩耗散修正。不可压模型取div(u)=0；可压模型保留应力的膨胀项。无随机入口扰动。

墙面固定、光滑、不可穿透。采用平衡壁函数描述未解析近壁层：k法向梯度为零；壁面剪应力与切向速度反向，`u_tau=sqrt(|tau_w|/rho)`、`y_plus=y*u_tau/nu`、`u_plus=|u_parallel|/u_tau`，黏性层 `u_plus=y_plus`、对数层 `u_plus=ln(9.8*y_plus)/0.41`，在两式正的非零交点切换；取连续支。y是近壁计算位置到墙面的法向距离。耗散率壁面闭合在对数层为 `Cmu^(3/4)*k^(3/2)/(0.41*y)`，黏性层为 `2*nu*k/y^2`。近壁生产与壁面剪切一致，非负涡黏度在黏性层趋于零。不要求把对数关系直接用于几何墙面y=0。数值离散、近壁位置、网格和离散壁函数实现由考生负责，必须遵守这些光滑壁、常数和层区关系；不要求特定软件函数名。k与epsilon是非负物理量，退化k=0取mu_t=0；数值正则化不能成为额外物理输入。
'''

def output_table(turb=False, thermal=False, alpha=False):
    rows=[('velocity','m/s','vector'),('pressure','Pa','scalar')]
    if thermal: rows.append(('temperature','K','scalar'))
    if turb: rows += [('turbulent_kinetic_energy','m2/s2','scalar'),('turbulent_dissipation','m2/s3','scalar')]
    if alpha: rows.append(('water_fraction','1','scalar'))
    return '| quantity / variable | unit | kind |\n|---|---|---|\n'+'\n'.join(f'| `{q}` | `{u}` | {k} |' for q,u,k in rows)

def oblique(prompt, item):
    u=number(r'inlet velocity of ([\d.]+)',prompt)
    ut=number(r'top velocity of \(([\d.]+)',prompt)
    ti=number(r'inlet temperature of ([\d.]+)',prompt)
    tt=number(r'top boundary temperature of ([\d.]+)',prompt)
    p={'gas_constant':(5/7,'J/(kg.K)'),'specific_heat_cp':(2.5,'J/(kg.K)'), 'start_time':(0,'s'),'end_time':(10,'s')}
    title='斜向来流驱动的可压缩波系'
    task=f'''在4.1m长、1m高的二维矩形气体域内，计算不同方向来流相互作用产生的压缩波、膨胀及其传播。左侧入口速度为({fmt(u)},0)m/s、温度{fmt(ti)}K、绝对静压1Pa；上边界速度为({fmt(ut)},−0.50632)m/s、温度{fmt(tt)}K。下边界为对称滑移面，右侧为零法向梯度出口。初始域内速度(2.9,0)m/s、温度1K、绝对静压1Pa；入口改变在t=0后立即施加，初边界不相容由瞬态传播解决。

介质为量热完全理想气体，R=5/7 J/(kg.K)、Cp=2.5 J/(kg.K)，故gamma=1.4；忽略黏性、热传导、重力、反应与湍流。计算t=0至10s，提交1、2、…、10s的速度、绝对静压和温度单元平均场。激波处采用守恒且满足物理熵增的弱解。二维域不因原始薄层厚度引入额外边界。'''
    details='''## 几何、时间和条件

spatial_dimension=2，域为 `[0,4.1]×[0,1]`。边界left=x0、right=x4.1、top=y1、bottom=y0。初态轴恰为[0]；输出轴恰为[1,2,3,4,5,6,7,8,9,10]，不包含数值迭代编号，内部步长自由。密度由rho=p/(R*T)计算，内能为(Cp−R)*T；压力是绝对静压，不能回传运动压、总压或减去参考压的值。

| role | variable | operator | location及data |
|---|---|---|---|
| initial | velocity、pressure、temperature | assign | domain；value为上述均匀初态，各一条 |
| boundary | velocity、pressure、temperature | dirichlet | left；value为本题入口值，各一条 |
| boundary | velocity、temperature | dirichlet | top；value为本题顶部值，各一条 |
| boundary | pressure | normal_derivative | top；value=0 Pa/m |
| boundary | velocity、pressure、temperature | normal_derivative | right；value分别为零，单位1/s、Pa/m、K/m；速度导数为vector零场 |
| boundary | flow | symmetry | bottom；data恰含mode={"option":"slip"} |

symmetry表示u·n=0、切向速度法向导数为零、p和T法向导数为零；它不额外约束切向速度的值。所有条件恰按表出现，变量列表分别展开为记录。top是指定斜向来流，不是无滑移固壁。mu=0，Pr不影响无热传导模型，参数表不再存储不起作用的Pr。正压力、正温度与理想气体状态须保持。
'''
    notes=['R采用5/7精确值，以Cp=2.5和gamma=1.4一致；原prompt R=0.7143以及molWeight=11640.3为舍入值。','初始U=(2.9,0)、T=1、p=1按0目录；并非各变体入口状态。','原60×30×1和dt=.0025是来源离散设置，不约束内部算法；矩形二维物理域保持。']
    return title,task,p,details,output_table(thermal=True),'foambench-obliqueshock',notes

def square(prompt,item):
    temp=number(r'inlet value of ([\d.]+)',prompt)
    mu=number(r'mu value of ([\deE.+-]+)',prompt)
    pr=number(r'Pr value of ([\d.]+)',prompt)
    p={'gas_constant':(8314.46261815324/28.9,'J/(kg.K)'),'specific_heat_cp':(1005,'J/(kg.K)'), 'dynamic_viscosity':(mu,'Pa.s'),'prandtl':(pr,'1'),'turbulent_prandtl':(.85,'1')}
    title='方截面回弯管的高温湍流输运'
    task=f'''计算方截面180度回弯管内的三维可压缩稳态雷诺平均流动及热输运。入口质量流量0.5kg/s、温度{fmt(temp)}K，出口绝对静压110000Pa。气体为R=8314.46261815324/28.9 J/(kg.K)、Cp=1005 J/(kg.K)的理想气体；动力黏度为{fmt(mu)}Pa.s、分子Pr={fmt(pr)}，湍流Pr=0.85。管壁固定光滑、绝热，采用标准k–epsilon闭合及平衡壁函数；不考虑重力、辐射、反应和外部加热。

入口、弯曲段和长出口段共同形成弯管二次流和压力损失。求充分收敛的稳态速度、绝对静压、温度、k和epsilon场。稳态时间轴只有占位值0s；本题没有500s物理演化要求，也没有物理初态。实现自行选择数值方法、稳态迭代和初始化。'''
    details=f'''## 几何、稳态和条件

spatial_dimension=3。以下坐标均为m：横截面z∈[−0.025,0.025]；xy域为上游矩形 `[−0.05,0]×[0.025,0.075]`、右半环 `x≥0,0.025≤sqrt(x²+y²)≤0.075`、下游矩形 `[−0.5,0]×[−0.075,−0.025]` 的并集。接缝为内部流体连接，不施加边界。inlet为x=−0.05的上游端面，outlet为x=−0.5的下游端面，其余为walls。物理边界是半径25mm和75mm的圆弧；输入网格给出离散边界。只允许上述管形及其网格离散，不引入未声明的分支和粗糙度。

输出时间轴恰为[0]，表示稳态而非初始时刻。p为绝对静压，rho=p/(R*T)，h=Cp*T，导热率lambda=mu*Cp/Pr，湍流热扩散使用mu_t*Cp/Pr_t。能量守恒包括平均动能与黏性功；采用给定热物性，不采用等温或常密度近似。

| role | variable | operator | location及data |
|---|---|---|---|
| boundary | flow | massflow_profile | inlet；rate=0.5 kg/s，profile为同位置vector场，quantity=inlet_shape、unit=1 |
| boundary | temperature | dirichlet | inlet；value={fmt(temp)} K |
| boundary | pressure | normal_derivative | inlet及walls，各一条；value=0 Pa/m |
| boundary | turbulence | intensity_length | inlet；intensity=0.05 (1)，length=0.005 m |
| boundary | pressure | dirichlet | outlet；value=110000 Pa |
| boundary | flow | pressure_open | outlet；backflow_velocity为vector场、quantity=velocity、值(0,0,0)m/s |
| boundary | temperature | inlet_outlet | outlet；backflow=1000 K |
| boundary | turbulent_kinetic_energy | inlet_outlet | outlet；backflow=1 m2/s2 |
| boundary | turbulent_dissipation | inlet_outlet | outlet；backflow=200 m2/s3 |
| boundary | flow | smooth_wall | walls；mode={{"option":"equilibrium"}} |
| boundary | temperature | normal_derivative | walls；value=0 K/m |

massflow_profile指定沿+x的无旋入口形状f=(d/0.025)^(1/7)，d为入口截面内点到四条边的最短距离，墙边f=0。profile场为(f,0,0)在入口面的平均值；按该字段的分片常值形状求统一正系数C，使积分 `∫rho*C*f dA=rate`，速度为C*profile；不能把0.5误作体积流量。rho取边界局部静压、指定温度的状态。intensity_length指定 `k=1.5*(intensity*|u|)^2`、`epsilon=Cmu^(3/4)*k^(3/2)/length`；rate、intensity、length必须为带单位常数，不允许场，profile必须为场。

pressure_open表示流出时速度法向导数为零；回流时切向速度取backflow_velocity的切向部分（此处零），法向分量由保持压力条件及质量守恒的开放边界求出，不再施加零法向速度。inlet_outlet表示u·n≥0时法向导数零、u·n<0时取backflow常量；零流量采用流出支。backflow均为常量。smooth_wall包含上述光滑壁的速度、k、epsilon条件，不重复对这些变量添加边界记录。其他参数、条件及源项均不允许。

{TURB}'''
    notes=['源rhoSimpleFoam为稳态；controlDict结束500和dt是迭代控制，不解释成500s瞬态。仅迭代步差异的变体物理范围重复，保留独立源标识。','原prompt省略完整管形，按blockMesh毫米尺度和圆弧补全。','turbulentBL源名称未给数学函数；移植采用明确1/7幂次最近壁距剖面，属于作者公开规范化，不能宣称与原插件剖面逐点完全相同。','R取通用气体常数除以源molWeight=28.9，Cp=1005；出口回流T/k/epsilon按0目录1000/1/200。','120000单元为源网格预算（源块数总112000），当前评测资源未校准；不将其当执行时间/内存限制。']
    return title,task,p,details,output_table(turb=True,thermal=True),'foambench-squarebend',notes

def dam(prompt,item):
    air=number(r'viscosity of air to be ([\deE.+-]+)',prompt)
    water=number(r'viscosity of water to be ([\deE.+-]+)',prompt)
    p={'air_density':(1,'kg/m3'),'water_density':(1000,'kg/m3'),'air_kinematic_viscosity':(air,'m2/s'),'water_kinematic_viscosity':(water,'m2/s'),'surface_tension':(.07,'N/m'),'gravity_z':(-9.81,'m/s2'),'start_time':(0,'s'),'end_time':(.1,'s')}
    title='方形障碍旁的三维溃坝与自由面'
    task=f'''计算1m立方箱内水柱释放后绕过固定方形障碍的三维层流双相运动。水密度1000kg/m3、空气密度1kg/m3，水和空气的运动黏度分别为{fmt(water)}m2/s、{fmt(air)}m2/s，表面张力0.07N/m。两相均不可压、不可混溶、无相变，共享速度；考虑重力(0,0,−9.81)m/s²，不引入湍流黏度。

障碍占据[0.375,0.625]×[0.375,0.625]×[0,0.25]m³；初始静止水柱占据[0,0.6]×[0,0.1875]×[0,0.75]m³，其余为空气。箱体y=1面是大气开口，其余外表面及障碍表面为固定无滑移固壁；z=1是墙面。重力与开口方向以此为准。输出t=0.02、0.04、0.06、0.08、0.10s的速度、物理静压表压及水体积分数单元平均。'''
    details='''## 两相模型、几何和时间

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
'''
    notes=['粘度prompt未标类型，constant/physicalProperties.air与.water明确为nu，采用运动黏度m2/s。','障碍来自topoSet删除box及Allrun subsetMesh，不是blockMesh直接外形。','源重力-z而atmosphere=y1；保留该配置，不擅自旋转开口。','初始p_rgh=0是不可压压力求解初猜；公开只固定速度及水柱初态，压力输出恢复物理静压表压。','源动态网格refiner作为算法选项，不改变公共固定采样接口。','中性润湿90度是从alpha零法向梯度与表面张力给出的公开闭合解释。']
    return title,task,p,details,output_table(alpha=True),'foambench-dambreakwithobstacle',notes

def pitz(prompt,item):
    u=number(r'velocity of ([\d.]+)m/s',prompt)
    nu=number(r'nu value of ([\deE.+-]+)',prompt)
    p={'density':(1,'kg/m3'),'kinematic_viscosity':(nu,'m2/s'),'start_time':(0,'s'),'end_time':(.3,'s')}
    title='后向台阶及收缩通道的非定常平均流'
    task=f'''求解毫米尺度后向台阶及下游收缩通道中的二维不可压非定常雷诺平均流动。入口速度({fmt(u)},0)m/s，出口物理静压表压0Pa，墙面固定无滑移；运动黏度{fmt(nu)}m2/s，密度固定1kg/m3。标准k–epsilon闭合，入口与初始k=0.375m2/s²、epsilon=14.855m2/s³；光滑壁采用平衡壁函数。忽略重力、热传递和可压缩性。

从t=0的静止平均速度启动，入口在0后保持指定速度。求t=0.01、0.02、…、0.30s的平均速度、静压表压、k和epsilon单元平均场。这里的时刻是URANS平均场的物理时间，不是瞬时湍流快照或稳态迭代计数。算法、内部时间步和离散方式自由。'''
    details=f'''## 几何、初态与时间

spatial_dimension=2。按顺序连接以下xy顶点（单位m）形成流体多边形：(-0.0206,0)、(0,0)、(0,-0.0254)、(0.206,-0.0254)、(0.290,-0.0166)、(0.290,0.0166)、(0.206,0.0254)、(-0.0206,0.0254)，再闭合。直线段边界，无曲线、圆角或额外厚度。inlet是x=−0.0206的端线，outlet是x=0.290的端线，其余均为walls（包含台阶竖壁）。二维平面全局xy，网格z=0。

初态轴恰为[0]，输出轴为0.01*i (i=1,…,30)。域内初始velocity=(0,0)、k=0.375、epsilon=14.855。突然启动允许t=0处初边界不相容；不额外要求入口角点连续。pressure是以出口为0的静压表压Pa；运动压力仅为内部可选变量，输出须乘density恢复Pa。初始压力由约束求得，不固定为任意初猜。

| role | variable | operator | location及data |
|---|---|---|---|
| initial | velocity | assign | domain；value为零vector场，m/s |
| initial | turbulent_kinetic_energy | assign | domain；value=0.375 m2/s2 |
| initial | turbulent_dissipation | assign | domain；value=14.855 m2/s3 |
| boundary | velocity | dirichlet | inlet；value为({fmt(u)},0)的vector场，m/s |
| boundary | turbulent_kinetic_energy | dirichlet | inlet；value=0.375 m2/s2 |
| boundary | turbulent_dissipation | dirichlet | inlet；value=14.855 m2/s3 |
| boundary | pressure | normal_derivative | inlet及walls各一条；value=0 Pa/m |
| boundary | pressure | dirichlet | outlet；value=0 Pa |
| boundary | velocity | normal_derivative | outlet；value为零vector场，unit=1/s |
| boundary | turbulent_kinetic_energy | normal_derivative | outlet；value=0 m/s2 |
| boundary | turbulent_dissipation | normal_derivative | outlet；value=0 m/s3 |
| boundary | flow | smooth_wall | walls；mode={{"option":"equilibrium"}} |

smooth_wall包含光滑壁速度、k、epsilon边界关系，不再重复指定这三项的墙面边界。出口零导数条件在局部回流时仍为零导数，不暗加不同的回流入口值。表中scalar给定值在本题必须为所列常量或同值场；vector必须用场，初态场/边界场单位及quantity与variable相同。只允许这些条件与参数，不存在热方程、额外湍流变量、质量源或体力。

{TURB}'''
    notes=['源压力单位m2/s2，源无密度；为统一物理Pa输出，本移植公开补充density=1kg/m3，出口零压基准不变。','初始U=(0,0)按0/U，k与epsilon按源题；没有把入口速度当整个域初态。','原PIMPLE与dt=.0001为算法设置，本移植不绑定软件或内部步长。','源13000单元为网格预算，不伪装成已校准评测限制。']
    return title,task,p,details,output_table(turb=True),'foambench-pitzdaily',notes

def main():
    entries=read_source('basic')
    funcs={'obliqueShock':oblique,'squareBend':square,'damBreakWithObstacle':dam,'pitzDaily':pitz}
    generated=[]
    for index,(key,item) in enumerate(list(entries.items())[:40],1):
        family,variant=key.split('/')
        slug=f'fb-basic-{family.lower()}-{variant}'
        dest=SECTION/slug
        dest.mkdir(parents=True,exist_ok=True)
        prompt=item['usr_requirement']
        title,task,params,details,outputs,model,notes=funcs[family](prompt,item)
        instruction=f'''# 2.12.{index} {title}（变体{variant}）

{task}

本题要求实现可重复读取同一契约输入的求解程序；几何、参数、初边值与采样的完整定义见[DATA.md](DATA.md)，存储规则见[通用数据协议](../../../../docs/CONTRACT.md)。选择语言、软件、数值方法、内部网格和求解策略由考生负责，必须满足给定物理与输出语义。

## 提交与运行

提交统一入口 `solve.py`，运行方式为：

```sh
python solve.py --input /path/to/problem.json --output /path/to/result.h5
```

程序读取指定清单及其引用文件；清单内相对路径以problem.json所在目录为基准，不能依赖进程工作目录。成功写完并关闭结果文件后以0退出，标准输出和标准错误仅作日志，不作为答案。提交冻结后逐例运行，依赖须预先安装固定，运行过程不得访问网络或下载额外数据。

## 评价与资源阶段

本次交付为题面阶段，没有可运行的正式评测、样例数据或可信参考。拟按DATA规定的各输出物理量、固定实体及时间上的单元平均场分别评价，所有要求字段均须输出；结构合法只说明可读写，不等于物理正确。正式发布前将统一公开误差度量、量纲尺度、容差、字段权重及通过规则，并以参考和网格/时间收敛证据校准。

CPU、内存、执行时间和允许输入网格规模尚未校准，不存在本题已验证的资源保证；正式评测前须公布相应限制。输出采样间隔不限制内部时间步。当前材料不支持宣称通过评测或资源达标。
'''
        data=f'''# 2.12.{index} 数据说明

任务、资源与评价见[本题题面](instruction.md)，通用数组和引用规则见[CONTRACT](../../../../docs/CONTRACT.md)。`task` 精确为 `{slug}`，`physics.model` 精确为 `{model}`。模型在本题内由下文完整定义；不从目录、源软件或其他题推断物理。

## 参数

`physics.parameters` 恰含下表，各项为 `{{"value":有限标量,"unit":"表列代码"}}`，所有值固定为本题给定值，不允许添加数值算法参数。单位不得隐式归一化或换算。物理支持范围为本题几何、参数和初边值；数据可改变网格离散及其合法实体编号，不暗示对任意其他材料或工况均有支持。

{param_table(params)}

{COMMON}

{outputs}

{details}
'''
        (dest/'instruction.md').write_text(instruction,encoding='utf-8')
        (dest/'DATA.md').write_text(data.rstrip()+'\n',encoding='utf-8')
        author=dest/'author';author.mkdir(exist_ok=True)
        evidence={'upstream_revision':REVISION,'source_file':'FoamBench_basic.json','upstream_key':key,'prompt':prompt,'source_entry_sha256':hashlib.sha256(json.dumps(item,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'adopted_interpretations':notes,'stage':'statements_only_no_data','original_numerical_controls':{n:re.sub(r'/\*.*?\*/|//[^\n]*','',item.get('system/controlDict',''),flags=re.S).strip() for n in []}}
        # Keep only concise scalar control evidence, never entire solver dictionaries.
        controls=item.get('system/controlDict','')
        evidence['original_numerical_controls']={name:re.search(r'\b'+name+r'\s+([^;]+);',controls).group(1).strip() for name in ('startTime','endTime','deltaT','writeInterval') if re.search(r'\b'+name+r'\s+([^;]+);',controls)}
        (author/'source.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        generated.append(slug)
    assert len(generated)==40 and len(set(generated))==40
    print(f'Generated {len(generated)} instruction/DATA pairs.')

if __name__=='__main__':
    main()
