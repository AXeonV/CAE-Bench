# 2.12.101 数据说明

`task` 固定为 `fb-basic-cylinder-7`。

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

`physics.model="foambench-Cylinder"`，parameters 精确为：

```json
{
  "density": {
    "value": 1,
    "unit": "kg/m3"
  },
  "nu": {
    "value": 0.1,
    "unit": "m2/s"
  },
  "drive_speed": {
    "value": 2.0,
    "unit": "m/s"
  },
  "start_time": {
    "value": 0,
    "unit": "s"
  },
  "end_time": {
    "value": 0.5,
    "unit": "s"
  },
  "nuInf": {
    "value": 10,
    "unit": "m2/s"
  },
  "cross_time": {
    "value": 0.4,
    "unit": "s"
  },
  "cross_exponent": {
    "value": 3,
    "unit": "1"
  }
}
```

所有数值固定。domain 为矩形 [−5,5]×[−1.5,2.5] m² 减去闭圆盘 x²+y²≤1 m²。位置 left 为 x=−5，right 为 x=5，up 为 y=2.5，down 为 y=−1.5，cylinder 为圆周。内孔用真实圆弧几何建模，网格边界是其离散表示；源出平面 −1≤z≤1 m 的薄片已化为二维，无端面边界和端面摩擦。

本题速度是不可压连续介质速度；压力输出为机械静表压 p，单位 Pa；固定密度 ρ=density=1 kg/m3，零点是本题所定表压基准，不是绝对真空。采用 ∇·u=0，∂t u+u·∇u=−∇p/ρ+∇·[2νeff S]；无重力、旋转、热输运或其他体力。

无湍流闭合，νeff=νC。令 γdot=√(2 S:S)，S=(∇u+∇uᵀ)/2，νC=nuInf+(nu−nuInf)/[1+(cross_time γdot)^cross_exponent]。parameters.nu 明确是零剪切运动黏度 ν₀，不是另一层恒定黏度；源配置的基础 constant 属性与广义牛顿模型合成后仅采用该 Cross 公式。γdot 单位 1/s，cross_time 单位 s，νC 单位 m2/s；应力除以密度为 2νC S。无黏度截断、屈服应力或附加输运方程。

## 输入场与条件集合

fields 必须且仅包含：`initial_velocity`（velocity，m/s，vector，domain，initial，全零）、`initial_pressure`（pressure，Pa，scalar，domain，initial，全零），`inlet_velocity`（velocity，m/s，vector，left，constant，值 (2,0)），以及 `up_velocity`、`down_velocity`、`cylinder_velocity`（均 quantity=velocity，m/s，vector，分别在同名边界，constant，值全零）。

除边界速度字段外，每个 initial 字段恰有一条 initial/assign 条件，variable 为括号中的 quantity；条件 data.value 引用相应字段。所有初态是给定物理状态。边界场恒定于整个区间。下表中列出多个 location 时，必须逐一独立声明记录，不以字符串并集代替 location。

| location | variable | operator | data |
|---|---|---|---|
| left | velocity | dirichlet | value=field(inlet_velocity) |
| right | velocity | normal_derivative | mode=option(zero) |
| right | pressure | dirichlet | value=常量 0 Pa |
| left、up、down、cylinder（各一次） | pressure | normal_derivative | mode=option(zero) |
| up、down、cylinder（各一次） | velocity | dirichlet | value=field(对应的 up_velocity、down_velocity、cylinder_velocity) |

出口只执行上述固定值／梯度条件，不隐含应力自由边界或自动反流切换。压力基准由出口 p=0 唯一固定，不再减去全域均值。

## 输出

`outputs` 必须且仅含下列对象；完整元数据如下，不在结果文件中重复存元数据。所有输出均为 domain 单元面积平均。输出物理时刻精确为 t=0,0.05,…,0.5 s（11 帧），不是迭代编号；内部时间步自由选择。

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
  }
}
```

提交一个结果 `.h5`，恰含上述输出对象的 array key、`cell_ids`、`result_times`。IDs 和时间数组逐值、逐序复制输入；不导出边界 IDs、初态、常量时间轴、坐标或网格。初态帧按给定初态面积平均填入；压力同时遵守本题压力基准。结果 HDF5 写到题面规定命令行的 `--output` 路径。

## 支持状态

本文定义使用通用协议可表达的本题声明；本题模型的专用声明检查、公开运行工具、输入数据、数值参考和评分器尚未装配。通用结构检查不能验证上述物理条件或解的正确性。此阶段没有可运行的正式评测包。
