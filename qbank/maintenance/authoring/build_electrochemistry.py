"""Expand electrochemical statements and contracts; never generate cases/solutions."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
CH=ROOT/'qbank/10-electrochemistry'
SECTIONS=[('10.1-ionic-transport','离子输运与空间电荷',['ionic-equilibrium','blocking-pnp']),('10.2-electrode-kinetics','电极反应与混合电位',['mixed-potential']),('10.3-interfaces','电化学界面',['capacitive-redox','redox-impedance']),('10.4-electrode-transport','传质与电极反应耦合',['electrode-diffusion']),('10.5-storage','电化学储能',['particle-battery']),('10.6-energy-conversion','电化学能量转换',['fuel-cell-energy'])]
NAMES=['自洽空间电荷平衡','阻挡电极离子瞬态','多通道电极混合电位','双电层与有限库存反应','有限库存界面小信号阻抗','电极反应与有限层扩散','双电极颗粒扩散电池','燃料电池极化与能量分配']
def P(u,m,**kw):return dict(unit=u,meaning=m,**kw)
def S(u,m,**kw):return dict(kind='scalar',shape=[1],unit=u,meaning=m,**kw)
def C(sh,u,m,**kw):return dict(kind='components',shape=sh,unit=u,meaning=m,**kw)
M={}
for slug,name in zip([s for _,_,ss in SECTIONS for s in ss],NAMES):
    dynamic=slug in ('blocking-pnp','capacitive-redox','electrode-diffusion','particle-battery')
    c=dict(name=name,dynamic=dynamic,parameters=dict(temperature=P('K','恒定温度T>0',positive=True),gas_constant=P('J/(mol.K)','输入明确给定气体常数R>0',positive=True),faraday=P('C/mol','输入明确给定法拉第常数F>0',positive=True)),locations={},records={},outputs={},timeout=1200 if slug in ('blocking-pnp','particle-battery') else 900 if slug=='electrode-diffusion' else 600 if slug=='ionic-equilibrium' else 240)
    axis='initial' if dynamic else 'state'
    def loc(n,k,lo,hi,m):c['locations'][n]=dict(kind=k,minimum=lo,maximum=hi,meaning=m)
    def rec(op,role,var,l,data,time=None):c['records'][op]=dict(role=role,variable=var,location=l,data=data,axis=time or axis)
    def out(q,s,l,atol=1e-6,rtol=.002):c['outputs'][q]=dict(s,location=l,atol=atol,rtol=rtol)
    if slug in ('ionic-equilibrium','blocking-pnp'):
        c['parameters'].update(species_count=P('1','离子及可选中性组分数s，JSON整数2..8',integer=True,lower=2,upper=8),length=P('m','液体区间长度L>0',positive=True),permittivity=P('F/m','绝对介电率ε>0，不是相对介电常数',positive=True))
        loc('system','entities',1,1,'唯一均匀溶液材料对象')
        loc('left','points',1,1,'x=0的左电极液体侧边界');loc('right','points',1,1,'x=L的右电极液体侧边界')
        loc('probes','points',1,256,'真实观测点0≤x≤L，可重复坐标；边界浓度取液体迹')
        data=dict(charge=C(['s'],'1','电荷数z_i，整数−3..3；至少一个正与一个负，允许中性组分',integral=True,lower=-3,upper=3))
        if dynamic:data['diffusivity']=C(['s'],'m2/s','各组分恒定D_i>0',positive=True)
        else:data['reservoir']=C(['s'],'mol/m3','φ=0储槽浓度c_i,∞>0；Σz_i c_i,∞=0',positive=True)
        rec('ions','material','ions','system',data)
        if dynamic:rec('initial','initial','concentration','system',dict(value=C(['s'],'mol/m3','全区间均匀c_i0>0，Σz_i c_i0=0',positive=True)))
        for end in ('left','right'):
            rec(end,'boundary','potential',end,dict(value=S('V','边界液体电势φ，相对于固定同一φ=0参考；正负均可')),time='drive' if dynamic else 'state')
            out('surface_charge_'+end,S('C/m2','该电极单位真实面积自由电荷，左−εφ_x(0)，右+εφ_x(L)，无Stern层'),end,1e-8)
        out('potential',S('V','液体电势φ(x,t)' if dynamic else '液体电势φ(x)'),'probes',2e-6)
        out('concentration',C(['s'],'mol/m3','按液体体积计的组分浓度，轴i与输入一致'),'probes',1e-6)
    if slug=='mixed-potential':
        c['parameters']['applied_current']=P('A','公共金属给定总阳极电流I，可正负或0；0为整体开路')
        loc('metal','entities',1,1,'唯一等电位导体，电势Φ相对于已固定公共参考')
        loc('channels','entities',1,32,'导体表面的独立氧化还原反应通道；不共享库存，输入活度由外部储槽维持')
        rec('channels','material','channel','channels',dict(area=S('m2','该通道真实反应面积A>0',positive=True),electrons=S('1','反应R→O+n e⁻的n，精确整数1..4',integral=True,lower=1,upper=4),alpha=S('1','阴极指数系数α，0<α<1',positive=True,upper_exclusive=1),rate=S('mol/(m2.s)','标准面摩尔速率k>0',positive=True),standard_potential=S('V','标准还原电位E0，相对于同一公共参考'),solution_potential=S('V','本通道电解液电势φl，同一公共参考'),reduced_activity=S('1','还原态无量纲活度aR>0',positive=True),oxidized_activity=S('1','氧化态无量纲活度aO>0',positive=True)))
        out('metal_potential',S('V','公共金属电势Φ'),'metal',2e-6)
        out('faradaic_current',S('A/m2','各通道阳极为正的法拉第电流密度j'),'channels',1e-5)
    if slug in ('capacitive-redox','redox-impedance'):
        c['parameters']['concentration_scale']=P('mol/m3','活度归一化浓度c*>0',positive=True)
        l='cells' if dynamic else 'interface'
        loc(l,'entities',1,32 if dynamic else 1,'独立完全混合的工作半电池；电解液电势恒定为0，无空间梯度')
        rec('material','material','interface',l,dict(area=S('m2','实际工作电极面积A>0',positive=True),volume=S('m3','固定液相体积V>0',positive=True),capacitance=S('F/m2','按真实面积计的恒正微分电容Cdl',positive=True),electrons=S('1','R→O+n e⁻，n为精确整数1..4',integral=True,lower=1,upper=4),alpha=S('1','阴极指数系数α，0<α<1',positive=True,upper_exclusive=1),rate=S('mol/(m2.s)','标准面摩尔速率k>0',positive=True),standard_potential=S('V','标准还原电位E0；与电解液电势0采用同一参考')))
        rec('initial','initial','concentration',l,dict(value=C([2],'mol/m3','依次R、O浓度，均≥0且每行总和>0' if dynamic else '平衡cR、cO，均严格>0',positive=not dynamic,nonnegative=True)))
        if dynamic:
            rec('potential_initial','initial','potential',l,dict(value=S('V','初始Δ=φm−φl=φm，可为任意有限值')))
            rec('current','source','applied_current',l,dict(value=S('A/m2','单位真实面积外电路阳极电流J(t)，可正负或0')),time='drive')
            out('potential',S('V','Δ=φm−φl，电解液电势为0，不是扣掉Nernst电位后的过电位'),l,2e-6)
            out('concentration',C([2],'mol/m3','依次cR、cO，按液体体积计'),l,1e-6)
            out('faradaic_current',S('A/m2','jF，阳极正'),l,1e-5)
            out('capacitive_current',S('A/m2','jC=J−jF，包含充放电符号'),l,1e-5)
        else:
            loc('frequencies','entities',1,128,'独立频率对象，不作频率间插值，ID不代表频率')
            rec('frequency','source','angular_frequency','frequencies',dict(value=S('rad/s','角频率ω>0，非Hz',positive=True)))
            out('area_impedance',C([2],'Ohm.m2','Z=δΔ/δJ，最内轴实部、虚部，exp(+iωt)'),'frequencies',1e-7)
    if slug=='electrode-diffusion':
        c['parameters'].update(length=P('m','有限扩散层L>0',positive=True),diffusivity_reduced=P('m2/s','还原态恒定D_R>0',positive=True),diffusivity_oxidized=P('m2/s','氧化态恒定D_O>0',positive=True),concentration_scale=P('mol/m3','活度归一化浓度c*>0',positive=True),electrons=P('1','n为JSON整数1..4',integer=True,lower=1,upper=4),alpha=P('1','阴极指数系数α，0<α<1',positive=True,upper_exclusive=1),rate=P('mol/(m2.s)','标准面摩尔速率k>0',positive=True),standard_potential=P('V','标准还原电位E0，与电解液0采用同一参考'))
        loc('electrode','points',1,1,'x=0处电极的液体侧位置');loc('system','entities',1,1,'唯一外部远端储槽／初态参数对象')
        loc('probes','points',1,256,'严格内部0<x<L的真实接收点，可重复坐标')
        rec('initial','initial','concentration','system',dict(value=C([2],'mol/m3','全区间初始均匀cR0、cO0>0；x=L始终由同样浓度的储槽维持',positive=True)))
        rec('potential','boundary','potential','electrode',dict(value=S('V','电极电位Δ(t)=φm−φl，电解液φl=0')),time='drive')
        out('concentration',C([2],'mol/m3','内部点的cR、cO'),'probes',1e-6)
        out('surface_concentration',C([2],'mol/m3','x=0液体侧唯一迹cR,s、cO,s'),'electrode',1e-6)
        out('faradaic_current',S('A/m2','单位真实电极面积的阳极法拉第电流j'),'electrode',1e-5)
    if slug=='particle-battery':
        c['parameters']['area_resistance']=P('Ohm.m2','电池单位几何截面积串联电阻RΩ≥0',nonnegative=True)
        loc('electrodes','entities',2,2,'IDs必须恰[0,1]；0负极n、1正极p，含两种代表性球形固体颗粒')
        loc('cell','entities',1,1,'唯一电池；驱动电流密度按几何截面积计')
        for e in ('negative','positive'):loc(e+'_probes','points',1,256,'该电极颗粒内真实径向坐标r，0≤r≤对应R，允许表面／中心及重复坐标')
        rec('particles','material','particle','electrodes',dict(radius=S('m','球颗粒半径R_i>0',positive=True),diffusivity=S('m2/s','固相恒定D_i>0',positive=True),maximum_concentration=S('mol/m3','固体体积最大浓度cmax_i>0',positive=True),solid_fraction=S('1','电极固相体积分数ε_i，0<ε_i≤1',positive=True,upper=1),thickness=S('m','电极厚度L_i>0',positive=True),exchange_scale=S('A/m2','按真实活性面积计的b_i>0，j0_i=b_i√(θ_i,s(1−θ_i,s))',positive=True),ocp=C([4],'V','OCP三次多项式系数b0,b1,b2,b3；U_i(θ)=b0+b1θ+b2θ²+b3θ³，两极共用电位参考')))
        rec('initial','initial','stoichiometry','electrodes',dict(value=S('1','各颗粒初始均匀θ_i0，1e−6≤θ_i0≤1−1e−6',lower=1e-6,upper=1-1e-6)))
        rec('current','source','applied_current','cell',dict(value=S('A/m2','几何截面积放电为正的J(t)；t=0必须为0')),time='drive')
        for e in ('negative','positive'):out('solid_concentration_'+e,S('mol/m3','该颗粒内c_i(r,t)，按固体体积计'),e+'_probes',.01)
        out('surface_stoichiometry',S('1','每极表面θ_i,s=c_i(R_i,t)/cmax_i'),'electrodes',1e-5)
        out('cell_voltage',S('V','正极端子减负极端子电压Vcell'),'cell',1e-4)
    if slug=='fuel-cell-energy':
        c['parameters']['reference_pressure']=P('Pa','活度采用的标准压力p*>0',positive=True)
        loc('operating','entities',1,128,'独立稳态工况，不是空间点或物理时间序列')
        rec('operating','source','operating_point','operating',dict(hydrogen_pressure=S('Pa','氢气分压pH2>0',positive=True),oxygen_pressure=S('Pa','氧气分压pO2>0',positive=True),water_activity=S('1','产物水无量纲活度aW>0，由输入给定其相态参考',positive=True),standard_voltage=S('V','此温度下给定标准可逆电池电压E0'),thermoneutral_voltage=S('V','同一反应、温度和水相态的热中性电压Etn>0',positive=True),current_density=S('A/m2','单位几何面积电流J≥0，正向消耗燃料；允许外电源强迫高电流',nonnegative=True),exchange_anode=S('A/m2','阳极有效交换电流密度j0a>0，已换算到几何面积',positive=True),exchange_cathode=S('A/m2','阴极有效交换电流密度j0c>0，几何面积基准',positive=True),effective_electrons_anode=S('1','对称BV动力学的有效电子数ma，精确整数1..4',integral=True,lower=1,upper=4),effective_electrons_cathode=S('1','对称BV动力学的有效电子数mc，精确整数1..4',integral=True,lower=1,upper=4),area_resistance=S('Ohm.m2','几何面积串联欧姆电阻RΩ≥0',nonnegative=True)))
        out('reversible_voltage',S('V','由气体活度修正的Erev'),'operating',2e-6)
        out('cell_voltage',S('V','含活化与欧姆损失的端电压Vcell，可负'),'operating',1e-4)
        out('electric_power',S('W/m2','单位几何面积向外输出电功率P=J Vcell，可负'),'operating',.001)
        out('heat_release',S('W/m2','单位几何面积向外释放热Q=J(Etn−Vcell)，含可逆与不可逆热，可负'),'operating',.001)
    M[slug]=c

PHYS={
'ionic-equilibrium':'''一维平行平板之间0<x<L，等温理想稀溶液、恒定绝对介电率ε，液体电势相对于同一储槽φ=0参考。各组分与该电化学势储槽平衡：c_i(x)=c_i,∞ exp(−z_iFφ/(RT))；−εφ_xx=FΣ_i z_i c_i。两端分别给定φ(0)、φ(L)。给定储槽浓度为电中性，不对有限间隙内各离子总数另加守恒或独立归一化约束。表面电荷σL=−εφ_x(0)，σR=+εφ_x(L)，均按该电极真实面积计。无固定体电荷、Stern层、离子有限尺寸、化学反应或电流；不是线性Debye–Hückel近似。''',
'blocking-pnp':'''一维0<x<L的封闭等温理想稀溶液，介电率ε恒定。通量正向为+x：N_i=−D_i(∂x c_i+z_iF c_i ∂xφ/(RT))，∂t c_i=−∂x N_i；−εφ_xx=FΣ_i z_i c_i。两端φ由历史给定，所有离子两端N_i=0（阻挡，无通透、吸附或法拉第反应）。初态各c_i全区间均匀且电中性，两端初始电势均为0，因此初始φ=0与零通量相容。后续各离子有限库存分别守恒；不可用储槽Boltzmann浓度替代此瞬态问题。σL=−εφ_x(0)，σR=+εφ_x(L)，为电极真实面积电荷。无流动、固定体电荷、Stern层、体反应或额外电中性方程，电势必须与空间电荷自洽。''',
'mixed-potential':'''一个等电位金属导体表面具有多个独立通道r，每通道为R_r⇌O_r+n_r e⁻，正j表示氧化，浓度活度由外储槽维持。所有电位均相对同一固定参考。令f_r=n_rF/(RT)，ψ_r=Φ−φl_r−E0_r，j_r=n_r F k_r[aR_r exp((1−α_r)f_rψ_r)−aO_r exp(−α_r f_rψ_r)]。求唯一公共金属电位Φ，使Σ_r A_r j_r=I。I=0仅要求总电流为0，允许各通道存在非零且抵消的电流。所有A、k及活度严格正且0<α<1，保证总电流随Φ严格单调且两端无界。无双电层、欧姆压降、传质限制或未声明副反应；不把每通道分别置于Nernst平衡。''',
'capacitive-redox':'''各半电池彼此独立，恒温、封闭定容完全混合R/O液体；支持电解质与理想远端对电极将液体电势固定为0，其库存不属本题。工作界面R⇌O+n e⁻，阳极氧化为正；Δ=φm−φl、ψ=Δ−E0、f=nF/(RT)。jF=nFk[(cR/c*)exp((1−α)fψ)−(cO/c*)exp(−αfψ)]。Cdl dΔ/dt=J(t)−jF；dcR/dt=−A jF/(nFV)，dcO/dt=+A jF/(nFV)。Cdl为单位真实面积微分电容，J及jF也按真实工作面积计；电容不消耗R/O，jC=J−jF，cR+cO守恒。无空间扩散、热变化、串联电阻、额外均相反应或未声明电极。初始Δ不要求Nernst平衡，外加电流不要求初始为0。''',
'redox-impedance':'''恒温封闭定容完全混合R/O工作半电池，液体电势固定为0；支持电解质及远端对电极不计入库存。平衡cR,cO均正，Δeq=E0+(RT/(nF))ln(cO/cR)。令f=nF/(RT)、ψeq=Δeq−E0、j0=nFk(cR/c*)^α(cO/c*)^(1−α)、G=f j0，gR=(nFk/c*)exp((1−α)fψeq)，gO=−(nFk/c*)exp(−αfψeq)。对exp(+iωt)微扰，线性系统为δjF=GδΔ+gRδcR+gOδcO，iωδcR=−AδjF/(nFV)，iωδcO=+AδjF/(nFV)，δJ=δjF+iωCdlδΔ。输出Z=δΔ/δJ，单位Ohm.m²，不乘／除面积；任意非零微扰归一化给相同Z，不求有限振幅非线性响应。A和V决定有限库存反馈，不能直接套用无限储槽Rct并联电容；无扩散Warburg项、串联电阻或额外自由拟合项。所有ω>0，不请求DC零频或零库存极限。''',
'electrode-diffusion':'''支持电解质充分过量，使一维0<x<L液体电势固定0；还原态R及氧化态O只扩散，∂t cR=D_R∂xx cR、∂t cO=D_O∂xx cO，无迁移、对流或体反应。x=L固定为初始均匀储槽浓度。x=0电极电位Δ(t)给定，令f=nF/(RT)、ψ=Δ−E0，j=nFk[(cR,s/c*)exp((1−α)fψ)−(cO,s/c*)exp(−αfψ)]，c_s为液体侧表面浓度。通量正向+x，N_R(0)=−j/(nF)、N_O(0)=+j/(nF)，N=−D∂x c；等价D_R cR_x(0)=j/(nF)、D_O cO_x(0)=−j/(nF)。必须耦合求表面浓度，不能以储槽值替代。无双电层、串联电阻或电位反馈。允许初始均匀浓度与初始非零反应通量的导数不相容：通量边界对t>0成立，采用该初态的抛物型连续极限解；t=0浓度取均匀初值，t=0电流按该初始表面浓度及Δ(0)计算，不要求初始浓度梯度同时满足通量。''',
'particle-battery':'''恒温双电极锂插层单颗粒电池，每极一个代表性球颗粒。i=n,p；∂t c_i=D_i r⁻² ∂r(r²∂r c_i)，中心取正则球对称解∂r c_i(0)=0。a_i=3ε_i/R_i为单位电极体积真实活性面积；J按电池几何截面积计、放电为正，j_n=J/(a_n L_n)、j_p=−J/(a_p L_p)。表面向外锂摩尔通量−D_i∂r c_i(R_i)=j_i/F，初态c_i=θ_i0 cmax_i均匀，J(0)=0。θ_i,s=c_i(R_i)/cmax_i；j0_i=b_i√(θ_i,s(1−θ_i,s))，η_i=2RT/F·asinh(j_i/(2j0_i))。U_i由输入三次多项式在表面θ求值，两个OCP使用同一电位参考。Vcell=U_p+η_p−U_n−η_n−J RΩ，正极端子减负极端子。忽略电解液浓度／电势梯度、双电层、机械和热反馈；RΩ已含指定串联欧姆贡献，不另加任意电阻或过电位。全过程颗粒浓度须在[1e−6,1−1e−6]cmax内，由正式数据独立验证；输入初态合法不证明全过程适用。''',
'fuel-cell-energy':'''等温氢氧燃料电池的各独立稳态工况，总反应H2+(1/2)O2→H2O，每mol H2转移2mol电子。Erev=E0+(RT/(2F))ln[(pH2/p*)√(pO2/p*)/aW]。几何面积电流J≥0，活化损失ηa=2RT/(ma F)asinh[J/(2j0a)]、ηc=2RT/(mc F)asinh[J/(2j0c)]，对应输入有效电子数的对称BV经验动力学；ma、mc不是总反应的热力学电子计数2。Vcell=Erev−ηa−ηc−J RΩ；单位几何面积电功P=J Vcell，向外热释放Q=J(Etn−Vcell)，因此P+Q=J Etn。E0、Etn与水活度的相态参考按输入一致给定，不能自动引入液态／气态水数据库或另加反应热。支持外电源强迫高电流，故Vcell、P可负，Q按公式带符号；不截零。无气体传输限制、燃料利用率修正、混合电位、双电层、温度场或水管理，提供的分压和交换电流已是该工况的有效值。'''
}

EXTRA={
'ionic-equilibrium':'储槽满足Σz_i c_i,∞=0；按存储float64作为精确实数计算加权和，必须严格为0。声明检查使用精确二进制有理数，无电中性容差、不投影输入。每端还须max_i |z_i F φ端/(RT)|≤20，限制本题平衡指数范围。',
'blocking-pnp':'初始电中性要求将存储float64视为精确实数后Σz_i c_i0严格为0；声明检查使用精确二进制有理数，无电中性容差、不投影输入；两端drive首帧电势必须精确为0。各drive帧每端max_i |z_i F φ端/(RT)|≤20；线性历史的中间值亦有界。',
'capacitive-redox':'初始每个cells对象cR+cO>0；初始浓度允许某一态为0。所有参数和初态逐cell独立给定，未要求各行相同。',
'redox-impedance':'初始记录在此表示用于线性化的平衡组成，不是待积分的物理时间；Δeq由正的cR、cO和E0按本题公式确定，没有额外输入金属电势或初始扰动。',
'particle-battery':'electrodes IDs严格为[0,1]；negative_probes对应负极第0行、positive_probes对应正极第1行的半径，两个径向域互不拼接。首帧J精确为0。正式数据须核验全过程浓度范围，不以参考截断或表面θ投影使平方根合法。',
}

def desc(s):return s['kind']+' ['+','.join(map(str,s['shape']))+']，`'+s['unit']+'`；'+s['meaning']
def build(selected=None):
    CH.mkdir(parents=True,exist_ok=True)
    index=['# 第十章 电化学分析\n\n六节八题，考生只阅读本题instruction、DATA及通用CONTRACT。正式数据、参考解与发布留后。\n']
    for section,title,slugs in SECTIONS:
        index.append(f'- [{section.split("-")[0]} {title}]({section}/README.md)')
        if selected and section not in selected:continue
        d=CH/section;d.mkdir(exist_ok=True)
        (d/'README.md').write_text(f'# {section.split("-")[0]} {title}\n\n'+'\n'.join(f'- [{section.split("-")[0]}.{i} {M[s]["name"]}]({s}/instruction.md)' for i,s in enumerate(slugs,1))+'\n')
        for i,slug in enumerate(slugs,1):
            c=M[slug];dynamic=c['dynamic'];t=d/slug;t.mkdir(exist_ok=True)
            score='\n'.join(f'| `{q}` | {s["atol"]} | {s["rtol"]} | `{s["unit"]}` |' for q,s in c['outputs'].items())
            instruction=f'''# {section.split('-')[0]}.{i} {c['name']}

实现覆盖整个公开问题族的可复用求解器，冻结后处理多个未见算例。{PHYS[slug]}

材料、几何尺度、状态及{'驱动历史和观测时刻' if dynamic else '独立工况或观测位置'}随算例变化。上述物理响应已固定；考生负责将其实现为覆盖契约的计算程序，自主选择内部离散、积分、求根与误差控制。语言、软件及算法自由，覆盖整个范围的解析或降阶方法同样有效，不要求参考算法。输入输出由[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)完整定义。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{c['timeout']}秒墙钟（含启动与I/O）、2CPU、4096MB、0GPU，逐例无网络。程序0退出并写完结果HDF5；无独立输出字节上限。生成求解器3600秒，构建1800秒；环境预置Python3、NumPy、SciPy、h5py、Gmsh、jsonschema、C++/OpenMP/OpenMPI/HDF5，不强制Python。

对象规模见DATA；输入／输出场各至多2000000数值分量。资源与容差是待校准设计目标，正式数据须有预算内可达精度的独立基准；不声称任意形式合法的病态尺度或无限刚性组合均能在本预算求准。

## 评分

每有效例正常退出、输出合法且所有quantity的全部帧／对象／分量满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分；等号接受。{'复数实虚分别比较，无相位旋转或共轭修正。' if slug=='redox-impedance' else ''}无电势平移拟合、重排、截零、时间对齐或其他归一化。

| quantity | atol | rtol | 单位 |
|---|---|---|---|
{score}

总成绩为通过有效例数／有效例数，无有效例不产生成绩。输入、配置、参考或工具错误为基础设施错误，不计考生失败。结构、dtype、有限值和身份遵守CONTRACT；工具验证不构成物理适用性、参考精度或容差／预算校准证据。
'''
            (t/'instruction.md').write_text(instruction)
            params='\n'.join(f'| `{k}` | `{s["unit"]}` | {s["meaning"]} |' for k,s in c['parameters'].items())
            locs='\n'.join(f'| `{k}` | {s["kind"]}，{s["minimum"]}..{s["maximum"]}项 | {s["meaning"]} |' for k,s in c['locations'].items())
            time='time_axes恰含initial、drive、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0且末项H>0；drive引用float64[B]，2≤B≤129、首项0且末项H，中间严格递增。输出只用observe，材料与初态用initial，驱动条件用drive。驱动逐对象在相邻时刻线性插值，覆盖[0,H]，不外推；输出请求不是内部时间步。' if dynamic else 'time_axes恰含state，其引用float64[1]=[0.0]，所有输入和输出均用state；0是'+('频域存储标记，不是物理初态或频率值。' if slug=='redox-impedance' else '稳态存储标记，不是物理初态。')
            records=[]
            for op,r in c['records'].items():
                records.append(f'### `{op}`\n\nrole=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`，location=`{r["location"]}`；所引用字段均为time_axis=`{r["axis"]}`（条件记录本身不含time_axis键）。恰一条，完整覆盖该位置。data恰含：\n\n| 键 | 类型、单位及含义 |\n|---|---|\n'+'\n'.join(f'| `{k}` | {desc(s)} |' for k,s in r['data'].items()))
            outs='\n'.join(f'| `{q}` | {desc(s)} | `{s["location"]}` |' for q,s in c['outputs'].items())
            detail=''
            if 'probes' in c['locations']:detail+='points位置仅定义真实边界／观测坐标，均为float64[N,1]、单位m，不是内部离散网格；ID不携带坐标信息。'
            if slug=='particle-battery':detail+='points坐标为float64[N,1]、单位m，表示从相应球心测得的半径r，不是笛卡尔直线上的平面扩散坐标。'
            initial=''
            if slug=='blocking-pnp':initial='t=0浓度取全区间初始值，电势及两个表面电荷均为0。'
            if slug=='capacitive-redox':initial='t=0浓度和电位取输入初态，jF按同一动力学求值，jC=J(0)−jF(0)。'
            if slug=='electrode-diffusion':initial='t=0内部及表面浓度均取均匀初态，电流按初始浓度与Δ(0)的公式求值；边界导数不要求在t=0相容。'
            if slug=='particle-battery':initial='t=0固相浓度与表面θ由均匀初态给出，J(0)=0，端电压为两极初始OCP之差。'
            component_note=('s分量依次对应输入组分i=1..s。' if slug in ('ionic-equilibrium','blocking-pnp') else 'R/O双分量c1=还原态R、c2=氧化态O。' if slug in ('capacitive-redox','electrode-diffusion') else '平衡浓度双分量c1=R、c2=O；阻抗双分量c1=实部、c2=虚部。' if slug=='redox-impedance' else 'OCP的c1..c4依次为0..3次多项式系数。' if slug=='particle-battery' else '')
            data=f'''# {slug} 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单。顶层采用CONTRACT结构，physics恰含model、parameters；model=`electrochemistry-{slug}-v1`，task可省略，出现须为`{slug}`。禁止profile、contract_version、analysis、materials混用；不接受未列参数、条件、字段或位置。

## 物理定义与支持组合

{PHYS[slug]}

## 全局参数

parameters恰含下表全部项；各项只有value、unit，数值有限，布尔不能作数值，JSON整数要求不得用浮点数替代。全部无缺省。

| 参数 | 单位 | 含义与值域 |
|---|---|---|
{params}

## 位置、几何及身份

spatial_dimension=1，meshes、geometries均为空。entities表示真实有限对象，无虚构坐标；{'维度1表示真实一维空间坐标。' if slug in ('ionic-equilibrium','blocking-pnp','electrode-diffusion') else '维度1表示球内径向坐标。' if slug=='particle-battery' else '维度1仅为有限对象的存储标记，不增加空间方程。'}IDs为int64、非负、严格递增，身份仅在location内有效，字段N轴按IDs行序对应，不按ID数值作数组下标。{detail}

| location | kind、数量 | 完整语义 |
|---|---|---|
{locs}

## 时间、数组及重建

{time}

场均float64，完整形状[T,N,*component_shape]。scalar为[1]、components=["value"]；components按表中shape行优先展平标签为c1..cL（L为分量总数）。{'s替换为species_count。' if slug in ('ionic-equilibrium','blocking-pnp') else ''}{component_note}

所有data只允许{{"field":"逻辑字段名"}}，禁止内联数值、option或数组。fields恰为实际被引用场；quantity等于data键名，键value例外等于该条件variable；逻辑字段名与array key自由且区分。字段必须在对应条件同location及上表规定时间轴，不能借相同数组长度配对其他身份。每字段均point，sampling显式，space=uniform、extrapolation=forbid；{'drive场time=linear，其他场time=constant' if dynamic else '所有场time=constant'}。uniform表示各对象上给定值，不要求不同对象行相同，不作实体或观测点之间插值；连续物理解由方程求出，禁止把输入采样当内部解网格。

## 条件全集

{chr(10).join(records)}

## 输出

每个下列quantity至少出现一次，可重复请求；逻辑名及array key自由。全部float64、point、{'observe' if dynamic else 'state'}轴，无sampling，分量规则同上。必须使用表中完整location及全部对象，不能新增输出位置、重排身份或省略分量。输出是{'指定角频率的线性响应' if slug=='redox-impedance' else '各独立工况的稳态值' if not dynamic else '瞬时状态'}，不是时间平均、单元平均或整体积分。

| quantity | 类型、单位、含义 | location |
|---|---|---|
{outs}

结果HDF5只含输出array和必需IDs／时间轴，严格复制输入支持数组；不输出输入场、坐标、网格或额外数组。{initial}

## 接收限制

{EXTRA.get(slug,'')}

对象数量、参数及场值范围见各表；输入和输出场各≤2000000数值分量。正式数据还须独立核验本题模型及材料适用、给定条件相容、所请求观测存在、参考精度与预算内可达性。{'涉及浓度场或库存演化时须验证全过程非负与适定性，排除任意病态尺度和无限刚性组合。' if slug in ('ionic-equilibrium','blocking-pnp','capacitive-redox','electrode-diffusion','particle-battery') else '有限参数的极端条件仍须有稳定求值与预算内基准证据。'}声明检查不证明物理解、参考或数值准确性。不从目录、来源软件或隐藏配置补题意。
'''
            # Present a valid JSON example of sampling separately from its two supported time branches.
            data=data.replace('"time":"constant或linear"','"time":"linear"')
            (t/'DATA.md').write_text(data)
            policy={'version':2,'quantities':{q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()}}
            (t/'grading.json').write_text(json.dumps(policy,indent=2)+'\n')
            (t/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
            (t/'harbor').mkdir(exist_ok=True)
            (t/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 2\nmemory_mb = 4096\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
            (t/'harbor/requirements.txt').write_text('scipy==1.18.1\n')
    index.append('\n维护：[章规划](../design/chapter-10-electrochemistry.md)、[清单](../design/chapter-10-task-plan.md)、[进度](../design/reviews/chapter-10-progress.md)。\n')
    (CH/'README.md').write_text('\n'.join(index))
    ext=ROOT/'qbank/extensions/caeoj_ext/electrochemistry';ext.mkdir(exist_ok=True)
    (ext/'models.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    import sys
    build(sys.argv[1:] or None)
