"""Maintainer-only finite catalog and self-contained statement renderer.

No case data, reference solutions, or public solver dependency is generated.
Run from repository root; --batch selects a section range.
"""
from pathlib import Path
from caeoj_tools.author import public_model_catalog
import argparse
import json

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = json.loads((ROOT/'qbank/maintenance/solid-plan.json').read_text())
CAT = {}
Q = {
 'displacement':('m','vector',1e-6,'nodes','位移u，参考全局坐标分量'),
 'stress':('Pa','tensor',100.,'cells','Cauchy应力；小应变时等同线性应力，完整对称矩阵'),
 'energy':('J','scalar',1e-5,'sum','参考域上弹性储能积分'),
 'deflection':('m','scalar',1e-6,'nodes','沿正横向的挠度w'),
 'slope':('rad','scalar',1e-5,'nodes','梁截面转角dw/dx'),
 'axial_force':('N','scalar',.01,'cells','轴向内力，受拉为正'),
 'bending_moment':('N.m','scalar',.01,'cells','梁弯矩EI·w″，按长度平均'),
 'curvature':('1/m','tensor',1e-5,'cells','板曲率张量−Hessian(w)，全局xy完整矩阵'),
 'velocity':('m/s','vector',1e-5,'nodes','位移对物理时间导数'),
 'frequency':('Hz','spectrum',1e-3,'mean','前k个正固有频率，升序，重数保留'),
 'displacement_real':('m','vector',1e-6,'nodes','复位移幅实部'),
 'displacement_imag':('m','vector',1e-6,'nodes','复位移幅虚部'),
 'stress_real':('Pa','tensor',100.,'cells','复应力幅实部'),
 'stress_imag':('Pa','tensor',100.,'cells','复应力幅虚部'),
 'load_factor':('1','scalar',1e-4,'mean','首个正屈曲载荷倍率'),
 'contact_pressure':('Pa','scalar',100.,'contact','刚性障碍对固体的压应力大小p≥0，非接触处0'),
 'contact_traction':('Pa','vector',100.,'contact','刚性障碍对固体的总接触牵引，包含法向与切向'),
 'plastic_strain':('1','tensor',1e-5,'cells','完整小应变塑性应变，不是工程剪切'),
 'equivalent_plastic_strain':('1','scalar',1e-5,'cells','累积等效塑性应变p'),
 'branch_stress':('Pa','tensor',100.,'cells','Maxwell偏支的偏应力q'),
 'creep_strain':('1','tensor',1e-5,'cells','完整偏蠕变应变张量'),
 'damage':('1','scalar',1e-4,'nodes','不可逆连续损伤d∈[0,1]'),
 'opening':('m','scalar',1e-6,'interface','界面正法向张开量，按初始界面长度平均'),
 'cohesive_traction':('Pa','scalar',100.,'interface','内聚拉应力T，按初始界面长度平均'),
 'fatigue_damage':('1','scalar',1e-4,'sites','已累计Miner损伤，可大于1，不截断'),
 'crack_length':('m','scalar',1e-6,'sites','给定一维裂纹路径上的标量裂长a')}
# parameter: unit, lower (exclusive unless flagged), upper inclusive, description.
def p(unit,lo=None,hi=None,desc='',closed=False):return dict(unit=unit,lower=lo,upper=hi,closed=closed,description=desc)
EL={'young_modulus':p('Pa',0,desc='Young模量E'), 'poisson_ratio':p('1',-1,.49,'Poisson比ν，严格小于0.5')}
TIME={'start_time':p('s',desc='初始时刻t0'), 'end_time':p('s',desc='末时刻tf，严格大于t0')}
# value: unit, kind, quantity, location class, description; constants only for scalars.
def v(unit,kind,quantity,where,desc):return dict(unit=unit,kind=kind,quantity=quantity,where=where,description=desc)
BC={'displacement':('boundary','displacement','nodes',{'value':v('m','vector','displacement','nodes','位移向量；所有分量均被约束')},'给定全部位移分量，边界P1迹；同一节点只允许一条位移记录'),
 'traction':('boundary','traction','facets',{'value':v('Pa','vector','traction','facets','外界对固体牵引t=σn')},'在参考边界实体上分片常数；未声明的外边界为零牵引'),
 'body_force':('source','body_force','cells',{'value':v('N/m3','vector','body_force','cells','每参考体积的外力')},'按输入单元分片常数；必须一条覆盖cells，零载也须给出')}
def make(slug,d,mode,outs,params=None,rules=None,required=None,detail='',top=None):
 cfg=dict(slug=slug,dimension=d,topology=d if top is None else top,mode=mode,outputs=outs,
          parameters={**EL,**(params or {}),**(TIME if mode=='history' else {})},rules=rules or dict(BC),
          required=required or ['body_force'],detail=detail)
 CAT[slug]=cfg;return cfg
for slug,dim,desc in [('plane-stress',2,'平面应力σzz=σxz=σyz=0；ε= sym∇u，σ=2με+λps tr(ε)I，μ=E/[2(1+ν)]，λps=Eν/(1−ν²)。厚度只乘体积与边界积分，载荷仍为Pa和N/m3。'),('plane-strain',2,'平面应变εzz=εxz=εyz=0；σxy块=2με+λ tr(ε)I，μ=E/[2(1+ν)]，λ=Eν/[(1+ν)(1−2ν)]；σzz=λtr(ε)，输出stress只含xy块。所有力／能量按单位z长度。'),('elastic-solid-3d',3,'三维各向同性小应变；ε=sym∇u，σ=2με+λtr(ε)I，μ=E/[2(1+ν)]，λ=Eν/[(1+ν)(1−2ν)]。')]:
 make(slug,dim,'static',['displacement','stress','energy'],{'thickness':p('m',0,desc='实际恒定厚度h')} if slug=='plane-stress' else {},detail=desc+' 静力平衡divσ+b=0。体无初始应力、无本征应变、材料均匀；位移约束排除刚体模态。')
c=make('elastic-truss',2,'static',['displacement','axial_force'],rules={
 'displacement':BC['displacement'],
 'nodal_force':('source','force','nodes',{'value':v('N','vector','force','nodes','作用于节点的外力')},'同一节点的已声明力相加；未声明为0'),
 'cross_section':('material','area','cells',{'value':v('m2','scalar','area','cells','每杆横截面积A>0')},'必须一条覆盖全部杆，杆内常数')},required=['cross_section'],top=1,detail='输入为xy平面铰接直杆网络，节点共享tag表示铰接；交叉但不共享节点的杆不连接。忽略弯曲、剪切、自重和惯性。每杆轴向应变等于其两端位移差在初始杆轴的投影除以杆长；N=EAε，受拉为正；节点向量平衡。E全局，A每杆给定。支撑为全分量位移；不含机构、孤立节点或预应力。')
c['parameters'].pop('poisson_ratio')
beam_rules={
 'clamp':('boundary','deflection','ends',{'value':v('m','scalar','deflection','ends','端挠度'), 'rotation':v('rad','scalar','slope','ends','dw/dx')},'同时固定w与w′'),
 'end_load':('boundary','end_load','ends',{'force':v('N','scalar','force','ends','端横向集中力'), 'moment':v('N.m','scalar','moment','ends','与w′共轭的端弯矩')},'虚功Fδw+Mδw′；未声明端自由，默认F=M=0'),
 'line_load':('source','line_load','cells',{'value':v('N/m','scalar','line_load','cells','沿正横向的均布线载荷q')},'一条覆盖cells，每单元常数'),
 'flexural_rigidity':('material','rigidity','cells',{'value':v('N.m2','scalar','rigidity','cells','EI>0')},'一条覆盖cells，每单元常数')}
c=make('elastic-beam',1,'static',['deflection','slope','bending_moment'],rules=beam_rules,required=['line_load','flexural_rigidity'],detail='一根沿全局x轴严格递增的直梁，线性Euler–Bernoulli弯曲；横向w是抽象横向挠度而非x位移。连续方程(EIw″)″=q。跨单元w、w′及无集中力偶处内力连续。端力按虚功定义，右端F=−(EIw″)′、M=EIw″，左端符号相反。不求轴向伸长、扭转或剪切变形；恰有一个端点clamp，另一个端点可end_load。');c['parameters']={}
plate_rules={
 'plate_clamp':('boundary','deflection','facets',{'value':v('m','scalar','deflection','facets','挠度w=0'), 'slope':v('rad','scalar','normal_slope','facets','外法向导数∂nw=0')},'覆盖全部外边界；首版只支持齐次夹持，两个值必须均为零'),
 'pressure_load':('source','pressure','cells',{'value':v('Pa','scalar','pressure','cells','沿正z方向压力q')},'一条覆盖cells，单元内常数')}
make('elastic-plate',2,'static',['deflection','curvature'],{'thickness':p('m',0,desc='恒定厚度h')},plate_rules,['pressure_load','plate_clamp'],detail='各向同性Kirchhoff–Love薄板，参考中面xy，w沿+z；弯曲刚度D=Eh³/[12(1−ν²)]，DΔ²w=q。全边界w=∂nw=0；无膜力、横向剪切变形、剪切锁定的隐藏离散要求或转动惯性。评价连续板弯曲而非输入网格的有限元刚度矩阵；厚度满足薄板适用条件由算例保证。')
DYN={'density':p('kg/m3',0,desc='质量密度ρ')}
make('elastic-modes',3,'static',['frequency'],{**DYN,'mode_count':p('1',1,12,'正整数k，1≤k≤12',True)},
 {'fixed':('boundary','displacement','nodes',{'value':v('m','vector','displacement','nodes','齐次固定边界u=0')},'至少一条，全部值必须0')},['fixed'],detail='三维均匀各向同性小应变自由振动，divσ=ρü；约束排除刚体，未约束边界零牵引，无预应力与阻尼。求连续弹性问题前k个正固有频率f=ω/(2π)，升序排列并保留重数；不评分振型符号、归一化或重复特征值子空间中的基。')
for slug in ['elastic-transient','elastic-harmonic']:
 rules=dict(BC)
 params={**DYN,'mass_damping':p('1/s',0,desc='质量比例黏性阻尼α≥0',closed=True)}
 if slug=='elastic-transient':
  for q,u in [('displacement','m'),('velocity','m/s')]:rules['initial_'+q]=('initial',q,'nodes',{'value':v(u,'vector',q,'nodes','初始全域状态')},'恰一条覆盖domain；采样单帧t0，节点P1重建')
  make(slug,3,'history',['displacement','velocity','stress'],params,rules,['body_force','initial_displacement','initial_velocity'],detail='三维线弹性，ρü+αρu̇−divσ=b，ε=sym∇u，σ=2με+λtrεI，λ与μ由E、ν确定。无预应力；给定物理位移与速度初态，不能把迭代初猜当初态。位移边界随时间只允许全程仿射（多帧需共线），因此不含速度折点；初位移及速度与边界的起点值和全程导数相容，不施加脉冲载荷。体力和牵引仍可按一般连续分段线性历史给定。')
 else:
  rules={}
  for suffix in ['real','imag']:
   for key,(role,var,where,data,desc) in BC.items():
    value=dict(data['value']);value['quantity']=var+'_'+suffix
    rules[key+'_'+suffix]=(role,var+'_'+suffix,where,{'value':value},desc+'；'+suffix+'幅部')
  make(slug,3,'static',['displacement_real','displacement_imag','stress_real','stress_imag'],{**params,'angular_frequency':p('rad/s',0,desc='单个驱动角频率ω')},rules,['body_force_real','body_force_imag'],detail='三维线弹性谐响应，采用Re(û exp(iωt))；−ρω²û+iαρ ωû−divσ̂=b̂，σ̂=2μsym∇û+λtr(sym∇û)I。所有实虚载荷、位移边界分别给出且几何覆盖相同，缺失幅部不得猜零。阻尼α>0；避开病态共振。时间轴[0]只是复幅存储标记；没有启动瞬态或多频扫频。')
make('hyperelastic-solid',3,'history',['displacement','stress','energy'],detail='三维可压缩Neo-Hookean材料。F=I+Grad u，J=detF>0，W=μ/2(tr(FᵀF)−3)−μ lnJ+λ/2(lnJ)²，μ、λ由E、ν确定且ν≥0；P=∂W/∂F，DivP+b=0，σ=PFᵀ/J。牵引是参考面上的名义死载Pn，body_force是每参考体积死载；不支持随动压力。由t0零位移、零载荷无应力参考态沿连续局部稳定分支准静态加载，支撑位移控制、无极限点跳跃；伪时间仅为加载参数。不改变输入拓扑，允许内部更新几何。')
make('elastic-buckling',3,'static',['load_factor'],detail='三维小应变各向同性弹性结构；齐次支撑先解参考死载下的线弹性应力σ0。对同一齐次增量约束，求a(v,w)+λ gσ0(v,w)=0的最小正λ，a=∫ε(v):C:ε(w)dV，g=∫σ0_ij ∂i v_k ∂j w_k dV。总临界载荷为λ乘全部给定牵引和体力，不能乘支撑；位移条件必须全零。正根存在且隔离，不求后屈曲或振型，不含接触或材料失稳。')
plane={'normal_x':p('1',desc='平面单位法向nx'), 'normal_y':p('1',desc='平面单位法向ny'),'normal_z':p('1',desc='平面单位法向nz'), 'plane_offset':p('m',desc='平面n·x=c的c')}
for slug in ['frictionless-contact','frictional-contact']:
 rules=dict(BC);rules['rigid_plane']=('boundary','contact','facets',{'mode':dict(option='unilateral')},'声明候选外表面；不得同时作用位移或给定牵引；全候选面可分成多个互不重叠记录')
 extra=plane if slug=='frictionless-contact' else {**plane,'friction_coefficient':p('1',0,1,'库仑系数μf∈[0,1]',True)}
 make(slug,3,'history',['displacement','stress','contact_pressure','contact_traction'],extra,rules,['body_force','rigid_plane'],detail='三维小应变各向同性弹性准静态接触，平面刚性固定。允许区域n·(X+u)≤c；g=c−n·(X+u)≥0，p≥0，pg=0；障碍对固体法向牵引−pn。初态零位移零载荷，候选面g≥0，排除初始侵入；未声明边界零牵引，所有载荷在参考域定义；法向不随变形更新。'+('切向牵引严格为0，无黏附。' if slug=='frictionless-contact' else '相对切向速度vT=(I−n⊗n)u̇；|tT|≤μf p，滑动时tT=−μf p vT/|vT|，粘着时vT=0。初始切向接触力和滑移均0，按给定加载历史选择粘滑状态；开离时接触力为0。无正则化摩擦或罚刚度材料参数。')+' 支撑排除刚体自由度，保证连续唯一稳定解，无大滑动／转动或接触冲击。')
for slug,params,outs,detail in [
 ('j2-plasticity',{'yield_stress':p('Pa',0,desc='初始屈服应力σy'),'hardening_modulus':p('Pa',0,desc='各向同性硬化H')},['plastic_strain','equivalent_plastic_strain'],'εe=ε−εp，σ=C:εe；s=devσ，σeq=√(3s:s/2)，f=σeq−(σy+Hp)≤0，ε̇p=γ̇(3s/2σeq)，ṗ=γ̇，γ̇≥0，γ̇f=0；σeq=0时塑性流动为0。无运动硬化、有限应变或应变率效应。'),
 ('linear-viscoelastic',{'branch_shear_modulus':p('Pa',0,desc='Maxwell偏支剪切模量G1'),'relaxation_time':p('s',0,desc='偏支松弛时间τ')},['branch_stress'],'E、ν定义平衡弹簧K=E/[3(1−2ν)]、G∞=E/[2(1+ν)]；σ=K trε I+2G∞devε+q，q̇+q/τ=2G1 dev ε̇，q为偏应力；体积响应纯弹性。初始ε=q=0，禁止擅自把E解释成瞬时模量。'),
 ('power-law-creep',{'creep_rate':p('1/s',0,desc='应力参考尺度下速率A'),'reference_stress':p('Pa',0,desc='蠕变参考应力σr'),'creep_exponent':p('1',1,10,'幂指数n≥1',True)},['creep_strain'],'σ=C:(ε−εc)，s=devσ，σeq=√(3s:s/2)，ε̇c=(3/2)A(σeq/σr)^n s/σeq；σeq=0时导数0。蠕变无体积应变，不含屈服、硬化、损伤或温度方程。')]:
 make(slug,3,'history',['displacement','stress']+outs,params,detail='三维等温小应变材料，divσ+b=0，准静态加载卸载；C为E、ν确定的各向同性刚度。'+detail+' 从t0零位移、零应力、所有内部状态0开始，起始边界载荷0；输出在加载或卸载任意给定时刻的物理历史，不能逐帧重置状态。算例保证唯一稳定响应。')
make('gradient-damage',2,'history',['displacement','damage','energy'],{'fracture_energy':p('J/m2',0,desc='断裂能Gc'),'length_scale':p('m',0,desc='内部长度ℓ'),'residual_stiffness':p('1',0,1,'残余刚度η，严格0<η<1')},detail='二维平面应变，单位z长度；ε=sym∇u，ψ0=με:ε+λ(trε)²/2，g(d)=(1−η)(1−d)²+η。能量泛函E=∫[g(d)ψ0+Gc(d²/(2ℓ)+ℓ|∇d|²/2)]dA−外力势；本题是拉压对称正则化损伤，无张压谱分解，允许压缩损伤。t0的u=d=0、载荷0。u满足力平衡；d∈[0,1]、ḋ≥0，以每一时刻满足不可逆变分不等式的连续局部稳定分支演化，外边界∂nd=0。算例限定此分支唯一且无跳跃；不允许改成每步无历史全局最小值。energy输出含弹性储能及正则化裂纹能，不含外力势；不评价网格依赖局部软化。')
make('linear-elastic-fracture',2,'static',['displacement','stress','energy'],detail='二维各向同性平面应变，单位z长度，固定贯穿裂纹；裂纹由同坐标不同tag的裂面节点及不跨裂缝的三角网格显式给出，连通未断区仍共享节点。两侧无载裂面显式traction=0，裂面互不粘结、不发生接触，裂尖无人工钝化。线弹性小应变divσ+b=0。应力输出为裂尖邻域也有定义的单元积分平均，位移可含裂尖节点；不请求裂尖点应力、裂纹扩展路径或由离散能量差猜J积分。energy=∫ε:C:ε/2 dA。算例保证裂面张开、无相互穿透。')
cohrules=dict(BC);cohrules['cohesive_pair']=('boundary','interface','facets',{'partner':dict(location=True)},'一条minus界面与plus界面配对，按坐标逐顶点一一对应；禁止按行号配对')
make('cohesive-interface',2,'history',['displacement','stress','opening','cohesive_traction'],{
 'normal_x':p('1',desc='minus指向plus的单位法向nx'),'normal_y':p('1',desc='minus指向plus的单位法向ny'),
 'interface_stiffness':p('Pa/m',0,desc='初始法向刚度Kn'),'peak_traction':p('Pa',0,desc='峰值T0'), 'fracture_energy':p('J/m2',0,desc='界面开裂耗能Gc')},cohrules,['body_force','cohesive_pair'],detail='两个二维平面应变线弹性体，单位厚度；直线预设界面两侧几何重合、节点tag不同，无跨界单元。n从minus体指向plus体；δ=(uplus−uminus)·n≥0，切向位移跳跃为0（严格粘结），无压缩接触分支。δ0=T0/Kn，δf=2Gc/T0>δ0；κ=max历史δ，κ≤δ0时d=0，δ0<κ<δf时d=δf(κ−δ0)/[κ(δf−δ0)]，κ≥δf时d=1；T=(1−d)Knδ。minus体界面法向牵引+Tn、plus体−Tn；切向反力由零切向跳跃约束确定，反力在两体上大小相等方向相反，不强制为零；T只表示法向内聚牵引。卸载按已损伤割线回原点。起始u=κ=0，无牵引；载荷位移控制，保证唯一连续稳定、无回闭／压缩／跳跃分支。界面完全断开后切向仍严格约束，只评价给定纯I型问题族。')
fatigue_rules={'cycle_blocks':('source','fatigue','sites',{
 'amplitude':v('Pa','scalar','stress_amplitude','sites','已计数循环的非负幅值σa'),
 'mean':v('Pa','scalar','mean_stress','sites','均值σm，必须小于Su'),
 'rate':v('1/s','scalar','cycle_rate','sites','非负完整循环数率r，非反转数率')},'一条覆盖sites；每个时间区间是一块已计数恒幅循环，不执行雨流计数')}
c=make('stress-life-fatigue',2,'history',['fatigue_damage'],{'fatigue_strength':p('Pa',0,desc='Basquin参考强度S'),'fatigue_exponent':p('1',0,desc='指数m'),'ultimate_strength':p('Pa',0,desc='Goodman极限强度Su')},fatigue_rules,['cycle_blocks'],detail='给定每个真实材料观测点的完整循环块；σeff=σa/[1−max(σm,0)/Su]；σeff>0时破坏循环数N=(S/σeff)^m，σeff=0时损伤率0；D(t)=∫t0^t r/N dt，D(t0)=0。所有块只按输入次序累计，无序列效应、耐久极限、应力场重算或裂纹反馈。D允许超过1，D=1是本模型失效判据；本题只输出有限的累计损伤，不以无穷寿命作为HDF5值。观测点不承载网格求解。',top=0);c['parameters']={k:x for k,x in c['parameters'].items() if k not in EL}
crules={'initial_length':('initial','crack_length','sites',{'value':v('m','scalar','crack_length','sites','初始裂长a0，0<a0<width')},'一条覆盖sites，单帧t0'),
 'stress_cycles':('source','fatigue','sites',{'range':v('Pa','scalar','stress_range','sites','非负完整循环应力范围Δσ，不是半幅'),'rate':v('1/s','scalar','cycle_rate','sites','非负完整循环数率r')},'一条覆盖sites，各加载块内恒定')}
c=make('fatigue-crack-growth',2,'history',['crack_length'],{'growth_rate':p('m',0,desc='参考ΔKr下每完整循环增长C0，循环计数无量纲'),'reference_intensity_squared':p('Pa2.m',0,desc='参考应力强度范围的平方ΔKr²>0'),'growth_exponent':p('1',0,8,'Paris指数m'),'width':p('m',0,desc='路径尺度W'),'geometry_constant':p('1',0,desc='Y0>0'),'geometry_linear':p('1',0,desc='Y1≥0',closed=True),'geometry_quadratic':p('1',0,desc='Y2≥0',closed=True),'critical_intensity_squared':p('Pa2.m',0,desc='临界应力强度平方Kc²>0')},crules,list(crules),detail='观测点标识一条给定直线路径的初始裂尖位置；只解标量裂长ODE，固定位置不是移动网格节点。Y(a)=Y0+Y1(a/W)+Y2(a/W)²，ΔK=Y(a)Δσ√(πa)，ΔKr=√reference_intensity_squared，Kc=√critical_intensity_squared；da/dt=r C0(ΔK/ΔKr)^m。平方参数使用Pa2.m以保持整数幂SI单位。应力比固定R=0，故Kmax=ΔK；不包含闭合、阈值、过载迟滞或裂纹相互作用。初值显式给出，全部请求时刻位于a<W且ΔK<Kc的增长阶段，不允许跨失稳延长模型。临界状态与路径改变属于数据不合法，不要求编造失效后裂长。',top=0);c['parameters']={k:x for k,x in c['parameters'].items() if k not in EL}

# Physical output units depend on dimensional reduction, never on quantity name alone.
for cfg in CAT.values():
 if cfg['slug']=='hyperelastic-solid':
  rule=list(cfg['rules']['traction']);rule[3]={'value':v('Pa','vector','traction','facets','外界对固体的参考名义死载t0=P N；N为参考外法向，每参考面积')};cfg['rules']['traction']=rule
 cfg['output_specs']={q:dict(zip(['unit','kind','atol','where','description'],Q[q])) for q in cfg['outputs']}
 if cfg['dimension']==2 and 'energy' in cfg['outputs'] and cfg['slug']!='plane-stress':cfg['output_specs']['energy']['unit']='J/m'
 if cfg['slug']=='gradient-damage':cfg['output_specs']['energy']['description']='完整内部能∫[g(d)ψ0+Gc(d²/(2ℓ)+ℓ|∇d|²/2)]dA，含裂纹正则化能'
 cfg['model']='solid-'+cfg['slug']+'-v1'
 if cfg['slug']=='elastic-harmonic':cfg['parameters']['mass_damping']['closed']=False
 if cfg['slug']=='hyperelastic-solid':cfg['parameters']['poisson_ratio']['lower']=0;cfg['parameters']['poisson_ratio']['closed']=True
 cfg['limits']=dict(cells=5000 if cfg['topology'] else 0,nodes=15000 if cfg['topology'] else 1000,frames=201,components=3000000)
 cfg['timeout']=900 if cfg['mode']=='static' else 1500


def param_table(cfg):
 s='| 参数名（physics.parameters 下） | 单位 | 值域与含义 |\n|---|---|---|\n'
 for name,x in cfg['parameters'].items():
  bound=('；下界'+('≥' if x['closed'] else '>')+str(x['lower']) if x['lower'] is not None else '')+('；上界'+('<' if name=='residual_stiffness' else '≤')+str(x['upper']) if x['upper'] is not None else '')
  s+=f"| `{name}` | `{x['unit']}` | {x['description']}{bound} |\n"
 return s if cfg['parameters'] else '`physics.parameters={}`，本题无全局标量参数；EI由材料条件给出。\n'


def data_text(cfg):
 d=cfg['dimension'];slug=cfg['slug'];hist=cfg['mode']=='history';top=cfg['topology']
 fatigue=not top
 rule_values=[x for rule in cfg['rules'].values() for x in rule[3].values() if 'kind' in x]
 kinds={x['kind'] for x in rule_values}; places={rule[2] for rule in cfg['rules'].values()}
 has_initial=any(rule[0]=='initial' for rule in cfg['rules'].values())
 s=f'''# {slug} 数据契约

本题与instruction、通用CONTRACT共同构成完整契约。入口为UTF-8 `problem.json`和扁平HDF5{ '，网格为MSH 4.1 ASCII' if top else '' }；文件相对清单解析，名称不携带物理条件。`physics`恰为model与parameters，`physics.model="{cfg['model']}"`；`task`若出现必须为`{slug}`。`spatial_dimension={d}`。只接受本题定义的模型和键。

## 分析与材料

{cfg['detail']}

{param_table(cfg)}
'''
 s+='以上参数全部必填；每项恰为`{"value":有限标量,"unit":"表中单位"}`，无隐藏缺省或额外参数。' if cfg['parameters'] else ''
 s+=('除mode_count必须为整数值外，' if slug=='elastic-modes' else '')+'数值均为有限实数，布尔值不能作为数值。'
 if top>=2 and slug!='elastic-truss':
  if slug not in ('elastic-plate','hyperelastic-solid'):
   s+='ε是完整张量，剪切εxy不是工程剪切γxy。'
  if slug=='plane-stress':s+='本题使用材料段的平面应力λps。'
  elif slug!='elastic-plate':s+='μ=E/[2(1+ν)]、λ=Eν/[(1+ν)(1−2ν)]。'
 s+='\n\n## 几何、位置与数组身份\n\n'
 if top:
  types={1:'非退化一阶直线段（Gmsh type 1）',2:'非退化一阶三角形（type 2）',3:'非退化一阶四面体（type 4）'}
  s+=f'`meshes`恰含main，`locations.domain`是main全部顶维单元所用节点，`locations.cells`是main全部{top}维单元；IDs按tag递增。计算域是输入{types[top]}拼成的精确参考域，不以可选CAD替代。未用坐标为0；输出采样身份始终使用参考位置。内部分网、升阶或重网格自由，但输出映回固定身份。'
  if slug not in ('elastic-truss','cohesive-interface','linear-elastic-fracture'):s+='域连通无悬挂节点。'
  if top>=2 and slug!='elastic-plate':s+='体单元共享tag的公共面是完美粘结界面。'
  s+='\n\n其他mesh位置允许同一main的顶维cells单元子集（只用于输出）、节点子集或边界'+str(max(top-1,0))+'维单元子集。输入须导出每个外边界实体。每条边界记录的实体集合由引用的location IDs明确给出，Physical Group若声明须与这些IDs完全一致。'
  if top>=2:
   s+='边界面外法向由相邻体决定，不能由节点存储方向猜。'
   if slug!='elastic-plate':
    bc_name='实部和虚部位移' if slug=='elastic-harmonic' else ('fixed' if slug=='elastic-modes' else '位移')
    s+=f'{bc_name}条件引用边界节点，实际作用在全部顶点均属于该记录IDs的完整外边界单元之并；该节点集必须恰为这些完整面／边的顶点并，禁止孤立点或棱支撑。'
   if any(op.startswith('traction') for op in cfg['rules']):s+=('名义牵引引用参考外边界单元。' if slug=='hyperelastic-solid' else '牵引引用外边界单元。')
   if 'rigid_plane' in cfg['rules']:s+='接触引用候选外边界单元。'
   if 'cells' in places:s+=('横向面载荷使用全部cells。' if slug=='elastic-plate' else '体力使用全部cells。')
   s+=('配对界面按下文cohesive_pair处理。' if slug=='cohesive-interface' else '不把内部面当外边界。')
  if slug=='elastic-truss':s+='杆系的位移和集中力可作用任意杆节点（包括连接节点）；cells是全部杆，domain是全部杆端节点。N为每根直杆平均内力。'
  if slug=='elastic-beam':s+='梁只有一条无分叉区间，domain包括其全部节点；ends位置恰含一个实际端点节点，按x最小／最大确定左右。梁内部单元端点不允许clamp或end_load。'
  s+='\n\n'
 else:
  state='循环与裂长状态' if slug=='fatigue-crack-growth' else '循环与损伤状态'
  s+=f'`meshes={{}}`、`geometries={{}}`；`locations.sites`为独立实际观测点，含递增非负IDs及float64[N,2]坐标（m），点之间独立、不插值。同一观测点的{state}始终按ID行对应。'+('坐标不决定隐含几何因子。' if slug=='fatigue-crack-growth' else '')+'\n\n'
 if top:
  s+='aggregate位置仅支持source引用覆盖整个域的cells，IDs恰含一项；operation=sum对应integral，operation=mean对应average。具体观测按本题输出表请求，不接受边界或单元子集聚合。'
 else:s+='本题仅使用sites独立点point输出。'
 s+='字段对象名、HDF5 key和tag是三种身份：条件`{"field":"logical_name"}`引用fields对象；`fields.logical_name.array`才是HDF5 key。各对象名自由选择（'+('domain、cells' if top else 'sites')+'保留位置名除外），不得由名称推断quantity或数组key。\n\n## 时间、连续解释和输入场\n\n'
 if hist:
  s+='`start_time=t0<end_time=tf`；输出轴恰为一个名为response的轴，时刻全部位于[t0,tf]，可包括初态。'
  if fatigue:
   s+='所有source场共享同一不少于2帧的载荷轴，首末恰为t0、tf。'
   if has_initial:s+='初态场单帧且时刻恰为t0。'
   s+='输出时刻不改变块的累计历史。'
  else:
   s+='非初态多帧输入场必须首末恰为t0、tf；单帧constant加载场定义域为整个[t0,tf]，存储时刻必须为t0，这是显式全程常量而非外推。'
   if has_initial:s+='初态场单帧且时刻恰为t0。'
   s+='各输入场可引用不同轴；输出时刻不是求解器内部时间步，不可跳过未输出的中间加载历史。'
 else:
  marker={'elastic-modes':'固有频率','elastic-buckling':'屈曲倍率','elastic-harmonic':'复幅'}.get(slug,'静力')
  s+=f'所有时间轴恰为单帧[0.0]，输出引用steady轴；它是{marker}存储标记，不是物理启动初态；不接受多帧条件或时间插值。'
 s+='\n\n输入场恰为被条件引用的fields，全部float64。'
 if 'scalar' in kinds:s+='标量kind=scalar、component_shape=[1]、components=["value"]；'
 if 'vector' in kinds:s+=f'vector使用全局前{d}坐标，component_shape=[{d}]、components='+('["x","y"]' if d==2 else '["x","y","z"]')+'；'
 s+='数组始终[T,N,*component_shape]，不得省略任何轴。'
 if fatigue:
  s+='所有source数据参数必须显式使用同location、表中quantity／unit／kind的field引用；即使恒幅或各点相同，也不能用带单位常量简写。'
  if has_initial:s+='initial_length.value可用单位m的标量常量，或同sites、quantity=crack_length、unit=m、kind=scalar的field。'
 else:
  if 'scalar' in kinds:s+='标量数据参数允许表中单位的带单位常量，或同location、相同quantity／unit／kind的显式field。'
  if 'vector' in kinds:s+='向量数据参数必须使用同location、相同quantity／unit／kind的显式field，即使均匀也不能使用常量简写。'
 s+='只允许条件表列出的参数，无额外选项或默认单位。\n\n每个输入field必须显式sampling。'
 if fatigue:s+='sites场space=uniform表示每个独立点的时间记录，不进行跨点重建。'
 else:
  if places & {'nodes','ends'}:s+='节点场space=piecewise_linear，沿一阶输入单元唯一P1重建（边界节点在边界单元上重建）。'
  if places & {'cells','facets'}:s+='element场space=piecewise_constant，表示每个单元上的常值。'
 s+='所有场extrapolation=forbid，禁止范围外外推。'
 if fatigue:
  s+='source场sampling.time=previous；[ti,ti+1)取第i帧，末帧仅作闭区间存储标记并与倒数第二帧相等。不接受linear或constant循环源场。'
  if has_initial:s+='初始裂长场sampling.time=constant。'
  s+='输出在断点上包含此前完整块的累积贡献，与采用右块继续演化相容。'
 elif hist:
  if has_initial:s+='初态场time=constant；'
  s+='多帧加载场time=linear，时间节点间逐分量线性；单帧加载场time=constant且为全程常量。先空间重建再时间插值。'
 else:s+='所有输入场time=constant。'
 s+='\n\n## 条件全集\n\n每条记录的role、variable、operator、location及data全部显式。下表是本题唯一允许的operator；不得通过列表顺序覆盖冲突条件。\n\n| operator | role／variable | 位置类别 | data精确键与类型 | 含义与组合 |\n|---|---|---|---|---|\n'
 for op,(role,var,where,data,desc) in cfg['rules'].items():
  entries=[]
  for name,x in data.items():
   if 'option' in x:entries.append(f'`{name}={{"option":"{x["option"]}"}}`')
   elif 'location' in x:entries.append(f'`{name}={{"location":"plus位置名"}}`')
   else:entries.append(f'`{name}`：{x["kind"]}，`{x["unit"]}`，quantity=`{x["quantity"]}`；{x["description"]}')
  if slug=='elastic-harmonic':desc=desc.replace('同一节点只允许一条位移记录','同一节点在同一幅部只允许一条位移记录')
  s+=f'| `{op}` | `{role}`／`{var}` | {where} | '+'<br>'.join(entries)+f' | {desc} |\n'
 s+='\n必须出现：'+', '.join('`'+x+'`' for x in cfg['required'])+'。'
 if 'cells' in places:s+='cells类的每个算子恰一条且覆盖全部cells。'
 if has_initial:s+='initial类恰一条且覆盖'+('sites' if fatigue else 'domain')+'。'
 if fatigue:s+='sites类每个算子恰一条覆盖sites。'
 else:
  if places & {'nodes','ends'}:s+=('每个幅部内的节点边界允许多条互不重叠记录。' if slug=='elastic-harmonic' else '节点边界允许多条互不重叠记录。')
  if slug=='elastic-truss':s+='不同来源的nodal_force可累加。'
  s+='固定约束必须足以排除刚体和机构；无条件的边界按本题零自然载荷处理，不能添加隐含对称或弹簧。'
 s+='\n\n'
 if top>=2:
  if slug=='elastic-harmonic':s+='边界记录在实部、虚部内分别去重；同一节点不得重复声明同一幅部的位移，实部与虚部必须覆盖相同节点。每个幅部内给定牵引与位移可在共享棱边交会，但不能在整面重合。'
  elif slug=='elastic-plate':s+='同一边界单元不能重复声明plate_clamp；夹持条件覆盖全部外边界。'
  else:
   s+='同一实体同种边界只能一条；位移边界重叠节点不得重复声明。'
   if any(op.startswith('traction') for op in cfg['rules']):s+='给定牵引与位移可在共享棱边交会，但不能在整面重合。'
  s+='数据不含相互矛盾约束。\n\n'
 if slug in ('hyperelastic-solid','frictionless-contact','frictional-contact','j2-plasticity','linear-viscoelastic','power-law-creep','gradient-damage','cohesive-interface'):s+='起始全域位移与本题内部状态由材料段明确为0，无需initial记录；全部给定位移、牵引、体力的起始值必须0。给定加载场须多帧覆盖端点或显式全程零常量；不允许用非零常量瞬间加载。历史初态与迭代初猜不同。\n\n'
 if slug=='cohesive-interface':s+='cohesive_pair的location是minus侧边界线单元，partner是plus侧线单元。两集合几何逐段完全重合，按端点坐标双射配对，节点tag不同；n与minus侧外法向一致，plus侧相反。两侧不能再声明traction、接触或位移边界；沿界面端点与外界夹持交会时，位移须相容。全域cells包含两体；opening与cohesive_traction只在minus集合输出，每段恰一次。不得按两集合IDs的行号配对。\n\n'
 if slug in ('frictionless-contact','frictional-contact'):s+='rigid_plane各location合并为候选面集合；它不与traction实体重叠、也不含任何被位移约束的节点。法向参数(normal_x,normal_y,normal_z)的欧氏长度为1（声明数值允许1e-10误差），所有候选面初始在允许半空间；接触输出可选候选面的子集，不含非候选面。\n\n'
 s+='## 请求输出与结果HDF5\n\noutputs中的逻辑名称及array key自由，quantity必须来自下表。每个必需quantity至少出现一次，可在不同允许采样子集重复请求。结果只包含每个输出array及其IDs和时间轴，严格沿用输入行序、dtype及全部轴；不得重复坐标或输入场。所有输出float64且有限。\n\n| quantity（均必需） | 单位 | kind／位置与采样 | 定义 |\n|---|---|---|---|\n'
 for q,x in cfg['output_specs'].items():
  where={'nodes':'domain或其节点子集的point；不接受单元中心替代','cells':'cells或其单元子集，average','sum':'aggregate(sum)，source=cells且覆盖整个域，integral','mean':'aggregate(mean)，source=cells且覆盖整个域，average','sites':'sites，point','contact':'候选接触边界单元，average','interface':'minus侧界面线单元，average'}[x['where']]
  kind=x['kind'] if x['kind']!='spectrum' else 'components，shape=[k]，components=[f1,…,fk]'
  description='Cauchy应力，完整对称矩阵' if slug=='hyperelastic-solid' and q=='stress' else x['description']
  s+=f'| `{q}` | `{x["unit"]}` | {kind}；{where} | {description} |\n'
 if any(x['kind']=='vector' for x in cfg['output_specs'].values()):s+=f'\n输出vector的component_shape=[{d}]，components='+('["x","y"]' if d==2 else '["x","y","z"]')+'。'
 if any(x['kind']=='tensor' for x in cfg['output_specs'].values()):s+=f'\n输出tensor的component_shape=[{d},{d}]，components按xx,xy'+(',xz,yx,yy,yz,zx,zy,zz' if d==3 else ',yx,yy')+'完整行优先排列，不只存对称矩阵的独立项。'
 if any(x['kind']=='scalar' for x in cfg['output_specs'].values()):s+='\n输出scalar的component_shape=[1]，components=["value"]。'
 if top:
  measure={1:'长度',2:'面积',3:'体积'}[top]
  if any(x['where']=='nodes' for x in cfg['output_specs'].values()):s+='\n节点输出取连续解在给定节点的值。'
  if any(x['where'] in ('cells','contact','interface') for x in cfg['output_specs'].values()):s+=f'单元average按参考{measure}（边界按其自身维数的测度）积分再除测度，不取节点算术均值或单元中心点值。'
  if 'energy' in cfg['outputs']:
   if slug=='hyperelastic-solid':s+='energy=∫W dV，Cauchy应力的单元平均也按参考体积加权。'
   elif slug=='gradient-damage':s+='energy按材料段包含弹性储能及正则化裂纹能，不含外力势；二维按单位z长度。'
   else:s+='energy=½∫ε:σ，使用参考域测度，不含外力势。'+('二维平面应力乘实际thickness。' if slug=='plane-stress' else '二维按单位z长度。' if d==2 else '')
  if 'frequency' in cfg['outputs']:s+='frequency在全域cells的aggregate(mean)输出：把同一整体谱视为空间常量后的体积平均，不要求构造局部频率。k由mode_count确定，不输出振型。'
  if 'load_factor' in cfg['outputs']:s+='load_factor在全域cells的aggregate(mean)输出：把同一整体倍率视为空间常量后的体积平均，不要求构造局部倍率，不输出振型。'
 s+='\n\n## 合法范围与保证\n\n除上文明确的自由键和时间轴名外不增加字段或条件组合。'
 if fatigue:s+='数据制作方须确认材料模型适用、循环块与初态合法、各请求时刻的累计响应有限且可确定，并在题面预算内用独立基准达到目标精度。'
 else:s+='数据制作方须确认材料适用、网格非退化、载荷与约束相容、解在规定分支上可确定、所请求点值及平均存在，并在题面预算内用独立基准达到目标精度。'
 if slug=='elastic-transient':s+='所有请求节点和时刻的速度必须存在唯一经典点值；排除波前或折点处没有唯一时间导数的速度观测。此正则性要求是正式数据接收条件，不能由P1初态或位移边界的相容性自动推出。'
 if hist and not fatigue and slug!='elastic-transient':s+='规定的连续稳定分支须在正式数据接收时核验。'
 s+='这些是数据接收条件，不是结构校验器已经证明的事实；尚无正式数据时不声称已获验证。\n'
 return s


def render(batch=None):
 for sec,title,tasks in SECTIONS:
  n=int(sec.split('.')[1].split('-')[0])
  if batch and not batch[0]<=n<=batch[1]:continue
  parent=ROOT/'qbank/03-solid-mechanics'/sec;parent.mkdir(parents=True,exist_ok=True)
  index=f'# {sec.split("-")[0]} {title}\n\n| 编号 | 题目 |\n|---|---|\n'
  for i,(slug,name,scope) in enumerate(tasks,1):
   cfg=CAT[slug];folder=parent/slug;folder.mkdir(exist_ok=True)
   number=sec.split('-')[0]+'.'+str(i)
   index+=f'| {number} | [{name}]({slug}/instruction.md) |\n'
   sizes=cfg['limits'];rule_rows='\n'.join(f'| `{q}` | {x["atol"]} `{x["unit"]}` |' for q,x in cfg['output_specs'].items())
   mesh=bool(cfg['topology']);history=cfg['mode']=='history'
   varying='几何、参数、载荷、支撑'+('、历史' if history else '')+'与观测' if mesh else '材料参数、循环块'+('、初始裂长' if slug=='fatigue-crack-growth' else '')+'与观测'
   geometry='输入网格定义精确参考几何及采样支持，不是强制有限元离散。' if mesh else '各观测点独立演化，无空间网格或跨点重建。'
   scope_notes=[]
   if mesh:scope_notes.append('首版不承诺任意病态网格')
   if 'poisson_ratio' in cfg['parameters'] and slug!='elastic-plate':scope_notes.append('Poisson比范围按DATA给定')
   if history:scope_notes.append('历史长度和采样规模受本题上限约束')
   if slug=='elastic-modes':scope_notes.append('模态至多12阶')
   limits_note='；'.join(scope_notes)+'。' if scope_notes else ''
   size_note=f"每例至多{sizes['cells']}个顶维单元、{sizes['nodes']}个网格节点" if mesh else f"每例至多{sizes['nodes']}个独立点"
   spectral='谱量也是逐分量比较且保留重数。' if slug=='elastic-modes' else ''
   velocity_note='所有请求节点与时刻的速度观测须具有唯一经典点值，正式数据须核验这一接收条件，排除波前或折点处未定义的速度点值。' if slug=='elastic-transient' else ''
   method='考生负责选择相容的积分与累计方法并控制误差；给定的材料响应及循环历史不能改写。允许任意语言、软件或解析方法，只要覆盖公开问题族；不要求复现参考软件。' if not mesh else '考生负责由物理描述建立相容的连续问题、选择模型允许范围内的适当表示和求解方法、离散与误差控制；给定的材料响应、降维假设和历史不能改写。允许任意语言、软件、内部网格、解析或降阶方法，只要覆盖公开问题族；不要求复现参考软件和参考离散。'
   instr=f'''# {number} {name}

实现本题范围内可复用求解器，冻结后处理多个未见算例。能力范围：{scope}。具体{varying}由算例给定。任务目标是{ '、'.join(cfg['outputs']) }对应的物理量，含义以本题DATA就地定义。

{cfg['detail']}{velocity_note}

{method}{geometry}不同方法输出须满足相同观测。

阅读[本题DATA](DATA.md)和[通用数据协议](../../../../docs/CONTRACT.md)即可确定全部输入输出。模型仅为`{cfg['model']}`；只接受本题定义的模型与组合。

## 规模与运行

{size_note}，每个轴至多{sizes['frames']}帧，全部输入和输出场分别至多{sizes['components']}个float64分量。{limits_note}数据制作方须用独立基准证明同预算可达到设计精度；当前规模、预算及容差尚待正式数据校准。

入口：`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{cfg['timeout']}秒墙钟、4CPU、8192MB内存、0GPU；启动与全部读写计时，逐例无网络。依赖提前准备，可用Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5；不强制使用Python计算。程序以0退出，输出为完整HDF5，路径以命令行参数为准；无独立输出字节限额，shape规模仍受限。生成求解器时间为3600秒，构建环境最多1800秒。

## 评分

每例正常退出、结构合法且全部请求quantity通过得1分，否则0分；本题成绩为通过有效例数／有效例数。输入、配置和参考错误属于基础设施问题，不计考生失败；没有正式有效例时不产生成绩。

每个float64输出在全部时刻、实体与分量上逐值满足 `|结果−参考| ≤ atol(quantity)+0.01|参考|`。不去均值、平移、重排、拟合偏置、豁免少数超限点或按整体RMSE替代。全部字段同时通过，阈值等号接受。{spectral}IDs／时间、shape、dtype及有限值严格遵守CONTRACT。

| quantity | atol（单位同输出） |
|---|---|
{rule_rows}

这些是待校准设计目标；契约工具验证不构成数值解、物理模型或参考精度的证据。正式数据、参考及评测发布另行完成。
'''
   (folder/'instruction.md').write_text(instr);(folder/'DATA.md').write_text(data_text(cfg))
   policy={'version':2,'quantities':{q:{'unit':x['unit'],'rule':dict(metric='pointwise',time='per_time',components='per_component',atol=x['atol'],rtol=.01)} for q,x in cfg['output_specs'].items()}}
   (folder/'author').mkdir(parents=True,exist_ok=True)
   (folder/'author/grading-template.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2)+'\n')
   (folder/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=cfg['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
   (folder/'harbor').mkdir(exist_ok=True)
   (folder/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 4\nmemory_mb = 8192\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
  (parent/'README.md').write_text(index+'\n正式数据、参考与发布留后；题面DATA仅依赖本题和通用CONTRACT。\n')
 parent=ROOT/'qbank/03-solid-mechanics';parent.mkdir(exist_ok=True)
 index='# 第三章 固体与结构力学分析\n\n9节21题。考生逐题阅读instruction、DATA及通用CONTRACT；规划、审阅与验证仅为维护入口。\n\n| 节 | 题数 |\n|---|---:|\n'
 for sec,title,tasks in SECTIONS:index+=f'| [{sec.split("-")[0]} {title}]({sec}/README.md) | {len(tasks)} |\n'
 index+='\n[章规划](../design/chapter-03-solid-mechanics.md) · [逐题清单](../design/chapter-03-task-plan.md) · [进度与验证](../design/reviews/chapter-03-progress.md)\n\n未生成正式数据、参考解或发布包。\n'
 (parent/'README.md').write_text(index)
 if not batch:
  ext=ROOT/'qbank/extensions/caeoj_ext/solid';ext.mkdir(exist_ok=True)
  (ext/'models.json').write_text(json.dumps(public_model_catalog(CAT),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--batch',nargs=2,type=int);args=parser.parse_args();render(args.batch)
