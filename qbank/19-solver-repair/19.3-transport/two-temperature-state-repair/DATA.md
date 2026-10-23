# 双温状态关系数据

通用结构见 [CONTRACT](../../../../docs/CONTRACT.md)。每例包含 `problem.json` 与 `input.h5`。`task=two-temperature-state-repair`，`physics.model=two-temperature-state-v1`，`spatial_dimension=1` 为协议占位；无空间几何、网格、边界或物理时间演化，`geometries`、`meshes`为空对象，`conditions=[]`，`physics.parameters={}`。

`locations.states={"kind":"entities","ids":"state_ids"}`。`state_ids` 是长度 N、互异 int64 标识，1≤N≤32；数组行顺序定义状态顺序。`time_axes.instant=times`，`times` 是 float64 数组 `[0.0]`。下述每个字段的 `location=states`、`time_axis=instant`、`value_kind=point`，标量 `kind=scalar, component_shape=[1], components=["value"]`，三分量 `kind=components, component_shape=[3], components=["O2","O","E"]`。输入 `sampling={"space":"uniform","time":"constant","extrapolation":"forbid"}`。除 mode 为 int64 外，所有字段为 float64；数据集键与字段名相同。

|输入字段|quantity|单位|shape|含义及范围|
|---|---|---|---|---|
|mode|state_constraint|1|[1,N,1]|0为密度约束；1为总压约束|
|temperature|temperature|K|[1,N,1]|重粒子温度T，200至3000|
|electron_temperature|temperature|K|[1,N,1]|初始电子温度Te，200至100000|
|final_electron_temperature|temperature|K|[1,N,1]|改变后的电子温度Te2，同范围|
|constraint_value|state_constraint_value|1|[1,N,1]|mode0表示质量密度kg/m³，1e-5至10；mode1表示绝对总压Pa，10至1e7。协议单位1标识按mode解释的带标签数值，并非物理无量纲量|
|mole_fractions|mole_fraction|1|[1,N,3]|O2、O、E摩尔分数，均非负，和为1（绝对误差≤1e-12），电子分数≤0.8|

每行从新建的 `PlasmaPhase` 开始，依次设置摩尔分数与初始电子温度；mode0调用 `setState_TD(T,constraint_value)`，mode1调用 `setState_TP(T,constraint_value)`；然后调用 `setElectronTemperature(Te2)`，mode1另调用 `setPressure(constraint_value)`。输出此时的最终状态。mode0始终保持给定密度；mode1以最终Te2满足给定总压，最终密度由状态关系决定。T与组分在上述电子温度修改中保持不变。气体常数为Cantera常数8314.46261815324 J/(kmol K)，O原子摩尔质量15.999 kg/kmol，电子0.0005485799088728283 kg/kmol；完整实际物种定义为公开YAML。

|输出字段|quantity|单位|shape|意义|
|---|---|---|---|---|
|pressure|pressure|Pa|[1,N,1]|最终绝对总压|
|electron_pressure|electron_pressure|Pa|[1,N,1]|最终电子分压|
|density|density|kg/m^3|[1,N,1]|最终质量密度|
|concentrations|molar_concentration|kmol/m^3|[1,N,3]|O2、O、E的实际摩尔浓度，按相同顺序|

可信运行器负责调用SDK `write_result` 产生 `result.h5`，以输入中的状态及瞬时轴身份写回全部输出。考生只提交规定的库头文件，无须另写结果程序。输入有限且在以上范围内，不要求容错处理范围外状态。密度和压力约束不会在同一行同时指定，初始Te与Te2可以相等，也可以比T更高或更低。零电子和等温状态是公开支持的回归极限。
