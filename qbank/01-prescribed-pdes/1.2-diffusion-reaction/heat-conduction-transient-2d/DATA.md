# 瞬态热传导输入说明

采用[通用数据协议](../../../../docs/CONTRACT.md)。本说明是题目的一部分。

`task="heat-conduction-transient-2d"`、`spatial_dimension=2`、`physics.model="transient_heat_conduction"`。

## 网格与参数

`problem.json` 引用 `mesh.msh` 和 `input.h5`；可附 `mesh.geo`。求解域和三角形连接关系以 MSH 为准。

`physics.parameters` 给出带单位常量：`conductivity`、`volumetric_heat_capacity`、`x0`、`y0`、`length_x`、`length_y`。热扩散系数为 k/C。

Physical Groups 为域 `(2,1)`，left/right/bottom/top `(1,2)/(1,3)/(1,4)/(1,5)`。位置 `domain` 和四边均为 element；位置 `nodes` 包含全部网格节点，按 tag 递增排列，tag 可以不连续。

## 初始条件与时间轴

`time_axes.initial` 引用 `initial_times=float64([0.0])`。初始场 `fields.initial_temperature` 位于 `nodes`，时间轴为 `initial`，shape `[1,N,1]`，单位 K。

初始条件记录为：

```json
{
  "role": "initial", "variable": "temperature", "location": "nodes",
  "operator": "assign", "data": {"value": {"field": "initial_temperature"}}
}
```

**连续初始温度由 MSH 中每个三角形的三个节点值线性确定**，邻接三角形在公共边连续。这些节点值不隐含其他解析函数或插值规则。

`time_axes.output` 引用 `times`，其中第一项为零，后续为要求输出的物理时刻（s）。初始轴和输出轴分别声明，不能用输出层数推断内部步数，也不能把非均匀输出间隔当作固定时间步。

## 边界条件

每条边恰有一条 `role=boundary` 记录，`variable=temperature`，`location` 引用该边。`data.value` 是带单位的零常量：Dirichlet 为 K，法向导数为 K/m，热流和 Robin 为 W/m2。

Robin 另含 `data.alpha`、`data.beta`，均为 `{"value": 数值, "unit": 单位}` 常量，单位分别为 `W/(m2.K)` 和 `W/(m.K)`；α、β均为正。所有条件以题面方程解释，法向指向域外。

条件列表顺序没有含义。角点相邻边含 Dirichlet 时，该节点温度为零；其他条件作用在各自边的内部。

## 读取与输出

可使用 SDK：

```python
from caeoj.sdk import load_problem, read_constant, read_field

problem = load_problem("problem.json")
capacity = read_constant(problem.manifest["physics"]["parameters"]["volumetric_heat_capacity"])
initial = next(c for c in problem.manifest["conditions"] if c["role"] == "initial")
temperature0 = read_field(problem, initial["data"]["value"])
```

输出 `temperature[t,i,0]` 对应输入 `times[t]` 和 `node_ids[i]`。不能输出内部步、额外诊断或另一套时间轴；无需输出 `initial_times`。

结构校验器检查字段、数组形状、类型和固定轴，不验证时间步稳定性、初始／边界相容性或物理解。
