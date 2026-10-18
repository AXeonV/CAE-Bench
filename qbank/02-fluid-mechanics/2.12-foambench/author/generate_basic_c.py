"""Rebuild only basic source items 81--110; creates statements, never case data."""
from pathlib import Path
import hashlib
import json
import re
from source_snapshot import read_source

ROOT = Path(__file__).resolve().parents[4]
SECTION = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runs/foambench-import/FoamBench_basic.json'
COMMIT = 'e37e8b61fbb1f3532dcfd2f2e8ab67e7c91c3ee2'


def num(text):
    return float(text)


def fmt(value):
    return f'{value:.12g}'


def scalar(value, unit):
    return {'value': value, 'unit': unit}


def field(quantity, unit, location, axis, vector=False):
    return dict(array=quantity, quantity=quantity, location=location,
                time_axis=axis, dtype='float64', kind='vector' if vector else 'scalar',
                component_shape=[2] if vector else [1],
                components=['x', 'y'] if vector else ['value'], unit=unit,
                value_kind='average')


COMMON = '''## 文件与空间身份

本说明与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、评分与资源见[题面](instruction.md)。输入包由 `problem.json`、其引用的一个 Gmsh MSH 4.1 ASCII 网格和一个扁平 HDF5 文件组成；可附 `.geo` 几何。路径以清单所在目录为基准。这里只定义格式，不提供实际输入包。

`spatial_dimension=2`，全部坐标采用 m、时间采用 s，网格位于全局 xy 平面，z=0。`meshes.main` 引用网格；`locations.domain` 是 `kind=mesh, mesh=main, entity=element, dimension=2, ids=cell_ids`，恰含全部流体二维单元。网格使用一阶三角形或四边形。边界按下文位置名给出 `entity=element,dimension=1` 的线段 location，`ids` 为对应位置名加 `_ids`，各组不重叠且恰好覆盖外边界。location 还须声明真实 Gmsh `physical_group` 的维度和 tag；名称不代替编号。流体域组为二维，其余组为一维。所有 IDs 为严格递增、无重复的 int64；单元 tag 是身份，不是数组下标。外法向始终指向流体域外，内孔法向指向孔内。

输入和输出的域字段均为该二维单元的面积平均值，`value_kind=average`；边界字段为该线段的长度平均值。向量按 x、y 顺序。标量统一 `[T,N,1]`、`kind=scalar,component_shape=[1],components=["value"]`；向量统一 `[T,N,2]`、`kind=vector,component_shape=[2],components=["x","y"]`。全部物理场 dtype=float64，值有限，禁止省略时间轴或分量轴。不得用单元中心点值冒充面积平均。

## 声明与采样

本题使用通用 `physics` 声明；不写 `profile`、`analysis`、`materials` 或 `contract_version`。模型标识、参数和条件由下文完整定义。参数均为 `{ "value":有限标量,"unit":"指定代码" }`，不允许内联向量或隐式单位转换。

`time_axes.initial=initial_times` 对应 `[0]`；`time_axes.constant=constant_times` 对应 `[0]`；`time_axes.result=result_times` 对应下文物理输出时刻，数组均为严格递增 float64 一维数组。不同轴使用不同 key。初始场仅在 t=0 赋值，常量场在整个物理区间恒定，不能把初态当作后续强制解。每个输入字段显式声明 `sampling={"space":"piecewise_constant","time":"constant","extrapolation":"hold"}`：每个单元／边界线段上常值，时间上恒定延拓；初态的延拓只用于读取初值。连续初态与本说明的解析定义一致；数值更新不得把该常值重建误认为额外物理界面。

每个输入字段名和 array key 相同，quantity 为下文所列物理量；location 与引用条件完全一致，time_axis 为 initial 或 constant。每个字段只承担所列角色。初态以 `role=initial,operator=assign,location=domain` 声明，variable 为相应物理量，`data={"value":{"field":"字段名"}}`。不允许以初猜替代物理初态。

边界条件均 `role=boundary`。`dirichlet` 表示强制变量等于给定值，data 仅含 value；标量采用 `{value,unit}` 常量，向量必须引用该边界上的显式场。`normal_derivative` 表示各分量向外法向导数为零，data 仅含 `mode:{"option":"zero"}`。`slip` 表示法向分量为零、切向分量的法向导数为零，data 仅含 `mode:{"option":"impermeable"}`。条件在 t>0 生效；起点初态在内部成立，边界突加驱动允许与初态存在瞬时不相容。边界线段端点按相邻线段各自的迹解释，不给端点重复自由度设置相互冲突的值。

输入 HDF5 恰含全部 location IDs、三条时间轴与 fields 数组，无额外数组、属性或子组。实际文件名由清单 `data_file` 给出，建议 `input.h5`。
'''


def emit(i, key, case):
    family, variant = key.split('/')
    slug = f'fb-basic-{family.lower()}-{variant}'
    directory = SECTION / slug
    directory.mkdir(parents=True, exist_ok=True)
    prompt = case['usr_requirement']
    sw = family == 'shallowWaterWithSquareBump'
    cavity = family == 'Cavity'
    if sw:
        H = num(re.search(r'water depth of ([\d.]+)', prompt)[1])
        title = f'方形浅水床突起：初始自由面 {fmt(H)} m'
        params = {'gravity': scalar(9.81, 'm/s2'), 'rotation_rate': scalar(7.292e-5, '1/s'),
                  'initial_surface': scalar(H, 'm'), 'inlet_flux': scalar(.001, 'm2/s'),
                  'outlet_depth': scalar(.01, 'm'), 'bump_height': scalar(.001, 'm'),
                  'start_time': scalar(0, 's'), 'end_time': scalar(100, 's')}
        physical = f'''在 1 m × 1 m 水平区域中计算单层浅水流经过中央方形床突起后的非定常响应。床突起范围为 0.45≤x≤0.55、0.45≤y≤0.55 m，高 0.001 m，其余床面高程为零。初始自由面严格平坦，η={fmt(H)} m；初始速度严格均匀，为 ({fmt(.001/H)},0) m/s，因此突起外 h={fmt(H)} m、q=(0.001,0) m²/s，突起上 h={fmt(H-.001)} m、q=({fmt(.001*(H-.001)/H)},0) m²/s。q=h u 是单位宽度体积流量，不是速度或质量动量。

保留重力 9.81 m/s² 和绕竖直轴角速度 7.292×10⁻⁵ s⁻¹ 的科氏力。左边界给定 q=(0.001,0) m²/s，右边界水深固定为 0.01 m；其余边界和变量的条件见 DATA。物理区间为 0≤t≤100 s，输出 t=0,1,…,100 s 的水深与流量。床面台阶需要符合 DATA 给出的静水源项解释。'''
        details = f'''## 本题模型、地形与初态

`physics.model="foambench-shallowWaterWithSquareBump"`，parameters 精确为：

```json
{json.dumps(params, ensure_ascii=False, indent=2)}
```

上述数值均固定。domain 的几何为 [0,1]×[0,1] m²；位置 inlet 为 x=0，outlet 为 x=1，sides 为 y=0 与 y=1 的并集。二维网格须沿方形突起的四条边分区，使任一单元内部床高 b 不跳变。原始薄片厚度 0.1 m 仅用于二维实现，不是水深，不参与水平面积、流量或体积的计算。

采用不可压、静水压、无底摩擦、无黏性扩散的单层旋转浅水模型，u=q/h，η=h+b，g=gravity，f=2 rotation_rate。守恒方程为 ∂t h+∇·q=0，∂t q+∇·(q⊗q/h+g h²I/2)=−g h∇b−f Jq，其中 J(qx,qy)=(−qy,qx)。无风、降水、渗漏或其他源。要求水深非负；出现水力跃变时取耗散机械能的熵解。固定床台阶源项采用静水路径：同一界面两侧将自由面 η 与床高 b 作线性路径连接、h=η−b，因此床源跳跃积分为 −g(hL+hR)(bR−bL)n/2；不是把台阶当成固体障碍侧壁。

fields 必须包含：`bed`（quantity=bed，m，scalar，domain，constant）、`initial_depth`（quantity=depth，m，scalar，domain，initial）、`initial_flux`（quantity=water_flux，m2/s，vector，domain，initial）、`inlet_flux`（quantity=water_flux，m2/s，vector，inlet，constant）。bed 在突起内为 0.001 m、外部为零；初态严格为 h={fmt(H)}−b、q=(0.001 h/{fmt(H)},0)，以此精确关系为准，不能使用来源文件中遗留的统一 0.009 m 或 0.0009 m²/s，也不把原 prompt 的小数截断当作额外扰动。自由面初始高度不意味着出口深度改为 {fmt(H)} m；右侧 t>0 一律为 0.01 m。

bed 使用 `role=material,variable=bed,operator=assign,location=domain,data={{"value":{{"field":"bed"}}}}`，表示固定床高而非材料黏度。两个初态各有一次 initial/assign 条件。

## 边界条件集合

下表每行必须出现一次；除列出条件外无其他物理边界。data 的键精确固定，表示法向导数零的模式按前文定义。

| location | variable | operator | data |
|---|---|---|---|
| inlet | depth | normal_derivative | mode=option(zero) |
| inlet | water_flux | dirichlet | value=field(inlet_flux)，每条线段值均 (0.001,0) m2/s |
| outlet | depth | dirichlet | value=常量 0.01 m |
| outlet | water_flux | normal_derivative | mode=option(zero) |
| sides | depth | normal_derivative | mode=option(zero) |
| sides | water_flux | slip | mode=option(impermeable) |

这些是固定值／梯度边界条件，不隐含储槽 Riemann 边界或随流向自动切换。初态与出口可能不相容，产生的瞬态属于任务。
'''
        quantities = [('depth','m',False),('water_flux','m2/s',True)]
        times = 't=0,1,…,100 s（101 帧）'
        adaptation = ['原prompt优先：平自由面与均匀速度以精确关系定义，修正非variant1配置遗留的bump h=.009,q=.0009；hTotal为派生量不独立输入。',
                      '从配置补全旋转、重力、出入口与滑移；出口固定.01m，不随初态改动。',
                      '二维去除实现厚度，固定静水路径解释台阶；网格数量、求解器名、时间步不作为物理约束。']
    else:
        speed = num(re.search(r'uniform velocity of ([\d.]+)',prompt)[1] if cavity else re.search(r'fixed velocity of ([\d.]+)',prompt)[1])
        nu = num(re.search(r'value of (\S+) m\^2/s',prompt)[1] if cavity else re.search(r'nu value of (\S+) in',prompt)[1])
        params = {'density':scalar(1,'kg/m3'),'nu':scalar(nu,'m2/s'),'drive_speed':scalar(speed,'m/s'),
                  'start_time':scalar(0,'s'),'end_time':scalar(10 if cavity else .5,'s')}
        if cavity:
            params.update({k:scalar(v,'1') for k,v in [('Cmu',.09),('C1',1.44),('C2',1.92),('sigma_k',1),('sigma_epsilon',1.3),('kappa',.41),('E',9.8)]})
            title = f'湍流顶盖腔流：U={fmt(speed)} m/s，ν={fmt(nu)} m²/s'
            physical = f'''计算边长 0.1 m 的正方形腔体中的不可压、等温非定常顶盖驱动流。上壁沿 +x 方向以 {fmt(speed)} m/s 运动，其余三壁静止且无滑移。运动黏度 ν={fmt(nu)} m²/s；必须采用标准 k–ε 雷诺平均闭合及 DATA 明确的壁面函数。初始内部速度为零，k=0.00375 m²/s²、ε=0.00754 m²/s³。涡黏度由 k–ε 闭合确定。

物理区间为 0≤t≤10 s，输出每 0.5 s 的速度、静压、k 和 ε。源几何的整体 0.1 缩放已计入上述 0.1 m 边长；不再采用单位边长。'''
            geom = 'domain 为 [0,0.1]×[0,0.1] m²。movingWall 为 y=0.1，fixedWalls 为其余三壁的并集。源薄片缩放后的出平面厚度 0.01 m 是二维实现厚度，已消除；不乘入二维平均和积分。'
            closure = '''标准 k–ε 闭合为 νt=Cmu k²/ε，Pk=2νt S:S，S=(∇u+∇uᵀ)/2；∂t k+u·∇k=∇·[(ν+νt/sigma_k)∇k]+Pk−ε；∂t ε+u·∇ε=∇·[(ν+νt/sigma_epsilon)∇ε]+C1(ε/k)Pk−C2 ε²/k。无浮力、压缩性或低雷诺数附加修正。νt 由给定 k、ε 及闭合关系确定，不是独立物理初态。k、ε 均保持正；本题不授权变更模型以迎合某个标称雷诺数。

壁面函数作如下明确解释，避免依赖软件专有名：k 为零法向导数；设邻壁单元面积平均值为 kP、单元面积质心距该壁线段所在直线的垂距为 d，uτ=Cmu^(1/4)√kP，y+=uτ d/ν。取正根 yL≈11.53 满足 yL=ln(E yL)/kappa。壁面 νtw 在 y+≤yL 时为零，在 y+>yL 时为 max(0,ν[kappa y+/ln(E y+)−1])。邻壁 ε 在低支为 2νkP/d²，高支为 Cmu^(3/4)kP^(3/2)/(kappa d)。高支的邻壁生产率 Pk=(ν+νtw)|∂n u|uτ/(kappa d)，低支为零；该邻壁约束覆盖 ε 输运和 Pk 的内部表达式。多个壁段邻接同一单元时，对各段贡献等权平均；ε 壁面迹取所得邻壁值。此壁函数距离由给定物理网格确定，不是可调模型参数。求解可采用不同内部离散，但须保持该近壁解释。上盖端点与侧壁只按各自边迹施加，不请求角点输出。'''
            inputs = '''`initial_velocity`（velocity，m/s，vector，domain，initial，全零）、`initial_pressure`（pressure，Pa，scalar，domain，initial，全零）、`initial_k`（turbulent_k，m2/s2，scalar，domain，initial，0.00375）、`initial_epsilon`（turbulent_epsilon，m2/s3，scalar，domain，initial，0.00754），以及 `lid_velocity`（velocity，m/s，vector，movingWall，constant）和 `fixed_velocity`（velocity，m/s，vector，fixedWalls，constant）。'''
            boundary = f'''| movingWall | velocity | dirichlet | value=field(lid_velocity)，({fmt(speed)},0) m/s |
| fixedWalls | velocity | dirichlet | value=field(fixed_velocity)，(0,0) m/s |
| movingWall、fixedWalls（各一次） | pressure | normal_derivative | mode=option(zero) |
| movingWall、fixedWalls（各一次） | turbulent_k | normal_derivative | mode=option(zero) |
| movingWall、fixedWalls（各一次） | turbulent_epsilon | epsilon_wall | mode=option(standard) |
| movingWall、fixedWalls（各一次） | turbulent_viscosity | nut_wall | mode=option(standard) |

`epsilon_wall` 和 `nut_wall` 精确表示前文壁面函数；data 仅含 mode，值仅允许 standard。压力无 Dirichlet 约束，每个时刻将压力平移到全域面积加权平均为零，作为输出唯一基准；不沿用来源“第0单元”的网格依赖基准。'''
            quantities = [('velocity','m/s',True),('pressure','Pa',False),('turbulent_k','m2/s2',False),('turbulent_epsilon','m2/s3',False)]
            times='t=0,0.5,…,10 s（21 帧）'
            adaptation=['保留prompt指定k-epsilon和壁函数，公开列出系数及OpenFOAM 10式分支近壁语义；不暴露无关omega/nuTilda输入。',
                        '整体缩放后边长.1m；源第0单元压力改为逐时全域面积均值零，消除网格编号基准依赖。',
                        '源nut=0只是派生字段存储初始化，不迁移成独立物理初态；原每100步输出转为物理.5s间隔；改用rho=1 kg/m3下机械静压Pa输出。']
        else:
            params.update(nuInf=scalar(10,'m2/s'),cross_time=scalar(.4,'s'),cross_exponent=scalar(3,'1'))
            title=f'偏置圆柱广义牛顿绕流：U={fmt(speed)} m/s，ν₀={fmt(nu)} m²/s'
            physical=f'''计算矩形通道内偏置圆柱附近不可压、等温的非定常层流。矩形范围为 −5≤x≤5、−1.5≤y≤2.5 m，剔除以原点为圆心、半径 1 m 的圆盘。入口 x=−5 给定 ({fmt(speed)},0) m/s，出口 x=5 静压为零、速度法向导数为零；上下壁与圆柱均静止且无滑移。内部初始速度和静压均为零。

采用 Cross 广义牛顿运动黏度，零剪切黏度 ν₀={fmt(nu)} m²/s、无限剪切黏度 ν∞=10 m²/s、时间常数 0.4 s、指数 3；本题这些参数产生剪切增稠，不可自动交换两端黏度，也不可把基础 ν₀ 当作全程恒定黏度。物理区间为 0≤t≤0.5 s，每 0.05 s 输出速度和静压。'''
            geom='domain 为矩形 [−5,5]×[−1.5,2.5] m² 减去闭圆盘 x²+y²≤1 m²。位置 left 为 x=−5，right 为 x=5，up 为 y=2.5，down 为 y=−1.5，cylinder 为圆周。内孔用真实圆弧几何建模，网格边界是其离散表示；源出平面 −1≤z≤1 m 的薄片已化为二维，无端面边界和端面摩擦。'
            closure='''无湍流闭合，νeff=νC。令 γdot=√(2 S:S)，S=(∇u+∇uᵀ)/2，νC=nuInf+(nu−nuInf)/[1+(cross_time γdot)^cross_exponent]。parameters.nu 明确是零剪切运动黏度 ν₀，不是另一层恒定黏度；源配置的基础 constant 属性与广义牛顿模型合成后仅采用该 Cross 公式。γdot 单位 1/s，cross_time 单位 s，νC 单位 m2/s；应力除以密度为 2νC S。无黏度截断、屈服应力或附加输运方程。'''
            inputs=f'''`initial_velocity`（velocity，m/s，vector，domain，initial，全零）、`initial_pressure`（pressure，Pa，scalar，domain，initial，全零），`inlet_velocity`（velocity，m/s，vector，left，constant，值 ({fmt(speed)},0)），以及 `up_velocity`、`down_velocity`、`cylinder_velocity`（均 quantity=velocity，m/s，vector，分别在同名边界，constant，值全零）。'''
            boundary='''| left | velocity | dirichlet | value=field(inlet_velocity) |
| right | velocity | normal_derivative | mode=option(zero) |
| right | pressure | dirichlet | value=常量 0 Pa |
| left、up、down、cylinder（各一次） | pressure | normal_derivative | mode=option(zero) |
| up、down、cylinder（各一次） | velocity | dirichlet | value=field(对应的 up_velocity、down_velocity、cylinder_velocity) |

出口只执行上述固定值／梯度条件，不隐含应力自由边界或自动反流切换。压力基准由出口 p=0 唯一固定，不再减去全域均值。'''
            quantities=[('velocity','m/s',True),('pressure','Pa',False)]
            times='t=0,0.05,…,0.5 s（11 帧）'
            adaptation=['从blockMesh补全偏置矩形与半径1圆柱，二维化去除源z厚度2m。',
                        'Cross动量输运优先于基础constant标签；基础nu解释为nu0，公开完整Cross公式，保留nuInf大于nu0的增稠参数。',
                        '保留初态、压力出口及全部壁条件；rho=1 kg/m3下静压Pa替代来源运动学压力；不迁移PIMPLE、网格上限1800或数值时间步为物理要求。']
        details=f'''## 本题模型、参数与几何

`physics.model="foambench-{family}"`，parameters 精确为：

```json
{json.dumps(params,ensure_ascii=False,indent=2)}
```

所有数值固定。{geom}

本题速度是不可压连续介质速度；压力输出为机械静表压 p，单位 Pa；固定密度 ρ=density=1 kg/m3，零点是本题所定表压基准，不是绝对真空。采用 ∇·u=0，∂t u+u·∇u=−∇p/ρ+∇·[2νeff S]；无重力、旋转、热输运或其他体力。{'νeff=ν+νt；p 是机械静压，动量方程中额外包含 −∇(2k/3)，不能把 p+2ρk/3 这一吸收各向同性湍流应力的修正压力直接作为 p 输出。' if cavity else ''}

{closure}

## 输入场与条件集合

fields 必须且仅包含：{inputs}

除边界速度字段外，每个 initial 字段恰有一条 initial/assign 条件，variable 为括号中的 quantity；条件 data.value 引用相应字段。所有初态是给定物理状态。边界场恒定于整个区间。下表中列出多个 location 时，必须逐一独立声明记录，不以字符串并集代替 location。

| location | variable | operator | data |
|---|---|---|---|
{boundary}
'''
    output_fields={q:field(q,u,'domain','result',v) for q,u,v in quantities}
    output = f'''## 输出

`outputs` 必须且仅含下列对象；完整元数据如下，不在结果文件中重复存元数据。所有输出均为 domain 单元面积平均。输出物理时刻精确为 {times}，不是迭代编号；内部时间步自由选择。

```json
{json.dumps(output_fields,ensure_ascii=False,indent=2)}
```

提交一个结果 `.h5`，恰含上述输出对象的 array key、`cell_ids`、`result_times`。IDs 和时间数组逐值、逐序复制输入；不导出边界 IDs、初态、常量时间轴、坐标或网格。初态帧按给定初态面积平均填入；压力同时遵守本题压力基准。结果 HDF5 写到题面规定命令行的 `--output` 路径。

## 支持状态

本文定义使用通用协议可表达的本题声明；本题模型的专用声明检查、公开运行工具、输入数据、数值参考和评分器尚未装配。通用结构检查不能验证上述物理条件或解的正确性。此阶段没有可运行的正式评测包。
'''
    instruction=f'''# 2.12.{i} {title}

{physical}

考生应实现读取输入声明、网格和字段并生成规定输出的求解程序。模型、边界、初态、坐标、压力定义和时间语义由[DATA.md](DATA.md)完整给出，文件结构遵循[通用数据协议](../../../../docs/CONTRACT.md)。必须保持这里指定的物理模型及闭合；数值离散、语言、软件、网格内部处理和求解算法可自主选择，不要求使用特定 CFD 软件。不能仅返回初态或以稳态解替代时间序列。

统一提交入口为 `python solve.py --input /path/to/problem.json --output /path/to/result.h5`。程序读取 `--input` 指定的清单，清单内相对路径均相对该 `problem.json` 所在目录解析，不能依赖当前工作目录。成功完成时退出码为 0；所有答案写入 `--output` 指定的 HDF5，标准输出和标准错误仅作日志，不作为答案。所有依赖在提交冻结前准备，每次调用独立处理一个算例，运行期间不得访问网络。该入口是提交契约，本题数据和判题装配仍处于未完成阶段。

评价目标是规定时刻、规定单元上的{'水深与单位宽度流量' if sw else '速度、静压及指定湍流状态' if cavity else '速度与静压'}。当前交付为题面与数据契约，尚无数据、独立参考或误差校准；评分公式、数值容差、通过阈值及 CPU、内存、墙钟时间和提交大小限制均未发布。数据就绪、工具装配、数值验证和正式评测不得由文档存在推定。
'''
    (directory/'instruction.md').write_text(instruction,encoding='utf-8')
    (directory/'DATA.md').write_text(f'# 2.12.{i} 数据说明\n\n`task` 固定为 `{slug}`。\n\n'+COMMON+'\n'+details+'\n'+output,encoding='utf-8')
    (directory/'author').mkdir(exist_ok=True)
    metadata=dict(source_repository='https://github.com/NLR-Theseus/cfdllmbench',upstream_commit=COMMIT,
                  source_file='FoamBench/Dataset/FoamBench_basic.json',source_key=key,source_ordinal=i,
                  original_prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                  consulted_keys=[k for k in case if k=='usr_requirement' or k.startswith('constant/') or k.startswith('0/') or k in ['system/blockMeshDict','system/setFieldsDict','system/controlDict','system/fvSolution']],
                  adaptation=adaptation,status='statements-only; no data, reference, runtime contract or grading calibration')
    (directory/'author/source.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return dict(number=f'2.12.{i}',slug=slug,key=key,parameters=params)


if __name__=='__main__':
    source=read_source('basic')
    rows=[emit(i,k,c) for i,(k,c) in enumerate(source.items(),1) if 81<=i<=110]
    assert len(rows)==30
    report='''# Basic 81–110 题面迁移设计记录

本批固定按 basic JSON 插入顺序保留 shallowWaterWithSquareBump、Cavity、Cylinder 各十题。仅交付中文题面、逐题 DATA 与轻量来源记录，不制作网格、HDF5、参考、判题配置或运行器。独立设计／考生审阅由上级任务统一协调，本记录不冒称已通过。

已逐族读完整 prompt，逐题提取初始深度、驱动速度与黏度；核读全部条件、材料、几何、setFields 和物理时刻配置。复用实际通用 physics/conditions 协议，未往 CFD profile 添加未知键。输入采用 Gmsh 实体身份与 HDF5 显式场，输出采用给定单元面积平均值。

## 改编与冲突

- 浅水：所有题保留0.001m中央方形床突起、0.001m2/s左边界流量、.01m右边界水深、旋转与滑移。除variant1外原setFields中的突起初态未随prompt调整；公开以平自由面与均匀速度精确关系覆盖遗留值，不隐藏冲突。hTotal是派生量，不另解。采用公开静水路径给出床台阶解释；尚无数值参考验证此选择与原离散结果的差别。
- 腔流：使用缩放后0.1m边长，保留k–epsilon而非以低雷诺数擅改层流。去除不被模型消费的omega与nuTilda。源nut=0属于派生字段存储初始化，不迁移成公开独立物理初态。明确标准系数与低／高y+壁函数含义；压力由源第0单元归零改为全域面积均值零，避免编号依赖。输出机械静压Pa（取rho=1 kg/m3），动量方程显式包含各向同性湍流应力；来源运动学压力需作对应转换。
- 圆柱：从几何配置补全x∈[−5,5]、y∈[−1.5,2.5]、原点半径1m孔。基础constant nu作为Cross的nu0，不覆盖广义牛顿模型；nuInf=10大于nu0保持不变，公开说明剪切增稠。端面为二维实现痕迹，去除厚度2m。
- 求解器名称、PISO/PIMPLE、离散网格数和内部时间步不迁移成物理或算法要求；输出间隔转成秒，资源未校准不伪造限制。

## 壁函数依据

用于核对源码专有名的主来源为 [OpenFOAM 10 epsilonWallFunction](https://github.com/OpenFOAM/OpenFOAM-10/blob/master/src/MomentumTransportModels/momentumTransportModels/derivedFvPatchFields/wallFunctions/epsilonWallFunctions/epsilonWallFunction/epsilonWallFunctionFvPatchScalarField.C)。本题公开给出其分支公式和角单元贡献解释，不要求考生读源码。原始FOAMBench来源身份以总任务核准仓库为准，commit和源key逐题固定。

## 覆盖清单

| 题号 | 源key | 参数（带单位） |
|---|---|---|
'''
    for r in rows:
        report+=f"| {r['number']} | {r['key']} | "+'; '.join(f"{k}={v['value']} {v['unit']}" for k,v in r['parameters'].items())+' |\n'
    report+='\n## 已执行核查与边界\n\n30题双文件与30条source记录均存在；逐题核对编号、源key、源prompt SHA-256、仓库URL及120条本地链接，JSON片段均可解析。对每族配置全键哈希分组，确认几何、物理边界、模型及时间配置在族内一致，变化范围为本清单保留的深度或速度/黏度。节静态检查通过（扫描题量随其他并行批次增加，结果见runs/foambench-import/static-basic-c.json）。统一提交入口、相对路径解析、退出码、日志、预冻结依赖和逐例无网络要求已逐题写入题面。\n\n上述仅证明文档结构、链接及源差异覆盖；未产生实际数据或fixture，未执行数值求解、物理专用校验器、独立公开包安装或评分/资源校准，不代表数值正确或评测可运行。独立审阅由总任务接续。\n'
    (SECTION/'author/design-basic-c.md').write_text(report,encoding='utf-8')
    print(f'Wrote {len(rows)} statement pairs and source records')
