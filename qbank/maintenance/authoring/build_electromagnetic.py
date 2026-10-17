"""Expand independent electromagnetic contracts/configuration; no data maker."""
from pathlib import Path
from caeoj_tools.author import public_model_catalog
import json,math
ROOT=Path(__file__).resolve().parents[3];CH=ROOT/'qbank/07-electromagnetics'
SECTIONS=[('7.1-electrostatics','静电场',['electrostatic','floating-electrode']),('7.2-conduction','电流传导',['dc-conduction','dielectric-relaxation']),('7.3-magnetostatics','静磁场',['magnetostatic']),('7.4-eddy-currents','磁准静态涡流',['harmonic-eddy']),('7.5-waves','高频全波',['maxwell-cavity']),('7.6-circuits','集总电路',['rlc-transient','rlc-harmonic']),('7.7-field-circuit','场—路反馈',['coil-circuit'])]
NAMES=['介质静电场','浮置导体静电场','稳恒电流传导','介质电荷弛豫','面外电流静磁场','面外单频涡流','有耗腔体全波响应','有向RLC电路瞬态','有向RLC电路单频','线圈与涡流场反馈']
def S(unit,meaning,**kw):return dict(kind='scalar',shape=[1],unit=unit,meaning=meaning,**kw)
def V(d,unit,meaning):return dict(kind='vector',shape=[d],unit=unit,meaning=meaning)
def Z(unit,meaning):return dict(kind='components',shape=[2],unit=unit,meaning=meaning)
def ZV(d,unit,meaning):return dict(kind='components',shape=[d,2],unit=unit,meaning=meaning)
def P(unit,meaning,**kw):return dict(unit=unit,meaning=meaning,**kw)
M={}
for slug,name in zip([v for _,_,ss in SECTIONS for v in ss],NAMES):
 circuit=slug.startswith('rlc-');tr=slug in ('dielectric-relaxation','rlc-transient');harm=slug in ('harmonic-eddy','maxwell-cavity','rlc-harmonic','coil-circuit');d=0 if circuit else 3 if slug=='maxwell-cavity' else 2
 c=dict(name=name,dimension=d,transient=tr,harmonic=harm,parameters={},records={},outputs={},timeout=240 if circuit else 1800 if d==3 else 1200 if slug=='coil-circuit' else 900 if tr or harm else 600)
 def rec(op,role,var,where,data,required=True,static=False):c['records'][op]=dict(role=role,variable=var,where=where,data=data,required=required,static=static)
 def out(q,s,where='cells',atol=1e-7):c['outputs'][q]=dict(s,where=where,atol=atol,rtol=.005)
 if tr:c['parameters'].update(start_time=P('s','初始时刻t0'),end_time=P('s','末时刻tf>t0'))
 if harm:c['parameters']['frequency']=P('Hz','f>0，ω=2πf',positive=True)
 if circuit:
  c['parameters']['ground_node']=P('1','地节点的真实ID，非负JSON整数，须属于nodes',integer=True,lower=0)
  if tr:rec('initial_voltage','initial','node_voltage','nodes',dict(value=S('V','节点真实初始电压，地为0')),static=True)
  for op,unit,key in [('resistor','Ohm','resistance'),('capacitor','F','capacitance'),('inductor','H','inductance'),('voltage_source','V','value'),('current_source','A','value')]:
   data={k:S('1',('正向起点' if k=='tail' else '正向终点')+'节点ID',dtype='int64',static=True) for k in ('tail','head')}
   data[key]=S(unit,'正元件参数',positive=True,static=True) if key!='value' else Z(unit,'规定支路源相量') if harm else S(unit,'规定支路源历史')
   if tr and op=='inductor':data['current0']=S('A','正向初始电感电流',static=True)
   rec(op,'source' if op.endswith('source') else 'material','branch', 'branches',data,op=='resistor')
  for q,u,w in [('node_voltage','V','nodes'),('branch_voltage','V','branches'),('branch_current','A','branches')]:out(q,Z(u,'指定方向的复量') if harm else S(u,'指定方向的实量'),w,1e-6 if u=='V' else 1e-8)
 elif slug=='maxwell-cavity':
  rec('material','material','electromagnetic','cells',dict(permittivity=S('F/m','绝对介电常数ε>0',positive=True),permeability=S('H/m','绝对磁导率μ>0',positive=True),conductivity=S('S/m','电导率σ>0',positive=True)),static=True)
  rec('current_source','source','current_density','cells',dict(value=ZV(3,'A/m2','外加体电流Js')))
  out('electric_field',ZV(3,'V/m','E'));out('magnetic_field',ZV(3,'A/m','H'));out('joule_loss',S('W/m3','时间平均焦耳损耗'),atol=1e-8)
 else:
  electro=slug in ('electrostatic','floating-electrode');cond=slug in ('dc-conduction','dielectric-relaxation');mag=not electro and not cond
  mat={}
  if electro or tr:mat['permittivity']=S('F/m','绝对介电常数ε>0',positive=True)
  if cond:mat['conductivity']=S('S/m','电导率σ>0',positive=True)
  if mag:
   mat['reluctivity']=S('m/H','磁阻率ν=1/μ>0',positive=True)
   if harm:mat['conductivity']=S('S/m','电导率σ≥0',lower=0)
  rec('material','material','electromagnetic','cells',mat,static=True)
  boundary_var='vector_potential' if mag else 'potential';bu='Wb/m' if mag else 'V'
  rec('dirichlet','boundary',boundary_var,'boundary_nodes',dict(value=Z(bu,'给定Az') if harm else S(bu,'给定Az' if mag else '给定电势')))
  if slug!='coil-circuit':rec('volume_source','source','current_density' if mag else 'charge_density' if electro else 'current_injection','cells',dict(value=Z('A/m2','面外外加电流Js') if harm else S('A/m2' if mag else 'C/m3' if electro else 'A/m3','面外电流Jz' if mag else '自由体电荷ρf' if electro else '正值为注入的体电流s')))
  if not mag:rec('normal_flux','boundary','displacement_flux' if electro else 'current_flux','facets',dict(value=S('C/m2' if electro else 'A/m2','域外正的D·n' if electro else '域外正的总电流Jtot·n' if tr else '域外正的传导电流Jc·n')),False)
  if slug=='floating-electrode':rec('floating','boundary','potential','floating',dict(charge=S('C/m','该导体单位轴长总自由电荷Q；若用节点field，所有值须严格相等，取共同值作唯一Q，不作空间重建或积分')))
  if tr:rec('initial_potential','initial','potential','domain',dict(value=S('V','真实初始电势')),static=True)
  if slug=='coil-circuit':
   c['parameters'].update(length=P('m','真实轴向长度ℓ>0',positive=True),resistance=P('Ohm','串联电阻R>0',positive=True),inductance=P('H','外部串联电感L>0，不含所求场磁链',positive=True),capacitance=P('F','串联电容C>0',positive=True))
   rec('winding','source','winding_density','cells',dict(value=S('1/m2','有符号绕组密度w，可正负且不恒零')),static=True)
   rec('voltage_drive','source','voltage','coil',dict(value=Z('V','外加串联电压Vs')))
   out('coil_current',Z('A','未知线圈正向电流I'),'coil',1e-8);out('flux_linkage',Z('Wb','线圈磁链λ'),'coil',1e-9)
  if mag:
   out('vector_potential',Z('Wb/m','Az') if harm else S('Wb/m','Az'),atol=1e-9)
   out('magnetic_flux_density',ZV(2,'T','B') if harm else V(2,'T','B'),atol=1e-8)
   if harm:out('induced_current',Z('A/m2','Jind,z=−iωσAz'))
   else:out('magnetic_field',V(2,'A/m','H=νB'))
  else:
   out('potential',S('V','电势V'),atol=1e-6);out('electric_field',V(2,'V/m','E=−∇V'))
   if electro:out('electric_displacement',V(2,'C/m2','D=εE'),atol=1e-10)
   else:out('conduction_current',V(2,'A/m2','Jc=σE'))
   if tr:out('total_current',V(2,'A/m2','Jtot=σE+ε∂tE'))
   if slug=='dc-conduction':out('joule_loss',S('W/m3','σ|E|²'),atol=1e-8)
   if slug=='floating-electrode':out('electrode_potential',S('V','各浮置导体等势值'),'floating',1e-6)
 M[slug]=c
ELECTRIC='二维xy平面、z平移不变，材料逐三角形常数，各向同性线性。E=−∇V。'
PHYS={
'electrostatic':ELECTRIC+'D=εE，div D=ρf。内部界面V连续、D法向连续，无额外界面自由电荷。外法向n指向计算域外；Dirichlet固定V，normal_flux给D·n；其余外边界D·n=0。至少一条Dirichlet锚定绝对电势。',
'floating-electrode':ELECTRIC+'D=εE，div D=ρf。域仅为介质，不含导体内部。内部界面V和D法向连续。固定电势、D·n及默认D·n=0同普通静电；每条floating节点集表示一个独立导体，电势Uf在该集合全部作用边上为同一未知数，并满足−∫边界D·n ds=Q。n指介质向外，Q为导体单位轴长总自由电荷C/m。不同导体不默认短接，固定电势锚定绝对基准，不以每帧去均值处理；每个浮置导体输出其Uf。',
'dc-conduction':ELECTRIC+'Jc=σE，div Jc=s，s为正的体电流注入。界面V与Jc法向连续；Dirichlet给V，normal_flux给Jc·n，其他外边界绝缘。至少一条Dirichlet固定参考。焦耳热σ|E|²只作为观测，不反馈温度、电导或流动。',
'dielectric-relaxation':ELECTRIC+'Jc=σE，Jtot=σE+ε∂tE，div Jtot=s。无磁感应或材料温度反馈。界面V与Jtot法向连续，初始V节点P1且与边界相容；不强制初态满足稳恒传导方程。Dirichlet规定V(t)，normal_flux给总电流Jtot·n，其余外边界Jtot·n=0，至少一条Dirichlet固定参考。请求total_current的时刻必须严格晚于t0且不等于任意加载轴内部折点，以免∂tE有多种迹。',
'magnetostatic':'二维xy、z平移不变，只求Az。B=(∂yAz,−∂xAz)，H=νB，−div(ν∇Az)=Jz。ν逐三角形正常数，无磁滞、永磁或运动。内部Az连续、ν∂nAz连续；Dirichlet给绝对Az并固定其规范，其余外边界ν∂nAz=0。至少一条Dirichlet锚定，Az不再减去均值。二维磁场不含Bz。',
'harmonic-eddy':'二维xy、z平移不变，e^(+iωt)相量，只求Az。B=(∂yAz,−∂xAz)，−div(ν∇Az)+iωσAz=Js，Jind,z=−iωσAz。明确固定纵向标势梯度为0，E_z=−iωAz；Js是独立给定的面外外加电流，不包含Jind。ν>0、σ≥0逐三角形常数，内部Az和ν∂nAz连续；Dirichlet固定绝对Az，其余ν∂nAz=0，至少一条Dirichlet。忽略位移电流、运动和磁滞；不能解释为任意三维导体电极连接模型。',
'maxwell-cavity':'三维有界静止各向同性线性介质，ε、μ、σ均为逐四面体正实常数，e^(+iωt)相量。求curl(μ^−1 curl E)−(ω²ε−iωσ)E=−iωJs，H=i curl E/(ωμ)，时间平均损耗D=σ|E|²/2。全部外边界PEC：n×E=0；不附加E法向为0。内部无附加表面电流，E及H切向连续，分布意义方程含源所需自由电荷；不额外把div E设为0。保留位移电流，无端口、PML、开放辐射或本征模任务。',
'coil-circuit':'二维xy、z平移不变，e^(+iωt)相量，线性ν>0、σ≥0。B=(∂yAz,−∂xAz)，−div(ν∇Az)+iωσAz=wI，Jind,z=−iωσAz，纵向标势梯度固定0。给定有符号绕组密度w；绕组为独立理想绞线激励，不把wI再算成块体σ中的电流。真实轴长ℓ给λ=ℓ∫ΩwAz dS，电路满足(R+iωL+1/(iωC))I+iωλ=Vs。L只含外部串联电感，不重复场磁链。正向绕组、I、λ、Vs按上述能量共轭符号，场与电路双向反馈。Dirichlet给绝对Az，其余ν∂nAz=0，内部Az及ν∂nAz连续；至少一条Dirichlet。电路只有一个线圈及给定串联RLC，不要求提取绕组几何、端部场或电路拓扑。'
}
CIRCUIT='无空间几何的有向集总网络。每个支路tail→head定义正电流I和电压v=Vtail−Vhead，地节点电压恒0。每节点流出电流代数和0，无未声明的节点注入；源也作为支路。R、L、C为严格正常数；电阻v=RI。'
PHYS['rlc-transient']=CIRCUIT+'电容I=C dv/dt，电感v=L dI/dt；电压源v=value(t)，电流源I=value(t)。全部节点初始电压及每个电感初流显式给出；电容初压由节点初压差确定。不以迭代初猜或零初态替代。初态与源及代数约束相容。内部解时间连续，加载连续分段线性。'
PHYS['rlc-harmonic']=CIRCUIT+'e^(+iωt)相量，电容I=iωCv，电感v=iωLI；电压源v=value，电流源I=value。无瞬态初态或额外直流偏置。'
CIRCUIT_RULE='nodes为全部电路节点entities，2..33个；branches为全部支路entities，1..64个。两组ID各自非负唯一，可数值重合但不是同一对象；ground_node必须属于nodes。所有location只能为这两组之一的非空entities子集；条件支路集合按实际ID形成branches的无遗漏、无重叠划分。tail/head字段须为int64节点真实ID、不同且属于nodes；参数及端点静态。所有节点至少在一个支路上，所有节点通过电阻子图连通（保障参考和耗散），电压源子图无无向环（平行两源也算环）。其他RLC及源可有并联。合法数据须进一步保证约束相容、DAE正则且响应唯一，校验器的图检查不证明这些性质。无空间坐标、mesh、geometry、points或aggregate。'
def description(s):return f'{s["kind"]} {s["shape"]}，{s["unit"]}；{s["meaning"]}'+('；严格正' if s.get('positive') else '；非负' if s.get('lower')==0 else '')
def main():
 ext=ROOT/'qbank/extensions/caeoj_ext/electromagnetic';ext.mkdir(parents=True,exist_ok=True);(ext/'models.json').write_text(json.dumps(public_model_catalog(M),ensure_ascii=False,indent=2)+'\n');toc=[]
 for sec,title,slugs in SECTIONS:
  sd=CH/sec;sd.mkdir(parents=True,exist_ok=True);links=[]
  for i,slug in enumerate(slugs,1):
   c=M[slug];d=c['dimension'];tr=c['transient'];harm=c['harmonic'];circuit=d==0;td=sd/slug;td.mkdir(exist_ok=True);num=sec.split('-')[0]+'.'+str(i);links.append(f'- [{num} {c["name"]}]({slug}/instruction.md)')
   axis='response' if tr else 'harmonic' if harm else 'steady'
   physics=PHYS[slug]
   if d==2:physics+='二维所有面积积分按单位z长度解释；没有隐含厚度，coil-circuit中明确的ℓ只用于总磁链和电路。' if slug=='coil-circuit' else '二维面积／边界积分按单位z长度解释；没有隐含厚度。'
   geometry=CIRCUIT_RULE+'geometries和meshes必须为空。spatial_dimension=1只作协议元数据标记，不表示一维空间传输线。' if circuit else f'meshes恰含main；MSH4.1 ASCII，坐标m，spatial_dimension={d}。main只含非退化一阶'+('三角形type2及全部外边界线type1，全部节点z=0。' if d==2 else '四面体type4及全部外边界三角形type2。')+'无未用节点、悬挂节点、重叠体、自交或非流形公共面；域通过完整公共边／面连通；每个外面导出一次，不导出更低维单元。domain恰为main全部节点，cells恰为全部体单元；其他location仅main节点、体单元或外边界元素的非空子集。tag为身份不是行号，Physical Group若声明必须与IDs精确相符，组名不定义物理。禁止points或aggregate。'
   if not circuit and slug=='coil-circuit':geometry+='另有coil唯一entities对象，恰一个非负ID，无坐标；只用于电路源及输出，其他entities禁止。'
   elif not circuit:geometry+='禁止entities。'
   if not circuit and slug!='maxwell-cavity':geometry+='节点边界取所有顶点均属于该节点集的全部完整外面，节点集须恰等于这些面的顶点并。Dirichlet至少一条，各节点边界的节点集互不相交；所有边界作用面不得重叠。已声明边界与其余默认自然边界共享端点时按弱解解释，数据须保证所需观测存在。'+('每条floating节点集是一个独立等势导体，其闭包边集合须连通，至少一条floating；Dirichlet和floating不能接触同一节点。' if slug=='floating-electrode' else '')
   if slug=='maxwell-cavity':geometry+='PEC作用于全部外面，无boundary记录。'
   times='time_axes必须含initial=[t0]和response非空请求时刻，所有response在[t0,tf]内，各轴至多129帧。static字段仅initial；其他加载单帧须t0，表示全区间常量，多帧首末须t0、tf，逐分量连续分段线性，不外推。输出时刻不代替内部积分；不允许initial／response之外未被加载引用的轴。' if tr else 'time_axes仅含键'+axis+'，其引用的float64[1]数组恰为[0.0]，所有字段和输出引用该轴。0仅为'+('相量' if harm else '静态')+'存储标记。'
   if slug=='dielectric-relaxation':times+='response严格大于t0，不得等于任何加载轴内部折点；区间内采用普通时间导数，tf采用区间内左导数，不选择左右平均。'
   fields='条件data引用fields逻辑名，其array才是HDF5 key，两者名称自由。fields恰为全部实际引用项；quantity等于data键名，value例外等于条件variable。字段须与条件同location。数组[T,N,*component_shape]不省略轴；scalar=[1]、components=["value"]；'+('vector固定[2]及x/y。' if not circuit and not harm else '')
   if harm:fields+='复标量components [2]依次实虚，'+('复向量components ['+str(d)+',2]按'+('x/y/z' if d==3 else 'x/y')+'各自实虚，' if not circuit else '')+'组件标签按shape行优先展平c1..cL，不使用复数dtype、幅相或RMS。'
   fields+='所有数值float64'+('，唯tail/head为int64' if circuit else '')+'。scalar数据可用同单位有限数值value/unit常量或field；'+('tail/head必须field，不能用常量或浮点ID。' if circuit else '')+(('components' if harm else 'vector')+'必须field，不允许内联数组。' if not circuit or harm else '')+'输入value_kind'+(' entities为point，sampling.space=uniform。' if circuit else '节点为point、单元为average；节点sampling.space=piecewise_linear，为一阶网格上的唯一P1重建，元素为piecewise_constant，元素值即该元素常值。'+('coil实体为point、space=uniform。' if slug=='coil-circuit' else ''))
   fields+='sampling必须显式，extrapolation=forbid，时间单帧constant'+('、多帧linear。先空间再时间重建。表中static只能常量或initial轴字段。' if tr else '。只作上述空间／实体重建，无额外时间演化。')+'无本题未列数据、选项、模型或隐藏默认值。'
   records=[]
   where=dict(cells='cells完整体域，恰一条',domain='domain全部节点，恰一条',boundary_nodes='上述闭包规则的外边界节点集，可多条',facets='外面元素集，可多条',floating='上述闭包规则的浮置节点集，可多条',nodes='nodes全部节点，恰一条',branches='branches非空支路子集，可多条，同算子也可分组',coil='coil唯一实体，恰一条')
   for op,r in c['records'].items():
    records.append(f'### `{op}`\n\nrole=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`；location为{where[r["where"]]}。'+('必须出现。' if r['required'] else '可不出现。')+'data恰含以下全部键：\n\n| 键 | 类型、单位、含义 |\n|---|---|\n'+'\n'.join(f'| `{k}` | {description(s)}'+('；static' if tr and (r['static'] or s.get('static')) else '')+' |' for k,s in r['data'].items()))
   outs=[]
   for q,s in c['outputs'].items():
    w=s['where'];site='nodes全部节点，point' if w=='nodes' else 'branches全部支路，point' if w=='branches' else '每条floating的完整节点集，point；每条必须请求' if w=='floating' else 'coil唯一实体，point' if w=='coil' else 'cells或非空体单元子集，average'
    outs.append(f'| `{q}` | {description(s)} | {site} |')
   obs='电路量为离散实体值，无空间插值或几何平均。' if circuit else ('体单元按实际体积' if d==3 else '体单元按实际三角面积')+'积分再除体积／面积，不得把点值当作积分平均；在所用场表示下与积分严格等价的重心值、节点均值或求积公式允许使用。'+('焦耳损耗先逐点计算再平均，不能从平均场平方得到。' if 'joule_loss' in c['outputs'] else '')
   size='2..33节点、1..64支路。' if circuit else ('至多1800四面体、6000节点。' if d==3 else '至多5000三角形、6000节点。')
   admit='正式数据须独立核验几何与材料适用、源及初边值相容、正则／唯一响应、观测存在和预算内精度；校验器不证明这些性质。'
   if not tr:admit=admit.replace('源及初边值相容','源及边界条件相容')
   if circuit:admit=admit.replace('几何与材料适用','元件适用')
   if tr:admit+='电路response若等于加载折点，连续节点电压／支路电压／电流取其唯一连续值；合法数据排除这些量跳跃或冲激。' if circuit else ''
   frame_limit='每轴至多129帧' if tr else '唯一时间轴含1帧'
   (td/'DATA.md').write_text(f'# {slug} 数据契约\n\n入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰为model、parameters；model=`electromagnetic-{slug}-v1`，task可省略，出现须为`{slug}`。禁止profile、contract_version、analysis或materials混用；不能以题号补物理。\n\n## 物理定义\n\n'+physics+'\n\n## 全局参数\n\nparameters恰含下表项，每项只有value和unit；有限实数，布尔不能作数值，整数须JSON整数。空表表示parameters={}。\n\n| 参数 | 单位 | 含义与范围 |\n|---|---|---|\n'+'\n'.join(f'| `{k}` | `{s["unit"]}` | {s["meaning"]} |' for k,s in c['parameters'].items())+'\n\n## 几何和身份\n\n'+geometry+'\n\n## 时间、数组与重建\n\n'+times+'\n\n'+fields+'\n\n## 条件全集\n\n'+'\n\n'.join(records)+'\n\n## 输出\n\n逻辑名与array key自由，每个quantity至少出现一次，可重复请求；全部float64，无sampling，时间轴为'+axis+'，shape及components遵守前述规则。\n\n| quantity | 类型、单位与含义 | 位置与value_kind |\n|---|---|---|\n'+'\n'.join(outs)+'\n\n'+obs+'结果仅含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标或新网格。\n\n## 接收限制\n\n'+size+frame_limit+'，输入场和输出场各至多4000000数值分量。'+admit+'结构合法不代表电磁结果正确。\n')
   tol='\n'.join(f'| `{q}` | {s["atol"]} | {s["rtol"]} | `{s["unit"]}` |' for q,s in c['outputs'].items())
   (td/'instruction.md').write_text(f'# {num} {c["name"]}\n\n实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。'+physics+'\n\n'+('元件、源、拓扑及观测由算例变化。' if circuit else '几何、材料、源及观测由算例变化。')+'考生负责相容实现、内部离散／积分、线性代数与误差控制，语言和软件自由；覆盖整个契约的解析或降阶方法同样有效，不要求复制参考程序。仅需[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)确定输入输出。\n\n## 运行与资源\n\n'+size+frame_limit+'，输入／输出场各至多4000000分量。规模、预算及容差为待校准设计目标，正式数据须独立证明可达精度。\n\n'+f'入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{c["timeout"]}秒墙钟（含启动和I/O）、4CPU、8192MB、0GPU，逐例无网络；程序0退出并完成HDF5写入，无独立字节上限。生成求解器3600秒、构建1800秒；提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5，不强制Python。\n\n## 评分\n\n每有效例正常退出、结构合法且全部quantity的所有时刻／实体／分量满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分，等号接受。'+('复量实虚分别比较，不调整全局相位、不用幅值或RMS替代。' if harm else '')+'无去均值、拟合或超限豁免。\n\n| quantity | atol | rtol | 单位 |\n|---|---|---|---|\n'+tol+'\n\n成绩为通过有效例数／有效例数；输入、配置或参考错误为基础设施错误，不计考生失败；无有效例不产生成绩。结构和有限值遵守CONTRACT；容差与资源须正式评测前校准，工具测试不构成物理精度证据。\n')
   (td/'author').mkdir(parents=True,exist_ok=True)
   (td/'author/grading-template.json').write_text(json.dumps(dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()}),indent=2)+'\n')
   (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
   (td/'harbor').mkdir(exist_ok=True);(td/'harbor/requirements.txt').write_text('scipy==1.18.1\n');(td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 4\nmemory_mb = 8192\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
  (sd/'README.md').write_text(f'# {sec.split("-")[0]} {title}\n\n'+'\n'.join(links)+'\n');toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
 (CH/'README.md').write_text('# 第七章 电磁场与电路分析\n\n7节10题，考生只依赖本题instruction、DATA与CONTRACT。正式数据、参考及发布留后。\n\n'+'\n'.join(toc)+'\n\n维护：[章规划](../design/chapter-07-electromagnetics.md)、[清单](../design/chapter-07-task-plan.md)、[进度](../design/reviews/chapter-07-progress.md)。\n')
if __name__=='__main__':main()
