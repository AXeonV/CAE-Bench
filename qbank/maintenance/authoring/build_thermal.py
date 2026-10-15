"""Expand task-specific public statements and metadata. No case/reference maker."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3];CH=ROOT/'qbank/05-heat-transfer'
SECTIONS=[('5.1-conduction','导热与各向异性',['thermal-steady','thermal-transient','anisotropic-conduction']),('5.2-properties','温度相关热物性',['nonlinear-conductivity','nonlinear-capacity']),('5.3-interfaces-layers','界面与降维薄层',['thermal-contact','thin-sheet-heat']),('5.4-convection','给定流场下的对流换热',['prescribed-advection-heat','conjugate-prescribed-flow']),('5.5-radiation','热辐射',['radiative-boundary','gray-enclosure']),('5.6-phase-change','相变传热',['mushy-enthalpy','isothermal-stefan'])]
NAMES=['三维稳态导热','三维瞬态导热','各向异性瞬态导热','温变导热系数稳态传热','温变热容量瞬态传热','有限界面热阻传热','薄层面内传热与面换热','给定速度场热输运','给定流场的流固共轭换热','导热体表面对流辐射换热','灰漫封闭腔体辐射热响应','有限相变温区的焓传热','等温相变的Stefan焓响应']
def S(unit,meaning,**kw):return dict(unit=unit,meaning=meaning,kind='scalar',shape=[1],**kw)
def V(d,unit,meaning,**kw):return dict(unit=unit,meaning=meaning,kind='vector',shape=[d],**kw)
def C(shape,unit,meaning,**kw):return dict(unit=unit,meaning=meaning,kind='components',shape=shape,**kw)
def P(unit,meaning,**kw):return dict(unit=unit,meaning=meaning,**kw)
M={}
for slug,name in zip([s for _,_,ss in SECTIONS for s in ss],NAMES):
 steady=slug in ('thermal-steady','nonlinear-conductivity');gray=slug=='gray-enclosure';sheet=slug=='thin-sheet-heat';phase=slug in ('mushy-enthalpy','isothermal-stefan');adv=slug in ('prescribed-advection-heat','conjugate-prescribed-flow');d=2 if sheet else 3
 cfg=dict(name=name,dimension=d,topology=0 if gray else d,steady=steady,phase=phase,advection=adv,parameters={},records={},outputs={},timeout=180 if gray else 600 if steady and slug=='thermal-steady' else 1500 if phase or slug in ('nonlinear-conductivity','nonlinear-capacity') else 1000,limits=dict(cells=4000,nodes=10000,frames=101,components=3000000))
 if not steady:cfg['parameters'].update(start_time=P('s','初始时刻t0'),end_time=P('s','终止时刻tf，严格大于t0'))
 cfg['parameters'].update(temperature_min=P('K','适用温区下界Tmin>0',positive=True),temperature_max=P('K','适用温区上界Tmax>Tmin',positive=True))
 if slug in ('nonlinear-conductivity','nonlinear-capacity'):cfg['parameters']['temperature_reference']=P('K','物性参考温度Tr，位于[Tmin,Tmax]')
 if gray:cfg['parameters']['patch_count']=P('1','表面数p，整数2..24',integer=True,lower=2,upper=24)
 if slug=='mushy-enthalpy':cfg['parameters'].update(solidus=P('K','固相线Ts，Tmin<Ts<Tl<Tmax'),liquidus=P('K','液相线Tl'))
 if slug=='isothermal-stefan':cfg['parameters']['melting_temperature']=P('K','熔点Tm，Tmin<Tm<Tmax')
 def rec(op,role,var,where,data,required=True,static=False):cfg['records'][op]=dict(role=role,variable=var,where=where,data=data,required=required,static=static)
 def out(q,s,where='cells',atol=.1,rtol=.005):cfg['outputs'][q]=dict(s,where=where,atol=atol,rtol=rtol)
 if gray:
  rec('enclosure','material','radiation','enclosure',dict(area=C(['p'],'m2','各表面积Ai>0',positive=True),capacity=C(['p'],'J/K','每个等温表面的总热容Ci>0',positive=True),emissivity=C(['p'],'1','灰漫发射率0<εi≤1',positive=True,upper=1),view_factors=C(['p','p'],'1','Fij，行i射向列j的能量比例',lower=0,upper=1)),static=True)
  rec('initial_temperature','initial','temperature','enclosure',dict(value=C(['p'],'K','各表面初温Ti(t0)')),static=True)
  rec('power','source','heat','enclosure',dict(value=C(['p'],'W','外界给每个表面的非辐射净加热功率Pi(t)，可正可负')))
  out('temperature',C(['p'],'K','各等温表面温度Ti'),'enclosure',.1,0)
  out('radiosity',C(['p'],'W/m2','总离面辐射度Ji，包含发射和反射'),'enclosure')
  out('net_radiation',C(['p'],'W','向腔内离开表面i的净辐射功率Ai(Ji−Gi)'),'enclosure')
 else:
  mat=dict(conductivity=S('W/(m.K)','导热率k>0',positive=True))
  if slug=='anisotropic-conduction':mat['conductivity']=dict(unit='W/(m.K)',kind='tensor',shape=[3,3],meaning='全局导热张量K，对称正定')
  if not steady:mat['capacity']=S('J/(m3.K)','体积热容量C>0',positive=True)
  if slug=='nonlinear-conductivity':mat['beta']=S('1/K','指数导热率系数β，可正可负')
  if slug=='nonlinear-capacity':mat['gamma']=S('1/K','容量线性温度系数γ，可正可负')
  if sheet:mat['thickness']=S('m','实际厚度a>0，逐单元常数',positive=True)
  if phase:mat['latent_heat']=S('J/m3','单位体积相变潜热L>0',positive=True)
  if slug=='conjugate-prescribed-flow':mat['medium']=S('1','0=固体，1=流体，int64，只允许field引用',dtype='int64')
  rec('material','material','thermal','cells',mat,static=True)
  rec('heat_source','source','heat','cells',dict(value=S('W/m2' if sheet else 'W/m3',('单位参考面积' if sheet else '单位体积')+'的净加热源Q，正值加热')))
  if not steady:
   rec('initial_enthalpy' if phase else 'initial_temperature','initial','enthalpy' if phase else 'temperature','cells' if phase else 'domain',dict(value=S('J/m3' if phase else 'K','初始焓密度H0' if phase else '初始绝对温度T0')),static=True)
  if adv:rec('prescribed_velocity','source','velocity','domain',dict(value=V(3,'m/s','全局给定稳态无散速度v；节点P1重建，不求动量')),static=True)
  rec('temperature','boundary','temperature','nodes',dict(value=S('K','给定边界绝对温度Tb')),False)
  rec('heat_flux','boundary','heat_flux','facets',dict(value=S('W/m' if sheet else 'W/m2','向外的导热热流，正值从域内流出')),False)
  rec('convection','boundary','heat_flux','facets',dict(coefficient=S('W/(m.K)' if sheet else 'W/(m2.K)','非负换热系数h',lower=0),ambient=S('K','外界温度Ta')),False)
  if sheet:rec('face_exchange','source','heat_exchange','cells',dict(h_plus=S('W/(m2.K)','上表面换热系数≥0',lower=0),h_minus=S('W/(m2.K)','下表面换热系数≥0',lower=0),ambient_plus=S('K','上表面环境温度'),ambient_minus=S('K','下表面环境温度')))
  if slug=='thermal-contact':rec('thermal_pair','boundary','heat_flux','facets',dict(partner={'location':True,'meaning':'另一侧几何重合外表面location'},conductance=S('W/(m2.K)','严格正界面热导g；按本侧实体分片常数',positive=True)))
  if slug=='radiative-boundary':rec('radiation','boundary','heat_flux','facets',dict(emissivity=S('1','发射率0<ε≤1',positive=True,upper=1),radiation_temperature=S('K','外部大黑体浴绝对温度Tr'),coefficient=S('W/(m2.K)','同一表面的对流换热系数h≥0',lower=0),ambient=S('K','同一表面对流环境温度Ta')))
  out('temperature',S('K','连续物理温度的实体平均值'),'cells',.1,0)
  out('sheet_heat_flow' if sheet else 'conductive_heat_flux',V(d,'W/m' if sheet else 'W/m2','厚度积分的面内导热流a q' if sheet else '导热热流q；不包含对流携热'),'cells')
  if slug=='thermal-contact':out('interface_heat_flux',S('W/m2','本条thermal_pair记录侧向partner流出的面平均导热热流'),'interface')
  if phase:
   out('enthalpy',S('J/m3','物理焓密度H的单元平均'),'cells',100.,.005)
   out('liquid_fraction',S('1','液相体积分数f的单元平均'),'cells',.005,0)
 M[slug]=cfg
BASE='''以热响应为分析目标，固体不运动、不变形，无未声明的热源或流动。热流q=−k∇T，界面无热阻时温度连续且法向导热热流守恒；输入单元共享节点tag的内部面均为这种完美热连接。空间非均匀材料参数按每个参考单元分片常数，材料跳变不暗加接触热阻。'''
PHYS={
 'thermal-steady':BASE+'稳态满足div q=Q。无物理初态或时间推进；至少有非空给定温度边界，或正面积上h>0的对流边界以确定绝对温度，排除纯Neumann欠定。',
 'thermal-transient':BASE+'热惯性满足C∂tT+div q=Q；C是体积容量，不再乘密度。给定初态，不将迭代初猜当初温。',
 'anisotropic-conduction':BASE.replace('q=−k∇T','q=−K∇T')+'K是全局坐标的对称正定完整张量，不按主轴重新解释输入。C∂tT+div q=Q。',
 'nonlinear-conductivity':BASE.replace('q=−k∇T','q=−k(T)∇T')+'k(T)=k0 exp[β(T−Tr)]，材料表conductivity给k0；β逐单元给定，|β(Tmin−Tr)|与|β(Tmax−Tr)|均≤20。稳态div q=Q，至少有非空温度边界或正面积h>0的对流边界。只评价[Tmin,Tmax]内的唯一物理解，不把k0当实际常导热率。',
 'nonlinear-capacity':BASE+'体积容量C(T)=C0[1+γ(T−Tr)]，material.capacity给C0；两端Tmin、Tmax的括号值均严格正。储热函数H(T)=C0[(T−Tr)+0.5γ(T−Tr)²]，因此∂tH+div q=Q。H的常数基准不影响演化，不能仅使用C(T)T代替其积分。',
 'thermal-contact':BASE+'储热为C∂tT+div q=Q。thermal_pair给定温度可跳跃的成对独立表面，记录侧记为minus、partner为plus。逐点q_minus·n_minus=g(T_minus−T_plus)，q_plus·n_plus=−g(T_minus−T_plus)。g在minus三角面上分片常数，按几何配对传给plus；局部节点存储方向不决定正负。其他共享节点内部面仍完美热连接。',
 'thin-sheet-heat':'''平面薄层厚度a(x)>0，温度在厚度方向均匀，但保留面内导热与两面的换热。q=−k∇xyT，sheet_heat_flow=a q，方程aC∂tT+divxy(aq)=Q_A−h_plus(T−Ta_plus)−h_minus(T−Ta_minus)。Q_A是单位面面积净加热源；容量C仍按体积，a与k、C逐三角形给定。跨内部边温度连续、(a q)法向守恒。不额外乘2或单位厚度，不含热辐射或厚度方向温度场。边界heat_flux指定(aq)·n（W/m），convection指定(aq)·n=h_edge(T−Ta)，h_edge为W/(m.K)；这与上下表面h的W/(m2.K)不同。''',
 'prescribed-advection-heat':BASE.replace('固体不运动、不变形','固定参考域')+'''给定无散稳态速度v，不求动量、压力、湍流或浮力。C为整个流体域一致的正体积容量；C(∂tT+v·∇T)+div q=Q。输入速度在一阶网格上节点P1重建，每单元div v=0。每个外面上v·n不变号；所有入流面（存在v·n<0）必须有给定温度，不能用仅热流或对流边界替代。出流／壁面边界规定导热热流，与对流携热不同；输出q也只含导热。''',
 'conjugate-prescribed-flow':BASE+'''medium=0固体、1流体，必须两者都有；共享tag界面完美热连接，不同材料可有不同k与C。速度在整个域节点P1重建，固体所有节点速度为0，因而流固界面v=0；流体每单元div v=0，所有流体单元的C为相同常数，固体C可逐单元变化。全域方程C(∂tT+v·∇T)+div q=Q；流体质量和速度不因温度反馈。外面v·n不变号，入流面必须有给定温度，其他边界及输出的热流均仅指导热。''',
 'radiative-boundary':BASE+'''C∂tT+div q=Q。radiation表面向外热流为h(T−Ta)+εσ(T⁴−Tr⁴)，σ固定为5.670374419e−8 W/(m2.K4)。Tr是外部大黑体浴温度；非参与介质，不求多表面反射、遮挡或光谱。此算子同时定义同一表面对流和辐射，不能再叠加另一边界记录。ε是灰漫发射率，绝对温度以K计算。''',
 'gray-enclosure':'''封闭非参与介质腔体由p个内部等温的灰漫表面组成，几何效果完全由输入视角系数F给定，不要求从隐藏几何求射线。Fij≥0、ΣjFij=1、AiFij=AjFji，可有非零自视角；不把F转置或按另一表面面积定义。Gi=ΣjFij Jj，Ji=εiσTi⁴+(1−εi)Gi，σ=5.670374419e−8 W/(m2.K4)。每表面Ci dTi/dt=Pi−Ai(Ji−Gi)，Ci为总热容J/K，不再乘面积。表面净功率以向腔内离开为正，Pi为外界非辐射加热。0<εi≤1保证辐射度系统可解；不指定额外环境温度、对流或导热网络。F与面积接收检查的绝对容差为1e−10（互易性比较AiFij与AjFji时用1e−10 max(1 m2,Ai,Aj)）；不归一化或修复输入。''',
 'mushy-enthalpy':BASE+'''无流动、密度或体积变化；体积焓H=C(T−Ts)+L f(T)，f=clip((T−Ts)/(Tl−Ts),0,1)，Ts<Tl，固液两相显热容量同为给定C。演化∂tH+div q=Q，k不随相分数变化。初态直接给H0逐单元常数，温度由此单调关系唯一反解；不能只给熔点温度并猜液相分数。输出是H、T、f各自的空间平均，不能用f(平均T)替代平均f。''',
 'isothermal-stefan':BASE+'''无流动、密度或体积变化；体积焓与温度采用等温相变图：H<0时T=Tm+H/C、f=0；0≤H≤L时T=Tm、f=H/L；H>L时T=Tm+(H−L)/C、f=1。固液两相显热容量同为C，k不随相分数变化。演化∂tH+div q=Q。初态给H0逐单元常数，因此平台内的液相分数也确定；不以微小人工温区替换此图，不另加隐藏界面速度或成核规则。允许内部追踪界面或焓算法；最终T、H、f及q映回固定输入单元平均。'''
}

def shape(s,p):return [p['patch_count'] if x=='p' else x for x in s['shape']]
def labels(s,p):
 sh=shape(s,p);kind=s['kind'];return ['value'] if kind=='scalar' else list('xyz'[:sh[0]]) if kind=='vector' else [a+b for a in 'xyz'[:sh[0]] for b in 'xyz'[:sh[0]]] if kind=='tensor' else ['c'+str(i+1) for i in range(__import__('math').prod(sh))]
def describe(s):
 if 'location' in s:return s['meaning']+'；仅允许`{"location":"名称"}`'
 return f"{s['kind']} {s['shape']}，`{s['unit']}`；{s['meaning']}"+('，dtype=int64' if s.get('dtype')=='int64' else '')

def main():
 ext=ROOT/'qbank/extensions/caeoj_ext/thermal';ext.mkdir(parents=True,exist_ok=True);(ext/'models.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n')
 toc=[]
 for sec,title,slugs in SECTIONS:
  sd=CH/sec;sd.mkdir(parents=True,exist_ok=True);links=[]
  for i,slug in enumerate(slugs,1):
   c=M[slug];td=sd/slug;td.mkdir(exist_ok=True);gray=c['topology']==0;phase=c['phase'];steady=c['steady'];sheet=c['dimension']==2;axis='steady' if steady else 'response';num=sec.split('-')[0]+'.'+str(i)
   links.append(f'- {num} [{c["name"]}]({slug}/instruction.md)')
   geometry='''meshes和geometries均为空对象。locations恰含enclosure：kind=entities，ids指向一个非负int64 ID；它代表一套腔体，表面顺序是components轴的顺序，不是假空间探针。p取patch_count；面积、容量、发射率、初温和功率的shape=[p]，F的shape=[p,p]，第i行第j列是Fij。components标签固定按行优先c1..cL（L为shape分量数）；不增加表面ID表，不按面积排序。''' if gray else f'''meshes恰含main，格式MSH4.1 ASCII；可选geometries按CONTRACT引用，但域以输入网格为准。顶维为{c['dimension']}，只允许非退化一阶{'三角形type2' if sheet else '四面体type4'}及其一阶外边界{'线段type1' if sheet else '三角形type2'}；每个外边界面／边导出一次，不允许非流形公共面或悬挂节点。保留locations.domain为全部顶维单元所用节点，locations.cells为全部顶维单元；两者恰好覆盖，不能有未用节点。其他位置只允许同网格节点子集、顶维单元子集或外边界单元子集；不允许points、entities、aggregate或其他网格。IDs按实际tag递增，组若声明必须精确匹配IDs；tag不是行号，组名不决定物理条件。二阶以上单元不属于本题支持集合。'''
   if not gray:
    geometry+='节点位置用于温度边界／初态和给定速度；元素位置用于材料、热源和平均观测。给定温度的节点集必须是完整外边界面的顶点之并，作用面精确定义为所有顶点均属于该节点集的全部完整外面；该节点集必须恰好等于这些作用面的顶点并，不得选择同一节点并的另一组面。禁止孤立节点／棱支撑。各温度记录不能共享节点；不同类别边界可在棱上相交但不能覆盖同一完整面。面外法向由唯一相邻顶维单元确定，与面内节点顺序无关。'
    geometry+=('thermal_pair的两侧使用不同节点及面tag，几何三角面逐顶点坐标完全重合且一一配对，相邻体位于公共面相反侧；partner不可与本侧相同或复用任一侧。接触表面不再施加其他边界。配对按完整几何顶点集合，不按行序；不支持非匹配网格或部分面接触。' if slug=='thermal-contact' else '参考域连通；相邻单元共享tag的内部面是完美热连接，不得将内部面当外边界。')
   time='''time_axes恰含steady=[0.0]；所有字段和输出都引用steady，输入不随时间变化，无初态或输出多帧。''' if steady else '''time_axes必须含initial单帧[t0]、response非空严格递增请求时刻；全部轴至多101帧。response位于[t0,tf]。材料、初态以及标注static的记录字段只用initial单帧；其他加载字段可用任意已声明轴：单帧必须在t0，表示全程常量；多帧须首末恰为t0、tf，逐分量连续分段线性插值，不外推。除initial、response外，不允许未被加载字段使用的轴。输出时刻不等于内部时间步，不能跳过未请求的中间载荷。'''
   if phase:time+='本题response必须严格晚于t0；初始焓可跨单元不连续，避免请求初始瞬间无有限平均意义的热流。'
   fields='''所有fields必须被条件引用，条件引用fields逻辑名，field.array才是HDF5 key；名称均自由，不靠名字推断quantity。输入field的quantity必须等于条件表给出的data键，只有value固定按variable取名：heat_source.value为heat_source、power.value为power、initial_enthalpy.value为enthalpy、prescribed_velocity.value为velocity、heat_flux.value为heat_flux，其余value为temperature。'''
   mapping={'heat_source':'heat_source','power':'power','initial_enthalpy':'enthalpy','prescribed_velocity':'velocity','heat_flux':'heat_flux'}
   active=[op+'.value为'+mapping.get(op,'temperature') for op,r in c['records'].items() if 'value' in r['data']]
   fields=fields[:fields.index('只有value固定按variable取名：')]+'只有value的quantity按以下规则：'+'；'.join(active)+'。'
   fields+='全部输入field显式sampling，extrapolation=forbid；space在节点为piecewise_linear（沿一阶网格唯一P1重建），在元素为piecewise_constant（每实体常值）'+('，enclosure为uniform（每个表面离散参数，不作空间插值）' if gray else '')+'；time为constant（static或单帧）或linear（加载多帧）。先空间重建再时间插值；给定温度节点场在对应完整外表面P1重建。'
   if gray:fields=fields.replace('在节点为piecewise_linear（沿一阶网格唯一P1重建），在元素为piecewise_constant（每实体常值），enclosure为uniform（每个表面离散参数，不作空间插值）','enclosure为uniform，表示每个表面的离散参数，不作空间插值').replace('先空间重建再时间插值；给定温度节点场在对应完整外表面P1重建。','矩阵参数恒定，加载逐分量插值。')
   fields+='标量默认float64，shape=[1]、components=["value"]；vector为全局x/y/z前D分量；tensor用完整全局矩阵及行优先xx,xy,...标签，不以Voigt或局部主轴替代。'+('components的分量标签见位置段。' if gray else '')+'数组始终[T,N,*shape]；medium若列出使用int64，其余均float64。'
   fields+='标量data可用同location、同unit／quantity／kind的field引用，或`{"value":有限实数,"unit":"表中单位"}`表示全位置全程常量；不接受布尔值。矢量、张量、components和medium只能field引用；禁止内联数组、跨location借相同长度或省略sampling。所有数值范围也适用于常量表示。'
   if gray:
    fields=fields.replace('或张量','或张量').replace('标量默认float64，shape=[1]、components=["value"]；vector为全局x/y/z前D分量；tensor用完整全局矩阵及行优先xx,xy,...标签，不以Voigt或局部主轴替代。','').replace('medium若列出使用int64，其余均float64。','全部float64。').replace('标量data可用同location、同unit／quantity／kind的field引用，或`{"value":有限实数,"unit":"表中单位"}`表示全位置全程常量；不接受布尔值。矢量、张量、components和medium只能field引用；禁止内联数组、跨location借相同长度或省略sampling。所有数值范围也适用于常量表示。','本题全部data仅允许同location、同quantity／unit／kind的显式field引用，不允许内联数组或常量替代；禁止省略sampling。')
   elif slug!='conjugate-prescribed-flow':
    fields=fields.replace('medium若列出使用int64，其余均float64。','全部float64。').replace('矢量、张量、components和medium只能field引用','矢量、张量只能field引用')
   fields+='输入field的value_kind在节点为point、在元素为average，表示上述P1节点值或实体常值；不接受integral。' if not gray else '输入field的value_kind为point，表示每个离散表面的参数。'
   if not gray and slug!='anisotropic-conduction':fields=fields.replace('；tensor用完整全局矩阵及行优先xx,xy,...标签，不以Voigt或局部主轴替代','')
   if not gray and not c['advection']:geometry=geometry.replace('和给定速度','')
   if phase:geometry=geometry.replace('节点位置用于温度边界／初态','节点位置仅用于温度边界，初始焓使用cells')
   recs=[]
   for op,r in c['records'].items():
    where={'domain':'domain全部节点','cells':'cells全部单元','enclosure':'enclosure','nodes':'完整外边界面顶点之并的节点location','facets':'外边界单元location'}[r['where']]
    recs.append(f'### `{op}`\n\nrole=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`，location={where}。'+('必须出现；' if r['required'] else '可不出现；')+('恰一条覆盖整个位置。' if r['where'] in ('domain','cells','enclosure') else '可多条，但对应边界实体不得重复。')+('参数只随实体变化，不随时间变化。' if r['static'] else '允许上述加载历史。')+'data恰含下列全部键：\n\n| data键 | 类型、单位及含义 |\n|---|---|\n'+'\n'.join(f'| `{key}` | {describe(spec)} |' for key,spec in r['data'].items()))
   boundary=''
   if not gray:
    boundary=('convection的精确关系为q·n=h(T−Ta)，heat_flux给定q·n；正值均向外。' if not sheet else '')+'未声明的外边界为绝热q·n=0'+('（薄层为(aq)·n=0）' if sheet else '')+'。每个完整外面至多一种边界记录，不以列表顺序覆盖；对流h=0合法并表示绝热。静态材料、体源及初态记录各算子恰一条覆盖表定全域；边界可多条互不重叠记录。Tmin、Tmax约束所有温度输入和物理解；环境温度也在此区间。初始温度与温度边界在t0相容；初始焓时由H0反解T0后核对。'
   params='\n'.join(f'| `{k}` | `{s["unit"]}` | {s["meaning"]} |' for k,s in c['parameters'].items())
   outputs='\n'.join(f'| `{q}` | {describe(spec)} | '+('enclosure，point' if gray else '每条thermal_pair记录侧完整面，average；每条均需请求' if spec['where']=='interface' else 'cells或其任意非空单元子集，average')+' |' for q,spec in c['outputs'].items())
   observation='''输出平均按实体实际体积''' if not sheet else '''输出平均按参考三角形面积'''
   observation+='（边界面观测按其实际面积）积分再除测度，不是单元中心值或节点算术均值。非线性材料与相分数必须先逐点计算再平均；同一输出位置不规定内部求解网格。' if not gray else ''
   if gray:observation='输出point指每个离散表面自身状态；不表示固定空间探针或平均后的虚构温度，不对components轴排序、旋转或归一化。'
   admission='''正式数据须确认材料响应在声明温区内有效、网格非退化、初边值相容、所请求平均／点态存在、物理解唯一，并以独立基准核验预算内可达设计精度。温区保证约束全程，不只约束请求帧；不能由Schema或残差自动证明。''' if not gray else '''正式数据须确认给定F可代表本题灰漫表面系统、温度全程位于[Tmin,Tmax]、初态和加载相容，并用独立基准核验预算内可达设计精度。数值接受的F不被工具归一化，合法格式或线性系统可解不能替代参考和物理证据。'''
   if slug!='thermal-contact':observation=observation.replace('（边界面观测按其实际面积）','')
   if steady:
    geometry=geometry.replace('温度边界／初态','温度边界')
    boundary=boundary.replace('静态材料、体源及初态记录','静态材料和体源记录')
   if not phase:
    boundary=boundary.replace('；初始焓时由H0反解T0后核对','')
    boundary=boundary.replace('初始焓时由H0反解T0后核对。','')
    observation=observation.replace('非线性材料与相分数必须先逐点计算再平均；','物理量先逐点计算再作实体积分；' if slug in ('nonlinear-conductivity','nonlinear-capacity','radiative-boundary') else '')
   if steady:
    boundary=boundary.replace('初始温度与温度边界在t0相容；','').replace('初始温度与温度边界在t0相容。','')
    time_fields=fields.replace('time为constant（static或单帧）或linear（加载多帧）','time仅为constant').replace('先空间重建再时间插值','只作上述空间重建，不作时间插值')
    fields=time_fields
    recs=[r.replace('允许上述加载历史。','只允许上述稳态常量。') for r in recs]
   if not gray:
    geometry=geometry.replace('外边界面／边导出一次','外边界'+('边' if sheet else '面')+'导出一次').replace('参考域连通','参考域通过完整公共面连通')
   fields=fields.replace('spaceenclosure为uniform','sampling.space=uniform')
   (td/'DATA.md').write_text(f'# {slug} 数据契约\n\n入口为problem.json及data_file引用的扁平HDF5，路径相对清单。`spatial_dimension={c["dimension"]}`；physics恰含model与parameters，model=`thermal-{slug}-v1`；task可省略，出现时必须为`{slug}`。不允许contract_version、profile、analysis或materials混用。除自由对象名和数组key外，不接受本题未列的模型、字段或条件。\n\n## 物理定义\n\n'+PHYS[slug]+'\n\n## 全局参数\n\nparameters恰含下表全部项，每项恰为value和unit对象；值为有限实数，不含布尔值，整数项必须JSON整数。Tmin<Tmax，温区约束不是评分归一化基准。\n\n| 参数 | 单位 | 含义与值域 |\n|---|---|---|\n'+params+'\n\n## 几何、位置和身份\n\n'+geometry+'\n\n## 时间与输入场\n\n'+time+'\n\n'+fields+'\n\n## 条件全集\n\n'+'\n\n'.join(recs)+'\n\n'+boundary+'\n\n## 输出及采样\n\noutputs逻辑名称和array key自由，每个quantity至少一次；可重复请求。输出全部float64，轴为'+axis+'，不含sampling；位置、单位、kind及分量按表，不允许其他quantity。\n\n| quantity | 类型、单位与含义 | 位置及value_kind |\n|---|---|---|\n'+outputs+'\n\n'+observation+'结果仅含输出array及其IDs、时间轴，严格沿用输入身份和行序；不复制坐标、输入字段或重新导出网格。\n\n## 接收范围与验证边界\n\n'+admission+'\n'+('表面数2..24，一套enclosure。' if gray else '至多4000个顶维单元、10000节点。')+'各轴至多101帧，输入与输出场分别至多3000000个数值分量。没有正式数据时，不把工具fixture当物理／数值验证。\n')
   tolerances='\n'.join(f'| `{q}` | {s["atol"]} | {s["rtol"]} | `{s["unit"]}` |' for q,s in c['outputs'].items())
   (td/'instruction.md').write_text(f'# {num} {c["name"]}\n\n实现本题完整公开问题族的可复用求解器，冻结后处理多个未见算例。'+PHYS[slug]+'\n\n具体材料、参数、几何或离散表面、热载荷、初态（仅瞬态）与输出由本题DATA定义。考生负责依据给定物理事实建立相容热分析，选择适当表示、离散、非线性及时间求解和误差控制；不能替换本题给定的物理响应。语言、软件、内部网格和算法自由，覆盖公开范围的解析／降阶方法同样有效，不要求复现参考软件或参考离散。只需阅读[本题DATA](DATA.md)和[通用CONTRACT](../../../../docs/CONTRACT.md)。\n\n## 运行与规模\n\n'+('一套腔体、2..24个灰漫表面。' if gray else '参考网格至多4000顶维单元、10000节点。')+'每轴至多101帧，输入／输出场分别至多3000000分量；数据方须避免任意病态组合，并用独立基准证明预算内精度。当前预算与容差是待校准设计目标，不能视作已获得参考精度或物理验证。\n\n'+f'入口`python solve.py --input /path/problem.json --output /path/result.h5`；每例Linux AMD64、{c["timeout"]}秒墙钟（含启动和读写）、4CPU、6144MB、0GPU；逐例无网络。程序0退出并写出完整HDF5；无独立输出字节限额。生成求解器3600秒，构建1800秒。环境提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5，不强制Python求解。\n\n## 评分\n\n每个有效例正常退出、输出结构合法、所有quantity在全部请求时刻／实体／分量上逐值满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分；阈值等号接受，无平移、拟合、重排、去均值或少数超限豁免。温度直接以K比较，rtol=0；不按绝对开尔文温度放宽相对误差。\n\n| quantity | atol | rtol | 单位 |\n|---|---|---|---|\n'+tolerances+'\n\n成绩为通过有效例数／有效例数；输入／配置／参考错误属于基础设施错误，不算考生失败，无有效例时不产生成绩。IDs、时间、shape、dtype及有限值严格遵守CONTRACT。正式数据、参考准确性、容差／预算校准及评测发布留后。\n')
   if steady:
    pth=td/'instruction.md';pth.write_text(pth.read_text().replace('、初态（仅瞬态）',''))
   (td/'grading.json').write_text(json.dumps(dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()}),indent=2)+'\n')
   (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
   (td/'harbor').mkdir(exist_ok=True);(td/'harbor/requirements.txt').write_text('scipy==1.18.1\n');(td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 4\nmemory_mb = 6144\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
  (sd/'README.md').write_text(f'# {sec.split("-")[0]} {title}\n\n'+'\n'.join(links)+'\n');toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
 (CH/'README.md').write_text('# 第五章 传热与热过程分析\n\n6节13题，自包含instruction与DATA，配合通用CONTRACT。正式数据、参考及评测发布留后。\n\n'+'\n'.join(toc)+'\n\n维护：[章规划](../design/chapter-05-heat-transfer.md)、[逐题清单](../design/chapter-05-task-plan.md)、[进度与证据](../design/reviews/chapter-05-progress.md)。\n')
if __name__=='__main__':main()
