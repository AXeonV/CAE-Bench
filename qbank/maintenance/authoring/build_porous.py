"""Expand the porous-media task statements and declarative model catalog.

This is an authoring template, not a case generator, numerical solver or reference.
"""
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[3]
CHAPTER = ROOT / 'qbank/13-porous-media'
SECTIONS = [
    ('13.1-saturated', '饱和单相渗流', ['darcy-steady', 'darcy-transient', 'forchheimer-steady']),
    ('13.2-unsaturated', '非饱和渗流', ['richards-steady', 'richards-transient']),
    ('13.3-multiphase', '不混溶多相渗流', ['immiscible-two-phase', 'compressible-two-phase']),
    ('13.4-fractures', '裂隙与双重介质', ['embedded-fracture', 'dual-continuum']),
    ('13.5-pore-scale', '孔隙尺度流动', ['pore-creeping', 'pore-laminar-transient']),
    ('13.6-transport', '多孔介质输运', ['porous-tracer', 'porous-sorption-decay']),
]


def scalar(unit, meaning, **constraints):
    return dict(unit=unit, meaning=meaning, kind='scalar', shape=[1], **constraints)


def vector(unit, meaning):
    return dict(unit=unit, meaning=meaning, kind='vector', shape=[2])


def tensor(unit, meaning):
    return dict(unit=unit, meaning=meaning, kind='tensor', shape=[2, 2], spd=True)


def parameter(unit, meaning, **constraints):
    return dict(unit=unit, meaning=meaning, **constraints)


NAMES = [
    '各向异性饱和稳态渗流', '饱和介质储集渗流', '惯性阻力稳态渗流',
    '非饱和稳态渗流', '变饱和瞬态渗流', '不可压缩两相渗流', '弱可压缩两相渗流',
    '嵌入裂隙稳态渗流', '双连续体瞬态渗流', '固定孔隙低惯性流动',
    '固定孔隙层流瞬态流动', '饱和多孔介质被动输运', '多孔介质吸附衰减输运',
]
MODELS = {}
for slug, name in zip([s for _, _, items in SECTIONS for s in items], NAMES):
    steady = slug.endswith('steady') or slug in ('embedded-fracture', 'pore-creeping')
    family = ('richards' if slug.startswith('richards') else 'two_phase' if 'two-phase' in slug
              else 'dual' if slug == 'dual-continuum' else 'fracture' if slug == 'embedded-fracture'
              else 'pore' if slug.startswith('pore-') else 'transport' if slug.startswith('porous-')
              else 'darcy')
    cfg = dict(name=name, family=family, steady=steady, parameters={}, records={}, outputs={},
               timeout=300 if slug in ('darcy-steady', 'pore-creeping', 'embedded-fracture')
               else 1200 if slug == 'pore-laminar-transient' else 900)
    ps, records, outputs = cfg['parameters'], cfg['records'], cfg['outputs']
    if not steady:
        ps.update(start_time=parameter('s', '物理初始时刻 t0'),
                  end_time=parameter('s', '结束时刻 tf>t0'))
    if family in ('darcy', 'fracture', 'dual', 'pore'):
        ps.update(density=parameter('kg/m3', '恒定参考密度 ρ', positive=True),
                  viscosity=parameter('Pa.s', '动力黏度 μ', positive=True))
    if family in ('darcy', 'fracture', 'dual', 'two_phase'):
        ps.update(gravity_x=parameter('m/s2', '重力加速度 x 分量 gx'),
                  gravity_y=parameter('m/s2', '重力加速度 y 分量 gy'))
    if family == 'pore':
        ps['pressure_mean'] = parameter('Pa', '仅当全部外边界为速度条件时指定的体域平均压力；存在牵引边界时必须为 0 且不再约束平均压')
    if family == 'two_phase':
        for phase, label in [('w', '润湿相'), ('n', '非润湿相')]:
            ps['density_' + phase] = parameter('kg/m3', label + '参考密度 ρ0', positive=True)
            ps['viscosity_' + phase] = parameter('Pa.s', label + '动力黏度 μ', positive=True)
        if slug == 'compressible-two-phase':
            ps.update(reference_pressure=parameter('Pa', '密度参考绝对压力 pr>0', positive=True),
                      pressure_min=parameter('Pa', '适用绝对压力下界 pmin>0', positive=True),
                      pressure_max=parameter('Pa', '适用绝对压力上界 pmax>pmin', positive=True))
            for phase in ('w', 'n'):
                ps['compressibility_' + phase] = parameter('1/Pa', '该相等温压缩率 c>0', positive=True)

    def rec(op, role, variable, where, data, required=True, static=False):
        records[op] = dict(role=role, variable=variable, where=where, data=data,
                           required=required, static=static)

    def out(q, spec, where='cells', atol=1e-6, rtol=.01):
        outputs[q] = dict(spec, where=where, atol=atol, rtol=rtol)

    permeability = tensor('m2', '全局对称正定本征渗透率 K；特征值位于 [1e-16,1e-6] m2，条件数≤1e6')
    if family in ('darcy', 'fracture'):
        material = dict(permeability=permeability)
        if not steady:
            material['storage'] = scalar('1/Pa', '单位总体积压力储集系数 C>0，已含孔隙体积分数', positive=True)
        if slug == 'forchheimer-steady':
            material['inertial_resistance'] = scalar('1/m', '二次阻力 β≥0', lower=0)
        rec('material', 'material', 'porous_medium', 'cells', material, static=True)
        rec('volume_source', 'source', 'volume', 'cells', dict(value=scalar('1/s', '单位总体积净体积注入 Q；正值注入')))
        rec('pressure', 'boundary', 'pressure', 'nodes', dict(value=scalar('Pa', '给定压力 pD')), required=True)
        rec('normal_flux', 'boundary', 'volume_flux', 'facets', dict(value=scalar('m/s', '向域外 Darcy 体积通量 q·n')), required=False)
        rec('leakance', 'boundary', 'volume_flux', 'facets', dict(
            conductance=scalar('m/(Pa.s)', '边界导通系数 L≥0', lower=0),
            external_pressure=scalar('Pa', '外界压力 pe')), required=False)
        if not steady:
            rec('initial_pressure', 'initial', 'pressure', 'domain', dict(value=scalar('Pa', '初始压力 p0')), static=True)
        out('pressure', scalar('Pa', '压力 p 的单元面积平均'), atol=1.)
        out('darcy_velocity', vector('m/s', '按总体积截面积定义的 Darcy 体积通量 q，不是 q/φ'), atol=1e-8)
        if family == 'fracture':
            rec('fracture_material', 'material', 'fracture', 'fractures', dict(
                aperture=scalar('m', '裂隙等效开度 a>0', positive=True),
                tangential_permeability=scalar('m2', '切向本征渗透率 kf>0', positive=True),
                exchange=scalar('m/(Pa.s)', '单位裂隙长度的净交换导通 α>0；已合并两侧贡献', positive=True)), static=True)
            rec('fracture_source', 'source', 'fracture_volume', 'fractures', dict(value=scalar('m/s', '每单位线长的体积注入 Qf')))
            out('fracture_pressure', scalar('Pa', '裂隙线压 pf 的线段长度平均'), 'fractures', atol=1.)
            out('fracture_discharge', vector('m2/s', '开度积分的全局切向体积通量 qf'), 'fractures', atol=1e-10)
            out('fracture_exchange', scalar('m/s', 'α(pm|Γ−pf) 的线段平均，正值由基质进入裂隙'), 'fractures', atol=1e-9)
    elif family == 'richards':
        material = dict(
            hydraulic_conductivity=tensor('m/s', '饱和水力传导张量 Ks；特征值位于 [1e-12,1e-2] m/s，条件数≤1e6'),
            porosity=scalar('1', '孔隙体积分数 φ，0.05≤φ≤0.8', lower=.05, upper=.8),
            residual_water=scalar('1', '残余体积含水率 θr，0≤θr<φ', lower=0, upper=.8),
            retention_alpha=scalar('1/m', '持水参数 α，0.01≤α≤10', lower=.01, upper=10),
            retention_n=scalar('1', '持水参数 n，1.2≤n≤4', lower=1.2, upper=4))
        if not steady:
            material['saturated_storage'] = scalar('1/m', '饱和区水头储集 Ss>0', positive=True)
        rec('material', 'material', 'unsaturated_medium', 'cells', material, static=True)
        rec('volume_source', 'source', 'water_volume', 'cells', dict(value=scalar('1/s', '单位总体积净水体积注入 Q')))
        rec('head', 'boundary', 'pressure_head', 'nodes', dict(value=scalar('m', '相对恒定气压的压力水头 hD，−100≤hD≤100', lower=-100, upper=100)))
        rec('normal_flux', 'boundary', 'water_flux', 'facets', dict(value=scalar('m/s', '向外 Darcy 水通量')), required=False)
        if not steady:
            rec('initial_head', 'initial', 'pressure_head', 'domain', dict(value=scalar('m', '初始压力水头，−100≤h0≤100', lower=-100, upper=100)), static=True)
        out('pressure_head', scalar('m', '压力水头 h 的单元平均'), atol=1e-3)
        out('water_content', scalar('1', '体积含水率 θ(h) 的单元平均，不含弹性储集量'), atol=1e-4)
        out('darcy_velocity', vector('m/s', 'Darcy 水通量 q 的单元平均'), atol=1e-8)
    elif family == 'two_phase':
        rec('material', 'material', 'two_phase_medium', 'cells', dict(
            permeability=permeability,
            porosity=scalar('1', '孔隙体积分数 φ，0.05≤φ≤0.8', lower=.05, upper=.8),
            residual_w=scalar('1', '润湿相残余孔隙饱和度 Swr≥0', lower=0, upper=.45),
            residual_n=scalar('1', '非润湿相残余孔隙饱和度 Snr≥0；Swr+Snr≤0.8', lower=0, upper=.45),
            capillary_scale=scalar('Pa', '线性毛细响应尺度 pe，1≤pe≤1e6', lower=1, upper=1e6)), static=True)
        rec('phase_source', 'source', 'phase_mass', 'cells', dict(
            wetting=scalar('kg/(m3.s)', '单位总体积润湿相净质量注入 Qw'),
            nonwetting=scalar('kg/(m3.s)', '单位总体积非润湿相净质量注入 Qn')))
        state = dict(wetting_pressure=scalar('Pa', '润湿相压力 pw'),
                     wetting_saturation=scalar('1', '润湿相孔隙饱和度 Sw', lower=0, upper=1))
        rec('phase_state', 'boundary', 'phase_state', 'nodes', state)
        rec('phase_mass_flux', 'boundary', 'phase_mass', 'facets', dict(
            wetting=scalar('kg/(m2.s)', '向外润湿相质量通量 ρw qw·n'),
            nonwetting=scalar('kg/(m2.s)', '向外非润湿相质量通量 ρn qn·n')), required=False)
        rec('initial_state', 'initial', 'phase_state', 'domain', state, static=True)
        out('wetting_pressure', scalar('Pa', 'pw 单元平均'), atol=1.)
        out('wetting_saturation', scalar('1', 'Sw 单元平均'), atol=1e-3)
        for phase in ('wetting', 'nonwetting'):
            out(phase + '_velocity', vector('m/s', '该相相对于总体积截面的 Darcy 通量'), atol=1e-8)
        if slug == 'compressible-two-phase':
            for phase in ('wetting', 'nonwetting'):
                out(phase + '_inventory', scalar('kg/m3', '单位总体积该相质量 φραSα 的平均'), atol=1e-3)
    elif family == 'dual':
        material = dict(exchange=scalar('1/(Pa.s)', '单位总体积交换 α>0，正流向为基质至裂隙连续体', positive=True))
        for phase, label in [('matrix', '基质连续体'), ('fracture', '裂隙连续体')]:
            material[phase + '_permeability'] = tensor('m2', label + '体积折算渗透率 K，已含体积份额')
            material[phase + '_storage'] = scalar('1/Pa', label + '单位总体积压力储集 C>0，已含体积份额', positive=True)
            rec(phase + '_pressure', 'boundary', phase + '_pressure', 'nodes', dict(value=scalar('Pa', label + '给定压力')))
            rec(phase + '_normal_flux', 'boundary', phase + '_volume', 'facets', dict(value=scalar('m/s', label + '向外折算体积通量')), required=False)
            rec('initial_' + phase, 'initial', phase + '_pressure', 'domain', dict(value=scalar('Pa', label + '初压')), static=True)
            out(phase + '_pressure', scalar('Pa', label + '压力平均'), atol=1.)
            out(phase + '_velocity', vector('m/s', label + '体积折算 Darcy 通量平均'), atol=1e-8)
        rec('material', 'material', 'dual_medium', 'cells', material, static=True)
        rec('volume_source', 'source', 'dual_volume', 'cells', dict(
            matrix=scalar('1/s', '基质单位总体积注入'), fracture=scalar('1/s', '裂隙连续体单位总体积注入')))
        out('exchange_rate', scalar('1/s', 'α(pm−pf) 的单元平均，正值基质流向裂隙'), atol=1e-8)
    elif family == 'pore':
        rec('body_force', 'source', 'momentum', 'cells', dict(value=vector('N/m3', '每单位流体体积体力 f，已包含重力')))
        rec('wall', 'boundary', 'velocity', 'facets', dict(motion=dict(option='stationary', meaning='固定无滑移孔壁')))
        rec('velocity', 'boundary', 'velocity', 'nodes', dict(value=vector('m/s', '给定流体速度 uD')), required=False)
        rec('traction', 'boundary', 'traction', 'facets', dict(value=vector('Pa', '全局总牵引 σn，σ=−pI+μ(∇u+∇uᵀ)')), required=False)
        if not steady:
            rec('initial_velocity', 'initial', 'velocity', 'domain', dict(value=vector('m/s', '初始流体速度 u0')), static=True)
        out('pressure', scalar('Pa', '流体机械压力 p 的单元平均'), atol=1.)
        out('pore_velocity', vector('m/s', '孔隙内部真实流体速度 u 的单元平均'), atol=1e-5)
        out('mean_pore_velocity', vector('m/s', '流体区域面积平均 ∫Ωu dA/|Ω|，不是总体积表观速度'), 'mean', atol=1e-5)
    else:
        material = dict(porosity=scalar('1', '孔隙体积分数 φ，0.05≤φ≤0.8', lower=.05, upper=.8),
                        molecular_diffusivity=scalar('m2/s', '孔隙有效分子扩散 Dm>0，已含曲折度修正', positive=True),
                        longitudinal_dispersivity=scalar('m', '纵向弥散度 aL≥aT≥0', lower=0),
                        transverse_dispersivity=scalar('m', '横向弥散度 aT≥0', lower=0))
        if slug == 'porous-sorption-decay':
            material.update(solid_density=scalar('kg/m3', '固体颗粒真密度 ρs>0，不是干容重', positive=True),
                            distribution_coefficient=scalar('m3/kg', '线性平衡吸附系数 Kd≥0', lower=0),
                            dissolved_decay=scalar('1/s', '溶解相衰减常数 λw≥0', lower=0),
                            sorbed_decay=scalar('1/s', '吸附相衰减常数 λs≥0', lower=0))
        rec('material', 'material', 'transport_medium', 'cells', material, static=True)
        rec('given_flux', 'source', 'darcy_velocity', 'domain', dict(value=vector('m/s', '给定稳态 Darcy 通量 q，不是孔隙流速')), static=True)
        rec('solute_source', 'source', 'solute_mass', 'cells', dict(value=scalar('kg/(m3.s)', '单位总体积溶质净质量注入 Q')))
        rec('initial_concentration', 'initial', 'concentration', 'domain', dict(value=scalar('kg/m3', '初始水相浓度 c0≥0', lower=0)), static=True)
        rec('concentration', 'boundary', 'concentration', 'nodes', dict(value=scalar('kg/m3', '给定水相浓度 cD≥0', lower=0)), required=False)
        rec('diffusive_flux', 'boundary', 'solute_diffusion', 'facets', dict(value=scalar('kg/(m2.s)', '向外扩散／弥散质量通量 (−φD∇c)·n，不含平流')), required=False)
        out('concentration', scalar('kg/m3', '水相浓度 c 的单元平均'), atol=1e-5)
        out('solute_flux', vector('kg/(m2.s)', '总溶质通量 qc−φD∇c 的单元平均'), atol=1e-9)
        out('stored_mass', scalar('kg/m3', '单位总体积总溶质存量的平均'), atol=1e-5)
        if slug == 'porous-sorption-decay':
            out('sorbed_mass', scalar('kg/m3', '单位总体积固相吸附质量的平均'), atol=1e-5)
    MODELS[slug] = cfg

PHYSICS = {
    'darcy-steady': '单相饱和、等温、固定骨架。水量按总体积守恒；压力驱动、重力和黏性阻力共同确定通量。材料本征渗透率 K 与黏度满足 q=−K(∇p−ρg)/μ。p 是相对固定共同零点的机械压力，不是水头；不另乘孔隙率。源 Q 正值向域内注入体积。无储集或物理初态。',
    'darcy-transient': '单相饱和、等温、固定骨架，采用线性压力储集近似。单位总体积储量相对于任意固定基准的变化为 C(p−p基准)，C 已包含孔隙份额，不再乘密度或孔隙率。流动使用恒定参考密度，q=−K(∇p−ρg)/μ；储集变化与体积通量散度共同平衡体积注入 Q。给定物理初压，不指定内部时间积分方案。',
    'forchheimer-steady': '单相饱和、等温、固定骨架，保留宏观惯性阻力而不解析孔隙。局部阻力为 μK⁻¹q+ρβ|q|q，与驱动力 ρg−∇p 平衡。β 是各向同性二次阻力系数，|q| 为全局欧氏模；线性项仍使用完整 K。按总体积守恒体积，Q 为净注入。β=0 明确退化到 Darcy 响应，不另加 Brinkman 剪切或自由流对流项。',
    'richards-steady': '气相恒压且不运动，水不发生蒸发或相变，忽略动量惯性。y 轴向上，压力水头 h 是水压减气压后除以恒定水重度，不是总水头；总水头为 h+y。q=−Ks kr(h)∇(h+y)。设 m=1−1/n；h<0 时 Se=[1+(α|h|)^n]^(−m)，h≥0 时 Se=1；θ=θr+(φ−θr)Se，kr=Se^(1/2)[1−(1−Se^(1/m))^m]^2。Ks 是饱和水力传导率而非 m2 的本征渗透率。稳态按水体积守恒平衡 Q；不引入滞回、大气交换或未声明的蒸散。',
    'richards-transient': '气相恒压且不运动、等温、固定骨架，无相变。y 轴向上，h 为相对气压的压力水头，总水头 h+y。q=−Ks kr(h)∇(h+y)。m=1−1/n；h<0 时 Se=[1+(α|h|)^n]^(−m)，h≥0 时 Se=1；θ=θr+(φ−θr)Se，kr=Se^(1/2)[1−(1−Se^(1/m))^m]^2。单位总体积储水响应为 W(h)=θ(h)+Ss max(h,0)，水量变化与体积流出共同平衡 Q；Ss 仅在饱和区给出额外线性储集。不把 W 当输出含水率，water_content 只表示 θ。不引入滞回或空气压力未知量。',
    'immiscible-two-phase': '固定骨架中两种不可压缩、等温、不混溶流体，无相变或质量交换。w 为润湿相、n 为非润湿相，Sw+Sn=1，饱和度相对孔隙体积。令 Se=(Sw−Swr)/(1−Swr−Snr)，pc=pn−pw=pe(1−Se)，krw=Se²，krn=(1−Se)²；qα=−K krα(∇pα−ραg)/μα。两相分别按质量守恒，单位总体积质量为 φραSα，phase_source 给真实质量注入。所有物理解及初边值满足 1e−4≤Se≤1−1e−4；材料可逐单元变化，界面以两相压力连续及各相法向质量通量连续解释，Sw 可随毛细材料跳变。不将压力、饱和度或通量重新归一化。',
    'compressible-two-phase': '固定骨架、等温、两种不混溶弱可压缩流体，无相变、组分溶解或孔隙率变化。w 为润湿相，Sw+Sn=1；Se=(Sw−Swr)/(1−Swr−Snr)，pc=pn−pw=pe(1−Se)，krw=Se²，krn=(1−Se)²。两相压力是绝对压力；ρα(pα)=ρ0α exp[cα(pα−pr)]，qα=−K krα(∇pα−ρα(pα)g)/μα。各相守恒质量 φρα(pα)Sα，不能将密度只放入重力而忽略储集和质量输运。所有物理解中 pmin≤pw,pn≤pmax，1e−4≤Se≤1−1e−4，且参考压力在该区间、指数绝对值≤20。材料界面两相压力和法向质量通量连续；均值库存必须平均非线性乘积。',
    'embedded-fracture': '固定骨架单相饱和稳态渗流。二维基质的 p、q 使用 q=−K(∇p−ρg)/μ。内部嵌入线 Γ 有独立线压 pf；基质压力在 Γ 两侧连续，法向流量允许因交换而跳变。裂隙开度积分切向流为 qf=−a kf(∂s pf−ρ g·τ)τ/μ（全局矢量），净基质至裂隙交换 e=α(pm|Γ−pf)；α 已合并两侧，不再乘 2。每单位线长裂隙守恒为 divΓ qf=Qf+e，基质以同量 e 作为线分布体积损失。a 只乘裂隙切向通量，不再乘源或交换。线端均封闭；内部折点线压连续、切向流守恒，无交叉、分叉或边界出口。本题是压力连续基质的有限交换嵌入线模型，不是切开基质的双侧压力跳跃模型。',
    'dual-continuum': '一个固定二维区域中有基质 m、裂隙 f 两个重叠连续体，使用同一参考几何而有独立压力。K_m、K_f 与 C_m、C_f 均按单位总体积折算，不能各再乘体积份额或把总体积算两次。q_i=−K_i(∇p_i−ρg)/μ，储量变化为 C_i dp_i；e=α(pm−pf) 正值基质流入裂隙。基质净源为 Qm−e，裂隙净源为 Qf+e，二者交换严格相反。边界条件与初态按每个连续体独立读取，不以单一等效压代替两个状态。',
    'pore-creeping': '网格显式描述连通的流体孔隙，不含实体固体单元；wall 指定固定孔壁，无滑移。单相、不可压缩、牛顿、等温，忽略全部流动惯性；μ 为动力黏度，体力 f 已包含重力。总应力 σ=−pI+μ(∇u+∇uᵀ)，不以 μ∇u 代替黏性牵引。速度是孔隙内真实速度；mean_pore_velocity 为流体区域面积平均，不是 Darcy 速度或整个固液区域平均。没有牵引边界时用全流体域平均 p=pressure_mean 固定压零点；有牵引时压力由牵引决定，不再施加均值约束。',
    'pore-laminar-transient': '网格显式给出固定连通流体孔隙，wall 为固定无滑移孔壁。单相、不可压缩、牛顿、等温层流，保留局部加速度和速度对流惯性；无湍流闭合。总应力 σ=−pI+μ(∇u+∇uᵀ)，体力 f 已含重力；初态给真实流体速度，不是迭代初猜。没有牵引边界时每时刻用全域平均 p=pressure_mean 定压零点；存在牵引时不加均值。mean_pore_velocity 仅对流体面积平均，不乘未知孔隙率。数据保证在给定时间内有唯一足够正则的层流响应。',
    'porous-tracer': '固定饱和介质中单一被动溶质，水相不可压缩，流动不受浓度反馈。given_flux 给 q：节点 P1 重建、单元内无散且跨面连续的稳态 Darcy 通量；孔隙速度 v=q/φ。D=Dm I+aT|v|I+(aL−aT)vvᵀ/|v|，v=0 时 D=Dm I；Dm 已包含曲折度。c 是单位水体积溶质质量，单位总体积存量 M=φc，总通量 J=qc−φD∇c，体积源 Q 按总体积注入。材料界面 c 连续、总法向质量通量连续，允许 φ 与 D 跳变。给定全部入流浓度，出流扩散与平流的边界含义按 DATA 条件表；不再求压力或速度。',
    'porous-sorption-decay': '固定饱和介质，给定无散稳态 Darcy 通量 q，v=q/φ；D=Dm I+aT|v|I+(aL−aT)vvᵀ/|v|，v=0 时取 Dm I。c 是水相浓度；每单位固体质量平衡吸附量 s=Kd c，颗粒真密度 ρs，因此单位总体积吸附存量 Ms=(1−φ)ρsKd c，总存量 M=φc+Ms。总通量 J=qc−φD∇c；净质量损失为 λwφc+λsMs，源 Q 仍按总体积。吸附瞬时平衡、线性且固相不运动；初始吸附量由 c0 唯一确定，不另给独立初态。界面 c 与总法向通量连续，不含有限速率吸附或一般化学网络。',
}


def describe(spec):
    if 'option' in spec:
        return '`{"option":"' + spec['option'] + '"}`；' + spec['meaning']
    return f"{spec['kind']}，component_shape={spec['shape']}，unit=`{spec['unit']}`；{spec['meaning']}"


def render(slug, section, number):
    c = MODELS[slug]
    axis = 'steady' if c['steady'] else 'response'
    threshold = '\n'.join(f"| `{q}` | `{s['unit']}` | {s['atol']:g} | {s['rtol']:g} |" for q, s in c['outputs'].items())
    instruction = f'''# {number} {c['name']}

编写一个可复用求解程序，处理输入所描述的{c['name']}问题族。域、材料、载荷与初边值由输入给定。

## 分析要求

{PHYSICS[slug]}

采用二维平面固定参考域，按单位厚度解释体积守恒与流量。骨架固定且等温，无未声明的相变、力学变形或热反馈。材料关系是输入物理事实；语言、软件、数值离散、内部网格及收敛策略自行选择。输入参考网格只定义材料、边界和观测，不强制数值方法。{'稳态不进行物理时间推进。' if c['steady'] else '固定或自适应时间步、稳定性控制及每步非线性迭代自行选择；必须输出给定请求时刻，不能将输出间隔当固定内部步长。'}

## 输入与输出

输入为 problem.json 及其引用的 Gmsh 网格与 HDF5 数组。字段与条件见 [DATA.md](DATA.md)，通用格式见 [通用数据协议](../../../../docs/CONTRACT.md)。按 outputs 声明输出全部物理量及原有 IDs／时间轴到一个 result.h5，不添加其他 dataset。

程序入口：`python /app/submission/solve.py --input <problem.json> --output <result.h5>`。solve.py 可以启动自行编写的其他语言程序；逐例时间包含启动、编译及程序自身 I/O。

## 输入范围与资源

- 非退化、无悬挂节点的平面一阶三角网格；至多 6000 三角形、8000 节点，坐标绝对值≤1e6 m；最长边／最短高≤100。具体连通与边界规则见 DATA。
- 每轴至多 101 个时刻，全部输入场与输出场各自的浮点标量总数≤5e6。瞬态时间跨度在 (0,1e8] s 内。
- 标量参数及场取 DATA 中给定范围；未额外指定范围的物理数值绝对值≤1e12，且有限。数据保证所述物理响应存在、唯一，并满足本题适用范围。
- 每例 {c['timeout']} s、4 逻辑 CPU、4096 MB。内部线程与 MPI 进程数在该 CPU 配额内自行选择。

## 评分

每个测试点 1 分。所有输出浮点分量均须满足 `|计算值−比较值|≤atol+rtol·|比较值|`，包含等号；全部字段、时刻、单元及分量通过才得分。整数／布尔量、IDs、时间轴按通用协议精确一致，不拟合压力偏移，不对输出重排。

| quantity | unit | atol | rtol |
|---|---|---:|---:|
{threshold}

程序失败、超时、缺输出或输出格式不合法，该测试点不得分。
'''
    data = f'''# {c['name']}的数据约定

本题使用[通用数据协议](../../../../docs/CONTRACT.md)，以下定义本题的全部专用语义。task 为 `{slug}`（可以省略，由单题工具包确定）；spatial_dimension 必须为整数 2。只使用 `physics` 形式，不同时提供 profile、analysis、materials 或 contract_version。

## 文件、网格与位置

data_file 指向单个扁平 HDF5 文件；文件名与 HDF5 key 不携带物理含义。meshes 恰含 main，指向 Gmsh MSH 4.1 ASCII 的平面三角网格，z=0。geometries 可为空或按协议引用文件，不要求运行几何脚本。

三角形 type 2 描述参考域，线段 type 1 导出全部外边界，每条外边界恰好一次；不导出点单元。三角形沿边连通，共享节点 tag 的内部边表示相邻连续材料，不是边界。没有未使用节点、重复几何三角形、非流形或悬挂节点。

locations.domain 为全部三角形节点：kind=mesh、mesh=main、entity=node。locations.cells 为全部三角形：entity=element、dimension=2。二者均完整覆盖，ids 引用严格递增 int64 tag。其他条件位置为同网格节点子集或线段子集；边界线段位置 dimension=1，节点位置不写 dimension。Physical Group 如果声明必须与 IDs 精确一致，不按组名判断条件。

节点边界位置表示所有顶点都在该节点集中的完整外边界线段；节点集必须正好等于这些线段的端点并，不允许孤立节点。面／边条件在相应线段上分片常数。外法向由唯一相邻三角形指向域外，与线段 tag、节点存储顺序无关。
'''
    if c['family'] == 'fracture':
        data += '''
本题另有 locations.fractures，kind=mesh、mesh=main、entity=element、dimension=1，包含全部裂隙线段。它们是额外导出的三角形内部共享边，使用基质原节点，不切开基质。几何线段无重复，内部节点度≤2，端点全部严格在域内；各条开曲线不自交、不闭合、不分叉，线端封闭。除外边界与 fractures 外，不导出其他线段。pf、线源和线材料均按 fracture ID 对应；线压在折点连续、流量守恒。基质压力迹从共享两侧的同一连续压力读取。
'''
    else:
        data += '\n本题只导出三角形与外边界线段，不允许内部线段或其他单元类型。\n'
    if c['family'] == 'pore':
        data += '''
网格只覆盖流体孔隙，可以有固体孔壁围成的孔洞。locations.mean 是唯一 aggregate：source=cells、operation=mean，ids 为含一个非负 int64 ID 的数组。它用于流体域面积平均，不能替换为空间探针；其余位置不使用 aggregate、points 或 entities。
'''
    else:
        data += '\n不使用 points、entities、aggregate 或其他网格位置。\n'
    data += f'''
## 物理声明与参数

physics.model 必须为 `porous-{slug}-v1`，parameters 恰含下表全部键。每项为 `{{"value":有限数值,"unit":"表中代码"}}`，不得写成数组或场引用。

| parameters 键 | unit | 含义与范围 |
|---|---|---|
'''
    data += '\n'.join(f"| `{k}` | `{s['unit']}` | {s['meaning']} |" for k, s in c['parameters'].items()) + '\n'
    if not c['parameters']:
        data += '\n本题 parameters 为 `{}`，没有全局标量参数。\n'
    data += f'''
## 物理响应

{PHYSICS[slug]}

## 时间、字段与连续含义

'''
    if c['steady']:
        data += 'time_axes 恰含 steady，其 HDF5 数组为 float64[1] 的 [0.0]。所有输入与输出引用 steady，不提供初态或多帧。\n'
    else:
        data += 'time_axes 必含 initial=[t0]、response（1..101 个严格递增请求时刻，位于 [t0,tf]）。材料、初态及标明 static 的记录只引用 initial。变化载荷可另引用加载轴，该轴至少两帧且端点恰为 t0、tf；单帧载荷必须引用 initial 并在全过程恒定。全部轴均须被字段或输出使用。response 不表示内部时间步；只输出声明时刻，不额外输出 t0 或迭代历史。\n'
    data += '''
fields 的逻辑名与 array key 可任意取协议允许的唯一名称，条件引用逻辑名，HDF5 使用 array key。所有数值场 dtype=float64。scalar 为 [T,N,1]、component_shape=[1]、components=["value"]；vector 为 [T,N,2]、[2]、["x","y"]；tensor 为 [T,N,2,2]、[2,2]、["xx","xy","yx","yy"]。不使用 Voigt、局部坐标或省略轴。

节点场 value_kind=point、sampling.space=piecewise_linear，按参考三角形重心坐标作 P1 重建；边界节点按线段线性重建。材料、源及线段场 value_kind=average、space=piecewise_constant，给定均值同时定义整个实体上的常值。材料在时间上恒定；单帧 sampling.time=constant，多帧为 linear（分量逐段线性），extrapolation=forbid。初态按同样空间规则定义，不能当迭代初猜；传输中的非线性响应在重建后计算，不对响应直接插值。

每个字段 quantity 必须等于下表对应的 data 键；键为 value 时 quantity 等于条件 variable。字段 location 必须与条件 location 相同，unit、kind、分量由下表固定。只允许被条件引用的 fields；引用同一字段可复用，但不隐式广播或匹配不同位置。标量数据可取同单位的 {"value":数值,"unit":"代码"} 常量或 {"field":"字段逻辑名"}；矢量、张量只能引用 HDF5 场。常量表示在该条件位置和全过程均匀。

## 全部条件

每条记录恰含 role、variable、location、operator、data。下表列出全部算子和 data 键；必需记录不得省略。材料／源／初态在其全支撑上各恰有一条记录，不能用顺序叠加或省略源来表示零源。边界记录可有多条，以同一未知变量为组不允许覆盖同一完整外边界线段；节点条件之间也不共享节点，同一节点位置可由一条记录包含多个边界分段。
'''
    for op, r in c['records'].items():
        where = {'cells': 'cells（全部三角形）', 'domain': 'domain（全部域节点）', 'nodes': '完整外边界节点子集',
                 'facets': '外边界线段子集', 'fractures': 'fractures（全部裂隙线段）'}[r['where']]
        data += f"\n### {op}\n\nrole=`{r['role']}`，variable=`{r['variable']}`，location={where}；{'必需' if r['required'] else '可选'}。{'仅使用静态初始轴。' if r['static'] and not c['steady'] else '支持上述时间表示。'}data 恰含：\n\n| data 键 | 表示与含义 |\n|---|---|\n"
        data += '\n'.join(f"| `{k}` | {describe(s)} |" for k, s in r['data'].items()) + '\n'
    if c['family'] in ('darcy', 'fracture'):
        data += '\npressure 必须至少覆盖一条正长度外边界以确定压力。normal_flux 指定 q·n；leakance 指定 q·n=L(p−pe)。未覆盖外边界取 q·n=0。pressure、normal_flux、leakance 不在同一完整边上叠加。材料界面压力和法向体积通量连续，裂隙交换处按本题物理响应例外。\n'
    elif c['family'] == 'richards':
        data += '\nhead 至少覆盖一条外边界以固定压力水头；未覆盖处向外水通量为零。head 与 normal_flux 不覆盖同一完整边。材料界面水压力水头与法向水通量连续；持水关系可跳变，θ 不要求跨界面连续。所有初边值及物理解均位于 h∈[−100,100] m。\n'
    elif c['family'] == 'two_phase':
        data += '\nphase_state 至少覆盖一条外边界，同处指定 pw、Sw，pn 由毛细关系确定；不可另加 phase_mass_flux。phase_mass_flux 给各相质量通量，不能除以恒定参考密度后当体积通量使用。未覆盖边界两相均无穿透。初态／给定状态在各相邻材料上须满足上述 Se 范围和界面相容性；节点饱和度 P1 只定义输入初态／状态数据，不强迫未知饱和度在毛细材料跳变处连续。\n'
    elif c['family'] == 'dual':
        data += '\n每个连续体都至少有一条自身的 pressure 外边界；其余未覆盖边对该连续体 normal_flux=0。同一几何边可分别给基质和裂隙连续体条件，它们属于不同未知量，不算重叠；同一连续体的压力与通量不能在完整边上叠加。两套初压都必需。\n'
    elif c['family'] == 'pore':
        data += '\nwall 至少覆盖一条孔壁边，motion 只能是 {"option":"stationary"}，表示 u=0，不是数值标量。wall、velocity、traction 必须互斥并完整覆盖全部外边界；wall 与 velocity 均视为速度约束，velocity 数据在与 wall 相接节点处必须为零。仅速度边界时数据保证净体积流入为零；瞬态初速度无散且与 t0 边界相容。牵引指定黏性与压力的总作用，不能误作仅法向压力。牵引边界上的速度符号不预设，数据保证在所述预算和区间有唯一层流解。\n'
    else:
        data += '\nconcentration 必须覆盖每条存在 q·n<0 的完整入流边；各边 q·n 不变号，允许全零。diffusive_flux 仅指定 (−φD∇c)·n，不是包含平流的总通量；只用于非入流边，不能与 concentration 叠加。未覆盖边界扩散通量为零，出流平流仍以域内浓度携出；全零法向速度边为无平流边。数据保证初边值／源所确定的浓度非负。给定 q 在全域静态、节点 P1 重建，每个三角形内散度为零；材料跳变不改变 q 的身份或将其除以孔隙率后重新守恒。\n'
    data += f'''
## 输出

outputs 必须恰好请求下表各 quantity，每种恰好一次，逻辑名与 array key 不固定。全部输出 dtype=float64、time_axis={axis}，kind、component_shape、components 按上面的统一分量表。cells 上 value_kind=average 表示三角形面积平均；fractures 上 average 为线长平均，mean 上 average 为整个流体域面积平均。非线性量先由连续状态计算再积分，不能用平均状态代入非线性关系。所有量保留其物理压力基准和符号。

| quantity | location | kind／shape | unit | 含义 |
|---|---|---|---|---|
'''
    for q, s in c['outputs'].items():
        location = 'mean' if s['where'] == 'mean' else s['where']
        data += f"| `{q}` | `{location}` | {s['kind']}／{s['shape']} | `{s['unit']}` | {s['meaning']} |\n"
    data += '\nresult.h5 仅包含上述 outputs.array 及这些输出引用的位置 IDs 和时间轴。共享 key 只写一次，不复制坐标、输入材料或网格。可用 `caeoj.sdk.load_problem`、`read_field`、`write_result` 辅助读写，也可直接使用 JSON、Gmsh、HDF5 库；结构工具不求解或修正物理结果。\n'
    return instruction, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sections', nargs='*', help='Section prefixes, e.g. 13.1 13.2; default all')
    args = parser.parse_args()
    selected = set(args.sections or [s.split('-')[0] for s, _, _ in SECTIONS])
    valid = {s.split('-')[0] for s, _, _ in SECTIONS}
    if not selected <= valid:
        parser.error('Unknown section')
    for section, title, slugs in SECTIONS:
        if section.split('-')[0] not in selected:
            continue
        base = CHAPTER / section
        base.mkdir(parents=True, exist_ok=True)
        entries = []
        for index, slug in enumerate(slugs, 1):
            number = section.split('-')[0] + '.' + str(index)
            cfg = MODELS[slug]
            directory = base / slug
            directory.mkdir(exist_ok=True)
            instruction, data = render(slug, section, number)
            for name, text in [('instruction.md', instruction), ('DATA.md', data)]:
                (directory / name).write_text(text, encoding='utf-8')
            policy = dict(version=2, quantities={q: dict(unit=s['unit'], rule=dict(
                metric='pointwise', time='per_time', components='per_component',
                atol=s['atol'], rtol=s['rtol'])) for q, s in cfg['outputs'].items()})
            config = dict(timeout_seconds=cfg['timeout'], max_output_bytes=None, stage='provisional',
                          verifier_budget=dict(base_seconds=300, per_case_overhead_seconds=60))
            for name, value in [('grading.json', policy), ('judge-config.json', config)]:
                (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            harbor = directory / 'harbor'
            harbor.mkdir(exist_ok=True)
            (harbor / 'task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\ncpus = 4\nmemory_mb = 4096\nbuild_timeout_sec = 1800.0\n', encoding='utf-8')
            (directory / 'README.md').write_text(f'# {cfg["name"]}\n\n[题面](instruction.md)、[数据约定](DATA.md)。\n\n当前已完成题面与配置设计；正式样例、隐藏数据、参考、误差及资源校准留待数据阶段。配置验证见仓库 tests/test_porous_contract.py，临时 fixture 不属于题库数据。\n', encoding='utf-8')
            entries.append(f'- {number} [{cfg["name"]}]({slug}/instruction.md)')
        (base / 'README.md').write_text(f'# {section.split("-")[0]} {title}\n\n' + '\n'.join(entries) + '\n', encoding='utf-8')
    toc = ['# 第十三章 多孔介质与渗流分析', '', '固定骨架二维渗流、孔隙尺度流动与输运；题目按能力划分，具体几何和工况属于算例。', '']
    for section, title, slugs in SECTIONS:
        toc.append(f'- [{section.split("-")[0]} {title}]({section}/README.md)：{len(slugs)} 题')
    toc += ['', '整章六节十三题的题面、契约和配置按阶段实施；正式数据、参考及发布另行建设。',
            '', '维护方入口：[章规划](../design/chapter-13-porous-media.md)、[逐题清单](../design/chapter-13-task-plan.md)、[进度与验证](../design/reviews/chapter-13-progress.md)。']
    CHAPTER.mkdir(exist_ok=True)
    (CHAPTER / 'README.md').write_text('\n'.join(toc) + '\n', encoding='utf-8')
    ext = ROOT / 'qbank/extensions/caeoj_ext/porous'
    ext.mkdir(parents=True, exist_ok=True)
    (ext / 'models.json').write_text(json.dumps(MODELS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
