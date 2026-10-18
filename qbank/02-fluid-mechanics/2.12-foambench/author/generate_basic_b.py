"""Regenerate 40 basic and two advanced statements; no numerical data are made."""
from pathlib import Path
import hashlib
import json
import re
from source_snapshot import read_source

ROOT = Path(__file__).resolve().parents[4]
SECTION = Path(__file__).resolve().parent.parent
UPSTREAM = "e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2"


def number(text, pattern):
    return float(re.search(pattern, text, re.I).group(1))


def scalar(value, unit):
    return {"value": value, "unit": unit}


def table(rows, header="参数 | 值 | 单位"):
    return "| " + header + " |\n| " + " | ".join("---" for _ in header.split("|")) + " |\n" + "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def field(name, unit, kind="scalar", shape=None, components=None):
    return {"array": name, "quantity": name, "location": "samples", "time_axis": "output", "dtype": "float64", "kind": kind, "component_shape": shape or [1], "components": components or ["value"], "unit": unit, "value_kind": "point"}


GAS = """求二维无黏可压缩 Euler 质量、动量、总能量守恒方程，状态方程 p=ρRT，e=Cv T，E=e+|u|²/2；无黏应力、无热传导、无体力、无化学和其他体源。取 R=5/7 J/(kg.K)，Cp=2.5 J/(kg.K)，Cv=Cp−R，γ=Cp/Cv=1.4。p 是绝对静压。来源 molWeight=11640.3 kg/kmol 仅保留为归一化气体标签，R 由本题精确定义而不从舍入摩尔质量反算。Pr 保留源变体的值，但因 μ=0，Pr 不改变本题方程。激波取满足热力学熵增的弱解。
"""

CHEM = """求二维瞬态可压缩反应混合物的质量、动量、五组分质量和总能量守恒方程。组分顺序固定为 CH4、O2、N2、CO2、H2O，Y 是质量分数，ΣY=1，ρ=p/(Rmix T)，Rmix=ΣYs Rs，Rs=Ru/Ms，Ru=8314.462618 J/(kmol.K)。无重力、无辐射、无额外外部热源。层流黏应力 τ=μ[∇u+(∇u)ᵀ−(2/3)(∇·u)I]，无附加体黏度。

唯一反应 CH4+2O2→CO2+2H2O；反应进度率 q=5.2×10¹⁶ exp(−14906/T)cCH4 cO2²，cs=ρYs/Ms（kmol/m3），q 单位 kmol/(m3.s)，前因子单位 m6/(kmol2.s)，温度指数0。ωs=Ms νs q，其中 ν=(-1,-2,0,1,2)，单位 kg/(m3.s)；N2源严格为0。为保证元素和总质量守恒，统一原子量C=12.0107、H=1.00794、O=15.9994、N=14.0067 kg/kmol，各分子量按化学式求和，详见下表；不使用各物种独立舍入而不一致的分子量。反应是单步全局机理，不能解释为详细机理。

每组分采用 NASA 七系数多项式：cp,s/Rs=a1+a2T+a3T²+a4T³+a5T⁴；hs/(Rs T)=a1+a2T/2+a3T²/3+a4T³/4+a5T⁴/5+a6/T；ss/Rs=a1 lnT+a2T+a3T²/2+a4T³/3+a5T⁴/4+a7。T≤1000K用低温系数，T>1000K用高温系数；在标注温度区间外仍按同一端侧多项式外推，此为确定的数学延拓，不承诺真实物性有效。es=hs−RsT，混合物e=ΣYs es；总能量 E=e+|u|²/2 包含生成焓，故保守总能量方程不再添加化学热源，反应热由组分改变自然体现。导热与组分焓通量为 −κ∇T+Σhs Js。

组分 μs=As T^(3/2)/(T+Ts)；Cv,s=cp,s−Rs，κs=μs Cv,s[1.32+1.77Rs/Cv,s]。以摩尔分数 Xs=(Ys/Ms)/Σ(Yj/Mj) 混合：Φij=[1+sqrt(μi/μj)(Mj/Mi)^(1/4)]²/sqrt[8(1+Mi/Mj)]，μ=Σ Xi μi/(Σj Xj Φij)，κ=Σ Xi κi/(Σj Xj Φij)。cp=ΣYs cp,s。统一单位Lewis数扩散 D=κ/(ρcp)，先取 Js*=−ρD∇Ys，再取 Js=Js*−YsΣJj*，从而ΣJs=0；不加Soret、Dufour、压力扩散。能量方程含黏应力功；无独立燃烧效率因子、湍流火焰速度或点火模型。

| 组分 | M (kg/kmol) | As (Pa.s/K^(1/2)) | Ts (K) | 多项式温度范围(K) |
| --- | --- | --- | --- | --- |
| O2 | 31.9988 | 1.753e-6 | 139 | 200–5000 |
| H2O | 18.01528 | 2.978e-7 | 1064 | 200–5000 |
| CH4 | 16.04246 | 1.0194e-6 | 171.06 | 200–6000 |
| CO2 | 44.0095 | 1.503e-6 | 222 | 200–5000 |
| N2 | 28.0134 | 1.401e-6 | 107 | 200–5000 |

| 组分 | 温段 | (a1,a2,a3,a4,a5,a6,a7)，T以K代入 |
| --- | --- | --- |
| O2 | 低 | (3.21294,0.00112749,-5.75615e-7,1.31388e-9,-8.76855e-13,-1005.25,6.03474) |
| O2 | 高 | (3.69758,0.00061352,-1.25884e-7,1.77528e-11,-1.13644e-15,-1233.93,3.18917) |
| H2O | 低 | (3.38684,0.00347498,-6.3547e-6,6.96858e-9,-2.50659e-12,-30208.1,2.59023) |
| H2O | 高 | (2.67215,0.00305629,-8.73026e-7,1.201e-10,-6.39162e-15,-29899.2,6.86282) |
| CH4 | 低 | (5.14988,-0.013671,4.91801e-5,-4.84744e-8,1.66694e-11,-10246.6,-4.64132) |
| CH4 | 高 | (1.63543,0.0100844,-3.36924e-6,5.34973e-10,-3.15528e-14,-10005.6,9.9937) |
| CO2 | 低 | (2.27572,0.00992207,-1.04091e-5,6.86669e-9,-2.11728e-12,-48373.1,10.1885) |
| CO2 | 高 | (4.45362,0.00314017,-1.27841e-6,2.394e-10,-1.66903e-14,-48967,-0.955396) |
| N2 | 低 | (3.29868,0.00140824,-3.96322e-6,5.64152e-9,-2.44486e-12,-1020.9,3.95037) |
| N2 | 高 | (2.92664,0.00148798,-5.68476e-7,1.0097e-10,-6.75335e-15,-922.798,5.98053) |
"""

SA = """采用可压缩平均流上的自由剪切 SA-noft2 涡黏闭合；该域没有固壁，壁距取无穷大，壁面破坏项为0，不建立虚构壁面。输运变量 ν̃≥0，ν=μ/ρ，χ=ν̃/ν，fv1=χ³/(χ³+7.1³)，νt=ν̃fv1，μt=ρνt。其方程为 Dν̃/Dt=0.1355 Ων̃+[∇·((ν+ν̃)∇ν̃)+0.622|∇ν̃|²]/(2/3)，Ω=sqrt(2WijWij)，W=(∇u−∇uᵀ)/2。无转捩项、无可压缩修正，湍动能各向同性应力不另引入。初始及两入口ν̃=1e-5 m2/s，出口法向导数为0（包括倒流）。这一定义保留SA涡黏机制，但明确选择了原配置未说明的无壁版本。
"""

KE = """采用标准可压缩平均流 k–ε 闭合，不加浮力生产、膨胀耗散、低雷诺数或燃烧专用修正。μt=0.09ρk²/ε，τt=2μt dev(S)−(2/3)ρkI，S=(∇u+∇uᵀ)/2，P=max(τt:∇u,0)。守恒输运为 ∂t(ρk)+∇·(ρuk)=∇·[(μ+μt)∇k]+P−ρε；∂t(ρε)+∇·(ρuε)=∇·[(μ+μt/1.3)∇ε]+1.44(ε/k)P−1.92ρε²/k。k=0时取μt=P=0，ε/k相关源项按k→0且ε→0的静止无湍流极限取0；其他时刻要求k≥0、ε>0。

初始k=30 m2/s2、ε=30000 m2/s3。燃料入口强度 I=0.0458、混合长度 L=0.000504m，空气入口 I=0.0471、L=0.019677m，入口 k=1.5(I|u|)²、ε=0.09^(3/4)k^(3/2)/L。出口k、ε法向导数均为0，包括倒流；不把源文件占位value=1当作入口物理值。
"""


def details(family, prompt, entry, advanced):
    params = {}
    def add(k, v, u):
        params[k] = scalar(v, u)
    add("end_time", {"counterFlowFlame2D": .5, "forwardStep": 4, "BernardCells": 1000, "wedge": .2}[family], "s")
    add("output_interval", {"counterFlowFlame2D": .05, "forwardStep": .1, "BernardCells": 50, "wedge": .02}[family], "s")
    extra_outputs = {}
    if family == "counterFlowFlame2D":
        fuel = number(prompt, r"velocity of fuel is ([\d.e+-]+)")
        air = number(prompt, r"velocity of air is ([\d.e+-]+)")
        add("fuel_velocity_x", fuel, "m/s"); add("air_velocity_x", air, "m/s")
        add("inlet_temperature", 293, "K"); add("reservoir_total_pressure", 1e5, "Pa")
        title = "甲烷与空气对向扩散火焰" + ({"SA": "：SA平均流", "KE": "：k–ε平均流"}.get(advanced, "：层流"))
        target = f"研究燃料速度 {fuel:g} m/s 与空气速度 {air:g} m/s 的相向供给下，混合、点火热态启动和单步甲烷反应的耦合演化。"
        geometry = "域为 0<x<0.02m、−0.01<y<0.01m。fuel 是 x=0，air 是 x=0.02，outlet 是 y=±0.01 的两段开口；四角按入口边界取值。二维场在z不变，无前后表面条件。"
        model = CHEM + "\n" + (SA if advanced == "SA" else KE if advanced == "KE" else "本题为层流，μt=0，不求解任何湍流变量。\n")
        if advanced:
            model += "\n平均流动量和能量方程采用τ+τt，其中SA为τt=2μt dev(S)，KE采用上述τt。总能量定义仍不含k；不另加k扩散能量通量。有效导热κeff=κ+μt cp/0.85；扩散Js*=[−ρD−μt/0.7]∇Ys，再按同一修正保证ΣJs=0。化学源直接用平均T、Y计算，不加湍流化学相互作用。\n"
        bounds = f"""fuel：u=({fuel:g},0)m/s，T=293K，Y=(1,0,0,0,0)，∂np=0。air：u=({air:g},0)m/s，T=293K，Y=(0,0.23,0.77,0,0)，∂np=0。

outlet：总压储槽 p0=100000Pa。令un=u·n；外流(un≥0)取p=p0、∂nu=0、∂nT=0、∂nY=0；倒流(un<0)取切向速度为0、∂nun=0，p=p0−ρ|u|²/2，T=293K，Y=(0,0,1,0,0)。这是本题明确采用的动压总压定义，不使用等熵总压关系；密度由边界p/T/Y联立状态方程得到。边界切换在un=0按外流处理，扩散通量由指定值或零梯度决定。

初始内部u=(0,0)m/s、p=100000Pa、T=2000K、Y=(0,0,1,0,0)，密度按状态方程；t=0边界优先于内部初值。高温氮气是明确的初态，不能替换为预混火焰或冷态。"""
        conditions = """| role | variable | location | operator | data键与物理含义 |
| --- | --- | --- | --- | --- |
| initial | velocity, temperature, pressure, mass_fractions | domain | assign | 各变量一条，value引用对应initial字段 |
| boundary | velocity, temperature, mass_fractions | fuel, air | dirichlet | 各入口各变量一条，value引用对应均匀入口字段 |
| boundary | pressure | fuel, air | normal_derivative | value=0 Pa/m |
| boundary | velocity | outlet | open_velocity | backflow_tangential_speed=0 m/s；按上文切换定义 |
| boundary | pressure | outlet | reservoir_total_pressure | p0=100000 Pa；按上文联立定义 |
| boundary | temperature | outlet | inlet_outlet | backflow_value=293 K；外流零法向梯度 |
| boundary | mass_fractions | outlet | inlet_outlet | backflow_value引用五分量氮气字段；外流零法向梯度 |
"""
        if advanced:
            tv = "nu_tilda" if advanced == "SA" else "turbulent_kinetic_energy, dissipation_rate"
            conditions += f"| initial | {tv} | domain | assign | value引用对应initial字段，数值见闭合定义 |\n"
            conditions += f"| boundary | {tv} | fuel, air | dirichlet | value引用入口字段，由闭合定义给定或计算后存数组 |\n"
            conditions += f"| boundary | {tv} | outlet | normal_derivative | value=0，单位为对应变量单位/m |\n"
        extra_outputs["mass_fractions"] = field("mass_fractions", "1", "components", [5], ["CH4", "O2", "N2", "CO2", "H2O"])
        if advanced == "SA":
            extra_outputs["nu_tilda"] = field("nu_tilda", "m2/s")
        if advanced == "KE":
            extra_outputs["turbulent_kinetic_energy"] = field("turbulent_kinetic_energy", "m2/s2")
            extra_outputs["dissipation_rate"] = field("dissipation_rate", "m2/s3")
        adapt = "入口只列CH4/O2/N2但配置含CO2/H2O，展开为五组分；补齐单位Le扩散和出口总压、回流定义；热态氮气初始条件按配置。用一致原子量推导分子量，调整CH4/H2O/CO2末位以保持元素和质量守恒，N2源严格0；NASA系数保留，比气体常数用一致分子量，NASA端侧外推定义保证数学自包含。"
        if advanced:
            adapt += " 明确平均流闭合、Prt=0.85/Sct=0.7和原缺失的无壁/湍化学定义；不承诺复现源软件隐式缺省。"
    elif family == "BernardCells":
        bottom = number(prompt, r"floor\) has a temperature of ([\d.]+)")
        top = number(prompt, r"ceiling\) has a temperature of ([\d.]+)")
        for k,v,u in [("bottom_temperature",bottom,"K"),("top_temperature",top,"K"),("reference_density",1,"kg/m3"),("reference_temperature",300,"K"),("expansion_coefficient",.001,"1/K"),("dynamic_viscosity",.001,"Pa.s"),("thermal_diffusivity",.001,"m2/s"),("heat_capacity",712,"J/(kg.K)"),("gravity_y",-9.81,"m/s2")]: add(k,v,u)
        title = "底部加热封闭腔的贝纳德对流"
        target = f"研究底面 {bottom:g} K、顶面 {top:g} K 的封闭腔内热浮力、黏性和热扩散的竞争及涡胞发展。"
        geometry = "域为0<x<9m、0<y<1m；floor为y=0，ceiling为y=1，side_walls为x=0及x=9，wall为这四边的并集。二维场在z不变，无前后壁面。温度角点按floor/ceiling定温，side_walls仅对其开边施加绝热。"
        model = """采用标准不可压缩Boussinesq层流模型：∇·u=0，∂tu+u·∇u=−∇π/ρ0+ν∇²u−β(T−T0)g，∂tT+u·∇T=α∇²T。ρ0=1 kg/m3，T0=300K，β=0.001/K，g=(0,−9.81)m/s2，ν=μ/ρ0=0.001m2/s，α=0.001m2/s，对应Pr=1。热容量取712J/(kg.K)，导热系数κ=ρ0 cp α=0.712W/(m.K)。除浮力外密度恒为ρ0；不求解声学、变密度质量输运、黏性发热、辐射或湍流。π=p−ρ0 g·x是扣除恒定参考密度静水压后的动力压力，单位Pa，每一时刻以域面积均值π=0固定规范；输出pressure即π，不输出绝对静压或源软件p_rgh。无额外体源，温差是唯一热驱动。"""
        bounds = f"""所有四壁无滑移u=0。floor温度T={bottom:g}K，ceiling温度T={top:g}K，side_walls为∂nT=0。压力法向梯度由动量方程与不可穿透条件一致确定，不额外指定绝对压力；域面积均值为0。

初始温度T=300K。初始速度由流函数ψ=1e-4 sin²(πx/9) sin²(πy) m2/s定义，u=(∂yψ,−∂xψ)；因此全域无散且四壁速度严格为0。该明确的小扰动替代不满足封闭域无穿透约束的均匀横流。不可压缩压力由约束求得，不将π=0初猜作为额外独立初始条件。"""
        conditions = """| role | variable | location | operator | data键与物理含义 |
| --- | --- | --- | --- | --- |
| initial | velocity, temperature | domain | assign | 各变量一条，value引用对应initial字段 |
| boundary | velocity | wall | dirichlet | value引用全0二维速度字段 |
| boundary | temperature | floor, ceiling | dirichlet | 各边一条，value为本题定温，单位K |
| boundary | temperature | side_walls | normal_derivative | value=0 K/m |
| boundary | pressure | wall | momentum_compatible | normal_speed=0 m/s；压力梯度由上文动量一致性定义 |
| source | pressure | domain | mean_gauge | value=0 Pa，表示每时刻域面积均值约束，不是质量或动量体源 |
"""
        adapt = "源heRhoThermo+Boussinesq明确限定成标准不可压缩Boussinesq，alpha=nu/Pr；将不相容均匀横流改为公开流函数生成的无散且无滑移相容扰动；修复wall组未在网格定义的问题，对全部四壁施加无滑移；压力改为明确定义的去静水压零均值规范，不宣称逐字复现源可压缩实现。"
    else:
        velocity = number(prompt, r"(?:fixed velocity of |inlet velocity is )([\d.]+)")
        temp = number(prompt, r"(?:temperature of |inlet temperature is )([\d.]+)")
        pr = number(entry["constant/physicalProperties"], r"Pr\s+([\d.]+)")
        for k,v,u in [("inlet_velocity_x",velocity,"m/s"),("inlet_temperature",temp,"K"),("inlet_pressure",1,"Pa"),("gas_constant",5/7,"J/(kg.K)"),("specific_heat_cp",2.5,"J/(kg.K)"),("dynamic_viscosity",0,"Pa.s"),("prandtl_number",pr,"1"),("source_molecular_weight",11640.3,"kg/kmol")]: add(k,v,u)
        model = GAS
        if family == "forwardStep":
            title = "可压缩气流越过前向台阶"
            target = f"研究入口速度{velocity:g}m/s的气流在前向台阶处产生的压缩波、激波及其反射。"
            geometry = "流体域为矩形(0,3)×(0,1)m去掉[0.6,3]×[0,0.2]m，边界依次为(0,0)、(0.6,0)、(0.6,0.2)、(3,0.2)、(3,1)、(0,1)。inlet是x=0整段，outlet是x=3且0.2<y<1，bottom是y=0且0<x<0.6，top是y=1，obstacle是台阶竖面及抬高底面。二维源挤出厚度0.1m不引入三维条件。正式输入域网格不超过17000个二维域单元；内部离散自由。"
            initial_u = velocity
            out = f"outlet：∂np=0；外流u·n≥0时∂nu=∂nT=0；倒流时u=({velocity:g},0)m/s、T=1K。"
            adapt = "原laminar配置mu=0，明确Euler；按配置补齐台阶几何、归一化气体、初态与倒流入口值。"
        else:
            title = "超声速气流与楔面斜激波"
            target = f"研究入口速度{velocity:g}m/s、温度{temp:g}K的气流遇到15度楔面的瞬态压缩与激波反射。Pr={pr:g}被保留为来源差异，但无黏模型下不改变解。"
            geometry = "二维流体多边形顶点依次为(−0.15242,0)、(0,0)、(0.3048,0.081670913853)、(0.3048,0.1524)、(−0.15242,0.1524)，单位m。inlet为x=−0.15242，outlet为x=0.3048，bottom为y=0且x<0，top为y=0.1524，obstacle为(0,0)至(0.3048,0.081670913853)的楔面（约15度）。源z∈[−0.005,0.005]仅二维挤出。正式输入域网格不超过4800个二维域单元；内部离散自由。"
            initial_u = 5
            out = "outlet：u、T、p均为零法向导数，包括瞬时倒流；不引入未声明的环境储槽。"
            adapt = "补齐15度楔面实际端点，源入口温度/速度变化但内部初值始终1K及5m/s，按配置保留；mu=0下Pr变体数学等价；用R=5/7替代近似0.7143且保留molWeight标签。"
        bounds = f"""inlet：u=({velocity:g},0)m/s，T={temp:g}K，p=1Pa。bottom、top、obstacle均为滑移不可穿透：u·n=0、∂nut=0、∂nT=∂np=0，ut是切向速度；无黏模型没有壁面摩擦和热通量。入口与壁面交点按入口状态，其他角点取相邻开边极限，输出点不设在角点。

{out}

初始内部u=({initial_u:g},0)m/s、T=1K、p=1Pa，ρ=p/(RT)，能量由状态方程；t=0边界优先。"""
        conditions = """| role | variable | location | operator | data键与物理含义 |
| --- | --- | --- | --- | --- |
| initial | velocity, temperature, pressure | domain | assign | 各变量一条，value引用对应initial字段 |
| boundary | velocity, temperature, pressure | inlet | dirichlet | 各变量一条；速度value引用二维field，T/p为带单位常数 |
| boundary | velocity | bottom, top, obstacle | slip | normal_speed=0 m/s，且切向速度零法向导数 |
| boundary | temperature, pressure | bottom, top, obstacle | normal_derivative | 各边各变量一条，value=0，单位K/m或Pa/m |
| boundary | pressure | outlet | normal_derivative | value=0 Pa/m |
"""
        if family == "forwardStep":
            conditions += "| boundary | velocity, temperature | outlet | inlet_outlet | backflow_value为出口location上的独立field、数值等于入口速度，或T=1K；不得引用入口location的field；外流零法向导数 |\n"
        else:
            conditions += "| boundary | velocity, temperature | outlet | normal_derivative | value=0，速度导数以显式二维field表达(m/s/m)，温度K/m |\n"
    return title, target, geometry, model, bounds, conditions, params, extra_outputs, adapt


def generate(key, entry, index, advanced=""):
    family = key.split("/")[0] if not advanced else "counterFlowFlame2D"
    slug = "fb-basic-" + key.replace("/", "-").lower() if not advanced else "fb-advanced-counterflowflame2d-" + advanced.lower()
    path = SECTION / slug
    path.mkdir(parents=True, exist_ok=True)
    (path / "author").mkdir(exist_ok=True)
    title,target,geometry,model,bounds,conditions,params,extra,adapt = details(family, entry["usr_requirement"], entry, advanced)
    modelid = "foambench-" + family.lower() + ("-" + advanced.lower() if advanced else "")
    end, interval = params["end_time"]["value"],params["output_interval"]["value"]
    count = round(end/interval)+1
    outputs = {"velocity": field("velocity","m/s","vector",[2],["x","y"]),"pressure":field("pressure","Pa"),"temperature":field("temperature","K"), **extra}
    instruction = f"""# 2.12.{index} {title}

{target}

实现一个读取本题输入包、输出指定物理时刻全场采样的求解程序。任务为二维瞬态，几何、物性、初边值条件和输出规范完整定义在 [DATA.md](DATA.md)，文件表示遵守 [通用数据协议](../../../../docs/CONTRACT.md)。本题固定的是物理模型和条件，语言、软件、离散方法、线性/非线性算法及内部固定或自适应时间步均由考生选择；无需安装或使用来源软件。

{geometry}

计算0至{end:g}s的物理演化，输出时刻t=j×{interval:g}s，j=0,…,{count-1}，共{count}帧。t=0也要求输出；时间轴是采样时刻，不是内部时间步或迭代次数。不得将本题改为只求最终稳态。

必须输出速度、压力、温度{('、五组分质量分数' if family=='counterFlowFlame2D' else '')}{('以及'+('SA修正运动黏度' if advanced=='SA' else '湍动能和耗散率') if advanced else '')}，按DATA规定的固定点、编号、分量及时间轴写入一个结果HDF5文件。输出是这些位置的点值；内部网格或算法不改变采样定义。

提交入口统一为 `solve.py`，每个算例以 `python solve.py --input /path/to/problem.json --output /path/to/result.h5` 调用。输入内所有相对文件路径以problem.json所在目录为基准，输出文件写到--output指定路径；成功退出码为0，日志不是答案。提交程序和依赖在评测前冻结，逐例运行不得联网获取数据、代码或依赖；程序须自行完成本题全部必需结果。

本阶段仅交付题面与契约草案，尚无可运行评测包。资源上限、数值容差、归一化与字段权重、参考构造及分数映射均未校准；发布前必须完整指定并验证，目前不提供分数或通过门槛。未来评价应比较上述物理场在固定采样位置和物理时刻的误差，并区分结构非法、求解失败与数值偏差；不能以来源软件运行成功、残差或文件格式合法代替数值正确。新模型声明检查尚未装配，不宣称现有工具已接受本题。
"""
    rows=[(k,v["value"],v["unit"]) for k,v in params.items()]
    data=f"""# 数据定义：{title}

## 范围与状态

本题是2.12.{index}的自包含接口定义。`task` 必须精确为 `{slug}`。采用 [CONTRACT](../../../../docs/CONTRACT.md) 的 `physics` 路径，不使用CFD profile。`physics.model` 必须精确为 `{modelid}`，`spatial_dimension=2`。此模型是文档契约草案，尚未装配领域声明检查、网格、HDF5或数值参考；以下文件与数组均为未来数据包要求，不表示当前目录已有可运行输入。

## 几何、方程与材料

{geometry}

{model}

`physics.parameters` 只允许下面列出的带单位有限标量；值固定为本移植变体，隐藏数据不得无声明更换物理参数。公式中的固定热化学/闭合系数按本页定义，不在JSON中存放多项式字符串、列表或可执行表达式。边界值在条件中明确存储，重复标量必须与表中一致。

{table(rows)}

## 初始、边界及源项

法向n始终指向域外，所有速度与向量按全局(x,y)顺序。边界在0至{end:g}s保持不变。除本页模型已定义的反应/浮力/闭合源外无其他源项。初始状态是瞬态起始条件，不是可任意改变的数值初猜。

{bounds}

## 文件、位置与采样

未来输入包包含 `problem.json`、Gmsh MSH 4.1 ASCII `mesh.msh`、`input.h5`，可选 `domain.geo`。路径相对problem.json，清单 `meshes.main.file=mesh.msh`；坐标为m，Gmsh第三坐标为0，网格拓扑二维。几何可由 `geometries.domain` 引用并由网格记录链接；实际离散以msh为准。`locations.domain` 是全部二维域单元，`kind=mesh, mesh=main, entity=element, dimension=2, ids=domain_ids`。每个条件边界名称在locations中定义为相应一维边单元集合，记录 `kind=mesh, mesh=main, entity=element, dimension=1, ids=<名称>_ids`，并以 `physical_group={{dimension:1,tag:整数}}` 显式绑定；domain绑定维度2组。组号在实际清单给出，不能靠组名称推断条件；并集wall或outlet可用单独Physical Group表示，同一边可属于多个组但不得产生矛盾条件。

输出 `locations.samples={{"kind":"points","ids":"sample_ids","coordinates":"sample_coordinates"}}`；sample_ids为非负严格递增int64[N]，sample_coordinates为float64[N,2]，全为流体内部固定点，不含边界、角点和固体。输出为点值，不是单元平均；激波恰过采样点时取该时刻求解场的熵解外侧极限，若两侧极限不同则取两侧算术平均。没有自动生成中心点或隐含网格顺序。所有mesh位置的ID为正严格递增int64；边界单元ID不是domain单元ID。

`time_axes.initial=initial_times`，initial_times为float64[1]=[0]；`time_axes.output=output_times`，output_times为float64[{count}]，第j项为j×{interval:g}s。输出时间与内部积分步长无关。没有统计平均或伪时间。时间轴由输入提供并在结果中逐值复制，不重算或重排。

初始场在domain单元上以 `value_kind=average` 存储，各单元的值严格为上文均匀内部初值；入口/边界数值场在相应边单元上同样为average。其空间采样 `sampling={{"space":"uniform","time":"constant","extrapolation":"hold"}}`，表示给定位置全部单元上的同一常值并在整个物理区间保持，不从相邻边或域外外推。均匀矢量和组分也必须以完整数组存储，禁止内联JSON数值列表或省略实体轴；均匀标量条件可用带单位常数。每个变量的初始字段命名 `initial_<变量>`，time_axis为initial；边界字段命名 `<边界>_<变量>`，time_axis也为initial，作为全时段常量使用。此命名表的变量由下列条件表逐项枚举；为constant表达的标量无需另造field。所有字段dtype=float64，标量component_shape=[1]/components=["value"]，速度[2]/["x","y"]，质量分数[5]/["CH4","O2","N2","CO2","H2O"]，单位与对应输出一致。

## 条件清单

每个表格中逗号列出的变量或位置均展开为独立条件记录，不在JSON键内塞逗号列表。每条记录恰含 `role,variable,operator,location,data`。数值常数写成 `{{"value":数值,"unit":"单位"}}`，字段引用 `{{"field":"字段对象名"}}`；data键列未标为可选的均必需，不接收其他算子或参数。value/backflow_value是数据参数名，不是未声明表达式。条件不依排列先后生效；初态和边界在t=0的相交点遵守前述优先规则。

{conditions}

域内全部常系数和显式公式源已由physics和本页方程定义，不额外添加material/source记录。mean_gauge（若出现）是以source角色承载的非局部规范约束，不是物理体源。momentum_compatible/open_velocity/slip等含无数据分支的算子仍须带表列的数值参数，避免用未知字段或空data暗示物理。

例如某均匀二维边界速度条件采用 `data={{"value":{{"field":"fuel_velocity"}}}}`，该field必须位于同一location；边界温度常数采用 `data={{"value":{{"value":293,"unit":"K"}}}}`。示例仅说明类型，实际变量、位置与数值以本题上述定义为准。标量0导数表示相应变量的零法向导数；矢量0导数必须引用显式二维零field，不将一个标量隐式广播为两个分量。

## 输出

`outputs` 必须逐项为下面结构，所有字段共用samples/output，T={count}、N=len(sample_ids)，无空间/时间重建或隐式轴。单位和quantity字符串由此固定，压力含义以模型段落为准。

```json
{json.dumps(outputs,ensure_ascii=False,indent=2)}
```

结果 `result.h5` 必须恰包含各输出array、sample_ids与output_times；float64场shape为[T,N,*component_shape]，IDs和时间的dtype/shape/值/顺序与输入完全一致。不写坐标、网格、初态、边界场、额外诊断或元数据。input.h5恰包含locations引用的IDs和坐标、time_axes数组、fields数组，不夹带未引用数据。上述全部条件、字段、ID与几何边界须在数据制作时交叉核验；通用结构检查不验证方程、模型闭合、网格分辨率或数值准确度。
"""
    if family == "BernardCells":
        data=data.replace('各单元的值严格为上文均匀内部初值','各单元的值严格为上文解析初态的单元平均')
        data=data.replace('其空间采样 `sampling=', '除下文单列的非均匀 initial_velocity 外，其余均匀输入场的空间采样 `sampling=')
        data += '\n初始速度的特殊采样规则：initial_velocity字段采用space=piecewise_constant、time=constant、extrapolation=hold，数组仅存储上述解析流函数速度的单元平均。连续物理初态由本页解析式唯一确定，不把单元平均重建成另一个分片常数初态；其余均匀输入场仍按uniform规则。\n'
    # Remove illustrative fuel condition in non-fuel problems; no irrelevant domain examples.
    if family != "counterFlowFlame2D":
        data=data.replace('fuel_velocity','inlet_velocity').replace('293,"unit":"K"','1,"unit":"K"')
        if family == "BernardCells":
            data=data.replace('inlet_velocity','wall_velocity').replace('1,"unit":"K"','300,"unit":"K"')
    (path/"instruction.md").write_text(instruction,encoding="utf-8")
    (path/"DATA.md").write_text(data,encoding="utf-8")
    provenance={"upstream_commit":UPSTREAM,"source_file":"FoamBench_advanced.json" if advanced else "FoamBench_basic.json","source_key":key,"source_entry_sha256":hashlib.sha256(json.dumps(entry,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()).hexdigest(),"original_prompt":entry["usr_requirement"],"adaptation":adapt,"numerical_controls":"原deltaT/Co/软件与算法不约束考生；保留物理输出时刻。","stage":"statements-only; no data/reference/judge calibration"}
    (path/"author/source.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return slug


if __name__ == "__main__":
    basic=read_source('basic')
    advanced=read_source('advanced')
    slugs=[generate(k,v,i) for i,(k,v) in enumerate(list(basic.items())[40:80],41)]
    slugs += [generate("counterFlowFlame2D_SA",advanced["counterFlowFlame2D_SA"],116,"SA"),generate("counterFlowFlame2D_KE",advanced["counterFlowFlame2D_KE"],120,"KE")]
    assert len(slugs)==42 and len(set(slugs))==42
    print("Generated",len(slugs),"statement/DATA/source triples")
