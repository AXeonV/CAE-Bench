"""Expand standalone granular contracts/configs; no data or reference generator."""
from pathlib import Path
import json
import math

ROOT=Path(__file__).resolve().parents[3]
CH=ROOT/'qbank/12-granular'
SECTIONS=[('12.1-motion','颗粒受力运动',['granular-forced-motion']),
          ('12.2-collision','耗散碰撞',['granular-normal-contact']),
          ('12.3-friction','摩擦与自转',['granular-sliding-friction']),
          ('12.4-adhesion','黏附',['granular-cohesive-contact']),
          ('12.5-assembly','散体整体响应',['granular-periodic-assembly']),
          ('12.6-population','粒群分布演化',['granular-coagulation','granular-fragmentation'])]


def P(unit,meaning,lo,hi,integer=False):
    return dict(unit=unit,meaning=meaning,lower=lo,upper=hi,integer=integer)


def F(unit,meaning,location,axis='static',kind='scalar',shape=None,lo=None,hi=None):
    return dict(unit=unit,meaning=meaning,location=location,axis=axis,kind=kind,
                shape=shape or ([3] if kind=='vector' else [3,3] if kind=='tensor' else [1]),lower=lo,upper=hi)


MODELS={}
names=['受力与阻力下的颗粒运动','多球法向耗散碰撞','滑动摩擦与球体自转','有限程黏聚颗粒动力学','周期散体的宏观力学响应','离散粒群聚并','离散粒群破碎']
for slug,name in zip([s for _,_,ss in SECTIONS for s in ss],names):
    pop=slug in ('granular-coagulation','granular-fragmentation')
    c=dict(name=name,population=pop,dimension=1 if pop else 3,parameters={},inputs={},outputs={},locations={},timeout=300 if pop or slug=='granular-forced-motion' else 900)
    MODELS[slug]=c
    p,ins,outs,loc=c['parameters'],c['inputs'],c['outputs'],c['locations']
    def out(q,s,atol,rtol):outs[q]=dict(s,atol=atol,rtol=rtol)
    if pop:
        p.update(bin_count=P('1','粒级数K，JSON整数',2,64,True),monomer_volume=P('m3','每个基础体积单元v0',1e-24,1e-6))
        loc.update(bins=dict(minimum=2,maximum=64,meaning='IDs恰为1..K，第k级体积为k v0，不是粒径或质量'),system=dict(minimum=1,maximum=1,meaning='唯一均匀粒群总体'))
        ins['initial_density']=F('1/m3','初始各级数量密度n_k(0)，非概率/体积分数','bins','initial',lo=0,hi=1e24)
        if slug=='granular-coagulation':ins['collision_kernel']=F('m3/s','对称聚并核A_ij，包含碰撞效率，不额外乘体积','system',kind='components',shape=['K','K'],lo=0,hi=1)
        else:
            ins['breakage_rate']=F('1/s','各级破碎频率a_k，a_1=0','bins',lo=0,hi=1e8)
            ins['daughter_count']=F('1','b_jk为一个第k级母粒子产生第j级子粒子的期望数量','system',kind='components',shape=['K','K'],lo=0,hi=64)
        out('size_density',F('1/m3','各级n_k(t)','bins','observe'),1e-3,.002)
        out('number_density',F('1/m3','Σ_k n_k(t)','system','observe'),1e-3,.002)
        out('solid_fraction',F('1','v0 Σ_k k n_k(t)，本题为稀相名义固相体积分数','system','observe'),1e-10,.002)
    else:
        loc['particles']=dict(minimum=1,maximum=128,meaning='具有固定ID的球形颗粒；位置是未知状态，不用固定points伪装运动颗粒')
        ins.update(mass=F('kg','粒子质量m_i','particles',lo=1e-12,hi=10),radius=F('m','固定球半径R_i','particles',lo=1e-6,hi=.1),drag=F('kg/s','相对静止背景的线性平动阻力系数b_i','particles',lo=0,hi=1e4),
                   initial_position=F('m','t=0质心位置x_i','particles','initial','vector',lo=-100,hi=100),initial_velocity=F('m/s','t=0平动速度v_i','particles','initial','vector',lo=-1e3,hi=1e3),external_force=F('N','已包含重力等全部外加力，不再额外加g或浮力','particles','drive','vector',lo=-1e4,hi=1e4))
        if slug!='granular-forced-motion':p.update(stiffness=P('N/m','公共法向弹性刚度k',1e-4,1e7),normal_damping=P('kg/s','公共法向阻尼γ，无隐藏质量乘数',0,1e3))
        if slug=='granular-sliding-friction':
            p.update(friction=P('1','摩擦系数μ',0,2),slip_speed=P('m/s','正则化滑动速度v_s',1e-8,10))
            ins.update(initial_spin=F('1/s','初始全局角速度ω_i，弧度按无量纲','particles','initial','vector',lo=-1e6,hi=1e6),external_torque=F('N.m','外加力矩τ_i','particles','drive','vector',lo=-1e4,hi=1e4),spin_drag=F('kg.m2/s','相对静止背景的转动阻力bω_i','particles',lo=0,hi=1e4))
        if slug=='granular-cohesive-contact':p.update(cohesive_force=P('N','吸引力幅值F0',0,1e3),interaction_range=P('m','表面间隙的吸引程a',1e-8,.01))
        if slug=='granular-periodic-assembly':
            p['box_length']=P('m','固定立方周期代表体边长L',1e-4,10)
            loc['system']=dict(minimum=1,maximum=1,meaning='唯一周期代表体；整体物理属性使用entities状态，不伪装网格积分')
            out('stress',F('Pa','拉应力为正的完整Cauchy张量σ','system','observe','tensor'),1e-5,.003)
            out('kinetic_energy',F('J','相对质量加权平均速度的平动涨落动能','system','observe'),1e-12,.003)
            out('coordination',F('1','2 Nc/N，包括无接触粒子，Nc为δ>0的无序对数','system','observe'),1e-9,0)
            out('solid_fraction',F('1','Σ_i 4πRi³/(3L³)，不扣除软球重叠体积','system','observe'),1e-10,1e-6)
        else:
            out('position',F('m','逐粒子的全局质心位置','particles','observe','vector'),1e-9,0)
            out('velocity',F('m/s','逐粒子的全局平动速度','particles','observe','vector'),1e-7,1e-4)
            if slug=='granular-sliding-friction':out('angular_velocity',F('1/s','逐粒子的全局角速度','particles','observe','vector'),1e-6,1e-4)

NEWTON='三维球形颗粒，质量和半径恒定，dx_i/dt=v_i，m_i dv_i/dt=Fext_i(t)−b_i v_i+Σ_j Fij。外力是已合成的实际力，背景静止，不自行增加重力、浮力、随机力或流体反馈。所有相互作用按无序对i<j各算一次，Fji=−Fij，允许同时多接触，不顺序执行两两瞬时速度跳跃。'
NORMAL='令r=x_i−x_j，d=|r|>0，n=r/d从j指向i，δ=Ri+Rj−d，vn=(vi−vj)·n。δ>0时P=max(0,kδ−γ vn)，否则P=0；法向力为P n，γ直接以kg/s使用，不乘约化质量。δ=0时按非接触取P=0。'
PHYSICS={
    'granular-forced-motion':'三维无相互作用球形粒子，dx_i/dt=v_i，m_i dv_i/dt=Fext_i(t)−b_i v_i。背景静止、阻力线性，外力已包含重力等全部效应，不反求流场、不加布朗力。粒子可重叠或穿越，半径仅为对象属性，不进行碰撞、约束或自转计算。',
    'granular-normal-contact':NEWTON+NORMAL+'无切向力、黏附、墙、周期边界或自转方程；物理域为无界三维空间。',
    'granular-sliding-friction':NEWTON+NORMAL+'接触时取共同接触点的力臂ℓi=Ri−δ/2、ℓj=Rj−δ/2，故ℓi+ℓj=d；vt=vi−vj−(ℓiωi+ℓjωj)×n−vn n，Ft=−μP vt/sqrt(|vt|²+vs²)，Fij=P n+Ft；非接触时Ft=0。该单值滑动响应没有静摩擦、切向弹簧、历史变量、滚动或扭转阻力，不用理想Coulomb集合值条件代替。颗粒为均匀实心球，Ii=2miRi²/5，Ii dωi/dt=τext_i−bω_i ωi+Σ_j τij，τij=(−ℓi n)×Ft，τji=(−ℓj n)×Ft；公式中的n及Ft均取i<j方向。球形无取向相关性质，不输出四元数；无墙或周期边界。',
    'granular-cohesive-contact':NEWTON+NORMAL+'定义表面间隙s=d−Ri−Rj。只有0<s<a时Q=−F0 sin(πs/a)，其余Q=0（含s=0及a）。Fij=(P+Q)n；允许未接触粒子在吸引程内被吸引，脱离不保留粘结标记。该可逆有限程响应不等同JKR/DMT，不含滞回、塑性、烧结、切向力或自转；无墙或周期边界。',
    'granular-periodic-assembly':NEWTON+'本题固定立方体在三个方向周期延拓；位置轨迹保留连续未包裹x。计算相互作用时逐分量取r=x_i−x_j−L floor((x_i−x_j)/L+1/2)，取最近像；不与自身镜像相互作用。'+NORMAL.replace('令r=x_i−x_j，','令')+'此处r始终是上述最近像位移，不用未包裹位置差覆盖。初始位置在[0,L)³，输出仅宏观状态，不请求位置。V=L³，vbar=Σ mi vi/Σ mi，ci=vi−vbar。σ=−(Σ_i mi ci⊗ci+Σ_{i<j} r_ij⊗Fij)/V，拉为正；各对用同一最近像r和其作用在i上的Fij，不重复计数、不除2。Ekin=Σ mi|ci|²/2，配位数Z=2Nc/N（Nc恰为δ>0的对数，不以P>0计），φ=Σ4πRi³/(3V)。无自转、摩擦、黏附、墙或盒形变；名义堆积率不扣重叠。不是把颗粒应力除以各自任意体积后平均，也不把平均流动动能计入涨落应力。',
    'granular-coagulation':'均匀稀相粒群，粒级k代表体积k v0，n_k为每实际总体积内的粒子数密度。对1≤k≤K，dn_k/dt=(1/2)Σ_{i+j=k}A_ij n_i n_j−n_k Σ_{j:k+j≤K}A_kj n_j。所有求和为有序索引，增益1/2避免双计，损失不加1/2；i=j一次碰撞消耗两个同类粒子已由公式处理。i+j>K的碰撞整个禁用，不生成溢出粒级、也不作为损失/截断汇。不含破碎、空间输运、外部进料或沉降。对称非负核已给，不再根据粒径选择碰撞模型；v0 Σ k n_k守恒。',
    'granular-fragmentation':'均匀稀相粒群，粒级k体积k v0，n_k为每总体积数密度。dn_j/dt=Σ_{k=j+1}^K a_k b_jk n_k−a_j n_j。a1=0，b_jk=0对j≥k；对每k≥2有Σ_{j=1}^{k−1}j b_jk=k。b为期望子粒子个数，可为非整数，不是概率或质量分数；每个母粒子的事件频率a乘一次，不额外除/乘子粒子总数。即使a_k=0，b的该列仍须完整守恒。无聚并、外部源、输运或粒级外碎屑；v0 Σ k n_k守恒。'
}


def shape(s,p):return [p['bin_count'] if x=='K' else x for x in s['shape']]


def labels(s,p):
    return ['value'] if s['kind']=='scalar' else ['x','y','z'] if s['kind']=='vector' else ['xx','xy','xz','yx','yy','yz','zx','zy','zz'] if s['kind']=='tensor' else ['c'+str(i+1) for i in range(math.prod(shape(s,p)))]


def main():
    ext=ROOT/'qbank/extensions/caeoj_ext/granular';ext.mkdir(parents=True,exist_ok=True)
    (ext/'models.json').write_text(json.dumps(MODELS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    toc=[]
    for sec,title,slugs in SECTIONS:
        sd=CH/sec;sd.mkdir(parents=True,exist_ok=True);links=[]
        for i,slug in enumerate(slugs,1):
            c=MODELS[slug];td=sd/slug;td.mkdir(exist_ok=True);num=sec.split('-')[0]+'.'+str(i)
            links.append(f'- [{num} {c["name"]}]({slug}/instruction.md)')
            ins=f'# {num} {c["name"]}\n\n实现覆盖公开问题族的可复用求解器，冻结后同一提交处理多个未见算例。\n\n'+PHYSICS[slug]+'\n\n输入明确的材料属性、初态、载荷及采样可变化，不能按某个特定算例硬编码。物理响应固定如上，考生负责数值方法、时间积分、必要的相互作用处理及误差控制，语言与软件自由；不要求复现某参考算法。\n\n运行入口`python solve.py --input <input_json> --output <output_h5>`，允许入口调用其他语言程序。资源相对输入清单定位，从任意工作目录运行；每例无网络，0退出并写完HDF5。Linux AMD64、2CPU、2048MB、0GPU，每例墙钟'+str(c['timeout'])+'秒（含启动与I/O）；生成3600秒、构建1200秒。输出无独立字节上限，但受公开数组规模及内存限制。\n\n每个输出的全部时刻、对象和分量均须满足`|结果−参考|≤atol+rtol×|参考|`，等号通过，无旋转/平移/时间重对齐或背景偏移拟合，不按平均误差豁免个别点。结构合法、正常结束且全部quantity通过才通过该例。总成绩为通过例数/计划例数，各例等权；超时、程序错误、缺输出及非法输出为该例失败。输入、参考、配置或工具错误中止评测，不算考生失分。\n\n| quantity | 单位 | atol | rtol |\n|---|---|---:|---:|\n'
            for q,s in c['outputs'].items():ins+=f'| {q} | `{s["unit"]}` | {s["atol"]} | {s["rtol"]} |\n'
            ins+='\n资源与容差为本版公开设计目标，正式数据须有独立适用性、收敛与预算证据，尚未完成校准。输入输出详见[DATA.md](DATA.md)、通用存储规则见[CONTRACT.md](../../../../docs/CONTRACT.md)。\n'
            if slug=='granular-forced-motion':ins=ins.replace('必要的相互作用处理及','')
            (td/'instruction.md').write_text(ins,encoding='utf-8')
            data=f'# {num} 数据契约\n\n仅本题instruction、DATA及通用CONTRACT定义要求；以下为格式定义，不是可运行数值样例。\n\nphysics恰含model、parameters；model=`{slug}-v1`，task若给须为`{slug}`。spatial_dimension={c["dimension"]}；meshes、geometries均为空，不混用profile/analysis/materials/contract_version。'
            data+=('spatial_dimension仅为有限维粒群的存储标记，不引入空间方程。' if c['population'] else '坐标为全局三维笛卡尔，长度m、时间s；移动位置由状态字段给出。')
            data+='\n\nparameters恰含下表键，每项恰为value、unit，无默认、无隐式换算；数值有限，bool不能充当数值，整数必须为JSON整数。'+('本题parameters为空对象。' if not c['parameters'] else '')+'\n\n| 参数 | unit | 范围与含义 |\n|---|---|---|\n'
            for key,s in c['parameters'].items():data+=f'| {key} | `{s["unit"]}` | {s["lower"]}≤value≤{s["upper"]}；{s["meaning"]} |\n'
            data+='\nlocations恰含下表，全部kind=entities，仅含kind、ids。IDs为非负严格递增int64，除明确的bins身份规则外，不按ID大小猜属性或坐标。实体场value_kind=point指对象自身属性/状态，不是空间点、单元平均或区域积分。\n\n| location | 数量 | 对象 |\n|---|---|---|\n'
            for key,s in c['locations'].items():data+=f'| {key} | {s["minimum"]}..{s["maximum"]} | {s["meaning"]} |\n'
            axes={'static','initial','observe'}|({ 'drive'} if not c['population'] else set())
            data+='\ntime_axes恰含'+', '.join('`'+x+'`' for x in sorted(axes))+'。static与initial各为[0.0]单帧，前者材料常数、后者物理初态，允许共用数组key。observe含1..256个严格递增时刻，0≤t≤tend、0<tend≤10 s，末项为tend；可请求t=0状态。'
            if not c['population']:data+='drive含2..512个严格递增时刻，首项0、末项恰tend，逐粒子外载在相邻驱动时刻逐分量线性插值，不外推；observe无需与drive重合，内部时间步自行选择。'
            else:data+='所有核和材料响应在整个分析时间内保持不变；输出时刻不约束内部步长。'
            data+='\n\nfields逻辑名和array key自由且不必相同；下列quantity各恰一个输入，禁止额外或未引用场，所有输入仅接受field，不允许常量/option代替。dtype=float64，value_kind=point，数组[T,N,*shape]保留全部轴。sampling恰为space=uniform、time='+('linear（drive轴）/constant（其他轴）' if not c['population'] else 'constant')+'、extrapolation=forbid。uniform不表示不同实体同值，不进行实体之间的插值。\n\n| 输入quantity | location | time_axis | kind/shape | unit | 范围与含义 |\n|---|---|---|---|---|---|\n'
            for q,s in c['inputs'].items():
                bound=('逐分量'+str(s['lower'])+'..'+str(s['upper'])) if s['lower'] is not None else '有限'
                data+=f'| {q} | {s["location"]} | {s["axis"]} | {s["kind"]} {s["shape"]} | `{s["unit"]}` | {bound}；{s["meaning"]} |\n'
            data+='\nscalar固定shape=[1]、components=["value"]。'
            if not c['population']:data+='vector固定[3]及x/y/z；tensor固定[3,3]及xx,xy,xz,yx,yy,yz,zx,zy,zz，不用Voigt。'
            else:data+='表中K=bin_count，components矩阵shape=[K,K]，标签按行优先为c1..c(K²)；矩阵不展平为数组轴，最后一轴变化最快。'
            data+='\n\nconditions每个输入quantity恰一条，variable等于quantity，location同表，operator=prescribed，data恰为`{"value":{"field":"该输入场逻辑名"}}`。role：initial轴为initial、'+('drive轴为source、' if not c['population'] else '')+'static轴为material。顺序任意，无重复或隐藏条件。\n\n物理语义：\n\n'+PHYSICS[slug]+'\n\n'
            if c['population']:
                data+='bins数量恰K；每个量数组行与bins的1..K身份一致；system恰一个对象。初始φ=v0 Σ k n_k≤0.1，保证稀相，本题φ为全局实体属性而非网格体积积分。'
                if slug=='granular-coagulation':data+='A矩阵第i行第j列为A_ij，要求|A_ij−A_ji|≤1e−12 max(1e−30,max|A|)。公式直接使用存储值；正式数据保证精确对称，工具容差不授权考生平均/投影矩阵。难度界tend max(A) Σ n_k(0)≤1e5。'
                else:data+='b矩阵行j为子粒级、列k为母粒级；所有j≥k项必须精确0，a1必须精确0，每k≥2列的加权和与k差≤1e−12 k；按原值计算，不自行归一化。难度界tend max(a)≤1e5。'
            else:
                data+='合法问题族要求全程每个位置分量|x|≤100 m、速度分量|v|≤1000 m/s，含自转时每分量|ω|≤1e6/s；这些响应尺度是正式数据须独立验证的适用条件，声明校验不演化轨迹。各粒子的质量、半径及阻力与初态/驱动按同一particles身份逐行关联，不能重排。难度界tend max_i(b_i/m_i)≤1e5。'
                if slug=='granular-forced-motion':data+='另用输入充分界逐粒子逐分量要求|x0|+tend |v0|+tend² max_drive|Fext|/(2mi)≤100 m，排除绝对位置误差低于float64可分辨尺度的输入。'
                if slug!='granular-forced-motion':data+='另有tend sqrt(k/min_i mi)≤1e5、tend γ/min_i mi≤1e5；全演化每对中心d>0且δ≤0.05 min(Ri,Rj)，排除中心重合及大变形。工具仅检查初态，正式数据须独立验证全程条件、事件附近收敛及短时轨迹可重复精度，不能用碰撞后不受控的混沌放大掩盖逐值判据。'
                if slug=='granular-sliding-friction':data+='另要求tend max_i(bω_i/Ii)≤1e5。令Psum=(N−1)[0.05 k max(R)+2000 sqrt(3) γ]，它根据小重叠与全程速度界给出每粒子法向力之和的保守上界；要求tend μ Psum max_i(1/mi+Ri²/Ii)/vs≤1e5，控制正则化滑动刚性。静摩擦滞回不是本题输入分支。'
                if slug=='granular-cohesive-contact':data+='另要求tend sqrt(πF0/(min_i mi a))≤1e5，控制有限程黏聚振荡难度。'
                if slug=='granular-periodic-assembly':data+='每对Ri+Rj<0.49L，保证接触不涉及最近像半盒歧义，单颗粒也须2Ri<0.49L；初态坐标各分量在[0,L)，运动时不包裹状态。输出时刻每对|δ|≥1e−8 min(Ri,Rj)，使配位计数避开刚接触/脱离的阈值；该全程/输出适用承诺需正式数据独立验证。名义φ≤0.74。'
            data+='\n\noutputs逻辑名和array key自由且唯一，每个下表quantity至少一次，允许多个独立命名的同quantity输出，逐个评分；禁止其他quantity。全部float64、value_kind=point、time_axis=observe，无sampling，分量标签沿上述规则。\n\n| quantity | location | kind/shape | unit | 含义 |\n|---|---|---|---|---|\n'
            for q,s in c['outputs'].items():data+=f'| {q} | {s["location"]} | {s["kind"]} {s["shape"]} | `{s["unit"]}` | {s["meaning"]} |\n'
            data+='\n结果只含全部outputs.array及所引用的IDs和observe时间数组，须逐值精确复制轴；不输出输入场、坐标、附加诊断或元数据。场数组为[T,N,*shape]，全部有限，不省轴、重排或悄悄截断。输入场总标量数与请求输出总标量数各≤2000000。HDF5扁平布局及dtype等通用细节依CONTRACT。结构通过不证明物理适用、数值正确或参考可信。\n'
            if not c['population']:data=data.replace('除明确的bins身份规则外，','')
            if slug!='granular-sliding-friction':data=data.replace('，含自转时每分量|ω|≤1e6/s','')
            if slug!='granular-periodic-assembly':data=data.replace('；tensor固定[3,3]及xx,xy,xz,yx,yy,yz,zx,zy,zz，不用Voigt。','。')
            (td/'DATA.md').write_text(data,encoding='utf-8')
            policy=dict(version=2,quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()})
            (td/'grading.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
            (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=180,per_case_overhead_seconds=60)),indent=2)+'\n',encoding='utf-8')
            (td/'harbor').mkdir(exist_ok=True)
            (td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1200.0\ncpus = 2\nmemory_mb = 2048\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n',encoding='utf-8')
        (sd/'README.md').write_text('# '+sec.split('-')[0]+' '+title+'\n\n'+'\n'.join(links)+'\n',encoding='utf-8')
        toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
    (CH/'README.md').write_text('# 第十二章 颗粒与散体力学分析\n\n6节7题；题面与DATA逐题自包含，正式数据、参考与发布留后。\n\n'+'\n'.join(toc)+'\n\n维护入口：[章规划](../design/chapter-12-granular.md)、[逐题清单](../design/chapter-12-task-plan.md)、[进度与证据](../design/reviews/chapter-12-progress.md)。\n',encoding='utf-8')


if __name__=='__main__':main()
