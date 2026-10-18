# 2.12.96 数据说明

`task` 固定为 `fb-basic-cavity-4`。

## 文件与空间身份

本说明与[通用数据协议](../../../../docs/CONTRACT.md)共同定义输入输出；任务、评分与资源见[题面](instruction.md)。输入包由 `problem.json`、其引用的一个 Gmsh MSH 4.1 ASCII 网格和一个扁平 HDF5 文件组成；可附 `.geo` 几何。路径以清单所在目录为基准。这里只定义格式，不提供实际输入包。

`spatial_dimension=2`，全部坐标采用 m、时间采用 s，网格位于全局 xy 平面，z=0。`meshes.main` 引用网格；`locations.domain` 是 `kind=mesh, mesh=main, entity=element, dimension=2, ids=cell_ids`，恰含全部流体二维单元。网格使用一阶三角形或四边形。边界按下文位置名给出 `entity=element,dimension=1` 的线段 location，`ids` 为对应位置名加 `_ids`，各组不重叠且恰好覆盖外边界。location 还须声明真实 Gmsh `physical_group` 的维度和 tag；名称不代替编号。流体域组为二维，其余组为一维。所有 IDs 为严格递增、无重复的 int64；单元 tag 是身份，不是数组下标。外法向始终指向流体域外，内孔法向指向孔内。

输入和输出的域字段均为该二维单元的面积平均值，`value_kind=average`；边界字段为该线段的长度平均值。向量按 x、y 顺序。标量统一 `[T,N,1]`、`kind=scalar,component_shape=[1],components=["value"]`；向量统一 `[T,N,2]`、`kind=vector,component_shape=[2],components=["x","y"]`。全部物理场 dtype=float64，值有限，禁止省略时间轴或分量轴。不得用单元中心点值冒充面积平均。

## 声明与采样

本题使用通用 `physics` 声明；不写 `profile`、`analysis`、`materials` 或 `contract_version`。模型标识、参数和条件由下文完整定义。参数均为 `{ "value":有限标量,"unit":"指定代码" }`，不允许内联向量或隐式单位转换。

`time_axes.initial=initial_times` 对应 `[0]`；`time_axes.constant=constant_times` 对应 `[0]`；`time_axes.result=result_times` 对应下文物理输出时刻，数组均为严格递增 float64 一维数组。不同轴使用不同 key。初始场仅在 t=0 赋值，常量场在整个物理区间恒定，不能把初态当作后续强制解。每个输入字段显式声明 `sampling={"space":"piecewise_constant","time":"constant","extrapolation":"hold"}`：每个单元／边界线段上常值，时间上恒定延拓；初态的延拓只用于读取初值。连续初态与本说明的解析定义一致；数值更新不得把该常值重建误认为额外物理界面。

每个输入字段名和 array key 相同，quantity 为下文所列物理量；location 与引用条件完全一致，time_axis 为 initial 或 constant。每个字段只承担所列角色。初态以 `role=initial,operator=assign,location=domain` 声明，variable 为相应物理量，`data={"value":{"field":"字段名"}}`。不允许以初猜替代物理初态。

边界条件均 `role=boundary`。`dirichlet` 表示强制变量等于给定值，data 仅含 value；标量采用 `{value,unit}` 常量，向量必须引用该边界上的显式场。`normal_derivative` 表示各分量向外法向导数为零，data 仅含 `mode:{"option":"zero"}`。`slip` 表示法向分量为零、切向分量的法向导数为零，data 仅含 `mode:{"option":"impermeable"}`。条件在 t>0 生效；起点初态在内部成立，边界突加驱动允许与初态存在瞬时不相容。边界线段端点按相邻线段各自的迹解释，不给端点重复自由度设置相互冲突的值。

输入 HDF5 恰含全部 location IDs、三条时间轴与 fields 数组，无额外数组、属性或子组。实际文件名由清单 `data_file` 给出，建议 `input.h5`。

## 本题模型、参数与几何

`physics.model="foambench-Cavity"`，parameters 精确为：

```json
{
  "density": {
    "value": 1,
    "unit": "kg/m3"
  },
  "nu": {
    "value": 0.001,
    "unit": "m2/s"
  },
  "drive_speed": {
    "value": 1.5,
    "unit": "m/s"
  },
  "start_time": {
    "value": 0,
    "unit": "s"
  },
  "end_time": {
    "value": 10,
    "unit": "s"
  },
  "Cmu": {
    "value": 0.09,
    "unit": "1"
  },
  "C1": {
    "value": 1.44,
    "unit": "1"
  },
  "C2": {
    "value": 1.92,
    "unit": "1"
  },
  "sigma_k": {
    "value": 1,
    "unit": "1"
  },
  "sigma_epsilon": {
    "value": 1.3,
    "unit": "1"
  },
  "kappa": {
    "value": 0.41,
    "unit": "1"
  },
  "E": {
    "value": 9.8,
    "unit": "1"
  }
}
```

所有数值固定。domain 为 [0,0.1]×[0,0.1] m²。movingWall 为 y=0.1，fixedWalls 为其余三壁的并集。源薄片缩放后的出平面厚度 0.01 m 是二维实现厚度，已消除；不乘入二维平均和积分。

本题速度是不可压连续介质速度；压力输出为机械静表压 p，单位 Pa；固定密度 ρ=density=1 kg/m3，零点是本题所定表压基准，不是绝对真空。采用 ∇·u=0，∂t u+u·∇u=−∇p/ρ+∇·[2νeff S]；无重力、旋转、热输运或其他体力。νeff=ν+νt；p 是机械静压，动量方程中额外包含 −∇(2k/3)，不能把 p+2ρk/3 这一吸收各向同性湍流应力的修正压力直接作为 p 输出。

标准 k–ε 闭合为 νt=Cmu k²/ε，Pk=2νt S:S，S=(∇u+∇uᵀ)/2；∂t k+u·∇k=∇·[(ν+νt/sigma_k)∇k]+Pk−ε；∂t ε+u·∇ε=∇·[(ν+νt/sigma_epsilon)∇ε]+C1(ε/k)Pk−C2 ε²/k。无浮力、压缩性或低雷诺数附加修正。νt 由给定 k、ε 及闭合关系确定，不是独立物理初态。k、ε 均保持正；本题不授权变更模型以迎合某个标称雷诺数。

壁面函数作如下明确解释，避免依赖软件专有名：k 为零法向导数；设邻壁单元面积平均值为 kP、单元面积质心距该壁线段所在直线的垂距为 d，uτ=Cmu^(1/4)√kP，y+=uτ d/ν。取正根 yL≈11.53 满足 yL=ln(E yL)/kappa。壁面 νtw 在 y+≤yL 时为零，在 y+>yL 时为 max(0,ν[kappa y+/ln(E y+)−1])。邻壁 ε 在低支为 2νkP/d²，高支为 Cmu^(3/4)kP^(3/2)/(kappa d)。高支的邻壁生产率 Pk=(ν+νtw)|∂n u|uτ/(kappa d)，低支为零；该邻壁约束覆盖 ε 输运和 Pk 的内部表达式。多个壁段邻接同一单元时，对各段贡献等权平均；ε 壁面迹取所得邻壁值。此壁函数距离由给定物理网格确定，不是可调模型参数。求解可采用不同内部离散，但须保持该近壁解释。上盖端点与侧壁只按各自边迹施加，不请求角点输出。

## 输入场与条件集合

fields 必须且仅包含：`initial_velocity`（velocity，m/s，vector，domain，initial，全零）、`initial_pressure`（pressure，Pa，scalar，domain，initial，全零）、`initial_k`（turbulent_k，m2/s2，scalar，domain，initial，0.00375）、`initial_epsilon`（turbulent_epsilon，m2/s3，scalar，domain，initial，0.00754），以及 `lid_velocity`（velocity，m/s，vector，movingWall，constant）和 `fixed_velocity`（velocity，m/s，vector，fixedWalls，constant）。

除边界速度字段外，每个 initial 字段恰有一条 initial/assign 条件，variable 为括号中的 quantity；条件 data.value 引用相应字段。所有初态是给定物理状态。边界场恒定于整个区间。下表中列出多个 location 时，必须逐一独立声明记录，不以字符串并集代替 location。

| location | variable | operator | data |
|---|---|---|---|
| movingWall | velocity | dirichlet | value=field(lid_velocity)，(1.5,0) m/s |
| fixedWalls | velocity | dirichlet | value=field(fixed_velocity)，(0,0) m/s |
| movingWall、fixedWalls（各一次） | pressure | normal_derivative | mode=option(zero) |
| movingWall、fixedWalls（各一次） | turbulent_k | normal_derivative | mode=option(zero) |
| movingWall、fixedWalls（各一次） | turbulent_epsilon | epsilon_wall | mode=option(standard) |
| movingWall、fixedWalls（各一次） | turbulent_viscosity | nut_wall | mode=option(standard) |

`epsilon_wall` 和 `nut_wall` 精确表示前文壁面函数；data 仅含 mode，值仅允许 standard。压力无 Dirichlet 约束，每个时刻将压力平移到全域面积加权平均为零，作为输出唯一基准；不沿用来源“第0单元”的网格依赖基准。

## 输出

`outputs` 必须且仅含下列对象；完整元数据如下，不在结果文件中重复存元数据。所有输出均为 domain 单元面积平均。输出物理时刻精确为 t=0,0.5,…,10 s（21 帧），不是迭代编号；内部时间步自由选择。

```json
{
  "velocity": {
    "array": "velocity",
    "quantity": "velocity",
    "location": "domain",
    "time_axis": "result",
    "dtype": "float64",
    "kind": "vector",
    "component_shape": [
      2
    ],
    "components": [
      "x",
      "y"
    ],
    "unit": "m/s",
    "value_kind": "average"
  },
  "pressure": {
    "array": "pressure",
    "quantity": "pressure",
    "location": "domain",
    "time_axis": "result",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "Pa",
    "value_kind": "average"
  },
  "turbulent_k": {
    "array": "turbulent_k",
    "quantity": "turbulent_k",
    "location": "domain",
    "time_axis": "result",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "m2/s2",
    "value_kind": "average"
  },
  "turbulent_epsilon": {
    "array": "turbulent_epsilon",
    "quantity": "turbulent_epsilon",
    "location": "domain",
    "time_axis": "result",
    "dtype": "float64",
    "kind": "scalar",
    "component_shape": [
      1
    ],
    "components": [
      "value"
    ],
    "unit": "m2/s3",
    "value_kind": "average"
  }
}
```

提交一个结果 `.h5`，恰含上述输出对象的 array key、`cell_ids`、`result_times`。IDs 和时间数组逐值、逐序复制输入；不导出边界 IDs、初态、常量时间轴、坐标或网格。初态帧按给定初态面积平均填入；压力同时遵守本题压力基准。结果 HDF5 写到题面规定命令行的 `--output` 路径。

## 支持状态

本文定义使用通用协议可表达的本题声明；本题模型的专用声明检查、公开运行工具、输入数据、数值参考和评分器尚未装配。通用结构检查不能验证上述物理条件或解的正确性。此阶段没有可运行的正式评测包。
