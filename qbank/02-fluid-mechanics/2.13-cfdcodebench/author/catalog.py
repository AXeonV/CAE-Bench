"""Frozen mathematical migration decisions and public protocol facts.

The source JSON is acquired by fetch_upstream.py; it is never a runtime dependency
of a candidate's public bundle. render.py expands all definitions into each DATA.
"""
import json
from pathlib import Path
import math

SECTION = Path(__file__).resolve().parent.parent
ROOT = SECTION.parents[2]
WORK = ROOT / 'runs/cfdcodebench-local-20261019'
REVISION = 'e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2'
IDS = ['1D_Burgers_Equation','1D_Diffusion','1D_Euler_Shock_Tube',
       '1D_Linear_Convection','1D_Nonlinear_Convection','2D_Burgers_Equation',
       '2D_Convection','2D_Diffusion','2D_Inviscid_Burgers','2D_Laplace_Equation',
       '2D_Linear_Convection','2D_Navier_Stokes_Cavity','2D_Navier_Stokes_Channel',
       '2D_Poisson_Equation','2D_Steady_Heat_Equation','2D_Unsteady_Heat_Equation',
       'Fully_Developed_Turbulent_Channel_Flow','Lid_Driven_Cavity',
       'Flow_Past_Circular_Cylinder','1D_KdV_Burgers_Equation',
       '2D_Rayleigh_Benard_Convection','2D_Shear_Flow_With_Tracer',
       'Pipe_Flow_Disk_EVP','Lane_Emden_Equation']
TITLES = ['一维周期黏性 Burgers','一维矩形初态扩散','理想气体激波管',
          '一维周期对流扩散','一维非线性熵输运','二维黏性 Burgers',
          '二维对角熵输运（终时 0.32）','二维矩形初态扩散','二维对角熵输运（终时 0.40）',
          '矩形混合边界 Laplace 势','二维线性脉冲平移','不可压盖驱方腔（黏度 0.01）',
          '周期通道启动流','双 Gaussian 源 Poisson 势','四边恒温矩形稳态传热',
          'Gaussian 初温与持续热源','Cess 闭合双壁湍流通道',
          '不可压盖驱方腔（黏度 0.1）','圆柱外圆环涡量流函数流动',
          '周期 KdV–Burgers','二维 Rayleigh–Bénard 对流','周期剪切流与被动示踪剂',
          '圆管扰动的最右增长率','Lane–Emden 正基态']
TIMES = [0.14*math.pi,.0333,.25,10.,5.,.027,.32,.3777,.4,0.,.5,10.,5.,0.,0.,3.,0.,.5,10.,10.,50.,20.,0.,0.]
DOMAINS = [[0,2*math.pi],[0,2],[-1,1],[-5,5],[0,2*math.pi],
           [0,2,0,2],[0,2,0,2],[0,2,0,2],[0,2,0,2],[0,2,0,1],
           [0,2,0,2],[0,1,0,1],[0,2,0,2],[0,2,0,1],[0,5,0,4],[-1,1,-1,1],
           [0,2],[0,1,0,1],[.5,10,0,2*math.pi],[0,10],[0,4,0,1],[0,1,-1,1],[0,1],[0,1]]

NOTES = {
1: '初态按所给区间公式作几乎处处周期延拓；不把极小但非零的端导数差当成严格光滑。t>0 取黏性周期解及周期迹。',
3: '取理想气体 Euler 熵解。反射壁质量与总能通量为零，动量通量可为壁压。E 是比总能，不能提交 rho*E。输出是指定位置的点值，不是单元平均；不在波面上安排观测点。',
4: '实际模型含扩散 epsilon=0.0005，不能只做平移。Gaussian 初态按区间式周期延拓；t>0 的解及导数周期。',
5: '连续定义为 u_t+(u^2/2)_x=0 的周期 Kružkov 熵解。初态按区间公式周期延拓；nu 字样不代表物理黏性。激波面如被采样，取沿正 x 的右迹。',
6: '这是黏性矢量 Burgers，不施加不可压条件。固定初边值满足 u=v；两个字段都必须提交。矩形阶跃的区间端点取高值，t>0 为黏性解。',
7: '本题固定 u=v=q，取 q_t+(q^2/2)_x+(q^2/2)_y=0 的标量熵解，再输出 u=v=q。只在入流施加背景1，其他边界取熵外流；本终时扰动尚未到达外边界。激波采样取沿 (1,1) 的右迹。',
9: '本题固定 u=v=q，取 q_t+(q^2/2)_x+(q^2/2)_y=0 的标量熵解，再输出 u=v=q。只在入流施加背景1，其他边界取熵外流；本终时扰动尚未到达外边界。激波采样取沿 (1,1) 的右迹。与终时0.32的题保留不同来源身份。',
10: 'p 是势函数，没有常数自由度。边界在各开边施加，允许角点导数奇异；若采样角点，Dirichlet 迹优先。稳态没有物理初态，零值仅可作迭代初猜。',
11: '仅左、下边为入流边界，右、上取外流。固定终时的平移脉冲未触外流；因此该时刻外流值也为1。平移矩形开内部取2，外部取1；矩形开边点取1.5，四个顶点取四象限平均1.25。',
12: '修订移植版：采用连续不可压 Navier–Stokes，删除原盖板整边 p=0 及其他独立压力条件。压力由动量与散度约束确定，只固定常数基准。t=0 内部静止，t>0 突然启动盖板；速度边界作用于各开边。顶角如被采样取速度(0,0)，允许角点/启动奇异。',
13: '补明 div U=0；周期压力排除额外线性压降，驱动仅为 F=1。固定初态给平行启动流；只提交 u，不能用无限时刻抛物线代替 t=5。',
14: 'p 是有固定 Dirichlet 边界的势，不消均值。零初值仅为稳态迭代猜测。',
15: '边温作用于开边，允许角点不连续；若采样角点，上下边优先于左右边。输入和输出是以 1 摄氏度为尺度的温度读数数值，记为无量纲 T；本题温度评分减去公开背景20，不允许转成 Kelvin 后直接提交。',
16: 't>0 边温1优先；内部初态按几乎处处意义给出。热源持续作用至终时，不能省略；评分背景为1。所有数值均无量纲。',
17: '修订移植版：按作者实际程序采用最近壁面距离 d=min(y,2-y)，y+=Re_tau*d。Cess 根式减去1后的一半是 mu_t/mu，总黏度 mu_eff=mu+mu_t；不允许退化成壁面零总黏度或改换闭合模型。',
18: '修订移植版：连续不可压 Navier–Stokes，删除全墙独立物理压力 Neumann 条件及未定义的 U*、Delta t；分步压力修正不是必交物理压力。压力仅固定基准。t=0 内部静止，t>0 突然启动盖板；速度条件作用于开边，顶角如被采样取(0,0)，允许启动/角点奇异。',
19: '修订移植版：初始内部 omega=0，由其及给定流函数 Dirichlet 边界解 Poisson 得到初始 psi，不再独立指定内部 psi=0。t>0 内圆连续无滑移：psi=20、partial_r psi=0；壁涡量由运动学与方程确定，不把含网格步长的 Thom 模板作为物理条件。外圆 psi=20+r*sin(theta)、omega=0，theta 周期。',
20: 'L=10；保持原有限区间初态并作周期延拓，不改成精确孤波。t>0 所需空间导数周期；三阶项符号按给定方程。',
21: 'b 是原无量纲总浮力/温度变量，不是减去1-z后的偏差。原 x-z 平面在协议中映射为 x-y，w 为第二方向分量。压力无独立初态，仅固定常数基准。',
22: '修订移植版：令 U_raw 为下列原始速度，实际 U0=P U_raw=U_raw-grad(chi)，其中 lap(chi)=div U_raw，chi 为双周期零均值解；这是保持速度均值的周期 Helmholtz 投影。示踪剂初态仍为原始水平速度剖面，不随投影替换。原 x-z 映射为协议 x-y，w 为第二方向分量；压力无独立初态。',
23: '取非零速度模态 exp(s*t+i*m*phi+i*kz*z)，固定 m=5、kz=1、Re=10000；取该物理谱实部最大的增长率，只输出其实部。横向 grad/div/向量 Laplace 是欧氏圆盘算子，不能漏曲率耦合；中心要求笛卡尔光滑与有限能正则性。无需提交特征向量。',
24: '明确选取 0<=r<1 内严格为正的无节点基态，排除零解及内部有节点分支。不固定 f(0)=1；中心 f_prime(0)=0，方程在中心取正则极限。',
}

def catalog():
    source = json.loads((WORK/'upstream/CFDCodeBench/PDE_Benchmark/prompt/PDE_TASK_QUESTION_ONLY.json').read_text(encoding='utf-8'))
    records = []
    for i, identity in enumerate(IDS, 1):
        s = source[identity]
        task = 'cc-' + identity.lower().replace('_','-')
        equation, bc, ic = s['equation'], s['boundary conditions'], s['initial conditions']
        if i in (12,18):
            viscosity = .01 if i == 12 else .1
            equation = f'\\[\\partial_t U+(U\\cdot\\nabla)U=-\\nabla p+{viscosity}\\Delta U,\\quad \\nabla\\cdot U=0,\\quad U=(u,v).\\]'
            bc = '单位方腔：上开边 U=(1,0)，左、右、下开边 U=(0,0)。压力由方程确定，不额外施加独立压力边界条件。'
            ic = 't=0 内部 U=(0,0)；t>0 盖板突启。'
        if i == 17:
            equation = r'\[\frac{d}{dy}(\mu_{eff}u_y)=-1,\quad\mu=1/395,\quad d=\min(y,2-y),\quad y^+=395d.\]'+'\n'+r'\[\mu_{eff}=\mu\left[1+\frac{\sqrt{1+(0.426\cdot395)^2(2d-d^2)^2(3-4d+2d^2)^2(1-e^{-y^+/25.4})^2/9}-1}{2}\right].\]'
            bc,ic = 'u(0)=u(2)=0。', '稳态无初态。'
        if i == 19:
            equation = r'\[\Delta\psi=-\omega,\quad u_r=r^{-1}\psi_\theta,\quad u_\theta=-\psi_r,\quad \omega_t+u_r\omega_r+(u_\theta/r)\omega_\theta=0.005\Delta\omega,\quad\Delta=\partial_{rr}+r^{-1}\partial_r+r^{-2}\partial_{\theta\theta}.\]'
            bc = 'r=0.5: psi=20、partial_r psi=0（无滑移）；r=10: psi=20+r*sin(theta)、omega=0；theta 周期。'
            ic = '内部初始 omega=0；解 Delta psi=0，内圆 psi=20、外圆 psi=20+r*sin(theta) 初始化 psi。壁面启动允许瞬态不相容。'
        if i==21:equation=equation.replace('buoyancy (temperature deviation)','total buoyancy/temperature variable')
        if i==24:
            equation=r'\[f^{\prime\prime}(r)+\frac{2}{r}f^\prime(r)+f(r)^3=0,\quad 0<r<1.\]'+'\n这是三维球对称 Laplace 算子；中心取正则极限 Delta f(0)=3f_double_prime(0)。'
            bc='f_prime(0)=0，f(1)=0；0<=r<1 内 f(r)>0，取无内部节点的正基态。'
        if i in (10,14,15,17,23,24): ic = '稳态或特征值任务无物理时间初态。'+ ('\n'+ic if i == 24 else '')
        records.append(dict(index=i, source_id=identity, task=task, title=TITLES[i-1],
                            fields=s['save_values'], time=TIMES[i-1], domain=DOMAINS[i-1],
                            equation=equation, boundary=bc, initial=ic, domain_text=s['domain'],
                            note=NOTES.get(i,'初态按给定区间函数的几乎处处意义解释；t>0 边界优先。'),
                            pressure=i in (12,18,21,22), offset=20 if i==15 else 1 if i==16 else 0,
                            dimension=2 if len(DOMAINS[i-1])==4 and i!=23 else 1))
    return records
