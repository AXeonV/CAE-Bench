"""Expand independent optical problem contracts/configuration; no case generator."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parents[3];CH=ROOT/'qbank/08-optics'
SECTIONS=[('8.1-geometrical','几何光学',['layered-rays']),('8.2-coherence','相干与干涉',['coherent-interference','partial-coherence']),('8.3-diffraction','标量衍射',['fresnel-aperture','farfield-aperture']),('8.4-polarization','偏振',['jones-chain']),('8.5-layered-media','层状介质',['thin-film']),('8.6-guided-optics','导波光学',['slab-modes'])]
NAMES=['平行分层介质射线','单频相干光干涉','部分相干光强','有限孔径近轴衍射','有限孔径角分布衍射','被动偏振元件链','多层薄膜相干响应','分层平板导波模态']
def S(u,m,**kw):return dict(kind='scalar',shape=[1],unit=u,meaning=m,**kw)
def V(u,m):return dict(kind='vector',shape=[3],unit=u,meaning=m)
def C(sh,u,m):return dict(kind='components',shape=sh,unit=u,meaning=m)
def Z(u,m):return C([2],u,m)
def P(u,m,**kw):return dict(unit=u,meaning=m,**kw)
M={}
for slug,name in zip([s for _,_,ss in SECTIONS for s in ss],NAMES):
 aperture=slug.endswith('aperture');rays=slug=='layered-rays';c=dict(name=name,spatial_dimension=3 if aperture or rays or 'coherence' in slug or slug=='coherent-interference' else 1,mesh=aperture,parameters={},records={},outputs={},locations={},timeout=900 if slug=='fresnel-aperture' else 1200 if slug=='slab-modes' else 600 if aperture else 300 if slug=='thin-film' else 180)
 def entity(name,minimum,maximum,meaning):c['locations'][name]=dict(kind='entities',minimum=minimum,maximum=maximum,meaning=meaning)
 def points(name,meaning):c['locations'][name]=dict(kind='points',minimum=1,maximum=256,meaning=meaning)
 def rec(op,role,var,location,data):c['records'][op]=dict(role=role,variable=var,location=location,data=data)
 def out(q,s,location,atol=1e-6,rtol=.005):c['outputs'][q]=dict(s,location=location,atol=atol,rtol=rtol)
 if slug!='jones-chain' and not rays:c['parameters']['wavelength']=P('m','真空波长λ0>0',positive=True)
 if slug in ('coherent-interference','partial-coherence','fresnel-aperture','farfield-aperture'):
  c['parameters'].update(refractive_index=P('1','均匀背景折射率n>0',positive=True),impedance=P('Ohm','背景波阻抗Z>0；仅用于给定强度归一化',positive=True))
 if rays or slug in ('thin-film','slab-modes'):
  entity('layers',1,32,'按IDs行序沿正轴排列的有限层；ID本身不表示厚度或坐标')
  rec('layers','material','optical_layer','layers',dict(index=S('1','各层实折射率n>0',positive=True),thickness=S('m','各层厚度h>0',positive=True)))
 if rays:
  c['parameters'].update(input_index=P('1','z<0的入射介质n0>0',positive=True),output_index=P('1','z>H的出射介质nout>0',positive=True));entity('rays',1,128,'各独立入射射线')
  rec('launch','source','ray','rays',dict(origin=V('m','在z=0的起点'),direction=V('1','入射单位方向，d_z≥1e−4')))
  out('terminal_position',V('m','终点坐标'),'rays',1e-8,0);out('terminal_direction',V('1','终点方向'),'rays',1e-8,0);out('optical_path',S('m','从发射到终止的∫n ds'),'rays',1e-8,1e-6);out('termination',S('1','0=成功出射，1=首次全反射后终止'),'rays',0,0)
 elif slug in ('coherent-interference','partial-coherence'):
  c['parameters']['wave_count']=P('1','模态数w，JSON整数1..32',integer=True,lower=1,upper=32);entity('waves',1,32,'恰w个平面波，IDs固定0..w−1，矩阵索引按此顺序');points('receivers','真实三维接收点')
  data=dict(direction=V('1','单位传播方向d_j'),reference=V('m','每个模式的相位参考点r_j'))
  if slug=='coherent-interference':data['amplitude']=Z('V/m','参考点处复振幅a_j')
  rec('waves','source','optical_wave','waves',data)
  if slug=='partial-coherence':
   entity('ensemble',1,1,'唯一随机系综参数对象');rec('coherence','material','covariance','ensemble',dict(value=C(['w','w',2],'V2/m2','C_jl=E[c_j c_l*]；Hermitian半正定，完整矩阵，含对角与非对角')))
  else:out('amplitude',Z('V/m','相干标量复场U'),'receivers')
  out('intensity',S('W/m2','平均强度'),'receivers',1e-8)
 elif aperture:
  c['locations'].update(domain=dict(kind='mesh',entity='node',meaning='孔径全部节点'),aperture=dict(kind='mesh',entity='element',dimension=2,meaning='孔径全部三角形'))
  rec('aperture_field','source','amplitude','aperture',dict(value=Z('V/m','输入孔径复场U0，逐三角形常值，孔径外为0')))
  if slug=='fresnel-aperture':points('receivers','真实三维接收点，z>0');out('amplitude',Z('V/m','有限距离复场U'),'receivers');out('intensity',S('W/m2','|U|²/(2Z)'),'receivers',1e-8)
  else:
   entity('directions',1,256,'出射方向对象，无空间接收距离');rec('directions','source','direction','directions',dict(value=V('1','单位出射方向s，s_z≥1e−4')))
   out('far_amplitude',Z('V','远场系数A(s)'),'directions',1e-8);out('radiant_intensity',S('W/sr','每单位立体角功率|A|²/(2Z)'),'directions',1e-9)
 elif slug=='jones-chain':
  c['parameters']['impedance']=P('Ohm','背景波阻抗Z>0',positive=True);entity('elements',1,64,'同一固定xy横向基底下的有序Jones元件，按IDs行序依次作用');entity('states',1,64,'彼此独立的输入偏振态')
  rec('elements','material','jones_matrix','elements',dict(value=C([2,2,2],'1','复Jones矩阵J；J†J≼I，被动无增益')))
  rec('states','source','jones','states',dict(value=C([2,2],'V/m','Ex、Ey复振幅，最内层实虚')))
  out('jones',C([2,2],'V/m','输出Ex、Ey复振幅'),'states');out('stokes',C([4],'V2/m2','按S0,S1,S2,S3顺序'),'states',1e-7);out('intensity',S('W/m2','S0/(2Z)'),'states',1e-8)
 elif slug=='thin-film':
  c['parameters'].update(input_index=P('1','入射半空间实折射率n0>0',positive=True),output_index=P('1','出射半空间实折射率ns>0',positive=True),vacuum_impedance=P('Ohm','真空波阻抗Z0>0',positive=True),incidence_sine=P('1','sinθ0，0≤s<1',lower=0,upper_exclusive=1),polarization=P('1','JSON整数0=TE，1=TM',integer=True,lower=0,upper=1));entity('system',1,1,'唯一完整层系对象')
  for q in ('reflection','transmission'):out(q,Z('1','固定切向电场基底的复振幅系数r' if q=='reflection' else '固定切向电场基底的复振幅系数t'),'system',1e-7,.002)
  for q in ('reflectance','transmittance'):out(q,S('1','功率反射率R' if q=='reflectance' else '功率透射率T'),'system',1e-8,.002)
 elif slug=='slab-modes':
  c['parameters'].update(left_index=P('1','x<0包层折射率nL>0',positive=True),right_index=P('1','x>H包层折射率nR>0',positive=True),polarization=P('1','JSON整数0=TE(Ey)，1=TM(Hy)',integer=True,lower=0,upper=1),mode_count=P('1','请求m个导模，JSON整数1..8；数据保证至少存在m个',integer=True,lower=1,upper=8));entity('modes',1,8,'恰m个导模，IDs固定0..m−1，对应neff从大到小');points('receivers','真实横向采样点(x,0,0)，可在芯层或包层')
  out('effective_index',S('1','neff=β/k0，按从大到小排序'),'modes',1e-7,0);out('mode_profile',C(['m'],'m^(-1/2)','所有m个实归一化剖面；分量顺序同modes IDs'),'receivers',1e-5,.005)
 M[slug]=c
PHYS={
'layered-rays':'三维射线在平行平面分层介质中传播，层沿+z依次排列，界面z=0,h1,h1+h2,…,H；上下半空间折射率n0和nout。每条射线从z=0处向+z入射，按Snell定律保持界面切向n d连续，透射方向法向分量取正。若首个不能透射的界面发生全反射，将法向方向反号，终点为该界面交点，并立即终止，不再追踪反射支路；termination=1。若通过全部层及z=H出口，终点为H面交点、方向为出射介质透射方向，termination=0。首次入射界面全反射时终点仍为起点、光程0。累计光程只计已走过的有限层内∫n ds，不含上下半空间距离。允许偏折、全反射，不计算Fresnel功率分裂、相干相位或偏振。对所有潜在界面，q=n0²(dx²+dy²)，须满足|q/n_target²−1|≥1e−8，排除临界／掠射退化。',
'coherent-interference':'均匀介质单频标量固定偏振近似，e^(+iωt)，k=2πn/λ0。U(r)=Σ_j a_j exp[−ik d_j·(r−r_j)]，I=|U|²/(2Z)。各波完全相干，共用固定相位参考约定，不逐波强度相加，不另作方向相关矢量偏振投影。Z显式给定用于强度归一化，振幅为峰值相量而非RMS。',
'partial-coherence':'均匀介质单频标量固定偏振近似，e^(+iωt)，k=2πn/λ0。随机模式系数c_j的完整二阶矩C_jl=E[c_j c_l*]由输入给定，C为Hermitian半正定；不假定模态独立，也不另加未给定均值。令b_j(r)=exp[−ik d_j·(r−r_j)]，平均强度I(r)=Σ_jl C_jl b_j(r)b_l(r)*/(2Z)，结果为实数。只求统计强度，不要求输出一次随机场或虚构确定相位。无需随机抽样，不能删除非对角相关项。',
'fresnel-aperture':'均匀背景中的单频标量近轴Fresnel模型，e^(+iωt)，介质波长λ=λ0/n，k=2π/λ。输入z=0有限孔径复场U0，孔径外为0。对r=(X,Y,z)、z>0，U(r)=exp(−ikz)/(−iλz) ∫孔径 U0(x,y) exp[−ik((X−x)²+(Y−y)²)/(2z)] dxdy，I=|U|²/(2Z)。这一定义固定近轴模型，不替换为Fraunhofer、球面Green全波或光线投射；正式数据须核验近轴适用。',
'farfield-aperture':'均匀背景中的指定标量角分布衍射模型，e^(+iωt)，λ=λ0/n，k=2π/λ。z=0有限孔径上U0、孔径外0。对单位出射方向s且s_z>0，A(s)=i s_z/λ ∫孔径 U0(x,y) exp[+ik(s_x x+s_y y)] dxdy。远处U(Rs)~A(s)exp(−ikR)/R，A单位V。radiant_intensity=|A|²/(2Z)，单位W/sr；这是每立体角功率，不是某个虚构距离的W/m²点强度。倾斜因子明确为s_z，不另选标量边界近似。',
'jones-chain':'固定共同横向xy基底、单频e^(+iωt)峰值Jones向量e=(Ex,Ey)。各元件矩阵已给定，按elements的IDs行序先J1后J2…作用，eout=JN…J2J1 ein；矩阵在同一基底，无隐含旋转、传播相位或基底重置。J†J≼I，只含确定、无去偏振的被动元件。对输出定义S0=|Ex|²+|Ey|²，S1=|Ex|²−|Ey|²，S2=2Re(Ex Ey*)，S3=2Im(Ex Ey*)，I=S0/(2Z)。S3的符号以此公式为准，不借左／右旋名称猜测；不归一化Stokes、不丢弃总强度或全局相位。',
'thin-film':'平行无限层，z<0入射半空间、各实正折射率层及z>H出射半空间；无吸收、增益、磁性或粗糙面，e^(+iωt)。令p=n0 sinθ0，cosθ_j=√(1−p²/n_j²)>0，kz_j=(2π/λ0)n_j cosθ_j。TE取切向Ey，TM取固定全局切向Ex；反射也使用同一笛卡尔基底，不随传播方向翻转。相应光学导纳TE为Y_j=n_j cosθ_j/Z0，TM为Y_j=n_j/(Z0 cosθ_j)。每层切向场E=F exp(−ikz_j(z−z_left))+B exp(+ikz_j(z−z_left))，配对切向场G（不取复共轭）=Y_j(F exp(−ikz_j(z−z_left))−B exp(+ikz_j(z−z_left)))，各界面E和G连续。入射E振幅1，在z=0定义r，出射仅+z波，在z=H定义t；不把t再传播到其他参考面。R=|r|²，T=(Ys/Y0)|t|²。所有层及出射介质须p²/n_j²≤1−1e−8，排除倏逝和临界入射；不独立相加各界面反射强度，须保留多次反射相干。',
'slab-modes':'无耗非磁性平板沿z导波，折射率只依赖x：x<0为nL，有限层按厚度排列于[0,H]，x>H为nR。e^(+iωt−iβz)，k0=2π/λ0，β>0。TE剖面f=Ey满足f\'\'+(k0²n²−β²)f=0且f、f\'连续；TM剖面f=Hy满足(n^−2 f\')\'+(k0²−β²/n²)f=0且f、n^−2 f\'连续。两端为真正无限包层的指数衰减，不用有限箱体零边界代替。只求β/k0>max(nL,nR)的实导模，按neff从大到小取前m个；数据保证至少m个且远离截止，模态简单无排序简并。每个剖面为实，∫全实轴 f² dx=1，包含无限包层尾部，且f(0)>0定相；输出为归一化剖面，单位m^(−1/2)，不冒充物理场振幅或单位功率模态。receivers只用横坐标x，y=z=0。'
}
def description(s):return f'{s["kind"]} {s["shape"]}，`{s["unit"]}`；{s["meaning"]}'+('；严格正' if s.get('positive') else '')
def main():
 ext=ROOT/'qbank/extensions/caeoj_ext/optics';ext.mkdir(parents=True,exist_ok=True);(ext/'models.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n');toc=[]
 for sec,title,slugs in SECTIONS:
  sd=CH/sec;sd.mkdir(parents=True,exist_ok=True);links=[]
  for i,slug in enumerate(slugs,1):
   c=M[slug];td=sd/slug;td.mkdir(exist_ok=True);num=sec.split('-')[0]+'.'+str(i);axis='steady' if slug=='layered-rays' else 'optical';links.append(f'- [{num} {c["name"]}]({slug}/instruction.md)')
   locations=[]
   for name,s in c['locations'].items():
    locations.append(f'| `{name}` | '+('main的全部'+('节点' if s['entity']=='node' else '一阶三角形单元，dimension=2') if s['kind']=='mesh' else f'{s["kind"]}，{s["minimum"]}..{s["maximum"]}个')+'；'+s['meaning']+' |')
   geo='spatial_dimension='+str(c['spatial_dimension'])+'，固定坐标为m。locations恰为下表，无其他位置。entities为真实离散对象，IDs非负严格递增；不按ID数值猜坐标或物理参数。points为真实坐标且不能伪装成entities。'
   if 'layers' in c['locations']:geo+='层按layers IDs的数组行序沿正轴排列。'
   if slug=='jones-chain':geo+='元件按elements IDs的数组行序依次作用。'
   if c['mesh']:geo+='meshes恰为main，MSH4.1 ASCII，只含z=0的非退化一阶三角形type2，至多800三角形、4000所用节点；不导出边界线、点或其他单元，无未用节点、重叠或自交，允许孔洞和互不接触的孔径片。domain及aperture须完整；geometries若给仅作来源，求解几何以网格为准。'
   else:geo+='meshes及geometries必须为空，无隐藏空间网格。spatial_dimension为物理维数或分层／有限维系统的协议标记，不引入额外空间方程。'
   if slug=='fresnel-aperture':geo+='所有receivers的z>0，且z至少1e−8倍孔径包围盒对角线。'
   if slug=='slab-modes':geo+='receivers.coordinates实际为[N,1]，只存x；(x,0,0)仅表示物理嵌入，y=z=0不占HDF5列。'
   fields='所有输入场和输出场均float64，IDs为int64，时间轴按CONTRACT为float64。场数组[T,N,*component_shape]不省略轴。scalar固定[1]及components=["value"]；'
   kinds={s['kind'] for r in c['records'].values() for s in r['data'].values()}|{s['kind'] for s in c['outputs'].values()}
   if 'vector' in kinds:fields+='vector固定[3]及x/y/z；'
   if 'components' in kinds:fields+='components按表中shape行优先展平为c1..cL；复量最内层2依次实／虚，不用复数dtype或幅相。'
   if slug=='jones-chain':fields+='Stokes为实[4]数组，不增加复轴。'
   if slug=='slab-modes':fields+='表中m代入mode_count，实剖面shape=[m]，第j分量对应modes ID j。'
   if slug=='partial-coherence':fields+='表中w代入wave_count，矩阵shape=[w,w,2]，前两轴对应waves IDs。'
   fields+='条件data引用fields逻辑名，该对象的array才是HDF5 key，两者名称自由。fields恰为实际引用项；quantity等于data键名，value例外等于条件variable。字段必须与条件同location，不能按相同长度借别处数据。scalar data可用同单位有限实数value/unit常量或显式field，非scalar类型只能field，不允许内联数组。'
   fields+='输入sampling必须显式：time=constant、extrapolation=forbid，entities的space=uniform、value_kind=point'+('；孔径元素space=piecewise_constant、value_kind=average，表示每片唯一常值；domain节点不接受输入场。' if c['mesh'] else '。')+'不作实体间插值或隐藏时间演化。'
   if 'vector' in kinds:fields+='所有声明为单位方向的输入字段均须|norm(d)−1|≤1e−12；公式按原存储分量求值，不由考生归一化。此规则不作用于带长度单位的坐标。'
   if slug=='partial-coherence':fields+='C为完整二阶矩而非减去均值的中心协方差；公式按存储值计算，取二重和的实部以除去浮点虚残量，不投影矩阵。生产数据保证Hermitian半正定；浮点声明检查令ε=1e−12·max(1,||C||F)，要求max_jl|C_jl−C_lj*|≤ε，且Hermitian部分(C+C†)/2的最小特征值≥−ε；仅用于诊断，不改变原矩阵，不构成物理性证明。'
   if slug=='jones-chain':fields+='矩阵value[0,e,a,b,0/1]为J_ab实／虚部，a为输出x/y、b为输入x/y；检查最大奇异值≤1+1e−12，生产数据保证J†J≼I；不归一化或修正矩阵。'
   records=[]
   for op,r in c['records'].items():records.append(f'### `{op}`\n\nrole=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`，location=`{r["location"]}`；恰一条覆盖完整该位置。data恰含下表全部键：\n\n| 键 | 类型、单位和含义 |\n|---|---|\n'+'\n'.join(f'| `{k}` | {description(s)} |' for k,s in r['data'].items()))
   outputs='\n'.join(f'| `{q}` | {description(s)} | `{s["location"]}`全部对象，point |' for q,s in c['outputs'].items())
   alltime='time_axes恰含键'+axis+'，其引用的float64[1]数组为[0.0]，所有输入和输出只引用该轴。0仅为'+('静态' if slug=='layered-rays' else '单频／状态')+'存储标记，不是物理初态或频谱轴。'
   limits='孔径至多800三角形、4000节点，其他对象数量按DATA各表；' if c['mesh'] else '离散对象'+('及接收点' if any(s['kind']=='points' for s in c['locations'].values()) else '')+'数量按DATA各表；'
   admit='正式数据须独立核验本题模型适用、参数相容、所请求观测存在、参考精度与预算内可达性；校验器只检查声明，不证明物理或数值准确性。'
   if c['mesh']:admit+='孔径几何须独立核验无重叠／自交。'
   if slug=='jones-chain':admit+='零态、零矩阵及理想偏振片允许，不把被动性误解为可逆性。'
   if slug=='slab-modes':admit+='有限层最大折射率须严格大于两包层；模态存在数量、截止距离和谱间隔须由数据制作独立核验，不能由给定mode_count假称已证明。'
   (td/'DATA.md').write_text(f'# {slug} 数据契约\n\n入口problem.json和data_file引用的扁平HDF5，路径相对清单。physics恰含model、parameters；model=`optics-{slug}-v1`，task可省略，出现须为`{slug}`。禁止profile、contract_version、analysis、materials混用；不接受未列条件、字段或组合。\n\n## 物理定义\n\n'+PHYS[slug]+'\n\n## 全局参数\n\nparameters恰含下表全部项，每项只有value和unit，数值有限，布尔不能作数值，整数须JSON整数。\n\n| 参数 | 单位 | 含义与范围 |\n|---|---|---|\n'+'\n'.join(f'| `{k}` | `{s["unit"]}` | {s["meaning"]} |' for k,s in c['parameters'].items())+'\n\n## 几何、对象和身份\n\n'+geo+'\n\n| location | 完整支持与含义 |\n|---|---|\n'+'\n'.join(locations)+'\n\n## 时间、数组与重建\n\n'+alltime+'\n\n'+fields+'\n\n## 条件全集\n\n'+'\n\n'.join(records)+'\n\n## 输出\n\n每个quantity至少出现一次，可重复请求；逻辑名和array key自由，但不得改变quantity、单位或位置。全部float64，无sampling，shape和components按上述规则，均引用'+axis+'。\n\n| quantity | 类型、单位和含义 | 完整位置与value_kind |\n|---|---|---|\n'+outputs+'\n\n结果HDF5只含输出array及所需IDs／时间轴，严格复制输入身份与行序，不导出输入场、坐标、新网格或额外数组。\n\n## 接收限制\n\n'+limits+'唯一时间轴1帧；全部输入／输出场各至多2000000数值分量。'+admit+'\n')
   tol='\n'.join(f'| `{q}` | {s["atol"]} | {s["rtol"]} | `{s["unit"]}` |' for q,s in c['outputs'].items())
   (td/'instruction.md').write_text(f'# {num} {c["name"]}\n\n实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。'+PHYS[slug]+'\n\n本题输入对象及其参数随算例变化。考生负责覆盖完整契约的数值实现和误差控制，语言与软件自由；覆盖完整契约的解析或降阶方法同样有效，不要求复现参考算法。仅需[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)定义输入输出。\n\n## 运行与资源\n\n'+limits+'唯一存储轴1帧，输入／输出场各至多2000000分量。规模、容差和预算为待校准设计目标，正式数据须独立验证预算内可达精度，不声称任意结构合法参数都可在同一预算求准。\n\n'+f'入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{c["timeout"]}秒墙钟（含启动与I/O）、2CPU、4096MB、0GPU，逐例无网络；程序0退出并写完HDF5，无独立字节上限。生成求解器3600秒、构建1800秒；提前提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5，不强制Python。\n\n## 评分\n\n每有效例正常退出、结构合法且所有quantity的全部对象／分量满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分，等号接受。'+('复量实虚独立比较，无全局相位旋转或振幅拟合。' if any(s['kind']=='components' and s['shape'][-1]==2 for s in c['outputs'].values()) else '')+'无去均值、归一化重排或超限豁免。'+('模态必须遵守题定排序及定相。' if slug=='slab-modes' else '')+'\n\n| quantity | atol | rtol | 单位 |\n|---|---|---|---|\n'+tol+'\n\n成绩为通过有效例数／有效例数；输入、配置或参考错误为基础设施错误，不计考生失败，无有效例不产生成绩。结构与有限值遵守CONTRACT。工具验证不构成光学精度、模型适用性或资源校准证据。\n')
   (td/'grading.json').write_text(json.dumps(dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()}),indent=2)+'\n')
   (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
   (td/'harbor').mkdir(exist_ok=True);(td/'harbor/requirements.txt').write_text('scipy==1.18.1\n');(td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 2\nmemory_mb = 4096\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
  (sd/'README.md').write_text(f'# {sec.split("-")[0]} {title}\n\n'+'\n'.join(links)+'\n');toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
 (CH/'README.md').write_text('# 第八章 光学与光子学分析\n\n6节8题；考生只依赖本题instruction、DATA和通用CONTRACT。正式数据、参考和发布留后。\n\n'+'\n'.join(toc)+'\n\n维护：[章规划](../design/chapter-08-optics.md)、[清单](../design/chapter-08-task-plan.md)、[进度](../design/reviews/chapter-08-progress.md)。\n')
if __name__=='__main__':main()
