"""Expand independent material-evolution contracts; never generate case data."""
from pathlib import Path
from caeoj_tools.author import public_model_catalog
import json

ROOT = Path(__file__).resolve().parents[3]
CH = ROOT/'qbank/16-microstructure'
SECTIONS = [
    ('16.1-separation','守恒相分离',['binary-separation','ternary-separation']),
    ('16.2-ordering','非守恒有序化',['order-relaxation','driven-ordering']),
    ('16.3-grains','多取向晶粒长大',['grain-coarsening']),
    ('16.4-precipitation','析出与组织耦合',['coupled-precipitation']),
    ('16.5-crystal','晶体尺度密度组织',['crystal-density']),
]


def p(unit, meaning, **kw):
    return dict(unit=unit,meaning=meaning,**kw)


def s(unit, meaning, shape=None):
    return dict(unit=unit,meaning=meaning,shape=shape or [1],kind='components' if shape else 'scalar')


PHYS = {
'binary-separation': 'c为相对于参考成分缩放的无量纲成分偏差，可为负，不是原子数密度。体自由能密度f=A(c²−1)²/4，梯度能κ|∇c|²/2，化学势μ=A(c³−c)−κΔc，单位J/m3。动力学∂t c=∇·[M0(1+αc²)∇μ]，M0>0、α≥0。必须保留变量迁移率在散度内，不把它错误移到Δμ前，也不在每步重新投影均值。无对流、反应或热噪声，周期封闭系统保持c的空间均值。给定非线性多项式响应不裁剪c，演化中不强制c∈[−1,1]。',
'ternary-separation': 'c1、c2为两独立无量纲成分，c3=1−c1−c2。体能f=AΣ_{i=1}^3 c_i²(1−c_i)²/4，梯度能κΣ_i|∇c_i|²/2；约束变分给μ_i=A[c_i(1−c_i)(1−2c_i)−c3(1−c3)(1−2c3)]/2−κΔ(c_i−c3)，i=1,2，单位J/m3。常量对称正定迁移率矩阵M按∂t c_i=Σ_{j=1}^2 M_ij Δμ_j演化；M第一轴为响应成分i、第二轴为驱动力j，允许负交叉项但整体SPD。初态在三元单纯形内；多项式模型演化不另作非负裁剪、单纯形投影或独立二元近似。两独立成分的空间均值各自守恒；无反应、弹性或对流。',
'order-relaxation': 'η为无量纲有序度，两个变体对应±1。体能f=A(η²−1)²/4，梯度能κ|∇η|²/2，热力学驱动力h=A(η³−η)−κΔη，单位J/m3。非守恒动力学∂tη=−Lh，L>0；不约束空间均值，不把它改为守恒扩散或每步归一化。无外驱、噪声、形核规则或热反馈，模型不对η作裁剪。',
'driven-ordering': 'η为无量纲有序度，变体对应±1。给定外部均匀偏置b(t)，体能f=A(η²−1)²/4−b(t)η、梯度能κ|∇η|²/2，h=A(η³−η)−κΔη−b(t)，单位J/m3，∂tη=−Lh。b是能量密度偏置，不是温度，不从热学或其他库推断响应；外场无反馈。b按控制结点连续分段线性插值，仅输出requests时刻，控制结点不增加输出帧。均值不守恒，不裁剪η，不以准静态能量极小值序列代替瞬态。',
'grain-coarsening': 'K个固定取向标签η_i，各标签是连续无量纲序参量而非互斥分类。体能f=A[Σ_i(η_i^4/4−η_i²/2)+(γ/2)Σ_{i<j}η_i²η_j²]，梯度能κΣ_i|∇η_i|²/2。h_i=A[η_i³−η_i+γ η_i Σ_{j≠i}η_j²]−κΔη_i，∂tη_i=−L h_i。γ>1，界面系数和迁移率各向同性且各标签相同。无Ση_i=1约束、Lagrange乘子或裁剪，不作阈值化标签替换。取向分量按输入固定顺序输出，即使晶粒消失也保留该分量，禁止按面积重新命名或置换。无形核、弹性、存储变形能或随机驱动。',
'coupled-precipitation': 'c为无量纲成分偏差，η为无量纲有序度，均可取有符号值。体能f=A(η²−1)²/4+B(c−c_ref−δ η)²/2，梯度能κc|∇c|²/2+κη|∇η|²/2。μc=B(c−c_ref−δ η)−κcΔc，hη=A(η³−η)−Bδ(c−c_ref−δ η)−κηΔη，单位J/m3。联合动力学∂t c=MΔμc、∂tη=−Lhη。c的空间均值守恒，η不守恒；两式同时反馈，不能先独立演化再拼接。δ>0定义正η偏好更高c，无额外相图、自屏蔽、热反馈或弹性。多项式模型不裁剪c或η，不按局部平衡关系消去一个状态。',
'crystal-density': 'n为相对参考密度的无量纲偏差，可为负，不是非负原子数。体能泛函密度约定为A[r n²/2+n^4/4+n(1+ell²Δ)²n/2]；泛函在周期矩形上积分，(1+ell²Δ)为自伴算子。化学势μ=A[r n+n³+(1+ell²Δ)²n]=A[(r+1)n+n³+2ell²Δn+ell^4Δ²n]，单位J/m3；∂t n=MΔμ，M>0。这是总六阶守恒密度演化，不用二阶扩散替代，不将(1+ell²Δ)²误作1+ell^4Δ²。所有阶空间导数周期匹配，均值守恒；无原子势拟合、速度惯性、噪声或密度裁剪。',
}

MODELS = {}
for sec,title,slugs in SECTIONS:
    for slug in slugs:
        size = 'k' if slug=='grain-coarsening' else 2 if slug in ('ternary-separation','coupled-precipitation') else 1
        c = dict(name={'binary-separation':'非线性迁移率二元相分离','ternary-separation':'三元约束相分离与交叉迁移','order-relaxation':'非守恒有序度弛豫','driven-ordering':'外场历史驱动有序化','grain-coarsening':'多取向晶粒竞争长大','coupled-precipitation':'成分与有序度耦合析出','crystal-density':'晶体尺度守恒密度演化'}[slug],
            state_size=size,parameters={},records={},outputs={},
            timeout={'binary-separation':900,'ternary-separation':1200,'order-relaxation':300,'driven-ordering':450,'grain-coarsening':1200,'coupled-precipitation':1200,'crystal-density':1800}[slug])
        MODELS[slug] = c
        c['parameters'] = {'length_x':p('m','周期长度Lx>0',positive=True), 'length_y':p('m','周期长度Ly>0',positive=True), 'energy_scale':p('J/m3','自由能系数A>0',positive=True)}
        if slug != 'crystal-density':
            if slug=='coupled-precipitation':
                c['parameters'].update(gradient_c=p('J/m','κc>0',positive=True),gradient_eta=p('J/m','κη>0',positive=True))
            else:
                c['parameters']['gradient'] = p('J/m','梯度能系数κ>0',positive=True)
        if slug in ('binary-separation','coupled-precipitation','crystal-density'):
            c['parameters']['mobility'] = p('m5/(J.s)',('M0' if slug=='binary-separation' else 'M')+'>0，按本题守恒动力学定义',positive=True)
        if slug in ('order-relaxation','driven-ordering','grain-coarsening','coupled-precipitation'):
            c['parameters']['relaxation'] = p('m3/(J.s)','非守恒迁移率L>0',positive=True)
        if slug=='binary-separation':
            c['parameters']['mobility_contrast'] = p('1','非线性迁移率系数α≥0，允许0',lower=0)
        if slug=='grain-coarsening':
            c['parameters'].update(grain_count=p('1','取向数K，JSON整数2..6，状态分量顺序为η1..ηK',integer=True,lower=2,upper=6), competition=p('1','竞争系数γ>1',lower_exclusive=1))
        if slug=='coupled-precipitation':
            c['parameters'].update(coupling_energy=p('J/m3','偏聚能系数B>0',positive=True), reference=p('1','参考成分偏差c_ref'), partition=p('1','δ>0',positive=True))
        if slug=='crystal-density':
            c['parameters'].update(length_scale=p('m','ell>0，确定晶体尺度',positive=True),undercooling=p('1','约化二次能系数r，有限实数，不是Kelvin温度'))
        c['state_order'] = {'binary-separation':'[c]','ternary-separation':'[c1,c2]（c3从约束确定，不另输入）','order-relaxation':'[η]','driven-ordering':'[η]','grain-coarsening':'[η1,…,ηK]，标签固定','coupled-precipitation':'[c,η]','crystal-density':'[n]'}[slug]
        c['records'] = {
            'offset':dict(role='initial',variable='state_offset',location='system',axis='static',data={'value':s('1','初态各分量空间均值m_a，顺序'+c['state_order'],['s'])}),
            'series':dict(role='initial',variable='initial_series',location='modes',axis='static',data={'wave':s('1','整数波矢(kx,ky)，由float64精确整数存储，不是物理波数', [2]), 'amplitude':s('1','每状态的cos／sin系数，shape=[s,2]最内层依次a、b', ['s',2])})
        }
        if slug=='ternary-separation':
            c['records']['mobility'] = dict(role='material',variable='mobility',location='system',axis='static',data={'value':s('m5/(J.s)','完整2×2迁移率矩阵M，精确对称且正定，含全部非对角项',[2,2])})
        if slug=='driven-ordering':
            c['records']['history'] = dict(role='source',variable='bias',location='system',axis='control',data={'value':s('J/m3','外部均匀偏置b(t)，可正可负')})
        def out(q,unit,meaning,sh=None):
            c['outputs'][q]=dict(s(unit,meaning,sh),atol=1e-5 if unit=='1' else 1e-7,rtol=.005)
        if slug in ('binary-separation','coupled-precipitation'):
            out('composition','1','c，成分偏差点值');out('chemical_potential','J/m3','μ或μc，按本题公式的绝对势，无任意常量平移')
        if slug=='ternary-separation':
            out('composition','1','按c1,c2顺序，c3不单独输出',[2]);out('diffusion_potential','J/m3','按μ1,μ2顺序，绝对约束扩散势，不平移',[2])
        if slug in ('order-relaxation','driven-ordering','coupled-precipitation'):
            out('order_parameter','1','η点值');out('thermodynamic_force','J/m3',('hη' if slug=='coupled-precipitation' else 'h')+'，包含本题全部能量项，不是dη/dt')
        if slug=='grain-coarsening':
            out('order_parameters','1','按固定η1..ηK顺序，保留消失取向',['k']);out('thermodynamic_forces','J/m3','按固定h1..hK顺序',['k'])
        if slug=='crystal-density':
            out('density_deviation','1','n点值');out('chemical_potential','J/m3','按公式给定的有符号μ点值，势零点固定；包含完整四阶空间算子，不作常量平移或取模')
        limits={'length_x':(1e-9,1e-3),'length_y':(1e-9,1e-3),'energy_scale':(1.,1e9),
                'mobility':(1e-30,1e-6),'relaxation':(1e-12,1e6),'mobility_contrast':(0.,4.),
                'competition':(None,4.),'reference':(-1.,1.),'partition':(.1,1.),'undercooling':(-1.,1.)}
        for key,(lo,hi) in limits.items():
            if key in c['parameters']:
                if lo is not None:c['parameters'][key]['lower']=lo
                c['parameters'][key]['upper']=hi


def describe(v,size):
    sh='['+','.join(str(size).replace('k','K') if x=='s' else 'K' if x=='k' else str(x) for x in v['shape'])+']'
    return f'{v["kind"]} {sh}；`{v["unit"]}`；{v["meaning"]}'


def main():
    ext=ROOT/'qbank/extensions/caeoj_ext/microstructure';ext.mkdir(parents=True,exist_ok=True)
    (ext/'models.json').write_text(json.dumps(public_model_catalog(MODELS),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    toc=[]
    for sec,title,slugs in SECTIONS:
        sd=CH/sec;sd.mkdir(parents=True,exist_ok=True);links=[]
        for index,slug in enumerate(slugs,1):
            c=MODELS[slug];td=sd/slug;td.mkdir(exist_ok=True);num=sec.split('-')[0]+'.'+str(index)
            links.append(f'- [{num} {c["name"]}]({slug}/instruction.md)')
            parameters='\n'.join(f'| `{key}` | `{v["unit"]}` | {v["meaning"]}'+(f'；{v["lower"]}≤value' if 'lower' in v else '')+(f'；value≤{v["upper"]}' if 'upper' in v else '')+' |' for key,v in c['parameters'].items())
            timing='time_axes恰含static和requests'+('及control' if slug=='driven-ordering' else '')+'。static引用float64[1]的[0.0]。requests引用float64[T]，1≤T≤256，严格递增、首项≥0、末项t_end>0；不要求包含0。初态总在物理t=0，输出只在requests时刻，内部步长自由。'
            if slug=='driven-ordering':
                timing+='control引用float64[Kt]，2≤Kt≤256，严格递增，首项0、末项恰为t_end；外场在相邻控制结点间线性插值、结点取存储值，不外推；control可以不同于requests，积分遇控制结点不增加输出帧。'
            timing+='时间单位s，数组key自由。初始及材料字段引用static，输出全部引用requests。'
            initial='令状态向量u的分量顺序为'+c['state_order']+'，s='+('grain_count' if c['state_size']=='k' else str(c['state_size']))+'。在全部连续周期矩形上严格定义u_a(x,y,0)=m_a+Σ_j[a_ja cosθ_j+b_ja sinθ_j]，θ_j=2π(kx_j x/Lx+ky_j y/Ly)。m取offset，a、b取series.amplitude，波矢取series.wave；不能把模态ID当波数，也不按探针重建初态。每个波矢必须为非零、各分量绝对值≤8的精确整数，规范方向为kx>0或kx=0且ky>0；波矢对两两不同。模态按IDs行序对应系数，无强制频率排序。允许所有系数为0，因此均匀初态合法；没有未给定随机扰动。'
            if slug=='ternary-separation':
                initial+='定义R_a=Σ_j sqrt(a_ja²+b_ja²)。要求m1−R1≥0、m2−R2≥0且m1+m2+R1+R2≤1，作为保证初态单纯形的保守接收条件；不以此重新缩放系数。'
            elif slug=='grain-coarsening':
                initial+='逐分量R_a=Σ_j sqrt(a_ja²+b_ja²)，要求m_a−R_a≥0及m_a+R_a≤1；不要求各分量和为1，演化也不作此投影。'
            else:
                initial+='逐分量R_a=Σ_j sqrt(a_ja²+b_ja²)，要求|m_a|+R_a≤1，只限定初态，不对演化场裁剪或重新缩放。'
            initial+='此有限三角级数仅定义初态；求解对象为连续非线性初边值问题，非线性产生的新谐波不得截断到输入模态集合。内部空间分辨率、基函数及时间步由考生选择并控制误差。'
            records=[]
            for op,r in c['records'].items():
                records.append(f'### `{op}`\n\nconditions中该operator恰一条完整记录：role=`{r["role"]}`，variable=`{r["variable"]}`，operator=`{op}`，location=`{r["location"]}`，字段时间轴=`{r["axis"]}`；data恰含下列全部键，无默认值：\n\n| data键 | 类型、单位及含义 |\n|---|---|\n'+'\n'.join(f'| `{key}` | {describe(v,c["state_size"])} |' for key,v in r['data'].items()))
            outputs='\n'.join(f'| `{q}` | {describe(v,c["state_size"])} |' for q,v in c['outputs'].items())
            data=f'# {slug} 数据契约\n\n入口problem.json和data_file引用的扁平HDF5遵循CONTRACT，所有路径相对清单目录。physics恰含model、parameters，model=`microstructure-{slug}-v1`；task可省略，出现只能为`{slug}`。不接受profile、contract_version、analysis或materials混用。\n\n## 物理与边界\n\n{PHYS[slug]}\n\n二维连续周期矩形Ω=[0,Lx)×[0,Ly)，x、y单位m。场及本题动力学涉及的全部阶空间导数在两对边周期匹配；没有墙面、流入／流出或隐藏表面能。材料系数均匀、恒定，外驱若有仅按本题显式定义。\n\n## 参数全集\n\nphysics.parameters恰含下表全部项，每项仅value和unit；所有数值有限，布尔不可作数值，整数必须JSON整数。\n\n| 参数 | 单位 | 定义及范围 |\n|---|---|---|\n{parameters}\n\n## 对象与身份\n\nspatial_dimension=2；meshes和geometries必须为空，不存在未给定空间网格。locations恰含system、modes、probes：system为entities且IDs恰[0]；modes为entities，1..32个系数对象，IDs非负严格递增，可不连续；probes为points，1..128个真实坐标，coordinates为float64[N,2]，0≤x<Lx、0≤y<Ly，IDs非负严格递增，不要求坐标排序。探针不是内部计算网格，重复坐标允许，但身份独立。\n\n## 初态的连续定义\n\n{initial}\n\n## 时间与场数组\n\n{timing}\n\n所有字段float64，shape=[T,N,*component_shape]；T按字段time_axis，N按location IDs。scalar的component_shape=[1]、components=["value"]；components类型按表shape代入s'+('及k=grain_count' if slug=='grain-coarsening' else '')+'，components标签为按行优先展开的c1..cL，末轴变化最快。矩阵若有必须存完整数组。所有value_kind=point；entities字段是对象自身系数，不是空间平均或探针值。data只接受{"field":"逻辑字段名"}；fields记录的array才是HDF5 key，两种名称自由。字段与引用必须同location及所定时间轴；quantity等于data键名，value例外等于该条件variable。fields恰为实际被引用项，无内联常量、选项或隐式广播。\n\n每个输入字段显式sampling：space=uniform（独立系数对象之间无插值）、extrapolation=forbid；static的time=constant'+('、control的time=linear' if slug=='driven-ordering' else '')+'。连续初态按上节公式，不能按sampling枚举猜测空间插值。\n\n## 条件全集\n\n'+'\n\n'.join(records)+f'\n\n## 输出\n\n每种quantity至少一次，可重复请求；逻辑字段名及array key自由。均为probes上连续解的指定时刻点值，float64、value_kind=point、time_axis=requests、无sampling；shape及分量标签遵循上节，不是空间／时间平均。\n\n| quantity | 类型、单位与含义 |\n|---|---|\n{outputs}\n\n结果仅含输出array及其输入probes IDs／requests时间数组的精确副本；不导出坐标、输入模态、内部离散或其他数组。势和驱动力必须按给定绝对公式输出，不能借动力学只依赖导数而加常量；不旋转、平移组织、重排标签或拟合幅度。\n\n## 接收限制\n\n输入场及输出场总分量分别≤2000000。所有浮点值有限，初态的保守范围按上节逐项检查。\n'
            if slug=='ternary-separation':
                data=data.replace('## 输出\n', '迁移率矩阵检查要求存储值M12=M21，且M11>0、M22>0、M11M22−M12²>0；不取对称部分或修正特征值。\n\n## 输出\n')
            data=data.replace('## 条件全集\n', f'## 条件全集\n\nconditions恰含{len(c["records"])}条记录，下列每种operator各一条，无其他条件；记录顺序自由。\n')
            bounds='令ℓ0=min(Lx,Ly)，A=energy_scale。要求max(Lx,Ly)/ℓ0≤4、0<t_end≤1e9 s。'
            if slug=='crystal-density':
                bounds+='ell/ℓ0∈[1/16,1/4]；τ=M A t_end/ℓ0²≤0.2。'
            else:
                bounds+='每个梯度系数κ（或κc、κη）都满足κ/(Aℓ0²)∈[0.0025,0.1]。'
            if slug=='binary-separation':bounds+='τc=M0 A t_end/ℓ0²≤1。'
            if slug=='ternary-separation':bounds+='M的本征值位于[1e−30,1e−6] m5/(J.s)，条件数λmax/λmin≤20，且λmax A t_end/ℓ0²≤1。'
            if slug in ('order-relaxation','driven-ordering','grain-coarsening','coupled-precipitation'):bounds+='τa=L A t_end≤10。'
            if slug=='coupled-precipitation':bounds+='B/A∈[0.1,10]，τc=M A t_end/ℓ0²≤1。'
            if slug=='driven-ordering':bounds+='所有控制结点|b|/A≤2，区间内由线性插值继承此界限。'
            bounds+='上述接收范围包含端点，用于限定界面／晶体尺度、长宽比与演化跨度。全部请求的连续观测可表示为有限float64，并可在公开资源预算内达到评分精度。'
            data=data.replace('## 接收限制\n', '## 接收限制\n\n'+bounds+'\n')
            data=data.replace('components类型按表shape代入s'+('及k=grain_count' if slug=='grain-coarsening' else ''),'components类型按表shape'+('（K=grain_count）' if slug=='grain-coarsening' else ''))
            if slug!='ternary-separation':data=data.replace('矩阵若有必须存完整数组。','')
            if slug!='coupled-precipitation':data=data.replace('κ（或κc、κη）','κ')
            if slug!='crystal-density':data=data.replace('界面／晶体尺度','界面尺度')
            else:data=data.replace('界面／晶体尺度','晶体尺度')
            if slug!='driven-ordering':data=data.replace('外驱若有仅按本题显式定义','没有外驱')
            if slug!='grain-coarsening':data=data.replace('不旋转、平移组织、重排标签或拟合幅度','不旋转、平移组织或拟合幅度')
            if slug in ('order-relaxation','driven-ordering','grain-coarsening'):
                data=data.replace('势和驱动力必须按给定绝对公式输出，不能借动力学只依赖导数而加常量','驱动力必须按给定有符号公式输出，不加常量或取模')
            (td/'DATA.md').write_text(data,encoding='utf-8')
            tolerances='\n'.join(f'| `{q}` | {v["atol"]} | {v["rtol"]} | `{v["unit"]}` |' for q,v in c['outputs'].items())
            instruction=f'# {num} {c["name"]}\n\n实现覆盖公开问题族的可复用求解器，冻结后处理多个未见算例。\n\n问题位于二维周期矩形，材料系数、组织初态、尺寸、请求时刻'+('及外场历史' if slug=='driven-ordering' else '')+'随算例变化。输入及精确初边值定义见[本题DATA](DATA.md)，存储和通用引用见[CONTRACT](../../../../docs/CONTRACT.md)，三文件构成全部题意。考生负责给定有效材料模型的数值实现、内部空间离散、非线性／高阶处理和时间误差控制；不要求某种软件、算法或复现参考实现。覆盖完整公开范围的解析／降阶方法同样有效。初态用有限三角级数定义，不要求谱方法，也不允许把连续演化固定截断到初始模式。\n\n## 运行与资源\n\n入口`python solve.py --input /path/problem.json --output /path/result.h5`。每例Linux AMD64、{c["timeout"]}秒墙钟（含启动与I/O）、2CPU、4096MB、0GPU、逐例无网络；0退出并完成关闭结果文件，无独立输出字节限额。生成求解器3600秒、构建1800秒；提供Python3、NumPy、SciPy、h5py、Gmsh、jsonschema及C++/OpenMP/OpenMPI/HDF5，不强制Python。输入模式1..32、探针1..128、输出帧1..256；输入／输出场各≤2000000分量。模式及输出点数不限制内部数值自由度。\n\n## 评分\n\n每有效例正常退出、结构合法且每quantity全部时刻／探针／分量满足`|结果−参考|≤atol+rtol·|参考|`得1分，否则0分，等号接受。无常量势平移、组织平移／旋转、幅度拟合或标签重排；守恒、能量下降或低残差不替代逐值结果。\n\n| quantity | atol | rtol | 单位 |\n|---|---|---|---|\n{tolerances}\n\n成绩=通过有效例数／有效例总数。输入、参考或配置错误属基础设施错误，不计为考生失分；无有效例不产生成绩。\n'
            if slug!='grain-coarsening':
                instruction=instruction.replace('或标签重排','')
            instruction=instruction.replace('{c["timeout"]}',str(c['timeout'])).replace('{tolerances}',tolerances)
            instruction=instruction.replace('模式及输出点数不限制内部数值自由度；','模式及输出点数不限制内部数值自由度；仅接收DATA公开的有限长度、能量、无量纲界面／晶体尺度和时程范围，所有请求观测须能以有限float64表示；')
            if slug in ('order-relaxation','driven-ordering','grain-coarsening'):
                instruction=instruction.replace('无常量势平移','无驱动力常量平移')
            instruction=instruction.replace('界面／晶体尺度','晶体尺度' if slug=='crystal-density' else '界面尺度')
            (td/'instruction.md').write_text(instruction,encoding='utf-8')
            policy=dict(version=2,quantities={q:dict(unit=v['unit'],rule=dict(metric='pointwise',time='per_time',components='per_component',atol=v['atol'],rtol=v['rtol'])) for q,v in c['outputs'].items()})
            (td/'author').mkdir(exist_ok=True)
            (td/'author/grading-template.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
            (td/'judge-config.json').write_text(json.dumps(dict(timeout_seconds=c['timeout'],max_output_bytes=None,stage='provisional',verifier_budget=dict(base_seconds=300,per_case_overhead_seconds=60)),indent=2)+'\n',encoding='utf-8')
            (td/'harbor').mkdir(exist_ok=True)
            (td/'harbor/requirements.txt').write_text('scipy==1.18.1\n',encoding='utf-8')
            (td/'harbor/task.toml').write_text('[agent]\ntimeout_sec = 3600.0\n\n[environment]\nbuild_timeout_sec = 1800.0\ncpus = 2\nmemory_mb = 4096\ngpus = 0\nos = "linux"\n\n[verifier]\nnetwork_mode = "no-network"\n',encoding='utf-8')
        (sd/'README.md').write_text(f'# {sec.split("-")[0]} {title}\n\n'+'\n'.join(links)+'\n',encoding='utf-8')
        toc.append(f'- [{sec.split("-")[0]} {title}]({sec}/README.md)')
    (CH/'README.md').write_text('# 第十六章 材料组织与微观演化分析\n\n五节七题；考生仅依赖本题instruction、DATA及通用CONTRACT。正式数据、参考与发布留后。\n\n'+'\n'.join(toc)+'\n\n维护：[规划](../design/chapter-16-microstructure.md)、[逐题清单](../design/chapter-16-task-plan.md)、[进度](../design/reviews/chapter-16-progress.md)、[声明维护](../maintenance/protocols/MICROSTRUCTURE.md)。\n',encoding='utf-8')


if __name__=='__main__':
    main()
