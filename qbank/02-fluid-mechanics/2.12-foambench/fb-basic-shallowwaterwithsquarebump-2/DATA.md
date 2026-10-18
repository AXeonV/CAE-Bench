# 2.12.85 数据说明

`task` 固定为 `fb-basic-shallowwaterwithsquarebump-2`。

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

## 本题模型、地形与初态

`physics.model="foambench-shallowWaterWithSquareBump"`，parameters 精确为：

```json
{
  "gravity": {
    "value": 9.81,
    "unit": "m/s2"
  },
  "rotation_rate": {
    "value": 7.292e-05,
    "unit": "1/s"
  },
  "initial_surface": {
    "value": 0.02,
    "unit": "m"
  },
  "inlet_flux": {
    "value": 0.001,
    "unit": "m2/s"
  },
  "outlet_depth": {
    "value": 0.01,
    "unit": "m"
  },
  "bump_height": {
    "value": 0.001,
    "unit": "m"
  },
  "start_time": {
    "value": 0,
    "unit": "s"
  },
  "end_time": {
    "value": 100,
    "unit": "s"
  }
}
```

上述数值均固定。domain 的几何为 [0,1]×[0,1] m²；位置 inlet 为 x=0，outlet 为 x=1，sides 为 y=0 与 y=1 的并集。二维网格须沿方形突起的四条边分区，使任一单元内部床高 b 不跳变。原始薄片厚度 0.1 m 仅用于二维实现，不是水深，不参与水平面积、流量或体积的计算。

采用不可压、静水压、无底摩擦、无黏性扩散的单层旋转浅水模型，u=q/h，η=h+b，g=gravity，f=2 rotation_rate。守恒方程为 ∂t h+∇·q=0，∂t q+∇·(q⊗q/h+g h²I/2)=−g h∇b−f Jq，其中 J(qx,qy)=(−qy,qx)。无风、降水、渗漏或其他源。要求水深非负；出现水力跃变时取耗散机械能的熵解。固定床台阶源项采用静水路径：同一界面两侧将自由面 η 与床高 b 作线性路径连接、h=η−b，因此床源跳跃积分为 −g(hL+hR)(bR−bL)n/2；不是把台阶当成固体障碍侧壁。

fields 必须包含：`bed`（quantity=bed，m，scalar，domain，constant）、`initial_depth`（quantity=depth，m，scalar，domain，initial）、`initial_flux`（quantity=water_flux，m2/s，vector，domain，initial）、`inlet_flux`（quantity=water_flux，m2/s，vector，inlet，constant）。bed 在突起内为 0.001 m、外部为零；初态严格为 h=0.02−b、q=(0.001 h/0.02,0)，以此精确关系为准，不能使用来源文件中遗留的统一 0.009 m 或 0.0009 m²/s，也不把原 prompt 的小数截断当作额外扰动。自由面初始高度不意味着出口深度改为 0.02 m；右侧 t>0 一律为 0.01 m。

bed 使用 `role=material,variable=bed,operator=assign,location=domain,data={"value":{"field":"bed"}}`，表示固定床高而非材料黏度。两个初态各有一次 initial/assign 条件。

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

## 输出

`outputs` 必须且仅含下列对象；完整元数据如下，不在结果文件中重复存元数据。所有输出均为 domain 单元面积平均。输出物理时刻精确为 t=0,1,…,100 s（101 帧），不是迭代编号；内部时间步自由选择。

```json
{
  "depth": {
    "array": "depth",
    "quantity": "depth",
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
    "unit": "m",
    "value_kind": "average"
  },
  "water_flux": {
    "array": "water_flux",
    "quantity": "water_flux",
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
    "unit": "m2/s",
    "value_kind": "average"
  }
}
```

提交一个结果 `.h5`，恰含上述输出对象的 array key、`cell_ids`、`result_times`。IDs 和时间数组逐值、逐序复制输入；不导出边界 IDs、初态、常量时间轴、坐标或网格。初态帧按给定初态面积平均填入；压力同时遵守本题压力基准。结果 HDF5 写到题面规定命令行的 `--output` 路径。

## 支持状态

本文定义使用通用协议可表达的本题声明；本题模型的专用声明检查、公开运行工具、输入数据、数值参考和评分器尚未装配。通用结构检查不能验证上述物理条件或解的正确性。此阶段没有可运行的正式评测包。
