"""Maintenance-only statement source; no case data or reference solver."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
MODELS={}

def par(unit,text,positive=False,nonnegative=False):
    return dict(unit=unit,text=text,positive=positive,nonnegative=nonnegative)
P={
'length':par('m','L，区间长度',True),
'density':par('kg/m3','rho，体密度',True),
'bulk_modulus':par('Pa','Kf，流体体积模量',True),
'radius':par('m','R，未变形内半径',True),
'wall_thickness':par('m','h，管壁厚度，h/R≤0.1',True),
'young_modulus':par('Pa','E，约束降维模型轴向／环向弹性模量（非另作三维平面应变换算）',True),
'flow_drag':par('Pa.s/m2','r，线性动量阻力系数',False,True),
'piston_mass':par('kg','M，活塞质量',True),
'piston_damping':par('N.s/m','C，活塞阻尼',True),
'piston_stiffness':par('N/m','Ks，活塞弹簧刚度',True),
'area':par('m2','A，液柱与活塞有效截面积',True),
'conductivity':par('W/(m.K)','k，热导率',True),
'heat_capacity':par('J/(m3.K)','c，单位体积定应变热容',True),
'alpha':par('1/K','alpha，线膨胀系数（允许0）',False,True),
'reference_temperature':par('K','T0，无应力平衡参考绝对温度',True),
'electric_conductivity':par('S/m','sigma0，参考温度电导率',True),
'resistivity_slope':par('1/K','a，电阻率温度系数',True),
'permittivity':par('F/m','eps，定应变介电常数',True),
'piezo_coefficient':par('C/m2','e，有符号应力电荷耦合系数'),
'viscosity':par('Pa.s','eta，Kelvin轴向／剪切黏性',True),
'omega':par('rad/s','omega，角频率',True),
'shunt_conductance':par('S','G，并联电导',False,True),
'shunt_capacitance':par('F','Cs，并联电容',False,True),
'magnetic_permeability':par('H/m','mu，定应变小信号磁导率',True),
'magneto_coefficient':par('T','b，有符号偏置线性磁弹性系数'),
'shear_modulus':par('Pa','Gm，厚度剪切弹性模量',True),
'biot_alpha':par('1','ab，Biot系数，0<ab≤1',True),
'storage':par('1/Pa','S，定应变流体储存系数',True),
'mobility':par('m2/(Pa.s)','m，渗透率／动力黏度',True),
'fluid_thermal':par('1/K','gamma，定应变热致流体含量系数（允许0）',False,True),
'seebeck':par('V/K','s，有符号常数Seebeck系数'),
}

def model(slug,section,title,mode,params,eq,bcs,outputs,notes='',timeout=360):
    # bcs: side -> [(key, unit, explanation)], complete fixed records
    MODELS[slug]=dict(section=section,title=title,mode=mode,parameters={k:P[k] for k in ['length']+params},equations=eq,boundaries={side:{k:dict(unit=u,text=t) for k,u,t in rows} for side,rows in bcs.items()},outputs={q:dict(unit=u,text=t,location=l,atol=at,rtol=rt) for q,u,t,l,at,rt in outputs},notes=notes,timeout=timeout)

model('compliant-tube-wave','17.1-fluid-solid','17.1.1 弹性管壁与液柱波','transient',
['density','bulk_modulus','radius','wall_thickness','young_modulus','flow_drag'],
'''在固定区间0≤x≤L求小扰动表压p、轴向截面平均速度v和薄壁径向位移w（向外为正）。方程
p_t/Kf+v_x+2w_t/R=0，rho v_t+p_x+r v=0，w=R²p/(E h)。
管壁局部环向弹性，无轴向位移或壁惯性。存储项必须包含w反馈，不能先按刚壁声速求p再附加w。零表压为外界恒压与初始压力。''',
{'left':[('pressure','Pa','p(0,t)')],'right':[('pressure','Pa','p(L,t)')]},
[('pressure','Pa','p(x,t)','domain',1e-3,.003),('velocity','m/s','v(x,t)','domain',1e-7,.003),('wall_displacement','m','w(x,t)','domain',1e-10,.003)],
'初态p=v=w=0。接收条件h/R≤0.1、全过程|w|/R≤0.01及|v|小于有效波速的0.01；后两项由正式数据制作核验，不由声明检查器证明。外界恒压不另加到输出p。')
model('acoustic-piston-feedback','17.1-fluid-solid','17.1.2 声学液柱与惯性活塞','transient',
['density','bulk_modulus','flow_drag','area','piston_mass','piston_damping','piston_stiffness'],
'''固定参考区间0≤x≤L中的线性声学液柱满足p_t/Kf+v_x=0，rho v_t+p_x+r v=0；p为相对活塞外侧恒压的表压，v沿+x。
右端活塞位移y沿+x，v(L,t)=y_t；M y_tt+C y_t+Ks y=A p(L,t)+F(t)。压力力沿+x为正，F为外部额外作用于活塞的有符号力。在线性参考面x=L匹配，不移动输入采样坐标。''',
{'left':[('pressure','Pa','p(0,t)')],'right':[('force','N','F(t)，不含液压力、弹簧力及阻尼力')]},
[('pressure','Pa','p(x,t)','domain',1e-3,.003),('velocity','m/s','v(x,t)','domain',1e-7,.003),('piston_displacement','m','y(t)，右端真实活塞状态','right',1e-9,.003)],
'初态p=v=y=y_t=0。数据保证|y|/L≤0.01、|v|≤0.01 sqrt(Kf/rho)，排除碰撞、泄漏与有限位移几何反馈。')
model('constrained-thermal-expansion','17.2-thermo-solid','17.2.1 稳态热膨胀约束响应','steady',
['young_modulus','alpha','conductivity','reference_temperature'],
'''均匀直杆0≤x≤L，theta=T−T0。稳态无体热源：−k theta_xx=0；轴向平衡sigma_x=0，sigma=E(u_x−alpha theta)。两端位移约束参与热应力确定；温度对变形单向作用，忽略反向热源与惯性。输出应力为全区间唯一常应力（拉正），不是三维等效应力。''',
{'left':[('temperature_rise','K','theta(0)'),('displacement','m','u(0)')],'right':[('temperature_rise','K','theta(L)'),('displacement','m','u(L)')]},
[('temperature_rise','K','theta(x)','domain',1e-5,.002),('displacement','m','u(x)','domain',1e-9,.002),('axial_stress','Pa','sigma，常值在每个真实采样点返回','domain',1e-2,.002)],
'数据保证T0+theta>0、|alpha theta|≤0.01及|u_x|≤0.01。无热膨胀基准缺省：T0始终显式提供。')
model('reciprocal-thermoelastic-wave','17.2-thermo-solid','17.2.2 双向瞬态热弹性','transient',
['density','young_modulus','alpha','conductivity','heat_capacity','reference_temperature','viscosity'],
'''小应变杆0≤x≤L，theta=T−T0，beta=E alpha。方程
rho u_tt=sigma_x，sigma=E u_x+eta u_xt−beta theta；
c theta_t+T0 beta u_xt=k theta_xx。
eta为线性Kelvin阻尼，二阶小量黏性耗散热不计；必须保留线性互易应变率热反馈，不能只做顺序热膨胀。''',
{'left':[('temperature_rise','K','theta(0,t)'),('displacement','m','u(0,t)')],'right':[('temperature_rise','K','theta(L,t)'),('traction','Pa','sigma(L,t)，即右端沿+x牵引')]},
[('temperature_rise','K','theta(x,t)','domain',1e-5,.003),('displacement','m','u(x,t)','domain',1e-9,.003)],
'初态u=u_t=theta=0。数据保证|theta|/T0≤0.01及|u_x|≤0.01；无额外体力或热源。')
for transient in (False,True):
    model(('transient' if transient else 'steady')+'-joule-feedback','17.3-electrothermal',('17.3.2 瞬态' if transient else '17.3.1 稳态')+'温敏电阻焦耳反馈','transient' if transient else 'steady',
    ['electric_conductivity','resistivity_slope','conductivity','reference_temperature']+(['heat_capacity'] if transient else []),
    '''均匀导电杆0≤x≤L，theta=T−T0。sigma(theta)=sigma0/(1+a theta)，J=−sigma(theta) phi_x，J_x=0（每时刻准静态），'''+('c theta_t=k theta_xx+J²/sigma(theta)。' if transient else '−k theta_xx=J²/sigma(theta)。')+'''
温度改变电导，电流解确定体积焦耳热，必须自洽；没有Seebeck、Peltier、位移电流或电磁波。电势左端固定0，右端施加V。''',
    {'left':[('temperature_rise','K','theta(0'+(',t)' if transient else ')'))],'right':[('temperature_rise','K','theta(L'+(',t)' if transient else ')')),('voltage','V','phi(L)；phi(0)=0始终固定')]},
    [('temperature_rise','K','theta(x'+(',t)' if transient else ')'),'domain',1e-5,.003),('electric_potential','V','phi(x'+(',t)' if transient else ')'),'domain',1e-7,.003)],
    ('初态theta=0，V(0)=0。' if transient else '求从V=0连续延拓的稳态支，接收范围保证下述低反馈范围内唯一。')+'边界温升非负，且a theta_boundary≤0.1；所有加载节点满足a sigma0 V²/k≤0.1，数据另核验全域a theta≤0.25。不允许用截断电导掩盖失效。',timeout=480)
model('static-piezoelectric-rod','17.4-piezoelectric','17.4.1 静态直接与逆压电','steady',
['young_modulus','piezo_coefficient','permittivity'],
'''均匀压电杆0≤x≤L，S=u_x，电场Ef=−phi_x。应力电荷形式sigma=E S−e Ef，D=e S+eps Ef；sigma_x=0，D_x=0。
两端均为理想等势电极，左端u=phi=0，右端总轴向应力sigma=s和电势phi=V。D沿+x为正，含直接压电响应；e有符号，不把耦合项当附加外载。''',
{'right':[('traction','Pa','sigma(L)=s'),('voltage','V','phi(L)=V')]},
[('displacement','m','u(x)','domain',1e-10,.002),('electric_potential','V','phi(x)','domain',1e-8,.002),('electric_displacement','C/m2','D，沿+x','domain',1e-10,.002)],
'无惯性、自由体电荷、漏电或初态；数据保证|u_x|≤0.01。')
model('shunted-piezoelectric-rod','17.4-piezoelectric','17.4.2 谐振压电与电极阻抗','harmonic',
['young_modulus','piezo_coefficient','permittivity','density','viscosity','omega','area','shunt_conductance','shunt_capacitance'],
'''采用Re[fhat exp(+i omega t)]，所有负载及输出为峰值复相量。S=u_x，Ef=−phi_x，sigma=(E+i omega eta)S−e Ef，D=e S+eps Ef。
sigma_x=−rho omega²u，D_x=0；左端u=phi=0，右端sigma=s，phi(L)=V为未知电极电压。
右电极自由电荷Q=−A D(L)，对地并联电导G与电容Cs，注入电极的外部电流I满足(G+i omega Cs)V+i omega Q=I。该电流方向与右电极电荷符号固定，不可改用Q=+A D。''',
{'right':[('traction','Pa','复应力s'),('current','A','外部向右电极注入的复电流I')]},
[('displacement','m','复u(x)','domain',1e-9,.003),('electric_potential','V','复phi(x)','domain',1e-7,.003)],
'eta>0排除无损机械极点；omega>0、eps>0，理想电极覆盖整个端面。数据保证唯一有限响应且|u_x|≤0.01。不计电磁传播或体漏电。')
model('magnetic-diffusion-elasticity','17.5-magneto-solid','17.5.1 导电磁弹性板的小信号谐响应','harmonic',
['density','shear_modulus','viscosity','magnetic_permeability','magneto_coefficient','electric_conductivity','omega'],
'''厚度方向x∈[0,L]，横向剪切位移u沿y，偏置附近的小信号磁场H沿y。Re[fhat exp(+i omega t)]峰值复相量。
剪切应变S=u_x，tau=(Gm+i omega eta)S−b H，B=b S+mu H；tau_x=−rho omega²u，H_xx=i omega sigma0 B。
后一式来自准静态导电磁扩散，忽略位移电流；b是指定偏置点的线性互易系数，不是无偏置材料的任意磁致伸缩常数。H方向始终沿+y，非端面外法向。''',
{'left':[('magnetic_field','A/m','H(0)')],'right':[('magnetic_field','A/m','H(L)'),('traction','Pa','tau(L)，作用于右面沿+y牵引')]},
[('displacement','m','复u_y(x)，左端u(0)=0','domain',1e-9,.003),('magnetic_field','A/m','复H_y(x)','domain',1e-6,.003)],
'无额外体力、自由体电流源或电磁波入射；表面磁场已指定。eta>0，数据核验小信号与小应变有效性，不求非线性磁滞和饱和。')
model('biot-consolidation','17.6-poroelastic','17.6.1 一维Biot固结','transient',
['young_modulus','biot_alpha','storage','mobility'],
'''饱和多孔柱0≤x≤L，u为骨架轴向位移、p为相对初始平衡孔压。准静态sigma_x=0，sigma=E u_x−ab p；流体含量增量zeta=ab u_x+S p，Darcy体积通量q=−m p_x，zeta_t+q_x=0。
E为本一维约束骨架模量，不再从泊松比换算。流体源为零，忽略重力、惯性及非饱和过程。''',
{'left':[('pressure','Pa','p(0,t)')],'right':[('pressure','Pa','p(L,t)'),('traction','Pa','sigma(L,t)；u(0,t)=0')]},
[('displacement','m','u(x,t)','domain',1e-9,.003),('pore_pressure','Pa','p(x,t)','domain',1e-3,.003)],
'初态p=u=0；0<ab≤1，S>0、m>0。数据保证饱和小应变，不能将ab u_xt丢弃为刚性骨架渗流。')
model('thermo-poroelastic-transient','17.7-multiple-fields','17.7.1 热孔隙弹性联合演化','transient',
['young_modulus','alpha','biot_alpha','storage','mobility','fluid_thermal','heat_capacity','conductivity','reference_temperature'],
'''均匀饱和小应变柱0≤x≤L，theta=T−T0，beta=E alpha；
sigma=E u_x−ab p−beta theta，sigma_x=0；
zeta=ab u_x+S p−gamma theta，zeta_t=m p_xx；
c theta_t+T0 beta u_xt+T0 gamma p_t=k theta_xx。
这是本题固定的线性互易三场模型，包含热致流体含量和压力／应变率热反馈，忽略对流及二阶耗散热。不能将温度只作为指定外场，或用独立热扩散替代第三式。''',
{'left':[('pressure','Pa','p(0,t)'),('temperature_rise','K','theta(0,t)')],'right':[('pressure','Pa','p(L,t)'),('temperature_rise','K','theta(L,t)'),('traction','Pa','sigma(L,t)；u(0,t)=0')]},
[('displacement','m','u(x,t)','domain',1e-9,.003),('pore_pressure','Pa','p(x,t)','domain',1e-3,.003),('temperature_rise','K','theta(x,t)','domain',1e-5,.003)],
'初态u=p=theta=0。0<ab≤1；gamma≥0；T0>0。接收条件T0 gamma²<S c，数据保证|theta|/T0≤0.01与|u_x|≤0.01。正定性仅为本线性模型接收条件，不声称通用热孔隙材料判据。',timeout=480)
model('thermoelectric-leg','17.7-multiple-fields','17.7.2 稳态热电输运与总热流','steady',
['electric_conductivity','conductivity','seebeck'],
'''均匀热电腿0≤x≤L，T为绝对温度，s为常数Seebeck系数。J=−sigma0(phi_x+s T_x)，J_x=0；总热流密度q=s T J−k T_x，q_x+J phi_x=0。
等价温度方程−k T_xx=J²/sigma0；仍须用电势和端温差共同决定J，热流包含Peltier项。phi(0)=0、phi(L)=V，T两端给定。q沿+x为正，单位W/m2，不是只含导热的−k T_x，也不是乘截面积后的热率。''',
{'left':[('temperature','K','T(0)>0')],'right':[('temperature','K','T(L)>0'),('voltage','V','phi(L)=V')]},
[('temperature','K','绝对T(x)','domain',1e-5,.002),('electric_potential','V','phi(x)','domain',1e-8,.002),('total_heat_flux','W/m2','q(x)，含s T J','domain',1e-4,.003)],
'无Thomson项（s为常数）、接触热阻或侧面换热。J和温度分布必须共同确定，phi有明确基准；数据保证正温度与常物性适用。')


def write(selected=None):
    chosen=MODELS if selected is None else {k:v for k,v in MODELS.items() if k in selected}
    for slug,c in chosen.items():
        d=ROOT/'qbank/17-multiphysics'/c['section']/slug;d.mkdir(parents=True,exist_ok=True)
        mode=c['mode'];complex_=mode=='harmonic';transient=mode=='transient';axis='response' if transient else 'state'
        intro=c['equations']+'\n\n'+c['notes']
        btable='| quantity | atol | rtol | 单位 |\n|---|---|---|---|\n'+''.join(f"| `{q}` | {s['atol']:g} | {s['rtol']:g} | `{s['unit']}` |\n" for q,s in c['outputs'].items())
        inst=f'''# {c['title']}

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。

{intro}

模型、初边值和参数解释已固定；考生负责数值离散、耦合算法与误差控制，语言／软件自由，解析或降阶方法覆盖完整契约同样有效。区间长度、材料系数、载荷{'时程' if transient else '及频率' if complex_ else ''}和真实采样坐标随算例变化，不要求复现参考算法。输入输出见[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{c['timeout']}秒墙钟（含启动与I/O）、2CPU、4096MB、0GPU、无网络；0退出并完整写出HDF5，无独立输出字节上限。生成求解器3600秒、构建1800秒；环境提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python。采样点2..2048，瞬态载荷轴2..256节点、响应轴1..256节点；稳态／谐波1帧。输入场与输出场各至多2000000数值分量。内部网格、时间步和迭代不由采样点／输出时刻指定。

资源与容差为待正式数据校准的设计目标，不声称任意参数都已证明可在预算内求准。

## 评分

每有效例正常退出、结构合法且全部请求quantity的全部时间、位置、分量满足`|结果−参考|≤atol+rtol·|参考|`得1，否则0，等号接受。{'复数按实部／虚部逐分量比较，不比较模长或调整整体相位。' if complex_ else ''}无去均值、归一化重排或固定偏置。

{btable}
成绩为通过有效例数／有效例数，无有效例不产生成绩。输入、参考或配置错误属于基础设施错误，不计考生失败。工具校验和临时fixture测试不证明耦合物理、参考精度或预算校准。
'''
        (d/'instruction.md').write_text(inst)
        params='| 参数 | 单位 | 定义与范围 |\n|---|---|---|\n'+''.join(f"| `{k}` | `{s['unit']}` | {s['text']}；{'严格正' if s['positive'] else '非负' if s['nonnegative'] else '任意有限实数'} |\n" for k,s in c['parameters'].items())
        time=('''time_axes恰含load、response。load引用float64[2..256]，从0严格递增到t_end>0；response引用float64[1..256]，严格递增且位于[0,t_end]，可以不包含0。所有输入场用load，输出场用response。load所有边界数据在t=0恰为0，包括温升、位移、压力、力、电压及牵引；两加载节点之间逐分量线性插值，禁止区间外外推。零初态为题目固定事实，不提供初猜或额外initial条件。response是观测时刻，不是内部步长。''' if transient else '''time_axes恰含state，引用float64[1]=[0.0]，输入和输出均用state。0仅是存储标记，不是物理初态或频率。''' )
        shape='components、component_shape=[2]、components=["real","imag"]，末轴为峰值复数实部／虚部' if complex_ else 'scalar、component_shape=[1]、components=["value"]'
        data=f'''# {slug} 数据契约

入口problem.json及data_file引用的扁平HDF5；路径相对清单。physics恰含model、parameters，model=`multiphysics-{slug}-v1`；task可省略，出现须为`{slug}`。禁止profile、contract_version、analysis、materials混用。未列出的参数、位置、条件、字段、源或初态均不接受。

## 物理定义

{intro}

## 参数全集

parameters恰含下表所有键；每项恰含value、unit，value为有限JSON实数（布尔不算数值），unit严格按表，不隐式换单位。下列符号用于本题方程，未另列的源均为0。

{params}

## 空间与身份

spatial_dimension=1；geometries与meshes为空对象。连续体区间由length=L定义，没有未提供的CAD或求解网格。locations恰含domain、left、right。domain为points，2..2048个真实物理采样点，coordinates为float64[N,1]，单位m，x∈[0,L]，坐标两两不同，可不含端点且不按x排序；IDs为非负严格递增int64[N]。数组行始终依IDs，不按坐标重排输出。left、right各为entities、各一项非负int64 ID，代表x=0／x=L处实际端口或端面（right在活塞题同时是活塞对象）；无coordinates或空间插值。两端ID相同也不表示同一对象，不跨location匹配。无其他locations或几何。域采样只定义输出点，不指定内部网格或离散模型。

## 时间与数组

{time}

输入场、输出场均float64，数组完整shape=[T,N,*component_shape]，本题统一采用{shape}，value_kind=point。{'每个复字段按Re[fhat exp(+i omega t)]解释，omega只由参数给定，禁止幅相或RMS布局。' if complex_ else '所有值均为实数，无复数或附加分量。'}逻辑field名和HDF5 array key可不同且自由；条件field引用前者，array引用后者。fields恰为条件实际引用的场，可由多个条件共享符合声明的同一场；不能按长度从其他位置借数据。

输入场sampling恰为space=uniform、time={'linear' if transient else 'constant'}、extrapolation=forbid。uniform只表示单个端口的值，不在不同端口之间插值；没有域输入场。quantity等于条件data键名，unit按下表，location与该条件相同，time_axis={'load' if transient else 'state'}，dtype、kind、shape、components和value_kind按上述固定格式。{'所有data项必须用field引用；复常量也编码为一帧field。' if complex_ else ('所有data项必须用field引用，以明确加载时间支撑，不接受value常量。' if transient else '每个data项可用field引用，或恰含value/unit的有限实数常量；常量均匀作用于该端口。')}

## 条件全集

每个下列端口恰一条条件；未列端口按物理定义的固定零值闭合，不添加条件。role=boundary、variable=coupled_boundary、operator=prescribed、location为对应端口；data恰含该端口下表全部键，无额外键。condition本身恰含这五项。不同端口不能合并为一条条件。

'''
        for side,bs in c['boundaries'].items():
            data+=f'### `{side}`\n\n| data键 | unit | 物理值 |\n|---|---|---|\n'+''.join(f"| `{k}` | `{v['unit']}` | {v['text']} |\n" for k,v in bs.items())+'\n'
        data+='''field表示片段（逻辑名可变，完整清单还需其他必填项）：

```json
{"data":{"'''+next(iter(next(iter(c['boundaries'].values()))))+'''":{"field":"boundary_value"}}}
```

## 输出全集

每个quantity至少请求一次，可重复请求，逻辑输出名与array key自由但不得重复占用数组key。均为上文类型、shape、components、float64及point，不带sampling，time_axis=`'''+axis+'''`。domain输出是连续解在真实坐标的点值；端点取域内唯一迹，端面实体上的输出是该真实对象状态，不是区域积分。

| quantity | unit | location | 定义 |
|---|---|---|---|
'''+''.join(f"| `{q}` | `{s['unit']}` | `{s['location']}` | {s['text']} |\n" for q,s in c['outputs'].items())+'''
结果HDF5恰含所有输出array及所需locations的IDs、所需时间轴；严格复制输入轴和身份。domain坐标、输入场及不被输出使用的端口IDs不写入结果。不导出新网格或额外数组。

## 接收与验证边界

输入场／输出场各至多2000000数值分量（含时间和分量轴，重复输出也计入）。除可由声明检查器验证的参数、单位、轴和组合外，正式数据制作还须核验模型适用、小信号／小应变条件、解与观测存在唯一性、参考精度及预算可达性；声明通过不构成这些证据。无正式数据时不能把协议fixture当物理参考。
'''
        (d/'DATA.md').write_text(data)
        policy=dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()})
        (d/'grading.json').write_text(json.dumps(policy,indent=2)+'\n')
        (d/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
        (d/'harbor').mkdir(exist_ok=True)
        (d/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 2\nmemory_mb = 4096\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
        (d/'harbor/requirements.txt').write_text('scipy==1.18.1\n')
    if selected is None:
        d=ROOT/'qbank/17-multiphysics';(d/'README.md').write_text('# 第十七章 多物理场耦合分析\n\n7节12题；给定一维连续体模型，求解方法自由。全部题面／自包含DATA与配置已编写不表示正式数据、参考、校准或评测已就绪。\n\n| 编号／题名 | 题面 | DATA |\n|---|---|---|\n'+''.join(f"| {c['title']} | [instruction]({c['section']}/{s}/instruction.md) | [DATA]({c['section']}/{s}/DATA.md) |\n" for s,c in MODELS.items())+'\n维护入口：[章规划](../design/chapter-17-multiphysics.md)、[进度与限制](../design/reviews/chapter-17-progress.md)。\n')

if __name__=='__main__':
    import sys
    write(sys.argv[1:] or None)
