"""Maintain independent semiconductor statements and declarations, never case data."""
from pathlib import Path
from caeoj_tools.author import public_model_catalog
import json

ROOT = Path(__file__).resolve().parents[3]
CH = ROOT / 'qbank/11-semiconductor'
SECTIONS = [
    ('11.1-equilibrium', '电荷与热平衡', ['semiconductor-equilibrium']),
    ('11.2-drift-diffusion', '双极载流子输运', ['semiconductor-drift-steady', 'semiconductor-drift-transient']),
    ('11.3-recombination', '产生、复合与俘获', ['semiconductor-bulk-recombination', 'semiconductor-trap-kinetics']),
    ('11.4-minority', '少数载流子', ['semiconductor-minority-diffusion']),
    ('11.5-ballistic', '弹道电子输运', ['semiconductor-landauer']),
    ('11.6-quantum', '量子限域', ['semiconductor-effective-mass']),
]


def par(unit, meaning, lower=None, upper=None, positive=False, integer=False):
    return dict(unit=unit, meaning=meaning, lower=lower, upper=upper, positive=positive, integer=integer)


def field(unit, meaning, location, axis='static', lower=None, upper=None, positive=False, shape=None):
    return dict(unit=unit, meaning=meaning, location=location, axis=axis, lower=lower,
                upper=upper, positive=positive, shape=shape or [1])


MODELS = {}
NAMES = ['非简并半导体热平衡', '双极漂移扩散稳态', '双极漂移扩散瞬态',
         '均匀半导体体复合动力学', '单能级陷阱俘获动力学', '少数载流子扩散复合',
         '双储库弹道电流与热流', '分层有效质量量子态']
for slug, name in zip([s for _, _, ss in SECTIONS for s in ss], NAMES):
    c = dict(name=name, parameters={}, locations={}, inputs={}, outputs={}, timeout=300)
    MODELS[slug] = c
    p, loc, ins, outs = c['parameters'], c['locations'], c['inputs'], c['outputs']
    def location(k, kind, lo, hi, meaning):
        loc[k] = dict(kind=kind, minimum=lo, maximum=hi, meaning=meaning)
    def output(q, unit, meaning, location, axis, atol, rtol=.002, shape=None):
        outs[q] = dict(field(unit, meaning, location, axis, shape=shape), atol=atol, rtol=rtol)
    spatial = slug in ('semiconductor-equilibrium', 'semiconductor-drift-steady', 'semiconductor-drift-transient', 'semiconductor-minority-diffusion')
    drift = slug.startswith('semiconductor-drift-')
    transient = slug in ('semiconductor-drift-transient', 'semiconductor-bulk-recombination', 'semiconductor-trap-kinetics', 'semiconductor-minority-diffusion')
    c['transient'] = transient
    if spatial:
        p['length'] = par('m', '区间长度L，0<x<L', 1e-9, 1e-2)
        location('profile', 'points', 2, 1024, '包含x=0及x=L的剖面结点，按ID行序x严格递增；输入重建支撑，不是指定求解网格')
        location('receivers', 'points', 1, 256, '严格位于0<x<L的输出点；ID行序不要求坐标递增，允许重复坐标')
        location('contacts', 'points', 2, 2, '第一行x=0，第二行x=L的真实边界点')
    if slug == 'semiconductor-equilibrium' or drift:
        p.update(temperature=par('K', '等温温度T', 200, 500), permittivity=par('F/m', '绝对介电常数ε', 1e-12, 1e-9), intrinsic_density=par('1/m3', '本征密度ni', 1e8, 1e23))
        ins['doping'] = field('1/m3', '完全电离的净掺杂C=ND−NA，允许正负及零', 'profile', lower=-1e25, upper=1e25)
        ins['contact_potential'] = field('V', '两端电势ψ，绝对基准由输入固定', 'contacts', 'drive' if transient else 'static', lower=-2, upper=2)
        axis = 'observe' if transient else 'static'
        output('potential', 'V', 'ψ(x,t)', 'receivers', axis, 2e-5)
        output('electron_density', '1/m3', 'n(x,t)', 'receivers', axis, 1e10, .005)
        output('hole_density', '1/m3', 'p(x,t)', 'receivers', axis, 1e10, .005)
        if not drift: output('electric_field', 'V/m', 'E=−∂xψ', 'receivers', axis, 1., .005)
    if drift or slug == 'semiconductor-bulk-recombination':
        p.update(tau_n=par('s', 'SRH电子寿命τn', 1e-12, 1), tau_p=par('s', 'SRH空穴寿命τp', 1e-12, 1))
    if drift:
        c['timeout'] = 900 if transient else 600
        p.update(mobility_n=par('m2/(V.s)', '电子迁移率μn', 1e-6, 1), mobility_p=par('m2/(V.s)', '空穴迁移率μp', 1e-6, 1))
        for carrier in ('electron', 'hole'):
            ins['contact_' + carrier] = field('1/m3', '对应载流子的理想接触Dirichlet密度', 'contacts', 'drive' if transient else 'static', 1e6, 1e25)
            if transient: ins['initial_' + carrier] = field('1/m3', 't=0物理密度；非迭代初猜', 'profile', 'initial', 1e6, 1e25)
            output(carrier + '_current', 'A/m2', '向+x的常规传导电流密度J' + carrier[0], 'receivers', axis, .01, .005)
        ins['generation'] = field('1/(m3.s)', '外部成对产生率G≥0', 'profile', 'drive' if transient else 'static', lower=0, upper=1e35)
    if slug in ('semiconductor-bulk-recombination', 'semiconductor-trap-kinetics'):
        location('bodies', 'entities', 1, 128, '彼此独立的均匀体；无空间输运，不用ID推导位置或体积')
        if slug == 'semiconductor-bulk-recombination':
            p.update(intrinsic_density=par('1/m3', '本征密度ni', 1e8, 1e23), radiative=par('m3/s', '辐射复合系数B≥0', 0, 1e-10), auger_n=par('m6/s', '电子Auger系数Cn≥0', 0, 1e-35), auger_p=par('m6/s', '空穴Auger系数Cp≥0', 0, 1e-35))
        else:
            p.update(trap_density=par('1/m3', '每体积陷阱数Nt', 1e8, 1e25), capture_n=par('m3/s', '电子俘获系数cn', 1e-22, 1e-10), capture_p=par('m3/s', '空穴俘获系数cp', 1e-22, 1e-10), n1=par('1/m3', '电子发射平衡密度n1', 1e6, 1e25), p1=par('1/m3', '空穴发射平衡密度p1；ni²=n1 p1，不另输入ni', 1e6, 1e25))
            ins['initial_occupation'] = field('1', '陷阱初始电子占据概率f0', 'bodies', 'initial', 0, 1)
            output('occupation', '1', '电子占据陷阱的概率f(t)', 'bodies', 'observe', 1e-6)
        for carrier in ('electron', 'hole'):
            ins['initial_' + carrier] = field('1/m3', '初始载流子密度', 'bodies', 'initial', 1e6, 1e25)
            output(carrier + '_density', '1/m3', '相应体内瞬时密度', 'bodies', 'observe', 1e10, .003)
        ins['generation'] = field('1/(m3.s)', '成对产生G(t)≥0', 'bodies', 'drive', 0, 1e35)
        if slug == 'semiconductor-bulk-recombination':output('net_recombination', '1/(m3.s)', 'R，可负，不包含外部G', 'bodies', 'observe', 1e14, .005)
    if slug == 'semiconductor-minority-diffusion':
        p.update(diffusivity=par('m2/s', '少数电子扩散系数D', 1e-10, 1), lifetime=par('s', '线性复合寿命τ', 1e-12, 1), majority_density=par('1/m3', '固定均匀多数空穴密度p0，仅界定低注入', 1e12, 1e25))
        ins['surface_velocity'] = field('m/s', '两端表面复合速度S，时间恒定；0表示绝热粒子边界', 'contacts', lower=0, upper=1e7)
        ins['initial_excess'] = field('1/m3', '初始超额少数电子u0≥0', 'profile', 'initial', 0, 1e23)
        ins['generation'] = field('1/(m3.s)', '超额电子产生G≥0', 'profile', 'drive', 0, 1e35)
        output('excess_density', '1/m3', '超额少数电子u', 'receivers', 'observe', 1e9, .005)
        output('particle_flux', '1/(m2.s)', '向+x粒子通量Γ=−D∂xu，不是常规电流', 'receivers', 'observe', 1e10, .005)
    if slug == 'semiconductor-landauer':
        p.update(temperature_left=par('K', '左储库温度TL', 1, 1000), temperature_right=par('K', '右储库温度TR', 1, 1000), chemical_left=par('J', '左电化学势μL，相对共同能量零点', -1e-17, 1e-17), chemical_right=par('J', '右电化学势μR，共同零点', -1e-17, 1e-17), degeneracy=par('1', '额外简并度g，包含自旋；不再隐含乘2', 1, 16, integer=True))
        location('spectrum', 'entities', 2, 4096, '有序能量谱结点对象，按ID行序能量严格递增；不伪造空间坐标')
        location('system', 'entities', 1, 1, '唯一双端器件整体')
        ins['energy'] = field('J', 'E_j；共同能量基准，有限能带之外透射为0', 'spectrum', lower=-1e-17, upper=1e-17)
        ins['transmission'] = field('1', '所有横向通道透射之和T(E_j)，不含g', 'spectrum', lower=0, upper=128)
        output('electric_current', 'A', '向右常规电流I（电子粒子向右时I<0）', 'system', 'static', 1e-12)
        output('heat_left', 'W', '离开左储库的热流QL', 'system', 'static', 1e-14)
    if slug == 'semiconductor-effective-mass':
        c['timeout'] = 600
        p['mode_count'] = par('1', '请求前m个态，JSON整数', 1, 8, integer=True)
        location('layers', 'entities', 1, 64, '沿+x依次拼接的层，第一层左端x=0')
        location('modes', 'entities', 1, 8, 'IDs必须恰0..m−1，对应能量从小到大')
        location('receivers', 'points', 1, 256, '严格位于0<x<H的真实点，可恰在材料界面')
        ins['thickness'] = field('m', '各层厚度h', 'layers', lower=1e-10, upper=1e-6)
        ins['mass'] = field('kg', '各层纵向有效质量的绝对值，不是相对自由电子质量', 'layers', lower=1e-33, upper=1e-29)
        ins['band_edge'] = field('J', '各层常导带边U，相对公共零点', 'layers', lower=-1e-17, upper=1e-17)
        output('eigenenergy', 'J', '按升序排列的m个本征能量', 'modes', 'static', 1e-25, .0001)
        output('wavefunction', 'm^(-1/2)', '按modes行序的m个归一化实波函数', 'receivers', 'static', .01, .003, ['m'])


CLASSICAL = '取电子电荷−q，q=1.602176634e−19 C，kB=1.380649e−23 J/K，VT=kB T/q；电势ψ单位V，电场E=−∂xψ。均匀材料、等温、完全电离、非简并Boltzmann统计；不含异质结、能带收缩、场依赖迁移率、隧穿、雪崩或热反馈。'
SRH = 'SRH采用中带隙陷阱n1=p1=ni，R=(np−ni²)/[τp(n+ni)+τn(p+ni)]；这里R为净复合率，可负，不把外部G并入R。'
DD = CLASSICAL + 'Poisson为−ε∂xxψ=q(p−n+C)。常规电流Jn=qμn nE+qDn∂xn，Jp=qμp pE−qDp∂xp，Dn=μnVT、Dp=μpVT。连续方程∂tn=(∂xJn)/q+G−R，∂tp=−(∂xJp)/q+G−R。' + SRH + '两端均为理想储库，分别直接给ψ、n、p；不再用局部电中性或接触功函数覆盖给定值。'
PHYSICS = {
    'semiconductor-equilibrium': CLASSICAL + '全器件具有共同平衡Fermi能级，ψ=0定义为n=p=ni；因此n=ni exp(ψ/VT)，p=ni exp(−ψ/VT)。求−εψ″=q[p−n+C(x)]，两端ψ给定。零点已固定，不允许事后平移电势或自行用接触电中性替换边值。热平衡没有外加准Fermi分裂，不求非平衡电流。',
    'semiconductor-drift-steady': DD + '本题∂tn=∂tp=0，输入时间只是稳态标记。只包括有唯一正密度稳态的工况，不通过某个任意初猜或隐藏扫描方向选支。输出为该稳态的ψ、n、p、Jn、Jp；非零G/R时各分电流可随位置变化，稳态总传导电流应守恒。',
    'semiconductor-drift-transient': DD + '从t=0的物理n、p初态开始演化；ψ在每一时刻由瞬时电荷和电势边值解Poisson，没有独立ψ初态。给定初始n、p与t=0接触值在两端一致；驱动连续分段线性。输出Jn/Jp仅为传导电流密度，不包含ε∂tE的位移电流，不能将其强制为瞬态空间常量。',
    'semiconductor-bulk-recombination': '各独立均匀体封闭，无接触输运，等温材料系数给定，电势与电场不属于未知量。dn/dt=dp/dt=G−R，'+SRH+'总R=R_SRH+(B+Cn n+Cp p)×(np−ni²)。不把三种复合通道的平衡产生重复加入G，不强制n=p；初态可有不等电子/空穴数，n−p守恒。没有显式陷阱记忆，SRH为准稳态材料响应。',
    'semiconductor-trap-kinetics': '每个独立均匀体中陷阱电子占据概率f，电子俘获/发射净率An=cn[n(1−f)−n1 f]，空穴俘获/发射净率Ap=cp[p f−p1(1−f)]，单位s^−1。dn/dt=G−Nt An，dp/dt=G−Nt Ap，df/dt=An−Ap。en=cn n1、ep=cp p1；陷阱中带电子参与电荷账目，n−p+Nt f守恒。f是单个陷阱的电子占据概率，不是空穴占据或密度。无空间场、接触、辐射、Auger或额外准稳态SRH项，不能把df/dt设为0。',
    'semiconductor-minority-diffusion': '一维均匀p型材料、固定多数空穴背景p0，忽略电场及空间电荷反馈。求超额少数电子u≥0，∂tu=D∂xxu−u/τ+G；这里u不是总电子密度，不另加本征平衡浓度。粒子通量Γ=−D∂xu。两端表面复合满足外向粒子流Γ·ν=S u；左ν=−1、右ν=+1，因而D u′(0)=SL u(0)，−D u′(L)=SR u(L)。无外部注入边界。t=0剖面为物理初态；允许与Robin边界导数不相容，取抛物型初边值问题t>0解，本题只请求严格正输出时刻。低注入要求全时空u≤0.01 p0；合法输入须max(u0)≤0.01p0且τ max(G)≤0.01p0，该充分界限与非负Robin条件共同约束范围。',
    'semiconductor-landauer': '两端理想Fermi储库，弹性相干且无相互作用的输运；透射谱已给定，不要求由几何或散射势重建。q=1.602176634e−19 C、kB=1.380649e−23 J/K、h=6.62607015e−34 J.s。fα(E)=1/[1+exp((E−μα)/(kB Tα))]。在完整输入能带[E0,EN−1]积分，T(E)为结点间分段线性、区间外为0。向右电子数流Ndot=(g/h)∫T(E)[fL−fR]dE；向右常规电流I=−q Ndot。离开左储库热流QL=(g/h)∫(E−μL)T(E)[fL−fR]dE。包含输入g一次，不额外乘自旋2；能量全用J，不隐式使用eV。QL不是总能流，也不是两端热流之和。',
    'semiconductor-effective-mass': '单带一维有效质量模型，在[0,H]有限箱体求Hψ=Eψ，H算符为−(ℏ²/2)∂x[(1/m(x))∂x]+U(x)，ℏ=6.62607015e−34/(2π) J.s。m和U逐层常数，界面ψ及(1/m)ψ′连续，端点ψ(0)=ψ(H)=0；不得换为ψ′连续、周期边界或无限包层衰减。按能量严格升序取前m个简单本征态，无额外自旋简并计数。每态实且∫0^H ψ²dx=1，以ψ′(0)>0固定正负号；不能逐采样点翻号。输出界面处ψ为共同连续值；不请求界面导数。能量相对输入U共同零点，不做每例自动减基态处理。',
}


def expanded_shape(s, p='m'):
    return '[' + ','.join(str(v) for v in s['shape']) + ']'


def bounds(s):
    v = []
    if s.get('integer'): v.append('JSON整数')
    if s.get('positive'): v.append('严格正')
    if s.get('lower') is not None: v.append('≥' + str(s['lower']))
    if s.get('upper') is not None: v.append('≤' + str(s['upper']))
    return '，'.join(v) or '有限实数'


def main():
    ext = ROOT/'qbank/extensions/caeoj_ext/semiconductor'
    ext.mkdir(parents=True, exist_ok=True)
    (ext/'models.json').write_text(json.dumps(public_model_catalog(MODELS), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    toc = []
    for sec, title, slugs in SECTIONS:
        sd = CH/sec
        sd.mkdir(parents=True, exist_ok=True)
        links = []
        for i, slug in enumerate(slugs, 1):
            c = MODELS[slug]
            td = sd/slug
            td.mkdir(exist_ok=True)
            num = sec.split('-')[0]+'.'+str(i)
            links.append(f'- [{num} {c["name"]}]({slug}/instruction.md)')
            variation = '输入参数及DATA明确的全部剖面、状态、驱动与采样可逐例变化。' if 'profile' in c['locations'] else '输入参数及DATA明确的全部对象属性、状态与采样可逐例变化。'
            instruction = f'# {num} {c["name"]}\n\n实现可复用求解器，读取每例problem.json及引用的input.h5，覆盖以下完整问题族，向指定路径写result.h5。\n\n'+PHYSICS[slug]+'\n\n'+variation+'连续物理响应及统计约定如上固定；考生选择内部算法、离散、非线性求解与误差控制，不要求使用某个软件或参考方法。输入结点与输出采样不强制成为内部网格或积分步长。\n\n入口为`python solve.py --input <input_json> --output <output_h5>`（可由Python入口调用其他语言程序），每例无网络，从任意工作目录运行，资源相对输入清单解析。提交冻结后同一程序处理全部未见算例，不逐例修改。每例墙钟'+str(c['timeout'])+'秒，CPU 2核，内存2048 MB，无GPU；生成程序3600秒、构建1200秒。输出无独立字节上限，仍须满足规定形状与内存预算。\n\n所有输出、时刻、实体与分量均须满足`|candidate−reference| ≤ atol + rtol×|reference|`，无偏移拟合；逐值比较，不按点数平均稀释误差。全部字段通过且结构合法才通过该例；总成绩为通过例数除以计划例数，各例等权。超时、非零退出、缺输出或非法输出为该例失败；输入、参考或工具错误中止评测，不记考生失分。\n\n| quantity | 单位 | atol | rtol |\n|---|---|---:|---:|\n'
            for q, s in c['outputs'].items(): instruction += f'| {q} | `{s["unit"]}` | {s["atol"]} | {s["rtol"]} |\n'
            instruction += '\n数值阈值与资源是本版公开设计目标，正式算例建立前尚未完成校准。数据细节见[DATA.md](DATA.md)，通用存储、引用和输出结构见[CONTRACT.md](../../../../docs/CONTRACT.md)。\n'
            (td/'instruction.md').write_text(instruction, encoding='utf-8')
            data = f'# {num} 数据契约\n\n本文件与instruction.md及通用CONTRACT.md构成完整要求；无额外领域文档依赖。以下为格式定义，未提供可运行算例或参考答案。\n\n`spatial_dimension=1`；physics.model固定`semiconductor-{slug.removeprefix("semiconductor-")}-v1`；task若给必须为`{slug}`。仅使用physics及其parameters，不混用profile、analysis、materials、contract_version。meshes和geometries均为空对象，长度为m、时间为s，有限维实体不引入空间方程。\n\nphysics.parameters恰含下表键，每项恰为`{{"value":数值,"unit":"表中单位"}}`，无默认、无自动换算；布尔值不能作为数值。\n\n| 键 | unit | 范围与含义 |\n|---|---|---|\n'
            for k, s in c['parameters'].items(): data += f'| {k} | `{s["unit"]}` | {bounds(s)}；{s["meaning"]} |\n'
            data += '\nlocations恰含下表位置；IDs为非负、严格递增int64，不能按ID数值推断坐标。points.coordinates为float64[N,1]真实x坐标；entities只有kind和ids，不带伪坐标。\n\n| location | 类型及数量 | 对象 |\n|---|---|---|\n'
            for k, s in c['locations'].items(): data += f'| {k} | {s["kind"]}，{s["minimum"]}..{s["maximum"]} | {s["meaning"]} |\n'
            axes = {'static'} | {s['axis'] for s in c['inputs'].values()} | {s['axis'] for s in c['outputs'].values()}
            data += '\ntime_axes恰含'+', '.join('`'+k+'`' for k in sorted(axes))+'。static及initial各恰[0.0]，标记/物理初态分工不同，允许共用数组key。'
            if c['transient']:
                data += 'observe含1..256个严格递增时刻，末时刻0<tend≤1 s；drive含2..512个严格递增时刻，首项0、末项恰等于tend。observe位于[0,tend]内，不要求与drive重合。所有drive场在相邻时刻逐值线性插值、禁止区间外推；内部步长自行选择，不由任一时间数组指定。'
                if slug in ('semiconductor-minority-diffusion','semiconductor-drift-transient'):data += 'observe首项必须>0；不请求t=0初始剖面折点处可能未定义的导数通量/电流。'
            data += '\n\nfields的逻辑名和array key由清单给出，不必相同；每个下表quantity恰一个输入场，不能有其他输入场。每场dtype=float64、value_kind=point。除wavefunction输出外所有场kind=scalar、component_shape=[1]、components=["value"]；数组形状[T,N,1]，不省略长度为1的轴。所有输入均以field呈现，不接受常量替代、option或隐式广播。\n\n| 输入quantity | location | time_axis | unit | 范围与定义 |\n|---|---|---|---|---|\n'
            for q, s in c['inputs'].items(): data += f'| {q} | {s["location"]} | {s["axis"]} | `{s["unit"]}` | {bounds(s)}；{s["meaning"]} |\n'
            data += '\n每个输入场显式sampling：profile位置space=piecewise_linear，其他位置space=uniform；drive轴time=linear，其他轴time=constant；extrapolation=forbid。profile按真实x在相邻结点间线性重建，定义整个闭区间，不延拓到区间外；其他位置为各独立对象/边界自身的值，uniform不表示不同对象数值相等或可在对象之间插值。时间及空间线性重建可分离进行。静态场各自单帧，在整个分析区间保持不变，不将static标记误作有效驱动区间长度。\n\nconditions恰有每个输入quantity一条：variable等于该quantity；location同表；operator固定`prescribed`；data恰含value且为`{"field":"该场逻辑名"}`。role：initial轴为initial；contacts位置非initial为boundary；doping/thickness/mass/band_edge为material；其他为source。顺序任意，各记录只引用对应场，不允许重复或未使用场。\n\n物理重建、闭合和边界：\n\n'+PHYSICS[slug]+'\n\n'
            if slug in ('semiconductor-equilibrium','semiconductor-drift-steady','semiconductor-drift-transient'):
                data += '连续模型无材料内部界面；净掺杂在profile处连续、导数可折变。所有输入及实际解须在非简并等温模型适用范围；不包含密度负值、非唯一稳态或无法在预算内达标的病态工况。该适用承诺需由正式数据的独立建模与参考证据落实，声明检查不求解并不证明之。\n\n'
            if slug=='semiconductor-drift-transient':data += '初始密度两端与相应接触驱动第一帧相同，按相对1e−12、绝对0比较；初态内部的ψ不是输入，不要求用平衡Boltzmann关系重算n/p。\n\n'
            if slug=='semiconductor-effective-mass':data += 'H=各层thickness之和，layers按ID行序累加位置，接收点可乱序；modes数量恰mode_count且IDs=0..m−1。不将层宽当内部离散。谱条件性作为合法问题族的数据承诺：令Es=max(max(U)−min(U),ℏ²/(2 min(m)H²),1e−24 J)，前m个态与其相邻态（包括第m+1态）的能量间距均≥1e−6 Es，排除数值上不可分辨的近简并双阱。该条件需正式数据的独立谱与收敛证据验证，声明校验器不求谱；还须验证归一化波函数、定相和逐值精度在预算内可达。\n\n'
            if slug=='semiconductor-landauer':data += '相邻能量严格递增、跨度为正；能量结点是积分支撑，不是时间或空间点。接近零温的边缘仍采用给定正温Fermi函数，不用阶跃替代；可加密积分，不能仅把输入谱结点作固定求积规则。\n\n'
            data += 'outputs逻辑名与array key任意且各自唯一；下表quantity每种至少一次，允许同一quantity多个独立命名的输出，均使用表中固定location/time_axis/分量；禁止其他quantity。不写输出sampling。所有输出float64、value_kind=point。\n\n| quantity | location | time_axis | unit | 分量与含义 |\n|---|---|---|---|---|\n'
            for q, s in c['outputs'].items():
                desc = 'scalar [1]' if s['shape']==[1] else 'components [m]，m=mode_count，标签c1..cm'
                data += f'| {q} | {s["location"]} | {s["axis"]} | `{s["unit"]}` | {desc}；{s["meaning"]} |\n'
            data += '\n结果dataset形状[T,N,*component_shape]，只写各outputs.array及所引用的IDs、时间数组；不写坐标、输入场、额外诊断或元数据。输出点值为上述连续模型在给定坐标/时刻的值，不是内部单元均值；重复坐标保持不同ID行。输入场总标量数与全部请求输出标量数分别≤2000000，全部值有限，禁止默默截断。输入/输出HDF5的扁平、dtype与精确复制规则依CONTRACT。\n'
            # Expand only the branches belonging to this problem.
            if 'initial' not in axes:
                data = data.replace('static及initial各恰[0.0]，标记/物理初态分工不同，允许共用数组key。', 'static恰[0.0]，仅作稳态/静态标记。')
            if not any(s['kind']=='entities' for s in c['locations'].values()):
                data = data.replace('，有限维实体不引入空间方程', '')
                data = data.replace('；entities只有kind和ids，不带伪坐标', '')
            if slug=='semiconductor-effective-mass':data=data.replace('，有限维实体不引入空间方程', '；layers/modes是离散层与模态标识，物理模型仍是一维空间本征问题')
            if not any(s['kind']=='points' for s in c['locations'].values()):
                data = data.replace('points.coordinates为float64[N,1]真实x坐标；', '')
                data = data.replace('输出点值为上述连续模型在给定坐标/时刻的值，不是内部单元均值；重复坐标保持不同ID行。', '输出为各独立实体在指定时刻的状态/属性，按ID行序存储，不作对象间平均。')
            if slug!='semiconductor-effective-mass':data = data.replace('除wavefunction输出外所有场', '所有场')
            material_q = [q for q in c['inputs'] if q in ('doping','thickness','mass','band_edge')]
            role_text = []
            if 'initial' in axes:role_text.append('initial轴为initial')
            if 'contacts' in c['locations']:role_text.append('contacts位置非initial为boundary')
            if material_q:role_text.append('/'.join(material_q)+'为material')
            role_text.append('其他为source')
            data = data.replace('initial轴为initial；contacts位置非initial为boundary；doping/thickness/mass/band_edge为material；其他为source', '；'.join(role_text))
            if 'profile' not in c['locations']:
                data = data.replace('profile位置space=piecewise_linear，其他位置space=uniform', 'space=uniform')
                data = data.replace('profile按真实x在相邻结点间线性重建，定义整个闭区间，不延拓到区间外；其他位置为各独立对象/边界自身的值', '各位置为独立对象自身的值')
                data = data.replace('时间及空间线性重建可分离进行。', '')
            if 'drive' not in axes:
                data = data.replace('drive轴time=linear，其他轴time=constant', 'time=constant')
                data = data.replace('时间及空间线性重建可分离进行。', '')
                data = data.replace('，不将static标记误作有效驱动区间长度', '')
            (td/'DATA.md').write_text(data, encoding='utf-8')
            policy = dict(version=2, quantities={q:dict(unit=s['unit'], rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()})
            (td/'author').mkdir(parents=True,exist_ok=True)
            (td/'author/grading-template.json').write_text(json.dumps(policy, indent=2)+'\n', encoding='utf-8')
            (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=180,per_case_overhead_seconds=60)), indent=2)+'\n', encoding='utf-8')
            (td/'harbor').mkdir(exist_ok=True)
            (td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1200.0\ncpus = 2\nmemory_mb = 2048\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n', encoding='utf-8')
        (sd/'README.md').write_text('# '+sec.split('-')[0]+' '+title+'\n\n'+'\n'.join(links)+'\n', encoding='utf-8')
        toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
    (CH/'README.md').write_text('# 第十一章 半导体与电子输运分析\n\n6节8题，题面与DATA逐题自包含。正式数据、参考与评测发布留后；配置为待校准设计目标。\n\n'+'\n'.join(toc)+'\n\n维护入口：[章规划](../design/chapter-11-semiconductor.md)、[逐题清单](../design/chapter-11-task-plan.md)、[进度及证据](../design/reviews/chapter-11-progress.md)。\n', encoding='utf-8')


if __name__ == '__main__':
    main()
