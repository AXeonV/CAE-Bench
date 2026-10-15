"""Expand independent acoustic contracts and configurations; no case/reference maker."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[3];CH=ROOT/'qbank/06-acoustics'
SECTIONS=[('6.1-propagation','有界介质声传播',['acoustic-transient','acoustic-harmonic']),('6.2-exterior','外域辐射与散射',['surface-radiation','rigid-scattering']),('6.3-absorption','等效介质吸收',['equivalent-fluid']),('6.4-thermoviscous','热黏声学',['thermoviscous-acoustics']),('6.5-aeroacoustics','气动声学',['uniform-flow-acoustics','lighthill-radiation']),('6.6-vibroacoustics','振声响应与耦合',['resonator-wall','modal-vibroacoustics'])]
NAMES=['线性声学瞬态传播','非均匀介质单频声响应','给定表面振速的声辐射','刚性体平面波散射','被动等效流体吸声','理想气体热黏单频响应','均匀平均流中的声扰动','给定Lighthill应力的声辐射','局部共振吸声壁的瞬态响应','给定结构模态的单频振声耦合']
def S(u,m,**kw):return dict(unit=u,meaning=m,kind='scalar',shape=[1],**kw)
def V(u,m):return dict(unit=u,meaning=m,kind='vector',shape=[3])
def C(sh,u,m,**kw):return dict(unit=u,meaning=m,kind='components',shape=sh,**kw)
def Z(u,m,**kw):return C([2],u,m,**kw)
def ZV(u,m):return C([3,2],u,m)
def P(u,m,**kw):return dict(unit=u,meaning=m,**kw)
M={}
for slug,name in zip([s for _,_,ss in SECTIONS for s in ss],NAMES):
 transient=slug in ('acoustic-transient','uniform-flow-acoustics','resonator-wall');surface=slug in ('surface-radiation','rigid-scattering');source=slug=='lighthill-radiation';thermo=slug=='thermoviscous-acoustics';modal=slug=='modal-vibroacoustics'
 c=dict(name=name,family='surface' if surface else 'source' if source else 'bounded',transient=transient,parameters={},records={},outputs={},timeout=1500 if thermo or modal else 1200 if surface else 900,limits=dict(cells=3000,nodes=9000,surface_faces=800,receivers=128,frames=101,components=3000000))
 if transient:c['parameters'].update(start_time=P('s','物理初始时刻t0'),end_time=P('s','末时刻tf，严格大于t0'))
 else:c['parameters']['frequency']=P('Hz','单频f>0，ω=2πf',positive=True)
 if surface or source or thermo or slug=='uniform-flow-acoustics':
  if not source:c['parameters']['density']=P('kg/m3','均匀背景密度ρ>0',positive=True)
  if not thermo:c['parameters']['sound_speed']=P('m/s','均匀声速c>0',positive=True)
 if thermo:
  c['parameters'].update(temperature=P('K','均匀背景绝对温度T0>0',positive=True),gas_constant=P('J/(kg.K)','比气体常数R>0',positive=True),gamma=P('1','比热比γ>1',lower_exclusive=1),viscosity=P('Pa.s','动力黏度μ>0',positive=True),bulk_viscosity=P('Pa.s','体黏度ζ≥0',lower=0),conductivity=P('W/(m.K)','热导率κ>0',positive=True))
 if slug=='rigid-scattering':
  for key in ('x','y','z'):c['parameters']['direction_'+key]=P('1','入射传播单位方向d的'+key+'分量');c['parameters']['reference_'+key]=P('m','入射相位参考点x_ref的'+key+'分量')
  c['parameters'].update(amplitude_real=P('Pa','入射压力复振幅A实部'),amplitude_imag=P('Pa','入射压力复振幅A虚部'))
 if slug=='uniform-flow-acoustics':
  for key in ('x','y','z'):c['parameters']['mean_'+key]=P('m/s','均匀平均速度V0的'+key+'分量；|V0|/c<0.5')
 if modal:c['parameters']['mode_count']=P('1','模态数m，整数1..8',integer=True,lower=1,upper=8)
 def rec(op,role,var,where,data,required=True,static=False):c['records'][op]=dict(role=role,variable=var,where=where,data=data,required=required,static=static)
 def out(q,s,where='cells',atol=1e-5,rtol=.01):c['outputs'][q]=dict(s,where=where,atol=atol,rtol=rtol)
 if surface:
  if slug=='surface-radiation':rec('surface_velocity','boundary','normal_velocity','surface',dict(value=Z('m/s','固体向外法向的表面振速W')))
  else:rec('rigid','boundary','normal_velocity','surface',dict(state={'option':'stationary','meaning':'静止刚性体，总场法向速度为0'}))
  if slug=='rigid-scattering':out('scattered_pressure',Z('Pa','散射压力Psc'),'receivers')
  out('pressure',Z('Pa','辐射声压P' if slug=='surface-radiation' else '总声压Pinc+Psc'),'receivers')
 elif source:
  rec('lighthill_tensor','source','stress','cells',dict(value=C([3,3,2],'Pa','对称Lighthill应力Tij，完整张量；实虚分别对称')))
  out('pressure',Z('Pa','自由空间声压P'),'receivers')
 elif thermo:
  rec('force','source','force','cells',dict(value=ZV('N/m3','线性体积动量源F')))
  rec('heat','source','heat','cells',dict(value=Z('W/m3','线性体积加热源Q')))
  rec('wall_velocity','boundary','velocity','boundary_nodes',dict(value=ZV('m/s','外边界全部速度分量Vw，含切向与法向')))
  out('pressure',Z('Pa','声压P'))
  out('velocity',ZV('m/s','粒子速度U'),atol=1e-7)
  out('temperature_perturbation',Z('K','温度扰动Θ，不是绝对温度'),atol=1e-7)
 else:
  if slug!='uniform-flow-acoustics':
   material=dict(density=S('kg/m3','背景密度ρ>0',positive=True),sound_speed=S('m/s','声速c>0',positive=True))
   if slug=='equivalent-fluid':material=dict(density=Z('kg/m3','等效复密度ρ，Reρ>0、Imρ≤0'),compressibility=Z('1/Pa','等效复压缩率β，Reβ>0、Imβ≤0'))
   rec('material','material','acoustic','cells',material,static=True)
  rec('volume_source','source','dilatation','cells',dict(value=S('1/s','体积膨胀率源q') if transient else Z('1/s','体积膨胀率源q')))
  if transient:
   rec('initial_pressure','initial','pressure','domain',dict(value=S('Pa','初始声压p0')),static=True)
   rec('initial_velocity','initial','velocity','domain',dict(value=V('m/s','初始粒子速度u0')),static=True)
  if slug=='uniform-flow-acoustics':rec('periodic','boundary','acoustic','facets',dict(partner={'location':True,'meaning':'对应坐标最大面的位置；本侧为最小面'}))
  else:
   rec('pressure','boundary','pressure','nodes',dict(value=S('Pa','给定声压pb') if transient else Z('Pa','给定声压Pb')),False)
   rec('normal_velocity','boundary','normal_velocity','facets',dict(value=S('m/s','向域外的法向粒子速度') if transient else Z('m/s','向域外的法向粒子速度')),False)
   rec('impedance','boundary','normal_velocity','facets',dict(impedance=S('Pa.s/m','实阻抗R>0',positive=True,static=True) if transient else Z('Pa.s/m','复阻抗Z，ReZ≥0且|Z|>0'),drive=S('Pa','压力驱动pd') if transient else Z('Pa','压力驱动Pd')),False)
  if slug=='resonator-wall':
   rec('resonator','boundary','normal_velocity','facets',dict(mass=S('kg/m2','壁面面密度ms>0',positive=True,static=True),damping=S('Pa.s/m','壁面阻尼rs≥0',lower=0,static=True),stiffness=S('Pa/m','壁面刚度ks>0',positive=True,static=True),displacement0=S('m','初始向外位移ξ0',static=True),velocity0=S('m/s','初始向外速度w0',static=True),back_pressure=S('Pa','壁背压力扰动pb(t)')))
   out('wall_displacement',S('m','向外壁位移ξ'),'resonator',atol=1e-7)
   out('wall_velocity',S('m/s','向外壁速度∂tξ'),'resonator',atol=1e-7)
  if modal:
   rec('structure','material','structure','structure',dict(mass=C(['m','m'],'kg','对称正定模态质量M'),damping=C(['m','m'],'kg/s','对称半正定模态阻尼C'),stiffness=C(['m','m'],'N/m','对称正定模态刚度K'),force=C(['m',2],'N','外部模态力Fext；每模态实虚相邻')))
   rec('modal_wall','boundary','normal_velocity','facets',dict(shape=C(['m'],'1','实值法向位移形状φ，各面分片常数；正值沿流体外法向')))
   out('modal_displacement',C(['m',2],'m','模态位移η的复振幅，按输入模态顺序'),'structure',atol=1e-7)
  out('pressure',S('Pa','声压p') if transient else Z('Pa','复声压P'))
  out('velocity',V('m/s','粒子速度u') if transient else ZV('m/s','复粒子速度U'),atol=1e-7)
  if slug=='equivalent-fluid':out('dissipation',S('W/m3','体积耗散功率密度D的平均'),atol=1e-7)
 M[slug]=c
HARM='''相量约定为真实扰动Re(A exp(+iωt))，ω=2πf>0。声压是相对背景的扰动，不是总绝对压力；单频输入和输出均为复振幅，不是RMS或仅模长。'''
BASEH=HARM+'''有界静止非均匀无黏介质，体积模量K=ρc²。iωP/K+div U=q，iωρU+∇P=0。材料参数逐四面体常数；共享节点的内部面压力连续、法向速度连续。未声明外面U·n=0，n是流体域向外法向；没有额外压力基准或切向无滑移条件。'''
BASET='''有界静止非均匀线性介质，K=ρc²。∂tp/K+div u=q，ρ∂tu+∇p=0。材料参数逐四面体常数；共享节点的内部面压力连续、法向速度连续。给定物理p、u初态；不作额外声／涡投影，初速度中无源静态分量也保留。未声明外面u·n=0，n是流体域向外法向；不额外固定切向速度或每帧减去平均压力。'''
EXTERIOR=HARM+'''流体为均匀无穷外域，背景ρ、c给定，k=ω/c。障碍是单个封闭无自交、可定向、连通的多面体；Gmsh三角节点顺序规定固体向外法向ns（朝流体），与流体外域的边界向外法向相反。外域(∆+k²)P=0，出射条件r(∂rP+ikP)→0，基函数exp(−ikr)/(4πr)。不以有限截断或某个PML的结果定义真值；边界积分伪共振是数值方法责任。'''
PHYS={
'acoustic-transient':BASET,
'acoustic-harmonic':BASEH+'''数据须排除未消除的物理共振不唯一，不能由任意指定声压零点选择答案。''',
'surface-radiation':EXTERIOR+'''全部固体表面U·ns=W，等价∂nsP=−iωρW；W按实际三角面常值给定。输出真实外部接收点的辐射声压，不含入射场。''',
'rigid-scattering':EXTERIOR+'''入射场Pinc=A exp[−ik d·(x−xref)]，A=amplitude_real+i amplitude_imag，单位方向d由参数给出，Uinc=d Pinc/(ρc)。求出射散射场Psc，使总法向速度(Uinc+Usc)·ns=0，等价∂nsPsc=ik(ns·d)Pinc。输出Psc与Pinc+Psc；总场不满足仅出射条件，出射条件只施于散射场。''',
'equivalent-fluid':HARM+'''有界等效流体按单频给定复密度ρ和复压缩率β，iωβP+div U=q，iωρU+∇P=0。Reρ、Reβ严格正，Imρ、Imβ非正，符号对应exp(+iωt)被动耗散。共享节点内部面P与Un连续。D=−ω[Imρ |U|²+Imβ |P|²]/2，单位W/m3；输出先逐点计算D再体积平均，不能把平均P／U代入。无弹性多孔骨架自由度，不从单频物性推断跨频因果材料模型。未声明外面Un=0，其他边界同DATA明确的声学压力／速度／阻抗关系；数据须排除未消除的物理共振。''',
 'thermoviscous-acoustics':HARM+'''均匀静止理想气体，p0=ρ R T0，cp=γR/(γ−1)。未知为P、U、温度扰动Θ，满足iω(P/p0−Θ/T0)+div U=0；iωρU=−∇P+μ∆U+(ζ+μ/3)∇div U+F；iω(ρcpΘ−P)=κ∆Θ+Q。μ是剪切动力黏度，ζ是体黏度，未把ζ重复加上Stokes项。全部外边界给定完整U=Vw并固定Θ=0（等温扰动边界），不再指定压力或热通量。求解线性黏性／热边界层及体损失；不将Θ当作T0或擅用等熵降阶模型。''',
 'uniform-flow-acoustics':'''均匀背景ρ、c、V0，|V0|/c<0.5；固定轴对齐长方体上的三方向普通周期问题，不是Bloch相位周期。Dt=∂t+V0·∇，K=ρc²，Dtp/K+div u=q，ρDtu+∇p=0。给定p、u初态与体积源；各相对面p和全部u分量逐点同值，加载源按周期延拓，不附加入流或阻抗。只评价给定背景下的小扰动输运，不重求平均流或湍流，不声称完整流致噪声预测。''',
 'lighthill-radiation':HARM+'''均匀静止无穷介质，k=ω/c，给定紧支撑对称应力张量Tij，单位Pa；源域外T=0。全空间(∆+k²)P=−∂i∂jTij（重复指标全求和），P出射。等价定义P(x)=∫source Σij Tij(y) ∂xi∂xj G(x−y) dV_y，G=exp(−ik|x−y|)/(4π|x−y|)。T在源四面体上分片常数，双散度按分布意义解释；不能把单元内导数为0当作无源，也不能漏掉跳跃面的分布贡献。输出源域外真实接收点压力。输入是已给声类比张量，不需要从速度场猜声源或重做CFD；不包括背景流对传播的折射或声反馈。''',
 'resonator-wall':BASET+'''resonator表面有局部反应壁：u·n=∂tξ，ms∂ttξ+rs∂tξ+ksξ=p−pb。ξ向流体域外为正，ms为单位面积质量、rs为局部阻尼、ks为单位面积位移刚度，pb为背压扰动；压力正值推动壁向外。初始ξ、∂tξ显式给出并与声学初态相容。每个表面点独立局部振子，没有沿面弹性耦合；即使参数和初态按面常值给定，后续ξ也由局部压力迹决定，不强制每面刚性均动。保持壁储能与声场双向反馈，不以无记忆常阻抗替代。''',
 'modal-vibroacoustics':BASEH+'''唯一给定模态结构有m个长度坐标η、实质量M／阻尼C／刚度K_s，M与K_s正定、C半正定。modal_wall上Un=iωΣj φjηj，φ为实值面片常数，正向沿流体外法向。(−ω²M+iωC+K_s)η=Fext+∫wall φ P dS；模态声压力以正声压推动向外为正，与边界速度同一方向。所有modal_wall记录共同耦合同一个structure实体，积分是其并集的实际面积积分。m个形状在该并集上独立，不重排／重新归一化模态、不重复叠加附加质量。给定降阶模型不含模态提取、应力恢复或更新几何；数据排除未消除的耦合物理共振。'''
}

def shape(s,p):return [int(p['mode_count']) if n=='m' else n for n in s['shape']]
def labels(s,p):
 sh=shape(s,p);kind=s['kind']
 if kind=='scalar':return ['value']
 if kind=='vector':return ['x','y','z']
 return ['c'+str(i+1) for i in range(math.prod(sh))]
def description(s):
 if 'option' in s:return s['meaning']+'；精确为`{"option":"'+s['option']+'"}`'
 if 'location' in s:return s['meaning']+'；仅`{"location":"位置名"}`引用'
 return f"{s['kind']} {s['shape']}；`{s['unit']}`；{s['meaning']}"

def main():
 ext=ROOT/'qbank/extensions/caeoj_ext/acoustic';ext.mkdir(parents=True,exist_ok=True);(ext/'models.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n');toc=[]
 for sec,title,slugs in SECTIONS:
  sd=CH/sec;sd.mkdir(parents=True,exist_ok=True);links=[]
  for j,slug in enumerate(slugs,1):
   c=M[slug];td=sd/slug;td.mkdir(exist_ok=True);tr=c['transient'];family=c['family'];modal=slug=='modal-vibroacoustics';thermo=slug=='thermoviscous-acoustics';num=sec.split('-')[0]+'.'+str(j);axis='response' if tr else 'harmonic'
   links.append(f'- {num} [{c["name"]}]({slug}/instruction.md)')
   geo='''meshes恰含main，MSH4.1 ASCII；可选geometries只保留来源，求解几何以网格为准。spatial_dimension=3，坐标为m。tag是身份不是行号，Physical Group若声明必须与location的IDs精确相符；组名不定义边界。'''
   if family=='surface':
    geo+='''main仅含非退化一阶三角形type2，不导出边／点／体单元。surface为main全部二维三角单元location；domain为全部所用节点。表面单个连通闭壳、每条边恰有两相邻面且定向相反，按节点顺序的总有向体积为正（ns固体向外）；没有未用节点、自交、开口或多重壳。receivers为独立points，含真实外部接收点坐标与自己的非负IDs，允许位置集合中有多个接收点但不得在内部或表面。每点距表面至少1e−8倍障碍包围盒对角线。只允许domain、surface、receivers三个location；输出引用receivers全部IDs。'''
   else:
    geo+='''main只含非退化一阶四面体type4及全部外边界一阶三角形type2，不导出更低维单元。无未用节点、悬挂节点、重叠体或非流形公共面；每个外面导出一次，域通过完整公共面连通。保留domain为全部所用节点、cells为全部体单元；其他mesh位置只允许main节点子集、体单元子集或外面单元子集。'''
    if family=='source':geo+='''receivers为独立points真实接收点坐标，须在源域外且距源域表面至少1e−8倍包围盒对角线；输出引用全部receivers。源域仅表示T的支撑及积分位置，不施加声学边界或求域内压力。除receivers外不得使用points、entities或aggregate。'''
    else:
     geo+='''场的实体身份固定在参考几何上，内部升阶／改网格自由。外法向n从唯一相邻体指向域外，不由面节点存储顺序推断。压力边界用节点集，精确作用于全部顶点均在该集的所有完整外面；节点集须恰为这些作用面顶点之并，不允许孤立点／棱约束。多条压力记录不得共享节点。其他边界按实际面IDs给定，任何完整外面至多一种边界，不能依列表顺序覆盖；不同类别仅可在棱相交。'''
     if modal:geo+='''额外允许且必须有structure location，kind=entities、单个非负ID；它表示唯一模态结构，不是空间点或假区域聚合。'''
     else:geo+='''不允许points、entities或aggregate位置。'''
     if slug=='uniform-flow-acoustics':geo+='''本题无压力／阻抗记录，只允许三对普通周期面；main必须完整填充一个轴对齐长方体，每条periodic的本侧是一个坐标最小面，partner是同轴最大面，两者顶点／三角剖分平移一一对应。平移量由包围盒该轴长度确定，其他分量为0；三对覆盖全部外面且互不复用。'''
   if thermo or slug=='uniform-flow-acoustics':
    start=geo.index('压力边界用节点集');end=geo.index('不允许points')
    geo=geo[:start]+geo[end:]
   time='''time_axes恰为harmonic单帧[0.0]；全部输入和输出只引用harmonic。0是相量存储标记，不是物理初态、相位未知量或额外频率轴；每例只有parameters.frequency这一物理频率。所有输入sampling.time=constant，不接受物理历史或输出多帧。''' if not tr else '''time_axes必须含initial单帧[t0]及response非空请求时刻，response全部在[t0,tf]内；每个轴至多101帧。材料、初态及各参数注明static的field只引用initial。其他加载单帧须在t0，表示整个[t0,tf]常量；多帧须首末恰为t0、tf，逐分量连续分段线性插值，sampling.time=linear；不外推。不允许initial、response之外未被加载引用的轴；输出时刻不是内部求解步，不能跳过未请求的历史。所有初边值在t0相容，初态不代表数值初猜。'''
   fields='''fields恰为被条件引用的字段；条件field引用逻辑对象名，该对象的array才是HDF5 key，两者名称自由。输入quantity固定等于data键名；唯一例外是value，其quantity等于该条条件variable（下表明确）。field须与条件同location，不能按相同长度借别处数据。所有field为float64，数组[T,N,*component_shape]，不省略轴。scalar固定shape=[1]、components=["value"]；vector固定[3]及x/y/z。components按表shape行优先展平命名c1..cL（L为shape各维乘积）。复标量[2]依次实、虚，复向量[3,2]为x实虚、y实虚、z实虚；不使用复数dtype或幅相数组。'''
   if modal:fields+='m取mode_count；模态矩阵[m,m]按输入模态顺序行优先，模态复量[m,2]每模态实虚相邻，shape[m]是m个实值形状系数。'
   if family=='source':fields=fields.replace('，复向量[3,2]为x实虚、y实虚、z实虚','');fields+='源张量[3,3,2]按ij行优先、最内层实虚，包含全部9个张量项；各实虚部分均对称。'
   fields+='''输入field显式sampling，extrapolation=forbid；节点space=piecewise_linear，表示沿一阶参考网格的唯一P1重建（边界节点在对应面上重建）；单元space=piecewise_constant，为每个实体常值；entities的space=uniform，为离散模态参数，不作空间重建。value_kind节点／entities为point、元素为average，不接受输入integral。单帧或static的sampling.time=constant，加载多帧按时间段线性；先空间再时间重建。'''
   fields+='''scalar data可以用同单位有限数值的value/unit常量（全位置、全程常量），或显式field；components／vector仅field，不允许内联数组。表中static只允许常量或静态轴field。位置引用和option只能按表精确形式。所有数据无布尔数值、隐藏默认值或未列选项。'''
   if not modal:fields=fields.replace('；entities的space=uniform，为离散模态参数，不作空间重建','').replace('节点／entities为point','节点为point')
   if not tr:fields=fields.replace('单帧或static的sampling.time=constant，加载多帧按时间段线性；先空间再时间重建。','sampling.time固定constant；只作上述空间重建，不定义额外时间演化。')
   if family in ('surface','source'):
    fields=fields.replace('scalar固定shape=[1]、components=["value"]；vector固定[3]及x/y/z。','')
    fields=fields.replace('节点space=piecewise_linear，表示沿一阶参考网格的唯一P1重建（边界节点在对应面上重建）；','')
    fields=fields.replace('value_kind节点为point、元素为average','输入value_kind元素为average')
    fields=fields.replace('scalar data可以用同单位有限数值的value/unit常量（全位置、全程常量），或显式field；components／vector仅field，不允许内联数组。','本题复量输入仅允许显式field，不允许内联数组或常量替代。')
   if slug=='rigid-scattering':
    fields='本题fields必须为空；入射振幅、方向与相位参考点仅由全局参数给定，rigid只含规定option。输出为float64复标量components，shape=[2]、components=["c1","c2"]，依次为实部和虚部，保留[T,N,2]全部轴；不使用复数dtype或幅相表示。输入HDF5只含位置IDs、receivers坐标与harmonic时间数组。方向范数须满足|norm(d)−1|≤1e−12，不由工具归一化。'
   if tr:
    fields=fields.replace('复标量[2]依次实、虚，复向量[3,2]为x实虚、y实虚、z实虚；不使用复数dtype或幅相数组。','')
    fields=fields.replace('components按表shape行优先展平命名c1..cL（L为shape各维乘积）。','')
   if not any(r['static'] or any(s.get('static') for s in r['data'].values()) for r in c['records'].values()):
    fields=fields.replace('表中static只允许常量或静态轴field。','')
   records=[]
   wheres=dict(cells='cells完整体域',domain='domain全部节点',facets='外边界三角单元location',nodes='上述闭包规则的外边界节点location',surface='surface全部三角面',structure='structure唯一实体',boundary_nodes='全部外边界节点且恰一条记录')
   for op,r in c['records'].items():
    records.append(f'### `{op}`\n\nrole=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`；location为{wheres[r["where"]]}。'+('必须出现。' if r['required'] else '可不出现。')+('该算子恰一条覆盖表定完整位置。' if r['where'] in ('cells','domain','surface','structure','boundary_nodes') else ('可多条，作用面及partner不能重复。' if op=='periodic' else '可多条，作用面不能重复。'))+'data恰含下列全部键：\n\n| data键 | 类型、单位和含义 |\n|---|---|\n'+'\n'.join(f'| `{key}` | {description(s)}'+('；static' if r['static'] or s.get('static') else '')+' |' for key,s in r['data'].items()))
   bc=''
   if family=='bounded' and not thermo and slug!='uniform-flow-acoustics':
    bc='''pressure算子规定p=pb（单频P=Pb），normal_velocity规定u·n（单频U·n）等于value；impedance规定p=R u·n+drive（单频P=Z U·n+drive）。瞬态R为严格正的实常参数，可逐面变化；单频Z满足ReZ≥0且|Z|>0。驱动正负和法向均按向流体外。未声明外面法向速度0，不叠加切向速度或额外压力条件。'''
    if not tr:bc=bc.replace('p=pb（单频P=Pb）','P=Pb').replace('u·n（单频U·n）','U·n').replace('p=R u·n+drive（单频P=Z U·n+drive）','P=Z U·n+drive').replace('瞬态R为严格正的实常参数，可逐面变化；','')
    else:bc=bc.replace('（单频P=Pb）','').replace('（单频U·n）','').replace('（单频P=Z U·n+drive）','').replace('单频Z满足ReZ≥0且|Z|>0。','')
   params='\n'.join(f'| `{key}` | `{s["unit"]}` | {s["meaning"]} |' for key,s in c['parameters'].items())
   outs='\n'.join(f'| `{q}` | {description(s)} | '+('receivers全部点，point' if s['where']=='receivers' else 'structure唯一实体，point' if s['where']=='structure' else '每条'+s['where']+'完整面location，average；每条均需请求' if s['where']!='cells' else 'cells或其非空体单元子集，average')+' |' for q,s in c['outputs'].items())
   observation='''体单元平均按实际体积积分再除体积；壁面平均按实际三角面积积分再除面积，不是中心值或节点算术均值。非线性耗散须逐点计算后积分。''' if family=='bounded' else '''receivers输出是其真实坐标处点值，不是区域积分或任意角度函数；没有隐含远场近似。'''
   if slug!='equivalent-fluid':observation=observation.replace('非线性耗散须逐点计算后积分。','')
   if slug!='resonator-wall':observation=observation.replace('；壁面平均按实际三角面积积分再除面积','')
   size='外表面至多800三角面、9000节点，至多128接收点。' if family=='surface' else '至多3000四面体、9000节点'+('、128接收点。' if family=='source' else '。')
   admission='''正式数据须核验几何无自交／重叠、材料适用、小扰动线性范围、初边值相容、所请求点值／平均存在及物理解可确定，并用独立参考证明预算内精度；校验器不证明这些性质。不得以格式合法、求解器低残差或与同一离散一致替代声学正确性。'''
   (td/'DATA.md').write_text(f'# {slug} 数据契约\n\n入口problem.json及其data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model固定`acoustic-{slug}-v1`，task可省略，出现须为`{slug}`。禁止contract_version、profile、analysis、materials混用；不接受本题未列字段、模型或条件组合。\n\n## 物理定义\n\n'+PHYS[slug]+'\n\n## 全局参数\n\nparameters恰为下表全部项，各项只有value和unit，有限实数且布尔值不能作数值，整数须JSON整数。\n\n| 参数 | 单位 | 含义及值域 |\n|---|---|---|\n'+params+'\n\n## 几何、位置与身份\n\n'+geo+'\n\n## 时间、分量与输入重建\n\n'+time+'\n\n'+fields+'\n\n## 条件全集\n\n'+'\n\n'.join(records)+'\n\n'+bc+'\n\n## 输出\n\noutputs逻辑名与array key自由；每个quantity至少一次，可重复请求。全部float64、不含sampling、时间轴为'+axis+'，dtype／shape／components与单位按表及前述分量规则。\n\n| quantity | 类型、单位及定义 | 支持位置、value_kind |\n|---|---|---|\n'+outs+'\n\n'+observation+'结果HDF5仅含输出array、所需IDs及时间轴，严格复制输入身份与行序；不导出输入场、坐标或新网格。\n\n## 接收条件与限制\n\n'+size+'每轴至多101帧，全部输入／输出场各至多3000000数值分量。'+admission+'\n')
   tol='\n'.join(f'| `{q}` | {s["atol"]} | {s["rtol"]} | `{s["unit"]}` |' for q,s in c['outputs'].items())
   (td/'instruction.md').write_text(f'# {num} {c["name"]}\n\n实现覆盖本题完整公开问题族的可复用求解器，冻结后处理多个未见算例。'+PHYS[slug]+'\n\n具体几何、物性、声源、边界及观测在本题DATA定义，给定响应和范围不可替换。考生负责相容的建模实现、求解与误差控制，语言、软件、内部离散／积分步自由；覆盖整个契约的解析或降阶方法同样有效，不要求复现参考程序或参考网格离散。仅需[本题DATA](DATA.md)与[通用CONTRACT](../../../../docs/CONTRACT.md)补足输入输出。\n\n## 运行与资源\n\n'+size+'每轴至多101帧，输入与输出场分别至多3000000分量。当前规模、预算与容差均为待校准设计目标，正式数据须用独立基准证明预算内可达精度，排除任意病态或物理不唯一组合。\n\n'+f'入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{c["timeout"]}秒墙钟（含启动和I/O）、4CPU、6144MB、0GPU；逐例无网络。程序0退出并完成HDF5写入，无独立输出字节上限；生成求解器3600秒、构建1800秒。提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5，不强制Python求解。\n\n## 评分\n\n每有效例正常退出、结构合法且所有输出quantity在全部时刻／实体／分量上满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分；阈值等号接受。'+('复量实部和虚部分别比较，不做全局相位旋转、幅值拟合或RMS替换。' if not tr else '')+'无去均值、重排、平移或少数超限豁免。\n\n| quantity | atol | rtol | 单位 |\n|---|---|---|---|\n'+tol+'\n\n本题成绩为通过有效例数／有效例数；输入、配置或参考错误是基础设施错误，不计考生失败，无有效例不产生成绩。IDs、时间、shape、dtype及有限值严格遵守CONTRACT。容差与资源须在评测前校准；工具回归不构成声学精度证据。\n')
   (td/'grading.json').write_text(json.dumps(dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()}),indent=2)+'\n')
   (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
   (td/'harbor').mkdir(exist_ok=True);(td/'harbor/requirements.txt').write_text('scipy==1.18.1\n');(td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 4\nmemory_mb = 6144\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
  (sd/'README.md').write_text(f'# {sec.split("-")[0]} {title}\n\n'+'\n'.join(links)+'\n');toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
 (CH/'README.md').write_text('# 第六章 声学分析\n\n6节10题，独立instruction／DATA及通用CONTRACT为考生阅读集合。正式数据、参考和发布留后。\n\n'+'\n'.join(toc)+'\n\n维护：[章规划](../design/chapter-06-acoustics.md)、[逐题清单](../design/chapter-06-task-plan.md)、[进度与证据](../design/reviews/chapter-06-progress.md)。\n')
if __name__=='__main__':main()
