"""Expand independently readable species contracts. Never writes cases or solutions."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
CH=ROOT/'qbank/09-species-reactions'
SECTIONS=[('9.1-diffusion','扩散传质',['fick-diffusion']),('9.2-migration','外场迁移',['imposed-field-migration']),('9.3-adsorption','吸附与解吸',['competitive-adsorption','pore-adsorption']),('9.4-reaction-networks','化学反应网络',['mass-action-network']),('9.5-reactive-flow','反应流',['reactive-transport']),('9.6-combustion','燃烧与点火过程',['adiabatic-combustion']),('9.7-interphase-transfer','相间传质',['partition-transfer'])]
NAMES=['多组分瞬态扩散','给定外场漂移扩散','有限库存竞争吸附','孔隙扩散吸附耦合','等温反应网络','给定流场反应传输','绝热定容燃烧反应器','相间分配传质网络']
def P(u,m,**kw):return dict(unit=u,meaning=m,**kw)
def C(sh,u,m,**kw):return dict(kind='components',shape=sh,unit=u,meaning=m,**kw)
def S(u,m,**kw):return dict(kind='scalar',shape=[1],unit=u,meaning=m,**kw)
M={}
TRANSPORT={'fick-diffusion','imposed-field-migration','pore-adsorption','reactive-transport'}
REACTION={'mass-action-network','reactive-transport','adiabatic-combustion'}
ADSORPTION={'competitive-adsorption','pore-adsorption'}
for slug,name in zip([s for _,_,ss in SECTIONS for s in ss],NAMES):
    transport=slug in TRANSPORT;reaction=slug in REACTION;adsorption=slug in ADSORPTION;burn=slug=='adiabatic-combustion'
    c=dict(name=name,transport=transport,parameters={'species_count':P('1','组分数s，JSON整数1..8',integer=True,lower=1,upper=8)},locations={},records={},outputs={},timeout=1200 if burn else 900 if slug in ('pore-adsorption','reactive-transport') else 300)
    def loc(n,k,lo,hi,m):c['locations'][n]=dict(kind=k,minimum=lo,maximum=hi,meaning=m)
    def rec(op,role,var,l,data,axis='initial'):c['records'][op]=dict(role=role,variable=var,location=l,data=data,axis=axis)
    def out(q,s,l,atol,rtol=.002):c['outputs'][q]=dict(s,location=l,atol=atol,rtol=rtol)
    loc('system','entities',1,1,'唯一材料／动力学参数对象，不是空间探针')
    if transport:
        c['parameters']['length']=P('m','区间长度L>0',positive=True)
        loc('knots','points',2,257,'初态空间结点，x严格递增，首尾恰为0、L')
        loc('left','points',1,1,'左端坐标x=0');loc('right','points',1,1,'右端坐标x=L')
        loc('probes','points',1,256,'严格位于0<x<L的独立接收点；坐标可重复，身份独立')
        rec('diffusivity','material','diffusivity','system',dict(value=C(['s'],'m2/s','各组分常量有效扩散系数D_i>0',positive=True)))
        rec('initial','initial','concentration','knots',dict(value=C(['s'],'mol/m3','t=0的移动相体积浓度c_i≥0',nonnegative=True)))
        for end in ('left','right'):rec(end,'boundary','concentration',end,dict(value=C(['s'],'mol/m3','该端移动相浓度Dirichlet历史，c_i≥0',nonnegative=True)),axis='boundary')
        out('concentration',C(['s'],'mol/m3','移动相体积浓度c_i(x,t)'),'probes',1e-6)
    else:
        loc('vessels','entities',1,32,'独立完全混合有限容积反应器／容器，IDs可不连续，各组分轴按c1..cs')
        rec('initial','initial','concentration','vessels',dict(value=C(['s'],'mol/m3','初始浓度c_i≥0',nonnegative=True)))
        out('concentration',C(['s'],'mol/m3','各容器内体积摩尔浓度c_i(t)'),'vessels',1e-6)
    if slug=='imposed-field-migration':
        c['parameters'].update(temperature=P('K','给定恒温T>0',positive=True),electric_field=P('V/m','沿+x的恒定外场E，可正可负或零'),gas_constant=P('J/(mol.K)','气体常数R>0，由输入明确给定',positive=True),faraday=P('C/mol','法拉第常数F>0，由输入明确给定',positive=True))
        rec('charge','material','charge','system',dict(value=C(['s'],'1','整数电荷数z_i，−4..4，允许中性组分',integral=True,lower=-4,upper=4)))
    if adsorption:
        c['parameters'].update(capacity=P('mol/kg','公共位点容量qmax>0，每个吸附分子占一个位点',positive=True))
        if transport:c['parameters'].update(porosity=P('1','孔隙体积分数ε，0<ε<1',positive=True,upper_exclusive=1),solid_density=P('kg/m3','固体骨架单位固体体积质量ρs>0',positive=True))
        else:c['parameters']['solid_loading']=P('kg/m3','单位液体体积的固体质量ρb>0',positive=True)
        rec('sites','material','sites','system',dict(adsorption=C(['s'],'m3/(mol.s)','吸附速率ka_i≥0',nonnegative=True),desorption=C(['s'],'1/s','解吸速率kd_i≥0',nonnegative=True)))
        rec('initial_loading','initial','loading','knots' if transport else 'vessels',dict(value=C(['s'],'mol/kg','初始固相负载q_i≥0，逐位置Σq_i≤qmax',nonnegative=True)))
        out('loading',C(['s'],'mol/kg','单位固体质量的吸附量'+('q_i(x,t)' if transport else 'q_i(t)')+'，不乘固液比'),'probes' if transport else 'vessels',1e-8)
    if reaction:
        c['parameters']['species_count'].update(lower=2,meaning='组分数s，JSON整数2..8；非平凡质量守恒反应至少需两个组分')
        c['parameters'].update(reaction_count=P('1','反应数r，JSON整数1..16',integer=True,lower=1,upper=16),concentration_scale=P('mol/m3','共同活度归一化浓度c*>0，不是初态',positive=True))
        loc('reactions','entities',1,16,'r条有向不可逆反应，按IDs行序；可逆反应必须显式给两条')
        data=dict(reactants=C(['s'],'1','反应物计量α_ri，整数0..4，每行总和1..4',integral=True,lower=0,upper=4),products=C(['s'],'1','生成物计量β_ri，整数0..4，每行总和1..8，β行不等于α行',integral=True,lower=0,upper=4),prefactor=S('mol/(m3.s)','反应体积速率前因子a_r≥0，已用c*归一化，非传统随反应级数变单位的k',nonnegative=True))
        if burn:data['activation']=S('J/mol','活化能E_r≥0',nonnegative=True)
        rec('kinetics','material','kinetics','reactions',data)
        material=dict(molar_mass=C(['s'],'kg/mol','组分摩尔质量M_i>0；每行反应Σ(β−α)M=0',positive=True))
        if burn:material.update(heat_capacity=C(['s'],'J/(mol.K)','定容摩尔热容cv_i>0，整个温度区间常量',positive=True),reference_energy=C(['s'],'J/mol','Tref处的摩尔内能u_i,ref，含形成内能；可正负'))
        rec('species','material','species','system',material)
    if slug=='reactive-transport':c['parameters']['velocity']=P('m/s','沿+x的恒定给定液体速度v，可正负或零；不求流场')
    if burn:
        c['parameters'].update(gas_constant=P('J/(mol.K)','理想气体常数R>0，由输入给定',positive=True),reference_temperature=P('K','内能参考温度Tref>0',positive=True))
        rec('thermal_initial','initial','temperature','vessels',dict(value=S('K','初始温度T0>0',positive=True)))
        out('temperature',S('K','绝热能量守恒确定的温度T(t)'),'vessels',.02,.001)
        out('pressure',S('Pa','绝对压力p=RTΣ_i c_i'),'vessels',.1,.002)
    if slug=='partition-transfer':
        del c['locations']['system']
        loc('links','entities',1,64,'有向传质连接；方向只定义流率符号，不禁止逆向净交换')
        rec('volumes','material','volume','vessels',dict(value=S('m3','各容器固定体积V_a>0',positive=True)))
        rec('links','material','transfer_link','links',dict(origin=S('1','起点容器的实际ID，不是数组行号',integral=True,nonnegative=True),destination=S('1','终点容器实际ID，须不同于起点',integral=True,nonnegative=True),partition=C(['s'],'1','平衡分配比K_i=c_destination/c_origin>0',positive=True),conductance=C(['s'],'m3/s','组分传质导通率G_i≥0',nonnegative=True)))
        out('molar_flow',C(['s'],'mol/s','各连接从origin流向destination的有符号净摩尔率'),'links',1e-9)
    M[slug]=c

PHYS={
'fick-diffusion':'一维恒截面静止稀溶液，组分彼此独立、不改变溶剂或材料。0<x<L，∂t c_i=D_i ∂xx c_i。两端均为给定浓度储槽，初态由结点线性重建。D_i恒正；无对流、反应、迁移、交叉扩散或几何变化。',
'imposed-field-migration':'一维静止稀溶液中的独立离子示踪组分；恒温T、外场E沿+x，通量J_i=−D_i∂x c_i+w_i c_i，w_i=D_i z_i F E/(RT)，∂t c_i=−∂x J_i。两端均给定浓度；正电荷在正E下向+x漂移。背景支持电解质维持外场，其库存与电荷不参与输出；无Poisson反馈、电中性浓度约束、电极反应、流动或焦耳热。中性组分退化为Fick扩散。',
'competitive-adsorption':'各容器封闭、等温、固定液体体积且完全混合，互不连接；固体均匀悬浮，公共单层位点竞争吸附，无溶剂吸附与吸附热。dq_i/dt=ka_i c_i(qmax−Σ_j q_j)−kd_i q_i，dc_i/dt=−ρb dq_i/dt。q为每kg固体的摩尔数，c为每m³液体的摩尔数；每个组分c_i+ρb q_i守恒。不得把有限速率动力学换成瞬时平衡等温线。',
'pore-adsorption':'一维均匀不动多孔骨架，恒截面、等温，无对流或反应热。移动浓度c按孔隙液体体积计，固相q按固体质量计。dq_i/dt=ka_i c_i(qmax−Σ_j q_j)−kd_i q_i；∂t c_i=D_i∂xx c_i−[(1−ε)ρs/ε]∂t q_i。D是已含曲折效应的孔隙浓度扩散系数；单位总截面积通量为−εD_i∂x c_i。两端只给移动浓度Dirichlet条件，q无空间通量且无边界条件，其初态在闭区间定义；q的端值按同一局部动力学演化。',
'mass-action-network':'各封闭定容等温完全混合反应器互不连接，浓度按各自反应器体积计。反应r的反应物计量α_ri、生成物β_ri显式给定，速率v_r=a_r ∏_i(c_i/c*)^α_ri，dc_i/dt=Σ_r(β_ri−α_ri)v_r。零次因子包括0^0取1；所有反应只按输入有向执行，不从热力学或名称自动添加逆反应。材料与体积恒定，不求温度、压力、扩散或气液交换；单条反应守恒输入摩尔质量。',
'reactive-transport':'一维恒截面不可压缩稀溶液，以+x为正方向的速度v、各D_i>0恒定，组分不反馈流场或密度。反应速率v_r=a_r∏_i(c_i/c*)^α_ri，0^0=1，S_i=Σ_r(β_ri−α_ri)v_r。∂t c_i+v∂x c_i=D_i∂xx c_i+S_i。两端均给定浓度Dirichlet条件，即便某端为流出端也不改成零梯度或Danckwerts条件；有限扩散使此连续问题成立。等温，无湍流闭合、热反馈或自发逆反应。',
'adiabatic-combustion':'各独立完全混合、封闭、刚性定容理想气体反应器绝热，无流动功、热损失或外源。v_r=a_r exp(−E_r/(RT))∏_i(c_i/c*)^α_ri，0^0=1；dc_i/dt=Σ_r(β_ri−α_ri)v_r。u_i(T)=u_i,ref+cv_i(T−Tref)，单位体积总内能U=Σ_i c_i u_i(T)始终等于初态U0；因此(Σ_i c_i cv_i)dT/dt=−Σ_i u_i(T) dc_i/dt。压力p=RTΣ_i c_i。形成内能已包含在u_i,ref，不另加反应热。全部反应不可逆且质量守恒，允许惰性组分及多步反应；不根据名称引入数据库、辐射、解离平衡或反向速率。仅支持cv常量适用且全过程250≤T≤5000K的有限机理，初始总浓度严格正。燃烧考查组成与温度的热反馈，可含自加速点火，不要求输出阈值点火延迟或传播火焰。',
'partition-transfer':'多个封闭、等温、固定体积的完全混合相容器，通过任意有限传质网络交换同一组分，无反应或体积流动。连接e由a指向b，N_ei=G_ei(c_ai−c_bi/K_ei)，单位mol/s；V_a dc_ai/dt为入向连接N之和减去出向连接N之和。K是平衡时c_b/c_a，不是分配质量分数。N可负，反向净流不截零；隔离容器与平行连接均允许，各连接独立计入，同一容器不能自连。初态给定后网络库存Σ_a V_a c_ai守恒，不强制所有连接瞬间达平衡。'
}

def size(s):return '['+','.join(map(str,s['shape']))+']'
def desc(s):return f'{s["kind"]} {size(s)}，`{s["unit"]}`；{s["meaning"]}'
def build(selected=None):
    CH.mkdir(parents=True,exist_ok=True)
    index=['# 第九章 组分传输与化学反应分析\n\n7节8题；正式数据、参考解和发布留后。考生只需逐题instruction、DATA及通用CONTRACT。\n']
    for section,title,slugs in SECTIONS:
        index.append(f'- [{section.split("-")[0]} {title}]({section}/README.md)')
        if selected and section not in selected:continue
        d=CH/section;d.mkdir(exist_ok=True)
        (d/'README.md').write_text(f'# {section.split("-")[0]} {title}\n\n'+'\n'.join(f'- [{i+1} {M[s]["name"]}]({s}/instruction.md)' for i,s in enumerate(slugs))+'\n')
        for j,slug in enumerate(slugs,1):
            c=M[slug];t=d/slug;t.mkdir(exist_ok=True);transport=c['transport'];p=c['parameters']
            number=section.split('-')[0]+'.'+str(j)
            score='\n'.join(f'| `{q}` | {s["atol"]} | {s["rtol"]} | `{s["unit"]}` |' for q,s in c['outputs'].items())
            instruction=f'''# {number} {c['name']}

实现可复用求解器，覆盖本题全部公开问题族，冻结后处理多个未见算例。{PHYS[slug]}

算例变化材料、初态、时间和{'端部历史、尺度及接收位置' if transport else '容器、传质连接及交换参数' if slug=='partition-transfer' else '对象及吸脱附参数' if slug=='competitive-adsorption' else '对象及反应动力学参数'}。上述物理响应固定；考生负责建模落地、内部离散或积分、稳定性与误差控制。语言、软件和算法自由，覆盖完整契约的解析或降阶方法同样有效，不要求复现参考算法。输入输出由[本题DATA](DATA.md)及[通用CONTRACT](../../../../docs/CONTRACT.md)完整定义。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64，{c['timeout']}秒墙钟（含启动与I/O）、2CPU、4096MB、0GPU，逐例无网络；程序须0退出且完成HDF5写入，无独立输出字节上限。生成求解器3600秒，构建1800秒。环境预置Python3、NumPy、SciPy、h5py、Gmsh、jsonschema以及C++/OpenMP/OpenMPI/HDF5，不强制Python。

规模见DATA：s≤8，输出帧≤129，输入及输出各≤2000000数值分量。资源与容差是待校准设计目标；正式数据须有相同预算内可达精度的独立基准，不以参数形式合法推断任意病态或无限刚性问题可测。

## 评分

每有效例正常退出、输出合法且全部帧／对象／组分满足`|结果−参考|≤atol(quantity)+rtol(quantity)|参考|`得1分，否则0分；等号接受，不做归一化、时间对齐、截零或组分重排。

| quantity | atol | rtol | 单位 |
|---|---|---|---|
{score}

总成绩为通过有效例数／有效例数，无有效例不产生成绩。输入、参考、配置及工具错误属于基础设施错误，不计为考生失败。结构、dtype、有限值及身份按CONTRACT检查；工具通过不证明物理准确性、参考精度或预算已经校准。
'''
            (t/'instruction.md').write_text(instruction)
            params='\n'.join(f'| `{k}` | `{v["unit"]}` | {v["meaning"]} |' for k,v in p.items())
            locs='\n'.join(f'| `{k}` | {v["kind"]}，{v["minimum"]}..{v["maximum"]}项 | {v["meaning"]} |' for k,v in c['locations'].items())
            time='time_axes恰为initial、boundary、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0、末项H>0；boundary引用float64[B]，2≤B≤129，首项0、末项H；中间严格递增。输出仅用observe；材料与初态用initial；两端条件用boundary。' if transport else 'time_axes恰为initial、observe。initial引用float64[1]=[0.0]；observe引用float64[T]，1≤T≤129，首项≥0、末项H>0；输出仅用observe，所有输入场仅用initial。'
            fields='''场均float64，形状[T,N,*component_shape]。scalar固定shape=[1]、components=["value"]；components类型按表中shape行优先展平为["c1",...,"cL"]，L为分量总数。s替换为species_count；所有组分按i=1..s，同一算例各表始终同序，标签不表示化学名称。逻辑字段名与HDF5 array key自由且区分；quantity等于data键名，键value例外等于该条件variable。引用只能同location、同规定时间轴，fields恰为被条件实际引用的字段，无未用字段。

所有data均必须采用{"field":"逻辑字段名"}，不接受内联数值、option或数组；表中每种operator恰一条，data键全集如下，无可选键／缺省参数或其他条件。每字段均point；sampling显式，extrapolation=forbid。材料与所有entities场space=uniform、time=constant，表示各对象固定属性／初态，不作对象间插值；uniform不要求不同实体行的值相同，各行独立给定。'''
            if transport:fields+='初态knots场space=piecewise_linear、time=constant，在相邻结点按x逐组分线性重建，含两端；端部场space=uniform、time=linear，在boundary相邻时刻逐组分线性插值，覆盖[0,H]不外推。初态浓度两端与各端t=0边界值必须相等（存储float64精确相等），无不相容角点。'+('q初态只按knots重建，不施加边界值。' if slug=='pore-adsorption' else '')+''
            records=[]
            for op,r in c['records'].items():records.append(f'### `{op}`\n\nrole=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`，location=`{r["location"]}`；时间轴`{r["axis"]}`，完整覆盖该位置。data恰含：\n\n| 键 | 类型、单位、语义与限制 |\n|---|---|\n'+'\n'.join(f'| `{k}` | {desc(v)} |' for k,v in r['data'].items()))
            output='\n'.join(f'| `{q}` | {desc(s)} | `{s["location"]}` |' for q,s in c['outputs'].items())
            extra=''
            if slug in REACTION:extra+='reactions对象数恰为reaction_count；反应矩阵每个实体行是一条反应，每个分量是组分i，非转置矩阵。每行α和β均非零且不相等；α行和1..4、β行和1..8。质量声明检查每反应要求abs(Σ_i(β−α)M_i)≤1e−12·Σ_i(β+α)M_i，生产数据保证真实质量守恒；不投影／修正原计量或质量。归一化活度是无量纲c_i/c*，前因子单位固定mol/(m3.s)，不能直接当成传统k使用。'
            if slug in ADSORPTION:extra+='初始每个位置Σq_i≤qmax，且q_i≥0；ka、kd均允许为0，不额外假设已达平衡。'
            if slug=='adiabatic-combustion':extra+='每个反应器初始Σc_i>0、250≤T0≤5000K；全过程温度界限及气体模型适用性由数据建设独立验证，声明检查不以仅初温合法证明全过程适用。'
            if slug=='partition-transfer':extra+='links端点字段为float64但值须精确整数且≤2^53−1，引用实际vessels ID；vessels ID同样≤2^53−1。端点不能自连；允许非连续ID、平行连接和隔离容器。初态、V和所有边参数均按本表身份关联，不按ID大小推测相类型。'
            data=f'''# {slug} 数据契约

入口problem.json及data_file引用的扁平HDF5，路径相对清单；顶层采用CONTRACT通用结构。physics恰含model、parameters，model=`species-{slug}-v1`；task可省略，出现须为`{slug}`。禁止profile、contract_version、analysis、materials混用。不接受未列字段、位置、条件或参数组合。

## 物理与支持范围

{PHYS[slug]}

## 全局参数

parameters恰含下表全部项；每项只有value、unit，数值有限、布尔不是数值、integer必须JSON整数；全部参数无缺省。

| 参数 | 单位 | 含义及值域 |
|---|---|---|
{params}

## 几何、位置和身份

spatial_dimension=1；meshes、geometries均为空。{'所有points坐标为float64[N,1]、单位m；这些点只描述初态、边界或观测，不指定内部离散。' if transport else 'entities表示实际混合容器、反应或参数对象，无虚构坐标；空间维度1仅为此有限维模型的存储标记，不引入空间方程。'}IDs按CONTRACT非负、严格递增，实体行与字段N轴对应，ID不能作数组下标。

| location | kind及数量 | 完整语义 |
|---|---|---|
{locs}

## 时间、数组与重建

{time}输出请求不约束求解器内部时间步，也不表示帧间跳跃。物理初态固定t=0，不是迭代初猜。

{fields}

## 条件全集

{chr(10).join(records)}

## 输出

每个下列quantity至少一次，可重复请求；逻辑名及array key自由，不得修改quantity、单位、location或分量。输出均float64、point、引用observe，不含sampling。形状及components按上文规则；各输出是相应时刻与对象的瞬时状态，不是时间平均或积分。

| quantity | 类型、单位和含义 | 完整位置 |
|---|---|---|
{output}

结果HDF5只含输出array及必需IDs／时间轴，严格复制输入身份和顺序；不导出输入场、坐标或额外数组。{('恰好t=0的探针输出按初态空间重建。' if transport else '恰好t=0的浓度／负载取对应初态。' if slug=='competitive-adsorption' else '恰好t=0的浓度和温度取初态，压力按本题公式由初态计算。' if slug=='adiabatic-combustion' else '恰好t=0的浓度取初态，摩尔流率按本题公式由初态计算。' if slug=='partition-transfer' else '恰好t=0的浓度取初态。')}

## 接收限制与组合

{extra}

对象数量及参数范围见上表，输入与输出场各至多2000000数值分量。除显式声明检查外，正式数据还须独立核验材料模型适用、连续问题适定、所请求观测存在、非负物理解及预算内参考精度；排除任意病态尺度和无限刚性组合。声明校验不证明物理／数值准确性。无正式样例时不从目录名、来源软件或文件顺序推导任何额外条件。
'''
            (t/'DATA.md').write_text(data)
            policy={'version':2,'quantities':{q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()}}
            (t/'grading.json').write_text(json.dumps(policy,indent=2)+'\n')
            (t/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n')
            (t/'harbor').mkdir(exist_ok=True)
            (t/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 2\nmemory_mb = 4096\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n')
            (t/'harbor/requirements.txt').write_text('scipy==1.18.1\n')
    index.append('\n维护：[章规划](../design/chapter-09-species-reactions.md)、[逐题清单](../design/chapter-09-task-plan.md)、[进度](../design/reviews/chapter-09-progress.md)。\n')
    (CH/'README.md').write_text('\n'.join(index))
    target=ROOT/'qbank/extensions/caeoj_ext/species';target.mkdir(exist_ok=True)
    (target/'models.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    import sys
    build(sys.argv[1:] or None)
