"""Maintain self-contained statements and declaration metadata; never make cases."""
from pathlib import Path
from caeoj_tools.author import public_model_catalog
import json
ROOT=Path(__file__).resolve().parents[3]
CH=ROOT/'qbank/04-multibody-mechanics'
SECTIONS=[('4.1-kinematics','约束运动学与逆动力学',['planar-kinematics','planar-inverse-dynamics']),('4.2-rigid-dynamics','刚体多体动力学',['planar-multibody','spatial-free-rigid']),('4.3-connectors-drives','柔顺连接与驱动',['elastic-connectors','prescribed-drive']),('4.4-contact','柔顺接触与摩擦',['normal-contact','regularized-friction']),('4.5-impact','瞬时碰撞与冲量',['normal-impact','frictional-impact']),('4.6-flexible','柔性体与刚柔耦合',['modal-flexible','translating-flexible'])]
NAMES=['平面机构约束运动学','平面机构逆动力学','平面约束多体动力学','空间自由刚体动力学','弹簧阻尼连接动力学','给定运动驱动动力学','圆盘法向柔顺接触','圆盘正则化摩擦接触','圆盘无摩擦瞬时碰撞','圆盘摩擦瞬时碰撞','固定参考系柔性体模态响应','平移刚体与柔性模态耦合']

def f(unit,shape,meaning,**kw):return dict(unit=unit,shape=shape,meaning=meaning,**kw)
S=lambda u,m,**k:f(u,[1],m,**k)
V=lambda d,u,m:f(u,[d],m,kind='vector')
C=lambda shape,u,m:f(u,shape,m,kind='components')
P=lambda u,m,lower=None,upper=None,integer=False:dict(unit=u,meaning=m,lower=lower,upper=upper,integer=integer)
M={}
for slug,name in zip([s for _,_,ss in SECTIONS for s in ss],NAMES):
 impulse='impact' in slug; modal=slug in ('modal-flexible','translating-flexible'); spatial=slug=='spatial-free-rigid'; kin=slug=='planar-kinematics'; inv=slug=='planar-inverse-dynamics';contact=slug in ('normal-contact','regularized-friction')
 cfg=dict(name=name,dimension=3 if spatial else 2,family='modal' if modal else 'spatial' if spatial else 'impact' if impulse else 'planar',parameters={},records={},outputs={},timeout=120 if impulse else 900,limits=dict(entities=32,locations=129,frames=201,components=2000000))
 if not impulse:cfg['parameters'].update(start_time=P('s','初始时刻t0'),end_time=P('s','终止时刻tf，tf>t0'))
 if modal:cfg['parameters']['mode_count']=P('1','模态数k，整数',1,12,True)
 if impulse:cfg['parameters']['restitution']=P('1','法向恢复系数e',0,1)
 if slug=='frictional-impact':cfg['parameters']['friction']=P('1','冲量库仑系数μ',0)
 def rec(op,role,var,loc,data,required=True):cfg['records'][op]=dict(role=role,variable=var,location=loc,data=data,required=required)
 def out(q,u,shape,meaning,loc=None,atol=1e-6,kind=None):cfg['outputs'][q]=f(u,shape,meaning,location=loc or ('systems' if modal else 'bodies'),atol=atol,kind=kind or ('scalar' if shape==[1] else 'components'))
 if modal:
  body={'mass_matrix':C(['k','k'],'kg','对称正定模态质量M'),'stiffness':C(['k','k'],'N/m','对称正定模态刚度K'),'damping':C(['k','k'],'kg/s','对称半正定模态阻尼C'),'eta0':C(['k'],'m','初始模态位移η0'),'eta_dot0':C(['k'],'m/s','初始模态速度')}
  if slug=='translating-flexible':body.update(carrier_mass=S('kg','载体平移质量m>0',positive=True),coupling=C([2,'k'],'kg','双向惯性耦合B；完整质量矩阵正定'),position0=V(2,'m','载体初始质心位置x0'),velocity0=V(2,'m/s','载体初始速度'))
  rec('modal_system','material','system','systems',body)
  load={'modal_force':C(['k'],'N','各模态广义力f(t)')}
  if slug=='translating-flexible':load['force']=V(2,'N','载体外力F(t)，不另加重力')
  rec('loads','source','load','systems',load)
  out('modal_displacement','m',['k'],'η，按给定模态顺序，不作重新归一化或模态重排')
  out('modal_velocity','m/s',['k'],'η对时间导数',atol=1e-5)
  if slug=='translating-flexible':
   out('position','m',[2],'载体质心位置x',kind='vector');out('velocity','m/s',[2],'载体质心速度',atol=1e-5,kind='vector')
 elif spatial:
  rec('body','material','body','bodies',dict(mass=S('kg','质量m>0',positive=True),inertia=C([3,3],'kg.m2','质心体坐标惯性I，对称正定且三个主惯量满足三角不等式'),position0=V(3,'m','初始质心位置'),quaternion0=C([4],'1','单位四元数，分量w,x,y,z；体坐标到全局的主动旋转'),velocity0=V(3,'m/s','初始全局质心速度'),omega0=C([3],'rad/s','初始体坐标角速度，分量wx,wy,wz')))
  rec('loads','source','load','bodies',dict(force=V(3,'N','全局质心合外力，已包含重力'),torque=C([3],'N.m','体坐标质心合外转矩')))
  out('position','m',[3],'全局质心位置',kind='vector');out('velocity','m/s',[3],'全局质心速度',atol=1e-5,kind='vector');out('quaternion','1',[4],'体到全局的四元数w,x,y,z，连续沿用初态符号',atol=1e-6);out('angular_velocity','rad/s',[3],'体坐标角速度wx,wy,wz',atol=1e-5)
 else:
  body=dict(position0=V(2,'m','初始质心位置'))
  if not impulse:body['angle0']=S('rad','初始体到全局转角θ0；不取模')
  if not kin:body.update(mass=S('kg','质量m>0',positive=True),inertia=S('kg.m2','质心平面转动惯量I>0',positive=True))
  if not (kin or inv):body.update(velocity0=V(2,'m/s','初始质心速度'),omega0=S('rad/s','初始角速度ω，逆时针为正'))
  if contact or impulse:body['radius']=S('m','圆盘半径r>0；惯量独立给定，质量可非均匀',positive=True)
  rec('body','material','body','bodies',body)
  if not kin and not impulse:rec('loads','source','load','bodies',dict(force=V(2,'N','全局质心合外力，已包含重力'),torque=S('N.m','质心合外转矩，逆时针为正')))
  if not contact and not impulse:
   joint=dict(a=P('1','第a体的实际ID，-1为地面',integer=True),b=P('1','第b体实际ID，-1为地面',integer=True),ax=P('m','a体局部锚点x'),ay=P('m','a体局部锚点y'),bx=P('m','b体局部锚点x'),by=P('m','b体局部锚点y'))
   rec('revolute','boundary','joint','site',joint,False)
   rec('weld','boundary','joint','site',dict(joint,angle=P('rad','约束θb−θa的常值')),False)
   if kin or inv or slug=='prescribed-drive':
    rec('angle_drive','boundary','angle','site',dict(body=P('1','被驱动体实际ID，不允许地面',integer=True),a0=P('rad','驱动θ(t)常数项'),a1=P('rad/s','一次项'),a2=P('rad/s2','二次项'),a3=P('rad/s3','三次项')),True)
   if slug=='elastic-connectors':rec('spring','source','connector','site',dict(joint,stiffness=P('N/m','轴向刚度k≥0',0),damping=P('kg/s','轴向黏性系数c≥0',0),rest_length=P('m','无应力长度l0>0',0)),True)
  if contact:
   data=dict(a=P('1','第a体实际ID',integer=True),b=P('1','第b体实际ID',integer=True),stiffness=P('N/m','法向刚度kn>0',0),damping=P('kg/s','法向阻尼cn≥0',0))
   if slug=='regularized-friction':data.update(friction=P('1','摩擦系数μ≥0',0),slip_speed=P('m/s','正则化速度vs>0',0))
   rec('contact','boundary','contact','site',data,True)
  if impulse:
   rec('collision','boundary','collision','site',dict(a=P('1','第a体实际ID',integer=True),b=P('1','第b体实际ID',integer=True)),True)
   out('post_velocity','m/s',[2],'碰撞后全局质心速度',atol=1e-6,kind='vector');out('post_omega','rad/s',[1],'碰撞后角速度',atol=1e-6);out('impulse','N.s',[2],'作用于b体的全局接触冲量J',loc='collision',atol=1e-6,kind='vector')
  else:
   out('position','m',[2],'全局质心位置',kind='vector');out('angle','rad',[1],'连续展开的体到全局转角θ，不按2π取模')
   out('velocity','m/s',[2],'全局质心速度',atol=1e-5,kind='vector');out('angular_velocity','rad/s',[1],'逆时针角速度ω',atol=1e-5)
   if kin or inv:
    out('acceleration','m/s2',[2],'全局质心加速度',atol=1e-4,kind='vector');out('angular_acceleration','rad/s2',[1],'逆时针角加速度',atol=1e-4)
   if inv or slug=='prescribed-drive':out('drive_torque','N.m',[1],'驱动对被驱动体施加的逆时针转矩；地面承受反转矩',loc='angle_drive',atol=1e-4)
 M[slug]=cfg

PLANAR='''平面刚体以质心x=(x,y)和连续展开转角θ描述，局部锚点s的全局位置p=x+R(θ)s，R=[[cosθ,−sinθ],[sinθ,cosθ]]。地面ID=-1，x=0、θ=0、速度及加速度均为0；地面锚点直接是全局坐标。a、b不能相同。外力作用于质心，外转矩逆时针为正；没有额外重力、浮力、隐含阻尼或碰撞。

revolute精确约束p_b−p_a=0（x、y两行）；weld再加θ_b−θ_a−angle=0（第三行）。关节理想无摩擦、无质量。各记录按location名的Unicode字典序排列，同一记录内按上述行顺序拼接Φ；角驱动为θ_body−d(t)=0，d=a0+a1τ+a2τ²+a3τ³、τ=t−t0。关节约束与驱动不含罚参数。分支由初始位形连续延拓；不在闭环的另一装配分支跳转。
'''
MECH={
'planar-kinematics':PLANAR+'''本题必须有角驱动，关节加驱动的Φ_q为3n×3n且全程可逆；给定初始位形满足Φ=0。由Φ(q,t)=0确定位形，速度和加速度是该同一连续分支对物理时间的一、二阶导数。不需要质量、外力或动力学初速度。''',
'planar-inverse-dynamics':PLANAR+'''关节加驱动的Φ_q为3n×3n且全程可逆；运动和速度、加速度由Φ=0的初态连续分支唯一确定。质量矩阵M逐体为diag(m,m,I)，外力Q逐体为(Fx,Fy,torque)。逆动力学满足M q̈=Q+Φ_qᵀλ。每条angle_drive的λ即所求驱动转矩；其余λ是关节反力，不要求回传。无额外驱动惯量或传动效率。''',
'planar-multibody':PLANAR+'''本题不允许角驱动或弹性连接。M逐体为diag(m,m,I)，运动满足M q̈=Q+Φ_qᵀλ、Φ=0；λ只表示理想关节约束力。初态q0、q̇0满足位置及速度约束，Φ_q全程满行秩。允许无关节的自由体、多连杆及闭环，不允许切换关节拓扑。''',
'elastic-connectors':PLANAR+'''M逐体为diag(m,m,I)，运动满足M q̈=Q+Qspring+Φ_qᵀλ、Φ=0。弹簧的d=p_b−p_a、l=|d|>0、n=d/l、l̇=n·(ṗ_b−ṗ_a)。弹簧对a的力为[k(l−l0)+c l̇]n，对b反向；分别在锚点产生s_global×F的转矩。这里u×v=u_x v_y−u_y v_x。允许连接地面，不允许零长度或索松弛模型。初态相容，Φ_q全程满行秩；不含角驱动。''',
'prescribed-drive':PLANAR+'''M逐体为diag(m,m,I)，满足M q̈=Q+Φ_qᵀλ、Φ=0。本题必须有角驱动，约束含驱动但行数严格少于3n且Φ_q全程满行秩；至少有一个被动自由度。给定q0、q̇0与Φ=0及Φ_q q̇+Φ_t=0相容。每条angle_drive的λ是驱动对该体的转矩；被动运动同时受惯性和载荷影响，不能将所有坐标按运动学直接指定。''',
'spatial-free-rigid':'''本题由相互独立的三维自由刚体组成，无关节和接触。每体以质心全局坐标x、全局速度v、体坐标角速度ω及体到全局的单位四元数q=(w,xq,yq,zq)表示。使用Hamilton乘法，(w,u)⊗(s,v)=(ws−u·v,wv+su+u×v)，R(q)a由q⊗(0,a)⊗q*的向量部分给出。动力学为m v̇=F、ẋ=v、I ω̇+ω×(Iω)=τ、q̇=0.5 q⊗(0,ω)。I和τ均在随体坐标；F在全局。惯性关于质心，恒定对称正定且主惯量满足三角不等式，初始四元数范数1（接收容差1e-12）。姿态从给定初态连续演化，q和−q不作为可任意切换的输出；不能每帧强制w≥0。没有额外重力或阻尼。''',
'normal-contact':'''平面圆盘以质心x、连续转角θ、速度v、自旋ω、质量m、惯量I及半径r表示，无关节、无地面接触。只对显式列出的不同圆盘对施加接触，未列对不相互作用。候选对可共享圆盘。对a、b取d=x_b−x_a、l=|d|>0、n=d/l、t=(-n_y,n_x)、δ=r_a+r_b−l，u_n=(v_b−v_a)·n。δ>0时N=max(0,kn δ−cn u_n)，δ≤0时N=0；接触对b施加Nn，对a反向，无接触转矩。m v̇=F+ΣFcontact、I ω̇=torque、ẋ=v、θ̇=ω。合外力已含重力。接触是本题指定的有限刚度材料响应，不是刚性非穿透约束；不得自行增加恢复系数或冲量跳跃。''',
'regularized-friction':'''平面圆盘无关节，只对显式候选对相互作用；候选对可共享圆盘，未列对不作用。对a、b取d=x_b−x_a、l=|d|>0、n=d/l、t=(-n_y,n_x)、δ=r_a+r_b−l，接触臂ρ_a=r_a n、ρ_b=−r_b n。平面ω×ρ=(-ωρ_y,ωρ_x)。相对接触速度u=v_b+ω_b×ρ_b−v_a−ω_a×ρ_a，u_n=u·n、u_t=u·t。δ>0时N=max(0,knδ−cn u_n)，否则N=0。作用于b的力为F_b=Nn−μN tanh(u_t/vs)t，对a为−F_b；两体接触转矩分别为ρ_b×F_b和ρ_a×(−F_b)，平面叉积u×v=u_xv_y−u_yv_x。m v̇=F+ΣFcontact、Iω̇=torque+Στcontact、ẋ=v、θ̇=ω。此模型无静摩擦集合、无切向弹性内部状态，不允许以其他摩擦或恢复律替换；没有额外重力。''',
'normal-impact':'''给定若干互不共享圆盘的二体碰撞对；每体恰属于一对，没有地面、关节、持续力或同时耦合多接触。0标记瞬时事件，不作有限时间积分。对a、b取n=(x_b−x_a)/|x_b−x_a|，两体外切且接近u_n=(v_b−v_a)·n<0。接收外切容差为||x_b−x_a|−r_a−r_b|≤1e-10 max(1 m,r_a+r_b)；法向始终由实际输入质心确定，不投影位置。法向冲量j_n=−(1+e)u_n/(1/m_a+1/m_b)，对b的J=j_n n，对a为−J。碰后v_a⁺=v_a−J/m_a、v_b⁺=v_b+J/m_b，自旋不变。半径和质心惯量独立给定，允许非均匀圆盘。''',
'frictional-impact':'''每体恰属于一个互不共享圆盘的碰撞对；无地面、关节、持续力或耦合多接触。0标记瞬时事件。取n=(x_b−x_a)/|x_b−x_a|、t=(-n_y,n_x)、ρ_a=r_a n、ρ_b=−r_b n；ω×ρ=(-ωρ_y,ωρ_x)。碰前u=v_b+ω_b×ρ_b−v_a−ω_a×ρ_a，u_n=u·n<0、u_t=u·t。两体外切，接收容差为||x_b−x_a|−r_a−r_b|≤1e-10 max(1 m,r_a+r_b)，n由实际质心确定，不投影位置。j_n=−(1+e)u_n/(1/m_a+1/m_b)，K_t=1/m_a+1/m_b+r_a²/I_a+r_b²/I_b，j_t=clip(−u_t/K_t,−μj_n,μj_n)。作用于b的J=j_n n+j_t t，对a为−J；v_a⁺=v_a−J/m_a、v_b⁺=v_b+J/m_b，ω_a⁺=ω_a+[ρ_a×(−J)]/I_a、ω_b⁺=ω_b+(ρ_b×J)/I_b。叉积p×f=p_xf_y−p_yf_x。圆盘几何使法切向有效质量解耦；这是本题明确采用的Newton法向恢复与最大耗散切向截断，不推广到任意形状或冲量时程。''',
'modal-flexible':'''每个system是一套固定参考系下的线性柔性模态模型：Mη̈+Cη̇+Kη=f(t)。η每个分量具有长度单位；M、K对称正定，C对称半正定，允许非对角耦合。它们和初态是输入物理事实，不能重新提取、重排、截断或归一化模态。不同system互不作用；给定的是有限维柔性模型，不要求重建连续应力场或证明模态截断误差。积分及误差控制由考生负责。''',
'translating-flexible':'''每个system包含不转动的二维刚性平移载体x和k个柔性模态η，η单位m。动能T=0.5m ẋᵀẋ+ẋᵀBη̇+0.5η̇ᵀMη̇，势能V=0.5ηᵀKη，耗散函数D=0.5η̇ᵀCη̇。m>0，完整质量矩阵A=[[mI₂,B],[Bᵀ,M]]对称正定，K正定、C半正定；输入M也正定。运动为m ẍ+Bη̈=F，Bᵀẍ+Mη̈+Cη̇+Kη=f。质量系数包含全部物理平移惯性，不额外叠加柔性体质量；F和f是分别与x、η共轭的广义外力，不重复计算耦合。不同system互不作用。模型只含平移，不隐含有限转动、陀螺项、模态基更新或应力恢复；这是给定的双向惯性耦合有限维物理模型，不能把Bη̈或Bᵀẍ作为单向已知载荷省略。'''
}

def shape_text(spec):return '['+','.join(map(str,spec['shape']))+']'
def fmt_field(s):return f"{s.get('kind','scalar')} {shape_text(s)}；{s['unit']}；{s['meaning']}"

def contact_slug(slug):return slug in ('normal-contact','regularized-friction')

def clean(text,slug,cfg):
 modal=cfg['family']=='modal';imp=cfg['family']=='impact';kin=slug=='planar-kinematics';contact=contact_slug(slug)
 text=text.replace('至多32个刚体或独立柔性系统、129个位置，每轴至多201帧；柔性题k≤12，其他题不含模态。', '至多32套独立系统、k≤12、129个位置，每轴至多201帧。' if modal else '至多32个刚体、129个位置，每轴至多201帧。')
 text=text.replace('具体体数、质量、惯性、锚点、约束、参数、初态、载荷历史和观测由算例给定，以本题支持集合为准。', '具体系统数、模态矩阵、耦合参数、初态、载荷历史和观测由算例给定。' if modal else '具体体数、位置、速度、质量、惯性、半径及碰撞对由算例给定。' if imp else '具体体数、初态、质量、惯性、载荷历史和观测由算例给定。' if contact or cfg['family']=='spatial' else '具体体数、锚点、关节、驱动和初始位形由算例给定，以本题条件全集为准。' if kin else '具体体数、质量、惯性、锚点、关节、参数、初态、载荷历史和观测由算例给定，以本题条件全集为准。')
 if not modal:text=text.replace('k取mode_count。','')
 if not modal and cfg['family']!='spatial':text=text.replace('components类型采用表中shape，标签依行优先展平固定为c1,c2,...,cL（L是shape各维乘积）。','')
 if modal:text=text.replace('表中角度使用rad及其时间导数；这里rad不是度。','').replace('不能对角度取模、对速度作平移拟合或按量级重新归一化。','不能对速度作平移拟合、重排模态或重新归一化。')
 if imp:text=text.replace('表中角度使用rad及其时间导数；这里rad不是度。','角速度使用rad/s，不是度每秒。').replace('不能对角度取模、对速度作平移拟合或按量级重新归一化。','不能对速度作平移拟合或按量级重新归一化。')
 text=text.replace('material类body／modal_system及loads若列出，均恰一条覆盖整个保留位置，不允许按子集拆分。', 'modal_system及loads均恰一条覆盖systems，不允许按子集拆分。' if modal else 'body恰一条覆盖bodies，不允许按子集拆分。' if kin or imp else 'body及loads均恰一条覆盖bodies，不允许按子集拆分。')
 text=text.replace('身体的实际ID','刚体的实际ID')
 text=text.replace('一个身体参与','一个刚体参与')
 text=text.replace('字段正值要求见表；矩阵对称／正定含义按物理部分。','字段正值要求见表；矩阵对称／正定含义按物理部分。' if modal or cfg['family']=='spatial' else '字段正值要求见表。')
 if slug in ('planar-multibody','elastic-connectors'):
  text=text.replace('角驱动为θ_body−d(t)=0，d=a0+a1τ+a2τ²+a3τ³、τ=t−t0。','')
  text=text.replace('关节约束与驱动不含罚参数。','关节约束不含罚参数。')
 if slug=='elastic-connectors':text=text.replace('无应力长度l0>0；≥0','无应力长度l0>0')
 if contact:
  text=text.replace('collision或contact','contact')
  text=text.replace('所有理想约束必须全程独立，初态满足对应位置／速度约束；这属于数据接收保证，不由结构校验器证明。约束作用力只由Φ_qᵀλ定义，不能另加杆长、摩擦、驱动弹簧或稳定化物理。','')
  for a in ('法向刚度kn>0','正则化速度vs>0'):text=text.replace(a+'；≥0',a)
 if kin:
  text=text.replace('外力作用于质心，外转矩逆时针为正；没有额外重力、浮力、隐含阻尼或碰撞。','本题不求力和转矩，也不含碰撞。')
  text=text.replace('辅助位置仅供下列关节／驱动／连接记录使用','辅助位置仅供下列关节／驱动记录使用')
  text=text.replace('初态满足对应位置／速度约束','初始位形满足位置约束，初速度由驱动唯一确定')
  text=text.replace('仅关节和弹簧允许-1地面','关节允许-1地面')
  text=text.replace('其他轴仅可用于loads引用的场；这些加载轴单帧时必须为[t0]，表示整个[t0,tf]常量，多帧时首末恰为t0、tf，逐分量连续分段线性插值，不外推。','不允许其他时间轴或加载场。')
  text=text.replace('非loads字段均为initial轴单帧常量，不在时间上演化；','所有输入字段均为initial轴单帧常量，不在时间上演化；')
  text=text.replace('不得跳过未请求的中间载荷历史。','驱动由全程多项式定义。')
  text=text.replace('time在loads多帧时为"linear"、其余"constant"','time="constant"')
  text=text.replace('约束作用力只由Φ_qᵀλ定义，不能另加杆长、摩擦、驱动弹簧或稳定化物理。','不求约束反力或驱动转矩，不得增加隐含自由度或改变给定关节。')
 if not kin and not contact and cfg['family']=='planar' and slug!='elastic-connectors':text=text.replace('仅关节和弹簧允许-1地面','仅关节允许-1地面')
 text=text.replace('≥0；≥0','≥0')
 if imp:text=text.replace('collision或contact','collision')
 if cfg['family']!='spatial':text=text.replace('四元数符号拟合、','')
 if modal or imp or cfg['family']=='spatial':text=text.replace('角度模运算、','')
 if contact:text=text.replace('几何／约束适定','接触响应的唯一性')
 if slug=='elastic-connectors':
  text=text.replace('辅助位置仅供下列关节／驱动／连接记录使用','辅助位置仅供下列关节／连接记录使用')
  text=text.replace('a、b、body参数引用','a、b参数引用')
 if slug=='planar-inverse-dynamics':text=text.replace('关节／驱动／连接记录','关节／驱动记录')
 if cfg['family']=='spatial':text=text.replace('不能对角度取模、对速度作平移拟合或按量级重新归一化。','不能对四元数逐帧切换符号、对速度作平移拟合或按量级重新归一化。')
 if slug=='planar-multibody':
  text=text.replace('辅助位置仅供下列关节／驱动／连接记录使用','辅助位置仅供下列关节记录使用')
  text=text.replace('a、b、body参数引用','a、b参数引用')
 if not modal:text=text.replace('矩阵条件数、','')
 if cfg['family']=='spatial' or modal:text=text.replace('最多129个locations；所有ID为CONTRACT规定的非负、严格递增int64，辅助位置ID不跨location配对。','只允许保留位置，不允许其他location；所有ID为非负、严格递增int64。')
 return text

def main():
 ext=ROOT/'qbank/extensions/caeoj_ext/multibody';ext.mkdir(parents=True,exist_ok=True)
 (ext/'models.json').write_text(json.dumps(public_model_catalog(M),ensure_ascii=False,indent=2)+'\n')
 toc=[]
 for sec,title,slugs in SECTIONS:
  sd=CH/sec;sd.mkdir(parents=True,exist_ok=True);sr=[]
  for i,slug in enumerate(slugs,1):
   cfg=M[slug];td=sd/slug;td.mkdir(exist_ok=True);num=sec.split('-')[0]+'.'+str(i);family=cfg['family'];imp=family=='impact';modal=family=='modal';kin=slug=='planar-kinematics';inv=slug=='planar-inverse-dynamics'
   sr.append(f'- {num} [{cfg["name"]}]({slug}/instruction.md)')
   params='\n'.join(f'| `{k}` | `{p["unit"]}` | {p["meaning"]}'+(f'；范围[{p["lower"]},{p["upper"]}]' if p['lower'] is not None and p['upper'] is not None else f'；≥{p["lower"]}' if p['lower'] is not None else '')+' |' for k,p in cfg['parameters'].items())
   recs=[]
   for op,r in cfg['records'].items():
    field_keys={k:s for k,s in r['data'].items() if 'shape' in s};const_keys={k:s for k,s in r['data'].items() if 'shape' not in s}
    recs.append(f'### `{op}`\n\nrole=`{r["role"]}`、variable=`{r["variable"]}`、operator=`{op}`；location='+('`'+r['location']+'`，恰一条记录覆盖该位置全部IDs。' if r['location']!='site' else '任意单ID辅助entities位置，每个辅助location恰好一条记录；其ID只在本location内有意义。')+('必须出现。' if r['required'] else '可出现零条或多条。')+' data恰含下列全部键：\n\n| data键 | 表示及含义 |\n|---|---|\n'+'\n'.join(f'| `{k}` | field引用；{fmt_field(s)} |' for k,s in field_keys.items())+('\n' if field_keys else '')+'\n'.join(f'| `{k}` | 常量`{{"value":数值,"unit":"{s["unit"]}"}}`；{s["meaning"]}'+('；须整数（不接受小数形式或布尔值）' if s['integer'] else '')+(f'；≥{s["lower"]}' if s['lower'] is not None else '')+' |' for k,s in const_keys.items()))
   outs='\n'.join(f'| `{q}` | {fmt_field(s)} | '+('该算子每个辅助位置，全部记录均须被请求' if s['location'] not in ('bodies','systems') else '`'+s['location']+'`全部IDs')+' |' for q,s in cfg['outputs'].items())
   geom='''`meshes={}`、`geometries={}`。locations全部为CONTRACT的entities，记录恰为kind=entities及ids引用；没有coordinates或伪造网格。每个实体的状态或参数保留自己的ID，物理位置来自输入场及条件参数。实际ID可不连续，不能用数组行号代替ID。'''
   base='systems' if modal else 'bodies'
   geom+=f'保留位置名`{base}`，N=1..32。'+('每个ID是一套独立系统。' if modal else '每个ID是一个可动刚体，不含地面。')
   if family=='planar' and not contact_slug(slug):geom+='辅助位置仅供下列关节／驱动／连接记录使用，每个含一个ID，不得与bodies同名；每个辅助位置必须被且仅被一条记录使用。a、b、body参数引用bodies中的实际ID；仅关节和弹簧允许-1地面，且不得两端均为地面。同一无序体对允许不同锚点连接，但不得有冗余约束。'
   if family=='impact' or slug in ('normal-contact','regularized-friction'):geom+='辅助位置每个含一个ID，恰被一条collision或contact记录使用；a、b均是bodies中的实际ID，且a≠b，同一无序体对不得重复。'+('所有bodies被互不共享的碰撞对恰好覆盖。' if imp else '只计算显式候选对，允许一个身体参与多对。')
   timing='''所有time_axes恰为`event`，值为单帧[0.0]；输入场和输出都引用event，初速度是事件前左极限，输出是事件后右极限。输入field sampling恰为{"space":"uniform","time":"constant","extrapolation":"forbid"}；不作时间插值。''' if imp else '''必须有名为`initial`的单帧轴[t0]和名为`response`的输出轴，response全在[t0,tf]内、至多201帧且非空。其他轴仅可用于loads引用的场；这些加载轴单帧时必须为[t0]，表示整个[t0,tf]常量，多帧时首末恰为t0、tf，逐分量连续分段线性插值，不外推。非loads字段均为initial轴单帧常量，不在时间上演化；字段名带0表示真实初态。输出时刻不是内部积分步；不得跳过未请求的中间载荷历史。所有输入field显式sampling：space="uniform"，time在loads多帧时为"linear"、其余"constant"，extrapolation="forbid"。uniform表示每个独立ID自身的离散参数，不在不同ID间作空间重建、平滑或平均。'''
   labels='''所有表内字段均float64；kind=scalar固定shape=[1]、components=["value"]；vector使用全局前D分量及["x","y","z"]的前D项；components类型采用表中shape，标签依行优先展平固定为c1,c2,...,cL（L是shape各维乘积）。k取mode_count。所有数组为[T,N,*shape]，保留时间、ID、分量轴。表中角度使用rad及其时间导数；这里rad不是度。字段对象名和array key均自由，quantity对输入必须恰等于引用它的data键名，单位／kind／shape严格按表。字段必须和条件同location，不允许常量简写替代field，即使均匀亦然。输入fields恰为被条件引用的字段；同一field可复用，但不能靠同shape跨ID错配。'''
   extra=''
   if family=='planar':extra+='所有理想约束必须全程独立，初态满足对应位置／速度约束；这属于数据接收保证，不由结构校验器证明。约束作用力只由Φ_qᵀλ定义，不能另加杆长、摩擦、驱动弹簧或稳定化物理。'
   if slug in ('normal-contact','regularized-friction'):extra+='初态及全程须保持l>0，最大重叠不超过较小半径的5%；可从已接触的压缩状态开始，不要求初始δ=0。输出仅位置及速度，不请求接触切换时不唯一的加速度。'
   extra+='正式数据须核验相容性、唯一连续分支、所请求观测存在、无有限时间发散，并以独立基准证实预算内能达到目标。几何／约束适定、矩阵条件数、精度及预算目前没有正式数值验证；合法格式不能替代这些证据。'
   (td/'DATA.md').write_text(f'# {slug} 数据契约\n\n入口为UTF-8 problem.json及其data_file指定的扁平HDF5，路径相对清单解释。考生仅需本题instruction、DATA和通用CONTRACT。`spatial_dimension={cfg["dimension"]}`；`physics`恰含model、parameters，model固定为`multibody-{slug}-v1`；task可省略，出现时须为`{slug}`。不允许profile、analysis、materials、contract_version。无未列键、条件或隐藏默认值。\n\n## 物理与方法边界\n\n'+MECH[slug]+'\n\n## 全局参数\n\n'+('parameters恰为下表全部项，各项为带单位有限标量的value/unit对象，布尔值不能作数值。\n\n| 参数名 | 单位 | 含义及范围 |\n|---|---|---|\n'+params if params else '`parameters={}`，不含全局参数。')+'\n\n## 位置与身份\n\n'+geom+'最多129个locations；所有ID为CONTRACT规定的非负、严格递增int64，辅助位置ID不跨location配对。\n\n## 时间和字段\n\n'+timing+'\n\n'+labels+'\n\n## 条件全集\n\n'+'\n\n'.join(recs)+'\n\nmaterial类body／modal_system及loads若列出，均恰一条覆盖整个保留位置，不允许按子集拆分。未列出的算子一律不允许；字段正值要求见表；矩阵对称／正定含义按物理部分。常量参数不能使用field替代。\n\n## 输出\n\noutputs逻辑名及array key自由；每个quantity必须出现，允许重复请求但每次须覆盖对应完整位置。输出轴恰为'+('event' if imp else 'response')+'；均float64、value_kind=point，不含sampling。\n\n| quantity | 分量、单位与含义 | 位置 |\n|---|---|---|\n'+outs+'\n\n结果HDF5仅含输出arrays、所需IDs及时间轴，不重复坐标或输入字段；严格遵守输入行序。不能对角度取模、对速度作平移拟合或按量级重新归一化。\n\n## 接收边界\n\n'+extra+'\n每个输入轴至多201帧，输入字段与输出字段各自总分量数至多2000000；不是对HDF5压缩后字节数的约束。\n')
   atols='\n'.join(f'| `{q}` | {s["atol"]} | `{s["unit"]}` |' for q,s in cfg['outputs'].items())
   (td/'instruction.md').write_text(f'# {num} {cfg["name"]}\n\n实现覆盖本题公开问题族的可复用求解器，冻结后处理多个未见算例。'+MECH[slug]+'\n\n具体体数、质量、惯性、锚点、约束、参数、初态、载荷历史和观测由算例给定，以本题支持集合为准。考生负责相容的机械建模、坐标选择、求解与误差控制；给定的物理响应不可替换。算法、语言、软件和内部步长自由；覆盖整个契约的解析或降阶方法有效，不要求复现参考离散。阅读[本题DATA](DATA.md)及[通用协议](../../../../docs/CONTRACT.md)，无需其他资料补足题意。\n\n## 规模与运行\n\n'+f'至多32个刚体或独立柔性系统、129个位置，每轴至多201帧；柔性题k≤12，其他题不含模态。输入／输出字段分别至多2000000个分量。每例Linux AMD64，{cfg["timeout"]}秒墙钟（含启动和读写）、4CPU、8192MB、0GPU；逐例无网络。入口`python solve.py --input /path/problem.json --output /path/result.h5`，0退出并写出完整结果。依赖提前准备，可用Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5；不强制Python计算。无独立输出字节限额。生成求解器3600秒、构建环境1800秒。\n\n当前规模、预算与容差是待正式数据校准的设计目标。数据方须以独立基准证明预算内达到精度，排除奇异、病态至不可在预算内求解或无唯一观测的输入组合。\n\n## 评分\n\n每个有效例正常退出、结构合法且所有输出quantity全部逐值满足`|结果−参考| ≤ atol(quantity)+0.01|参考|`得1分，否则0分。比较覆盖所有时刻、ID和分量，阈值等号接受；无去均值、角度模运算、四元数符号拟合、重排或少数超限豁免。IDs／时间、shape、dtype及有限值严格遵守CONTRACT。\n\n| quantity | atol | 单位 |\n|---|---|---|\n'+atols+'\n\n本题成绩为通过有效例数／有效例数。输入、配置或参考错误是基础设施错误，不算考生失败；无有效例时不产生成绩。正式数据、独立参考、校准与评测发布留后；契约工具验证不是机械模型或数值解正确性的证据。\n')
   for doc in ('instruction.md','DATA.md'):
    path=td/doc;path.write_text(clean(path.read_text(),slug,cfg))
   policy=dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=.01)) for q,s in cfg['outputs'].items()})
   (td/'author').mkdir(parents=True,exist_ok=True)
   (td/'author/grading-template.json').write_text(json.dumps(policy,indent=2)+'\n')
   (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=cfg['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
   (td/'harbor').mkdir(exist_ok=True);(td/'harbor/requirements.txt').write_text('scipy==1.18.1\n');(td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 4\nmemory_mb = 8192\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
  (sd/'README.md').write_text(f'# {sec.split("-")[0]} {title}\n\n'+'\n'.join(sr)+'\n')
  toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
 (CH/'README.md').write_text('# 第四章 多体系统力学分析\n\n6节12题；每题instruction与DATA自包含，结合通用CONTRACT即可实现。正式数据、参考和评测发布留后。\n\n'+'\n'.join(toc)+'\n\n维护入口：[章规划](../design/chapter-04-multibody-mechanics.md)、[逐题清单](../design/chapter-04-task-plan.md)、[进度与证据](../design/reviews/chapter-04-progress.md)。\n')
if __name__=='__main__':main()
