"""Generate private, reproducible test descriptions alongside the input bank."""
INITIAL = {
    'zero':'0', 'linear':'z',
    'modes':'0.6 sin(πz) − 0.3 sin(3πz) + 0.2 sin(7πz)',
    'plate':'0.8（0.2<z<0.55）；−0.5（0.55≤z<0.8）；其余为 0',
    'pulse':'0.9 max(1−|z−0.35|/0.12,0)',
    'oscillatory':'0.45 sin(2πz) + 0.25 sin(9πz) − 0.15 sin(13πz)',
    'reverse':'0.7−1.4z',
    'double_pulse':'0.8 max(1−|z−0.25|/0.1,0) − 0.6 max(1−|z−0.7|/0.15,0)',
}
SIDES = ('left','right','bottom','top')


def write_case_document(destination, records, transient):
    title='瞬态' if transient else '稳态'
    lines=[f'# 二维{title}不可压缩流测试点与标答（出题材料）','',
        '本文件与 [DESIGN.md](DESIGN.md) 仅供出题使用，不进入解题材料。输入只含条件与场数据，不含下列配方或参考公式。',
        '', 'ν=μ/ρ；速度单位 m/s、压力 Pa、加速度 m/s²、时间 s。P 表示相对边周期连接；D 表示给定速度。所有点采用面积平均压力为零。',
        '通道取跨壁坐标 s∈[0,H]、z=s/H、流向单位向量 e；`q∞=U₀+(U₁−U₀)z+aH²z(1−z)/(2ν)`，`u∞=e q∞`、`p=0`。']
    if transient:
        lines += ['','## 初始条件与解析标答','',
            '下列通道配方只生成初始**节点值**；连续初值一律为相邻跨壁层之间的分片线性插值，不直接使用配方函数作为连续标答。',
            '`u=e[q∞+Σ bₙ sin(nπs/H) exp(−ν(nπ/H)²t)]`，`bₙ=(2/H)∫₀ᴴ(q₀−q∞)sin(nπs/H)ds`，`p=0`。',
            '系数按初始分片线性区间精确积分，求和 1,024 项；每例记录截断尾界。t=0 直接复制初值。',
            '', '| 初值配方 | 节点流向速度 q₀(z) |','|---|---|']
        lines += [f'| {name} | {formula} |' for name,formula in INITIAL.items()]
        lines += ['','二维周期点有两类：同一 Laplace 特征值的叠加涡旋，以及斜向剪切波；均包含常数平移速度 c。',
            '叠加涡旋令 `κ=2πm/L`，`X=κ(x−x₀−cₓt)+φₓ`，`Y=κ(y−y₀−cᵧt)+φᵧ`，`f=(sin,cos)`，',
            '`ψ=e^(−2νκ²t) f(X)ᵀ C f(Y)/κ`；`u=c+(ψ_y,−ψ_x)`，',
            '`p=ρ[e^(−4νκ²t)ΣCᵢⱼ²/2−(|u−c|²+2κ²ψ²)/2]`。C 只有左上项非零时退化为单涡旋。',
            '剪切波令 `k=2π(wₓ,wᵧ)/L`、`d=(kᵧ,−kₓ)/|k|`，',
            '`u=c+A d sin(k·(x−x₀−ct)+φ) e^(−ν|k|²t)`，`p=0`。',
            '这两类初值都是题目规定的低阶周期三角多项式。完整推导与独立参考实现见 [DESIGN.md](DESIGN.md) 和 `author/oracle.py`。']
    else:
        lines += ['','方腔使用 Ghia 1982 Re=100 的已发表中线数据；按壁速、尺度、旋转或反射变换坐标与矢量分量。只比较所发表的中线分量，不生成全场或压力标答。来源和表格见 [DESIGN.md](DESIGN.md#ghia-方腔中线)。']
    lines += ['', '## 测试点总览','',
        '| 测试点 | 类型／主要变化 | 左／右／下／上 | ν / ρ | 域 (x₀,y₀; Lx,Ly) | 节点／三角形 |'+(' 输出个数／首个正时刻／末时刻 |' if transient else ''),
        '|---|---|---|---|---|---|'+('---|' if transient else '')]
    for r in records:
        c=r['recipe']
        bc='P/P/D/D' if c['axis']==0 else 'D/D/P/P'
        kind=c['initial'] if transient else '通道'
        if c['family']=='cavity':bc='D/D/D/D';kind=f"方腔 {c['lid']} {'+' if c['lid_sign']>0 else '−'}"
        if c['family']=='periodic':bc='P/P/P/P';kind='斜向剪切波' if c['pattern']=='shear' else ('叠加涡旋' if c['coefficients'] else '单涡旋')
        lines.append(f"| {r['case']} | {kind} | {bc} | {c['nu']} / {c['rho']} | {tuple(c['origin'])}; {tuple(c['size'])} | {r['nodes']} / {r['triangles']} |"+
                     (f" {len(r['output_times_s'])} / {r['output_times_s'][1]:g} / {r['output_times_s'][-1]:g} |" if transient else ''))
    lines += ['', '## 每例初值、驱动、边界方程与参考范围' if transient else '## 每例驱动、边界方程与参考范围']
    for r in records:
        c=r['recipe'];lines += ['',f"### {r['case']}",'']
        if c['family']=='channel':
            axis=c['axis'];h=c['size'][1-axis];e='(1,0)' if axis==0 else '(0,1)'
            origin=c['origin'][1-axis];coord='y' if axis==0 else 'x'
            lines += [f"`s={coord}−({origin:g})`，`H={h:g}`，`e={e}`，`a={c['acceleration']:g} e`。",
                      f"`q∞={c['lower']:g}+({c['upper']-c['lower']:g})z+({c['acceleration']*h*h/(2*c['nu']):g})z(1−z)`。"]
            if transient:lines += [f"初始节点值 `u₀=e q₀(z)`，`q₀={INITIAL[c['initial']]}`；正时间参考为上述初值积分级数。"]
            else:lines += ['参考为 `u=e q∞`、`p=0`。']
            for side in SIDES:
                periodic=side in (('left','right') if axis==0 else ('bottom','top'))
                text=('与 '+({'left':'right','right':'left','bottom':'top','top':'bottom'}[side])+' 周期连接，u、p 及对应导数相等') if periodic else f"u={c['lower'] if side in ('left','bottom') else c['upper']:g} e"+('（t>0）' if transient else '')
                lines += [f'- {side}：{text}。']
        elif c['family']=='cavity':
            lines += ['`a=(0,0)`；Re=100。运动边开区间为恒定壁速，两个端点为零。']
            vector=(c['lid_sign']*c['upper'],0) if c['lid'] in ('top','bottom') else (0,c['lid_sign']*c['upper'])
            for side in SIDES:lines += [f"- {side}：`u={vector if side==c['lid'] else (0,0)}`。"]
            transform=r['reference']['coordinate_transform']
            lines += [f"归一化坐标变换 `x̂=M ξ+b`，`M={transform['matrix']}`、`b={transform['offset']}`；速度同乘 M 和壁速幅值 {c['upper']:g}。",
                      '只输出两个清单中的中线分量；坐标显式存于 NPZ，采样点 IDs 不代表网格 tag。']
        else:
            lines += [f"`a=(0,0)`，`c={tuple(c['drift'])}`。"]
            if c['pattern']=='shear':
                lines += [f"剪切波：`A={c['amplitude']:g}`、`w={tuple(c['wave'])}`、`φ={c['phase'][0]:g}`；初值和参考由上述剪切公式取 t=0 或输出时刻。"]
            else:
                coeff=c['coefficients'] or (c['amplitude'],0,0,0)
                lines += [f"叠加涡旋：`C=[[{coeff[0]:g},{coeff[1]:g}],[{coeff[2]:g},{coeff[3]:g}]]`、`m={c['mode']}`、`φ={tuple(c['phase'])}`；初值和参考由上述 ψ、u、p 公式生成。"]
            lines += ['- left/right：u、p 及对应导数周期相等。','- bottom/top：u、p 及对应导数周期相等。']
        lines += ['- 压力规范：`∫Ω p dΩ / |Ω| = 0`。']
        if transient:lines += ['输出时刻：`['+', '.join(f'{t:.9g}' for t in r['output_times_s'])+']` s。']
        lines += [f"网格：n={c['n']}，{'稀疏' if c['sparse'] else '连续'} tag，MSH 4.1 ASCII；全部参考参数及来源另存 `reference/{r['case']}/analytic.json`。"]
    (destination/'TEST-CASES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
