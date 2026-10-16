"""Expand independent radiation contracts/configuration, never numerical case data."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
CH = ROOT / 'qbank/15-radiation-nuclear'
SECTIONS = [
    ('15.1-deposition', '衰减与能量沉积', ['photon-absorption']),
    ('15.2-transport', '多群粒子输运', ['slab-transport-steady', 'slab-transport-transient']),
    ('15.3-diffusion', '中子扩散与临界', ['neutron-diffusion-source', 'neutron-diffusion-critical']),
    ('15.4-kinetics', '中子动力学', ['point-kinetics']),
    ('15.5-inventory', '核素库存演化', ['decay-network', 'irradiated-network']),
]


def spec(unit, meaning, shape=None, **kw):
    return dict(unit=unit, meaning=meaning, kind='components' if shape else 'scalar',
                shape=shape or [1], **kw)


def parameter(unit, meaning, **kw):
    return dict(unit=unit, meaning=meaning, **kw)


MODELS = {}
for section, title, slugs in SECTIONS:
    for slug in slugs:
        c = dict(parameters={}, locations={}, records={}, outputs={}, timeout=600)
        MODELS[slug] = c
        def loc(name, lo, hi, meaning, kind='entities'):
            c['locations'][name] = dict(kind=kind, minimum=lo, maximum=hi, meaning=meaning)
        def rec(op, role, variable, location, data, axis='static'):
            c['records'][op] = dict(role=role, variable=variable, location=location, data=data, axis=axis)
        def out(q, s, location, atol=1e-8, rtol=.005):
            c['outputs'][q] = dict(s, location=location, atol=atol, rtol=rtol)
        slab = slug not in ('point-kinetics', 'decay-network', 'irradiated-network')
        transient = slug in ('slab-transport-transient', 'point-kinetics', 'decay-network', 'irradiated-network')
        c['transient'] = transient
        c['output_axis'] = 'requests' if transient else 'static'
        if slab:
            c['parameters']['group_count'] = parameter('1', '群数G，JSON整数1..4；各群是输入给定有效响应的离散群，无隐含能群宽度权重', integer=True, lower=1, upper=4)
            loc('layers', 1, 32, '按IDs行序沿+x排列的材料层对象，x=0起始；层内参数常值')
            rec('layers', 'material', 'layer', 'layers', {'width': spec('m', '层厚h>0', positive=True)})
            loc('system', 1, 1, '完整平板系统对象，ID固定0')
        if slug == 'photon-absorption':
            c['name'] = '多群光子纯吸收与能量沉积'
            rec('absorption', 'material', 'absorption', 'layers', {'sigma': spec('1/m', '宏观纯吸收Σ_g≥0', ['g'], nonnegative=True)})
            rec('beam', 'source', 'beam', 'system', {'flux': spec('1/(m2.s)', 'x=0处向+x法向准直入射群粒子通量F_g≥0', ['g'], nonnegative=True), 'energy': spec('J', '群内每粒子能量E_g>0；按群行序', ['g'], positive=True)})
            out('transmitted_flux', spec('1/(m2.s)', 'x=H处各群出射法向通量', ['g']), 'system')
            out('deposited_power', spec('W/m2', '该层所吸收能量的每横截面积功率，属于层对象的集总响应'), 'layers')
        elif slug.startswith('slab-transport') or slug.startswith('neutron-diffusion'):
            transport = slug.startswith('slab-transport')
            critical = slug.endswith('critical')
            c['name'] = {'slab-transport-steady':'稳态多群平板粒子输运', 'slab-transport-transient':'有限速瞬态多群平板粒子输运', 'neutron-diffusion-source':'源驱动多群中子扩散', 'neutron-diffusion-critical':'多群中子扩散临界基模'}[slug]
            c['timeout'] = 1200 if transport else 600
            if transport:
                c['parameters']['particle'] = parameter('1', 'JSON整数0=光子，1=中子；不触发额外核数据或自动响应', integer=True, lower=0, upper=1)
            loc('probes', 1, 128, '真实位置x，严格在层内部，排除全部界面与两端；不作空间重建', 'points')
            data = {'absorption': spec('1/m', '宏观吸收Σa_g>0', ['g'], positive=True), 'scatter': spec('1/m', '各向同性群转移S[g,h]≥0，第一轴出射群g、第二轴入射群h；含自散射', ['g','g'], nonnegative=True)}
            if not transport:
                data['diffusion'] = spec('m', '各群扩散系数D_g>0，独立给定，不从总截面反推', ['g'], positive=True)
            if critical:
                data['production'] = spec('1/m', '各群νΣf_g>0，已含平均产额；吸收已含裂变损失，不再加一次Σf', ['g'], positive=True)
                data['spectrum'] = spec('1', '裂变谱χ_g>0，每层群和与1之差≤1e−12；按存储值计算，不再归一化', ['g'], positive=True)
            rec('medium', 'material', 'medium', 'layers', data)
            if not critical:
                rec('source', 'source', 'source', 'layers', {'value': spec('1/(m3.s)', '层内常量总群体源q_g≥0'+('；各向同性角源q_g/2' if transport else ''), ['g'], nonnegative=True)})
            if transport:
                rec('incoming', 'boundary', 'incoming', 'system', {'left': spec('1/(m2.s)', 'x=0、μ>0的角通量ψ=L_g≥0，入射半球内不依赖μ', ['g'], nonnegative=True), 'right': spec('1/(m2.s)', 'x=H、μ<0的角通量ψ=R_g≥0，入射半球内不依赖μ', ['g'], nonnegative=True)})
                if transient:
                    rec('speed', 'material', 'speed', 'system', {'value': spec('m/s', '群速v_g>0，全空间常量', ['g'], positive=True)})
                    rec('initial', 'initial', 'initial_flux', 'layers', {'value': spec('1/(m2.s)', 't=0层内各向同性标量通量φ0_g≥0，ψ0=φ0/2；独立于体源和入射', ['g'], nonnegative=True)})
            out('scalar_flux', spec('1/(m2.s)', '各群标量通量φ_g，'+('按题定积分归一化' if critical else '保持输入激励确定的绝对幅值，不另作归一化'), ['g']), 'probes')
            if not critical:
                out('current', spec('1/(m2.s)', '各群沿+x的净粒子流J_g，可为负', ['g']), 'probes')
            else:
                out('multiplication_factor', spec('1', '主正本征值k_eff'), 'system', 1e-7, .001)
        elif slug == 'point-kinetics':
            c['name'] = '给定反应性历史的缓发中子动力学'
            c['timeout'] = 300
            c['parameters'] = {'precursor_count':parameter('1', '缓发组数B，JSON整数1..8', integer=True, lower=1, upper=8), 'generation_time':parameter('s', '有效瞬发代时间Λ>0', positive=True)}
            loc('system', 1, 1, '整体点堆对象，ID固定0')
            loc('precursors', 1, 8, '缓发组，恰B个，IDs固定0..B−1；分量按此顺序')
            rec('precursors', 'material', 'precursor', 'precursors', {'fraction':spec('1', 'β_i>0，各组和β<1', positive=True), 'decay':spec('1/s', 'λ_i>0', positive=True)})
            rec('initial', 'initial', 'state', 'system', {'population':spec('1', 'n(0)>0，相对中子数', positive=True), 'precursor_state':spec('1', 'C_i(0)≥0，与n相同的任意固定归一化尺度，不是平衡预设', ['b'], nonnegative=True)})
            rec('history', 'source', 'driving', 'system', {'reactivity':spec('1', 'ρ(t)，定义(k−1)/k，绝对值≤0.5；不是美元单位'), 'source':spec('1/s', 'n方程中的外源s(t)≥0，与n归一化一致', nonnegative=True)}, 'control')
            out('population', spec('1', '相对中子数n(t)'), 'system', 1e-8, .002)
            out('precursor_state', spec('1', '按缓发组IDs排列的C_i(t)', ['b']), 'system', 1e-8, .002)
        else:
            c['name'] = '分支衰变核素库存与衰变功率' if slug == 'decay-network' else '给定通量照射下的核素库存演化'
            c['timeout'] = 300
            c['parameters']['nuclide_count'] = parameter('1', '核素数N，JSON整数1..32', integer=True, lower=1, upper=32)
            loc('nuclides', 1, 32, '核素对象，恰N个，IDs固定0..N−1，矩阵分量按此顺序；不凭ID查询核数据')
            loc('system', 1, 1, '完整库存系统，ID固定0')
            rec('nuclides', 'material', 'nuclide', 'nuclides', {'decay':spec('1/s', 'λ_j≥0，允许稳定核素', nonnegative=True), 'energy':spec('J', '每次衰变局部沉积能ε_j≥0，已扣除逃逸能，不是质量亏损', nonnegative=True)})
            rec('branches', 'material', 'decay_branch', 'system', {'value':spec('1', 'B[i,j]≥0，j衰变后进入i的分支；对角0、列和≤1，缺额流出系统；正边图无环', ['n','n'], nonnegative=True)})
            rec('initial', 'initial', 'inventory', 'nuclides', {'value':spec('1', '各核素初始原子数N_j(0)≥0，原子计数无量纲', nonnegative=True)})
            if slug == 'irradiated-network':
                rec('reaction', 'material', 'reaction', 'nuclides', {'cross_section':spec('m2', '给定单群有效微观移除截面σ_j≥0；不含衰变', nonnegative=True)})
                rec('products', 'material', 'reaction_branch', 'system', {'value':spec('1', 'Y[i,j]≥0，j反应后生成i；对角0、列和≤1，缺额流出系统，允许反应循环；不支持裂变多产物增殖', ['n','n'], nonnegative=True)})
                rec('history', 'source', 'irradiation', 'system', {'value':spec('1/(m2.s)', '给定外部标量粒子通量Φ(t)≥0，速率r_j=σ_jΦ，不作库存反馈', nonnegative=True)}, 'control')
            out('inventory', spec('1', '各核素原子数N_j(t)'), 'nuclides', 1e-6, .002)
            out('activity', spec('Bq', 'Σ_j λ_j N_j(t)，包含全部库存核素，无额外分支倍数'), 'system', 1e-8, .002)
            out('decay_power', spec('W', 'Σ_j ε_j λ_j N_j(t)，仅衰变沉积，不包含照射反应能'), 'system', 1e-12, .002)

PHYS = {
'photon-absorption': '无限横向平板在x∈[0,H]按层排列，多群法向准直光子束从x=0入射。只有纯吸收，无散射、发射、反射、群间转移或次级粒子逃逸；每个被吸收光子的给定能量全部局部沉积。F_g在界面连续，各层dF_g/dx=−Σ_g F_g。出射为F_g(H)，第l层deposited_power=Σ_g E_g[F_g(x_l)−F_g(x_l+h_l)]，是每横截面积功率，不能除以厚度或密度当作体积发热／剂量。群能不要求排序；没有能群宽度权重。沉积不改变材料，不求温度。',
'slab-transport-steady': '无限横向分层平板、一维空间x、连续方向余弦μ∈[−1,1]，方位角已积分。各群φ_g=∫ψ_g dμ、J_g=∫μψ_g dμ，不再乘2π或4π。宏观吸收和各向同性群散射给定，Σt_g=Σa_g+Σ_h S[h,g]；每次散射只产生一个粒子，无裂变、倍增或自发发射。稳态μ∂xψ_g+Σt_gψ_g=(q_g+Σ_h S[g,h]φ_h)/2。左右边界仅规定各自入射半球，出射由解确定；内部界面无表面源或折反射，ψ连续。介质静止、响应与粒子通量无反馈。光子／中子标记显式给定，粒子种类不改变这些有效群响应，无隐藏核数据。群号只表示已给定离散响应，不从能群宽度或数据库添加权重。',
'slab-transport-transient': '无限横向分层平板、一维x、方向余弦μ∈[−1,1]，方位角已积分。φ_g=∫ψ_g dμ、J_g=∫μψ_g dμ，不乘2π／4π。Σt_g=Σa_g+Σ_h S[h,g]，有限群速下v_g^−1 ∂tψ_g+μ∂xψ_g+Σt_gψ_g=(q_g+Σ_h S[g,h]φ_h)/2。吸收为正、各向同性非增殖散射，无裂变或反馈。t=0层内各向同性ψ_g=φ0_g/2；层间初值可间断，t>0内部界面ψ连续，入射边界和体源在整个区间恒定。t=0边界／界面不相容按初边值输运问题的内域初始迹及t>0入射理解；不把初态改成平衡场。求指定时刻的标量通量与流，包括有限传播效应，不用准稳态代替。光子／中子标记仅说明粒子种类，无隐藏核数据或群宽度权重。',
'neutron-diffusion-source': '无限横向分层平板的一维多群中子扩散，有效D_g独立给定。无裂变，−∂x(D_g∂xφ_g)+(Σa_g+Σ_h S[h,g])φ_g−Σ_h S[g,h]φ_h=q_g，J_g=−D_g∂xφ_g。矩阵第一轴目的群、第二轴来源群，允许自散射，其损失与产生恰抵消。每个界面φ_g和J_g连续；在真实几何边界x=0,H施加φ_g=0，无外推长度、额外入射或反射。这个零Dirichlet扩散模型不冒充角输运真空边界。材料响应和源给定，不作热反馈或核数据拟合。',
'neutron-diffusion-critical': '无限横向分层平板的一维多群裂变扩散：−∂x(D_g∂xφ_g)+(Σa_g+Σ_h S[h,g])φ_g−Σ_h S[g,h]φ_h=χ_g Σ_h(νΣf_h φ_h)/k。Σa包含裂变吸收，不再重复裂变损失；νΣf为生产截面。无外源，每层χ按存储值使用。各界面φ及−D∂xφ连续，两端真实x=0,H处φ=0，无外推边界。求正基模及其主正本征值k_eff；不选高阶变号模态，不取任意接近1的本征值。以Σ_g∫_0^H φ_g dx=1/(m.s)归一化，φ单位仍为1/(m2.s)，并取全域内部正号；这只是唯一幅度约定，不代表物理堆功率。生产截面、吸收、扩散及χ各群严格为正，以确保耦合的基模目标，不要求求瞬态或临界控制调节。',
'point-kinetics': '空间形状冻结的点堆中子动力学，n为相对中子数，C_i为与n相同固定尺度的缓发前驱状态。dn/dt=[(ρ(t)−β)/Λ]n+Σ_iλ_i C_i+s(t)，dC_i/dt=β_i n/Λ−λ_i C_i，β=Σ_iβ_i。反应性ρ=(k−1)/k为无量纲数，不按美元输入，不含自动温度反馈。Λ、β_i、λ_i及独立n(0)、C_i(0)给定，不假定初始缓发平衡，不以反应性反推空间分布。历史按输入连续分段线性插值，仅输出requests中的时刻；积分须正确处理其间的控制结点，不增加输出帧；没有未声明跳跃或瞬发跳跃近似。',
'decay-network': '有限库存的分支放射性衰变，N_j为原子数：dN_i/dt=Σ_j B[i,j]λ_j N_j−λ_i N_i。B第一轴子核素、第二轴母核素，列和不超过1，缺额为离开跟踪系统，不自动补一个核素。允许λ=0稳定核素和多个分支汇合，正边图无环、对角为0。总活度A=Σλ_j N_j，局部衰变沉积功率P=Σε_jλ_jN_j；ε已给定局部沉积能，不加逃逸能或其他库。系统无空间、迁移、照射或外部补料，所有初值独立给定，不假定长期平衡。',
'irradiated-network': '有限库存受给定外部单群标量通量照射，r_j(t)=σ_jΦ(t)。dN_i/dt=Σ_j[B[i,j]λ_j+Y[i,j]r_j(t)]N_j−[λ_i+r_i(t)]N_i。B、Y第一轴目的核素、第二轴来源核素；对角为0、各列和≤1，缺额离开系统，不支持一个反应生成多个被跟踪原子的裂变产额。衰变正边图无环，反应图可循环；允许零截面及稳定核素。所有率及局部衰变能由输入给定，不下载核库，不作自屏蔽、通量或功率反馈，无补料或迁移。输出A=Σλ_j N_j及P=Σε_jλ_jN_j只计衰变；无反应沉积能输入，不把它计入P。Φ按给定历史连续分段线性插值。',
}


def desc(s):
    return f'{s["kind"]} {s["shape"]}；`{s["unit"]}`；{s["meaning"]}'


def main():
    ext = ROOT/'qbank/extensions/caeoj_ext/radiation'
    ext.mkdir(parents=True, exist_ok=True)
    (ext/'models.json').write_text(json.dumps(MODELS, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    toc = []
    for sec, title, slugs in SECTIONS:
        sd = CH/sec
        sd.mkdir(parents=True, exist_ok=True)
        links = []
        for i, slug in enumerate(slugs, 1):
            c = MODELS[slug]; td = sd/slug; td.mkdir(exist_ok=True)
            number = sec.split('-')[0]+'.'+str(i)
            links.append(f'- [{number} {c["name"]}]({slug}/instruction.md)')
            params = '\n'.join(f'| `{k}` | `{s["unit"]}` | {s["meaning"]} |' for k,s in c['parameters'].items())
            locs = '\n'.join(f'| `{k}` | {s["kind"]}，{s["minimum"]}..{s["maximum"]}项；{s["meaning"]} |' for k,s in c['locations'].items())
            axes = {'static'} | {r['axis'] for r in c['records'].values()} | {c['output_axis']}
            timing = 'time_axes恰含'+ '、'.join('`'+a+'`' for a in sorted(axes))+'。static恰为float64[1]的[0.0]，静态参数及初态记录引用static。'
            if c['transient']:
                timing += 'requests为float64[T]，1≤T≤256，所有值在[0,t_end]，严格递增；t_end定义为requests最后值且必须>0，不要求首项为0。输出时刻不是内部步长；初态总是在物理t=0。'
            if 'control' in axes:
                timing += 'control为float64[K]，2≤K≤256，首项0、末项恰等于t_end；控制字段逐区间线性插值、端点取存储值，禁止外推。control和requests可不同，内部时间步自选。'
            timing += '所有时间单位s，时间数组key自由。未列轴不允许，输出均引用'+c['output_axis']+'。'
            records = []
            for op,r in c['records'].items():
                records.append(f'### `{op}`\n\nconditions中恰一条：role=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`，location=`{r["location"]}`；完整覆盖该location，使用`{r["axis"]}`时间轴。data恰含下列键，无默认值：\n\n| data键 | 类型、单位、含义与范围 |\n|---|---|\n'+'\n'.join(f'| `{k}` | {desc(s)} |' for k,s in r['data'].items()))
            symbols = 'g=group_count' if 'group_count' in c['parameters'] else 'b=precursor_count' if slug == 'point-kinetics' else 'n=nuclide_count'
            fields = '字段全部float64，shape=[T,N,*component_shape]，T取所引用时间轴长度，N取location IDs长度。scalar为kind=scalar、component_shape=[1]、components=["value"]；其余为kind=components，shape按表代入'+symbols+'，components为按行优先展开的c1..cL（从c1开始、末轴变化最快），包括矩阵非对角及零项。所有value_kind=point，entities表示其对象自身参数或集总状态，不表示空间平均。条件data只用{"field":"逻辑字段名"}引用；对应fields记录的array才是HDF5 key，名称自由。fields恰为条件实际引用项；quantity等于data键名，键value例外等于该条件variable；字段必须同location及上述时间轴。单个字段可被多个相容引用共享，不能以数组等长代替身份。无内联常量／选项或隐式广播。'
            fields += '每个输入字段必须显式sampling：space=uniform（每个独立对象自身的值，不在对象间插值），extrapolation=forbid；static的time=constant'+('，control的time=linear' if 'control' in axes else '')+'。'
            if 'layers' in c['locations']:
                fields += '层参数按对象记录构成各层常值，不在层之间线性插值。'
            special = ''
            if 'layers' in c['locations']:
                special += '层从x=0按IDs数组行序排列，H为全部width之和，坐标单位m；各层IDs可非连续，不从ID数值推坐标。所有累计界面必须有限且严格递增。'
            if 'probes' in c['locations']:
                special += 'probes.coordinates为float64[N,1]；每点x与任一界面的距离须≥1e−10·H且严格在(0,H)。不要求按坐标排序，值始终按IDs对应；无界面迹或边界导数请求。'
            if slug == 'point-kinetics':
                special += 'precursors的行序与输出C的分量序一致，fraction求和β必须<1；history.reactivity逐存储值绝对值≤0.5。'
            if 'network' in slug:
                special += '分支矩阵B和（若有）Y逐列和≤1，对角恰0，不用容差放宽；λ=0的核素其B列必须全0。B的正边图无环。矩阵分量顺序由nuclides IDs确定，不取决于conditions排列。'
            outputs = '\n'.join(f'| `{q}` | {desc(s)} | `{s["location"]}` |' for q,s in c['outputs'].items())
            # Expand only relevant physical branches into each independent contract.
            data = f'# {slug} 数据契约\n\nproblem.json及data_file引用的扁平HDF5遵循通用CONTRACT，路径相对清单目录。physics恰含model、parameters；model=`radiation-{slug}-v1`。task可省略，若出现只能为`{slug}`；模型不由目录或ID推断。禁止profile、contract_version、analysis、materials混用。\n\n## 物理定义\n\n{PHYS[slug]}\n\n## 全局参数\n\nphysics.parameters恰含下表全部项，每项仅value和unit；数值有限，布尔不能作数值，整数须JSON整数。\n\n| 参数 | 单位 | 定义及范围 |\n|---|---|---|\n{params}\n\n## 对象与几何\n\nspatial_dimension固定1。meshes和geometries均为空。有限维库存和动力学中1仅为协议标记，不引入空间方程。locations恰含下表；IDs为int64、非负严格递增，system必须ID=[0]；其余固定ID规则按表。{special}\n\n| location | 定义与数量 |\n|---|---|\n{locs}\n\n## 时间与数组\n\n{timing}\n\n{fields}\n\n## 条件全集\n\n'+'\n\n'.join(records)+f'\n\n## 输出\n\n每个quantity至少出现一次，可重复请求，outputs逻辑名与array key自由；同quantity的单位、位置、shape均按表，float64、value_kind=point、时间轴={c["output_axis"]}、无sampling。值为定义的时刻状态或连续空间点值，不是时间／空间平均。\n\n| quantity | 类型、单位与含义 | location |\n|---|---|---|\n{outputs}\n\n结果仅含要求的输出array及其输入IDs／时间轴的精确副本，不导出坐标、输入场或额外数组。\n\n## 接收限制\n\n各表规模为公开上限；输入场总分量与输出场总分量分别不超过2000000。所有输入／输出浮点值有限。正式数据须独立验证模型适用、观测存在、参考收敛及同预算可达性，排除任意刚性、极厚光学层、极端增长、病态谱或下溢主导的不可辨识组合；这不是由结构检查自动证明的事实，不能由参数正值代替数值证据。\n'
            data = data.replace('有限维库存和动力学中1仅为协议标记，不引入空间方程。', '1表示平板法向全局x轴。' if 'layers' in c['locations'] else '1仅为有限维系统的协议标记，不引入空间方程。')
            data = data.replace('值为定义的时刻状态或连续空间点值，不是时间／空间平均。', '各输出按下表定义，不另作时间或空间平均。')
            data = data.replace('排除任意刚性、极厚光学层、极端增长、病态谱或下溢主导的不可辨识组合；', '正式数据接收须有预算内达到公开精度的独立数值证据；')
            if not any(r['role'] == 'initial' for r in c['records'].values()):
                data = data.replace('静态参数及初态记录', '静态参数记录')
            if slug in ('photon-absorption', 'point-kinetics'):
                data = data.replace('，包括矩阵非对角及零项', '')
            if slug == 'decay-network':
                data = data.replace('分支矩阵B和（若有）Y', '分支矩阵B')
            (td/'DATA.md').write_text(data, encoding='utf-8')
            tol = '\n'.join(f'| `{q}` | {s["atol"]} | {s["rtol"]} | `{s["unit"]}` |' for q,s in c['outputs'].items())
            instruction = f'# {number} {c["name"]}\n\n实现覆盖公开问题族的可复用求解器，冻结后处理多个未见算例。{PHYS[slug]}\n\n层数、群数、材料、源／历史或网络及初态由输入变化；精确支持范围见[本题DATA](DATA.md)，通用存储见[CONTRACT](../../../../docs/CONTRACT.md)。这三份文件构成全部题意。考生负责实现给定物理响应、选择内部离散／积分／求解方法和控制数值误差；语言与软件自由，覆盖整个范围的解析／降阶方法同样有效，不要求复现参考算法。\n\n## 运行与资源\n\n入口`python solve.py --input /path/problem.json --output /path/result.h5`。程序0退出且关闭结果文件。每例Linux AMD64，{c["timeout"]}秒墙钟（含启动与I/O），2CPU、4096MB、0GPU，逐例无网络，无独立输出字节限额。生成求解器3600秒、构建1800秒。环境提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5；不强制Python。对象数量和帧数依DATA，输入／输出场各至多2000000数值分量；采样帧不限制内部步数。规模、精度和预算为待校准设计目标，正式数据须用独立参考验证可达性。\n\n## 评分\n\n每有效例正常结束、结果结构合法且每quantity的每帧／对象／分量满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0分，等号接受。无去均值、幅度拟合、排序替换或超限豁免；临界题的归一化和正号必须遵守物理定义。\n\n| quantity | atol | rtol | 单位 |\n|---|---|---|---|\n{tol}\n\n成绩为通过有效例数／有效例总数。输入、配置或参考错误属基础设施错误，不计为考生失分；无有效例不产生成绩。工具验证不证明数值精度、物理适用性或资源预算已校准。\n'
            variation = {'photon-absorption':'层数、群数、层厚、吸收、群能和入射束', 'slab-transport-steady':'层数、群数、材料、源和入射', 'slab-transport-transient':'层数、群数、材料、群速、源、入射、初态和请求时刻', 'neutron-diffusion-source':'层数、群数、材料和源', 'neutron-diffusion-critical':'层数、群数和材料响应', 'point-kinetics':'缓发组数、材料参数、独立初态、控制历史和请求时刻', 'decay-network':'核素数、衰变参数、分支、初始库存和请求时刻', 'irradiated-network':'核素数、衰变和反应参数、分支、初始库存、通量历史和请求时刻'}[slug]
            instruction = instruction.replace('层数、群数、材料、源／历史或网络及初态', variation)
            if slug != 'neutron-diffusion-critical':
                instruction = instruction.replace('；临界题的归一化和正号必须遵守物理定义', '')
            (td/'instruction.md').write_text(instruction, encoding='utf-8')
            policy = dict(version=2, quantities={q:dict(unit=s['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=s['atol'],rtol=s['rtol'])) for q,s in c['outputs'].items()})
            (td/'grading.json').write_text(json.dumps(policy, indent=2)+'\n', encoding='utf-8')
            (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n', encoding='utf-8')
            (td/'harbor').mkdir(exist_ok=True)
            (td/'harbor/requirements.txt').write_text('scipy==1.18.1\n', encoding='utf-8')
            (td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 2\nmemory_mb = 4096\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n', encoding='utf-8')
        (sd/'README.md').write_text(f'# {sec.split("-")[0]} {title}\n\n'+'\n'.join(links)+'\n', encoding='utf-8')
        toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
    (CH/'README.md').write_text('# 第十五章 辐射输运与核工程物理分析\n\n五节八题；各题只依赖instruction、DATA及通用CONTRACT。正式数据、参考与发布留后。\n\n'+'\n'.join(toc)+'\n\n维护：[章规划](../design/chapter-15-radiation-nuclear.md)、[清单](../design/chapter-15-task-plan.md)、[进度](../design/reviews/chapter-15-progress.md)。\n', encoding='utf-8')


if __name__ == '__main__':
    main()
