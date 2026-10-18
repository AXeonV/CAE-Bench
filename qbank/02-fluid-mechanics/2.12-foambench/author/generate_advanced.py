"""Render the fourteen nonreacting advanced statement adaptations.

Usage: python generate_advanced.py --source /path/FoamBench_advanced.json
Source bytes are pinned and checked; no cases, solver inputs or references are made.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REV = 'e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2'
SHA = '2e97ce1bd1444909000c4c6337c187c2237b7cdd81c3e2ef9f0ab8c0ea10c22b'

SA = """采用非定常 Reynolds 平均和 Spalart–Allmaras 一方程涡黏性闭合，使用无转捩、无 trip、无 ft2 的 SA-noft2 版本，不添加旋转／曲率修正。输运量为非负修正运动涡黏度 q，νt=q fv1，χ=q/ν，fv1=χ³/(χ³+7.1³)。

其运动形式为 Dq/Dt=cb1 S̃q + [∇·((ν+q)∇q)+cb2|∇q|²]/σ − cw1 fw(q/d)²。cb1=0.1355、cb2=0.622、σ=2/3、κ=0.41、cw1=cb1/κ²+(1+cb2)/σ、cw2=0.3、cw3=2；d 为到最近固体壁的距离，若本题有明示的滑移固体壁也包括之，不包括入口、出口或对称边。Ω=sqrt(2W:W)，W=(∇u−∇uᵀ)/2，fv2=1−χ/(1+χ fv1)，S̃=max(Ω+q fv2/(κ²d²),0.3Ω)。r=min(q/(max(S̃,10⁻³⁰ s⁻¹)κ²d²),10)，g=r+cw2(r⁶−r)，fw=g[(1+cw3⁶)/(g⁶+cw3⁶)]^(1/6)。壁面 q=0，S̃=0 时按连续极限处理。密度变化时本题仍采用上述物质导数形式，作为明确的移植闭合定义。

黏性应力使用 μeff=ρ(ν+νt)，可压缩时使用去迹应变；本版本不另加模型湍动能对应的各向同性应力。"""

KE = """采用非定常 Reynolds 平均和标准 k–ε 闭合，不使用 RNG、realizable、浮力产生或额外可压缩修正。νt=Cμ k²/ε，Cμ=0.09，Cε1=1.44，Cε2=1.92，σk=1，σε=1.3；P=2νt dev(D):dev(D)，D=(∇u+∇uᵀ)/2。

密度加权输运为 ∂t(ρk)+∇·(ρuk)=∇·[ρ(ν+νt/σk)∇k]+ρP−ρε−(2/3)ρk∇·u；ε 方程扩散系数为 ρ(ν+νt/σε)，产生与耗散为 ρ(Cε1 P−Cε2 ε)ε/k，另含 −(2/3)ρCε1 ε∇·u。零 k、ε 按非负极限处理，数值正则不得成为附加物理源。模型应力为 2ρνt dev(D)−(2/3)ρkI；不可压缩时压力仍指静压，不将 2ρk/3 藏入输出压力。"""

SST = """采用非定常 Reynolds 平均、k–ω SST 两方程闭合，2003 SST 形式；不加入转捩、旋转曲率、浮力和额外压缩修正。νt=a1 k/max(a1ω,sqrt(2D:D)F2)，a1=0.31；k 耗散为 β* kω，β*=0.09，产生 Pk=min(2νt D:D,10β*kω)。

k 方程 Dk/Dt=∇·[(ν+σkνt)∇k]+Pk−β*kω；ω 方程 Dω/Dt=∇·[(ν+σωνt)∇ω]+γ Pk/max(νt,10⁻³⁰ m²/s)−βω²+2(1−F1)σω2 ∇k·∇ω/ω。系数 φ=F1φ1+(1−F1)φ2，(σk1,σω1,β1,γ1)=(0.85,0.5,0.075,5/9)，(σk2,σω2,β2,γ2)=(1,0.856,0.0828,0.44)。

CD=max(2σω2∇k·∇ω/ω,10⁻¹⁰ s⁻²)，A1=min(max(sqrt(k)/(β*ωd),500ν/(d²ω)),4σω2 k/(CD d²))，F1=tanh(A1⁴)；A2=max(2sqrt(k)/(β*ωd),500ν/(d²ω))，F2=tanh(A2²)。d 是到无滑移壁的距离。壁面采用解析到壁的极限 k→0、ω~6ν/(β1d²)，不指定某软件的壁函数或首层单元。输出压力为静压；Reynolds 应力含 −2ρkI/3。"""

LES = """采用下面明确定义的二维动态一方程亚格子动能闭合；不将该二维模型成绩解释为三维真实湍流统计。Δ 为 parameters.filter_width 给定的固定物理长度，与内部网格无关。令 F_s f(x)=∫Ω exp(−|x−y|²/(2s²)) f(y)dy / ∫Ω exp(−|x−y|²/(2s²))dy，为在流体域内截断并归一化的共同高斯测试滤波；分量逐项处理，孔洞不参与积分。定义 F=F_Δ，测试尺度为2Δ，D=dev((∇u+∇uᵀ)/2)，所有迹与去迹按嵌入三维且u_z=∂z=0计算。

K=max((F_(2Δ)(|u|²)−|F_(2Δ)u|²)/2,0)，L=F(dev(F_(2Δ)(u⊗u)−F_(2Δ)u⊗F_(2Δ)u))，M=F(−2Δ sqrt(K) F_(2Δ)D)。Ck=max(0,F(L:M)/(2F(M:M)))，νt=Ck Δ sqrt(k_sgs)。Ce=max(0,F[(ν+νt)(F_(2Δ)(D:D)−F_(2Δ)D:F_(2Δ)D)]/F[K^(3/2)/(2Δ)])；分母为零时相应系数定义为0，不加入回散或未声明平均窗口。

亚格子能量满足 Dk_sgs/Dt=∇·[(ν+νt)∇k_sgs]+2νt D:D−Ce k_sgs^(3/2)/Δ。模型应力为2ρνtD−2ρk_sgsI/3，分子应力为2ρνD；速度满足不可压连续方程和动量方程。初始与入口k_sgs确为该方程状态，不能用解析速度扰动代替。所求 velocity 是此闭合模型的解析速度，pressure 是未吸收2ρk_sgs/3的机械静压；输出只再做指定单元平均，不另施可选滤波或时间平均。数值算法自由，模型、Δ和共同测试滤波不可改变。"""

SMAG = """采用二维可压缩 Favre 滤波的代数 Smagorinsky 闭合，Cs=0.17，Δ=parameters.filter_width，二者不随内部网格改变。三维嵌入的无迹应变 S=dev((∇u+∇uᵀ)/2)，νt=(CsΔ)²sqrt(2S:S)，模型黏性应力为2ρνt S。忽略亚格子各向同性应力与独立亚格子能量，压力直接为状态方程的热力学静压；不把已有k文件当成必须输运的未知量。velocity 为该模型的Favre速度，输出是其单元平均，不另施可选空间或时间滤波。热扩散含ρνt cp/Prt；采用气体总能量 E=cvT+|u|²/2，不附加独立k能量。守恒通量及模型耗散保持总能量一致；不使用额外压缩修正。"""

COMMON_DATA = """## 文件、引用与采样

通用规则见 [CONTRACT.md](../../../../docs/CONTRACT.md)，任务与评价见 [instruction.md](instruction.md)。本节定义本题全部物理语义；无需原始软件配置。

`problem.json` 使用 `task: "{slug}"`、`spatial_dimension: 2`、`physics: {{"model":"{slug}","parameters":{{...}}}}`。不使用 `profile`、`contract_version`、`analysis`、`materials`。这里是基于通用 physics 声明的题内模型契约，不将新字段冒充 cfd-2.1 已支持的配置；本次只交付文档，模型尚未绑定领域校验器或 judge。

`data_file` 为单个输入 HDF5；`meshes` 恰有一个 Gmsh MSH 4.1 ASCII 一阶三角形／四边形二维网格，`geometries` 可为空。几何物理边界以输入分片直线网格为准，曲线可细化近似。`locations` 中完整流体域与边界均为 mesh element，dimension 分别为 2、1，IDs 为按 tag 递增的 int64；边界按条件位置精确分区。不得以文件行号代替 tag。不存在未声明的壁、重力或旋转参考系。

所有输入场均 float64；标量 `[T,N,1]`，矢量 `[T,N,2]`，分量 x、y（轴对称时见下文）。场通过 `fields` 对象名、`array` 数据集名引用，二者不必相同。全域初态及边界采用单元平均，`value_kind: "average"`；只允许显式 `sampling={{"space":"piecewise_constant","time":"constant","extrapolation":"hold"}}`：每个实体内、整个计算区间均保持给定值。T=1 的输入场时间为 0 s，无额外空间平滑。条件中的带单位标量常量表示整个作用位置恒定；矢量即便均匀也必须经 field 引用。初态需覆盖全部流体单元；边界需覆盖全部外边界边。

输出只允许二维流体单元的面积平均；每个量可在非空单元子集上请求。输出元数据逐项给 `array,quantity,location,time_axis,dtype,kind,component_shape,components,unit,value_kind`；value_kind 为 average，标量 kind=scalar、components=["value"]、component_shape=[1]；速度 kind=vector、components=["x","y"]、component_shape=[2]。不输出模型专有湍流变量。每个输出时间轴为下面规定物理时刻的非空子集，float64 严格递增；求解器内部步长自选，必须在给定时刻求值。

## 模型参数

`physics.parameters` 恰包含下表参数，每项为 `{{"value":有限数值,"unit":"单位"}}`；这些是本题固定工况值，数值必须与表一致。表外数值在下面文字给定，不从名称推断。无隐含缺省。

{parameters}

## 几何、条件与初态

{physical}

## 条件编码

每条记录恰含 `role,variable,operator,location,data`。位置名称任意，以实际引用的实体集合识别，不能根据 inlet 等字符串猜条件。

| role / operator | variable | data 完整键 | 含义 |
|---|---|---|---|
| initial / assign | velocity、pressure、气体题temperature 或下列额外状态 | value | 全域物理初态；标量常量或同位置场，矢量只用场 |
| boundary / dirichlet | 同上 | value | 该变量边界迹等于 value |
| boundary / normal_derivative | 同上 | value | 外法向导数等于 value；只允许本题指定的零值，单位为原量单位除以 m |
| boundary / slip | velocity | normal_velocity | 法向速度为给定 0 m/s，切向速度外法向导数为零 |
| boundary / pressure_open | flow | pressure, backflow_velocity | 边界静压为给定 Pa；流出速度外法向导数零；流入只取给定场的切向分量，法向由压力与连续性求解；压力不是总压，也不是总牵引 |
| boundary / advective_open | 下列额外标量状态 | backflow_value | 流出为零外法向导数，流入取给定同位置标量场或带单位常量 |
| source / pressure_mean | pressure | value | 全域平均静压 gauge 固定于 value；仅无压力开口的封闭腔体允许 |

`value`、`pressure` 使用带单位标量或同位置 field，`backflow_velocity` 必须是同位置矢量 field；slip 的 normal_velocity 使用带单位零标量。flow 仅为联合边界变量名，不是输出。其他源项禁止。不同变量的边界可共址，同一变量不得重叠约束；角点不另赋覆盖优先级。下文指定的固定墙 velocity 使用 dirichlet 零矢量场。压力在速度入口／无滑移壁由法向动量约束确定，不额外强制零梯度；仅明确写出的零法向导数出口按该条件处理。所有压力为静压 Pa；gauge 以环境绝对压力 101325 Pa 为参考，且未另外说明时无压力重对齐。

{extra_conditions}

## 允许输出

{outputs}

输出为求得连续场在给定单元上的物理平均，不是单元中心点值；二维按单位出平面厚度，轴对称例外见本题定义。只写 `outputs` 请求的数组及其 IDs、时间轴，key、dtype、shape、值与顺序按 CONTRACT；不写额外网格、坐标、输入状态或日志到结果文件。所有量使用同一声明的压力基准，判分不做平移、缩放、网格包围盒对齐或重排。
"""

def table(params):
    return '| 参数 | 固定值 | 单位 | 含义 |\n|---|---:|---|---|\n'+'\n'.join(f'| {k} | {v} | {u} | {d} |' for k,v,u,d in params)

def setup(key):
    params=[];notes=[];extra='';outputs='| quantity | 分量 | 单位 |\n|---|---|---|\n| velocity | x,y | m/s |\n| pressure | value | Pa |'
    if 'Obstacle' in key or key=='Double_Square_SA':
        model=SST if 'KOMEGA' in key else SA
        title=('双方形障碍物' if key=='Double_Square_SA' else '菱形障碍物' if 'Diamond' in key else '方形障碍物')+(' k–ω SST 非定常绕流' if 'KOMEGA' in key else ' SA 非定常绕流')
        geom='[0,5]×[0,2.5] m²，去掉 [1,2]×[0.75,1.75] 与 [3,4]×[0.75,1.75] 两个闭方形' if key=='Double_Square_SA' else '[0,15]×[0,5] m²，去掉顶点 (2.5,2)、(3,2.5)、(2.5,3)、(2,2.5) m 的闭菱形' if 'Diamond' in key else '[0,15]×[0,5] m²，去掉 [2,3]×[2,3] m² 闭方形'
        params=[('density',1,'kg/m3','补足恒定密度，使源运动学压力具有明确 Pa 换算'),('kinematic_viscosity',2e-6,'m2/s','常运动黏度')]
        physical=f'二维 xy 平面域为 {geom}。左右分别为入口、出口，其余边界无滑移静止壁。入口 u=(1,0) m/s；出口静压 gauge=101325 Pa，回流仅切向速度给零，法向由压力和连续性确定。初始原始速度 v=(1,0) m/s，但真正不可压初态为 u0=v−∇φ：解 Δφ=0，入口 ∂nφ=0，全部固壁 ∂nφ=v·n，出口 φ=0。投影只约束入口法向初态，出口法向自由；入口切向条件在t>0施加；该Helmholtz投影使初态无散且固壁无穿透。随后入口启动与壁面无滑移由非定常动量方程满足，切向瞬时不相容按黏性启动解释。初始压力不是独立物理初值，由动量约束和出口压力确定，不把均匀101325 Pa猜测当成额外约束。无体力、无能量方程、不可压缩；σ=−pI+2ρνD 加模型应力。时间区间 [0,5] s，输出 0,0.5,…,5 s。\n\n{model}'
        if 'KOMEGA' in key:
            extra='额外状态为 `turbulent_kinetic_energy` k（m2/s2）和 `specific_dissipation_rate` ω（1/s）。初态 k=0.00375、ω=0.0612。入口 k=0.00375、ω=sqrt(0.00375)/(0.09^0.25×1.2) s⁻¹；出口使用 advective_open，回流值为这两个入口值；壁面按上文到壁极限。边界 operator=`sst_wall`，variable=`turbulence`，data 恰有 `kinematic_viscosity`（m2/s 标量），表示上述到壁极限，不依赖首层网格。'
        else:
            extra='额外状态为 `modified_eddy_viscosity` q（m2/s）。初态和入口 q=1e-6 m2/s，出口使用 advective_open、回流 q=1e-6；所有无滑移墙 q=0。'
        notes=['prompt 与 blockMeshDict1 存在几何不一致，本题采用 prompt 且可执行 blockMeshDict 的明确几何。','源压力维度为m2/s2却值101325；本移植取rho=1并明确保留数值为gauge Pa，不冒称大气绝对压。','SST明确2003到壁模型，替代软件壁函数。' if 'KOMEGA' in key else '源壁函数配置不一致，SA统一解析到壁q=0。','不可压原始均匀速度穿过障碍法向，公开定义Helmholtz投影；初始pressure仅猜测不当额外初值。']
    elif key.startswith('Cavity'):
        les=key=='Cavity_LES';L=.2 if key=='Cavity_geometry_1' else .1
        title=f'{L:g} m 方腔'+('二维滤波非定常流动' if les else ' SA 非定常流动')
        model=LES if les else SA
        params=[('density',1,'kg/m3','恒密度'),('kinematic_viscosity',1e-5,'m2/s','运动黏度'),('side_length',L,'m','缩放后边长')]
        if les:params.append(('filter_width',.005,'m','固定物理滤波长度，不是内部网格尺寸'))
        physical=f'二维域 [0,{L}]×[0,{L}] m²；顶壁给定 u=(1,0) m/s，其他墙 u=(0,0)。所有壁为无滑移，顶壁切向运动不改变几何。不求温度，不施加体力。初态 u=(0,0)；压力由动量约束确定、全域面积平均为0 Pa，逐时保持此基准。时间 [0,10] s，请求时刻为0,0.5,…,10 s；原100步×0.005 s转换为物理输出间隔。\n\n{model}'
        extra='封闭域必须提供 source/pressure_mean，location 覆盖全域，data.value=0 Pa；不允许压力开口。'
        extra+='额外初态为 `subgrid_kinetic_energy` k_sgs=0.00375 m2/s2，壁面零法向导数。' if les else '额外状态 `modified_eddy_viscosity` q=3e-5 m2/s 为均匀初态；全部墙 q=0。'
        notes=['按prompt缩放定义实际边长。', 'LES保留prompt初始未解析能量0.00375，墙k零梯度，不迁移无关q文件。' if les else '源prompt与q初态/墙条件冲突，采用prompt q=3e-5且墙q=0。']
    elif key.startswith('Cylinder'):
        les=key.endswith('LES');model=LES if les else SA
        title='偏置圆柱'+('二维滤波非定常绕流' if les else ' SA 非定常绕流')
        params=[('density',1,'kg/m3','恒密度'),('kinematic_viscosity',.01,'m2/s','常运动黏度')]
        if les:params.append(('filter_width',.25,'m','固定物理滤波长度'))
        physical=f'二维域为 [-5,5]×[-1.5,2.5] m² 去掉中心(0,0)、半径1 m的圆柱截面。曲线以输入网格近似；不是直径0.1 m的其他同名基准。入口 x=−5，u=(1,0)；出口 x=5，p_gauge=0 Pa、∂n u=0；上下墙及圆柱为无滑移静止壁。出口不允许回流，本题模型仅覆盖该阶段。初态 u=(0,0)，压力由动量约束及出口基准确定；入口瞬时启动不相容按非定常启动解释。不可压缩、不求温度、无体力。t∈[0,2] s，输出0,0.05,…,2 s。\n\n{model}'
        extra='额外状态 `subgrid_kinetic_energy` k_sgs（m2/s2）初态0、入口2e-5、墙0，出口零法向导数。' if les else '额外状态 `modified_eddy_viscosity` q（m2/s）初态和入口均0.03，墙0，出口零外法向导数。'
        notes=['圆柱实际几何来自blockMeshDict；密度未给，公开补足rho=1。','源LES保留二维模型目标、不宣称三维LES；固定滤波模型不复现原网格逐格reference。' if les else '保留prompt SA初态与入口q=0.03，源无关k文件不迁移。']
    elif key in ['obliqueShock_LES','obliqueShock_KE','wedge_SA']:
        wedge=key=='wedge_SA';model=SA if wedge else SMAG if key.endswith('LES') else KE
        title='超声速楔面 SA 非定常流动' if wedge else '斜激波'+('二维滤波流动' if key.endswith('LES') else ' k–ε 非定常平均流动')
        mu=.01 if wedge else 1.6646e-4
        params=[('gas_constant',.7143,'J/(kg.K)','明确采用prompt给定R，消除分子量四舍五入歧义'),('specific_heat_cp',2.5,'J/(kg.K)','常比热'),('dynamic_viscosity',mu,'Pa.s','常动力黏度'),('prandtl_number',1,'1','分子Pr'),('turbulent_prandtl_number',.85,'1','移植补足湍流Pr')]
        if key.endswith('LES'):params.append(('filter_width',.05,'m','明确固定的滤波长度'))
        base='理想气体 p=ρRT，cv=cp−R，e=cvT，γ=cp/cv；数值上γ略异于1.4，以该闭合为准。求质量、动量、总能量守恒，Stokes体黏度约定；热导率λ=μcp/Pr，加湍流热扩散ρνt cp/Prt；绝对静压，无重力。'
        if wedge:
            physical=f'二维多边形顶点(-0.15242,0)、(0,0)、(0.3048,0.081670913853)、(0.3048,0.1524)、(-0.15242,0.1524) m。入口x=−0.15242给u=(5,0) m/s、p=1 Pa、T=1 K；顶部和底部水平段为对称，楔斜面为无穿透滑移、绝热；出口超声速流出，u,p,T零外法向导数，不允许回流。初态u=(5,0)、p=1、T=1，ρ由状态方程得。t∈[0,0.2] s，输出0,0.02,…,0.2 s。{base}\n\n{model}'
            extra='额外状态 `modified_eddy_viscosity` q 初态、入口及出口Dirichlet均1e-5 m2/s，楔面q=0；对称边q零法向导数。滑移速度壁的q=0是本题明确的模型边界，不等于无滑移。'
        else:
            physical=f'二维矩形 [0,4.1]×[0,1] m²，入口x=0给u=(2.9,0) m/s、p=1 Pa、T=1 K；顶边给u=(2.61933,−0.50632)、T=1.25853 K且p零外法向导数；底边对称，无穿透，p,T零法向导数；右边为超声速流出，u,p,T零法向导数。初态u=(2.9,0)、p=1、T=1，密度由状态方程得。计算区间[0,10] s，输出0,1,…,10 s。{base}\n\n{model}'
            extra='本题无独立亚格子能量初态或边界，Smagorinsky涡黏度由当前解析应变代数计算。' if key.endswith('LES') else '额外状态 `turbulent_kinetic_energy` k 初态及入口0.01 m2/s2、`dissipation_rate` ε 初态及入口0.001 m2/s3，顶、底、出口均零法向导数。总能量明确 E=cvT+|u|²/2，不含k；能量通量包含上述模型应力做功及湍流热通量，不再加独立k扩散通量或k耗散加热项；这是本移植规定的工程平均流闭合。'
        outputs+='\n| temperature | value | K |\n| density | value | kg/m3 |'
        notes=['保留归一化气体，R明确取prompt近似值、gamma由cp/R一致导出。','不约束rhoCentralFoam、源网格数和内部时间步；本题具体湍流闭合、热力学及能量定义公开给出。']
    elif key=='nozzleFlow2D_SA':
        title='轴对称燃料射流 SA 两相非定常流动'
        params=[('fuel_density',840,'kg/m3','燃料常密度'),('air_density',20,'kg/m3','气相常密度'),('fuel_kinematic_viscosity',5.952e-6,'m2/s','燃料运动黏度'),('air_kinematic_viscosity',8.5e-7,'m2/s','气相运动黏度'),('surface_tension',.0261,'N/m','恒定表面张力')]
        physical='本题为无旋流轴对称(x,r)子午面，不是平面射流；x∈[0,0.003]、r∈[0,0.0016] m。输入网格二维坐标的x,y分别代表轴向x和半径r；速度的x,y分量分别为u_x,u_r。x=0且r≤0.0001 m为入口，其余x=0为无滑移固壁；r=0为正则轴（u_r=0、∂r u_x=0，其他标量偶对称）；r=0.0016与x=0.003为环境开口。入口u=(460,0) m/s、燃料体积分数α=1；环境流入α=0、切向速度0而法向由压力与连续性确定，流出α零法向导数。环境压力满足p_gauge+ρ|u|²/2=0 Pa，压力不是去静水压；重力为0。初态全域u=0、α=0，压力由动量约束及全压开口确定。无相变、反应、热传递或气体可压缩性。t∈[0,1e-5] s，输出0,1e-6,…,1e-5 s。\n\n两相不可压缩、界面共享速度，α按保守体积输运，ρ=αρf+(1−α)ρa、μ=αρfνf+(1−α)ρaνa；表面张力按界面曲率产生法向应力跳跃σ κ，κ取向使球形燃料滴内部压力高。壁面接触角90°（通过燃料相测量），无接触线钉扎或额外动态接触角；无其他体力。面积与积分必须使用轴对称环带权重2πr，不能按单位厚度。\n\n'+SA
        extra='额外状态 `fuel_volume_fraction` α（1）和 `modified_eddy_viscosity` q（m2/s）。q初态及入口1.7856e-5，固壁q=0，环境q使用advective_open、流入q=0；正则轴q与α零径向导数。SA中的分子ν=μ/ρ。环境不用上表pressure_open，而使用 boundary/total_pressure_open，variable=flow，data恰含 `total_pressure`（0 Pa）、`backflow_velocity`（同位置矢量场）；全压公式采用局部混合密度。环境速度流出为零外法向导数，流入只指定backflow_velocity的切向分量为0，法向由全压和连续性求解。α使用advective_open、回流0。axis边为 boundary/axis，variable=flow，data恰含 `normal_velocity`（0 m/s），表示上文正则条件；α及q用normal_derivative。轴对称输出单元平均用∫f2πr dxdr/∫2πr dxdr，覆盖上文平面面积平均规则；输入单元平均也使用同一权重。'
        outputs+='\n| fuel_volume_fraction | value | 1 |'
        notes=['源称2D但网格为角度楔形，解释为无旋流轴对称，保留子午面几何。','入口速度、密度、黏度、表面张力、初始空气来自源配置；q按prompt覆盖源0值；接触角明确补足90度。','输出均值采用2πr权重；不把压力转为运动学压力或假定可压缩。']
    else:
        raise ValueError(key)
    if key in ['Cavity_LES','Cylinder_LES']:
        notes.append('动态一方程模型采用软件无关固定Δ和完整高斯测试滤波定义，替换源随网格变化的体积滤波宽度及邻面离散滤波；不是原逐格reference复现。')
    if key=='obliqueShock_LES':
        notes.append('保留源Smagorinsky闭合，明确Cs=0.17与Delta=0.05m，舍弃源未消费的k初始文件；非原网格依赖滤波的逐格复现。')
    if key=='wedge_SA':notes.append('SA壁距显式包含滑移楔面，避免无无滑移壁时d未定义。')
    extra+='\n\n气体题中pressure与temperature的初态、边界必须成对提供以确定密度；density不作为独立初始约束。不可压题不提供initial/pressure，其压力由动量约束、指定开口或均值规范确定。初始速度为上文投影定义的题，initial/assign的value存原始v，不把其当未经投影的物理初态；除该特殊规则外assign直接给物理初态。初态额外变量均取非负值；输入与表列固定值不符即非法。'
    return title,params,physical,extra,outputs,notes

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);args=ap.parse_args()
    raw=args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:raise SystemExit('source SHA256 mismatch')
    src=json.loads(raw)
    for index,(key,v) in enumerate(src.items(),111):
        if key.startswith('counterFlow'):continue
        slug='fb-advanced-'+key.lower().replace('_','-')
        title,params,physical,extra,outputs,notes=setup(key)
        folder=ROOT/slug;(folder/'author').mkdir(parents=True,exist_ok=True)
        instruction=f'''# 2.12.{index} {title}

实现可重复运行的求解程序，完成下述具体工程工况，并按输入请求的空间单元和物理时刻输出结果。工况、材料及初边值定义见本题 [DATA.md](DATA.md)，通用文件规则见 [CONTRACT.md](../../../../docs/CONTRACT.md)。无需其他题目、原软件教程或作者材料。

## 任务与方法责任

求解本题标题所述的具体流动，保留给定材料响应、初边值、维度与物理时间。完整工况及必须遵守的湍流／界面模型责任集中定义在 DATA.md；本题不要求输出建模报告或某软件的内部变量。

几何与工况固定为本题声明，输入可改变离散网格、观测单元子集与请求时刻子集。提交冻结后须处理这些合法变化，不得硬编码某张网格的答案。允许自行选择语言、软件、内部网格、离散、非线性求解与时间步；必须遵守上述物理和模型责任。不强制指定实现软件，也不要求复现配置文件文本或内部迭代轨迹。

## 提交

入口 `solve.py`，每例执行：

```sh
python solve.py --input /path/to/problem.json --output /path/to/result.h5
```

读取路径以参数为准，输入相对路径相对 problem.json 所在目录。成功退出码0，输出为 CONTRACT 约定的独立 HDF5；日志写标准输出或错误。依赖在冻结前准备，逐例运行不使用网络。不得修改输入或依赖隐藏文件。

## 评价与交付阶段

数值评价对象为 DATA 列明的全部物理输出，按给定单元平均和时刻比较；不以配置文件相似度、网格拓扑相似度、残差或成功运行代替答案正确。每例全部请求通过才得1分，否则0分，题目成绩为通过比例。压力不平移，坐标不缩放，不以重新对齐消除物理误差。

本版本只交付题面和数据契约，尚无实际样例、参考、判分配置或运行资源校准，不能据此启动正式评测。数值容差、网格／输出规模上限、CPU／内存／墙钟预算及运行依赖清单须在数据验证后随公开题面一起冻结；当前不宣称任何未测限制或精度已可达。未要求本次制作数据或运行求解器。
'''
        (folder/'instruction.md').write_text(instruction,encoding='utf-8')
        (folder/'DATA.md').write_text(f'# 2.12.{index} {title}：数据说明\n\n'+COMMON_DATA.format(slug=slug,parameters=table(params),physical=physical,extra_conditions=extra,outputs=outputs),encoding='utf-8')
        record={'source_repository':'https://github.com/NLR-Theseus/cfdllmbench','revision':REV,'split':'advanced','source_id':key,'number':f'2.12.{index}','task':slug,'source_file_sha256':SHA,'prompt':v['usr_requirement'],'adaptation':notes,'status':'statements-only; no data, reference, runtime registration or calibration'}
        (folder/'author'/'source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
