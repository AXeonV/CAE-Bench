"""Render maintained plasma task definitions; never generate numerical cases."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHAPTER = ROOT / 'qbank/14-plasma'


def value(unit, meaning, lower=None, upper=None, integer=False):
    result = dict(unit=unit, meaning=meaning)
    if lower is not None:
        result['lower'] = lower
    if upper is not None:
        result['upper'] = upper
    if integer:
        result['integer'] = True
    return result


def field(unit, meaning, shape=(1,), *, location=None, axis='initial', lower=None,
          positive=False, labels=None):
    result = dict(unit=unit, meaning=meaning, shape=list(shape), axis=axis)
    if location:
        result['location'] = location
    if lower is not None:
        result['lower'] = lower
    if positive:
        result['positive'] = True
    if labels:
        result['labels'] = labels
    return result


def record(role, variable, location, **data):
    return dict(role=role, variable=variable, location=location, data=data)


def output(unit, meaning, location, shape=(1,), atol=1e-8, rtol=.002, labels=None):
    result = field(unit, meaning, shape, location=location, axis='output', labels=labels)
    result.update(atol=atol, rtol=rtol)
    return result


def entities(maximum, meaning, minimum=1):
    return dict(kind='entities', minimum=minimum, maximum=maximum, meaning=meaning)


def base(number, name, section, dimension, seconds, cpus=1, memory=1024):
    return dict(number=number, name=name, section=section, spatial_dimension=dimension,
                timeout=seconds, cpus=cpus, memory_mb=memory,
                parameters={'end_time': value('s', '物理终时τ，0<τ≤1000000', 0, 1e6)},
                locations={}, records={}, outputs={}, physics='', restrictions='')


def specifications():
    tasks = {}
    for slug, relativistic in [('charged-orbits', False), ('relativistic-orbits', True)]:
        s = base('14.1.2' if relativistic else '14.1.1',
                 '相对论外场带电粒子轨道' if relativistic else '非相对论外场带电粒子轨道',
                 '14.1-particle-orbits', 3, 60 if relativistic else 30)
        s['locations'] = dict(particles=entities(128, '互不作用的带电粒子'),
                              system=entities(1, '唯一外场参数对象'))
        s['records'] = dict(
            particles=record('material', 'particle', 'particles',
                             mass=field('kg', '静质量m，严格正', positive=True),
                             charge=field('C', '有符号电荷q，非零')),
            launch=record('initial', 'particle_state', 'particles',
                          position=field('m', 't=0位置x', (3,)),
                          **({'momentum': field('kg.m/s', 't=0机械动量p，不是γv或归一化动量', (3,))}
                             if relativistic else {'velocity': field('m/s', 't=0速度v', (3,))})),
            electric=record('source', 'electric_field', 'system',
                            offset=field('V/m', '外场E0(t)', (3,), axis='drive'),
                            gradient=field('V/m2', '对称矩阵G(t)，E=E0+G(x−r0)', (3, 3), axis='drive'),
                            origin=field('m', '固定参考点r0', (3,))),
            magnetic=record('source', 'magnetic_field', 'system',
                            value=field('T', '空间均匀且时间恒定的B0', (3,))))
        s['physics'] = ('在全空间R³中演化各独立粒子。外电场E(x,t)=E0(t)+G(t)(x−r0)，G为对称矩阵；外磁场B0均匀恒定。'
                        '无空间电荷反馈、粒子间力、碰撞、壁面、逃逸终止或辐射反作用。')
        if relativistic:
            s['physics'] += ('机械动量p满足dp/dt=q(E+v×B0)，dx/dt=v，v=p/(mγ)，'
                             'γ=sqrt(1+|p|²/(m²c²))，c=299792458 m/s。电荷和质量逐粒子给定，不把p当作速度。')
        else:
            s['physics'] += 'dx/dt=v，m dv/dt=q(E+v×B0)。非相对论模型不添加γ或速度裁剪。'
        s['restrictions'] = ('G各采样帧须严格对称。end_time严格正；数据保证全部所需轨道存在且有限。'
                             + ('' if relativistic else '正式数据还须保证全过程|v|≤0.01c，c=299792458 m/s。'))
        s['outputs'] = dict(position=output('m', '全局位置x(t)', 'particles', (3,), 1e-7, 1e-5))
        key = 'momentum' if relativistic else 'velocity'
        s['outputs'][key] = output('kg.m/s' if relativistic else 'm/s', '机械动量p(t)' if relativistic else '速度v(t)',
                                    'particles', (3,), 1e-28 if relativistic else 1e-3, 1e-5)
        tasks[slug] = s

    s = base('14.2.1', '离散速度态碰撞演化', '14.2-collisions-reactions', 3, 60)
    s['parameters']['state_count'] = value('1', '速度态数S，JSON整数2..16', 2, 16, True)
    s['locations'] = dict(states=entities(16, 'S个固定离散速度态，IDs为0..S−1', 2),
                          system=entities(1, '唯一碰撞系综'))
    s['records'] = dict(
        states=record('material', 'velocity_state', 'states', velocity=field('m/s', '各速度态v_i', (3,))),
        particles=record('material', 'particle', 'system', mass=field('kg', '各态共同质量m>0', positive=True),
                         charge=field('C', '各态共同非零电荷q')),
        transitions=record('material', 'transition_rate', 'system',
                           value=field('1/s', 'K_ij(t)：从态i转入态j的单位时间率；Kii=0，非对角非负', ('S', 'S'), axis='drive')),
        population=record('initial', 'state_density', 'states', value=field('1/m3', '各态初始数密度n_i≥0，总数密度>0', lower=0)))
    s['physics'] = ('均匀带电粒子与无限中性热浴发生给定离散态碰撞，不跟踪随机单粒子样本。'
                    'dn_i/dt=Σ_{j≠i}(K_ji n_j−K_ij n_i)。态速度和粒子质量、电荷恒定；'
                    '碰撞可以向热浴交换动量和能量，不强制细致平衡。'
                    '系综电流J=qΣ_i n_i v_i，动能密度W=(m/2)Σ_i n_i|v_i|²。无空间输运或外场加速。')
    s['restrictions'] = 'states数必须等于S。每帧K对角线严格零，非对角非负；初始人口总和严格正。'
    s['outputs'] = dict(state_density=output('1/m3', '各态数密度n_i', 'states', atol=1e3),
                        current_density=output('A/m2', '系综电流J', 'system', (3,), 1e-8),
                        kinetic_energy_density=output('J/m3', '系综动能密度W', 'system', atol=1e-8))
    tasks['collisional-states'] = s

    s = base('14.2.2', '均匀弱电离气体反应', '14.2-collisions-reactions', 1, 60)
    s['parameters'].update(neutral_density=value('1/m3', '固定中性库数密度N>0', 0, 1e30),
                            elementary_charge=value('C', '正的基本电荷量e>0', 0, 1))
    s['locations'] = dict(system=entities(1, '唯一均匀反应体积的局部密度状态'))
    species = ['electron', 'positive_ion', 'negative_ion']
    s['records'] = dict(
        initial=record('initial', 'number_density', 'system', value=field('1/m3', 'ne、ni、na，依次电子、单正离子、单负离子', (3,), lower=0, labels=species)),
        rates=record('material', 'reaction_rates', 'system',
                     ionization=field('m3/s', '电子碰撞电离系数ki(t)≥0', axis='drive', lower=0),
                     attachment=field('m3/s', '电子附着系数ka(t)≥0', axis='drive', lower=0),
                     recombination=field('m3/s', '电子—正离子复合系数kr(t)≥0', axis='drive', lower=0),
                     neutralization=field('m3/s', '负离子—正离子中和系数kn(t)≥0', axis='drive', lower=0)))
    s['physics'] = ('中性气体库N保持恒定，电子平均能量由外部维持，全部反应系数直接给定，不另解温度或电场。'
                    '反应为e+g→2e+i、e+g→a、e+i→g、a+i→2g。定义Ii=ki N ne，Ia=ka N ne，'
                    'R=kr ne ni，A=kn na ni；dne/dt=Ii−Ia−R，dni/dt=Ii−R−A，dna/dt=Ia−A。'
                    '输出净电荷密度ρ=e(ni−ne−na)，不强制初始电中性，也不从ρ反推外电场。')
    s['restrictions'] = '初态非负，至少一种带电物种非零；数据保证全部请求时刻前max(ne,ni,na)≤0.01N且解有限。'
    s['outputs'] = dict(number_density=output('1/m3', '依次ne、ni、na', 'system', (3,), 1e3, .002, species),
                        charge_density=output('C/m3', '净自由电荷ρ', 'system', atol=1e-10))
    tasks['plasma-chemistry'] = s

    s = base('14.3.1', '周期一维静电动力学', '14.3-electrostatic', 1, 600, 4, 4096)
    s['parameters'].update(velocity_count=value('1', '等宽速度箱数Nv，JSON整数8..128', 8, 128, True),
                           velocity_min=value('m/s', '速度区间左端vmin<0', -1e8, 0),
                           velocity_max=value('m/s', '速度区间右端vmax>0', 0, 1e8),
                           mass=value('kg', '移动物种质量m>0', 0, 1),
                           charge=value('C', '移动物种电荷q<0', -1, 0),
                           permittivity=value('F/m', '均匀绝对介电常数ε>0', 0, 1))
    s['locations'] = dict(domain=dict(kind='mesh', entity='node', maximum=257, meaning='全部区间网格节点'),
                          cells=dict(kind='mesh', entity='element', maximum=256, meaning='全部一阶区间单元'))
    s['records'] = dict(initial=record('initial', 'distribution', 'cells',
                                      value=field('s/m4', '每个空间单元、每个速度箱上的f0平均；按v递增排列', ('Nv',), lower=0)))
    s['physics'] = ('空间区间[xL,xR]周期，L=xR−xL；一移动负电物种与静止均匀正背景。'
                    '∂t f+v∂x f+(q/m)E∂v f=0，n=∫f dv，−ε∂xxφ=q(n−n0)，E=−∂xφ。'
                    '背景n0定义为初态总粒子数除以L，即n0=(1/L)∫∫f0 dv dx，全程固定，不是独立输入参数。'
                    'φ、E和f的空间周期迹相等，且∫φ dx=0固定电势规范，∫E dx=0；不逐帧减去电荷背景。'
                    '速度区间[vmin,vmax]被Nv个等宽箱划分，f0按每个空间单元×速度箱上的给定常值重建；区间外f=0。'
                    '速度端点使用零入流；数据保证直到τ分布支撑都与速度端点保持正距离，故没有截断损失。'
                    '观测distribution为每个相空间箱的双重平均，number_density、potential、electric_field为每个空间单元的长度平均。')
    s['restrictions'] = ('区间网格至少2单元，Nv≥8；vmin严格负、vmax严格正，q严格负。'
                         '初始f非负且总积分>0；按初态积分定义背景，保证周期Poisson相容。'
                         '相空间箱只是输入重建及输出观测，不指定内部离散。正式数据须验证速度支撑、正则弱解和预算。')
    s['outputs'] = dict(distribution=output('s/m4', 'f在空间单元×速度箱上的平均', 'cells', ('Nv',), 1e-6, .01),
                        number_density=output('1/m3', 'n的空间单元平均', 'cells', atol=1e3, rtol=.005),
                        potential=output('V', '零空间均值φ的单元平均', 'cells', atol=1e-5, rtol=.005),
                        electric_field=output('V/m', 'Ex的单元平均', 'cells', atol=1e-4, rtol=.005))
    tasks['vlasov-poisson'] = s

    s = base('14.3.2', '单向束流的稳态空间电荷', '14.3-electrostatic', 1, 60)
    s['steady'] = True
    s['parameters'] = dict(mass=value('kg', '束粒子质量m>0', 0, 1),
                          charge=value('C', '负束粒子电荷q<0', -1, 0),
                          permittivity=value('F/m', '绝对介电常数ε>0', 0, 1),
                          injection_energy=value('J', '每粒子注入动能W0>0', 0, 1e10),
                          particle_flux=value('1/(m2.s)', '沿+x恒定数通量Γ>0', 0, 1e40))
    s['locations'] = dict(domain=dict(kind='mesh', entity='node', maximum=513, meaning='全部区间网格节点'),
                          cells=dict(kind='mesh', entity='element', maximum=512, meaning='全部一阶区间单元'),
                          left=dict(kind='mesh', entity='node', maximum=1, meaning='唯一最左端点'),
                          right=dict(kind='mesh', entity='node', maximum=1, meaning='唯一最右端点'))
    s['records'] = dict(left_potential=record('boundary', 'potential', 'left', value=field('V', '左电极电势VL')),
                        right_potential=record('boundary', 'potential', 'right', value=field('V', '右电极电势VR>VL')))
    s['physics'] = ('负电束沿+x注入一维区间，单能、稳态、无碰撞、无背景和反射。'
                    'v(x)=sqrt(2[W0−q(φ(x)−VL)]/m)>0，n(x)=Γ/v(x)，−εφ″=q n，E=−φ′。'
                    '边界φ(xL)=VL、φ(xR)=VR；电势采用绝对给定基准。入射和出射均不反射粒子，未引入中和背景。'
                    '只接收单调加速分支φ′>0，不允许虚阴极／多流；每个输出为相应空间单元的长度平均，密度平均不是Γ除以平均速度。')
    s['restrictions'] = ('令e=−q、ΔV=VR−VL、vin=sqrt(2W0/m)、L=xR−xL；'
                         '须0<eΔV≤W0且eΓL²/(ε vin ΔV)≤0.25，以限定温和空间电荷单调分支。'
                         '接收域内非相对论全过程速度≤0.01c，c=299792458 m/s；正式数据仍须独立确认解和资源。')
    s['outputs'] = dict(potential=output('V', '绝对电势φ的单元平均', 'cells', atol=1e-5),
                        electric_field=output('V/m', 'Ex的单元平均', 'cells', atol=1e-4),
                        number_density=output('1/m3', 'n的单元平均', 'cells', atol=1e3),
                        velocity=output('m/s', '正向速度v的单元平均', 'cells', atol=1e-3))
    tasks['space-charge-beam'] = s

    for energy in (False, True):
        slug = 'energy-discharge' if energy else 'isothermal-discharge'
        s = base('14.4.2' if energy else '14.4.1', '含电子能量的弱电离放电' if energy else '等温弱电离放电',
                 '14.4-discharge', 1, 600 if energy else 300, 2, 4096 if energy else 2048)
        s['parameters'].update(elementary_charge=value('C', '正电荷量e>0', 0, 1),
                               permittivity=value('F/m', '均匀绝对介电常数ε>0', 0, 1),
                               neutral_density=value('1/m3', '固定中性库N>0', 0, 1e30))
        s['locations'] = dict(domain=dict(kind='mesh', entity='node', maximum=257, meaning='全部一阶区间网格节点'),
                              cells=dict(kind='mesh', entity='element', maximum=256, meaning='全部区间单元'),
                              left=dict(kind='mesh', entity='node', maximum=1, meaning='最左端点'),
                              right=dict(kind='mesh', entity='node', maximum=1, meaning='最右端点'))
        transport = dict(electron_mobility=field('m2/(V.s)', '取正数的电子迁移率μe>0，电荷负号另计', positive=True),
                         ion_mobility=field('m2/(V.s)', '正离子迁移率μi>0', positive=True),
                         electron_diffusion=field('m2/s', 'De>0', positive=True),
                         ion_diffusion=field('m2/s', 'Di>0', positive=True),
                         recombination=field('m3/s', '复合系数kr≥0', lower=0))
        if energy:
            transport.update(energy_mobility=field('m2/(V.s)', 'μw>0，独立给定，不自动用5/3倍电子系数', positive=True),
                             energy_diffusion=field('m2/s', 'Dw>0', positive=True),
                             ionization_prefactor=field('m3/s', 'k0≥0', lower=0),
                             ionization_energy=field('J', '电离阈值εI>0，也是每次电离损失能', positive=True),
                             energy_relaxation=field('1/s', '能量弛豫率νw≥0', lower=0),
                             thermal_energy=field('J', '中性热浴每电子目标平均能εg>0', positive=True))
        else:
            transport['ionization'] = field('m3/s', '固定ki≥0，不由局部场隐含推断', lower=0)
        initial = dict(electron_density=field('1/m3', 'ne(t=0)>0', positive=True),
                       ion_density=field('1/m3', 'ni(t=0)>0', positive=True))
        if energy:
            initial['electron_energy'] = field('J/m3', '真实初态电子能量密度w>0', positive=True)
        boundary = dict(potential=field('V', '电极电势V(t)', axis='drive'),
                        electron_density=field('1/m3', '电子库Dirichlet密度>0', axis='drive', positive=True),
                        ion_density=field('1/m3', '离子库Dirichlet密度>0', axis='drive', positive=True))
        if energy:
            boundary['electron_energy'] = field('J/m3', '电子库Dirichlet能量密度>0', axis='drive', positive=True)
        s['records'] = dict(transport=record('material', 'plasma_transport', 'cells', **transport),
                            initial=record('initial', 'plasma_state', 'domain', **initial),
                            left_reservoir=record('boundary', 'reservoir', 'left', **boundary),
                            right_reservoir=record('boundary', 'reservoir', 'right', **boundary))
        if energy:
            s['records']['heating'] = record('source', 'energy_source', 'cells',
                                               value=field('W/m3', '额外外加体功率Q≥0；不含电场做功', axis='drive', lower=0))
        s['physics'] = ('固定中性库中只含电子和单正离子。E=−∂xφ，−ε∂xxφ=e(ni−ne)。'
                        'Γe=−μe ne E−De∂xne，Γi=+μi ni E−Di∂xni，'
                        '∂tne+∂xΓe=R，∂tni+∂xΓi=R，R=ki N ne−kr ne ni。'
                        '左右端同时给定φ、ne、ni的库值；无默认绝缘、鞘层或二次发射。'
                        '初态给ne、ni，电势每时刻由Poisson与电极值确定，不作为迭代初猜输入。'
                        '各单元输运系数常数；t>0的解在内部界面各密度连续、各物种数通量连续，φ和ε∂xφ连续；初态按给定P1函数取弱初态，不额外要求其初始通量连续。')
        if energy:
            s['physics'] += ('此外Γw=−μw w E−Dw∂xw，∂tw+∂xΓw=−e Γe E+Q−εI ki N ne'
                             '−kr ni w−νw(w−ne εg)。ki=k0 max(w/(ne εI)−1,0)。'
                             'w为J/m³，w/ne为每电子能量J，不是eV、温度或动能速度矩。'
                             '左右给定w，内部w和Γw连续；所有损失只按上述式子计一次。')
        s['physics'] += '输入初态为网格节点P1连续重建，' + ('系数及Q' if energy else '系数') + '为逐单元常值。输出均为真实单元长度平均。'
        s['restrictions'] = ('初态和边界密度严格正，初态端点与t=0库值严格一致；'
                             '数据保证直到τ密度保持正、max(ne,ni)≤0.01N及弱电离漂移扩散适用，解与观测有限。'
                             + ('电子能量也须严格正且初态边界一致。' if energy else '')
                             + '不强制爱因斯坦关系；这是明确给定有效输运系数的有限物理模型。')
        s['outputs'] = dict(electron_density=output('1/m3', 'ne的单元平均', 'cells', atol=1e3, rtol=.005),
                            ion_density=output('1/m3', 'ni的单元平均', 'cells', atol=1e3, rtol=.005),
                            potential=output('V', 'φ的单元平均', 'cells', atol=1e-5, rtol=.005),
                            electric_field=output('V/m', 'Ex的单元平均', 'cells', atol=1e-4, rtol=.005))
        if energy:
            s['outputs']['electron_energy'] = output('J/m3', 'w的单元平均，而非平均每电子能', 'cells', atol=1e-8, rtol=.005)
        tasks[slug] = s

    s = base('14.5.1', '冷等离子体自洽电流弛豫', '14.5-electromagnetic-response', 3, 60)
    s['parameters']['permittivity'] = value('F/m', '背景绝对介电常数ε>0', 0, 1)
    s['locations'] = dict(species=entities(8, '1..8种均匀带电流体'), system=entities(1, '唯一均匀电磁状态'))
    s['records'] = dict(
        species=record('material', 'charged_species', 'species', mass=field('kg', 'm_s>0', positive=True),
                       charge=field('C', '有符号q_s，非零'), density=field('1/m3', '恒定n_s>0', positive=True),
                       collision_frequency=field('1/s', '对静止热浴动量弛豫ν_s≥0', lower=0)),
        initial_current=record('initial', 'current_density', 'species', value=field('A/m2', '各物种初始电流J_s', (3,))),
        initial_electric=record('initial', 'electric_field', 'system', value=field('V/m', '初始电场E', (3,))),
        magnetic=record('source', 'magnetic_field', 'system', value=field('T', '恒定背景B0', (3,))),
        impressed=record('source', 'impressed_current', 'system', value=field('A/m2', '外加电流Jext(t)，按安培定律作为总电流的一部分', (3,), axis='drive')))
    s['physics'] = ('空间均匀冷流体，密度恒定，静止补偿背景确保净电荷为零，不额外参与电流。'
                    'ε dE/dt=−Σ_s J_s−Jext(t)，dJ_s/dt=(n_s q_s²/m_s)E+(q_s/m_s)J_s×B0−ν_s J_s。'
                    '所有矢量均全局三维，无空间梯度或传播边界，无压力／热能方程。电场是未知量而非给定驱动；'
                    '碰撞耗散传给不演化的热浴。结果为同步物理时刻值，不接受半步电流。')
    s['restrictions'] = '各q_s非零，质量、密度正，碰撞率非负；数据保证全过程非相对论冷流体近似适用。'
    s['outputs'] = dict(electric_field=output('V/m', '自洽E(t)', 'system', (3,), 1e-6, .002),
                        current_density=output('A/m2', '各物种J_s(t)，不作物种求和', 'species', (3,), 1e-8, .002))
    tasks['cold-plasma-relaxation'] = s

    s = base('14.5.2', '分层磁化等离子体单频响应', '14.5-electromagnetic-response', 1, 180, 2, 2048)
    s['steady'] = True
    s['parameters'] = dict(angular_frequency=value('1/s', '角频率ω>0，单位不另乘2π', 0, 1e20),
                          permittivity=value('F/m', '两侧背景和全部层的束缚电荷介电常数ε>0', 0, 1),
                          permeability=value('H/m', '各处磁导率μ>0', 0, 1),
                          mass=value('kg', '移动负电物种质量m>0', 0, 1),
                          charge=value('C', '移动负电物种q<0', -1, 0))
    s['locations'] = dict(layers=entities(32, '沿+x的均匀层；行序决定层次'),
                          system=entities(1, '唯一入射／散射系统'),
                          receivers=dict(kind='points', minimum=1, maximum=256, meaning='层内真实一维空间接收点，坐标单位m'))
    complex_labels = ['y_real', 'y_imag', 'z_real', 'z_imag']
    s['records'] = dict(
        layers=record('material', 'plasma_layer', 'layers', thickness=field('m', '每层厚h>0', positive=True),
                      density=field('1/m3', '移动物种平衡数密度n>0，静止正背景中和', positive=True),
                      collision_frequency=field('1/s', '正的动量碰撞率ν>0', positive=True)),
        magnetic=record('source', 'magnetic_field', 'system',
                        value=field('T', '所有层及两侧共同的恒定有符号背景Bx，沿+x')),
        incident=record('source', 'incident_electric', 'system',
                        value=field('V/m', 'x=0处向右入射的Ey、Ez复振幅，非零', (2, 2), labels=complex_labels)))
    s['physics'] = ('采用Re[F(x)exp(−iωt)]。层从x=0依次到H=Σh，两侧为相同ε、μ的无等离子体半空间，'
                    '无右入射。背景磁场Bx沿+x且全空间恒定。每层的横向u满足m(ν−iω)u=q(E+u×Bx e_x)，J=n q u；'
                    '纵向场和速度为零。Maxwell为∇×E=iωμH场、∇×H场=J−iωεE；'
                    '界面Ey、Ez、Hy、Hz连续，无自由面电流。入射／反射振幅定义于x=0，透射振幅定义于x=H。'
                    '左侧E=Ei exp(ikx)+Er exp(−ikx)，右侧E=Et exp(ik(x−H))，'
                    'k=ωsqrt(εμ)，波阻抗Z=sqrt(μ/ε)，各行波H场=传播单位方向×E/Z。'
                    'R=|Er|²/|Ei|²，T=|Et|²/|Ei|²，不按各偏振分别除入射分量。'
                    '输出层内场包含所有反射与透射；不求随机粒子、热运动、非线性密度或纵向电静波。')
    s['restrictions'] = ('每层n、ν、h严格正；入射两复分量的总模平方>0。接收点须严格位于某一层内部，'
                         '不在界面或半空间，ID行序不代表x顺序。正碰撞率限定有耗响应；正式数据需校准近共振难度及场观测精度。')
    s['outputs'] = dict(reflected_amplitude=output('V/m', 'x=0处Er的Ey、Ez', 'system', (2, 2), 1e-7, .003, complex_labels),
                        transmitted_amplitude=output('V/m', 'x=H处Et的Ey、Ez', 'system', (2, 2), 1e-7, .003, complex_labels),
                        electric_amplitude=output('V/m', '接收点总场Ey、Ez', 'receivers', (2, 2), 1e-7, .003, complex_labels),
                        magnetic_amplitude=output('A/m', '接收点总场Hy、Hz', 'receivers', (2, 2), 1e-9, .003, complex_labels),
                        reflectance=output('1', '总功率反射率R', 'system', atol=1e-7, rtol=.003),
                        transmittance=output('1', '总功率透射率T', 'system', atol=1e-7, rtol=.003))
    tasks['magnetized-plasma-slab'] = s
    return tasks


def prepare_specs():
    specs = specifications()
    for cfg in specs.values():
        cfg['mesh'] = 'cells' in cfg['locations']
        cfg['driven'] = any(s['axis'] == 'drive' for r in cfg['records'].values() for s in r['data'].values())
        for s in [s for r in cfg['records'].values() for s in r['data'].values()] + list(cfg['outputs'].values()):
            if s.get('labels') or any(isinstance(x, str) for x in s['shape']):
                s['kind'] = 'components'
            elif s['shape'] == [1]:
                s['kind'] = 'scalar'
            elif s['shape'] == [cfg['spatial_dimension']]:
                s['kind'] = 'vector'
            elif s['shape'] == [cfg['spatial_dimension'], cfg['spatial_dimension']]:
                s['kind'] = 'tensor'
            else:
                s['kind'] = 'components'
    specs['charged-orbits']['scale_limits'] = (
        '记τ=end_time、a=max粒子|q|/m，B=|B0|，G*=max帧||G||F。须τ a B≤200、τ sqrt(a G*)≤100；'
        '||·||F为Frobenius范数。')
    specs['relativistic-orbits']['scale_limits'] = specs['charged-orbits']['scale_limits'] + '另须τ a max帧|E0−G r0|/c≤100。'
    specs['collisional-states']['scale_limits'] = '须τ max帧max_i Σ_j Kij≤10000，限制单位时段碰撞尺度。'
    specs['plasma-chemistry']['scale_limits'] = '须τ N max帧(ki+ka)≤100，τ (0.01N) max帧(kr+kn)≤10000；相同drive轴逐帧求和。'
    specs['vlasov-poisson']['scale_limits'] = (
        '令L=xR−xL、ωp=sqrt(q²n0/(mε))；须τ ωp≤200、τ max(|vmin|,vmax)/L≤1000。')
    for slug in ('isothermal-discharge', 'energy-discharge'):
        specs[slug]['scale_limits'] = (
            '记hmin为最短网格区间，D*为所有扩散系数最大值，μ*为所有迁移率最大值；须τ D*/hmin²≤100000、'
            'τ μ* e(0.01N)/ε≤10000。此范围不指定显式或隐式算法。')
    specs['cold-plasma-relaxation']['scale_limits'] = (
        '对每个物种须τ[ν_s+|q_s||B0|/m_s+sqrt(n_s q_s²/(m_s ε))]≤200。')
    specs['magnetized-plasma-slab']['scale_limits'] = (
        '1e−14≤ε≤1e−8 F/m，1e−8≤μ≤1e−4 H/m；各层须0.001≤ν/ω≤100、'
        'sqrt(n q²/(mε))/ω≤30、|q Bx|/(mω)≤30；总光学厚度ωsqrt(εμ)H≤100；'
        '入射复矢量模长在[1e−6,1e6] V/m。')
    return specs


def type_text(s):
    limits = ('；严格正' if s.get('positive') and '>0' not in s['meaning'] and '严格正' not in s['meaning'] else '')
    limits += f"；≥{s['lower']}" if 'lower' in s and '≥' not in s['meaning'] else ''
    shape = '[' + ','.join(map(str, s['shape'])) + ']'
    return f"kind=`{s['kind']}`、component_shape=`{shape}`，`{s['unit']}`；{s['meaning']}{limits}"


def data_text(slug, s):
    params = '\n'.join(f"| `{k}` | `{v['unit']}` | {v['meaning']} |" for k, v in s['parameters'].items())
    locs = '\n'.join(f"| `{k}` | {v['kind']}，{v.get('minimum', 1)}..{v['maximum']}个；{v['meaning']} |" for k, v in s['locations'].items())
    if s['mesh']:
        geometry = ('meshes恰含main，geometries为空。main是沿全局x轴的连通区间[xL,xR]，2..'
                    f"{s['locations']['cells']['maximum']}个非退化一阶线单元（Gmsh type1），所有节点y=z=0，"
                    '只有这些线单元，无未用节点、间隙、分叉、重复或重叠。domain和cells分别恰含全部节点和全部线单元。'
                    '编号按tag递增，单元在x方向的次序须由坐标和连接关系确定，不按tag猜测。'
                    + ('left、right分别恰含最左和最右节点，条件作用于该端点。' if 'left' in s['locations'] else '两端按周期迹关联，不合并其不同节点身份。'))
    else:
        geometry = 'meshes及geometries均为空，系统不提供空间网格。entities是真实粒子、物种、状态或层对象，不是伪造空间探针。'
    time = ('initial和output两轴均恰为float64[1]的[0.0]，0仅为稳态存储标记。' if s.get('steady') else
            'initial轴恰为float64[1]的[0.0]；output轴含2..65帧，从0严格递增至end_time。输出含真实初态。')
    if s['driven']:
        time += 'drive轴含2..129帧，从0严格递增至end_time；所有drive场在相邻样本间分量线性插值，不允许外推。'
    records = []
    for op, r in s['records'].items():
        rows = '\n'.join(f"| `{key}` | {type_text(d)} | {d['axis']} |" for key, d in r['data'].items())
        records.append(f"### `{op}`\n\nrole=`{r['role']}`、variable=`{r['variable']}`、operator=`{op}`、location=`{r['location']}`；恰一条覆盖完整该位置，data恰含以下键：\n\n| data键 | 类型、单位与含义 | 场时间轴 |\n|---|---|---|\n{rows}\n")
    outputs = '\n'.join(f"| `{q}` | {type_text(v)} | `{v['location']}` |" for q, v in s['outputs'].items())
    special_labels = []
    for key, d in [(f'{op}.{key}', d) for op, r in s['records'].items() for key, d in r['data'].items()] + list(s['outputs'].items()):
        if d.get('labels'):
            special_labels.append(f"`{key}`的components固定为`{json.dumps(d['labels'], ensure_ascii=False)}`。")
    if slug == 'collisional-states':
        special_labels.append('转移矩阵shape=[S,S]，按[i,j]最后轴优先展开，components依次为from_0_to_0、from_0_to_1、…、from_(S−1)_to_(S−1)。')
    if slug == 'vlasov-poisson':
        special_labels.append('distribution的component_shape=[Nv]，components依次v0、v1、…、v(Nv−1)，第j箱为[vmin+jΔv,vmin+(j+1)Δv]；端点对积分无影响。')
    output_kind = 'cells为average，其他位置为point' if s['mesh'] else '所有位置为point'
    identity = ('网格IDs为正且严格递增。' if s['mesh'] else 'entities的IDs非负严格递增，system恰一对象；ID数值不携带物理含义。')
    if any(v['kind'] == 'points' for v in s['locations'].values()):
        identity += 'points的IDs非负严格递增，coordinates为float64[N,D]米制坐标。'
    if not s['mesh']:
        identity += '对象之间无默认邻接或插值。'
    sampling = ('space：domain节点为piecewise_linear（网格P1重建），cells为piecewise_constant（逐单元常值），端点为uniform。'
                if s['mesh'] else 'space=uniform，仅表示对象自身属性，不作对象间空间重建。')
    time_sampling = 'initial场time=constant' + ('，drive场time=linear。' if s['driven'] else '。')
    stepping = '' if s.get('steady') else '内部时间步、稳定性限制及每步迭代策略由考生决定，输出时刻不是积分步长。'
    return f'''# {slug} 数据契约

本题使用[通用数据协议](../../../../docs/CONTRACT.md)。入口problem.json引用扁平HDF5数据文件，路径相对清单。physics恰含model、parameters，model=`plasma-{slug}-v1`；task可省略，出现须为`{slug}`。spatial_dimension={s['spatial_dimension']}；不混用profile、contract_version、analysis或materials。

## 物理语义

{s['physics']}

## 全局参数

parameters恰含下表，标量均为{{"value":数值,"unit":单位}}；有限且不接受布尔代替数值。标记整数的参数须JSON整数，其余为实数。

| 参数 | 单位 | 含义与范围 |
|---|---|---|
{params}

## 位置、几何与身份

{geometry} locations恰含下表；{identity}

| location | 支持范围与含义 |
|---|---|
{locs}

## 时间与数组

time_axes恰含{('initial、output、drive' if s['driven'] else 'initial、output')}。{time} initial轴上的材料或源表示全过程固定量，不是额外初态。{stepping}

输入和输出数值均float64；IDs为int64。完整场shape为[T,N,*component_shape]，不省略轴；scalar的shape=[1]、components=["value"]；vector按全局坐标顺序；tensor按最后轴优先的xx、xy、…顺序。components类型除下述特别标签外按最后轴优先依次c1、c2、…编号。{' '.join(special_labels)}

fields恰含条件实际引用的字段；data键引用{{"field":"逻辑字段名"}}，逻辑名和array key均可自由命名，两者不可混用。字段quantity等于data键；data键为value时等于该条件variable。字段须与条件同location。scalar也允许同单位的{{"value":有限标量,"unit":"单位"}}常量，表示全过程固定，不能表示随时间变化的数据；非scalar只能field，不接受内联数组。

输入sampling必须显式，extrapolation=forbid；{time_sampling}{sampling} 输入value_kind：{output_kind}。位置和分量含义由本题定义，不进行隐式单位、轴或归一化转换。

## 条件全集

以下每种operator均必须恰出现一次；不接受其他条件、data键或未被引用字段。条件数组次序不改变含义。

{chr(10).join(records)}
## 输出

每个quantity至少请求一次，允许以不同逻辑名／array重复请求；每个请求覆盖其表列完整位置。所有输出time_axis=output，无sampling，value_kind为{output_kind}，shape及components按上文规定。

| quantity | 类型、单位与物理含义 | location |
|---|---|---|
{outputs}

结果HDF5恰含输出array及需要复制的IDs／时间轴，严格保留输入给定身份和顺序；不额外输出坐标、输入场、新网格或中间步。

## 接收限制

{s['restrictions']} {s.get('scale_limits', '')} 所有规定输出均保证有限且绝对值不超过1e100，可由float64表示。输入场和请求输出各不超过4000000数值分量。上文范围、固定模型和组合共同定义接收集合；字段合法不证明物理适用、解精度或预算可达。
'''


def instruction_text(s):
    tolerances = '\n'.join(f"| `{q}` | {v['atol']:g} | {v['rtol']:g} | `{v['unit']}` |" for q, v in s['outputs'].items())
    return f'''# {s['number']} {s['name']}

实现可复用求解器，覆盖[DATA](DATA.md)声明的整个问题族。提交冻结后处理多个未见算例，不按某个几何、初态或参数固定输出。

{s['physics']}

模型及材料响应由题目固定，考生负责内部离散、求积、积分、线性／非线性求解与精度控制；语言和软件自由。覆盖完整契约的解析或降阶实现同样有效。输入字段和所有算例变化、输出定义见DATA，通用读写见[CONTRACT](../../../../docs/CONTRACT.md)。

## 运行与资源

入口`python solve.py --input /path/problem.json --output /path/result.h5`，可用此入口封装C++等实现。每例Linux AMD64，{s['timeout']}秒墙钟（包含启动与I/O）、{s['cpus']}个逻辑CPU、{s['memory_mb']}MB、0GPU。程序正常退出并写完HDF5；无独立输出字节上限，内存和DATA规模限制仍适用。逐例求解环境不联网；生成程序阶段网络由运行环境提供。

Agent生成预算3600秒，镜像构建预算1800秒。环境提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++、OpenMP、OpenMPI、HDF5开发库，不要求使用Python。仅保证串行HDF5写出，可用MPI计算后由一个进程汇总。{'稳态／单频输出轴仅作存储标记。' if s.get('steady') else '时间步和迭代由程序选择，按输入请求时刻输出同步状态。'} 输入规模见DATA；资源与阈值是设计目标，正式数据阶段另行校准。

## 评分

每例正常退出、输出结构合法且全部quantity、时刻、对象和分量均满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0分；等号接受，未通过分量不作豁免。不做去均值、相位对齐、自动重排或最佳拟合。

| quantity | atol | rtol | 单位 |
|---|---|---|---|
{tolerances}

总成绩为通过有效例数／有效例数。输入、参考、配置或判题工具错误属于基础设施错误，不计考生失分；无有效例不产生成绩。校验工具只检查契约，不检查方程是否求对。
'''


def build():
    specs = prepare_specs()
    for slug, s in specs.items():
        directory = CHAPTER / s['section'] / slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'instruction.md').write_text(instruction_text(s), encoding='utf-8')
        (directory / 'DATA.md').write_text(data_text(slug, s), encoding='utf-8')
        policy = dict(version=2, quantities={q: dict(unit=o['unit'], rule=dict(
            metric='pointwise', time='per_time', components='per_component', atol=o['atol'], rtol=o['rtol']))
            for q, o in s['outputs'].items()})
        (directory/'author').mkdir(parents=True,exist_ok=True)
        (directory / 'author/grading-template.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
        judge = dict(timeout_seconds=s['timeout'], max_output_bytes=None,
                     stage='design', verifier_budget=dict(base_seconds=120, per_case_overhead_seconds=15))
        (directory / 'judge-config.json').write_text(json.dumps(judge, indent=2) + '\n', encoding='utf-8')
        harbor = directory / 'harbor'
        harbor.mkdir(exist_ok=True)
        (harbor / 'task.toml').write_text(f"[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = {s['cpus']}\nmemory_mb = {s['memory_mb']}\ngpus = 0\n", encoding='utf-8')
        (harbor / 'requirements.txt').write_text('scipy>=1.17,<2\n', encoding='utf-8')
        (directory / 'README.md').write_text(f"# {s['number']} {s['name']}\n\n[题面](instruction.md)、[输入输出](DATA.md)。本目录完成题面、契约及评分执行配置设计；正式样例、隐藏数据、独立参考与预算／误差校准留后，尚未发布评测。harbor/仅补充本题资源和依赖。\n", encoding='utf-8')
    sections = {}
    for slug, s in specs.items():
        sections.setdefault(s['section'], []).append(f"- [{s['number']} {s['name']}]({slug}/instruction.md)")
    names = ['外场粒子轨道', '碰撞与反应', '静电自洽', '弱电离放电', '冷等离子体电磁响应']
    for (section, entries), name in zip(sections.items(), names):
        (CHAPTER / section / 'README.md').write_text(f"# {section.split('-')[0]} {name}\n\n" + '\n'.join(entries) + '\n', encoding='utf-8')
    (CHAPTER / 'README.md').write_text('# 第十四章 等离子体与带电粒子分析\n\n5节10题；题意及接口由每题instruction、DATA和通用CONTRACT定义。正式数据、参考和评测发布留后。\n\n'
        + '\n'.join(f'- [{key.split("-")[0]} {name}]({key}/README.md)' for key, name in zip(sections, names))
        + '\n\n维护：[章规划](../design/chapter-14-plasma.md)、[逐题清单](../design/chapter-14-task-plan.md)、[进度与证据](../design/reviews/chapter-14-progress.md)。\n', encoding='utf-8')
    public = {slug: {k: v for k, v in cfg.items() if k not in
                      ('number', 'name', 'section', 'physics', 'restrictions', 'scale_limits', 'timeout', 'cpus', 'memory_mb')}
              for slug, cfg in specs.items()}
    public = json.loads(json.dumps(public))
    for cfg in public.values():
        for output_spec in cfg['outputs'].values():
            output_spec.pop('atol')
            output_spec.pop('rtol')
    target = ROOT / 'qbank/extensions/caeoj_ext/plasma/models.json'
    target.write_text(json.dumps(public, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    provider = ROOT / 'qbank/extensions/caeoj_bundle/runtime.json'
    runtime = json.loads(provider.read_text(encoding='utf-8'))
    runtime['extensions']['plasma'] = dict(version=1, requires=[], geometry=True, error_code='E_PLASMA',
        selectors=[{'physics.model': f'plasma-{slug}-v1'} for slug in specs],
        check='caeoj_ext.plasma:check', files=['caeoj_ext/__init__.py',
            'caeoj_ext/plasma/__init__.py', 'caeoj_ext/plasma/models.json'])
    for slug in specs:
        runtime['tasks'][slug] = ['plasma']
    if 'plasma-' not in runtime['model_namespaces']:
        runtime['model_namespaces'].append('plasma-')
    runtime['model_namespace_diagnostics']['plasma-'] = 'E_PLASMA'
    provider.write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return specs


if __name__ == '__main__':
    build()
