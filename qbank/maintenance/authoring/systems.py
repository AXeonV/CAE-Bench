"""Maintain self-contained system-network statements; no data or reference solver."""
from pathlib import Path
from caeoj_tools.author import public_model_catalog
import json
ROOT=Path(__file__).resolve().parents[3]
MODELS={}


def field(unit,text,positive=False,nonnegative=False,shape=None,labels=None,dtype='float64'):
    return dict(unit=unit,text=text,positive=positive,nonnegative=nonnegative,shape=shape or [1],labels=labels or ['value'],dtype=dtype)


def record(role,location,data,axis='static'):
    return dict(role=role,location=location,data=data,axis=axis)


def output(unit,text,location='nodes',atol=1e-7,rtol=.002,shape=None,labels=None):
    return dict(unit=unit,text=text,location=location,atol=atol,rtol=rtol,shape=shape or [1],labels=labels or ['value'],dtype='float64')

ENDPOINTS=field('1','[tail,head]为nodes中的实际int64 ID，不是行号；两端不同',shape=[2],labels=['tail','head'],dtype='int64')


def network(slug,section,title,equations,props_node,props_edge,initial_node,sources,outputs,initial_edge=None,parameters=None,timeout=240,notes=''):
    records=dict(node_properties=record('material','nodes',props_node),edge_properties=record('material','edges',dict(endpoints=ENDPOINTS,**props_edge)))
    if initial_node:records['initial_nodes']=record('initial','nodes',initial_node)
    if initial_edge:records['initial_edges']=record('initial','edges',initial_edge)
    records['driving']=record('source','nodes',sources,'load')
    MODELS[slug]=dict(section=section,title=title,equations=equations,parameters=parameters or {},records=records,outputs=outputs,network=True,timeout=timeout,notes=notes)

for deadzone in (False,True):
    slug='deadzone-transmission-network' if deadzone else 'geared-torsional-network'
    network(slug,'18.1-mechanical-transmission',('18.1.2 含弹性死区的传动网络' if deadzone else '18.1.1 弹性变比传动网络'),
    '''每节点为相对惯性参考系的一自由度转子，角度theta、角速度omega，J_i omega_dot=F_i−d_i omega_i+支路力矩之和，theta_dot=omega。
每有向支路a→b具有指定有符号变比n，delta=theta_a−n theta_b，delta_dot=omega_a−n omega_b；'''+('t=k sign(delta) max(|delta|−g,0)+c delta_dot，其中sign(0)=0。弹性项在|delta|≤g恰为0，黏性项全程存在，含死区内。' if deadzone else 't=k delta+c delta_dot。')+'''
支路作用于a的力矩为−t，作用于b为+n t，输出t是尾端传向该支路的力矩。变比为无惯性的功率变换定义，不能按普通等大反向力矩连接。所有转子惯量为正；无固定角度、额外地约束、刚性齿轮约束或碰撞冲量。初态来自给定theta0、omega0，不是静态预平衡。''',
    dict(inertia=field('kg.m2','J，转动惯量',True),drag=field('N.m.s/rad','d，对惯性参考系黏性阻力',nonnegative=True)),
    dict(ratio=field('1','n，有符号变比，0.1≤|n|≤10'),stiffness=field('N.m/rad','k，弹性支路刚度',True),damping=field('N.m.s/rad','c，全程并联扭转阻尼',nonnegative=True),**({'gap':field('rad','g，对称弹性死区半宽',True)} if deadzone else {})),
    dict(angle=field('rad','theta0，初始角度'),angular_velocity=field('rad/s','omega0，初始角速度')),
    dict(torque=field('N.m','F，直接施加到每个节点的有符号外力矩')),
    dict(angle=output('rad','theta_i(t)',atol=1e-7),angular_velocity=output('rad/s','omega_i(t)',atol=1e-7),transmitted_torque=output('N.m','t_e(t)，尾端传入力矩','edges',1e-6)),timeout=300 if deadzone else 180,
    notes='角度不按2pi折返或重新对齐。死区题的折点按连续力ODE处理，不引入冲量、速度重置或接触历史。' if deadzone else '角度不按2pi折返或重新对齐；弹性变比元件已给定，不要求从齿形计算刚度。')
network('nonlinear-hydraulic-network','18.2-hydraulic','18.2.1 非线性阻容液压网络',
'''每节点为压力储存容腔，以共同恒定储槽压力为零点的表压p满足C_i p_dot=s_i−G_i p_i−(B q)_i。C为体积顺应性，G为对该共同储槽的线性泄漏导纳。
每支路a→b的体积流率q沿a→b为正，由R q+D q|q|=p_a−p_b唯一确定。R>0、D≥0，无液柱惯性；不能忽略平方压降或先指定流向。B为尾端+1、首端−1的关联矩阵。初始各节点p0给定，支路初流率由该瞬时压差关系确定。''',
 dict(compliance=field('m3/Pa','C，容腔体积顺应性',True),leakage=field('m3/(Pa.s)','G，到共同压力零点的泄漏导纳',nonnegative=True)),
 dict(resistance=field('Pa.s/m3','R，线性流阻',True),quadratic_resistance=field('Pa.s2/m6','D，平方压降系数',nonnegative=True)),
 dict(pressure=field('Pa','p0，初始表压')),dict(injection=field('m3/s','s，外部流入节点体积流率，正为注入')),
 dict(pressure=output('Pa','节点表压p',atol=1e-3),volume_flow=output('m3/s','支路q，按a→b正向','edges',1e-9)),
 notes='实际数据保证全程无空化及元件模型有效；声明检查不证明该适用性。表压可为负，不擅加大气压到输出。')
network('distributed-pipe-network','18.2-hydraulic','18.2.2 分布管路与容腔波动网络',
'''每有向管支路a→b有连续坐标x∈[0,l_e]，截面积A、密度rho、体积模量K、线性阻力r均在本管均匀。
管内表压P与沿+x的体积流率Q满足(A/K) P_t+Q_x=0，(rho/A) Q_t+P_x+r Q=0。
P_e(0,t)=p_a(t)，P_e(l_e,t)=p_b(t)。节点容腔C_i p_dot=s_i−G_i p_i−sum_{tail=i}Q_e(0,t)+sum_{head=i}Q_e(l_e,t)。
每管两端Q均按该管+x为正，首端流入节点项为+Q(l)，绝不能将首端输出改成外法向通量。节点具有正顺应性，所有管初态P=Q=0，所有节点初态p=0；加载从0开始且s(0)=0。各节点无外加压力约束。必须保留沿管传播与反射，不以单个集总阻力替代连续PDE。''',
 dict(compliance=field('m3/Pa','C，节点容腔顺应性',True),leakage=field('m3/(Pa.s)','G，节点向共同零表压储槽泄漏',nonnegative=True)),
 dict(length=field('m','l，管长',True),area=field('m2','A，截面积',True),density=field('kg/m3','rho，密度',True),bulk_modulus=field('Pa','K，体积模量',True),resistance_per_length=field('Pa.s/m4','r，方程中的单位长度线性流阻',nonnegative=True)),
 None,dict(injection=field('m3/s','s，节点外部注入体积流率，t=0恰为0')),
 dict(pressure=output('Pa','节点表压p',atol=1e-3,rtol=.003),endpoint_volume_flow=output('m3/s','[Q(0,t),Q(l,t)]，两个分量均沿支路+x','edges',1e-9,.003,[2],['tail','head'])),timeout=600,
 notes='固定参考管道、无壁运动。正式数据保证|P|/K≤0.01、|Q|/(A sqrt(K/rho))≤0.01；初边角点按因果弱解，观测为连续端口迹。内部空间网格和时间步自由，不由拓扑或请求时刻规定。')
network('isothermal-pneumatic-network','18.3-pneumatic','18.3.1 等温气动容腔与毛细阻流网络',
'''固定容腔理想气体，所有节点由充分恒温换热维持同一给定绝对温度Tg，气体比气体常数Rg。每节点绝对压力p>0满足[V_i/(Rg Tg)] p_dot=s_i−(B mdot)_i。
每条有向长毛细管a→b的质量流率mdot=H_e(p_a²−p_b²)，H>0为已给定等温层流导通系数，沿a→b为正。B为尾端+1、首端−1关联矩阵。不另用喷口临界流／绝热关系或以表压代入平方关系。管内储存与动量惯性忽略；初始绝对压力p0给定。''',
 dict(volume=field('m3','V，固定容腔体积',True)),dict(conductance=field('kg/(s.Pa2)','H，固定毛细质量导通系数',True)),
 dict(pressure=field('Pa','p0>0，初始绝对压力',True)),dict(mass_injection=field('kg/s','s，节点外部质量注入，允许有符号抽取')),
 dict(absolute_pressure=output('Pa','节点绝对压力p',atol=1e-3),mass_flow=output('kg/s','支路mdot，正向a→b','edges',1e-9)),
 parameters=dict(gas_constant=field('J/(kg.K)','Rg，比气体常数',True),gas_temperature=field('K','Tg，共同恒定绝对温度',True)),
 notes='正式数据核验全程p>0、理想气体／等温层流毛细管假设和预算内可达精度；不将元件导通关系解释为任意压比喷口模型。')
network('radiative-thermal-network','18.4-thermal','18.4.1 非线性传导辐射热网络',
'''节点为等温储热体，绝对温度T_i、正热容C_i；C_i T_dot=S_i−(B q)_i+h_i(Ta_i−T_i)+sigmaSB Aenv_i(Ta_i^4−T_i^4)。
支路a→b传热率q=g_e(T_a−T_b)+sigmaSB Arad_e(T_a^4−T_b^4)，正向a→b。B为尾端+1、首端−1关联矩阵。sigmaSB固定5.670374419e−8 W/(m2.K4)。
Arad和Aenv是包含发射率、面积及交换因子的非负有效辐射面积，由输入直接给定，不再从几何推导或重复乘发射率。h是对节点独立外界温度Ta的传导／对流热导，不是单位面积换热系数。所有初始绝对温度T0给定。''',
 dict(heat_capacity=field('J/K','C，节点集总热容',True),ambient_conductance=field('W/K','h，节点对外界热导',nonnegative=True),ambient_radiative_area=field('m2','Aenv，对外界有效辐射面积',nonnegative=True)),
 dict(conductance=field('W/K','g，支路热导',True),radiative_area=field('m2','Arad，支路有效辐射面积',nonnegative=True)),
 dict(temperature=field('K','T0，初始绝对温度',True)),dict(heat_source=field('W','S，外部热率，正加热'),ambient_temperature=field('K','Ta，节点各自的外界绝对温度',True)),
 dict(temperature=output('K','节点绝对温度T',atol=1e-5),heat_rate=output('W','支路热率q，正向a→b','edges',1e-5)),notes='实际数据保证全程正温度及集总均温／常热容适用。外界温度是给定热浴，不另计入节点图或未知状态。')
network('nonlinear-diode-rlc-network','18.5-electrical','18.5.1 双向二极管RLC网络',
'''每节点对共同电气参考地有C_i>0电容和G_i≥0漏导，电势V_i满足C_i V_dot=S_i−G_i V_i−(B I)_i。
每有向支路a→b串联L_e>0、R_e>0和一对理想化相同反并联Shockley二极管：L_e I_dot=V_a−V_b−R_e I−Vt_e asinh[I/(2 Is_e)]。
其中Is>0、Vt>0为给定常数；反并联对的I=2 Is sinh(Vd/Vt)，故上式二极管电压Vd不可改成单向截止开关或单二极管关系。B为尾端+1、首端−1关联矩阵，I沿a→b为正。给定节点初始电势V0和支路初始电流I0。''',
 dict(capacitance=field('F','C，对共同地电容',True),leakage=field('S','G，对共同地漏导',nonnegative=True)),
 dict(inductance=field('H','L，支路电感',True),resistance=field('Ohm','R，支路电阻',True),saturation_current=field('A','Is，单二极管饱和电流',True),thermal_voltage=field('V','Vt，指定二极管热电压，固定物性参数',True)),
 dict(voltage=field('V','V0，节点初始电势')),dict(current_source=field('A','S，向节点注入电流，允许正负')),
 dict(voltage=output('V','节点对地电势V',atol=1e-7),current=output('A','支路电流I，正向a→b','edges',1e-8)),
 initial_edge=dict(current=field('A','I0，支路初始电流')),timeout=300,
 notes='无其他电压源、理想开关、结电容、反向击穿或二极管温度反馈。参考地是公共电气基准，不是某个nodes实体；正节点电容允许任意有限初始V。')


def system(slug,section,title,equations,properties,sources,outputs,notes='',control=False,timeout=240):
    records=dict(properties=record('material','systems',properties),driving=record('source','systems',sources,'load'))
    if control:records['reference']=record('source','systems',dict(position_reference=field('rad','r_k，采样时钟第k点的参考角度')),'control')
    MODELS[slug]=dict(section=section,title=title,equations=equations,parameters={},records=records,outputs=outputs,network=False,control=control,timeout=timeout,notes=notes)

MOTOR=dict(inductance=field('H','L，电枢电感',True),resistance=field('Ohm','R0，参考温度电阻',True),motor_constant=field('V.s/rad','K，反电动势常数；SI数值也作力矩常数N.m/A',True),inertia=field('kg.m2','J，转子惯量',True),drag=field('N.m.s/rad','B，机械黏性阻力',nonnegative=True))
system('motor-thermal-feedback-system','18.6-cross-domain','18.6.1 电机旋转热反馈系统',
'''每个systems对象是一套独立集总电机—惯性—热系统。反电动势K omega和电磁力矩K i使用同一正SI耦合常数K，保证功率转换一致。
R(T)=R0[1+a(T−Tref)]；L i_dot=U−R(T)i−K omega；J omega_dot=K i−B omega−tau；
Cth T_dot=R(T)i²+B omega²−H(T−Ta)。tau沿正转方向的阻力矩为正，可有符号。Ta是给定外界绝对温度，T为线圈与黏性耗散统一热节点的绝对温度，所有B omega²均进入该热节点；负载做功tau omega不进入该节点。
固定初态i=omega=0、T=Tref。不同systems之间无未声明耦合。''',
 dict(**MOTOR,temperature_coefficient=field('1/K','a，电阻温度系数',nonnegative=True),reference_temperature=field('K','Tref，初始与电阻参考绝对温度',True),heat_capacity=field('J/K','Cth，统一热节点热容',True),heat_transfer=field('W/K','H，对外界热导',True)),
 dict(voltage=field('V','U，端电压'),load_torque=field('N.m','tau，外部有符号阻力矩'),ambient_temperature=field('K','Ta，外界绝对温度',True)),
 dict(current=output('A','电枢电流i','systems',1e-8),angular_velocity=output('rad/s','转速omega','systems',1e-7),temperature=output('K','统一热节点绝对温度T','systems',1e-5)),
 notes='正式数据保证全程T>0、R(T)>0及固定电机／集总热模型适用。不考虑磁饱和、铁损或分布温度场。')
system('electrohydraulic-actuator-system','18.6-cross-domain','18.6.2 电机泵与双腔液压执行系统',
'''每个systems对象为一套独立闭式电机泵—双腔液压缸—弹簧阻尼质量系统。变量i、omega、x、v、pA、pB；pA/B为相对共同参考绝对压力p0的表压。
L i_dot=U−R0 i−K omega；J omega_dot=K i−B omega−D(pA−pB)；
Q=D omega−Cl(pA−pB)，正流量从腔B泵往腔A；x_dot=v；M v_dot=A(pA−pB)−c v−k x−F；
VA=VA0+A x，VB=VB0−A x；pA_dot=Kf(Q−A v)/VA，pB_dot=Kf(−Q+A v)/VB。
D是泵每转角排量m3/rad，其SI数值使压差反力矩D(pA−pB)和流量D omega功率一致；Cl是A向B的内部泄漏导纳，Q已减去泄漏，不能再次从腔方程扣漏流。
固定初态i=omega=x=v=pA=pB=0。U有符号端电压，F为沿−x方向的有符号外部阻力；无行程止挡或速度重置。''',
 dict(**MOTOR,pump_displacement=field('m3/rad','D，泵排量',True),internal_leakage=field('m3/(Pa.s)','Cl，双腔内部泄漏导纳',nonnegative=True),mass=field('kg','M，平移质量',True),piston_area=field('m2','A，两腔相同有效活塞面积',True),linear_damping=field('N.s/m','c，平移阻尼',nonnegative=True),stiffness=field('N/m','k，弹簧刚度',True),volume_a=field('m3','VA0，x=0时腔A体积',True),volume_b=field('m3','VB0，x=0时腔B体积',True),bulk_modulus=field('Pa','Kf，液体体积模量',True),reference_pressure=field('Pa','p0，共同参考绝对压力',True)),
 dict(voltage=field('V','U，电机端电压'),load_force=field('N','F，有符号外部阻力')),
 dict(current=output('A','电枢电流i','systems',1e-8,.003),angular_velocity=output('rad/s','转子角速度omega','systems',1e-7,.003),displacement=output('m','活塞位移x','systems',1e-8,.003),velocity=output('m/s','活塞速度v','systems',1e-7,.003),chamber_pressure=output('Pa','[pA,pB]，两腔表压','systems',1e-2,.003,[2],['A','B'])),
 notes='正式数据保证全程VA>0、VB>0、p0+pA>0、p0+pB>0，且无空化／止挡和常物性失效；声明检查只核验初始参数正性，不证明轨迹限制。',timeout=480)
system('sampled-position-servo','18.7-sampled-control','18.7.1 饱和与抗积分饱和的采样位置伺服',
'''每个systems对象为独立数字位置伺服。连续对象：theta_dot=omega，L i_dot=U−R0 i−K omega，J omega_dot=K i−B omega−tau。固定初态theta=omega=i=0。
数字控制时钟给定0=t0<t1<…<tN=t_end，所有系统共享时钟；每系统积分状态z0=0。在tk用连续状态theta(tk)和该节点参考r_k计算e_k=r_k−theta(tk)，w_k=Kp e_k+Ki z_k，U_k=min(Umax,max(−Umax,w_k))。
在[tk,t{k+1})严格保持U=U_k；若|w_k|≤Umax或w_k e_k<0，则z{k+1}=z_k+(t{k+1}−tk)e_k，否则z{k+1}=z_k。该递推只在时钟上执行，不能用连续PI或改成先更新积分再算U。
最后时刻tN仍用theta(tN)、r_N、z_N计算U_N并作为端点输出，不再更新z。等号按未饱和分支；U输出在时钟点取新值，右连续；连续状态跨时钟不重置。tau是沿正转方向的有符号外部阻力矩。''',
 dict(**MOTOR,proportional_gain=field('V/rad','Kp，比例增益',True),integral_gain=field('V/(rad.s)','Ki，积分增益',nonnegative=True),voltage_limit=field('V','Umax，对称限幅',True)),
 dict(load_torque=field('N.m','tau，外部有符号阻力矩')),
 dict(angle=output('rad','theta','systems',1e-7),angular_velocity=output('rad/s','omega','systems',1e-7),current=output('A','i','systems',1e-8),control_voltage=output('V','保持电压U，在采样时钟点取新U_k','systems',1e-6)),
 notes='K、R0均固定，不含温度模型。control时钟与响应时刻独立，控制器不得在响应时刻额外更新。反向参考、饱和进入／退出和非均匀时钟均属于公开范围。',control=True,timeout=300)


def write(selected=None):
    chosen=MODELS if selected is None else {k:v for k,v in MODELS.items() if k in selected}
    for slug,c in chosen.items():
        d=ROOT/'qbank/18-system-multidomain'/c['section']/slug;d.mkdir(parents=True,exist_ok=True)
        intro=c['equations']+'\n\n'+c['notes']
        variations=('连通拓扑、并联支路、有向编号、元件参数及外源时程' if slug=='distributed-pipe-network' else '连通拓扑、并联支路、有向编号、元件参数、初态及外源时程') if c['network'] else ('元件参数、外源及参考时程' if c.get('control') else '元件参数及外源时程')
        comparison_exclusions='无去均值、'+('角度折返、' if 'angle' in c['outputs'] else '')+'按方向取绝对值、偏置拟合或超限豁免。'
        input_dtype='仅endpoints输入场为int64，其他输入场均float64；IDs为int64。' if c['network'] else '本题全部输入场均float64；IDs为int64。'
        initial_note='initial字段只定义t=0而非迭代初猜；' if any(r['role']=='initial' for r in c['records'].values()) else ''
        output_order_note='不重排或取绝对值'+('，不按图方向重新定向。' if c['network'] else '。')
        if not c['network'] and slug!='motor-thermal-feedback-system':
            s=c['records']['properties']['data']['resistance']
            c['records']['properties']['data']['resistance']={**s,'text':'R0，固定电枢电阻'}
        scores='| quantity | atol | rtol | unit |\n|---|---|---|---|\n'+''.join(f"| `{q}` | {s['atol']:g} | {s['rtol']:g} | `{s['unit']}` |\n" for q,s in c['outputs'].items())
        size='nodes 2..128、edges 1..256' if c['network'] else 'systems 1..32'
        instruction=f'''# {c['title']}

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。

{intro}

模型和元件关系固定，考生负责按身份组装、求解、内部时间步及误差控制；{'分布管路的内部空间离散也由考生决定。' if slug=='distributed-pipe-network' else ''}语言与软件自由，解析／降阶方法覆盖全部公开契约同样有效，不要求某种参考算法。{variations}由算例改变。输入输出只依赖[本题DATA](DATA.md)和[通用CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{c['timeout']}秒墙钟（含启动和I/O）、2CPU、4096MB、0GPU、无网络；正常0退出并完整写HDF5，无独立输出字节上限。生成求解器3600秒、构建1800秒。提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python或Modelica。

规模：{size}，load 2..256时间采样点，response 1..256时间采样点，static 1帧{'; control 2..256时间采样点' if c.get('control') else ''}；输入场／输出场各至多2000000数值分量。资源与容差是待校准设计目标，正式数据必须独立核验精度、模型适用性与预算可达性，不能由结构合法参数推得全范围已验证。

## 评分

每有效例正常退出、结构合法，且全部请求quantity在所有时刻／对象／分量满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0；等号接受。{comparison_exclusions}

{scores}
成绩为通过有效例数／有效例数；输入、参考或配置错误归基础设施错误，不计考生失分，无有效例不产生成绩。仅声明检查与临时工具测试不证明物理或数值正确。
'''
        (d/'instruction.md').write_text(instruction, encoding='utf-8')
        parameters='parameters为空对象，所有元件系数均由下列material字段逐对象给定，没有隐含全局数值参数。'
        if c['parameters']:
            parameters='parameters恰含下表所有项，每项仅value、unit，value为有限JSON实数，布尔不算数值，不隐式换单位。\n\n| 键 | unit | 定义 |\n|---|---|---|\n'+''.join(f"| `{k}` | `{s['unit']}` | {s['text']}，严格正 |\n" for k,s in c['parameters'].items())
        topology='''locations恰含nodes、edges，均为entities；nodes 2..128个真实储能节点，edges 1..256条真实元件支路。各自IDs为非负严格递增int64；不同表可出现相同ID，不能据此配对。无coordinates。edge_properties.endpoints的每行[tail,head]引用nodes的实际ID，禁止自环；忽略方向后的整个图须连通，允许环与并联，不以支路方向限制实际流动方向。除题目明文的对参考／环境连接外，没有未声明节点或支路。组件字段按所属location的ID行序，不按端点行序或ID数值作数组下标。'''
        if not c['network']:
            topology='''locations恰含systems，为entities；IDs为1..32个非负严格递增int64，代表独立的真实系统对象，不是伪空间采样点。每个对象内部连接按本题方程固定，不同对象互不耦合，也不默认共享状态。无coordinates或额外端口表。每个参数／输入／输出行对应该系统ID，不按ID数值作为数组下标。'''
        time='''time_axes恰含static、load、response。static引用float64[1]=[0.0]，用于不随时间变的属性和t=0初态。load引用float64[2..256]，从0严格递增至t_end>0。response引用float64[1..256]，严格递增且全部在[0,t_end]，可不含0或终点。load字段逐分量在load轴相邻时间采样点之间线性插值，禁止外推；不同实体之间不插值。输出时刻不是内部积分步或控制更新时刻。'''
        if c.get('control'):
            time=time.replace('恰含static、load、response','恰含static、load、response、control')+'''control引用float64[2..256]，严格递增，首点0、末点与load末点完全相等。control上参考字段仅提供各采样点值，按previous保持至下一时钟，但控制器只在control时钟计算；最后时钟点取新参考值。控制时钟与load节点、response时刻不必重合。'''
        data=f'''# {slug} 数据契约

入口problem.json与data_file所指扁平HDF5，路径相对清单。physics恰含model、parameters；model=`systems-{slug}-v1`，task可省略，出现须为`{slug}`。禁止profile、contract_version、analysis、materials混用，不接受本题未列的参数、条件、字段、位置或输出quantity。

## 物理与初边值

{intro}

## 参数

{parameters}

## 对象、拓扑和身份

spatial_dimension=1，为一维端口／支路坐标标记；geometries、meshes均为空对象，没有缺失的CAD或求解网格。{topology}

## 时间、存储与重建

{time}

全部场的value_kind=point，表示对象自身的状态、参数或端口值，不能解释为任意空间点或区域平均／积分。数组必须有完整[T,N,*component_shape]。标量float64字段kind=scalar、component_shape=[1]、components=["value"]；多分量字段kind=components、shape和标签按下表。{input_dtype}输出均float64、response轴、不带sampling。

条件data中每个键对应的值必须恰为{{"field":"逻辑字段名"}}；不接受value常量、内联数组、option或location替代，重复的相同元件值也显式写入数组。逻辑field名及array key可自由选择且可不同，quantity严格等于data键名；字段location与条件完全一致，单位／类型／轴按下表。fields恰为实际引用字段；同一字段可以被符合相同声明的多个条件引用，但不能用数组长度替代位置身份。

输入sampling显式为space=uniform、extrapolation=forbid；static字段time=constant，load字段time=linear{'; control字段time=previous' if c.get('control') else ''}。uniform不表示整个图数值相同，仅表示每个离散对象自身的属性／端口量，不进行对象间插值。static的material字段全程不变，{initial_note}没有其他隐含初态或预平衡。

## 条件全集

每个下列operator恰一条，覆盖完整对应location。variable固定system_data；role、location如下；condition恰含role、variable、operator、location、data五键，data恰含该表全部键。表内“正／非负”约束作用于该字段所有值；未限制者为任意有限有符号实数。所有单位严格按表。

'''
        for op,r in c['records'].items():
            data+=f"### `{op}`\n\nrole=`{r['role']}`，location=`{r['location']}`，全部字段time_axis=`{r['axis']}`。\n\n| data键 | unit | 类型／分量 | 定义与范围 |\n|---|---|---|---|\n"
            for k,s in r['data'].items():
                desc=('scalar [1] / value' if s['shape']==[1] else f"components {s['shape']} / {','.join(s['labels'])}")
                data+=f"| `{k}` | `{s['unit']}` | {s['dtype']} {desc} | {s['text']}；{'严格正' if s['positive'] else '非负' if s['nonnegative'] else '按定义'} |\n"
            data+='\n'
        data+='''condition片段示意（不是完整样例，逻辑名可变）：

```json
{"data":{"'''+next(iter(next(iter(c['records'].values()))['data']))+'''":{"field":"input_property"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求；逻辑输出名、array key自由但不得重复占用key。均为response轴、float64、point、无sampling；scalar为[1]/value，多分量按表。{output_order_note}

| quantity | unit | location | shape／components | 定义 |
|---|---|---|---|---|
'''+''.join(f"| `{q}` | `{s['unit']}` | `{s['location']}` | {s['shape']} / {','.join(s['labels'])} | {s['text']} |\n" for q,s in c['outputs'].items())+'''
结果HDF5恰含全部输出array、输出使用的locations之IDs和response时间数组，严格复制输入轴／身份。不额外写入属性、拓扑、未被输出复用的时间轴、坐标或其他数组；若输入不同轴共用相同key，只按输出需要复制一次，遵守CONTRACT的角色规则。

## 接收限制与证据

输入场／输出场各至多2000000数值分量，包含所有时间和分量轴，重复请求也计入。正式数据还须核验方程和元件适用性、全程状态接收限制、观测存在唯一性、参考误差及预算内可达精度；声明检查不会求解轨迹或代替这些证据。
'''
        data=data.replace('{output_order_note}',output_order_note)
        (d/'DATA.md').write_text(data, encoding='utf-8')
        (d/'author').mkdir(parents=True,exist_ok=True)
        (d/'author/grading-template.json').write_text(json.dumps(dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()}),indent=2)+'\n', encoding='utf-8')
        (d/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n', encoding='utf-8')
        (d/'harbor').mkdir(exist_ok=True)
        (d/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 2\nmemory_mb = 4096\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n', encoding='utf-8')
        (d/'harbor/requirements.txt').write_text('scipy==1.18.1\n', encoding='utf-8')
    if selected is None:
        d=ROOT/'qbank/18-system-multidomain';(d/'README.md').write_text('# 第十八章 系统级多领域分析\n\n7节10题，集总／一维分布网络与跨域系统；完成题面与配置不代表正式数据、参考或校准就绪。\n\n| 编号／题名 | 题面 | DATA |\n|---|---|---|\n'+''.join(f"| {c['title']} | [instruction]({c['section']}/{s}/instruction.md) | [DATA]({c['section']}/{s}/DATA.md) |\n" for s,c in MODELS.items())+'\n维护入口：[规划](../design/chapter-18-system-multidomain.md)、[进度](../design/reviews/chapter-18-progress.md)。\n', encoding='utf-8')
        public=ROOT/'qbank/extensions/caeoj_ext/systems/models.json'
        if public.parent.exists():public.write_text(json.dumps(public_model_catalog({k:{key:v for key,v in c.items() if key not in ('equations','notes','title','section','timeout')} for k,c in MODELS.items()}),indent=2)+'\n', encoding='utf-8')

if __name__=='__main__':
    import sys
    write(sys.argv[1:] or None)
